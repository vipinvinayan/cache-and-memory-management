"""Comprehensive benchmark runner for cache and memory allocators.

Run directly:
    python benchmark.py
"""
import random
import time

from lru_cache import LRUCache
from lfu_cache import LFUCache
from fifo_cache import FIFOCache
from clock_cache import ClockCache
from arc_cache import ARCCache
from mru_cache import MRUCache
from free_list_allocator import FreeListAllocator, FitStrategy
from buddy_allocator import BuddyAllocator
from slab_allocator import SlabAllocator


def benchmark_caches():
    print("=" * 70)
    print("           CACHE ALGORITHM BENCHMARK")
    print("=" * 70)

    capacity = 50
    workload_size = 5000
    unique_keys = 200

    # Zipfian (80/20 skew)
    weights = [1.0 / (i ** 1.2) for i in range(1, unique_keys + 1)]
    sum_w = sum(weights)
    probs = [w / sum_w for w in weights]
    keys = [f"k_{i}" for i in range(1, unique_keys + 1)]
    zipf_workload = random.choices(keys, weights=probs, k=workload_size)

    # Cyclic scan (Loop > Cache)
    loop_keys = [f"loop_{i}" for i in range(60)]
    loop_workload = [loop_keys[i % 60] for i in range(workload_size)]

    factories = {
        "LRU": lambda cap: LRUCache[str, int](cap),
        "LFU": lambda cap: LFUCache[str, int](cap),
        "FIFO": lambda cap: FIFOCache[str, int](cap),
        "Clock": lambda cap: ClockCache[str, int](cap),
        "ARC": lambda cap: ARCCache[str, int](cap),
        "MRU": lambda cap: MRUCache[str, int](cap),
    }

    for name, wl in [("Zipfian (80/20 Skew)", zipf_workload), ("Cyclic Loop (Loop > Cache)", loop_workload)]:
        print(f"\n--- Workload: {name} (Requests: {len(wl)}, Capacity: {capacity}) ---")
        print(f"{'Algorithm':<10} | {'Hits':<8} | {'Misses':<8} | {'Hit Ratio':<10} | {'Time (ms)':<10}")
        print("-" * 55)

        for algo_name, factory in factories.items():
            cache = factory(capacity)
            t0 = time.perf_counter()
            for k in wl:
                if cache.get(k) is None:
                    cache.put(k, 1)
            t_ms = (time.perf_counter() - t0) * 1000

            st = cache.stats()
            print(f"{algo_name:<10} | {st['hits']:<8} | {st['misses']:<8} | {st['hit_ratio']*100:>8.2f}% | {t_ms:>8.2f}ms")


def benchmark_allocators():
    print("\n" + "=" * 70)
    print("        MEMORY ALLOCATOR BENCHMARK (64KB Address Space)")
    print("=" * 70)

    total_mem = 65536
    num_ops = 2000
    sizes = [random.choice([32, 64, 128, 256]) for _ in range(num_ops)]

    allocators = {
        "FreeList (First-Fit)": FreeListAllocator(total_mem, strategy=FitStrategy.FIRST_FIT),
        "FreeList (Best-Fit)": FreeListAllocator(total_mem, strategy=FitStrategy.BEST_FIT),
        "Buddy System": BuddyAllocator(total_mem, min_block_size=16),
        "Slab Allocator": SlabAllocator(total_mem, slab_size=16384, size_classes=[32, 64, 128, 256]),
    }

    print(f"{'Allocator':<24} | {'Throughput (ops/sec)':<20} | {'Status'}")
    print("-" * 60)

    for name, alloc in allocators.items():
        live = []
        t0 = time.perf_counter()
        for sz in sizes:
            p = alloc.allocate(sz)
            if p is not None:
                live.append(p)
            if len(live) > 20 and random.random() < 0.4:
                victim = live.pop(random.randrange(len(live)))
                alloc.free(victim)
        for p in live:
            alloc.free(p)
        dur = time.perf_counter() - t0
        ops_sec = num_ops / dur if dur > 0 else 0
        print(f"{name:<24} | {ops_sec:>18.1f} | Finished")


if __name__ == "__main__":
    random.seed(42)
    benchmark_caches()
    benchmark_allocators()
