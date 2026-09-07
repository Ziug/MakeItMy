import json
import time

from flask import Blueprint, Response, jsonify, redirect, request, stream_with_context, url_for

from .. import state
from ..config import DEV_PERF, TRACK_PAGE_SIZE
from ..db import execute, row, rows
from ..downloads import enqueue_priority, ensure_resumed
from ..imports import start_async_import
from ..library import make_playlist, playlist_summary
from ..media import cover_path_ok

playlists_bp = Blueprint("playlists_api", __name__)


@playlists_bp.post("/api/import")
def api_import():
    url = request.form.get("url", "").strip()
    try:
        playlist_id = start_async_import(url)
        return redirect(url_for("pages.playlist_page", playlist_id=playlist_id))
    except Exception as exc:
        return (
            render_template_index_with_error(str(exc)),
            400,
        )


def render_template_index_with_error(error: str):
    from flask import render_template

    return render_template(
        "index.html", playlists=rows("SELECT * FROM playlists ORDER BY created_at DESC"), error=error
    )


@playlists_bp.post("/api/playlists")
def api_create_playlist():
    title = request.form.get("title", "").strip() or "Мой плейлист"
    playlist_id = make_playlist(title, None, True)
    return redirect(url_for("pages.playlist_page", playlist_id=playlist_id))


@playlists_bp.post("/api/playlists/<playlist_id>/rename")
def api_rename_playlist(playlist_id: str):
    title = request.form.get("title", "").strip()
    if title:
        execute("UPDATE playlists SET title = ? WHERE id = ?", (title, playlist_id))
    return redirect(url_for("pages.playlist_page", playlist_id=playlist_id))


@playlists_bp.post("/api/playlists/<playlist_id>/add")
def api_add_to_playlist(playlist_id: str):
    url = request.form.get("url", "").strip()
    try:
        start_async_import(url, playlist_id)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return redirect(url_for("pages.playlist_page", playlist_id=playlist_id))


@playlists_bp.get("/api/playlists/<playlist_id>")
def api_playlist(playlist_id: str):
    ensure_resumed()
    playlist = playlist_summary(playlist_id)
    if not playlist:
        return jsonify({"error": "Плейлист не найден"}), 404
    return jsonify(playlist)


@playlists_bp.get("/api/playlists/<playlist_id>/events")
def api_playlist_events(playlist_id: str):
    # стрим прогресса: фронт слушает, пока качается, и закрывает когда всё тихо
    ensure_resumed()
    if not row("SELECT id FROM playlists WHERE id = ?", (playlist_id,)):
        return jsonify({"error": "Плейлист не найден"}), 404

    @stream_with_context
    def event_stream():
        last_payload = None
        idle_ticks = 0
        while True:
            summary = playlist_summary(playlist_id)
            if not summary:
                yield "event: gone\ndata: {}\n\n"
                break
            payload = {
                "id": summary["id"],
                "title": summary["title"],
                "import_status": summary["import_status"],
                "import_error": summary.get("import_error"),
                "track_count": int(summary["track_count"] or 0),
                "done_count": int(summary["done_count"] or 0),
                "error_count": int(summary["error_count"] or 0),
                "pending_count": int(summary["pending_count"] or 0),
                "tracks_updated_at": summary.get("tracks_updated_at") or 0,
            }
            encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            if encoded != last_payload:
                yield f"event: playlist\ndata: {encoded}\n\n"
                last_payload = encoded
                idle_ticks = 0
            else:
                idle_ticks += 1
                if idle_ticks % 15 == 0:
                    yield ": keepalive\n\n"
            importing = payload["import_status"] == "importing"
            pending = payload["pending_count"] > 0
            if not importing and not pending and idle_ticks >= 3:
                yield f"event: idle\ndata: {encoded}\n\n"
                break
            time.sleep(1.0 if importing or pending else 2.0)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return Response(event_stream(), mimetype="text/event-stream", headers=headers)


