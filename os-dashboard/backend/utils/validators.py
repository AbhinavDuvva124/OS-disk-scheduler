"""Input validators"""
from typing import List, Dict, Tuple


def validate_processes(data: List[Dict]) -> Tuple[bool, str]:
    if not data or not isinstance(data, list):
        return False, "Processes must be a non-empty list."
    if len(data) > 20:
        return False, "Maximum 20 processes allowed."
    for i, p in enumerate(data):
        try:
            bt = int(p.get("burst_time", 0))
            at = int(p.get("arrival_time", -1))
            if bt <= 0:
                return False, f"Process {i + 1}: burst_time must be > 0."
            if at < 0:
                return False, f"Process {i + 1}: arrival_time must be >= 0."
        except (ValueError, TypeError):
            return False, f"Process {i + 1}: Invalid numeric values."
    return True, ""


def validate_disk_requests(requests: List, head: int, disk_size: int) -> Tuple[bool, str]:
    if not requests:
        return False, "Disk requests cannot be empty."
    if len(requests) > 50:
        return False, "Maximum 50 disk requests allowed."
    if not (0 <= head < disk_size):
        return False, f"Head position must be between 0 and {disk_size - 1}."
    for r in requests:
        try:
            val = int(r)
            if not (0 <= val < disk_size):
                return False, f"All requests must be between 0 and {disk_size - 1}."
        except (ValueError, TypeError):
            return False, "All requests must be valid integers."
    return True, ""
