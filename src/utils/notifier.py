"""Windows notification utilities."""
from __future__ import annotations

import contextlib
import io
import logging
import sys
import threading
from pathlib import Path
from typing import Optional, Any


class _StderrFilter:
    """过滤stderr输出，抑制win10toast库的WNDPROC/WPARAM警告。"""
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self._suppressed_patterns = [
            "WNDPROC return value cannot be converted to LRESULT",
            "WPARAM is simple, so must be an int object",
        ]
    
    def write(self, text):
        if not any(pattern in text for pattern in self._suppressed_patterns):
            self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()
    
    def fileno(self):
        return self.original_stderr.fileno()

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
        self._win11_disabled = False
        
        # 安装stderr过滤器以抑制win10toast后台线程的警告
        if not isinstance(sys.stderr, _StderrFilter):
            sys.stderr = _StderrFilter(sys.stderr)

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
            logger.info("Windows通知未启用，跳过发送", title=title)
            return False
        icon = str(self.icon_path) if self.icon_path.exists() else None
        message_preview = message if len(message) <= 120 else f"{message[:117]}..."
        logger.info("尝试发送Windows通知", title=title, has_icon=bool(icon), message_preview=message_preview)

        # 直接使用 Win10 toast（更稳定），不使用 Win11 toast（有已知问题）
        if self._send_win10(title, message, icon, duration):
            logger.info("Windows通知发送成功", title=title, channel="win10")
            return True

        logger.warning("Windows通知发送失败", title=title)
        if not self._warned_unavailable:
            logger.warning("Windows通知发送失败，请检查系统通知设置或相关依赖。")
            self._warned_unavailable = True
        return False

    def _send_win11(self, title: str, message: str, icon: Optional[str]) -> bool:
        if self._win11_disabled:
            return False
        if win11_toast is None or not sys.platform.startswith("win"):
            return False
        try:
            kwargs = {"icon": icon} if icon else {}
            result = win11_toast(title, message, **kwargs)
            if isinstance(result, bool):
                return result
            if result is None:
                logger.warning("Win11通知返回空结果，将尝试备用通道", title=title)
                self._win11_disabled = True
                return False
            self._log_win11_result(result)
            logger.warning("Win11通知返回非布尔结果，将尝试备用通道", title=title)
            self._win11_disabled = True
            return False
        except Exception as exc:  # pragma: no cover - win11 specific
            logger.error("Win11通知发送失败", error=str(exc))
            self._win11_disabled = True
            return False

    def _log_win11_result(self, result: Any) -> None:
        try:
            if isinstance(result, (list, tuple)):
                details = []
                for item in result:
                    value = getattr(item, "value", None)
                    details.append(value if value is not None else repr(item))
                logger.info("Win11通知返回结果", details=details)
            else:
                value = getattr(result, "value", None)
                if value is not None:
                    logger.info("Win11通知返回结果", details=value)
                else:
                    logger.info("Win11通知返回结果", details=repr(result))
        except Exception as exc:
            logger.debug("记录Win11通知结果时出错", error=str(exc))

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
