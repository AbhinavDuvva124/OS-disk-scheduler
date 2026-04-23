from flask import Blueprint, jsonify, request
from backend.services import disk_scheduler
from backend.utils.validators import validate_disk_requests
from backend.utils.disk_analysis import analyze_disk_algorithms, smart_workload_recommendation
import random

disk_bp = Blueprint("disk", __name__, url_prefix="/api/disk")

DISK_ALGO_MAP = {
    "fcfs":   disk_scheduler.fcfs_disk,
    "sstf":   disk_scheduler.sstf_disk,
    "scan":   disk_scheduler.scan_disk,
    "cscan":  disk_scheduler.cscan_disk,
    "look":   disk_scheduler.look_disk,
    "clook":  disk_scheduler.clook_disk,
    "nstep":  disk_scheduler.nstep_scan_disk,
    "fscan":  disk_scheduler.fscan_disk,
}


def _parse_body():
    body = request.get_json()
    if not body:
        return None, jsonify({"status": "error", "message": "No JSON body"}), 400
    return body, None, None


@disk_bp.route("/schedule", methods=["POST"])
def schedule():
    body, err, code = _parse_body()
    if err: return err, code

    requests_list = body.get("requests", [])
    head       = int(body.get("head", 50))
    algorithm  = body.get("algorithm", "fcfs").lower()
    disk_size  = int(body.get("disk_size", 200))
    direction  = body.get("direction", "right")
    n_step     = int(body.get("n_step", 4))

    valid, err_msg = validate_disk_requests(requests_list, head, disk_size)
    if not valid:
        return jsonify({"status": "error", "message": err_msg}), 422

    if algorithm not in DISK_ALGO_MAP:
        return jsonify({"status": "error", "message": f"Unknown algorithm: {algorithm}"}), 400

    try:
        reqs = [int(r) for r in requests_list]
        if algorithm == "scan":
            result = disk_scheduler.scan_disk(reqs, head, direction, disk_size)
        elif algorithm == "cscan":
            result = disk_scheduler.cscan_disk(reqs, head, disk_size)
        elif algorithm == "look":
            result = disk_scheduler.look_disk(reqs, head, direction)
        elif algorithm == "nstep":
            result = disk_scheduler.nstep_scan_disk(reqs, head, n_step, disk_size)
        elif algorithm == "fscan":
            result = disk_scheduler.fscan_disk(reqs, head, disk_size)
        else:
            result = DISK_ALGO_MAP[algorithm](reqs, head)
        return jsonify({"status": "ok", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@disk_bp.route("/compare", methods=["POST"])
def compare():
    body, err, code = _parse_body()
    if err: return err, code

    requests_list = body.get("requests", [])
    head      = int(body.get("head", 50))
    disk_size = int(body.get("disk_size", 200))
    n_step    = int(body.get("n_step", 4))

    valid, err_msg = validate_disk_requests(requests_list, head, disk_size)
    if not valid:
        return jsonify({"status": "error", "message": err_msg}), 422

    try:
        reqs = [int(r) for r in requests_list]
        results  = disk_scheduler.run_all_disk_algorithms(reqs, head, disk_size, n_step)
        analysis = analyze_disk_algorithms(results)
        return jsonify({"status": "ok", "data": results, "analysis": analysis})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@disk_bp.route("/priority", methods=["POST"])
def priority():
    body, err, code = _parse_body()
    if err: return err, code

    req_list  = body.get("requests", [])
    head      = int(body.get("head", 50))
    mode      = body.get("mode", "priority")   # "priority" | "deadline"

    if not req_list:
        return jsonify({"status": "error", "message": "No requests"}), 422

    try:
        if mode == "deadline":
            result = disk_scheduler.deadline_disk(req_list, head)
        else:
            result = disk_scheduler.priority_disk(req_list, head)
        return jsonify({"status": "ok", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@disk_bp.route("/recommend", methods=["POST"])
def recommend():
    body, err, code = _parse_body()
    if err: return err, code

    requests_list = body.get("requests", [])
    head      = int(body.get("head", 50))
    disk_size = int(body.get("disk_size", 200))

    try:
        reqs = [int(r) for r in requests_list]
        rec  = smart_workload_recommendation(reqs, head, disk_size)
        return jsonify({"status": "ok", "data": rec})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@disk_bp.route("/generate", methods=["POST"])
def generate():
    """Generate workload patterns: random, sequential, clustered, heavy, scatter."""
    body, err, code = _parse_body()
    if err: return err, code

    pattern   = body.get("pattern", "random")
    count     = min(int(body.get("count", 12)), 50)
    disk_size = int(body.get("disk_size", 200))

    try:
        reqs = _generate_workload(pattern, count, disk_size)
        head = random.randint(0, disk_size - 1)
        return jsonify({"status": "ok", "data": {"requests": reqs, "head": head}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@disk_bp.route("/race", methods=["POST"])
def race():
    """Run all algorithms simultaneously and return side-by-side results."""
    body, err, code = _parse_body()
    if err: return err, code

    requests_list = body.get("requests", [])
    head      = int(body.get("head", 50))
    disk_size = int(body.get("disk_size", 200))
    n_step    = int(body.get("n_step", 4))

    valid, err_msg = validate_disk_requests(requests_list, head, disk_size)
    if not valid:
        return jsonify({"status": "error", "message": err_msg}), 422

    try:
        reqs    = [int(r) for r in requests_list]
        results = disk_scheduler.run_all_disk_algorithms(reqs, head, disk_size, n_step)
        # Sort by total seek for ranking
        ranked  = sorted(results.items(), key=lambda x: x[1]["total_seek"])
        ranking = [{"rank": i+1, "algo": k, "total_seek": v["total_seek"],
                    "total_time_ms": v.get("total_time_ms", 0),
                    "fairness_index": v.get("fairness_index", 0)}
                   for i, (k, v) in enumerate(ranked)]
        analysis = analyze_disk_algorithms(results)
        return jsonify({"status": "ok", "data": results, "ranking": ranking, "analysis": analysis})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def _generate_workload(pattern: str, count: int, disk_size: int):
    if pattern == "sequential":
        start = random.randint(0, disk_size // 3)
        step  = random.randint(5, 20)
        return [min(start + i * step, disk_size - 1) for i in range(count)]

    elif pattern == "clustered":
        clusters = 3
        centers  = [random.randint(10, disk_size - 10) for _ in range(clusters)]
        reqs     = []
        for _ in range(count):
            c = random.choice(centers)
            reqs.append(max(0, min(disk_size - 1, c + random.randint(-15, 15))))
        return reqs

    elif pattern == "heavy":
        # Bimodal: lots of requests near two hot spots
        hot1 = random.randint(20, 80)
        hot2 = random.randint(120, 180)
        reqs = []
        for _ in range(count):
            center = random.choice([hot1, hot2])
            reqs.append(max(0, min(disk_size - 1, center + random.randint(-10, 10))))
        return reqs

    elif pattern == "scatter":
        return random.sample(range(disk_size), min(count, disk_size))

    else:  # random
        return [random.randint(0, disk_size - 1) for _ in range(count)]
