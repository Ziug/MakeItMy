from flask import Flask

from .media import media_bp
from .pages import pages_bp
from .playlists import playlists_bp
from .storage import storage_bp


def register_routes(app: Flask) -> None:
    # все ручки в одном месте цепляем
    app.register_blueprint(pages_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(storage_bp)
    app.register_blueprint(media_bp)
