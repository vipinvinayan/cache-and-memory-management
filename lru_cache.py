"""Least Recently Used (LRU) Cache Implementation.

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


class _Node(Generic[K, V]):
    """Internal doubly linked list node."""

    def __init__(self, key: Any, value: Any) -> None:
        self.key: K = key
        self.value: V = value
        self.prev: Optional[_Node[K, V]] = None
        self.next: Optional[_Node[K, V]] = None


class LRUCache(Generic[K, V]):
    """LRU Cache evicts items that have not been accessed for the longest period.

    Uses a Hash Map + Sentinel Doubly Linked List for strict O(1) operations.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError(f"Capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self._lookup: dict[K, _Node[K, V]] = {}

        # Sentinel head (MRU) and tail (LRU)
        self._head: _Node[K, V] = _Node("__HEAD__", None)
        self._tail: _Node[K, V] = _Node("__TAIL__", None)
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

    def _remove_node(self, node: _Node[K, V]) -> None:
        if node.prev and node.next:
            node.prev.next = node.next
            node.next.prev = node.prev
            node.prev = None
            node.next = None

    def _add_front(self, node: _Node[K, V]) -> None:
        """Insert node immediately after sentinel head (MRU position)."""
        node.prev = self._head
        node.next = self._head.next
        if self._head.next:
            self._head.next.prev = node
        self._head.next = node

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Retrieve item and move it to Most Recently Used position."""
        if key not in self._lookup:
            self._misses += 1
            return default

        self._hits += 1
        node = self._lookup[key]
        self._remove_node(node)
        self._add_front(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        """Insert or update item. Evicts LRU item if at capacity."""
        if key in self._lookup:
            node = self._lookup[key]
            node.value = value
            self._remove_node(node)
            self._add_front(node)
            return

        if len(self._lookup) >= self.capacity:
            # Evict LRU (node immediately before tail)
            lru_node = self._tail.prev
            if lru_node and lru_node is not self._head:
                self._remove_node(lru_node)
                del self._lookup[lru_node.key]

        new_node = _Node(key=key, value=value)
        self._lookup[key] = new_node
        self._add_front(new_node)

    def delete(self, key: K) -> bool:
        """Remove a key from the cache."""
        if key not in self._lookup:
            return False
        node = self._lookup.pop(key)
        self._remove_node(node)
        return True

    def clear(self) -> None:
        """Clear cache state."""
        self._lookup.clear()
        self._head.next = self._tail
        self._tail.prev = self._head
        self._hits = 0
        self._misses = 0

    def keys_in_order(self) -> list[K]:
        """Return keys from Most Recently Used to Least Recently Used."""
        keys: list[K] = []
        curr = self._head.next
        while curr and curr is not self._tail:
            keys.append(curr.key)
            curr = curr.next
        return keys

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
    cache = LRUCache[str, int](capacity=3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)
    print("Initial (MRU to LRU):", cache.keys_in_order())
    cache.get("A")  # Moves A to MRU
    print("After GET(A):", cache.keys_in_order())
    cache.put("D", 4)  # Evicts B (LRU)
    print("After PUT(D):", cache.keys_in_order())
    print("Stats:", cache.stats())
