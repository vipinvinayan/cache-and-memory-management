"""Virtual Memory Paging and Page Replacement Simulator.

Simulates MMU virtual-to-physical address translation and page fault resolution.
Compares 4 fundamental page replacement algorithms:
- FIFO
- LRU
- Clock (Second-Chance)
- Optimal (Belady's MIN algorithm)
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class ReplacementAlgorithm(str, Enum):
    FIFO = "FIFO"
    LRU = "LRU"
    CLOCK = "CLOCK"
    OPTIMAL = "OPTIMAL"


@dataclass
class PageTableEntry:
    vpn: int
    pfn: Optional[int] = None
    present: bool = False
    referenced: bool = False


@dataclass
class TranslationResult:
    virtual_address: int
    vpn: int
    offset: int
    physical_address: Optional[int]
    is_page_fault: bool
    evicted_vpn: Optional[int] = None


class PagingSimulator:
    """Simulates Virtual Memory translation and page replacement policies."""

    def __init__(
        self,
        num_frames: int = 4,
        page_size: int = 4096,
        algorithm: ReplacementAlgorithm = ReplacementAlgorithm.LRU,
    ) -> None:
        if num_frames <= 0 or page_size <= 0:
            raise ValueError("num_frames and page_size must be positive")

        self.num_frames: int = num_frames
        self.page_size: int = page_size
        self.algorithm: ReplacementAlgorithm = algorithm

        self._frames: list[Optional[int]] = [None] * num_frames
        self._page_table: dict[int, PageTableEntry] = {}

        self._fifo_queue: list[int] = []
        self._lru_access: dict[int, int] = {}
        self._clock_hand: int = 0
        self._current_time: int = 0

        self._total_accesses: int = 0
        self._page_faults: int = 0
        self._page_hits: int = 0

    @property
    def fault_rate(self) -> float:
        return self._page_faults / self._total_accesses if self._total_accesses > 0 else 0.0

    def _get_entry(self, vpn: int) -> PageTableEntry:
        if vpn not in self._page_table:
            self._page_table[vpn] = PageTableEntry(vpn=vpn)
        return self._page_table[vpn]

    def _find_free_frame(self) -> Optional[int]:
        for pfn, occupant in enumerate(self._frames):
            if occupant is None:
                return pfn
        return None

    def _select_victim(self, future_vpns: Optional[list[int]] = None) -> int:
        if self.algorithm == ReplacementAlgorithm.FIFO:
            return self._fifo_queue.pop(0)

        elif self.algorithm == ReplacementAlgorithm.LRU:
            loaded_vpns = [vpn for vpn in self._frames if vpn is not None]
            return min(loaded_vpns, key=lambda v: self._lru_access.get(v, 0))

        elif self.algorithm == ReplacementAlgorithm.CLOCK:
            while True:
                pfn = self._clock_hand
                vpn = self._frames[pfn]
                self._clock_hand = (self._clock_hand + 1) % self.num_frames
                if vpn is not None:
                    entry = self._get_entry(vpn)
                    if entry.referenced:
                        entry.referenced = False
                    else:
                        return vpn

        elif self.algorithm == ReplacementAlgorithm.OPTIMAL:
            loaded_vpns = [vpn for vpn in self._frames if vpn is not None]
            if not future_vpns:
                return min(loaded_vpns, key=lambda v: self._lru_access.get(v, 0))

            furthest_dist = -1
            victim = loaded_vpns[0]
            for vpn in loaded_vpns:
                try:
                    next_idx = future_vpns.index(vpn)
                except ValueError:
                    return vpn
                if next_idx > furthest_dist:
                    furthest_dist = next_idx
                    victim = vpn
            return victim

        raise ValueError(f"Unknown algorithm: {self.algorithm}")

    def access(
        self,
        virtual_address: int,
        future_trace: Optional[list[int]] = None,
    ) -> TranslationResult:
        """Translate virtual address to physical address, handling page faults."""
        self._total_accesses += 1
        self._current_time += 1

        vpn = virtual_address // self.page_size
        offset = virtual_address % self.page_size
        entry = self._get_entry(vpn)

        if entry.present and entry.pfn is not None:
            self._page_hits += 1
            entry.referenced = True
            self._lru_access[vpn] = self._current_time
            phys_addr = (entry.pfn * self.page_size) + offset
            return TranslationResult(
                virtual_address=virtual_address,
                vpn=vpn,
                offset=offset,
                physical_address=phys_addr,
                is_page_fault=False,
            )

        self._page_faults += 1
        free_pfn = self._find_free_frame()
        evicted_vpn: Optional[int] = None

        if free_pfn is not None:
            pfn = free_pfn
        else:
            victim_vpn = self._select_victim(future_vpns=future_trace)
            evicted_vpn = victim_vpn
            victim_entry = self._get_entry(victim_vpn)
            pfn = victim_entry.pfn  # type: ignore[assignment]
            victim_entry.present = False
            victim_entry.pfn = None
            if victim_vpn in self._lru_access:
                del self._lru_access[victim_vpn]

        self._frames[pfn] = vpn
        entry.present = True
        entry.pfn = pfn
        entry.referenced = True
        self._lru_access[vpn] = self._current_time

        if self.algorithm == ReplacementAlgorithm.FIFO:
            self._fifo_queue.append(vpn)

        phys_addr = (pfn * self.page_size) + offset
        return TranslationResult(
            virtual_address=virtual_address,
            vpn=vpn,
            offset=offset,
            physical_address=phys_addr,
            is_page_fault=True,
            evicted_vpn=evicted_vpn,
        )

    def stats(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm.value,
            "frames": self.num_frames,
            "accesses": self._total_accesses,
            "page_hits": self._page_hits,
            "page_faults": self._page_faults,
            "fault_rate": round(self.fault_rate, 4),
        }


if __name__ == "__main__":
    trace = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    print(f"Reference Page Trace: {trace}")
    for algo in [ReplacementAlgorithm.FIFO, ReplacementAlgorithm.LRU, ReplacementAlgorithm.CLOCK, ReplacementAlgorithm.OPTIMAL]:
        sim = PagingSimulator(num_frames=3, page_size=4096, algorithm=algo)
        for i, page in enumerate(trace):
            va = page * 4096 + 0x10
            future = trace[i + 1:] if algo == ReplacementAlgorithm.OPTIMAL else None
            sim.access(va, future_trace=future)
        st = sim.stats()
        print(f"  {algo.value:<8} -> Page Faults: {st['page_faults']:<2} (Fault rate: {st['fault_rate'] * 100:.1f}%)")
