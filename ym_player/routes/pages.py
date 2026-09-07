from flask import Blueprint, redirect, render_template, url_for

from ..db import rows
from ..db import row as db_row
from ..yandex import playlist_yandex_id

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    playlists = rows(
        """
        SELECT p.*, COUNT(t.id) AS track_count,
               SUM(t.status = 'done') AS done_count,
               SUM(t.status = 'error') AS error_count
        FROM playlists p
        LEFT JOIN tracks t ON t.playlist_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """
    )
    for playlist in playlists:
        playlist["yandex_id"] = playlist_yandex_id(playlist.get("source_url"))
    return render_template("index.html", playlists=playlists)


@pages_bp.route("/playlist/<playlist_id>")
def playlist_page(playlist_id: str):
    playlist = db_row("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
    if not playlist:
        return redirect(url_for("pages.index"))
    playlist["yandex_id"] = playlist_yandex_id(playlist.get("source_url"))
    return render_template("playlist.html", playlist=playlist)
