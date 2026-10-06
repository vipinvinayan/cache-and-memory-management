"""Clock (Second-Chance) Cache Implementation.

Simulates operating system second-chance page replacement.
Uses a circular buffer and a reference bit. When an item is read,
its reference bit is set to True. On eviction, the clock hand advances,
clearing reference bits until an unreferenced victim is found.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class _ClockEntry(Generic[K, V]):
    key: K
    value: V
    referenced: bool = False


class ClockCache(Generic[K, V]):
    """Clock Cache gives entries a second chance before eviction."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self._entries: list[Optional[_ClockEntry[K, V]]] = [None] * capacity
        self._key_to_index: dict[K, int] = {}
        self._hand: int = 0
        self._count: int = 0
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
        """Retrieve value and set referenced bit to True (grant second chance)."""
        if key not in self._key_to_index:
            self._misses += 1
            return default

        self._hits += 1
        idx = self._key_to_index[key]
        entry = self._entries[idx]
        if entry is not None:
            entry.referenced = True
            return entry.value
        return default

    def put(self, key: K, value: V) -> None:
        """Insert or update item. If full, sweep clock hand until victim is found."""
        if key in self._key_to_index:
            idx = self._key_to_index[key]
            entry = self._entries[idx]
            if entry is not None:
                entry.value = value
                entry.referenced = True
            return

        # Buffer has empty slots
        if self._count < self.capacity:
            for i in range(self.capacity):
                if self._entries[i] is None:
                    self._entries[i] = _ClockEntry(key=key, value=value, referenced=False)
                    self._key_to_index[key] = i
                    self._count += 1
                    return

        # Buffer full: sweep clock hand
        while True:
            entry = self._entries[self._hand]
            if entry is None:
                self._entries[self._hand] = _ClockEntry(key=key, value=value, referenced=False)
                self._key_to_index[key] = self._hand
                self._hand = (self._hand + 1) % self.capacity
                self._count += 1
                return

            if entry.referenced:
                # Clear second chance and advance hand
                entry.referenced = False
                self._hand = (self._hand + 1) % self.capacity
            else:
                # Evict victim entry
                del self._key_to_index[entry.key]
                self._entries[self._hand] = _ClockEntry(key=key, value=value, referenced=False)
                self._key_to_index[key] = self._hand
                self._hand = (self._hand + 1) % self.capacity
                return

    def delete(self, key: K) -> bool:
        if key not in self._key_to_index:
            return False
        idx = self._key_to_index.pop(key)
        self._entries[idx] = None
        self._count -= 1
        return True

    def clear(self) -> None:
        self._entries = [None] * self.capacity
        self._key_to_index.clear()
        self._hand = 0
        self._count = 0
        self._hits = 0
        self._misses = 0

    def __len__(self) -> int:
        return self._count

    def __contains__(self, key: K) -> bool:
        return key in self._key_to_index

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "size": self._count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self.hit_ratio, 4),
            "clock_hand": self._hand,
        }


if __name__ == "__main__":
    cache = ClockCache[str, int](capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.get("A")  # Gives A a second chance (referenced=True)
    cache.put("C", 3)  # Evicts B because B was unreferenced
    print("Contains A?", "A" in cache)  # True
    print("Contains B?", "B" in cache)  # False
    print("Contains C?", "C" in cache)  # True
    print("Stats:", cache.stats())
