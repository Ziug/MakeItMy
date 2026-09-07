import threading
import time
from pathlib import Path
from typing import Iterable

from . import state
from .config import COVER_RESOLUTION, COVERS_DIR, MEDIA_DIR
from .db import db as db_ctx
from .db import row, rows
from .library import set_playlist_import_state, set_track_state
from .media import (
    attach_local_media,
    backfill_covers_from_siblings,
    cleanup_storage,
    cover_path_ok,
    ensure_track_cover,
    invalidate_media_index,
    save_shared_cover,
    to_best_available_downloadable,
)
from .yandex import client


def download_worker(track_row_id: str, phase: str = 'short') -> None:
    track_row = row("SELECT * FROM tracks WHERE id = ?", (track_row_id,))
    if not track_row:
        return

    # если уже докачано - только обложку дотянуть, если той нема
    if track_row["status"] == "done" and track_row.get("audio_path"):
        from .config import ROOT

        audio = ROOT / track_row["audio_path"]
        if audio.is_file():
            if cover_path_ok(track_row.get("cover_path")):
                return
            try:
                ym = client()
                tracks = list(ym.tracks([track_row["source_track_id"]]))
                if tracks:
                    ensure_track_cover(track_row_id, tracks[0])
            except Exception:
                pass
            return

    # короткая версия есть, а обложки нет - дотягиваем только её
    if track_row["status"] == "done_short" and track_row.get("short_audio_path"):
        from .config import ROOT

        audio = ROOT / track_row["short_audio_path"]
        if audio.is_file() and not cover_path_ok(track_row.get("cover_path")):
            try:
                ym = client()
                tracks = list(ym.tracks([track_row["source_track_id"]]))
                if tracks:
                    ensure_track_cover(track_row_id, tracks[0])
            except Exception:
                pass
            return
        if audio.is_file():
            return

    # файл под эту фазу уже лежит - делать нечего
    if phase == 'short' and track_row.get("short_audio_path"):
        from .config import ROOT

        audio = ROOT / track_row["short_audio_path"]
        if audio.is_file():
            return

    if phase == 'full' and track_row.get("audio_path"):
        from .config import ROOT

        audio = ROOT / track_row["audio_path"]
        if audio.is_file():
            return

    try:
        from download_tracks import core

        ym = client()
        tracks = list(ym.tracks([track_row["source_track_id"]]))
        if not tracks:
            raise RuntimeError("Трек не найден.")
        track = tracks[0]
        if not track.available:
            raise RuntimeError("Трек недоступен для скачивания.")

        playlist_dir = MEDIA_DIR / track_row["playlist_id"]
        playlist_dir.mkdir(parents=True, exist_ok=True)
        base_name = core.prepare_base_path(Path("#track-artist - #title"), track)
        base_path = playlist_dir / f"{track_row['id'][:8]}_{base_name.name}"

        if phase == 'short':
            # короткая версия для быстрого старта - качаем первой
            set_track_state(track_row_id, "downloading_short")
            downloadable = core.to_downloadable_track(track, core.CoreTrackQuality.LOW, base_path)
            core.download_track(
                track_info=downloadable,
                lyrics_format=core.LyricsFormat.NONE,
                embed_cover=False,
                cover_resolution=COVER_RESOLUTION,
                covers_cache=state._covers_cache,
                compatibility_level=1,
                write_cover_file=False,
            )
            cover = save_shared_cover(track, COVER_RESOLUTION)
            set_track_state(track_row_id, "done_short", short_audio_path=downloadable.path, cover_path=cover)
        else:
            # полная версия - сначала смотрим, нет ли файла на диске
            set_track_state(track_row_id, "downloading_full")
            if attach_local_media(track_row_id, track):
                ensure_track_cover(track_row_id, track)
                return
            downloadable = to_best_available_downloadable(track, base_path)
            core.download_track(
                track_info=downloadable,
                lyrics_format=core.LyricsFormat.NONE,
                embed_cover=False,
                cover_resolution=COVER_RESOLUTION,
                covers_cache=state._covers_cache,
                compatibility_level=1,
                write_cover_file=False,
            )
            cover = save_shared_cover(track, COVER_RESOLUTION)
            set_track_state(track_row_id, "done", audio_path=downloadable.path, cover_path=cover)

        invalidate_media_index()
    except Exception as exc:
        set_track_state(track_row_id, "error", str(exc))


