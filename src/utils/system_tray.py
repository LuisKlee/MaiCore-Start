"""System tray management utilities for the launcher."""
from __future__ import annotations

import ctypes
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

import structlog

try:  # Optional dependencies; gracefully degrade if unavailable.
    from PIL import Image  # type: ignore
    import pystray  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    Image = None  # type: ignore
    pystray = None  # type: ignore

logger = structlog.get_logger(__name__)


class SystemTrayManager:
    """Encapsulates minimize-to-tray behavior for Windows environments."""

    def __init__(self, icon_path: Path):
        self.icon_path = Path(icon_path)
        self._icon: Optional["pystray.Icon"] = None
        self._icon_thread: Optional[threading.Thread] = None
        self._icon_image = None
        self._is_visible = False
        self._restore_callback: Optional[Callable[[], None]] = None
        self._exit_callback: Optional[Callable[[], None]] = None
        self._console_icon_handle = None

    def is_supported(self) -> bool:
        """Return True if the current platform and dependencies support tray icons."""
        return (
            sys.platform.startswith("win")
            and pystray is not None
            and Image is not None
        )

    def minimize(self, on_restore: Callable[[], None], on_exit: Callable[[], None]) -> bool:
        """Hide the console window and show a tray icon with restore/exit actions."""
        if not self.is_supported():
            logger.warning("系统托盘功能当前环境不可用。")
            return False

        if not self.icon_path.exists():
            logger.error("托盘图标文件不存在", path=str(self.icon_path))
            return False

        if self._is_visible:
            logger.info("系统托盘图标已显示，无需重复创建。")
            return True

        self._restore_callback = on_restore
        self._exit_callback = on_exit

        try:
            with Image.open(self.icon_path) as img:  # type: ignore[arg-type]
                self._icon_image = img.copy()
        except Exception as exc:  # pragma: no cover - visual asset failure
            logger.error("加载托盘图标失败", error=str(exc))
            return False

        menu = pystray.Menu(  # type: ignore[union-attr]
            pystray.MenuItem("显示主窗口", self._handle_restore, default=True),
            pystray.MenuItem("退出程序", self._handle_exit)
        )

        self._icon = pystray.Icon("maicore_launcher", self._icon_image, "麦麦启动器", menu)  # type: ignore[union-attr]
        self._icon_thread = threading.Thread(target=self._icon.run, daemon=True)
        self._icon_thread.start()

        self._set_taskbar_visibility(False)
        self._hide_console_window()
        self._is_visible = True
        logger.info("应用已最小化至系统托盘", icon=str(self.icon_path))
        return True

    def restore(self) -> None:
        """Restore the console window if the tray icon is visible."""
        if not self._is_visible:
            return
        self._set_taskbar_visibility(True)
        self._show_console_window()
        self._shutdown_icon()
        logger.info("用户已从系统托盘恢复窗口")

    def request_exit(self) -> None:
        """Request application exit while ensuring the tray icon is cleaned up."""
        self._shutdown_icon()
        if self._exit_callback:
            self._exit_callback()

    def stop(self) -> None:
        """Forcefully remove the tray icon, used during application shutdown."""
        self._shutdown_icon()
        self._set_taskbar_visibility(True)

    # Internal helpers -----------------------------------------------------
    def _handle_restore(self, _icon, _item) -> None:
        self.restore()
        if self._restore_callback:
            self._restore_callback()

    def _handle_exit(self, _icon, _item) -> None:
        self._shutdown_icon()
        if self._exit_callback:
            self._exit_callback()

    def _shutdown_icon(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception as exc:  # pragma: no cover - backend-specific cleanup
                logger.warning("停止托盘图标失败", error=str(exc))
        self._icon = None
        self._icon_thread = None
        self._is_visible = False

    def apply_console_icon(self) -> None:
        """Update the console window icon so the taskbar shows output.ico instead of default."""
        if not sys.platform.startswith("win"):
            return
        hwnd = self._get_console_hwnd()
        if not hwnd or not self.icon_path.exists():
            return

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        icon_handle = ctypes.windll.user32.LoadImageW(
            None,
            str(self.icon_path),
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )
        if not icon_handle:
            logger.warning("加载窗口图标失败", path=str(self.icon_path))
            return

        WM_SETICON = 0x0080
        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, icon_handle)
        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, icon_handle)
        self._console_icon_handle = icon_handle  # keep reference alive
        logger.info("已应用自定义窗口图标", icon=str(self.icon_path))

    def _set_taskbar_visibility(self, visible: bool) -> None:
        if not sys.platform.startswith("win"):
            return
        hwnd = self._get_console_hwnd()
        if not hwnd:
            return
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if visible:
            style |= WS_EX_APPWINDOW
            style &= ~WS_EX_TOOLWINDOW
        else:
            style &= ~WS_EX_APPWINDOW
            style |= WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    @staticmethod
    def _hide_console_window() -> None:
        if not sys.platform.startswith("win"):
            return
        hwnd = SystemTrayManager._get_console_hwnd()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE

    @staticmethod
    def _show_console_window() -> None:
        if not sys.platform.startswith("win"):
            return
        hwnd = SystemTrayManager._get_console_hwnd()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
            ctypes.windll.user32.SetForegroundWindow(hwnd)

    @staticmethod
    def _get_console_hwnd():
        if not sys.platform.startswith("win"):
            return None
        return ctypes.windll.kernel32.GetConsoleWindow()
