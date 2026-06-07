import threading
from datetime import datetime

import pystray

import activity
import database
import dialogs
import icons
import single_instance
import sounds
from ui import DashboardUI


class StudyTrackerApp:
    def __init__(self) -> None:
        self.db_path = database.get_db_path()
        database.init_db(self.db_path)

        self.tray_icon: pystray.Icon | None = None
        self._tray_ready = threading.Event()
        self._tray_thread: threading.Thread | None = None
        self._instance = single_instance.SingleInstance()

        self.idle_icon = icons.create_idle_icon()
        self.active_icon = icons.create_active_icon()

        self.is_active = False
        self.is_paused = False
        self._auto_paused = False
        self.session_start: datetime | None = None
        self._segment_start: datetime | None = None
        self._accumulated_seconds = 0
        self.session_subject = ""
        self.session_note = ""
        self._timer_running = False
        self._inactivity_notified = False

        self.window = DashboardUI(self)
        self.window.setup_shortcuts()

    def quick_start_from_ui(self) -> None:
        self.show_window()
        if self.is_active:
            return

        subject = database.get_next_free_session_subject(self.db_path)
        note = self.window.note_var.get().strip()
        self.window.subject_var.set(subject)
        self._begin_session(subject, note)

    def toggle_pause_from_ui(self) -> None:
        if not self.is_active:
            return
        if self.is_paused:
            self.resume_from_ui()
        else:
            self.pause_from_ui()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("Abrir ventana", self._on_show_window, default=True),
            pystray.MenuItem("Inicio rápido", self._on_quick_start, enabled=self._can_start),
            pystray.MenuItem("Iniciar sesión", self._on_start_session, enabled=self._can_start),
            pystray.MenuItem("Pausar", self._on_pause_session, enabled=self._can_pause),
            pystray.MenuItem("Reanudar", self._on_resume_session, enabled=self._can_resume),
            pystray.MenuItem("Terminar sesión", self._on_end_session, enabled=self._can_end),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self._on_quit),
        )

    def _can_start(self, _item) -> bool:
        return not self.is_active

    def _can_end(self, _item) -> bool:
        return self.is_active

    def _can_pause(self, _item) -> bool:
        return self.is_active and not self.is_paused

    def _can_resume(self, _item) -> bool:
        return self.is_active and self.is_paused

    def _run_on_main(self, callback) -> None:
        self.window.after(0, callback)

    def show_window(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        self.window.attributes("-topmost", True)
        self.window.after(200, lambda: self.window.attributes("-topmost", False))

    def hide_window(self) -> None:
        self.window.withdraw()

    def _on_show_window(self, _icon=None, _item=None) -> None:
        self._run_on_main(self.show_window)

    def _on_start_session(self, _icon, _item) -> None:
        self._run_on_main(self.start_from_ui)

    def _on_quick_start(self, _icon, _item) -> None:
        self._run_on_main(self.quick_start_from_ui)

    def _on_end_session(self, _icon, _item) -> None:
        self._run_on_main(self.stop_from_ui)

    def _on_pause_session(self, _icon, _item) -> None:
        self._run_on_main(self.pause_from_ui)

    def _on_resume_session(self, _icon, _item) -> None:
        self._run_on_main(self.resume_from_ui)

    def _on_quit(self, _icon, _item) -> None:
        if self.is_active:
            self._run_on_main(self._confirm_quit_with_active_session)
        else:
            self._shutdown()

    def _confirm_quit_with_active_session(self) -> None:
        if dialogs.ask_yes_no(
            self.window,
            "Sesión activa",
            "Hay una sesión en curso. ¿Deseas guardarla y salir?",
        ):
            self._end_session(silent=True)
            self._shutdown()

    def get_elapsed_seconds(self) -> int:
        if not self.is_active:
            return 0
        elapsed = self._accumulated_seconds
        if not self.is_paused and self._segment_start:
            elapsed += int((datetime.now() - self._segment_start).total_seconds())
        return elapsed

    def start_from_ui(self) -> None:
        self.show_window()
        if self.is_active:
            return

        subject = self.window.subject_var.get().strip()
        if not subject:
            dialogs.show_warning(
                self.window,
                "Campo requerido",
                "Indica la materia antes de iniciar.",
            )
            self.window.subject_entry.focus_set()
            return

        self._begin_session(subject, self.window.note_var.get())

    def pause_from_ui(self) -> None:
        self._pause_session(auto=False)

    def resume_from_ui(self) -> None:
        self._resume_session()

    def stop_from_ui(self) -> None:
        self._end_session(silent=False)

    def _begin_session(self, subject: str, note: str) -> None:
        now = datetime.now()
        self.is_active = True
        self.is_paused = False
        self._auto_paused = False
        self._inactivity_notified = False
        self.session_start = now
        self._segment_start = now
        self._accumulated_seconds = 0
        self.session_subject = subject
        self.session_note = note
        self._timer_running = True

        sounds.play_start()
        self._update_app_icon()
        self._update_tray_title()
        if self.tray_icon:
            self.tray_icon.update_menu()

        self.window.update_session_controls()
        self._schedule_timer_tick()
        self._schedule_inactivity_check()

    def _pause_session(self, auto: bool = False) -> None:
        if not self.is_active or self.is_paused:
            return

        if self._segment_start:
            self._accumulated_seconds += int(
                (datetime.now() - self._segment_start).total_seconds()
            )
            self._segment_start = None

        self.is_paused = True
        self._auto_paused = auto

        if auto and not self._inactivity_notified:
            self._inactivity_notified = True
            activity.show_notification(
                "FocusFlow",
                "Tu sesión fue pausada por inactividad 😴",
            )

        self._update_app_icon()
        if self.tray_icon:
            self.tray_icon.update_menu()
        self.window.update_session_controls()
        self.window.update_timer_display(
            self.get_elapsed_seconds(),
            self.session_subject,
            active=True,
            paused=True,
        )

    def _resume_session(self) -> None:
        if not self.is_active or not self.is_paused:
            return

        self.is_paused = False
        self._auto_paused = False
        self._inactivity_notified = False
        self._segment_start = datetime.now()

        self._update_app_icon()
        if self.tray_icon:
            self.tray_icon.update_menu()
        self.window.update_session_controls()
        self.window.update_timer_display(
            self.get_elapsed_seconds(),
            self.session_subject,
            active=True,
            paused=False,
        )

    def _schedule_timer_tick(self) -> None:
        if not self._timer_running:
            return

        elapsed = self.get_elapsed_seconds()
        self.window.update_timer_display(
            elapsed,
            self.session_subject,
            active=self.is_active,
            paused=self.is_paused,
        )
        self._update_tray_title()
        self.window.after(1000, self._schedule_timer_tick)

    def _schedule_inactivity_check(self) -> None:
        if not self.is_active:
            return

        if not self.is_paused:
            idle_limit = database.get_inactivity_minutes(self.db_path) * 60
            idle_seconds = activity.get_idle_seconds()
            if idle_seconds >= idle_limit:
                self._pause_session(auto=True)
        elif self._auto_paused:
            if activity.get_idle_seconds() < 3:
                self._resume_session()

        self.window.after(5000, self._schedule_inactivity_check)

    def _update_app_icon(self) -> None:
        active = self.is_active
        if self.tray_icon:
            self.tray_icon.icon = self.active_icon if active else self.idle_icon
        icons.apply_window_icon(self.window, active=active)

    def _update_tray_title(self) -> None:
        if not self.tray_icon:
            return
        if not self.is_active or self.session_start is None:
            self.tray_icon.title = "FocusFlow — Inactivo (clic para abrir)"
            return
        elapsed = self.get_elapsed_seconds()
        state = "Pausado" if self.is_paused else "Estudiando"
        self.tray_icon.title = (
            f"{state}: {self.session_subject} — {database.format_duration(elapsed)}"
        )

    def _end_session(self, silent: bool = False) -> None:
        if not self.is_active or self.session_start is None:
            if not silent:
                dialogs.show_info(
                    self.window,
                    "Sin sesión",
                    "No hay ninguna sesión activa.",
                )
            return

        if not self.is_paused and self._segment_start:
            self._accumulated_seconds += int(
                (datetime.now() - self._segment_start).total_seconds()
            )

        duration = max(1, self._accumulated_seconds)
        session_date = self.session_start.date()

        database.save_session(
            session_date,
            self.session_subject,
            self.session_note,
            duration,
            self.db_path,
        )

        sounds.play_stop()
        self._timer_running = False
        self.is_active = False
        self.is_paused = False
        self._auto_paused = False
        self.session_start = None
        self._segment_start = None
        self._accumulated_seconds = 0
        saved_subject = self.session_subject
        self.session_subject = ""
        self.session_note = ""

        self._update_app_icon()
        if self.tray_icon:
            self.tray_icon.title = "FocusFlow — Inactivo (clic para abrir)"
            self.tray_icon.update_menu()

        self.window.update_timer_display(0, "", active=False, paused=False)
        self.window.subject_var.set("")
        self.window.note_var.set("")
        self.window.update_session_controls()
        self.window.refresh_all()

        if not silent:
            dialogs.show_info(
                self.window,
                "Sesión guardada",
                f"{saved_subject}\n\nDuración: {database.format_duration(duration)}",
            )

    def _shutdown(self) -> None:
        self._timer_running = False
        self._instance.release()
        if self.tray_icon:
            self.tray_icon.stop()
        self.window.after(0, self.window.destroy)

    def _run_tray(self) -> None:
        self.tray_icon = pystray.Icon(
            "focusflow_study_tracker",
            self.idle_icon,
            "FocusFlow — Clic para abrir",
            menu=self._build_menu(),
        )
        self._tray_ready.set()
        self.tray_icon.run()

    def run(self) -> None:
        if not self._instance.acquire():
            self._instance.notify_existing()
            return

        self._instance.listen(on_show=lambda: self._run_on_main(self.show_window))

        self._tray_thread = threading.Thread(target=self._run_tray, daemon=False)
        self._tray_thread.start()

        if not self._tray_ready.wait(timeout=5):
            dialogs.show_error(
                self.window,
                "Error",
                "No se pudo iniciar el icono en la bandeja del sistema.",
            )
            self._instance.release()
            self.window.destroy()
            return

        self.window.refresh_all()
        self.window.after(100, self.show_window)
        self.window.mainloop()

        if self.tray_icon:
            self.tray_icon.stop()
        if self._tray_thread.is_alive():
            self._tray_thread.join(timeout=3)
        self._instance.release()


def main() -> None:
    icons.set_windows_app_user_model_id()
    app = StudyTrackerApp()
    app.run()


if __name__ == "__main__":
    main()
