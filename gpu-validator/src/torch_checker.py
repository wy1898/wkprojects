"""PyTorch and CUDA runtime detection."""

from __future__ import annotations

from .models import CheckResult


class TorchChecker:
    """Inspect the installed PyTorch package and CUDA availability."""

    def check(self) -> CheckResult:
        """Check PyTorch installation, CUDA availability, and GPU identity.

        Returns:
            A result containing real PyTorch runtime information.
        """
        try:
            import torch
        except ImportError as exc:
            return CheckResult(
                check_name="pytorch",
                status="failed",
                message=f"PyTorch is not installed: {exc}",
            )

        try:
            if not torch.cuda.is_available():
                return CheckResult(
                    check_name="pytorch",
                    status="failed",
                    message=(
                        f"PyTorch {torch.__version__} is installed, "
                        "but CUDA is not available"
                    ),
                )

            device_name = torch.cuda.get_device_name(0)
            runtime_version = torch.version.cuda or "unknown"
        except Exception as exc:  # PyTorch may raise backend-specific errors.
            return CheckResult(
                check_name="pytorch",
                status="failed",
                message=f"PyTorch CUDA inspection failed: {exc}",
            )

        return CheckResult(
            check_name="pytorch",
            status="passed",
            message=(
                f"PyTorch {torch.__version__}; CUDA runtime {runtime_version}; "
                f"GPU {device_name}"
            ),
        )
