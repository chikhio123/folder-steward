import time
import threading
from typing import Optional

class AIRateLimitService:
    """Manages AI rate limiting and backoff strategies."""

    def __init__(self):
        # Global rate limiting state
        self.max_rpm = 20
        self.retry_after_seconds = 30
        self.requests_this_minute = 0
        self.last_reset_time = time.time()
        self._lock = threading.Lock()

    def wait_if_needed(self) -> None:
        """Blocks the thread if the rate limit is exceeded."""
        with self._lock:
            now = time.time()
            if now - self.last_reset_time > 60:
                self.requests_this_minute = 0
                self.last_reset_time = now

            if self.requests_this_minute >= self.max_rpm:
                # Calculate sleep time until next minute
                sleep_time = 60 - (now - self.last_reset_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.requests_this_minute = 0
                self.last_reset_time = time.time()

            self.requests_this_minute += 1

    def record_429(self) -> None:
        """Called when a 429 Too Many Requests is received from the provider."""
        # Sleep to backoff
        time.sleep(self.retry_after_seconds)
        with self._lock:
            self.requests_this_minute = 0
            self.last_reset_time = time.time()
