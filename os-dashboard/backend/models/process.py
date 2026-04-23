from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 1
    remaining_time: int = field(init=False)
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: Optional[int] = None

    def __post_init__(self):
        self.remaining_time = self.burst_time

    def to_dict(self):
        return {
            "pid": self.pid,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "start_time": self.start_time,
            "finish_time": self.finish_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Process":
        return cls(
            pid=str(data["pid"]),
            arrival_time=int(data["arrival_time"]),
            burst_time=int(data["burst_time"]),
            priority=int(data.get("priority", 1)),
        )
