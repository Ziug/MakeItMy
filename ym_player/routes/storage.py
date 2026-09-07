from flask import Blueprint, jsonify, redirect, request, url_for

from ..config import COVER_RESOLUTION, COVERS_DIR, DATA_DIR, DB_PATH, DOWNLOAD_QUALITY, MEDIA_DIR, ROOT
from ..db import rows
from ..downloads import ensure_resumed
from ..media import bytes_to_human, dir_size, is_bulky_audio

storage_bp = Blueprint("storage_api", __name__)


@storage_bp.get("/api/storage")
def api_storage():
    ensure_resumed()
    media = dir_size(MEDIA_DIR)
    covers = dir_size(COVERS_DIR)
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    done_tracks = rows(
        "SELECT audio_path FROM tracks WHERE status = 'done' AND audio_path IS NOT NULL"
    )
    flac_count = 0
    bulky_count = 0
    for track in done_tracks:
        path = ROOT / track["audio_path"]
        if not path.is_file():
            continue
        if path.suffix.lower() == ".flac" or is_bulky_audio(path):
            bulky_count += 1
            if path.suffix.lower() == ".flac":
                flac_count += 1
    return jsonify(
        {
            "data_human": bytes_to_human(dir_size(DATA_DIR)),
            "media_human": bytes_to_human(media),
            "covers_human": bytes_to_human(covers),
            "db_human": bytes_to_human(db_size),
            "flac_tracks": flac_count,
            "bulky_tracks": bulky_count,
            "quality": DOWNLOAD_QUALITY,
            "cover_size": COVER_RESOLUTION,
        }
    )


@storage_bp.post("/api/storage/cleanup")
def api_storage_cleanup():
    from ..media import cleanup_storage

    ensure_resumed()
    aggressive = request.args.get("aggressive") == "1" or request.form.get("aggressive") == "1"
    result = cleanup_storage(aggressive=aggressive, vacuum=True)
    wants_json = (
        request.is_json
        or "application/json" in (request.headers.get("Accept") or "")
    )
    if wants_json:
        return jsonify(result)
    return redirect(url_for("pages.index"))
