"""Most Recently Used (MRU) Cache Implementation.

Evicts the item accessed most recently.
Optimal for cyclical access patterns where elements are accessed in loops
larger than cache capacity, avoiding complete cache thrashing.

Time Complexity:
    - get(): O(1)
    - put(): O(1)
    - delete(): O(1)
Space Complexity: O(capacity)
"""
from __future__ import annotations
from typing import Any, Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class _MRUNode(Generic[K, V]):
    def __init__(self, key: Any, value: Any) -> None:
        self.key: K = key
        self.value: V = value
        self.prev: Optional[_MRUNode[K, V]] = None
        self.next: Optional[_MRUNode[K, V]] = None


class MRUCache(Generic[K, V]):
    """MRU Cache evicts items that were accessed most recently."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self._lookup: dict[K, _MRUNode[K, V]] = {}

        self._head: _MRUNode[K, V] = _MRUNode("__HEAD__", None)
        self._tail: _MRUNode[K, V] = _MRUNode("__TAIL__", None)
        self._head.next = self._tail
        self._tail.prev = self._head

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

    def _remove(self, node: _MRUNode[K, V]) -> None:
        if node.prev and node.next:
            node.prev.next = node.next
            node.next.prev = node.prev
            node.prev = None
            node.next = None

    def _add_front(self, node: _MRUNode[K, V]) -> None:
        node.prev = self._head
        node.next = self._head.next
        if self._head.next:
            self._head.next.prev = node
        self._head.next = node

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Retrieve value and place it at head (MRU)."""
        if key not in self._lookup:
            self._misses += 1
            return default

        self._hits += 1
        node = self._lookup[key]
        self._remove(node)
        self._add_front(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        """Insert or update value. Evicts MRU item (front) if full."""
        if key in self._lookup:
            node = self._lookup[key]
            node.value = value
            self._remove(node)
            self._add_front(node)
            return

        if len(self._lookup) >= self.capacity:
            mru_node = self._head.next
            if mru_node and mru_node is not self._tail:
                self._remove(mru_node)
                del self._lookup[mru_node.key]

        new_node = _MRUNode(key=key, value=value)
        self._lookup[key] = new_node
        self._add_front(new_node)

    def delete(self, key: K) -> bool:
        if key not in self._lookup:
            return False
        node = self._lookup.pop(key)
        self._remove(node)
        return True

    def clear(self) -> None:
        self._lookup.clear()
        self._head.next = self._tail
        self._tail.prev = self._head
        self._hits = 0
        self._misses = 0

    def __len__(self) -> int:
        return len(self._lookup)

    def __contains__(self, key: K) -> bool:
        return key in self._lookup

    def stats(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "size": len(self),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self.hit_ratio, 4),
        }


if __name__ == "__main__":
    cache = MRUCache[str, int](capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    # B is MRU. Inserting C evicts B!
    cache.put("C", 3)
    print("Contains B?", "B" in cache)  # False
    print("Contains A?", "A" in cache)  # True
    print("Stats:", cache.stats())
