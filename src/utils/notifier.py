"""Windows notification utilities."""
from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path
from typing import Optional

import structlog

from src.core.p_config import p_config_manager

try:
    from win10toast import ToastNotifier  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ToastNotifier = None  # type: ignore

try:
    from win11toast import toast as win11_toast  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    win11_toast = None  # type: ignore

logger = structlog.get_logger(__name__)


class WindowsNotifier:
    """Helper class to send notifications to Windows Action Center."""

    def __init__(self, icon_filename: str = "output.ico") -> None:
        self.icon_path = self._resolve_icon(icon_filename)
        self._toast: Optional[ToastNotifier] = None
        self._lock = threading.Lock()
        self._warned_unavailable = False

    @staticmethod
    def _resolve_icon(icon_filename: str) -> Path:
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent.parent))
        return base_dir / icon_filename

    def is_available(self) -> bool:
        return sys.platform.startswith("win") and (
            ToastNotifier is not None or win11_toast is not None
        )

    def is_enabled(self) -> bool:
        enabled = p_config_manager.get("notifications.windows_center_enabled", False)
        if not enabled:
            return False
        if not self.is_available():
            if not self._warned_unavailable:
                logger.warning(
                    "已开启Windows通知，但缺少 win10toast/win11toast 依赖或不在Windows环境。"
                )
                self._warned_unavailable = True
            return False
        return True

    def _ensure_toast(self) -> Optional[ToastNotifier]:
        if not self.is_available():
            return None
        with self._lock:
            if self._toast is None and ToastNotifier is not None:
                self._toast = ToastNotifier()
        return self._toast

    def send(self, title: str, message: str, duration: int = 5) -> bool:
        """Send a notification if enabled."""
        if not self.is_enabled():
            return False
        icon = str(self.icon_path) if self.icon_path.exists() else None
        if self._send_win11(title, message, icon):
            return True
        if self._send_win10(title, message, icon, duration):
            return True
        if not self._warned_unavailable:
            logger.warning("Windows通知发送失败，请检查系统通知设置或相关依赖。")
            self._warned_unavailable = True
        return False

    def _send_win11(self, title: str, message: str, icon: Optional[str]) -> bool:
        if win11_toast is None or not sys.platform.startswith("win"):
            return False
        try:
            kwargs = {"icon": icon} if icon else {}
            win11_toast(title, message, **kwargs)
            return True
        except Exception as exc:  # pragma: no cover - win11 specific
            logger.error("Win11通知发送失败", error=str(exc))
            return False

    def _send_win10(self, title: str, message: str, icon: Optional[str], duration: int) -> bool:
        toaster = self._ensure_toast()
        if toaster is None:
            return False
        try:
            toaster.show_toast(
                title,
                message,
                icon_path=icon,
                duration=duration,
                threaded=True,
            )
            return True
        except Exception as exc:  # pragma: no cover - win10 specific
            logger.error("Win10通知发送失败", error=str(exc))
            return False


class NotificationLogHandler(logging.Handler):
    """Logging handler that forwards high-severity records to Windows notifications."""

    def __init__(self, notifier: WindowsNotifier, title: str = "部署告警") -> None:
        super().__init__(level=logging.WARNING)
        self.notifier = notifier
        self.title = title

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - side effect
        if not self.notifier.is_enabled():
            return
        try:
            msg = self.format(record)
            self.notifier.send(self.title, msg)
        except Exception as exc:
            logger.warning("日志通知发送失败", error=str(exc))


windows_notifier = WindowsNotifier()
