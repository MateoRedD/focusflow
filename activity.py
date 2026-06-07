import ctypes
import sys
import threading
from ctypes import wintypes


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def get_idle_seconds() -> int:
    if sys.platform != "win32":
        return 0
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0
    tick = ctypes.windll.kernel32.GetTickCount()
    return int((tick - lii.dwTime) / 1000)


def show_notification(title: str, message: str) -> None:
    if sys.platform != "win32":
        return

    def _notify() -> None:
        try:
            from winotify import Notification

            toast = Notification(
                app_id="FocusFlow",
                title=title,
                msg=message,
                duration="short",
            )
            toast.show()
        except Exception:
            try:
                ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
            except Exception:
                pass

    threading.Thread(target=_notify, daemon=True).start()
