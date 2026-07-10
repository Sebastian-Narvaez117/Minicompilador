import os
from dotenv import load_dotenv
from flask import Flask

from views.lexical_routes import create_lexical_blueprint

load_dotenv()


def create_app() -> Flask:
    """Factory que crea y configura la aplicación Flask."""
    app = Flask(__name__)

    lexical_bp = create_lexical_blueprint()
    app.register_blueprint(lexical_bp)

    return app


if __name__ == "__main__":
    app = create_app()

    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    app.run(host="0.0.0.0", port=port, debug=debug)
