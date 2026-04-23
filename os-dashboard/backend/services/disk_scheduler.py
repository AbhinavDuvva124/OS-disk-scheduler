"""
Enhanced Disk Scheduling Algorithms:
- FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK, N-Step SCAN, FSCAN
- Realistic seek time model (linear + non-linear cost)
- Priority & deadline-aware scheduling
- Enhanced metrics: variance, max seek, fairness index, starvation detection
"""
import math
from typing import List, Dict, Any, Optional


# ─── Realistic Seek Time Model ───────────────────────────────────────────────
SEEK_LINEAR_COEFF  = 1.0     # ms per cylinder
SEEK_SQRT_COEFF    = 0.8     # ms per sqrt(cylinders)  – head acceleration
SEEK_SETTLE_TIME   = 1.5     # ms – fixed head-settle overhead
MAX_ROTATIONAL_LAT = 4.2     # ms – average rotational latency

def seek_cost(distance: int) -> float:
    """Realistic seek time: linear + sqrt component + settle + rotational."""
    if distance == 0:
        return round(MAX_ROTATIONAL_LAT, 3)
    t = (SEEK_LINEAR_COEFF * distance
         + SEEK_SQRT_COEFF * math.sqrt(distance)
         + SEEK_SETTLE_TIME
         + MAX_ROTATIONAL_LAT)
    return round(t, 3)


# ─── Metrics Helper ──────────────────────────────────────────────────────────
def build_metrics(movements: List[Dict], requests: List[int]) -> Dict[str, Any]:
    seeks = [m["seek"] for m in movements if not m.get("wrap", False)]
    if not seeks:
        return {}
    total       = sum(seeks)
    n           = len(seeks)
    avg         = total / n
    variance    = sum((s - avg) ** 2 for s in seeks) / n
    max_seek    = max(seeks)
    min_seek    = min(seeks)

    # Jain's Fairness Index  (1 = perfectly fair)
    sum_sq = sum(s ** 2 for s in seeks)
    fairness = (sum(seeks) ** 2) / (n * sum_sq) if sum_sq else 1.0

    # Starvation: any request served after waiting > threshold
    STARVATION_THRESH = 5  # number of steps
    starvation_warnings = []
    served_positions = [m["to"] for m in movements if not m.get("wrap", False)]
    for req in requests:
        try:
            wait_steps = served_positions.index(req)
            if wait_steps > STARVATION_THRESH:
                starvation_warnings.append({"track": req, "wait_steps": wait_steps})
        except ValueError:
            pass

    # Realistic total time (ms)
    total_time_ms = round(
        sum(seek_cost(m["seek"]) for m in movements if not m.get("wrap", False)), 2
    )

    return {
        "total_seek":           total,
        "avg_seek":             round(avg, 3),
        "max_seek":             max_seek,
        "min_seek":             min_seek,
        "seek_variance":        round(variance, 3),
        "fairness_index":       round(fairness, 4),
        "starvation_warnings":  starvation_warnings,
        "total_time_ms":        total_time_ms,
        "n_moves":              n,
    }


def _base_result(algo: str, head: int, seq: List[int],
                 movements: List[Dict], requests: List[int]) -> Dict[str, Any]:
    metrics = build_metrics(movements, requests)
    return {
        "algorithm":    algo,
        "head_start":   head,
        "seek_sequence": seq,
        "movements":    movements,
        **metrics,
    }


# ─── Utility ─────────────────────────────────────────────────────────────────
def _mv(frm: int, to: int, wrap=False) -> Dict:
    d = abs(to - frm)
    return {"from": frm, "to": to, "seek": d,
            "cost_ms": seek_cost(d), "wrap": wrap}


# ══════════════════════════════════════════════════════════════════════════════
# CORE ALGORITHMS
# ══════════════════════════════════════════════════════════════════════════════

