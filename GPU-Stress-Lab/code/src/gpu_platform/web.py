"""Flask Dashboard 应用入口。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, render_template

from .api import DashboardController, register_api
from .utils import get_logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_app(device: int = 0) -> Flask:
    """创建可测试、可部署的 Flask 应用实例。"""
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    controller = DashboardController(device=device)
    app.extensions["gpu_dashboard"] = controller
    register_api(app, controller)

    @app.get("/")
    def dashboard() -> Any:
        return render_template("dashboard.html")

    return app


def run_web(
    host: str = "127.0.0.1",
    port: int = 5000,
    device: int = 0,
    debug: bool = False,
) -> None:
    """启动 Web 服务；关闭 reloader 以避免重复后台线程。"""
    get_logger().info("Starting dashboard on %s:%s", host, port)
    app = create_app(device=device)
    app.run(host=host, port=port, debug=debug, use_reloader=False)
