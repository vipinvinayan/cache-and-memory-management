# ⚡ Cache and Memory Management Algorithms

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Pure%20StdLib)-success.svg)](https://docs.python.org/3/)
[![No Folders Needed](https://img.shields.io/badge/Repository%20Structure-Flat%20(No%20Folders)-brightgreen.svg)](#-repository-files-flat-structure)

A high-performance, educational, and modular implementation of fundamental **Cache Replacement Algorithms** and **Operating System Memory Management Algorithms** in Python.

**Features:**
- **Flat repository structure**: Everything is in the root directory. Zero subfolders—trivially easy to drag and drop or upload directly to GitHub.
- **Strict theoretical complexities**: $\mathcal{O}(1)$ cache lookups and promotions, $\mathcal{O}(\log N)$ binary buddy system, $\mathcal{O}(1)$ slab allocation.
- **Zero external dependencies**: Built using 100% Python standard library.

---

## 📁 Repository Files (Flat Structure)

Every file is self-contained and located directly in the root directory:

| File | Description | Complexity |
| :--- | :--- | :---: |
| [`lru_cache.py`](lru_cache.py) | **Least Recently Used (LRU)** Cache (Hash Map + Doubly Linked List) | $\mathcal{O}(1)$ |
| [`lfu_cache.py`](lfu_cache.py) | **Least Frequently Used (LFU)** Cache (Dual-map frequency buckets) | $\mathcal{O}(1)$ |
| [`fifo_cache.py`](fifo_cache.py) | **First-In, First-Out (FIFO)** Cache | $\mathcal{O}(1)$ |
| [`clock_cache.py`](clock_cache.py) | **Clock / Second-Chance** Cache (Circular buffer + reference bits) | $\mathcal{O}(1)$ |
| [`arc_cache.py`](arc_cache.py) | **Adaptive Replacement Cache (ARC)** (Self-tuning $T_1/T_2/B_1/B_2$) | $\mathcal{O}(1)$ |
| [`mru_cache.py`](mru_cache.py) | **Most Recently Used (MRU)** Cache (Scan-resistant) | $\mathcal{O}(1)$ |
| [`free_list_allocator.py`](free_list_allocator.py) | **Free-List Allocator** (First-Fit, Best-Fit, Worst-Fit, Next-Fit + coalescing) | $\mathcal{O}(N)$ |
| [`buddy_allocator.py`](buddy_allocator.py) | **Binary Buddy System** (Power-of-2 split & XOR bitwise coalescing) | $\mathcal{O}(\log N)$ |
| [`slab_allocator.py`](slab_allocator.py) | **Kernel Slab Allocator** (Fixed-size object pools, zero fragmentation) | $\mathcal{O}(1)$ |
| [`paging_simulator.py`](paging_simulator.py) | **Virtual Memory MMU** (FIFO, LRU, Clock, Belady's Optimal) | $\mathcal{O}(1)$ |
| [`test_algorithms.py`](test_algorithms.py) | Complete test suite for all 10 algorithms | — |
| [`benchmark.py`](benchmark.py) | Performance and hit-rate benchmarking suite | — |
| [`main_demo.py`](main_demo.py) | Interactive step-by-step visual demonstration script | — |
| [`requirements.txt`](requirements.txt) | Optional testing requirements | — |
| [`LICENSE`](LICENSE) | MIT License | — |
| [`README.md`](README.md) | Documentation & setup guide | — |

---

## 🚀 Quick Run & Usage

Because all files are in the root directory, you can run any algorithm directly:

```bash
# 1. Run all tests (zero dependencies required)
python test_algorithms.py

# 2. Run the interactive visual demonstration
python main_demo.py

# 3. Run performance & hit-ratio benchmarks
python benchmark.py

# 4. Or run any individual algorithm directly
python lru_cache.py
python buddy_allocator.py
python paging_simulator.py
```

---

## 🧠 Code Examples

### 1. LRU & ARC Caches

```python
from lru_cache import LRUCache
from arc_cache import ARCCache

# LRU Cache
cache = LRUCache(capacity=3)
cache.put("user_1", "Alice")
cache.put("user_2", "Bob")
cache.get("user_1")  # Hit! Moves user_1 to MRU
cache.put("user_3", "Charlie")
cache.put("user_4", "David")  # Evicts user_2 (LRU)
print("user_2 in cache?", "user_2" in cache)  # False
```

### 2. Binary Buddy Memory Allocator

```python
from buddy_allocator import BuddyAllocator

# 1024-byte address space, 16-byte minimum block
buddy = BuddyAllocator(total_size=1024, min_block_size=16)

# Allocates 100 bytes -> rounds up to power-of-two (128 bytes)
ptr1 = buddy.allocate(100, tag="TaskA")
ptr2 = buddy.allocate(120, tag="TaskB")

# Freeing both blocks automatically coalesces them into a 256-byte block
buddy.free(ptr1)
buddy.free(ptr2)
```

### 3. Virtual Memory MMU Paging

```python
from paging_simulator import PagingSimulator, ReplacementAlgorithm

# 3 physical memory frames, 4KB page size
sim = PagingSimulator(num_frames=3, page_size=4096, algorithm=ReplacementAlgorithm.LRU)

# Access virtual address 0x1020 (Page 1)
res = sim.access(0x1020)
print(f"Page Fault: {res.is_page_fault}, Phys Addr: 0x{res.physical_address:04X}")
```

---

## 📤 How to Upload Directly to GitHub (No Folders Needed!)

Since every file is in the root directory, uploading to GitHub is effortless:

### Method 1: Using the GitHub Website (Fastest)
1. Go to [github.com/new](https://github.com/new) and name your repository (e.g., `cache-and-memory-management`).
2. Click **Create repository**.
3. On the next screen, click the link: **"uploading an existing file"**.
4. Open the folder on your computer:
   `C:\Users\Vipin Chandran\.gemini\antigravity\scratch\cache-and-memory-management`
5. Press `Ctrl + A` to select all files, and **drag and drop all files into your browser**.
6. Click **Commit changes**!

### Method 2: Using the Command Line
```bash
cd "C:\Users\Vipin Chandran\.gemini\antigravity\scratch\cache-and-memory-management"
git init -b main
git add *.py *.md *.txt LICENSE
git commit -m "feat: complete cache and memory management algorithms"
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
