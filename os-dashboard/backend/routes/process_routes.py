from flask import Blueprint, jsonify, request

process_bp = Blueprint("process", __name__, url_prefix="/api/process")

# In-memory store for demo
_presets = [
    {
        "name": "Batch Processing",
        "processes": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 10, "priority": 2},
            {"pid": "P2", "arrival_time": 2, "burst_time": 4, "priority": 1},
            {"pid": "P3", "arrival_time": 4, "burst_time": 8, "priority": 3},
            {"pid": "P4", "arrival_time": 6, "burst_time": 2, "priority": 1},
            {"pid": "P5", "arrival_time": 8, "burst_time": 6, "priority": 2},
        ],
    },
    {
        "name": "Interactive System",
        "processes": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 3, "priority": 1},
            {"pid": "P2", "arrival_time": 1, "burst_time": 5, "priority": 2},
            {"pid": "P3", "arrival_time": 2, "burst_time": 2, "priority": 1},
            {"pid": "P4", "arrival_time": 3, "burst_time": 4, "priority": 3},
        ],
    },
    {
        "name": "Real-Time System",
        "processes": [
            {"pid": "P1", "arrival_time": 0, "burst_time": 6, "priority": 1},
            {"pid": "P2", "arrival_time": 1, "burst_time": 2, "priority": 1},
            {"pid": "P3", "arrival_time": 2, "burst_time": 8, "priority": 2},
            {"pid": "P4", "arrival_time": 0, "burst_time": 3, "priority": 1},
            {"pid": "P5", "arrival_time": 4, "burst_time": 4, "priority": 2},
            {"pid": "P6", "arrival_time": 6, "burst_time": 1, "priority": 1},
        ],
    },
]

_disk_presets = [
    {
        "name": "Light Load",
        "requests": [45, 21, 67, 90, 30, 56, 78],
        "head": 50,
        "disk_size": 200,
    },
    {
        "name": "Heavy Load",
        "requests": [176, 79, 34, 60, 92, 11, 41, 114, 145, 180, 60, 120],
        "head": 53,
        "disk_size": 200,
    },
    {
        "name": "Random Scatter",
        "requests": [10, 190, 50, 150, 30, 170, 70, 130, 90, 110],
        "head": 100,
        "disk_size": 200,
    },
]


@process_bp.route("/presets")
def get_presets():
    return jsonify({"status": "ok", "data": _presets})


@process_bp.route("/disk-presets")
def get_disk_presets():
    return jsonify({"status": "ok", "data": _disk_presets})
