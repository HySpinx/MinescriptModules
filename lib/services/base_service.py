import threading
import time


class BaseService:
    """Cooperative lifecycle wrapper for background services."""

    def __init__(self, service_id, tick_interval=0.1):
        self.service_id = service_id
        self.tick_interval = tick_interval
        self._stop_event = threading.Event()
        self._paused = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self, timeout=2.0):
        self._stop_event.set()
        thread = self._thread
        if (
            thread is not None
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=timeout)

    def pause(self):
        self._paused.set()

    def resume(self):
        self._paused.clear()
        self.on_resume()

    def reset_baseline(self):
        """Override in subclasses that track rolling baselines."""
        return None

    @property
    def is_running(self):
        return not self._stop_event.is_set()

    @property
    def is_paused(self):
        return self._paused.is_set()

    def sleep_tick(self):
        time.sleep(self.tick_interval)

    def on_resume(self):
        """Optional hook for subclasses."""
        return None

    def _run(self):
        while not self._stop_event.is_set():
            if self._paused.is_set():
                time.sleep(0.05)
                continue
            try:
                self.run_step()
            except Exception:
                # Keep long-running service loops alive on transient API failures.
                pass
            time.sleep(self.tick_interval)

    def run_step(self):
        raise NotImplementedError
