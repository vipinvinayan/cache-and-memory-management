"""Comprehensive demonstration of all cache and memory management algorithms.

Run directly:
    python main_demo.py
"""
from lru_cache import LRUCache
from lfu_cache import LFUCache
from fifo_cache import FIFOCache
from clock_cache import ClockCache
from arc_cache import ARCCache
from mru_cache import MRUCache
from free_list_allocator import FreeListAllocator, FitStrategy
from buddy_allocator import BuddyAllocator
from slab_allocator import SlabAllocator
from paging_simulator import PagingSimulator, ReplacementAlgorithm


def run_cache_demo():
    print("=" * 65)
    print(" 1. CACHE REPLACEMENT ALGORITHMS DEMONSTRATION")
    print("=" * 65)

    trace = ["A", "B", "C", "A", "D", "B", "E", "C"]
    capacity = 3
    print(f"Capacity: {capacity}")
    print(f"Access Sequence: {' -> '.join(trace)}\n")

    caches = {
        "LRU": LRUCache[str, str](capacity),
        "LFU": LFUCache[str, str](capacity),
        "FIFO": FIFOCache[str, str](capacity),
        "Clock": ClockCache[str, str](capacity),
        "ARC": ARCCache[str, str](capacity),
        "MRU": MRUCache[str, str](capacity),
    }

    for name, c in caches.items():
        for item in trace:
            if c.get(item) is None:
                c.put(item, f"val_{item}")
        st = c.stats()
        print(f"  {name:<6} -> Hits: {st['hits']}, Misses: {st['misses']}, Hit Ratio: {st['hit_ratio']*100:.1f}%")


def run_memory_demo():
    print("\n" + "=" * 65)
    print(" 2. MEMORY ALLOCATION & FRAGMENTATION DEMO")
    print("=" * 65)

    # Free List with ASCII Map
    print("[A] Free-List Allocator (100 Bytes):")
    fl = FreeListAllocator(total_size=100, strategy=FitStrategy.FIRST_FIT)
    p1 = fl.allocate(25, tag="A")
    p2 = fl.allocate(30, tag="B")
    p3 = fl.allocate(20, tag="C")
    print("  Allocated A(25B), B(30B), C(20B):", fl.render_map(40))
    fl.free(p2)
    print("  Freed B (creates hole/fragment) :", fl.render_map(40))
    print(f"  External Fragmentation: {fl.external_fragmentation * 100:.1f}%")
    fl.free(p3)
    print("  Freed C (coalesces with B & tail):", fl.render_map(40))

    # Buddy System
    print("\n[B] Binary Buddy System (512 Bytes):")
    buddy = BuddyAllocator(total_size=512, min_block_size=32)
    b1 = buddy.allocate(40, tag="Proc1")
    b2 = buddy.allocate(110, tag="Proc2")
    print(f"  Allocated Proc1 (40B -> 64B) at 0x{b1:04X}")
    print(f"  Allocated Proc2 (110B -> 128B) at 0x{b2:04X}")
    print(f"  Internal Fragmentation: {buddy.total_internal_fragmentation}B")
    buddy.free(b1)
    buddy.free(b2)
    print("  Freed Proc1 and Proc2: Memory coalesced back into 512B single block.")

    # Paging MMU
    print("\n[C] Virtual Memory Paging (3 Frames, Belady's comparison):")
    page_trace = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    for algo in [ReplacementAlgorithm.FIFO, ReplacementAlgorithm.LRU, ReplacementAlgorithm.CLOCK, ReplacementAlgorithm.OPTIMAL]:
        sim = PagingSimulator(num_frames=3, page_size=4096, algorithm=algo)
        for i, page in enumerate(page_trace):
            va = page * 4096 + 0x20
            future = page_trace[i + 1:] if algo == ReplacementAlgorithm.OPTIMAL else None
            sim.access(va, future_trace=future)
        st = sim.stats()
        print(f"  {algo.value:<8} -> Page Faults: {st['page_faults']:<2} (Fault Rate: {st['fault_rate']*100:.1f}%)")


if __name__ == "__main__":
    run_cache_demo()
    run_memory_demo()
