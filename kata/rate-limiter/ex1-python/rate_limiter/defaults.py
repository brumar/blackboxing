"""Ready-to-use implementations of Clock and Store.

These are simple reference implementations shipped with the module so users
can get started without writing their own.  They are NOT part of the black box
— their source is visible and intentionally straightforward.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Clock implementations
# ---------------------------------------------------------------------------

class SystemClock:
    """Clock backed by ``time.time()``."""

    def now(self) -> float:
        return time.time()

    async def anow(self) -> float:
        return time.time()


class FakeClock:
    """Manually-controlled clock for tests.

    Usage::

        clock = FakeClock(start=1000.0)
        clock.now()          # 1000.0
        clock.advance(5.0)
        clock.now()          # 1005.0
    """

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def now(self) -> float:
        return self._now

    async def anow(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        """Move time forward by *seconds*."""
        if seconds < 0:
            raise ValueError("Cannot go back in time")
        self._now += seconds

    def set(self, timestamp: float) -> None:
        """Jump to an absolute *timestamp*."""
        self._now = timestamp


# ---------------------------------------------------------------------------
# Store implementations
# ---------------------------------------------------------------------------

@dataclass
class _Entry:
    value: bytes
    expires_at: float


class MemoryStore:
    """In-memory store with TTL expiration. Suitable for single-process use.

    Thread-safe via a lock.

    Usage::

        store = MemoryStore(clock=my_clock)
    """

    def __init__(self, clock: SystemClock | FakeClock) -> None:
        self._clock = clock
        self._data: dict[str, _Entry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> bytes | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if self._clock.now() >= entry.expires_at:
                del self._data[key]
                return None
            return entry.value

    async def aget(self, key: str) -> bytes | None:
        return self.get(key)

    def set(self, key: str, value: bytes, ttl_seconds: float) -> None:
        with self._lock:
            self._data[key] = _Entry(
                value=value,
                expires_at=self._clock.now() + ttl_seconds,
            )

    async def aset(self, key: str, value: bytes, ttl_seconds: float) -> None:
        self.set(key, value, ttl_seconds)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    async def adelete(self, key: str) -> None:
        self.delete(key)
