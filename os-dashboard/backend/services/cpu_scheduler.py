"""
CPU Scheduling Algorithms:
- FCFS (First Come First Served)
- SJF (Shortest Job First - Non-preemptive)
- Round Robin (RR)
- Priority Scheduling (Non-preemptive)
"""
from copy import deepcopy
from typing import List, Dict, Any
from backend.models.process import Process


def _compute_metrics(processes: List[Process]) -> Dict[str, Any]:
    n = len(processes)
    if n == 0:
        return {}

    total_turnaround = sum(p.turnaround_time for p in processes)
    total_waiting = sum(p.waiting_time for p in processes)
    total_response = sum(p.response_time for p in processes if p.response_time is not None)

    makespan = max(p.finish_time for p in processes)
    total_burst = sum(p.burst_time for p in processes)
    cpu_utilization = (total_burst / makespan * 100) if makespan > 0 else 0
    throughput = n / makespan if makespan > 0 else 0

    return {
        "avg_turnaround_time": round(total_turnaround / n, 2),
        "avg_waiting_time": round(total_waiting / n, 2),
        "avg_response_time": round(total_response / n, 2),
        "cpu_utilization": round(cpu_utilization, 2),
        "throughput": round(throughput, 4),
        "makespan": makespan,
    }


def fcfs(processes_data: List[Dict]) -> Dict[str, Any]:
    """First Come First Served"""
    procs = [Process.from_dict(p) for p in processes_data]
    procs.sort(key=lambda p: p.arrival_time)

    current_time = 0
    gantt = []

    for p in procs:
        if current_time < p.arrival_time:
            gantt.append({"pid": "IDLE", "start": current_time, "end": p.arrival_time})
            current_time = p.arrival_time

        p.start_time = current_time
        p.response_time = current_time - p.arrival_time
        p.finish_time = current_time + p.burst_time
        p.turnaround_time = p.finish_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time

        gantt.append({"pid": p.pid, "start": current_time, "end": p.finish_time})
        current_time = p.finish_time

    return {
        "algorithm": "FCFS",
        "processes": [p.to_dict() for p in procs],
        "gantt": gantt,
        "metrics": _compute_metrics(procs),
    }


def sjf(processes_data: List[Dict]) -> Dict[str, Any]:
    """Shortest Job First (Non-preemptive)"""
    procs = [Process.from_dict(p) for p in processes_data]
    completed = []
    current_time = 0
    gantt = []
    remaining = list(procs)

    while remaining:
        available = [p for p in remaining if p.arrival_time <= current_time]

        if not available:
            next_arrival = min(p.arrival_time for p in remaining)
            gantt.append({"pid": "IDLE", "start": current_time, "end": next_arrival})
            current_time = next_arrival
            continue

        shortest = min(available, key=lambda p: p.burst_time)
        remaining.remove(shortest)

        shortest.start_time = current_time
        shortest.response_time = current_time - shortest.arrival_time
        shortest.finish_time = current_time + shortest.burst_time
        shortest.turnaround_time = shortest.finish_time - shortest.arrival_time
        shortest.waiting_time = shortest.turnaround_time - shortest.burst_time

        gantt.append({"pid": shortest.pid, "start": current_time, "end": shortest.finish_time})
        current_time = shortest.finish_time
        completed.append(shortest)

    return {
        "algorithm": "SJF",
        "processes": [p.to_dict() for p in completed],
        "gantt": gantt,
        "metrics": _compute_metrics(completed),
    }


def round_robin(processes_data: List[Dict], quantum: int = 2) -> Dict[str, Any]:
    """Round Robin"""
    procs = [Process.from_dict(p) for p in processes_data]
    procs.sort(key=lambda p: p.arrival_time)

    queue = []
    completed = []
    current_time = 0
    gantt = []
    remaining = list(procs)
    in_queue = set()

    # Add processes that arrive at time 0
    for p in remaining:
        if p.arrival_time <= current_time:
            queue.append(p)
            in_queue.add(p.pid)

    while queue or remaining:
        if not queue:
            next_arrival = min(p.arrival_time for p in remaining)
            gantt.append({"pid": "IDLE", "start": current_time, "end": next_arrival})
            current_time = next_arrival
            for p in remaining:
                if p.arrival_time <= current_time and p.pid not in in_queue:
                    queue.append(p)
                    in_queue.add(p.pid)
            continue

        proc = queue.pop(0)

        if proc.start_time is None:
            proc.start_time = current_time
            proc.response_time = current_time - proc.arrival_time

        exec_time = min(quantum, proc.remaining_time)
        gantt.append({"pid": proc.pid, "start": current_time, "end": current_time + exec_time})
        current_time += exec_time
        proc.remaining_time -= exec_time

        # Add newly arrived processes
        new_arrivals = [p for p in remaining if p.arrival_time <= current_time and p.pid not in in_queue and p.pid != proc.pid]
        for p in new_arrivals:
            queue.append(p)
            in_queue.add(p.pid)

        if proc.remaining_time == 0:
            proc.finish_time = current_time
            proc.turnaround_time = proc.finish_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            remaining = [p for p in remaining if p.pid != proc.pid]
            completed.append(proc)
        else:
            queue.append(proc)

    return {
        "algorithm": "Round Robin",
        "quantum": quantum,
        "processes": [p.to_dict() for p in completed],
        "gantt": gantt,
        "metrics": _compute_metrics(completed),
    }


def priority_scheduling(processes_data: List[Dict]) -> Dict[str, Any]:
    """Priority Scheduling (Non-preemptive, lower number = higher priority)"""
    procs = [Process.from_dict(p) for p in processes_data]
    completed = []
    current_time = 0
    gantt = []
    remaining = list(procs)

    while remaining:
        available = [p for p in remaining if p.arrival_time <= current_time]

        if not available:
            next_arrival = min(p.arrival_time for p in remaining)
            gantt.append({"pid": "IDLE", "start": current_time, "end": next_arrival})
            current_time = next_arrival
            continue

        highest = min(available, key=lambda p: p.priority)
        remaining.remove(highest)

        highest.start_time = current_time
        highest.response_time = current_time - highest.arrival_time
        highest.finish_time = current_time + highest.burst_time
        highest.turnaround_time = highest.finish_time - highest.arrival_time
        highest.waiting_time = highest.turnaround_time - highest.burst_time

        gantt.append({"pid": highest.pid, "start": current_time, "end": highest.finish_time})
        current_time = highest.finish_time
        completed.append(highest)

    return {
        "algorithm": "Priority",
        "processes": [p.to_dict() for p in completed],
        "gantt": gantt,
        "metrics": _compute_metrics(completed),
    }


def run_all_algorithms(processes_data: List[Dict], quantum: int = 2) -> Dict[str, Any]:
    """Run all algorithms and return comparative results"""
    results = {
        "FCFS": fcfs(deepcopy(processes_data)),
        "SJF": sjf(deepcopy(processes_data)),
        "RR": round_robin(deepcopy(processes_data), quantum),
        "Priority": priority_scheduling(deepcopy(processes_data)),
    }
    return results
