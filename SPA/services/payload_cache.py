"""Bounded in-memory LRU cache for lightweight JSON chart payloads."""

import hashlib
import json
from collections import OrderedDict
from typing import Any


class PayloadCache:
    """Thread-safe-compatible bounded LRU cache keeping JSON payloads <= 4 MB total."""

    def __init__(self, max_entries: int = 24) -> None:
        self.max_entries = max_entries
        self._cache: OrderedDict[str, Any] = OrderedDict()

    @staticmethod
    def make_key(namespace: str, params: dict[str, Any] | None = None) -> str:
        param_str = json.dumps(params or {}, sort_keys=True)
        h = hashlib.sha256(param_str.encode("utf-8")).hexdigest()[:16]
        return f"{namespace}:{h}"

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()


# Global singleton instance for chart and summary payload caching
global_payload_cache = PayloadCache(max_entries=24)
