import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

from yandex_music import Track

from .config import PLAYLIST_RE
from .db import execute, row, rows
from .yandex import (
    album_title,
    artist_names,
    normalize_source_url,
    playlist_yandex_id,
    track_url,
)


def make_playlist(
    title: str,
    source_url: str | None,
    is_custom: bool,
    import_status: str = "done",
) -> str:
    # новый плейлист, id - рандомный hex
    playlist_id = uuid.uuid4().hex
    execute(
        """
        INSERT INTO playlists
        (id, title, source_url, is_custom, import_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (playlist_id, title, source_url, int(is_custom), import_status, int(time.time())),
    )
    return playlist_id


def add_track_record(playlist_id: str, position: int, track: Track) -> str | None:
    from download_tracks import core

    source_track_id = str(track.id)
    # дубликаты скипаем, если те есть
    existing = row(
        "SELECT id FROM tracks WHERE playlist_id = ? AND source_track_id = ?",
        (playlist_id, source_track_id),
    )
    if existing:
        return None
    now = int(time.time())
    track_row_id = uuid.uuid4().hex
    execute(
        """
        INSERT INTO tracks
        (id, playlist_id, source_track_id, position, title, artist, album, duration_ms,
         status, source_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?)
        """,
        (
            track_row_id,
            playlist_id,
            source_track_id,
            position,
            core.full_title(track),
            artist_names(track),
            album_title(track),
            track.duration_ms,
            track_url(track),
            now,
            now,
        ),
    )
    return track_row_id


def set_track_state(
    track_id: str,
    status: str,
    error: str | None = None,
    audio_path: Path | None = None,
    cover_path: Path | None = None,
    short_audio_path: Path | None = None,
) -> None:
    from .config import ROOT

    # пути обновляем только если передали, старое не затираем (поэтому COALESCE)
    execute(
        """
        UPDATE tracks
        SET status = ?, error = ?, audio_path = COALESCE(?, audio_path),
            short_audio_path = COALESCE(?, short_audio_path),
            cover_path = COALESCE(?, cover_path), updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            error,
            str(audio_path.relative_to(ROOT)) if audio_path else None,
            str(short_audio_path.relative_to(ROOT)) if short_audio_path else None,
            str(cover_path.relative_to(ROOT)) if cover_path else None,
            int(time.time()),
            track_id,
        ),
    )


def set_playlist_import_state(
    playlist_id: str,
    status: str,
    error: str | None = None,
    title: str | None = None,
) -> None:
    if title:
        execute(
            """
            UPDATE playlists
            SET title = ?, import_status = ?, import_error = ?
            WHERE id = ?
            """,
            (title, status, error, playlist_id),
        )
        return
    execute(
        "UPDATE playlists SET import_status = ?, import_error = ? WHERE id = ?",
        (status, error, playlist_id),
    )


def find_playlist_by_source_url(url: str) -> dict | None:
    # сначала ищем точное совпадение ссылки, потом по куску user/kind
    target = normalize_source_url(url)
    playlists = rows(
        """
        SELECT * FROM playlists
        WHERE source_url IS NOT NULL AND source_url != ''
        ORDER BY created_at DESC
        """
    )
    for playlist in playlists:
        if normalize_source_url(playlist["source_url"]) == target:
            return playlist
    # запасной вариант: та же связка юзер/плейлист в пути
    match = PLAYLIST_RE.search(urlparse(url).path)
    if not match:
        return None
    user, kind = match.groups()
    needle = f"/{user}/playlists/{kind}"
    for playlist in playlists:
        if needle in (playlist["source_url"] or ""):
            return playlist
    return None


def playlist_summary(playlist_id: str) -> dict | None:
    # одна строчка для фронта: сколько всего, сколько готово, сколько упало
    playlist = row(
        """
        SELECT p.*,
               COUNT(t.id) AS track_count,
               SUM(t.status IN ('done', 'done_short', 'downloading_full')) AS done_count,
               SUM(t.status = 'error') AS error_count,
               SUM(t.status IN ('queued', 'downloading_short', 'downloading_full')) AS pending_count,
               MAX(t.updated_at) AS tracks_updated_at
        FROM playlists p
        LEFT JOIN tracks t ON t.playlist_id = p.id
        WHERE p.id = ?
        GROUP BY p.id
        """,
        (playlist_id,),
    )
    if not playlist:
        return None
    playlist["yandex_id"] = playlist_yandex_id(playlist.get("source_url"))
    return playlist
