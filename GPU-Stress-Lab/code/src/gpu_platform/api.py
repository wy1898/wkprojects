"""Dashboard API 和后台压力测试控制器。"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

from flask import Flask, jsonify, request

from .alert import detect_alerts
from .history import append_history, load_history
from .stress import run_stress
from .utils import GpuQueryError, get_logger, read_gpu_metrics


class DashboardController:
    """管理监控历史和一个后台压力测试任务。"""

    def __init__(self, device: int = 0, history_size: int = 120) -> None:
        self.device = device
        self.history: deque[dict[str, Any]] = deque(maxlen=history_size)
        self.lock = threading.RLock()
        self.stop_event: threading.Event | None = None
        self.worker: threading.Thread | None = None
        self.stress_state: dict[str, Any] = {
            "running": False,
            "started_at": None,
            "duration": 0,
            "size": 2048,
            "interval": 1,
            "summary": None,
            "history_record": None,
            "error": None,
        }
        self.last_error: str | None = None
        self.logger = get_logger("gpu-platform.web")

    def _record(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """写入快照并计算告警。"""
        with self.lock:
            previous = list(self.history)
            alerts = detect_alerts(
                snapshot,
                previous,
                stress_active=bool(self.stress_state["running"]),
            )
            snapshot = {**snapshot, "alerts": alerts}
            self.history.append(snapshot)
            self.last_error = None
            return snapshot

    def poll(self) -> dict[str, Any] | None:
        """读取并保存一份最新 GPU 快照；失败时保留错误状态。"""
        try:
            return self._record(read_gpu_metrics(self.device))
        except GpuQueryError as exc:
            with self.lock:
                self.last_error = str(exc)
            self.logger.warning("GPU polling failed: %s", exc)
            return None

    def record_stress_snapshot(self, snapshot: dict[str, Any]) -> None:
        """接收 stress.py 的实时采样回调。"""
        try:
            self._record(snapshot)
        except Exception as exc:
            self.logger.exception("Unable to record stress snapshot: %s", exc)

    def start_stress(self, options: dict[str, Any]) -> tuple[bool, str]:
        """启动后台压力测试，避免阻塞 Flask 请求线程。"""
        with self.lock:
            if self.worker and self.worker.is_alive():
                return False, "压力测试已经在运行"
            try:
                duration = float(options.get("duration", 60))
                size = int(options.get("size", 2048))
                interval = float(options.get("interval", 1))
                device = int(options.get("device", self.device))
                if duration <= 0 or size <= 0 or interval <= 0 or device < 0:
                    raise ValueError("duration、size、interval 必须大于 0，device 不能为负数")
            except (TypeError, ValueError) as exc:
                return False, f"参数错误：{exc}"

            self.device = device
            self.stop_event = threading.Event()
            self.stress_state.update({
                "running": True,
                "started_at": time.time(),
                "duration": duration,
                "size": size,
                "interval": interval,
                "summary": None,
                "history_record": None,
                "error": None,
            })
            self.worker = threading.Thread(
                target=self._stress_worker,
                args=(device, duration, size, interval, self.stop_event),
                name="gpu-stress-worker",
                daemon=True,
            )
            self.worker.start()
            return True, "压力测试已启动"

    def _stress_worker(
        self,
        device: int,
        duration: float,
        size: int,
        interval: float,
        stop_event: threading.Event,
    ) -> None:
        """在线程中执行压力测试，并把结果写回控制器。"""
        try:
            summary = run_stress(
                device=device,
                duration=duration,
                size=size,
                interval=interval,
                stop_event=stop_event,
                status_callback=self.record_stress_snapshot,
                console_output=False,
            )
            with self.lock:
                self.stress_state["summary"] = summary
                self.stress_state["history_record"] = append_history(summary)
                self.stress_state["error"] = None
        except Exception as exc:
            self.logger.exception("Stress worker failed: %s", exc)
            with self.lock:
                self.stress_state["error"] = str(exc)
                fallback_summary = {
                    "completed_at": time.time(),
                    "duration_seconds": max(0, time.time() - (self.stress_state["started_at"] or time.time())),
                    "average_utilization": 0,
                    "peak_temperature": 0,
                    "peak_memory": 0,
                    "status": "WARNING",
                }
                self.stress_state["summary"] = fallback_summary
                self.stress_state["history_record"] = append_history(fallback_summary)
        finally:
            with self.lock:
                self.stress_state["running"] = False

    def stop_stress(self) -> tuple[bool, str]:
        """请求后台压力测试在下一个安全点停止。"""
        with self.lock:
            if not self.worker or not self.worker.is_alive() or not self.stop_event:
                return False, "当前没有运行中的压力测试"
            self.stop_event.set()
            return True, "已发送停止请求"

    def status(self) -> dict[str, Any]:
        """返回前端所需的当前快照、历史和压力测试状态。"""
        current = self.poll()
        with self.lock:
            latest = current or (self.history[-1] if self.history else None)
            alerts = latest.get("alerts", []) if latest else []
            return {
                "gpu": latest,
                "history": list(self.history),
                "alerts": alerts,
                "error": self.last_error,
                "stress": dict(self.stress_state),
                "test_history": load_history(),
                "server_time": time.time(),
            }


def register_api(app: Flask, controller: DashboardController) -> None:
    """向 Flask 应用注册 Dashboard JSON API。"""

    @app.get("/api/status")
    def status() -> Any:
        return jsonify(controller.status())

    @app.get("/api/history")
    def history() -> Any:
        """返回最近十次压力测试记录，供历史表格单独刷新。"""
        return jsonify({"records": load_history()})

    @app.post("/api/stress/start")
    def start_stress() -> Any:
        payload = request.get_json(silent=True) or {}
        started, message = controller.start_stress(payload)
        return jsonify({"ok": started, "message": message}), (200 if started else 409)

    @app.post("/api/stress/stop")
    def stop_stress() -> Any:
        stopped, message = controller.stop_stress()
        return jsonify({"ok": stopped, "message": message}), (200 if stopped else 409)

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"ok": True, "service": "gpu-platform"})
