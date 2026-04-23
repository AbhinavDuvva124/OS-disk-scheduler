from flask import Blueprint, jsonify, request
from backend.services import cpu_scheduler
from backend.utils.validators import validate_processes
from backend.utils.calculations import analyze_cpu_algorithms

cpu_bp = Blueprint("cpu", __name__, url_prefix="/api/cpu")

ALGORITHMS = {
    "fcfs": cpu_scheduler.fcfs,
    "sjf": cpu_scheduler.sjf,
    "rr": cpu_scheduler.round_robin,
    "priority": cpu_scheduler.priority_scheduling,
}


@cpu_bp.route("/schedule", methods=["POST"])
def schedule():
    body = request.get_json()
    if not body:
        return jsonify({"status": "error", "message": "No JSON body provided"}), 400

    processes = body.get("processes", [])
    algorithm = body.get("algorithm", "fcfs").lower()
    quantum = int(body.get("quantum", 2))

    valid, err = validate_processes(processes)
    if not valid:
        return jsonify({"status": "error", "message": err}), 422

    if algorithm not in ALGORITHMS:
        return jsonify({"status": "error", "message": f"Unknown algorithm: {algorithm}"}), 400

    try:
        if algorithm == "rr":
            result = cpu_scheduler.round_robin(processes, quantum)
        else:
            result = ALGORITHMS[algorithm](processes)
        return jsonify({"status": "ok", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@cpu_bp.route("/compare", methods=["POST"])
def compare():
    body = request.get_json()
    if not body:
        return jsonify({"status": "error", "message": "No JSON body provided"}), 400

    processes = body.get("processes", [])
    quantum = int(body.get("quantum", 2))

    valid, err = validate_processes(processes)
    if not valid:
        return jsonify({"status": "error", "message": err}), 422

    try:
        results = cpu_scheduler.run_all_algorithms(processes, quantum)
        analysis = analyze_cpu_algorithms(results)
        return jsonify({"status": "ok", "data": results, "analysis": analysis})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
