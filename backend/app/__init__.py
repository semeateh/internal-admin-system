from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .common.errors import APIError
from .common.responses import api_error, api_success
from .config import config
from .routes.auth_routes import auth_bp
from .routes.directory_routes import directory_bp
from .routes.process_routes import process_blueprints


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=[origin.strip() for origin in config.CORS_ORIGINS.split(",") if origin.strip()])

    app.register_blueprint(auth_bp)
    app.register_blueprint(directory_bp)
    for blueprint in process_blueprints:
        app.register_blueprint(blueprint)

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
