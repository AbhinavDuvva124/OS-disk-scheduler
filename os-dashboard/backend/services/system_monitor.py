import psutil
import time


def get_cpu_info():
    cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_freq = psutil.cpu_freq()
    cpu_times = psutil.cpu_times_percent(interval=0.1)
    core_count = psutil.cpu_count(logical=False)
    logical_count = psutil.cpu_count(logical=True)

    return {
        "overall": psutil.cpu_percent(interval=0.1),
        "per_core": cpu_percent,
        "frequency": {
            "current": round(cpu_freq.current, 2) if cpu_freq else 0,
            "min": round(cpu_freq.min, 2) if cpu_freq else 0,
            "max": round(cpu_freq.max, 2) if cpu_freq else 0,
        },
        "times": {
            "user": cpu_times.user,
            "system": cpu_times.system,
            "idle": cpu_times.idle,
        },
        "core_count": core_count,
        "logical_count": logical_count,
        "load_avg": [round(x, 2) for x in psutil.getloadavg()] if hasattr(psutil, "getloadavg") else [0, 0, 0],
    }


def get_memory_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "percent": swap.percent,
            "total_gb": round(swap.total / (1024 ** 3), 2),
            "used_gb": round(swap.used / (1024 ** 3), 2),
        },
    }


def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "percent": usage.percent,
            })
        except PermissionError:
            continue

    io = psutil.disk_io_counters()
    return {
        "partitions": disks,
        "io": {
            "read_bytes": io.read_bytes if io else 0,
            "write_bytes": io.write_bytes if io else 0,
            "read_count": io.read_count if io else 0,
            "write_count": io.write_count if io else 0,
        } if io else {},
    }


def get_network_info():
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "bytes_sent_mb": round(net.bytes_sent / (1024 ** 2), 2),
        "bytes_recv_mb": round(net.bytes_recv / (1024 ** 2), 2),
    }


def get_top_processes(limit=10):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'num_threads']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "cpu_percent": round(info['cpu_percent'] or 0, 2),
                "memory_percent": round(info['memory_percent'] or 0, 2),
                "status": info['status'],
                "threads": info['num_threads'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:limit]


def get_system_overview():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    return {
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_disk_info(),
        "network": get_network_info(),
        "uptime": f"{hours}h {minutes}m",
        "uptime_seconds": uptime_seconds,
        "process_count": len(psutil.pids()),
        "top_processes": get_top_processes(),
    }
