import customtkinter as ctk

import theme

_VARIANTS = {
    "info": {
        "accent": theme.SECONDARY,
        "icon": "✓",
        "btn_text": "Entendido",
        "btn_color": theme.PRIMARY,
        "btn_hover": theme.PRIMARY_HOVER,
        "btn_text_color": theme.TEXT_ON_PRIMARY,
    },
    "warning": {
        "accent": theme.WARNING,
        "icon": "!",
        "btn_text": "Entendido",
        "btn_color": theme.TERTIARY,
        "btn_hover": theme.TERTIARY_HOVER,
        "btn_text_color": theme.TEXT,
    },
    "error": {
        "accent": theme.PRIMARY,
        "icon": "✕",
        "btn_text": "Cerrar",
        "btn_color": theme.PRIMARY,
        "btn_hover": theme.PRIMARY_HOVER,
        "btn_text_color": theme.TEXT_ON_PRIMARY,
    },
    "confirm": {
        "accent": theme.TERTIARY,
        "icon": "?",
        "btn_text": None,
        "btn_color": theme.PRIMARY,
        "btn_hover": theme.PRIMARY_HOVER,
        "btn_text_color": theme.TEXT_ON_PRIMARY,
    },
}


def _center_over_parent(dialog: ctk.CTkToplevel, parent: ctk.CTk) -> None:
    dialog.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    x = px + (pw - w) // 2
    y = py + (ph - h) // 2
    dialog.geometry(f"+{x}+{y}")


def _show_dialog(
    parent: ctk.CTk,
    title: str,
    message: str,
    variant: str,
) -> None:
    style = _VARIANTS[variant]

    dialog = ctk.CTkToplevel(parent)
    dialog.title("")
    dialog.resizable(False, False)
    dialog.configure(fg_color=theme.BG)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.attributes("-topmost", True)

    shell = ctk.CTkFrame(
        dialog,
        fg_color=theme.CARD,
        corner_radius=16,
        border_width=1,
        border_color=theme.CARD_BORDER,
    )
    shell.pack(padx=2, pady=2, fill="both", expand=True)

    inner = ctk.CTkFrame(shell, fg_color="transparent")
    inner.pack(padx=28, pady=24, fill="both")

    header = ctk.CTkFrame(inner, fg_color="transparent")
    header.pack(fill="x", pady=(0, 12))

    icon_wrap = ctk.CTkFrame(
        header,
        width=44,
        height=44,
        corner_radius=22,
        fg_color=style["accent"],
    )
    icon_wrap.pack(side="left")
    icon_wrap.pack_propagate(False)
    ctk.CTkLabel(
        icon_wrap,
        text=style["icon"],
        font=(theme.FONT, 18, "bold"),
        text_color="#ffffff",
    ).place(relx=0.5, rely=0.5, anchor="center")

    title_frame = ctk.CTkFrame(header, fg_color="transparent")
    title_frame.pack(side="left", fill="x", expand=True, padx=(14, 0))
    ctk.CTkLabel(
        title_frame,
        text=title,
        font=(theme.FONT, 17, "bold"),
        text_color=theme.TEXT,
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        inner,
        text=message,
        font=(theme.FONT, 13),
        text_color=theme.TEXT_MUTED,
        anchor="w",
        justify="left",
        wraplength=320,
    ).pack(fill="x", pady=(0, 20))

    def close() -> None:
        dialog.grab_release()
        dialog.destroy()

    ctk.CTkButton(
        inner,
        text=style["btn_text"],
        height=40,
        corner_radius=12,
        fg_color=style["btn_color"],
        hover_color=style["btn_hover"],
        text_color=style.get("btn_text_color", theme.TEXT_ON_PRIMARY),
        font=(theme.FONT, 13, "bold"),
        command=close,
    ).pack(anchor="e")

    dialog.bind("<Return>", lambda _e: close())
    dialog.bind("<Escape>", lambda _e: close())
    dialog.protocol("WM_DELETE_WINDOW", close)

    _center_over_parent(dialog, parent)
    dialog.wait_window()


def _ask_dialog(parent: ctk.CTk, title: str, message: str) -> bool:
    style = _VARIANTS["confirm"]
    result = {"value": False}

    dialog = ctk.CTkToplevel(parent)
    dialog.title("")
    dialog.resizable(False, False)
    dialog.configure(fg_color=theme.BG)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.attributes("-topmost", True)

    shell = ctk.CTkFrame(
        dialog,
        fg_color=theme.CARD,
        corner_radius=16,
        border_width=1,
        border_color=theme.CARD_BORDER,
    )
    shell.pack(padx=2, pady=2, fill="both", expand=True)

    inner = ctk.CTkFrame(shell, fg_color="transparent")
    inner.pack(padx=28, pady=24, fill="both")

    header = ctk.CTkFrame(inner, fg_color="transparent")
    header.pack(fill="x", pady=(0, 12))

    icon_wrap = ctk.CTkFrame(
        header,
        width=44,
        height=44,
        corner_radius=22,
        fg_color=style["accent"],
    )
    icon_wrap.pack(side="left")
    icon_wrap.pack_propagate(False)
    ctk.CTkLabel(
        icon_wrap,
        text=style["icon"],
        font=(theme.FONT, 18, "bold"),
        text_color="#ffffff",
    ).place(relx=0.5, rely=0.5, anchor="center")

    title_frame = ctk.CTkFrame(header, fg_color="transparent")
    title_frame.pack(side="left", fill="x", expand=True, padx=(14, 0))
    ctk.CTkLabel(
        title_frame,
        text=title,
        font=(theme.FONT, 17, "bold"),
        text_color=theme.TEXT,
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        inner,
        text=message,
        font=(theme.FONT, 13),
        text_color=theme.TEXT_MUTED,
        anchor="w",
        justify="left",
        wraplength=320,
    ).pack(fill="x", pady=(0, 20))

    buttons = ctk.CTkFrame(inner, fg_color="transparent")
    buttons.pack(fill="x")

    def choose(value: bool) -> None:
        result["value"] = value
        dialog.grab_release()
        dialog.destroy()

    ctk.CTkButton(
        buttons,
        text="Cancelar",
        width=110,
        height=40,
        corner_radius=12,
        fg_color=theme.INPUT,
        hover_color=theme.CARD_BORDER,
        text_color=theme.TEXT,
        font=(theme.FONT, 13),
        command=lambda: choose(False),
    ).pack(side="right", padx=(8, 0))

    ctk.CTkButton(
        buttons,
        text="Sí, guardar",
        width=120,
        height=40,
        corner_radius=12,
        fg_color=theme.PRIMARY,
        hover_color=theme.PRIMARY_HOVER,
        text_color=theme.TEXT_ON_PRIMARY,
        font=(theme.FONT, 13, "bold"),
        command=lambda: choose(True),
    ).pack(side="right")

    dialog.bind("<Escape>", lambda _e: choose(False))
    dialog.protocol("WM_DELETE_WINDOW", lambda: choose(False))

    _center_over_parent(dialog, parent)
    dialog.wait_window()
    return result["value"]


def show_info(parent: ctk.CTk, title: str, message: str) -> None:
    _show_dialog(parent, title, message, "info")


def show_warning(parent: ctk.CTk, title: str, message: str) -> None:
    _show_dialog(parent, title, message, "warning")


def show_error(parent: ctk.CTk, title: str, message: str) -> None:
    _show_dialog(parent, title, message, "error")


def ask_yes_no(parent: ctk.CTk, title: str, message: str) -> bool:
    return _ask_dialog(parent, title, message)
