import time
from threading import Lock
from typing import Dict


class TTLCache:
    def __init__(self, ttl_seconds: float = 300.0):
        self._ttl = ttl_seconds
        self._store: Dict[str, float] = {}
        self._lock = Lock()

    def seen_recently(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._evict(now)
            if key in self._store:
                return True
            self._store[key] = now
            return False

    def discard(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def _evict(self, now: float) -> None:
        expired = [k for k, ts in self._store.items() if now - ts > self._ttl]
        for k in expired:
            del self._store[k]


dedupe_cache = TTLCache()
