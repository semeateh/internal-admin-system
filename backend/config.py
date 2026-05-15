import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_environment():
    explicit_env_file = os.getenv("ENV_FILE")
    app_env = os.getenv("APP_ENV", "dev").lower()
    candidates = [explicit_env_file] if explicit_env_file else [f".env.{app_env}", ".env"]

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = ROOT_DIR / path
        if path.exists():
            load_dotenv(path, override=False)
            return path

    return None


LOADED_ENV_FILE = load_environment()


class Config:
    APP_ENV = os.getenv("APP_ENV", "dev")
    ENV_FILE = str(LOADED_ENV_FILE) if LOADED_ENV_FILE else ""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "5000"))
    BACKEND_DEBUG = os.getenv("BACKEND_DEBUG", "1" if APP_ENV == "dev" else "0").lower() in ("1", "true", "yes", "on")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "replace-with-a-long-random-secret")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "internal_admin_system")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5001,http://localhost:5001")
    DEFAULT_OPERATOR_ID = int(os.getenv("DEFAULT_OPERATOR_ID", "1"))


def validate_security_config():
    if os.getenv("APP_ENV", "dev").lower() != "prod":
        return
    insecure_values = {"", "dev-secret-change-me", "replace-with-a-long-random-secret"}
    if Config.SECRET_KEY in insecure_values:
        raise RuntimeError("SECRET_KEY must be set to a strong value in prod")
    if Config.JWT_SECRET_KEY in insecure_values:
        raise RuntimeError("JWT_SECRET_KEY must be set to a strong value in prod")
    if Config.BACKEND_DEBUG:
        raise RuntimeError("BACKEND_DEBUG must be disabled in prod")
    origins = [origin.strip().lower() for origin in Config.CORS_ORIGINS.split(",") if origin.strip()]
    if "*" in origins or any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
        raise RuntimeError("CORS_ORIGINS must not use localhost, 127.0.0.1, or * in prod")


config = Config()
validate_security_config()
