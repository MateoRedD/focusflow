import tkinter as tk
from datetime import date, timedelta

import customtkinter as ctk

import database
import icons
import settings_ui
import theme

DAY_LABELS = ["L", "M", "X", "J", "V", "S", "D"]

SESSION_TABLE_COLUMNS = (
    ("Día", 72),
    ("Materia", 0),
    ("Duración", 92),
    ("Nota", 0),
)


def _draw_rounded_rect(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    radius: int,
    fill: str,
) -> None:
    width = x1 - x0
    height = y1 - y0
    if width <= 0 or height <= 0:
        return
    r = min(radius, int(width // 2), int(height // 2))
    if r < 1:
        canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="", width=0)
        return
    canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill=fill, outline="", width=0)
    canvas.create_rectangle(x0, y0 + r, x1, y1 - r, fill=fill, outline="", width=0)
    canvas.create_arc(
        x0, y0, x0 + 2 * r, y0 + 2 * r,
        start=90, extent=90, style="pieslice", fill=fill, outline=fill,
    )
    canvas.create_arc(
        x1 - 2 * r, y0, x1, y0 + 2 * r,
        start=0, extent=90, style="pieslice", fill=fill, outline=fill,
    )
    canvas.create_arc(
        x0, y1 - 2 * r, x0 + 2 * r, y1,
        start=180, extent=90, style="pieslice", fill=fill, outline=fill,
    )
    canvas.create_arc(
        x1 - 2 * r, y1 - 2 * r, x1, y1,
        start=270, extent=90, style="pieslice", fill=fill, outline=fill,
    )