def fcfs_disk(requests: List[int], head: int) -> Dict[str, Any]:
    cur, seq, mvs = head, [head], []
    for r in requests:
        mvs.append(_mv(cur, r))
        cur = r; seq.append(cur)
    return _base_result("FCFS", head, seq, mvs, requests)


def sstf_disk(requests: List[int], head: int) -> Dict[str, Any]:
    remaining, cur, seq, mvs = list(requests), head, [head], []
    while remaining:
        closest = min(remaining, key=lambda x: abs(x - cur))
        mvs.append(_mv(cur, closest))
        remaining.remove(closest)
        cur = closest; seq.append(cur)
    return _base_result("SSTF", head, seq, mvs, requests)


def scan_disk(requests: List[int], head: int,
              direction: str = "right", disk_size: int = 200) -> Dict[str, Any]:
    cur, seq, mvs = head, [head], []
    left  = sorted([r for r in requests if r <  head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    if direction == "right":
        for r in right:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
        if right or left:
            mvs.append(_mv(cur, disk_size - 1)); cur = disk_size - 1; seq.append(cur)
        for r in left:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
    else:
        for r in left:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
        if left or right:
            mvs.append(_mv(cur, 0)); cur = 0; seq.append(cur)
        for r in right:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)

    return _base_result("SCAN", head, seq, mvs, requests)


def cscan_disk(requests: List[int], head: int, disk_size: int = 200) -> Dict[str, Any]:
    cur, seq, mvs = head, [head], []
    right = sorted([r for r in requests if r >= head])
    left  = sorted([r for r in requests if r <  head])

    for r in right:
        mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
    mvs.append(_mv(cur, disk_size - 1)); cur = disk_size - 1; seq.append(cur)
    mvs.append(_mv(cur, 0, wrap=True));  cur = 0;             seq.append(cur)
    for r in left:
        mvs.append(_mv(cur, r)); cur = r; seq.append(cur)

    return _base_result("C-SCAN", head, seq, mvs, requests)


def look_disk(requests: List[int], head: int,
              direction: str = "right") -> Dict[str, Any]:
    """LOOK: like SCAN but only goes as far as the last request."""
    cur, seq, mvs = head, [head], []
    left  = sorted([r for r in requests if r <  head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    if direction == "right":
        for r in right:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
        for r in left:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
    else:
        for r in left:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
        for r in right:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)

    return _base_result("LOOK", head, seq, mvs, requests)


def clook_disk(requests: List[int], head: int) -> Dict[str, Any]:
    """C-LOOK: circular LOOK — always sweeps right then jumps to smallest."""
    cur, seq, mvs = head, [head], []
    right = sorted([r for r in requests if r >= head])
    left  = sorted([r for r in requests if r <  head])

    for r in right:
        mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
    if left:
        mvs.append(_mv(cur, left[0], wrap=True)); cur = left[0]; seq.append(cur)
        for r in left[1:]:
            mvs.append(_mv(cur, r)); cur = r; seq.append(cur)

    return _base_result("C-LOOK", head, seq, mvs, requests)


def nstep_scan_disk(requests: List[int], head: int,
                    n: int = 4, disk_size: int = 200) -> Dict[str, Any]:
    """N-Step SCAN: Divide queue into sub-queues of size N; process each with SCAN."""
    cur, seq, mvs = head, [head], []
    direction = "right"
    chunks = [requests[i:i+n] for i in range(0, len(requests), n)]

    for chunk in chunks:
        left  = sorted([r for r in chunk if r <  cur], reverse=True)
        right = sorted([r for r in chunk if r >= cur])
        if direction == "right":
            for r in right:
                mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
            if right or left:
                mvs.append(_mv(cur, disk_size - 1)); cur = disk_size - 1; seq.append(cur)
            for r in left:
                mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
            direction = "left"
        else:
            for r in left:
                mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
            if left or right:
                mvs.append(_mv(cur, 0)); cur = 0; seq.append(cur)
            for r in right:
                mvs.append(_mv(cur, r)); cur = r; seq.append(cur)
            direction = "right"

    return _base_result("N-Step SCAN", head, seq, mvs, requests)


def fscan_disk(requests: List[int], head: int, disk_size: int = 200) -> Dict[str, Any]:
    """FSCAN: Two sub-queues. Serve Q1 with SCAN; Q2 (new arrivals) queued for next pass."""
    mid = len(requests) // 2
    q1  = requests[:mid] if mid else requests
    q2  = requests[mid:] if mid < len(requests) else []
    cur, seq, mvs = head, [head], []

    def _do_scan(queue, cur_pos, dir_="right"):
        c = cur_pos; s = []; m = []
        l = sorted([r for r in queue if r <  c], reverse=True)
        r = sorted([r for r in queue if r >= c])
        if dir_ == "right":
            for x in r: m.append(_mv(c, x)); c = x; s.append(c)
            if r or l: m.append(_mv(c, disk_size - 1)); c = disk_size - 1; s.append(c)
            for x in l: m.append(_mv(c, x)); c = x; s.append(c)
        else:
            for x in l: m.append(_mv(c, x)); c = x; s.append(c)
            if l or r: m.append(_mv(c, 0)); c = 0; s.append(c)
            for x in r: m.append(_mv(c, x)); c = x; s.append(c)
        return c, s, m

    if q1:
        cur, s1, m1 = _do_scan(q1, cur, "right")
        seq += s1; mvs += m1
    if q2:
        cur, s2, m2 = _do_scan(q2, cur, "left")
        seq += s2; mvs += m2

    return _base_result("FSCAN", head, seq, mvs, requests)


# ─── Priority-Based Scheduling ───────────────────────────────────────────────
def priority_disk(req_list: List[Dict], head: int) -> Dict[str, Any]:
    """
    Priority disk: higher priority requests served first (among reachable),
    within same priority use SSTF.
    req_list: [{"track": int, "priority": int, "deadline": optional float}]
    """
    remaining = [dict(r) for r in req_list]
    cur, seq, mvs = head, [head], []

    while remaining:
        max_pri = max(r["priority"] for r in remaining)
        candidates = [r for r in remaining if r["priority"] == max_pri]
        chosen = min(candidates, key=lambda x: abs(x["track"] - cur))
        mvs.append(_mv(cur, chosen["track"]))
        remaining.remove(chosen)
        cur = chosen["track"]; seq.append(cur)

    tracks = [r["track"] for r in req_list]
    return _base_result("Priority", head, seq, mvs, tracks)


def deadline_disk(req_list: List[Dict], head: int) -> Dict[str, Any]:
    """
    EDF (Earliest Deadline First) disk scheduling.
    req_list: [{"track": int, "deadline": float, "priority": int}]
    """
    remaining = [dict(r) for r in req_list]
    cur, seq, mvs = head, [head], []

    while remaining:
        chosen = min(remaining, key=lambda x: x.get("deadline", float("inf")))
        mvs.append(_mv(cur, chosen["track"]))
        remaining.remove(chosen)
        cur = chosen["track"]; seq.append(cur)

    tracks = [r["track"] for r in req_list]
    return _base_result("EDF", head, seq, mvs, tracks)


# ─── Run All ─────────────────────────────────────────────────────────────────
ALL_ALGOS = ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK", "N-Step SCAN", "FSCAN"]

def run_all_disk_algorithms(requests: List[int], head: int,
                             disk_size: int = 200, n_step: int = 4) -> Dict[str, Any]:
    return {
        "FCFS":         fcfs_disk(list(requests), head),
        "SSTF":         sstf_disk(list(requests), head),
        "SCAN":         scan_disk(list(requests), head, "right", disk_size),
        "CSCAN":        cscan_disk(list(requests), head, disk_size),
        "LOOK":         look_disk(list(requests), head, "right"),
        "CLOOK":        clook_disk(list(requests), head),
        "NSTEP":        nstep_scan_disk(list(requests), head, n_step, disk_size),
        "FSCAN":        fscan_disk(list(requests), head, disk_size),
    }
