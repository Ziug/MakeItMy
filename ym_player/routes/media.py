from flask import Blueprint, send_file

from ..config import ROOT
from ..db import row

media_bp = Blueprint("media_api", __name__)


@media_bp.get("/media/<track_id>/audio")
def media_audio(track_id: str):
    # отдаём файл с поддержкой перемотки, полное предпочитаем короткому
    track = row(
        """
        SELECT audio_path, short_audio_path, status FROM tracks
        WHERE id = ? AND status IN ('done', 'done_short', 'downloading_full')
        """,
        (track_id,),
    )
    if not track:
        return ("", 404)
    # полное аудио лучше, если его нет — сойдёт и короткое
    audio_rel = track["audio_path"] or track.get("short_audio_path")
    if not audio_rel:
        return ("", 404)
    path = ROOT / audio_rel
    if not path.is_file():
        return ("", 404)
    response = send_file(
        path,
        conditional=True,
        mimetype=None,
        as_attachment=False,
        download_name=path.name,
        max_age=3600,
    )
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@media_bp.get("/media/<track_id>/cover")
def media_cover(track_id: str):
    track = row("SELECT cover_path FROM tracks WHERE id = ?", (track_id,))
    # обложки нет — отдаём заглушку
    if not track or not track["cover_path"]:
        response = send_file(ROOT / "static" / "placeholder.svg", max_age=0)
        response.headers["Cache-Control"] = "no-store"
        return response
    path = ROOT / track["cover_path"]
    if not path.is_file():
        response = send_file(ROOT / "static" / "placeholder.svg", max_age=0)
        response.headers["Cache-Control"] = "no-store"
        return response
    response = send_file(path, conditional=True, max_age=86400)
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response
