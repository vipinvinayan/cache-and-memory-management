"""Free List Memory Allocator.

Implements dynamic contiguous memory allocation with four strategies:
- First-Fit
- Best-Fit
- Worst-Fit
- Next-Fit

Features automatic block splitting and bidirectional coalescing of free blocks.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class FitStrategy(str, Enum):
    FIRST_FIT = "first_fit"
    BEST_FIT = "best_fit"
    WORST_FIT = "worst_fit"
    NEXT_FIT = "next_fit"


@dataclass
class MemoryBlock:
    offset: int
    size: int
    is_free: bool = True
    tag: str = ""
    requested_size: int = 0

    @property
    def end_offset(self) -> int:
        return self.offset + self.size

    @property
    def internal_fragmentation(self) -> int:
        if not self.is_free and self.requested_size > 0:
            return max(0, self.size - self.requested_size)
        return 0

    def __repr__(self) -> str:
        state = "FREE" if self.is_free else f"ALLOC({self.tag})"
        return f"Block(0x{self.offset:04X}-0x{self.end_offset:04X}, {self.size}B, {state})"


class FreeListAllocator:
    """Contiguous memory allocator maintaining free and allocated block records."""

    def __init__(
        self,
        total_size: int,
        strategy: FitStrategy = FitStrategy.FIRST_FIT,
        min_split_threshold: int = 4,
    ) -> None:
        if total_size <= 0:
            raise ValueError(f"total_size must be positive, got {total_size}")
        self.total_size: int = total_size
        self.strategy: FitStrategy = strategy
        self.min_split_threshold: int = min_split_threshold

        self._blocks: list[MemoryBlock] = [
            MemoryBlock(offset=0, size=total_size, is_free=True)
        ]
        self._next_fit_index: int = 0
        self._allocation_count: int = 0
        self._deallocation_count: int = 0

    def get_blocks(self) -> list[MemoryBlock]:
        return list(self._blocks)

    @property
    def used_bytes(self) -> int:
        return sum(b.size for b in self._blocks if not b.is_free)

    @property
    def free_bytes(self) -> int:
        return sum(b.size for b in self._blocks if b.is_free)

    @property
    def external_fragmentation(self) -> float:
        free_blocks = [b.size for b in self._blocks if b.is_free]
        if not free_blocks:
            return 0.0
        total_free = sum(free_blocks)
        if total_free == 0:
            return 0.0
        return round(1.0 - (max(free_blocks) / total_free), 4)

    def _find_block_index(self, size: int) -> Optional[int]:
        n = len(self._blocks)
        if self.strategy == FitStrategy.FIRST_FIT:
            for i, block in enumerate(self._blocks):
                if block.is_free and block.size >= size:
                    return i
            return None

        elif self.strategy == FitStrategy.BEST_FIT:
            best_idx: Optional[int] = None
            best_size: int = float("inf")  # type: ignore[assignment]
            for i, block in enumerate(self._blocks):
                if block.is_free and block.size >= size:
                    if block.size < best_size:
                        best_size = block.size
                        best_idx = i
            return best_idx

        elif self.strategy == FitStrategy.WORST_FIT:
            worst_idx: Optional[int] = None
            worst_size: int = -1
            for i, block in enumerate(self._blocks):
                if block.is_free and block.size >= size:
                    if block.size > worst_size:
                        worst_size = block.size
                        worst_idx = i
            return worst_idx

        elif self.strategy == FitStrategy.NEXT_FIT:
            for step in range(n):
                idx = (self._next_fit_index + step) % n
                block = self._blocks[idx]
                if block.is_free and block.size >= size:
                    self._next_fit_index = idx
                    return idx
            return None

        return None

    def allocate(self, size: int, tag: str = "") -> Optional[int]:
        """Allocate a block of memory. Returns starting offset or None."""
        if size <= 0:
            raise ValueError("Allocation size must be positive")

        idx = self._find_block_index(size)
        if idx is None:
            return None

        target = self._blocks[idx]
        leftover = target.size - size

        if leftover >= self.min_split_threshold:
            allocated = MemoryBlock(
                offset=target.offset,
                size=size,
                is_free=False,
                tag=tag or f"blk_{self._allocation_count + 1}",
                requested_size=size,
            )
            free_remainder = MemoryBlock(
                offset=target.offset + size,
                size=leftover,
                is_free=True,
            )
            self._blocks[idx] = allocated
            self._blocks.insert(idx + 1, free_remainder)
            if self.strategy == FitStrategy.NEXT_FIT:
                self._next_fit_index = (idx + 1) % len(self._blocks)
        else:
            target.is_free = False
            target.tag = tag or f"blk_{self._allocation_count + 1}"
            target.requested_size = size
            if self.strategy == FitStrategy.NEXT_FIT:
                self._next_fit_index = (idx + 1) % len(self._blocks)

        self._allocation_count += 1
        return self._blocks[idx].offset

    def free(self, offset: int) -> bool:
        """Deallocate block at offset and coalesce adjacent free neighbors."""
        target_idx: Optional[int] = None
        for i, b in enumerate(self._blocks):
            if b.offset == offset:
                target_idx = i
                break

        if target_idx is None or self._blocks[target_idx].is_free:
            return False

        block = self._blocks[target_idx]
        block.is_free = True
        block.tag = ""
        block.requested_size = 0
        self._deallocation_count += 1

        # Coalesce right
        if target_idx + 1 < len(self._blocks) and self._blocks[target_idx + 1].is_free:
            right = self._blocks.pop(target_idx + 1)
            block.size += right.size

        # Coalesce left
        if target_idx - 1 >= 0 and self._blocks[target_idx - 1].is_free:
            left = self._blocks.pop(target_idx - 1)
            block.offset = left.offset
            block.size += left.size
            target_idx -= 1

        if self._next_fit_index >= len(self._blocks):
            self._next_fit_index = 0

        return True

    def render_map(self, width: int = 50) -> str:
        """Render ASCII visual memory map."""
        chars: list[str] = []
        for b in self._blocks:
            b_chars = max(1, int(round((b.size / self.total_size) * width)))
            char = "." if b.is_free else (b.tag[0].upper() if b.tag else "#")
            chars.append(char * b_chars)
        raw = "".join(chars)[:width]
        return f"[{raw:<{width}}]"

    def stats(self) -> dict[str, Any]:
        return {
            "total_size": self.total_size,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "utilization": round(self.used_bytes / self.total_size, 4),
            "external_fragmentation": self.external_fragmentation,
            "blocks": len(self._blocks),
        }


if __name__ == "__main__":
    alloc = FreeListAllocator(total_size=100, strategy=FitStrategy.FIRST_FIT)
    p1 = alloc.allocate(20, tag="A")
    p2 = alloc.allocate(30, tag="B")
    p3 = alloc.allocate(25, tag="C")
    print("Allocated A, B, C:")
    print(alloc.render_map())
    print("\nFreeing B (creates a hole):")
    alloc.free(p2)
    print(alloc.render_map())
    print(f"External Fragmentation: {alloc.external_fragmentation * 100:.1f}%")
    print("\nFreeing C (coalesces hole with tail):")
    alloc.free(p3)
    print(alloc.render_map())
