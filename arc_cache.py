"""Adaptive Replacement Cache (ARC) Implementation.

Based on Nimrod Megiddo & Dharmendra S. Modha (IBM Research, 2003).
Self-tuning cache balancing recency and frequency through four lists:
- T1: recent items (cached)
- T2: frequent items (cached)
- B1: ghost history for T1 (keys only)
- B2: ghost history for T2 (keys only)
Parameter p dynamically tunes target T1 size based on ghost hits.
"""
from __future__ import annotations
from collections import OrderedDict
from typing import Any, Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ARCCache(Generic[K, V]):
    """Adaptive Replacement Cache (ARC). Self-tuning between LRU and LFU."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self._p: float = 0.0  # Dynamic target size of T1

        self._t1: OrderedDict[K, V] = OrderedDict()
        self._t2: OrderedDict[K, V] = OrderedDict()
        self._b1: OrderedDict[K, None] = OrderedDict()
        self._b2: OrderedDict[K, None] = OrderedDict()

        self._hits: int = 0
        self._misses: int = 0

    @property
    def target_p(self) -> float:
        return self._p

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

    def _replace(self, in_b2: bool) -> None:
        t1_len = len(self._t1)
        if t1_len > 0 and ((t1_len > self._p) or (in_b2 and t1_len == int(self._p))):
            k, _ = self._t1.popitem(last=False)
            self._b1[k] = None
        else:
            if len(self._t2) > 0:
                k, _ = self._t2.popitem(last=False)
                self._b2[k] = None

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Retrieve item. Moves key to MRU of frequent list T2 on hit."""
        if key in self._t1:
            self._hits += 1
            val = self._t1.pop(key)
            self._t2[key] = val
            return val

        if key in self._t2:
            self._hits += 1
            val = self._t2.pop(key)
            self._t2[key] = val
            return val

        self._misses += 1
        return default

    def put(self, key: K, value: V) -> None:
        """Insert or update item, tuning p if a ghost hit occurs."""
        c = self.capacity

        if key in self._t1:
            self._t1.pop(key)
            self._t2[key] = value
            return
        if key in self._t2:
            self._t2.pop(key)
            self._t2[key] = value
            return

        # Ghost hit in B1 -> increase p (favor recency)
        if key in self._b1:
            delta = 1.0 if len(self._b1) >= len(self._b2) else len(self._b2) / len(self._b1)
            self._p = min(float(c), self._p + delta)
            self._replace(in_b2=False)
            del self._b1[key]
            self._t2[key] = value
            return

        # Ghost hit in B2 -> decrease p (favor frequency)
        if key in self._b2:
            delta = 1.0 if len(self._b2) >= len(self._b1) else len(self._b1) / len(self._b2)
            self._p = max(0.0, self._p - delta)
            self._replace(in_b2=True)
            del self._b2[key]
            self._t2[key] = value
            return

        # Complete miss
        if len(self._t1) + len(self._t2) >= c:
            if len(self._t1) + len(self._b1) >= c and len(self._b1) > 0:
                self._b1.popitem(last=False)
            self._replace(in_b2=False)

        while len(self._t1) + len(self._t2) + len(self._b1) + len(self._b2) > 2 * c:
            if len(self._b2) > 0:
                self._b2.popitem(last=False)
            elif len(self._b1) > 0:
                self._b1.popitem(last=False)
            else:
                break

        self._t1[key] = value

    def delete(self, key: K) -> bool:
        removed = False
        if key in self._t1:
            del self._t1[key]
            removed = True
        elif key in self._t2:
            del self._t2[key]
            removed = True

        if key in self._b1:
            del self._b1[key]
        if key in self._b2:
            del self._b2[key]

        return removed

    def clear(self) -> None:
        self._t1.clear()
        self._t2.clear()
        self._b1.clear()
        self._b2.clear()
        self._p = 0.0
        self._hits = 0
        self._misses = 0

    def __len__(self) -> int:
        return len(self._t1) + len(self._t2)

    def __contains__(self, key: K) -> bool:
        return key in self._t1 or key in self._t2

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "size": len(self),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self.hit_ratio, 4),
            "target_p": round(self._p, 2),
            "t1_size": len(self._t1),
            "t2_size": len(self._t2),
            "b1_size": len(self._b1),
            "b2_size": len(self._b2),
        }


if __name__ == "__main__":
    cache = ARCCache[str, int](capacity=3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)
    cache.put("D", 4)  # Evicts A to ghost cache B1
    print("Contains A in active cache?", "A" in cache)  # False
    print("Ghost B1 contains A?", "A" in cache._b1)     # True
    cache.put("A", 10)  # Ghost hit! Adapts p upwards
    print("New target_p:", cache.target_p)
    print("Stats:", cache.stats())
