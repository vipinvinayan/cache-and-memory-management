"""First-In, First-Out (FIFO) Cache Implementation.

Evicts items strictly in the chronological order they were first inserted.
Time Complexity:
    - get(): O(1)
    - put(): O(1)
    - delete(): O(1)
Space Complexity: O(capacity)
"""
from __future__ import annotations
from collections import OrderedDict
from typing import Any, Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class FIFOCache(Generic[K, V]):
    """FIFO Cache evicts the oldest inserted item when capacity is exceeded."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self._store: OrderedDict[K, V] = OrderedDict()
        self._hits: int = 0
        self._misses: int = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def hit_ratio(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Retrieve value without modifying eviction order."""
        if key not in self._store:
            self._misses += 1
            return default

        self._hits += 1
        return self._store[key]

    def put(self, key: K, value: V) -> None:
        """Insert or update item. Evicts oldest item if at capacity on new insert."""
        if key in self._store:
            self._store[key] = value
            return

        if len(self._store) >= self.capacity:
            self._store.popitem(last=False)

        self._store[key] = value

    def delete(self, key: K) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    def keys_in_order(self) -> list[K]:
        """Return keys in insertion order (oldest to newest)."""
        return list(self._store.keys())

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "size": len(self),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self.hit_ratio, 4),
        }


if __name__ == "__main__":
    cache = FIFOCache[str, int](capacity=3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)
    cache.get("A")  # Reading A does not prevent FIFO eviction
    cache.put("D", 4)  # Evicts A (the oldest inserted)
    print("Contains A?", "A" in cache)  # False
    print("Contains B?", "B" in cache)  # True
    print("Cached keys:", cache.keys_in_order())
    print("Stats:", cache.stats())
