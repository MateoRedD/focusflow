"""FocusFlow icon assets — tray, taskbar, and title bar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageTk

APP_USER_MODEL_ID = "FocusFlow"
TRAY_SIZE = 32
WINDOW_PHOTO_SIZE = 64
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)

IDLE_PNG = "tray-icon-idle.png"
ACTIVE_PNG = "tray-icon-active.png"
IDLE_ICO = "icon-idle.ico"
ACTIVE_ICO = "icon-active.ico"


def _assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parent / "assets"


def _ico_cache_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "FocusFlow"
    else:
        base = _assets_dir()
    cache = base / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def asset_path(filename: str) -> Path:
    return (_assets_dir() / filename).resolve()


def set_windows_app_user_model_id(app_id: str = APP_USER_MODEL_ID) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except (AttributeError, OSError):
        pass


def _load_png(filename: str) -> Image.Image:
    path = asset_path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"Missing icon asset: {path}")
    return Image.open(path).convert("RGBA")


def _ensure_ico(png_name: str, ico_name: str) -> Path:
    png_path = asset_path(png_name)
    ico_path = (_ico_cache_dir() / ico_name).resolve()
    if not ico_path.is_file() or png_path.stat().st_mtime > ico_path.stat().st_mtime:
        image = _load_png(png_name)
        image.save(ico_path, format="ICO", sizes=[(size, size) for size in ICO_SIZES])
    return ico_path


def create_idle_icon() -> Image.Image:
    return _load_png(IDLE_PNG).resize((TRAY_SIZE, TRAY_SIZE), Image.Resampling.LANCZOS)


def create_active_icon() -> Image.Image:
    return _load_png(ACTIVE_PNG).resize((TRAY_SIZE, TRAY_SIZE), Image.Resampling.LANCZOS)


def create_paused_icon() -> Image.Image:
    return create_active_icon()


class _WindowIcons:
    """Cached .ico paths and PhotoImage refs for a Tk root window."""

    def __init__(self) -> None:
        self._idle_ico: Path | None = None
        self._active_ico: Path | None = None
        self._photo_idle: ImageTk.PhotoImage | None = None
        self._photo_active: ImageTk.PhotoImage | None = None

    def _ensure(self) -> None:
        if self._idle_ico is not None:
            return
        self._idle_ico = _ensure_ico(IDLE_PNG, IDLE_ICO)
        self._active_ico = _ensure_ico(ACTIVE_PNG, ACTIVE_ICO)
        self._photo_idle = ImageTk.PhotoImage(
            _load_png(IDLE_PNG).resize(
                (WINDOW_PHOTO_SIZE, WINDOW_PHOTO_SIZE),
                Image.Resampling.LANCZOS,
            )
        )
        self._photo_active = ImageTk.PhotoImage(
            _load_png(ACTIVE_PNG).resize(
                (WINDOW_PHOTO_SIZE, WINDOW_PHOTO_SIZE),
                Image.Resampling.LANCZOS,
            )
        )

    def install(self, window, *, active: bool = False) -> None:
        self._ensure()
        self.apply(window, active=active)

    def apply(self, window, *, active: bool) -> None:
        self._ensure()
        ico_path = str(self._active_ico if active else self._idle_ico)
        photo = self._photo_active if active else self._photo_idle

        try:
            window.iconphoto(True, photo)
        except Exception:
            pass

        if sys.platform == "win32":
            try:
                window.iconbitmap(default=ico_path)
            except Exception:
                pass
            try:
                window.wm_iconbitmap(ico_path)
            except Exception:
                pass
        else:
            try:
                window.wm_iconbitmap(ico_path)
            except Exception:
                pass


_window_icons = _WindowIcons()


def install_window_icon(window, *, active: bool = False) -> None:
    _window_icons.install(window, active=active)


def apply_window_icon(window, *, active: bool) -> None:
    _window_icons.apply(window, active=active)
