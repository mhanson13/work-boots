from __future__ import annotations

from dataclasses import dataclass
import threading
import time


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


@dataclass
class _RateLimitBucket:
    window_start_epoch: float
    count: int


class InMemoryRateLimiter:
    """Small fixed-window in-memory limiter for application-level abuse protection."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, _RateLimitBucket] = {}

    def check(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if limit <= 0 or window_seconds <= 0:
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

        now = time.time()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None or (now - bucket.window_start_epoch) >= window_seconds:
                self._buckets[key] = _RateLimitBucket(window_start_epoch=now, count=1)
                return RateLimitDecision(allowed=True, retry_after_seconds=0)

            if bucket.count >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket.window_start_epoch)))
                return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)

            bucket.count += 1
            return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()


_RATE_LIMITER = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _RATE_LIMITER
