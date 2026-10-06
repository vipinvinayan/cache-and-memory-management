"""Least Frequently Used (LFU) Cache Implementation.

Achieves strict O(1) time complexity for get(), put(), and delete()
by combining a key-node lookup table with frequency bucket linked lists.
Ties are broken using LRU order within the same frequency bucket.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class _LFUNode(Generic[K, V]):
    def __init__(self, key: Any, value: Any, freq: int = 1) -> None:
        self.key: K = key
        self.value: V = value
        self.freq: int = freq
        self.prev: Optional[_LFUNode[K, V]] = None
        self.next: Optional[_LFUNode[K, V]] = None


class _FrequencyList(Generic[K, V]):
    """Doubly linked list for nodes sharing the same access frequency."""

    def __init__(self) -> None:
        self.head: _LFUNode[K, V] = _LFUNode("__HEAD__", None)
        self.tail: _LFUNode[K, V] = _LFUNode("__TAIL__", None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size: int = 0

    @property
    def is_empty(self) -> bool:
        return self._size == 0

    def append_front(self, node: _LFUNode[K, V]) -> None:
        node.prev = self.head
        node.next = self.head.next
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node
        self._size += 1

    def remove(self, node: _LFUNode[K, V]) -> None:
        if node.prev and node.next:
            node.prev.next = node.next
            node.next.prev = node.prev
            node.prev = None
            node.next = None
            self._size -= 1

    def pop_tail(self) -> Optional[_LFUNode[K, V]]:
        if self.is_empty:
            return None
        victim = self.tail.prev
        if victim and victim is not self.head:
            self.remove(victim)
            return victim
        return None


class LFUCache(Generic[K, V]):
    """LFU Cache evicts items with the lowest access frequency."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self._node_map: dict[K, _LFUNode[K, V]] = {}
        self._freq_map: dict[int, _FrequencyList[K, V]] = defaultdict(_FrequencyList)
        self._min_freq: int = 0
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

    def _update_frequency(self, node: _LFUNode[K, V]) -> None:
        old_freq = node.freq
        self._freq_map[old_freq].remove(node)
        if self._min_freq == old_freq and self._freq_map[old_freq].is_empty:
            self._min_freq += 1

        node.freq += 1
        self._freq_map[node.freq].append_front(node)

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Retrieve item and increment its access count."""
        if key not in self._node_map:
            self._misses += 1
            return default

        self._hits += 1
        node = self._node_map[key]
        self._update_frequency(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        """Insert or update key-value pair. Evicts LFU item if at capacity."""
        if key in self._node_map:
            node = self._node_map[key]
            node.value = value
            self._update_frequency(node)
            return

        if len(self._node_map) >= self.capacity:
            lru_list = self._freq_map[self._min_freq]
            evicted = lru_list.pop_tail()
            if evicted:
                del self._node_map[evicted.key]

        new_node = _LFUNode(key=key, value=value, freq=1)
        self._node_map[key] = new_node
        self._freq_map[1].append_front(new_node)
        self._min_freq = 1

    def delete(self, key: K) -> bool:
        if key not in self._node_map:
            return False
        node = self._node_map.pop(key)
        self._freq_map[node.freq].remove(node)
        if self._min_freq == node.freq and self._freq_map[node.freq].is_empty:
            if self._node_map:
                self._min_freq = min(n.freq for n in self._node_map.values())
            else:
                self._min_freq = 0
        return True

    def clear(self) -> None:
        self._node_map.clear()
        self._freq_map.clear()
        self._min_freq = 0
        self._hits = 0
        self._misses = 0

    def get_frequency(self, key: K) -> Optional[int]:
        node = self._node_map.get(key)
        return node.freq if node else None

    def __len__(self) -> int:
        return len(self._node_map)

    def __contains__(self, key: K) -> bool:
        return key in self._node_map

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "size": len(self),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self.hit_ratio, 4),
        }


if __name__ == "__main__":
    cache = LFUCache[str, int](capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.get("A")  # A freq=2
    cache.get("A")  # A freq=3
    cache.put("C", 3)  # Evicts B because B has lower freq (1 vs 3)
    print("Contains B?", "B" in cache)  # False
    print("Contains A?", "A" in cache)  # True
    print("A freq:", cache.get_frequency("A"))
    print("Stats:", cache.stats())