def _draw_rounded_top_bar(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    radius: int,
    fill: str,
) -> None:
    """Draw a bar with rounded top corners."""
    height = y1 - y0
    width = x1 - x0
    if height <= 1 or width <= 1:
        return
    r = min(radius, int(width // 2), int(height // 2))
    if r < 1:
        canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="", width=0)
        return
    canvas.create_rectangle(x0, y0 + r, x1, y1, fill=fill, outline="", width=0)
    canvas.create_rectangle(x0 + r, y0, x1 - r, y0 + r, fill=fill, outline="", width=0)
    canvas.create_arc(
        x0, y0, x0 + 2 * r, y0 + 2 * r,
        start=90, extent=90, style="pieslice", fill=fill, outline=fill,
    )
    canvas.create_arc(
        x1 - 2 * r, y0, x1, y0 + 2 * r,
        start=0, extent=90, style="pieslice", fill=fill, outline=fill,
    )


class DashboardUI(ctk.CTk):
    def __init__(self, app) -> None:
        super().__init__()
        self.app = app
        self._current_view = "dashboard"

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title(f"{theme.APP_NAME} — {theme.APP_SUBTITLE}")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=theme.BG)

        self.subject_var = ctk.StringVar()
        self.note_var = ctk.StringVar()
        self.timer_var = ctk.StringVar(value="00:00:00")
        self.status_var = ctk.StringVar(value="Sin sesión activa")
        self.week_total_var = ctk.StringVar(value="0h 0min")
        self.streak_var = ctk.StringVar(value="🔥 0 días seguidos")
        self.goal_var = ctk.StringVar(value="0h 0min / 10h  (0%)")

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._heatmap_tip: tk.Toplevel | None = None
        self._stats_expanded_day: int | None = None
        self._stats_week_offset = 0
        self._session_btn_styles: dict[str, dict] = {}
        self._heatmap_drawing = False
        self._layout_resize_job: str | None = None
        self._heatmap_retry_count = 0
        self._card_wraps: list[ctk.CTkFrame] = []
        self._heatmap_card_frames: list[tuple[ctk.CTkFrame, ctk.CTkFrame]] = []
        self._heatmap_legend_swatches: list[tuple[ctk.CTkFrame, str]] = []
        self._heatmap_legend_labels: list[ctk.CTkLabel] = []
        self._heatmap_col_wrappers: list[ctk.CTkFrame] = []
        self._body_labels: list[ctk.CTkLabel] = []
        self._build_layout()
        self.apply_theme()
        icons.install_window_icon(self, active=self.app.is_active)
        self.protocol("WM_DELETE_WINDOW", self.app.hide_window)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self) -> None:
        self._sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=theme.SIDEBAR)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=24, pady=(28, 32))
        self._brand_title = ctk.CTkLabel(
            brand,
            text=theme.APP_NAME,
            font=(theme.FONT, 22, "bold"),
            text_color=theme.PRIMARY,
        )
        self._brand_title.pack(anchor="w")
        self._brand_subtitle = ctk.CTkLabel(
            brand,
            text=theme.APP_SUBTITLE,
            font=(theme.FONT, 12),
            text_color=theme.TEXT_MUTED,
        )
        self._brand_subtitle.pack(anchor="w", pady=(2, 0))

        nav_items = [
            ("dashboard", "Dashboard", "◉"),
            ("stats", "Estadísticas", "▤"),
            ("settings", "Ajustes", "⚙"),
        ]
        for key, label, icon in nav_items:
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=42,
                corner_radius=10,
                fg_color=theme.SIDEBAR,
                hover_color=theme.NAV_ACTIVE,
                text_color=theme.TEXT_MUTED,
                font=(theme.FONT, 14),
                command=lambda k=key: self._switch_view(k),
            )
            btn.pack(fill="x", padx=16, pady=4)
            self._nav_buttons[key] = btn

        self._quick_start_btn = ctk.CTkButton(
            self._sidebar,
            text="Inicio rápido",
            height=44,
            corner_radius=12,
            fg_color=theme.PRIMARY,
            hover_color=theme.PRIMARY_HOVER,
            text_color=theme.TEXT_ON_PRIMARY,
            font=(theme.FONT, 14, "bold"),
            command=self.app.quick_start_from_ui,
        )
        self._quick_start_btn.pack(side="bottom", fill="x", padx=16, pady=(0, 6))

        self._shortcuts_label = ctk.CTkLabel(
            self._sidebar,
            text="Ctrl+Shift+Q  inicio rápido\nCtrl+Shift+P  pausar\nCtrl+Shift+D  detener",
            font=(theme.FONT, 10),
            text_color=theme.TEXT_DIM,
            justify="left",
        )
        self._shortcuts_label.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        self._highlight_nav("dashboard")

    def _track_label(self, label: ctk.CTkLabel) -> ctk.CTkLabel:
        self._body_labels.append(label)
        return label

    def setup_shortcuts(self) -> None:
        shortcuts = {
            "<Control-Shift-q>": self.app.quick_start_from_ui,
            "<Control-Shift-Q>": self.app.quick_start_from_ui,
            "<Control-Shift-p>": self.app.toggle_pause_from_ui,
            "<Control-Shift-P>": self.app.toggle_pause_from_ui,
            "<Control-Shift-d>": self.app.stop_from_ui,
            "<Control-Shift-D>": self.app.stop_from_ui,
        }
        for sequence, action in shortcuts.items():
            self.bind_all(sequence, lambda _e, fn=action: self._run_shortcut(fn))

    def _run_shortcut(self, action) -> str:
        action()
        return "break"

    def _build_main(self) -> None:
        self.main = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self._build_header()

        self.content_scroll = ctk.CTkScrollableFrame(
            self.main,
            fg_color=theme.BG,
            scrollbar_fg_color=theme.CARD,
            scrollbar_button_color=theme.INPUT,
            scrollbar_button_hover_color=theme.CARD_BORDER,
        )
        self.content_scroll.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
        self.content = self.content_scroll

        self._build_timer_card()
        self._build_week_card()
        self._build_sessions_card()
        self._build_stats_panel()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.main, fg_color="transparent", height=72)
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(20, 8))
        header.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        self._streak_label = ctk.CTkLabel(
            left,
            textvariable=self.streak_var,
            font=(theme.FONT, 15, "bold"),
            text_color=theme.PRIMARY,
        )
        self._streak_label.pack(anchor="w")

        goal_frame = ctk.CTkFrame(left, fg_color="transparent")
        goal_frame.pack(anchor="w", pady=(6, 0), fill="x")

        self.goal_bar = ctk.CTkProgressBar(
            goal_frame,
            width=220,
            height=12,
            corner_radius=6,
            fg_color=theme.INPUT,
            progress_color=theme.PRIMARY,
            border_width=0,
        )
        self.goal_bar.pack(side="left")
        self.goal_bar.set(0)

        self._goal_label = ctk.CTkLabel(
            goal_frame,
            textvariable=self.goal_var,
            font=(theme.FONT, 11),
            text_color=theme.TEXT_MUTED,
        )
        self._goal_label.pack(side="left", padx=(10, 0))

        self.start_btn = ctk.CTkButton(
            header,
            text="▶  Iniciar sesión",
            width=140,
            height=40,
            corner_radius=12,
            fg_color=theme.PRIMARY,
            hover_color=theme.PRIMARY_HOVER,
            text_color=theme.TEXT_ON_PRIMARY,
            font=(theme.FONT, 13, "bold"),
            command=self.app.start_from_ui,
        )
        self.start_btn.grid(row=0, column=1, padx=(0, 8))

        self.pause_btn = ctk.CTkButton(
            header,
            text="⏸  Pausar",
            width=110,
            height=40,
            corner_radius=12,
            fg_color=theme.PAUSE_BG,
            hover_color=theme.INPUT,
            text_color=theme.PAUSE_TEXT,
            font=(theme.FONT, 13, "bold"),
            command=self.app.pause_from_ui,
        )
        self.pause_btn.grid(row=0, column=2, padx=(0, 8))
        self._session_btn_styles["pause"] = {
            "fg_color": theme.PAUSE_BG,
            "hover_color": theme.INPUT,
            "text_color": theme.PAUSE_TEXT,
        }

        self.resume_btn = ctk.CTkButton(
            header,
            text="▶  Reanudar",
            width=120,
            height=40,
            corner_radius=12,
            fg_color=theme.SECONDARY,
            hover_color=theme.SECONDARY_HOVER,
            text_color=theme.TEXT_ON_PRIMARY,
            font=(theme.FONT, 13, "bold"),
            command=self.app.resume_from_ui,
        )
        self.resume_btn.grid(row=0, column=3, padx=(0, 8))
        self._session_btn_styles["resume"] = {
            "fg_color": theme.SECONDARY,
            "hover_color": theme.SECONDARY_HOVER,
            "text_color": theme.TEXT_ON_PRIMARY,
        }

        self.stop_btn = ctk.CTkButton(
            header,
            text="■  Detener",
            width=110,
            height=40,
            corner_radius=12,
            fg_color=theme.SUCCESS_BG,
            hover_color=theme.SUCCESS_HOVER,
            text_color=theme.SUCCESS,
            font=(theme.FONT, 13, "bold"),
            command=self.app.stop_from_ui,
        )
        self.stop_btn.grid(row=0, column=4)
        self._session_btn_styles["stop"] = {
            "fg_color": theme.SUCCESS_BG,
            "hover_color": theme.SUCCESS_HOVER,
            "text_color": theme.SUCCESS,
        }

    def _create_card(
        self,
        parent,
        *,
        fill_height: bool = False,
        pady: tuple[int, int] = (0, 12),
    ) -> tuple[ctk.CTkFrame, ctk.CTkFrame]:
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(
            fill="both" if fill_height else "x",
            anchor="nw",
            pady=pady,
            expand=fill_height,
        )

        shadow = ctk.CTkFrame(
            wrapper,
            fg_color=theme.CARD_SHADOW,
            corner_radius=17,
        )
        shadow.pack(fill="both" if fill_height else "x", expand=fill_height)

        card = ctk.CTkFrame(
            shadow,
            corner_radius=16,
            fg_color=theme.CARD,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        card.pack(
            fill="both" if fill_height else "x",
            expand=fill_height,
            padx=(0, 2),
            pady=(0, 3),
        )
        self._card_wraps.append(wrapper)
        return wrapper, card

    def _style_action_button(self, button: ctk.CTkButton, enabled_style: dict, enabled: bool) -> None:
        if enabled:
            button.configure(
                state="normal",
                border_width=0,
                border_color=enabled_style["fg_color"],
                **enabled_style,
            )
        else:
            button.configure(
                state="disabled",
                fg_color=theme.BTN_DISABLED_BG,
                hover_color=theme.BTN_DISABLED_BG,
                text_color=theme.BTN_DISABLED_TEXT,
                border_width=1,
                border_color=theme.BTN_DISABLED_BORDER,
            )

    def _build_timer_card(self) -> None:
        self.timer_card_wrap, self.timer_card = self._create_card(self.content)

        inner = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=28)

        self._timer_display_label = self._track_label(ctk.CTkLabel(
            inner,
            textvariable=self.timer_var,
            font=(theme.FONT_MONO, 52, "bold"),
            text_color=theme.TEXT,
        ))
        self._timer_display_label.pack(pady=(8, 12))

        self.status_badge = ctk.CTkLabel(
            inner,
            textvariable=self.status_var,
            font=(theme.FONT, 13),
            text_color=theme.TEXT_MUTED,
            fg_color=theme.INPUT,
            corner_radius=20,
            padx=16,
            pady=6,
        )
        self.status_badge.pack(pady=(0, 24))

        form = ctk.CTkFrame(inner, fg_color="transparent")
        form.pack(fill="x")
        form.grid_columnconfigure(1, weight=1)

        self._track_label(ctk.CTkLabel(form, text="Materia", font=(theme.FONT, 12), text_color=theme.TEXT_MUTED)).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.subject_entry = ctk.CTkEntry(
            form,
            textvariable=self.subject_var,
            height=40,
            corner_radius=10,
            fg_color=theme.INPUT,
            border_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
            placeholder_text="Ej. Cálculo, Python...",
            font=(theme.FONT, 13),
        )
        self.subject_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self._track_label(ctk.CTkLabel(form, text="Nota rápida", font=(theme.FONT, 12), text_color=theme.TEXT_MUTED)).grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        self.note_entry = ctk.CTkEntry(
            form,
            textvariable=self.note_var,
            height=40,
            corner_radius=10,
            fg_color=theme.INPUT,
            border_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
            placeholder_text="¿Qué vas a estudiar?",
            font=(theme.FONT, 13),
        )
        self.note_entry.grid(row=3, column=0, columnspan=2, sticky="ew")

    def _build_week_card(self) -> None:
        self.week_card_wrap, self.week_card = self._create_card(self.content)

        inner = ctk.CTkFrame(self.week_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        self._track_label(ctk.CTkLabel(
            inner,
            text="Esta semana",
            font=(theme.FONT, 16, "bold"),
            text_color=theme.TEXT,
        )).pack(anchor="w")

        self._track_label(ctk.CTkLabel(
            inner,
            textvariable=self.week_total_var,
            font=(theme.FONT, 36, "bold"),
            text_color=theme.TEXT,
        )).pack(anchor="w", pady=(8, 20))

        self.chart_frame = ctk.CTkFrame(inner, fg_color="transparent", height=120)
        self.chart_frame.pack(fill="x", expand=False)
        self.chart_frame.pack_propagate(False)
        self.chart_canvas = tk.Canvas(
            self.chart_frame,
            height=100,
            bg=theme.CARD,
            highlightthickness=0,
            bd=0,
        )
        self.chart_canvas.pack(fill="x", expand=True)
        self.chart_canvas.bind("<Configure>", lambda _e: self.refresh_week_chart())

        ctk.CTkButton(
            inner,
            text="Ver estadísticas detalladas",
            height=36,
            corner_radius=10,
            fg_color=theme.INPUT,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
            font=(theme.FONT, 12),
            command=lambda: self._switch_view("stats"),
        ).pack(fill="x", pady=(16, 0))

    def _build_sessions_card(self) -> None:
        self.sessions_card_wrap, self.sessions_card = self._create_card(
            self.content,
            pady=(0, 0),
        )

        inner = ctk.CTkFrame(
            self.sessions_card,
            fg_color=theme.SESSIONS_BG,
            corner_radius=12,
        )
        self._sessions_inner = inner
        inner.pack(fill="x", padx=14, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        self._track_label(ctk.CTkLabel(
            inner,
            text="Sesiones recientes",
            font=(theme.FONT, 16, "bold"),
            text_color=theme.TEXT,
        )).grid(row=0, column=0, sticky="w", pady=(0, 10))

        headers = ctk.CTkFrame(inner, fg_color="transparent")
        headers.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self._configure_session_table_columns(headers)
        for i, (title, _) in enumerate(SESSION_TABLE_COLUMNS):
            self._track_label(ctk.CTkLabel(
                headers,
                text=title,
                font=(theme.FONT, 11, "bold"),
                text_color=theme.TEXT_DIM,
                anchor="w",
            )).grid(row=0, column=i, sticky="ew", padx=6)

        self.sessions_list = ctk.CTkFrame(
            inner,
            fg_color=theme.SESSIONS_BG,
        )
        self.sessions_list.grid(row=2, column=0, sticky="ew", pady=(0, 4))

    def _build_stats_panel(self) -> None:
        self.stats_panel_wrap, self.stats_panel = self._create_card(
            self.content,
            pady=(0, 0),
        )
        self.stats_panel_wrap.pack_forget()

        self.stats_body = ctk.CTkFrame(self.stats_panel, fg_color=theme.BG)
        self.stats_body.pack(fill="x", padx=8, pady=8)

        self._heatmap_section = ctk.CTkFrame(self.stats_body, fg_color=theme.BG)
        self._heatmap_section.pack(fill="x", anchor="nw", pady=(0, 12))

        self._heatmap_activity_label = self._track_label(ctk.CTkLabel(
            self._heatmap_section,
            text="Actividad mensual",
            font=(theme.FONT, 16, "bold"),
            text_color=theme.TEXT,
        ))
        self._heatmap_activity_label.pack(anchor="w", pady=(0, 8))

        self._heatmap_legend = ctk.CTkFrame(self._heatmap_section, fg_color=theme.BG)
        self._heatmap_legend.pack(anchor="w", pady=(0, 12))
        for label, color_key in [
            ("0h", "HEAT_EMPTY"),
            ("1–2h", "HEAT_LOW"),
            ("2–4h", "HEAT_MED"),
            ("4h+", "HEAT_HIGH"),
        ]:
            item = ctk.CTkFrame(self._heatmap_legend, fg_color=theme.BG)
            item.pack(side="left", padx=(0, 14))
            swatch = ctk.CTkFrame(
                item,
                width=16,
                height=16,
                corner_radius=4,
                fg_color=getattr(theme, color_key),
            )
            swatch.pack(side="left", padx=(0, 6))
            swatch.pack_propagate(False)
            self._heatmap_legend_swatches.append((swatch, color_key))
            self._heatmap_legend_labels.append(self._track_label(ctk.CTkLabel(
                item,
                text=label,
                font=(theme.FONT, 10),
                text_color=theme.TEXT,
            )))
            self._heatmap_legend_labels[-1].pack(side="left")

        self.heatmap_row = ctk.CTkFrame(self._heatmap_section, fg_color=theme.BG)
        self.heatmap_row.pack(fill="x", expand=False)
        half_gap = theme.HEAT_MONTH_GAP // 2
        for col in range(3):
            self.heatmap_row.grid_columnconfigure(col, weight=1, uniform="heatmap_month")
        self.heatmap_row.grid_rowconfigure(0, weight=0)

        self.heatmap_months: list[tuple[ctk.CTkLabel, tk.Canvas]] = []
        for col in range(3):
            col_wrapper = ctk.CTkFrame(self.heatmap_row, fg_color=theme.BG)
            self._heatmap_col_wrappers.append(col_wrapper)
            if col == 0:
                padx = (0, half_gap)
            elif col == 2:
                padx = (half_gap, 0)
            else:
                padx = (half_gap, half_gap)
            col_wrapper.grid(row=0, column=col, sticky="nsew", padx=padx)

            title = self._track_label(ctk.CTkLabel(
                col_wrapper,
                text="",
                font=(theme.FONT, 14, "bold"),
                text_color=theme.TEXT,
            ))
            title.pack(anchor="w", pady=(0, 10))

            shadow = ctk.CTkFrame(
                col_wrapper,
                fg_color=theme.HEAT_CARD_SHADOW,
                corner_radius=13,
            )
            shadow.pack(fill="x", expand=False)

            card = ctk.CTkFrame(
                shadow,
                fg_color=theme.CARD,
                corner_radius=12,
                border_width=1,
                border_color=theme.CARD_BORDER,
            )
            card.pack(fill="x", padx=(0, 2), pady=(0, 3))
            self._heatmap_card_frames.append((shadow, card))

            card_inner = ctk.CTkFrame(card, fg_color=theme.CARD)
            card_inner.pack(fill="x", padx=theme.HEAT_CARD_PAD, pady=theme.HEAT_CARD_PAD)

            canvas = tk.Canvas(
                card_inner,
                height=120,
                bg=theme.CARD,
                highlightthickness=0,
                bd=0,
            )
            canvas.pack(fill="x", expand=False)
            canvas.bind("<Leave>", lambda _e: self._hide_heatmap_tip())
            self.heatmap_months.append((title, canvas))

        self.main.bind("<Configure>", self._on_window_resize)

        self._breakdown_shadow = ctk.CTkFrame(
            self.stats_body,
            fg_color=theme.CARD_SHADOW,
            corner_radius=13,
        )
        self._breakdown_shadow.pack(fill="x", anchor="nw", pady=(0, 8))

        self.week_breakdown_card = ctk.CTkFrame(
            self._breakdown_shadow,
            fg_color=theme.CARD,
            corner_radius=12,
            border_width=1,
            border_color=theme.CARD_BORDER,
        )
        self.week_breakdown_card.pack(fill="x", padx=(0, 2), pady=(0, 3))

        breakdown_header = ctk.CTkFrame(self.week_breakdown_card, fg_color="transparent")
        breakdown_header.pack(fill="x", padx=16, pady=(14, 6))

        self._desglose_title = self._track_label(ctk.CTkLabel(
            breakdown_header,
            text="Desglose semanal",
            font=(theme.FONT, 16, "bold"),
            text_color=theme.TEXT,
        ))
        self._desglose_title.pack(anchor="w", pady=(0, 8))

        nav_row = ctk.CTkFrame(breakdown_header, fg_color="transparent")
        nav_row.pack(fill="x")

        self.week_prev_btn = ctk.CTkButton(
            nav_row,
            text="← Anterior",
            width=100,
            height=32,
            corner_radius=10,
            fg_color=theme.INPUT,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
            font=(theme.FONT, 12),
            command=self._stats_prev_week,
        )
        self.week_prev_btn.pack(side="left")

        center = ctk.CTkFrame(nav_row, fg_color="transparent")
        center.pack(side="left", expand=True, fill="x", padx=8)

        self.week_range_var = ctk.StringVar(value="")
        self.week_total_label_var = ctk.StringVar(value="")
        self._week_range_label = self._track_label(ctk.CTkLabel(
            center,
            textvariable=self.week_range_var,
            font=(theme.FONT, 11),
            text_color=theme.TEXT,
        ))
        self._week_range_label.pack(anchor="center")
        self._week_total_label = self._track_label(ctk.CTkLabel(
            center,
            textvariable=self.week_total_label_var,
            font=(theme.FONT, 13, "bold"),
            text_color=theme.TEXT,
        ))
        self._week_total_label.pack(anchor="center")

        self.week_next_btn = ctk.CTkButton(
            nav_row,
            text="Siguiente →",
            width=100,
            height=32,
            corner_radius=10,
            fg_color=theme.INPUT,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
            font=(theme.FONT, 12),
            command=self._stats_next_week,
        )
        self.week_next_btn.pack(side="right")

        self.week_accordion = ctk.CTkFrame(
            self.week_breakdown_card,
            fg_color="transparent",
        )
        self.week_accordion.pack(fill="x", padx=16, pady=(4, 16))

    def _configure_session_table_columns(self, frame: ctk.CTkFrame) -> None:
        for i, (_, width) in enumerate(SESSION_TABLE_COLUMNS):
            if width > 0:
                frame.grid_columnconfigure(i, minsize=width, weight=0)
            elif i == 1:
                frame.grid_columnconfigure(i, weight=3)
            else:
                frame.grid_columnconfigure(i, weight=1)

    def _on_window_resize(self, event=None) -> None:
        if event is not None and event.widget is not self.main:
            return
        if self._layout_resize_job is not None:
            self.after_cancel(self._layout_resize_job)
        if self._current_view == "stats":
            self._layout_resize_job = self.after(150, self._debounced_stats_resize)

    def _debounced_stats_resize(self) -> None:
        self._layout_resize_job = None
        if self._current_view != "stats":
            return
        self.refresh_heatmap()

    def _heatmap_max_height(self) -> int:
        rows = 7
        gap = theme.HEAT_CELL_GAP
        min_h = 8 + rows * (theme.HEAT_CELL_MIN + gap) + 8
        return max(min_h, min(240, self.winfo_height() // 4))

    def _heatmap_layout_metrics(self) -> tuple[int, int, int, int, int, int]:
        return (
            theme.HEAT_CELL_GAP,
            7,
            8,
            18,
            4,
            8,
        )

    def _compute_shared_heatmap_cell(
        self,
        canvases: list[tk.Canvas],
        datasets: list[list[tuple[date, int]]],
        max_height: int,
    ) -> int | None:
        gap, rows, start_y, label_w, left_pad, bottom_pad = self._heatmap_layout_metrics()

        widths = [canvas.winfo_width() for canvas in canvases if canvas.winfo_width() > 1]
        if not widths or not datasets:
            return None

        width = min(widths)
        max_cols = max(self._heatmap_col_count(data) for data in datasets)
        grid_start_x = left_pad + label_w
        available_w = width - grid_start_x - left_pad
        cell_by_width = (available_w - (max_cols - 1) * gap) // max_cols if max_cols else 16
        cell_by_height = (max_height - start_y - bottom_pad - (rows - 1) * gap) // rows
        return max(theme.HEAT_CELL_MIN, min(cell_by_width, cell_by_height, theme.HEAT_CELL_MAX))

    def _heatmap_month_triplet(self, today: date | None = None) -> list[tuple[int, int]]:
        today = today or date.today()
        first_of_month = today.replace(day=1)
        prev_day = first_of_month - timedelta(days=1)
        if today.month == 12:
            next_year, next_month = today.year + 1, 1
        else:
            next_year, next_month = today.year, today.month + 1
        return [
            (prev_day.year, prev_day.month),
            (today.year, today.month),
            (next_year, next_month),
        ]

    def _heatmap_col_count(self, data: list[tuple[date, int]]) -> int:
        if not data:
            return 0
        start_offset = data[0][0].weekday()
        return (len(data) - 1 + start_offset) // 7 + 1

    def _draw_heatmap_on_canvas(
        self,
        canvas: tk.Canvas,
        data: list[tuple[date, int]],
        *,
        show_day_labels: bool = True,
        max_height: int | None = None,
        cell: int | None = None,
    ) -> None:
        canvas.delete("all")
        if not data:
            return

        canvas.configure(bg=theme.CARD)

        gap, rows, start_y, base_label_w, left_pad, bottom_pad = self._heatmap_layout_metrics()
        radius = theme.HEAT_CELL_RADIUS
        label_w = base_label_w if show_day_labels else 0

        start_date = data[0][0]
        start_offset = start_date.weekday()
        cols = (len(data) - 1 + start_offset) // 7 + 1

        canvas.update_idletasks()
        width = canvas.winfo_width()
        if width <= 1:
            return

        width = max(width, 80)
        if max_height is None:
            max_height = start_y + rows * (theme.HEAT_CELL_MIN + gap) + bottom_pad

        available_w = width - left_pad - label_w - left_pad
        if cell is None:
            cell_by_width = (available_w - (cols - 1) * gap) // cols if cols else theme.HEAT_CELL_MIN
            cell_by_height = (max_height - start_y - bottom_pad - (rows - 1) * gap) // rows
            cell = max(
                theme.HEAT_CELL_MIN,
                min(cell_by_width, cell_by_height, theme.HEAT_CELL_MAX),
            )

        grid_width = cols * cell + (cols - 1) * gap
        if show_day_labels:
            grid_start_x = left_pad + label_w
        else:
            grid_start_x = left_pad + max(0, (width - left_pad * 2 - grid_width) // 2)

        canvas_h = start_y + rows * (cell + gap) + bottom_pad
        if canvas.winfo_height() != canvas_h:
            canvas.configure(height=canvas_h)

        for index, (day, seconds) in enumerate(data):
            week = (index + start_offset) // 7
            row = day.weekday()
            x0 = grid_start_x + week * (cell + gap)
            y0 = start_y + row * (cell + gap)
            x1 = x0 + cell
            y1 = y0 + cell
            color = database.heatmap_color(seconds)
            tag = f"cell-{day.isoformat()}-{id(canvas)}"

            _draw_rounded_rect(canvas, x0, y0, x1, y1, radius, color)
            tip = database.format_day_tooltip(day, seconds)
            canvas.create_rectangle(
                x0, y0, x1, y1, fill="", outline="", width=0, tags=(tag,),
            )
            canvas.tag_bind(
                tag, "<Enter>",
                lambda _e, t=tip, cx=x0, cy=y0, c=canvas: self._show_heatmap_tip(t, cx, cy, c),
            )
            canvas.tag_bind(tag, "<Leave>", lambda _e: self._hide_heatmap_tip())

        if show_day_labels:
            for i, label in enumerate(["L", "M", "X", "J", "V", "S", "D"]):
                canvas.create_text(
                    left_pad,
                    start_y + i * (cell + gap) + cell / 2,
                    text=label,
                    fill=theme.HEAT_LABEL,
                    font=(theme.FONT, 9, "bold"),
                    anchor="w",
                )

    def _switch_view(self, view: str) -> None:
        if view == "settings":
            settings_ui.show_settings(
                self,
                self.app.db_path,
                on_save=self.refresh_all,
                on_theme_change=self.apply_theme,
            )
            return

        self._current_view = view
        self._highlight_nav(view)
        if view == "dashboard":
            self._show_dashboard_view()
        else:
            self._show_stats_view()

    def _show_dashboard_view(self) -> None:
        self.stats_panel_wrap.pack_forget()
        self.timer_card_wrap.pack(fill="x", anchor="nw", pady=(0, 12))
        self.week_card_wrap.pack(fill="x", anchor="nw", pady=(0, 12))
        self.sessions_card_wrap.pack(fill="x", anchor="nw", pady=(0, 0))

    def _show_stats_view(self) -> None:
        self._heatmap_retry_count = 0
        self.timer_card_wrap.pack_forget()
        self.week_card_wrap.pack_forget()
        self.sessions_card_wrap.pack_forget()
        self.stats_panel_wrap.pack(fill="x", anchor="nw", pady=(0, 0))
        self._stats_week_offset = 0
        self._stats_expanded_day = None
        self.after_idle(self.refresh_stats_panel)

    def _highlight_nav(self, active: str) -> None:
        for key, btn in self._nav_buttons.items():
            if key == active:
                btn.configure(fg_color=theme.NAV_ACTIVE, text_color=theme.NAV_ACTIVE_TEXT)
            else:
                btn.configure(fg_color=theme.SIDEBAR, text_color=theme.TEXT_MUTED)

    def _sync_scrollable_frame_theme(self) -> None:
        self.content_scroll.configure(
            fg_color=theme.BG,
            scrollbar_fg_color=theme.CARD,
            scrollbar_button_color=theme.INPUT,
            scrollbar_button_hover_color=theme.CARD_BORDER,
        )
        try:
            canvas = self.content_scroll._parent_canvas
            canvas.configure(bg=theme.BG, highlightthickness=0)
            self.content_scroll._scrollable_frame.configure(fg_color=theme.BG)
        except (AttributeError, tk.TclError):
            pass

    def _apply_stats_theme(self) -> None:
        if self.stats_panel_wrap.winfo_children():
            stats_shadow = self.stats_panel_wrap.winfo_children()[0]
            stats_shadow.configure(fg_color=theme.BG)
        self.stats_panel.configure(fg_color=theme.BG, border_color=theme.BG)
        self.stats_body.configure(fg_color=theme.BG)
        self._heatmap_section.configure(fg_color=theme.BG)
        self._heatmap_legend.configure(fg_color=theme.BG)
        for legend_item in self._heatmap_legend.winfo_children():
            if isinstance(legend_item, ctk.CTkFrame):
                legend_item.configure(fg_color=theme.BG)
        self.heatmap_row.configure(fg_color=theme.BG)
        for col_wrapper in self._heatmap_col_wrappers:
            col_wrapper.configure(fg_color=theme.BG)
        self._heatmap_activity_label.configure(text_color=theme.TEXT)
        for lbl in self._heatmap_legend_labels:
            lbl.configure(text_color=theme.TEXT)
        for title, _canvas in self.heatmap_months:
            title.configure(text_color=theme.TEXT)
        for shadow, card in self._heatmap_card_frames:
            shadow.configure(fg_color=theme.HEAT_CARD_SHADOW)
            card.configure(fg_color=theme.CARD, border_color=theme.CARD_BORDER)
            for child in card.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    child.configure(fg_color=theme.CARD)
        for swatch, color_key in self._heatmap_legend_swatches:
            swatch.configure(fg_color=getattr(theme, color_key))
        for _title, canvas in self.heatmap_months:
            canvas.configure(bg=theme.CARD)
        self._breakdown_shadow.configure(fg_color=theme.CARD_SHADOW)
        self.week_breakdown_card.configure(fg_color=theme.CARD, border_color=theme.CARD_BORDER)
        self._desglose_title.configure(text_color=theme.TEXT)
        self._week_range_label.configure(text_color=theme.TEXT)
        self._week_total_label.configure(text_color=theme.TEXT)
        self.week_prev_btn.configure(
            fg_color=theme.INPUT,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
        )
        self.week_next_btn.configure(
            fg_color=theme.INPUT,
            hover_color=theme.CARD_BORDER,
            text_color=theme.TEXT,
        )

    def _apply_body_text_theme(self) -> None:
        muted = theme.TEXT if theme.is_dark() else theme.TEXT_MUTED
        dim = theme.TEXT if theme.is_dark() else theme.TEXT_DIM
        for label in self._body_labels:
            label.configure(text_color=theme.TEXT)
        self._brand_subtitle.configure(text_color=muted)
        self._shortcuts_label.configure(text_color=dim)
        self._goal_label.configure(text_color=muted)

    def apply_theme(self) -> None:
        self._hide_heatmap_tip()
        dark = database.get_dark_mode(self.app.db_path)
        theme.apply_theme("dark" if dark else "light")

        self.configure(fg_color=theme.BG)
        self._sidebar.configure(fg_color=theme.SIDEBAR)
        self.main.configure(fg_color=theme.BG)
        self._brand_title.configure(text_color=theme.PRIMARY)
        self._quick_start_btn.configure(
            fg_color=theme.PRIMARY,
            hover_color=theme.PRIMARY_HOVER,
            text_color=theme.TEXT_ON_PRIMARY,
        )
        self._streak_label.configure(text_color=theme.PRIMARY)
        self.goal_bar.configure(fg_color=theme.INPUT, progress_color=theme.PRIMARY)

        self.start_btn.configure(
            fg_color=theme.PRIMARY,
            hover_color=theme.PRIMARY_HOVER,
            text_color=theme.TEXT_ON_PRIMARY,
        )
        self.pause_btn.configure(
            fg_color=theme.PAUSE_BG,
            hover_color=theme.INPUT,
            text_color=theme.PAUSE_TEXT,
        )
        self.resume_btn.configure(
            fg_color=theme.SECONDARY,
            hover_color=theme.SECONDARY_HOVER,
            text_color=theme.TEXT_ON_PRIMARY,
        )
        self.stop_btn.configure(
            fg_color=theme.SUCCESS_BG,
            hover_color=theme.SUCCESS_HOVER,
            text_color=theme.SUCCESS,
        )
        self._session_btn_styles["pause"] = {
            "fg_color": theme.PAUSE_BG,
            "hover_color": theme.INPUT,
            "text_color": theme.PAUSE_TEXT,
        }
        self._session_btn_styles["resume"] = {
            "fg_color": theme.SECONDARY,
            "hover_color": theme.SECONDARY_HOVER,
            "text_color": theme.TEXT_ON_PRIMARY,
        }
        self._session_btn_styles["stop"] = {
            "fg_color": theme.SUCCESS_BG,
            "hover_color": theme.SUCCESS_HOVER,
            "text_color": theme.SUCCESS,
        }

        for wrap in self._card_wraps:
            if not wrap.winfo_children():
                continue
            shadow = wrap.winfo_children()[0]
            if not shadow.winfo_children():
                continue
            card = shadow.winfo_children()[0]
            shadow.configure(fg_color=theme.CARD_SHADOW)
            if card is self.stats_panel:
                card.configure(fg_color=theme.BG, border_color=theme.BG)
            else:
                card.configure(fg_color=theme.CARD, border_color=theme.CARD_BORDER)
            for child in card.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    child.configure(fg_color=theme.SESSIONS_BG if child is self._sessions_inner else theme.CARD)

        entry_style = {
            "fg_color": theme.INPUT,
            "border_color": theme.CARD_BORDER,
            "text_color": theme.TEXT,
        }
        self.subject_entry.configure(**entry_style)
        self.note_entry.configure(**entry_style)
        self.status_badge.configure(fg_color=theme.INPUT, text_color=theme.TEXT)
        self._sessions_inner.configure(fg_color=theme.SESSIONS_BG)
        self.sessions_list.configure(fg_color=theme.SESSIONS_BG)
        self.chart_canvas.configure(bg=theme.CARD)
        self._sync_scrollable_frame_theme()
        self._apply_stats_theme()
        self._apply_body_text_theme()

        nav_key = self._current_view if self._current_view in self._nav_buttons else "dashboard"
        self._highlight_nav(nav_key)
        self.refresh_goal_progress()
        self.refresh_week_chart()
        self.refresh_sessions()
        if self._current_view == "stats":
            self.refresh_stats_panel()
        self.update_session_controls()
        if self.app.is_active:
            self.update_timer_display(
                self.app.get_elapsed_seconds(),
                self.app.session_subject,
                True,
                self.app.is_paused,
            )

    def refresh_all(self) -> None:
        self.apply_theme()
        self.refresh_streak()

    def refresh_streak(self) -> None:
        streak = database.update_streak_cache(db_path=self.app.db_path)
        word = "día" if streak == 1 else "días"
        self.streak_var.set(f"🔥 {streak} {word} seguidos")

    def refresh_goal_progress(self) -> None:
        _, _, _, total_seconds = database.get_week_sessions(db_path=self.app.db_path)
        goal_hours = database.get_weekly_goal_hours(self.app.db_path)
        goal_seconds = max(1, int(goal_hours * 3600))
        progress = min(1.0, total_seconds / goal_seconds)
        self.goal_bar.set(progress)
        self.goal_var.set(database.format_goal_progress(total_seconds, goal_hours))

    def refresh_week_chart(self) -> None:
        totals = database.get_daily_totals(db_path=self.app.db_path)
        total_seconds = sum(totals)
        self.week_total_var.set(database.format_hours_minutes(total_seconds))

        canvas = self.chart_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 280)
        height = 100
        max_val = max(totals) if any(totals) else 1
        today_idx = date.today().weekday()
        bar_w = (width - 40) / 7

        for i, seconds in enumerate(totals):
            x0 = 20 + i * bar_w + 4
            x1 = 20 + (i + 1) * bar_w - 4
            bar_h = (seconds / max_val) * (height - 30) if seconds else 4
            y1 = height - 18
            y0 = y1 - bar_h
            if seconds:
                color = theme.CHART_BAR if i != today_idx else theme.CHART_BAR_TODAY
                _draw_rounded_top_bar(canvas, x0, y0, x1, y1, radius=5, fill=color)
            else:
                canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill=theme.CHART_EMPTY,
                    outline="",
                    width=0,
                )
            canvas.create_text(
                (x0 + x1) / 2,
                height - 6,
                text=DAY_LABELS[i],
                fill=theme.TEXT,
                font=(theme.FONT, 9),
            )

    def refresh_sessions(self) -> None:
        for widget in self.sessions_list.winfo_children():
            widget.destroy()

        sessions = database.get_recent_sessions(db_path=self.app.db_path)
        if not sessions:
            ctk.CTkLabel(
                self.sessions_list,
                text="Aún no hay sesiones registradas.",
                text_color=theme.TEXT,
                font=(theme.FONT, 13),
            ).pack(pady=20, padx=6)
            return

        colors = (
            [theme.TEXT, theme.TEXT, theme.TEXT, theme.TEXT]
            if theme.is_dark()
            else [theme.TEXT_MUTED, theme.TEXT, theme.SECONDARY, theme.TEXT_MUTED]
        )
        for session in sessions:
            row = ctk.CTkFrame(self.sessions_list, fg_color="transparent")
            row.pack(fill="x", pady=3)
            self._configure_session_table_columns(row)

            values = [
                session["day_label"],
                session["subject"],
                database.format_timer(session["duration_seconds"]),
                session["note"] or "—",
            ]
            for i, text in enumerate(values):
                ctk.CTkLabel(
                    row,
                    text=text,
                    font=(theme.FONT, 12),
                    text_color=colors[i],
                    anchor="w",
                ).grid(row=0, column=i, sticky="ew", padx=6)

    def _stats_reference_date(self) -> date:
        return date.today() - timedelta(weeks=self._stats_week_offset)

    def _stats_prev_week(self) -> None:
        self._stats_week_offset += 1
        self._stats_expanded_day = None
        self.refresh_week_accordion()

    def _stats_next_week(self) -> None:
        if self._stats_week_offset > 0:
            self._stats_week_offset -= 1
            self._stats_expanded_day = None
            self.refresh_week_accordion()

    def refresh_stats_panel(self) -> None:
        self.refresh_heatmap()
        self.refresh_week_accordion()

    def refresh_week_accordion(self) -> None:
        for widget in self.week_accordion.winfo_children():
            widget.destroy()

        monday, sunday, by_day, total_seconds = database.get_week_sessions(
            reference=self._stats_reference_date(),
            db_path=self.app.db_path,
        )
        day_names = theme.DAY_NAMES_ES

        self.week_range_var.set(
            f"{monday.strftime('%d/%m/%Y')} – {sunday.strftime('%d/%m/%Y')}"
        )
        self.week_total_label_var.set(
            f"Total: {database.format_hours_minutes(total_seconds)}"
        )

        if self._stats_week_offset == 0:
            self.week_next_btn.configure(state="disabled")
        else:
            self.week_next_btn.configure(state="normal")

        for offset in range(7):
            day = monday + timedelta(days=offset)
            sessions = by_day.get(day, [])
            day_total = sum(s["duration_seconds"] for s in sessions)
            is_expanded = self._stats_expanded_day == offset
            is_coral = offset % 2 == 0

            pill_bg = (
                theme.ACCORDION_CORAL_ACTIVE if is_expanded and is_coral
                else theme.ACCORDION_SAGE_ACTIVE if is_expanded
                else theme.ACCORDION_CORAL if is_coral
                else theme.ACCORDION_SAGE
            )
            accent = theme.TEXT

            block = ctk.CTkFrame(self.week_accordion, fg_color="transparent")
            block.pack(fill="x", pady=4)

            pill = ctk.CTkFrame(
                block,
                fg_color=pill_bg,
                corner_radius=12,
                border_width=1,
                border_color=theme.CARD_BORDER,
                height=44,
            )
            pill.pack(fill="x")
            pill.pack_propagate(False)

            ctk.CTkLabel(
                pill,
                text=f"{'▾' if is_expanded else '▸'}  {day_names[offset]}  ·  {day.strftime('%d/%m')}",
                font=(theme.FONT, 13, "bold"),
                text_color=theme.TEXT,
            ).pack(side="left", padx=14)

            ctk.CTkLabel(
                pill,
                text=database.format_hours_minutes(day_total),
                font=(theme.FONT, 13, "bold"),
                text_color=accent,
            ).pack(side="right", padx=14)

            self._bind_accordion_click(pill, offset)

            if is_expanded:
                body = ctk.CTkFrame(
                    block,
                    fg_color=theme.ACCORDION_ROW,
                    corner_radius=10,
                    border_width=1,
                    border_color=theme.CARD_BORDER,
                )
                body.pack(fill="x", padx=8, pady=(6, 0))

                if not sessions:
                    ctk.CTkLabel(
                        body,
                        text="Sin sesiones",
                        font=(theme.FONT, 12),
                        text_color=theme.TEXT,
                    ).pack(anchor="w", padx=14, pady=12)
                else:
                    for session in sessions:
                        row = ctk.CTkFrame(body, fg_color="transparent")
                        row.pack(fill="x", padx=14, pady=8)
                        row.grid_columnconfigure(0, weight=1)

                        ctk.CTkLabel(
                            row,
                            text=session["subject"],
                            font=(theme.FONT, 13, "bold"),
                            text_color=theme.TEXT,
                            anchor="w",
                        ).grid(row=0, column=0, sticky="w")

                        ctk.CTkLabel(
                            row,
                            text=database.format_duration(session["duration_seconds"]),
                            font=(theme.FONT, 12, "bold"),
                            text_color=theme.TEXT,
                        ).grid(row=0, column=1, sticky="e", padx=(8, 0))

                        if session["note"]:
                            ctk.CTkLabel(
                                row,
                                text=session["note"],
                                font=(theme.FONT, 11),
                                text_color=theme.TEXT,
                                anchor="w",
                                wraplength=480,
                            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _bind_accordion_click(self, widget: ctk.CTkFrame, offset: int) -> None:
        def on_click(_event=None) -> None:
            self._toggle_stats_day(offset)

        widget.bind("<Button-1>", on_click)
        widget.configure(cursor="hand2")
        for child in widget.winfo_children():
            if isinstance(child, (ctk.CTkLabel, ctk.CTkFrame)):
                child.bind("<Button-1>", on_click)
                child.configure(cursor="hand2")

    def _toggle_stats_day(self, offset: int) -> None:
        if self._stats_expanded_day == offset:
            self._stats_expanded_day = None
        else:
            self._stats_expanded_day = offset
        self.refresh_week_accordion()

    def _month_label(self, year: int, month: int) -> str:
        return f"{theme.MONTH_NAMES_ES[month - 1].capitalize()} {year}"

    def refresh_heatmap(self) -> None:
        if self._heatmap_drawing:
            return
        self._heatmap_drawing = True
        needs_retry = False
        try:
            max_h = self._heatmap_max_height()
            months = self._heatmap_month_triplet()
            datasets = [
                database.get_month_daily_data(year, month, db_path=self.app.db_path)
                for year, month in months
            ]
            canvases = [canvas for _, canvas in self.heatmap_months]
            shared_cell = self._compute_shared_heatmap_cell(canvases, datasets, max_h)

            for (title, canvas), (year, month), data in zip(
                self.heatmap_months, months, datasets, strict=True
            ):
                title.configure(text=self._month_label(year, month))
                self._draw_heatmap_on_canvas(
                    canvas,
                    data,
                    show_day_labels=(canvas is self.heatmap_months[0][1]),
                    max_height=max_h,
                    cell=shared_cell,
                )

            needs_retry = any(canvas.winfo_width() <= 1 for _, canvas in self.heatmap_months)
        finally:
            self._heatmap_drawing = False

        if needs_retry and self._heatmap_retry_count < 8:
            self._heatmap_retry_count += 1
            self.after(50, self.refresh_heatmap)
        else:
            self._heatmap_retry_count = 0

    def _show_heatmap_tip(
        self,
        text: str,
        cx: int,
        cy: int,
        canvas: tk.Canvas | None = None,
    ) -> None:
        self._hide_heatmap_tip()
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.configure(bg=theme.TEXT)
        tk.Label(
            tip,
            text=text,
            bg=theme.TEXT,
            fg=theme.TEXT_ON_PRIMARY,
            font=(theme.FONT, 10),
            padx=8,
            pady=4,
        ).pack()
        target = canvas or self.heatmap_months[1][1]
        x = target.winfo_rootx() + cx
        y = target.winfo_rooty() + cy - 28
        tip.geometry(f"+{x}+{y}")
        self._heatmap_tip = tip

    def _hide_heatmap_tip(self) -> None:
        if self._heatmap_tip and self._heatmap_tip.winfo_exists():
            self._heatmap_tip.destroy()
        self._heatmap_tip = None

    def update_timer_display(
        self,
        seconds: int,
        subject: str,
        active: bool,
        paused: bool = False,
    ) -> None:
        self.timer_var.set(database.format_timer(seconds))
        if active and paused:
            self.status_var.set(f"Pausado ⏸ — {subject}")
            self.status_badge.configure(fg_color=theme.PAUSE_BG, text_color=theme.PAUSE_TEXT)
        elif active:
            self.status_var.set(f"● Estudiando — {subject}")
            self.status_badge.configure(fg_color=theme.SUCCESS_BG, text_color=theme.SUCCESS)
        else:
            self.status_var.set("Sin sesión activa")
            self.status_badge.configure(fg_color=theme.INPUT, text_color=theme.TEXT)

    def update_session_controls(self) -> None:
        active = self.app.is_active
        paused = self.app.is_paused
        state = "disabled" if active else "normal"
        self.subject_entry.configure(state=state)
        self.note_entry.configure(state=state)
        self.start_btn.configure(state="disabled" if active else "normal")

        self._style_action_button(
            self.pause_btn,
            self._session_btn_styles["pause"],
            active and not paused,
        )
        self._style_action_button(
            self.resume_btn,
            self._session_btn_styles["resume"],
            active and paused,
        )
        self._style_action_button(
            self.stop_btn,
            self._session_btn_styles["stop"],
            active,
        )

        if active:
            self.subject_var.set(self.app.session_subject)
            self.note_var.set(self.app.session_note)
