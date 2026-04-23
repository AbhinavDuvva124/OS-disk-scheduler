import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from flask_cors import CORS

from backend.routes.system_routes import system_bp
from backend.routes.cpu_routes import cpu_bp
from backend.routes.disk_routes import disk_bp
from backend.routes.process_routes import process_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    CORS(app)

    # Register blueprints
    app.register_blueprint(system_bp)
    app.register_blueprint(cpu_bp)
    app.register_blueprint(disk_bp)
    app.register_blueprint(process_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "ok", "message": "OS Dashboard running"}

    return app


if __name__ == "__main__":
    app = create_app()
    print("OS Dashboard starting at http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