@playlists_bp.get("/api/playlists/<playlist_id>/tracks")
def api_tracks(playlist_id: str):
    ensure_resumed()
    t0 = time.perf_counter()
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0
    try:
        limit = int(request.args.get("limit", TRACK_PAGE_SIZE))
    except ValueError:
        limit = TRACK_PAGE_SIZE
    limit = max(1, min(limit, 100))
    page_size = TRACK_PAGE_SIZE

    if request.args.get("align") == "1":
        offset = (offset // page_size) * page_size
        limit = page_size

    total_row = row("SELECT COUNT(*) AS c FROM tracks WHERE playlist_id = ?", (playlist_id,))
    total = int(total_row["c"]) if total_row else 0
    tracks = rows(
        """
        SELECT id, position, title, artist, status, error, duration_ms, updated_at,
               source_url, source_track_id, cover_path
        FROM tracks
        WHERE playlist_id = ?
        ORDER BY position ASC
        LIMIT ? OFFSET ?
        """,
        (playlist_id, limit, offset),
    )
    for track in tracks:
        has_cover = cover_path_ok(track.get("cover_path"))
        track["has_cover"] = has_cover
        has_short = track["status"] in ("done_short", "downloading_full", "done")
        has_full = track["status"] == "done"
        track["has_short"] = has_short
        track["has_full"] = has_full
        # cover_path не тащим в ответ, фронт сам соберёт ссылку на обложку
        track.pop("cover_path", None)
        if not track.get("source_url") and track.get("source_track_id"):
            track["source_url"] = f"https://music.yandex.com/track/{track['source_track_id']}"
    elapsed_ms = (time.perf_counter() - t0) * 1000
    response = jsonify(
        {
            "tracks": tracks,
            "total": total,
            "offset": offset,
            "limit": limit,
            "page": offset // page_size,
            "page_size": page_size,
            "server_ms": round(elapsed_ms, 2) if DEV_PERF else None,
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@playlists_bp.post("/api/tracks/<track_id>/prioritize_full")
def api_prioritize_full(track_id: str):
    # юзер ткнул в трек с короткой версией - качаем полную вне очереди
    from ..config import ROOT
    from ..db import db as db_ctx
    from ..library import set_track_state

    track = row("SELECT * FROM tracks WHERE id = ?", (track_id,))
    if not track:
        return jsonify({"ok": False, "error": "Трек не найден"}), 404
    if track["status"] in ("done", "error"):
        return jsonify({"ok": True, "status": track["status"]})
    # полный файл уже лежит - просто помечаем готовым
    if track.get("audio_path") and (ROOT / track["audio_path"]).is_file():
        set_track_state(track_id, "done")
        return jsonify({"ok": True, "status": "done"})
    # помечаем что качаем полную (короткая пока играет) и кидаем в быструю очередь
    with state.db_lock, db_ctx() as conn:
        conn.execute(
            "UPDATE tracks SET status = 'downloading_full' WHERE id = ? AND short_audio_path IS NOT NULL AND status NOT IN ('done', 'error')",
            (track_id,),
        )
    enqueue_priority(track_id, phase='full')
    return jsonify({"ok": True, "status": "downloading_full"})


@playlists_bp.delete("/api/tracks/<track_id>")
def api_delete_track(track_id: str):
    track = row("SELECT * FROM tracks WHERE id = ?", (track_id,))
    if not track:
        return jsonify({"ok": False, "error": "Трек не найден"}), 404
    _unlink_if_unreferenced(track.get("audio_path"), "audio_path", track_id)
    _unlink_if_unreferenced(track.get("cover_path"), "cover_path", track_id)
    _remove_track_media_dir(track["playlist_id"], track["position"])
    execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    return jsonify({"ok": True})


@playlists_bp.post("/api/playlists/<playlist_id>/delete")
def api_delete_playlist(playlist_id: str):
    import shutil

    from ..config import MEDIA_DIR

    playlist = row("SELECT id FROM playlists WHERE id = ?", (playlist_id,))
    if not playlist:
        return redirect(url_for("pages.index"))
    media_dir = MEDIA_DIR / playlist_id
    if media_dir.is_dir():
        shutil.rmtree(media_dir, ignore_errors=True)
    execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    return redirect(url_for("pages.index"))


def _unlink_media(relative_path: str | None) -> None:
    from ..config import ROOT

    if not relative_path:
        return
    path = ROOT / relative_path
    if path.is_file():
        path.unlink(missing_ok=True)


def _unlink_if_unreferenced(relative_path: str | None, column: str, exclude_id: str) -> None:
    # файл трём только если на него больше никто не ссылается
    if not relative_path:
        return
    refs = row(
        f"SELECT COUNT(*) AS c FROM tracks WHERE {column} = ? AND id != ?",
        (relative_path, exclude_id),
    )
    if refs and int(refs["c"]) > 0:
        return
    _unlink_media(relative_path)


def _remove_track_media_dir(playlist_id: str, position: int) -> None:
    import shutil

    from ..config import MEDIA_DIR

    for folder_name in (f"{int(position):05d}", f"{int(position):03d}", str(int(position))):
        track_dir = MEDIA_DIR / playlist_id / folder_name
        if track_dir.is_dir():
            shutil.rmtree(track_dir, ignore_errors=True)
