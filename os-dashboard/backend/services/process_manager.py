"""
Process Manager - Handles process lifecycle and state management
"""
from typing import List, Dict, Any
from backend.models.process import Process


class ProcessManager:
    def __init__(self):
        self._processes: Dict[str, Process] = {}
        self._next_pid = 1

    def add_process(self, arrival_time: int, burst_time: int, priority: int = 1) -> Process:
        pid = f"P{self._next_pid}"
        self._next_pid += 1
        proc = Process(pid=pid, arrival_time=arrival_time, burst_time=burst_time, priority=priority)
        self._processes[pid] = proc
        return proc

    def get_all(self) -> List[Dict]:
        return [p.to_dict() for p in self._processes.values()]

    def clear(self):
        self._processes.clear()
        self._next_pid = 1

    def get_process(self, pid: str) -> Dict:
        proc = self._processes.get(pid)
        return proc.to_dict() if proc else None

    def validate_processes(self, processes_data: List[Dict]) -> List[str]:
        errors = []
        for i, p in enumerate(processes_data):
            if "burst_time" not in p or int(p.get("burst_time", 0)) <= 0:
                errors.append(f"Process {i + 1}: burst_time must be > 0")
            if "arrival_time" not in p or int(p.get("arrival_time", 0)) < 0:
                errors.append(f"Process {i + 1}: arrival_time must be >= 0")
        return errors
