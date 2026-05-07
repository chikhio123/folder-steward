import time
import threading
from typing import Optional

class AIRateLimitService:
    """Manages AI rate limiting and backoff strategies."""

    def __init__(self):
        # Global rate limiting state
        self.max_rpm = 20
        self.background_max_rpm = 15  # Reserve 5 RPM for interactive tasks
        self.retry_after_seconds = 30
        self.requests_this_minute = 0
        self.last_reset_time = time.time()
        self._lock = threading.Lock()

    def wait_if_needed(self, is_interactive: bool = False) -> None:
        """Blocks the thread if the rate limit is exceeded."""
        sleep_time = 0
        with self._lock:
            now = time.time()
            if now - self.last_reset_time > 60:
                self.requests_this_minute = 0
                self.last_reset_time = now

            effective_limit = self.max_rpm if is_interactive else self.background_max_rpm

            if self.requests_this_minute >= effective_limit:
                # Calculate sleep time until next minute
                sleep_time = 60 - (now - self.last_reset_time)
                if sleep_time <= 0:
                    sleep_time = 1
                # Reset counters anticipating the sleep
                self.requests_this_minute = 0
                self.last_reset_time = now + sleep_time

            self.requests_this_minute += 1

        if sleep_time > 0:
            time.sleep(sleep_time)

    def record_429(self) -> None:
        """Called when a 429 Too Many Requests is received from the provider."""
        # Sleep outside the lock so we don't block threads querying status
        time.sleep(self.retry_after_seconds)
        with self._lock:
            self.requests_this_minute = 0
            self.last_reset_time = time.time()
