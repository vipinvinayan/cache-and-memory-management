"""Complete test suite for all cache and memory management algorithms.

Runs with pure Python standard library:
    python test_algorithms.py
"""
import unittest

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


class TestCacheAlgorithms(unittest.TestCase):
    def test_lru(self):
        c = LRUCache[str, int](capacity=2)
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(c.get("a"), 1)
        c.put("c", 3)  # evicts b
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)

    def test_lfu(self):
        c = LFUCache[str, int](capacity=2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")
        c.get("a")
        c.put("c", 3)  # evicts b (lower freq)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)

    def test_fifo(self):
        c = FIFOCache[str, int](capacity=2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")
        c.put("c", 3)  # evicts a (first inserted)
        self.assertNotIn("a", c)
        self.assertIn("b", c)

    def test_clock(self):
        c = ClockCache[str, int](capacity=2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")  # referenced=True
        c.put("c", 3)  # evicts b
        self.assertNotIn("b", c)
        self.assertIn("a", c)

    def test_arc(self):
        c = ARCCache[str, int](capacity=3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        c.put("d", 4)  # evicts a to b1
        self.assertNotIn("a", c)
        c.put("a", 10)  # ghost hit
        self.assertEqual(c.get("a"), 10)

    def test_mru(self):
        c = MRUCache[str, int](capacity=2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)  # evicts b (MRU)
        self.assertNotIn("b", c)
        self.assertIn("a", c)


class TestMemoryAlgorithms(unittest.TestCase):
    def test_free_list(self):
        alloc = FreeListAllocator(total_size=100, strategy=FitStrategy.FIRST_FIT)
        p1 = alloc.allocate(20, tag="A")
        p2 = alloc.allocate(30, tag="B")
        p3 = alloc.allocate(20, tag="C")
        self.assertEqual(p1, 0)
        self.assertEqual(p2, 20)
        self.assertEqual(p3, 50)
        self.assertTrue(alloc.free(p2))
        self.assertTrue(alloc.free(p3))  # coalesces with p2 and tail
        self.assertEqual(alloc.used_bytes, 20)
        self.assertEqual(alloc.free_bytes, 80)

    def test_buddy_allocator(self):
        buddy = BuddyAllocator(total_size=1024, min_block_size=16)
        p1 = buddy.allocate(100)  # rounds to 128
        p2 = buddy.allocate(120)  # rounds to 128
        self.assertEqual(p1, 0)
        self.assertEqual(p2, 128)
        self.assertTrue(buddy.free(p1))
        self.assertTrue(buddy.free(p2))
        self.assertEqual(buddy.used_bytes, 0)

    def test_slab_allocator(self):
        slab = SlabAllocator(total_size=4096, slab_size=1024, size_classes=[32, 64])
        p1 = slab.allocate(24)
        self.assertIsNotNone(p1)
        self.assertTrue(slab.free(p1))
        p2 = slab.allocate(24)
        self.assertEqual(p1, p2)  # recycled slot

    def test_paging_simulator(self):
        sim = PagingSimulator(num_frames=2, page_size=1000, algorithm=ReplacementAlgorithm.FIFO)
        r1 = sim.access(0)     # Fault (VPN 0)
        r2 = sim.access(1000)  # Fault (VPN 1)
        r3 = sim.access(500)   # Hit   (VPN 0)
        self.assertTrue(r1.is_page_fault)
        self.assertTrue(r2.is_page_fault)
        self.assertFalse(r3.is_page_fault)


if __name__ == "__main__":
    unittest.main()
