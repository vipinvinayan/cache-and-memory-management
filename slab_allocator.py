"""Slab Allocator Implementation.

Inspired by Jeff Bonwick's original Slab Allocator design for SunOS and Linux kernels.
Partitions memory into dedicated pools for fixed-size objects (e.g. 32B, 64B, 128B).
Eliminates external fragmentation within size classes and achieves O(1) allocation/free.
"""
from __future__ import annotations
from typing import Any, Optional


class _Slab:
    def __init__(self, base_offset: int, slab_size: int, object_size: int) -> None:
        self.base_offset: int = base_offset
        self.slab_size: int = slab_size
        self.object_size: int = object_size
        self.total_objects: int = slab_size // object_size
        self.free_slots: list[int] = list(range(self.total_objects))
        self.allocated_slots: dict[int, str] = {}

    @property
    def is_full(self) -> bool:
        return len(self.free_slots) == 0

    def allocate(self, tag: str = "") -> Optional[int]:
        if not self.free_slots:
            return None
        slot_idx = self.free_slots.pop()
        self.allocated_slots[slot_idx] = tag
        return self.base_offset + (slot_idx * self.object_size)

    def free(self, offset: int) -> bool:
        rel = offset - self.base_offset
        if rel < 0 or rel >= self.slab_size or rel % self.object_size != 0:
            return False
        slot_idx = rel // self.object_size
        if slot_idx not in self.allocated_slots:
            return False
        del self.allocated_slots[slot_idx]
        self.free_slots.append(slot_idx)
        return True


class _SlabCache:
    def __init__(self, object_size: int, slab_size: int = 1024) -> None:
        self.object_size: int = object_size
        self.slab_size: int = slab_size
        self.slabs: list[_Slab] = []

    def add_slab(self, base_offset: int) -> _Slab:
        slab = _Slab(base_offset, self.slab_size, self.object_size)
        self.slabs.append(slab)
        return slab

    def allocate(self, tag: str = "") -> Optional[int]:
        for slab in self.slabs:
            if not slab.is_full:
                return slab.allocate(tag)
        return None

    def free(self, offset: int) -> bool:
        for slab in self.slabs:
            if slab.base_offset <= offset < slab.base_offset + slab.slab_size:
                return slab.free(offset)
        return False


class SlabAllocator:
    """Multi-pool Slab Allocator managing fixed-size object classes."""

    def __init__(
        self,
        total_size: int = 4096,
        slab_size: int = 1024,
        size_classes: Optional[list[int]] = None,
    ) -> None:
        self.total_size: int = total_size
        self.slab_size: int = slab_size
        self.size_classes: list[int] = sorted(size_classes or [32, 64, 128, 256])
        self.num_slabs: int = total_size // slab_size

        if self.num_slabs < len(self.size_classes):
            raise ValueError("total_size too small to hold all size class slabs")

        self._caches: dict[int, _SlabCache] = {}
        for i, sc in enumerate(self.size_classes):
            slab_cache = _SlabCache(object_size=sc, slab_size=slab_size)
            slab_cache.add_slab(base_offset=i * slab_size)
            self._caches[sc] = slab_cache

        self._ptr_to_class: dict[int, int] = {}
        self._allocation_count: int = 0
        self._deallocation_count: int = 0

    def allocate(self, size: int, tag: str = "") -> Optional[int]:
        """Allocate an object slot from the smallest suitable size class pool."""
        target_class: Optional[int] = None
        for sc in self.size_classes:
            if sc >= size:
                target_class = sc
                break

        if target_class is None:
            return None

        cache = self._caches[target_class]
        ptr = cache.allocate(tag=tag)
        if ptr is not None:
            self._ptr_to_class[ptr] = target_class
            self._allocation_count += 1
            return ptr
        return None

    def free(self, offset: int) -> bool:
        """Deallocate object pointer back to its slab pool."""
        if offset not in self._ptr_to_class:
            return False
        sc = self._ptr_to_class.pop(offset)
        success = self._caches[sc].free(offset)
        if success:
            self._deallocation_count += 1
        return success

    def stats(self) -> dict[str, Any]:
        return {
            "total_size": self.total_size,
            "size_classes": self.size_classes,
            "allocations": self._allocation_count,
            "deallocations": self._deallocation_count,
            "active_objects": len(self._ptr_to_class),
        }


if __name__ == "__main__":
    alloc = SlabAllocator(total_size=4096, slab_size=1024, size_classes=[32, 64, 128, 256])
    ptr1 = alloc.allocate(24, tag="inode_1")  # fits in 32B class
    ptr2 = alloc.allocate(30, tag="inode_2")  # fits in 32B class
    print(f"Allocated 2 objects in 32B pool: 0x{ptr1:04X}, 0x{ptr2:04X}")
    alloc.free(ptr1)
    ptr3 = alloc.allocate(20, tag="inode_3")  # recycles slot!
    print(f"Recycled slot 0x{ptr3:04X} (equal to ptr1: {ptr3 == ptr1})")
    print("Stats:", alloc.stats())
