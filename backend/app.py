from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .config import config
from .errors import APIError
from .responses import api_error, api_success
from .routes.auth import auth_bp
from .routes.instances import instances_bp
from .routes.tasks import tasks_bp
from .routes.templates import templates_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=[origin.strip() for origin in config.CORS_ORIGINS.split(",") if origin.strip()])

    app.register_blueprint(auth_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(instances_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/api/health")
    def health():
        return api_success({"status": "ok"}, "服务正常。", "HEALTH_OK")

    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, APIError):
            return api_error(error.message, error.status_code, error.code, error.developer_hint)
        if isinstance(error, HTTPException):
            return api_error(error.description, error.code, f"HTTP_{error.code}")
        app.logger.exception(error)
        message = str(error) if config.APP_ENV == "dev" else "Internal server error"
        return api_error(message, 500, "INTERNAL_ERROR", config.APP_ENV != "dev")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=config.BACKEND_HOST, port=config.BACKEND_PORT, debug=config.BACKEND_DEBUG)
