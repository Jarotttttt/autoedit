from __future__ import annotations

import queue
import threading
from typing import Any, Callable


class Worker:
    def __init__(self) -> None:
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, target: Callable[[], Any]) -> None:
        if self.running:
            raise RuntimeError("proses sebelumnya masih berjalan")

        def runner() -> None:
            try:
                self.events.put(("done", target()))
            except BaseException as error:
                self.events.put(("error", error))

        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

    def progress(self, value: float, message: str) -> None:
        self.events.put(("progress", (value, message)))

    def poll(
        self,
        *,
        on_progress: Callable[[float, str], None],
        on_done: Callable[[Any], None],
        on_error: Callable[[BaseException], None],
        interval_ms: int = 80,
        schedule: Callable[[int, Callable[[], None]], None],
    ) -> None:
        def tick() -> None:
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                schedule(interval_ms, tick)
                return
            if kind == "progress":
                value, message = payload
                on_progress(float(value), str(message))
                schedule(interval_ms, tick)
                return
            if kind == "done":
                on_done(payload)
            else:
                on_error(payload)
            schedule(interval_ms, tick)

        schedule(interval_ms, tick)
