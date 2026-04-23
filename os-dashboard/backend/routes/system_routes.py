from flask import Blueprint, jsonify
from backend.services.system_monitor import get_system_overview, get_cpu_info, get_memory_info, get_top_processes

system_bp = Blueprint("system", __name__, url_prefix="/api/system")


@system_bp.route("/overview")
def overview():
    try:
        data = get_system_overview()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@system_bp.route("/cpu")
def cpu():
    try:
        data = get_cpu_info()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@system_bp.route("/memory")
def memory():
    try:
        data = get_memory_info()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@system_bp.route("/processes")
def processes():
    try:
        data = get_top_processes(15)
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
