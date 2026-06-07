import socket
import threading

PORT = 47653
HOST = "127.0.0.1"


class SingleInstance:
    """Evita múltiples instancias (y varios iconos en la bandeja)."""

    def __init__(self) -> None:
        self._lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._on_show: callable | None = None

    def acquire(self) -> bool:
        try:
            self._lock.bind((HOST, PORT))
            self._lock.listen(1)
            return True
        except OSError:
            return False

    def notify_existing(self) -> None:
        try:
            with socket.create_connection((HOST, PORT), timeout=1) as client:
                client.sendall(b"SHOW\n")
        except OSError:
            pass

    def listen(self, on_show: callable) -> None:
        self._on_show = on_show

        def serve() -> None:
            while True:
                try:
                    conn, _ = self._server.accept()
                except OSError:
                    break
                with conn:
                    data = conn.recv(64)
                    if data.strip() == b"SHOW" and self._on_show:
                        self._on_show()

        self._server = self._lock
        self._thread = threading.Thread(target=serve, daemon=True)
        self._thread.start()

    def release(self) -> None:
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
