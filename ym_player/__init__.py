from flask import Flask

from .config import ROOT


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(ROOT / "static"),
        template_folder=str(ROOT / "templates"),
    )
    from .routes import register_routes

    register_routes(app)
    return app


app = create_app()
