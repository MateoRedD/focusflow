import threading
import sys
import time


def _beep_sequence(notes: list[tuple[int, int]]) -> None:
    if sys.platform != "win32":
        return
    import winsound

    for freq, duration in notes:
        winsound.Beep(freq, duration)
        time.sleep(0.03)


def play_start() -> None:
    threading.Thread(
        target=_beep_sequence,
        args=([(523, 90), (659, 120), (784, 150)],),
        daemon=True,
    ).start()


def play_stop() -> None:
    threading.Thread(
        target=_beep_sequence,
        args=([(784, 100), (659, 120), (523, 180)],),
        daemon=True,
    ).start()
