from app import create_app
from app.config import config


app = create_app()


if __name__ == "__main__":
    app.run(host=config.BACKEND_HOST, port=config.BACKEND_PORT, debug=config.BACKEND_DEBUG)
