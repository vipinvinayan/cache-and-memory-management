"""Binary Buddy Memory Allocator.

Implements the classical Buddy System algorithm used in OS kernels (e.g., Linux page allocator).
Memory is partitioned into blocks of powers of two (2^k).
- Blocks are recursively split when a smaller size is required.
- Adjacent 'buddy' blocks (offset ^ size) are recursively merged (coalesced) on free.

Time Complexity:
    - allocate(): O(log N)
    - free(): O(log N)
"""
from __future__ import annotations
import math
from typing import Any, Optional


def next_power_of_two(n: int) -> int:
    if n <= 0:
        return 1
    return 1 << (n - 1).bit_length()


class BuddyAllocator:
    """Binary Buddy Memory Allocator."""

    def __init__(self, total_size: int = 1024, min_block_size: int = 16) -> None:
        self.total_size: int = next_power_of_two(total_size)
        self.min_block_size: int = next_power_of_two(min_block_size)

        self._min_order: int = int(math.log2(self.min_block_size))
        self._max_order: int = int(math.log2(self.total_size))

        self._free_lists: dict[int, set[int]] = {
            order: set() for order in range(self._min_order, self._max_order + 1)
        }
        self._free_lists[self._max_order].add(0)

        # offset -> (block_size, tag, requested_size)
        self._allocated: dict[int, tuple[int, str, int]] = {}
        self._allocation_count: int = 0
        self._deallocation_count: int = 0

    @property
    def used_bytes(self) -> int:
        return sum(sz for sz, _, _ in self._allocated.values())

    @property
    def free_bytes(self) -> int:
        return self.total_size - self.used_bytes

    @property
    def total_internal_fragmentation(self) -> int:
        return sum(sz - req for sz, _, req in self._allocated.values())

    def allocate(self, size: int, tag: str = "") -> Optional[int]:
        """Allocate memory of given size rounded up to power of two."""
        if size <= 0:
            raise ValueError("Allocation size must be positive")

        needed_size = max(self.min_block_size, next_power_of_two(size))
        if needed_size > self.total_size:
            return None

        target_order = int(math.log2(needed_size))

        found_order: Optional[int] = None
        for order in range(target_order, self._max_order + 1):
            if self._free_lists[order]:
                found_order = order
                break

        if found_order is None:
            return None

        offset = self._free_lists[found_order].pop()

        # Split downward to target order
        while found_order > target_order:
            found_order -= 1
            block_size = 1 << found_order
            buddy_offset = offset + block_size
            self._free_lists[found_order].add(buddy_offset)

        self._allocated[offset] = (needed_size, tag or f"task_{self._allocation_count + 1}", size)
        self._allocation_count += 1
        return offset

    def free(self, offset: int) -> bool:
        """Free block and recursively coalesce with buddy if free."""
        if offset not in self._allocated:
            return False

        block_size, _, _ = self._allocated.pop(offset)
        order = int(math.log2(block_size))
        self._deallocation_count += 1

        curr_offset = offset
        curr_order = order

        while curr_order < self._max_order:
            curr_size = 1 << curr_order
            buddy_offset = curr_offset ^ curr_size

            if buddy_offset in self._free_lists[curr_order]:
                self._free_lists[curr_order].remove(buddy_offset)
                curr_offset = min(curr_offset, buddy_offset)
                curr_order += 1
            else:
                break

        self._free_lists[curr_order].add(curr_offset)
        return True

    def get_blocks_info(self) -> list[dict[str, Any]]:
        blocks = []
        for offset, (size, tag, req) in self._allocated.items():
            blocks.append({
                "offset": offset,
                "size": size,
                "is_free": False,
                "tag": tag,
                "internal_frag": size - req,
            })
        for order, offsets in self._free_lists.items():
            sz = 1 << order
            for off in offsets:
                blocks.append({
                    "offset": off,
                    "size": sz,
                    "is_free": True,
                    "tag": "FREE",
                    "internal_frag": 0,
                })
        blocks.sort(key=lambda b: b["offset"])
        return blocks

    def stats(self) -> dict[str, Any]:
        return {
            "total_size": self.total_size,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "internal_fragmentation": self.total_internal_fragmentation,
            "allocations": self._allocation_count,
            "deallocations": self._deallocation_count,
        }


if __name__ == "__main__":
    buddy = BuddyAllocator(total_size=512, min_block_size=32)
    p1 = buddy.allocate(40, tag="Proc1")  # Rounds up to 64B
    p2 = buddy.allocate(110, tag="Proc2") # Rounds up to 128B
    print(f"Allocated Proc1 (40B -> 64B) at 0x{p1:04X}")
    print(f"Allocated Proc2 (110B -> 128B) at 0x{p2:04X}")
    print(f"Internal Fragmentation: {buddy.total_internal_fragmentation}B")
    buddy.free(p1)
    buddy.free(p2)
    print("Freed all blocks. Successfully coalesced back into 512B single block!")
