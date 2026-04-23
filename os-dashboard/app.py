import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template
from flask_cors import CORS

from backend.routes.cpu_routes import cpu_bp
from backend.routes.disk_routes import disk_bp
from backend.routes.process_routes import process_bp
from backend.routes.system_routes import system_bp


def _get_cors_origins():
    configured_origins = os.environ.get("CORS_ORIGINS", "*").strip()
    if configured_origins == "*":
        return "*"
    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return origins or "*"


def create_app():
    flask_app = Flask(__name__, template_folder="templates", static_folder="static")
    CORS(flask_app, resources={r"/api/*": {"origins": _get_cors_origins()}})

    # Register API blueprints
    flask_app.register_blueprint(system_bp)
    flask_app.register_blueprint(cpu_bp)
    flask_app.register_blueprint(disk_bp)
    flask_app.register_blueprint(process_bp)

    @flask_app.route("/")
    def index():
        return render_template("index.html")

    @flask_app.route("/health")
    @flask_app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "OS Dashboard running"})

    return flask_app


# Gunicorn entrypoint: gunicorn app:app
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