def _download_job(track_id: str, phase: str = 'short') -> None:
    try:
        download_worker(track_id, phase)
    finally:
        with state.enqueue_lock:
            state.inflight_downloads.discard(f"{track_id}:{phase}")


def _priority_download_job(track_id: str, phase: str = 'full') -> None:
    try:
        download_worker(track_id, phase)
    finally:
        with state.enqueue_lock:
            state.priority_inflight.discard(f"{track_id}:{phase}")


def enqueue(track_ids: Iterable[str]) -> None:
    for track_id in track_ids:
        enqueue_one(track_id)


def enqueue_one(track_id: str, phase: str = 'short') -> None:
    # если такую задачу уже кидали - второй раз не надо
    key = f"{track_id}:{phase}"
    with state.enqueue_lock:
        if key in state.inflight_downloads:
            return
        state.inflight_downloads.add(key)
    state.executor.submit(_download_job, track_id, phase)


def enqueue_priority(track_id: str, phase: str = 'full') -> None:
    # отдельная быстрая очередь - юзер ткнул в трек, качаем вне общей толпы
    # отдельно следим, чтобы обычная и быстрая задачи не задвоились
    key = f"{track_id}:{phase}"
    with state.enqueue_lock:
        if key in state.priority_inflight:
            return
        state.priority_inflight.add(key)
    state.priority_executor.submit(_priority_download_job, track_id, phase)


def enqueue_missing_covers(limit: int = 80) -> int:
    # треки без обложек - ставим в очередь на дотягивание
    missing = rows(
        """
        SELECT id FROM tracks
        WHERE status IN ('done', 'done_short')
          AND audio_path IS NOT NULL
          AND (cover_path IS NULL OR cover_path = '')
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    for item in missing:
        enqueue_one(item["id"])
    return len(missing)


def resume_pending_work() -> None:
    # после рестарта поднимаем недокачанное, заново ничего не заливаем
    # импорт ленивый, иначе downloads и imports тянут друг друга по кругу
    from .imports import import_worker

    now = int(time.time())
    with state.db_lock, db_ctx() as conn:
        # недокачанные короткие - назад в очередь
        conn.execute(
            """
            UPDATE tracks
            SET status = 'queued', error = NULL, updated_at = ?
            WHERE status IN ('downloading', 'downloading_short')
            """,
            (now,),
        )
        # недокачанные полные - откатываем на короткую, она-то цела
        conn.execute(
            """
            UPDATE tracks
            SET status = 'done_short', error = NULL, updated_at = ?
            WHERE status = 'downloading_full'
            """,
            (now,),
        )
    # короткие качаем первыми, полные потом
    pending = rows(
        """
        SELECT id, status FROM tracks
        WHERE status IN ('queued', 'done_short')
        ORDER BY
            CASE WHEN status = 'done_short' THEN 1 ELSE 0 END,
            position ASC, created_at ASC
        """
    )
    for item in pending:
        if item['status'] == 'done_short':
            enqueue_one(item["id"], phase='full')
        else:
            enqueue_one(item["id"], phase='short')

    interrupted_imports = rows(
        """
        SELECT id, source_url FROM playlists
        WHERE import_status = 'importing' AND source_url IS NOT NULL AND source_url != ''
        """
    )
    for playlist in interrupted_imports:
        threading.Thread(target=import_worker, args=(playlist["id"], playlist["source_url"], False), daemon=True).start()

    orphaned_imports = rows(
        """
        SELECT id FROM playlists
        WHERE import_status = 'importing'
          AND (source_url IS NULL OR source_url = '')
        """
    )
    for playlist in orphaned_imports:
        set_playlist_import_state(playlist["id"], "done")


def ensure_resumed() -> None:
    from .db import init_db

    init_db()
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    with state._resume_lock:
        if state._resume_started:
            return
        state._resume_started = True
    # при старте слегка прибираемся (без жести и без VACUUM)
    try:
        cleanup_storage(aggressive=False, vacuum=False)
    except Exception:
        pass
    try:
        backfill_covers_from_siblings()
    except Exception:
        pass
    resume_pending_work()
    try:
        enqueue_missing_covers()
    except Exception:
        pass
