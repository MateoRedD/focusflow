import customtkinter as ctk

import database
import theme


def show_settings(parent: ctk.CTk, db_path, on_save, on_theme_change=None) -> None:
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Ajustes")
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

    ctk.CTkLabel(
        inner,
        text="Ajustes",
        font=(theme.FONT, 20, "bold"),
        text_color=theme.TEXT,
    ).pack(anchor="w", pady=(0, 16))

    dark_row = ctk.CTkFrame(inner, fg_color="transparent")
    dark_row.pack(fill="x", pady=(0, 18))

    dark_var = ctk.BooleanVar(value=database.get_dark_mode(db_path))

    def on_dark_toggle() -> None:
        database.set_dark_mode(dark_var.get(), db_path)
        if on_theme_change:
            on_theme_change()

    ctk.CTkLabel(
        dark_row,
        text="Modo oscuro / Dark mode",
        font=(theme.FONT, 13, "bold"),
        text_color=theme.TEXT,
    ).pack(side="left")

    ctk.CTkSwitch(
        dark_row,
        text="",
        variable=dark_var,
        command=on_dark_toggle,
        width=46,
        progress_color=theme.PRIMARY,
        button_color=theme.TEXT_MUTED,
        button_hover_color=theme.TEXT,
        fg_color=theme.INPUT,
    ).pack(side="right")

    goal_var = ctk.StringVar(value=str(database.get_weekly_goal_hours(db_path)))
    idle_var = ctk.StringVar(value=str(database.get_inactivity_minutes(db_path)))

    ctk.CTkLabel(
        inner,
        text="Meta semanal (horas)",
        font=(theme.FONT, 12),
        text_color=theme.TEXT_MUTED,
    ).pack(anchor="w", pady=(0, 4))
    goal_entry = ctk.CTkEntry(
        inner,
        textvariable=goal_var,
        width=280,
        height=40,
        corner_radius=10,
        fg_color=theme.INPUT,
        border_color=theme.CARD_BORDER,
        text_color=theme.TEXT,
    )
    goal_entry.pack(anchor="w", pady=(0, 14))

    ctk.CTkLabel(
        inner,
        text="Auto-pausa por inactividad (minutos)",
        font=(theme.FONT, 12),
        text_color=theme.TEXT_MUTED,
    ).pack(anchor="w", pady=(0, 4))
    idle_entry = ctk.CTkEntry(
        inner,
        textvariable=idle_var,
        width=280,
        height=40,
        corner_radius=10,
        fg_color=theme.INPUT,
        border_color=theme.CARD_BORDER,
        text_color=theme.TEXT,
    )
    idle_entry.pack(anchor="w", pady=(0, 20))

    buttons = ctk.CTkFrame(inner, fg_color="transparent")
    buttons.pack(fill="x")

    def close() -> None:
        dialog.grab_release()
        dialog.destroy()

    def save() -> None:
        try:
            goal = max(0.5, float(goal_var.get().replace(",", ".")))
            idle = max(1, int(idle_var.get()))
        except ValueError:
            return
        database.set_setting("weekly_goal_hours", str(goal), db_path)
        database.set_setting("inactivity_minutes", str(idle), db_path)
        on_save()
        close()

    ctk.CTkButton(
        buttons,
        text="Cancelar",
        width=100,
        height=38,
        corner_radius=12,
        fg_color=theme.INPUT,
        hover_color=theme.CARD_BORDER,
        text_color=theme.TEXT,
        command=close,
    ).pack(side="right", padx=(8, 0))

    ctk.CTkButton(
        buttons,
        text="Guardar",
        width=100,
        height=38,
        corner_radius=12,
        fg_color=theme.PRIMARY,
        hover_color=theme.PRIMARY_HOVER,
        text_color=theme.TEXT_ON_PRIMARY,
        command=save,
    ).pack(side="right")

    dialog.bind("<Escape>", lambda _e: close())
    dialog.protocol("WM_DELETE_WINDOW", close)

    dialog.update_idletasks()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    dialog.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")
