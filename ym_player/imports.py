import threading
import traceback

from .config import ROOT
from .db import execute, row
from .downloads import enqueue_one
from .library import (
    add_track_record,
    find_playlist_by_source_url,
    make_playlist,
    set_playlist_import_state,
    set_track_state,
)
from .media import attach_local_media, cover_path_ok, ensure_track_cover, get_media_index
from .yandex import artist_names, resolve_url


def import_to_playlist(url: str, playlist_id: str | None = None, rename_playlist: bool = False) -> str:
    title, tracks = resolve_url(url)
    get_media_index(force=True)

    if playlist_id is None:
        existing_playlist = find_playlist_by_source_url(url)
        if existing_playlist:
            playlist_id = existing_playlist["id"]
            rename_playlist = True
        else:
            playlist_id = make_playlist(title, url, False)
    if rename_playlist:
        execute(
            "UPDATE playlists SET title = ?, source_url = ? WHERE id = ?",
            (title, url, playlist_id),
        )

    current = row(
        "SELECT COALESCE(MAX(position), 0) AS max_pos FROM tracks WHERE playlist_id = ?",
        (playlist_id,),
    )
    next_position = int(current["max_pos"]) + 1
    touched = 0
    reused = 0
    queued = 0

    for track in tracks:
        source_track_id = str(track.id)
        existing = row(
            """
            SELECT id, status, audio_path FROM tracks
            WHERE playlist_id = ? AND source_track_id = ?
            """,
            (playlist_id, source_track_id),
        )
        if existing:
            touched += 1
            audio_ok = bool(existing.get("audio_path") and (ROOT / existing["audio_path"]).is_file())
            if existing["status"] == "done" and audio_ok:
                # готовый трек оставляем, только обложку дотягиваем, если её нет
                full = row("SELECT cover_path FROM tracks WHERE id = ?", (existing["id"],))
                if not cover_path_ok((full or {}).get("cover_path")):
                    ensure_track_cover(existing["id"], track)
                continue
            if attach_local_media(existing["id"], track):
                reused += 1
                continue
            if existing["status"] != "queued":
                set_track_state(existing["id"], "queued", error=None)
            enqueue_one(existing["id"])
            queued += 1
            continue

        track_id = add_track_record(playlist_id, next_position, track)
        if track_id is None:
            continue
        next_position += 1
        touched += 1
        if attach_local_media(track_id, track):
            reused += 1
            continue
        enqueue_one(track_id)
        queued += 1

    if touched == 0:
        raise ValueError("По ссылке не найдено треков.")
    return playlist_id


def import_worker(playlist_id: str, url: str, rename_playlist: bool) -> None:
    # треки кладём в базу по мере поступления, чтобы фронт сразу их показывал
    from download_tracks import core

    from .db import rows

    try:
        set_playlist_import_state(playlist_id, "importing")
        print(f"погнали импортировать плейлист {playlist_id}")

        title, tracks = resolve_url(url)
        get_media_index(force=True)

        if rename_playlist:
            execute("UPDATE playlists SET title = ?, source_url = ? WHERE id = ?", (title, url, playlist_id))

        count = 0
        # фаза 1: пишем треки и сразу ставим короткие версии качаться
        for track in tracks:
            count += 1
            artist = artist_names(track)
            track_title = core.full_title(track)
            print(f"короткая версия #{count}: {artist} - {track_title}")

            current = row("SELECT COALESCE(MAX(position), 0) AS max_pos FROM tracks WHERE playlist_id = ?", (playlist_id,))
            next_pos = int(current["max_pos"]) + 1 if current else 1

            track_row_id = add_track_record(playlist_id, next_pos, track)
            if track_row_id:
                enqueue_one(track_row_id, phase='short')

        print(f"всё, {count} коротких поставили качаться")

        if count == 0:
            print("яндекс вообще ничего не отдал, плейлист пустой")
            raise ValueError("По ссылке не найдено треков (плейлист пуст).")

        # фаза 2: полные версии в конец очереди, они пойдут после всех коротких
        all_tracks = rows(
            "SELECT id FROM tracks WHERE playlist_id = ? AND status NOT IN ('error', 'done')",
            (playlist_id,),
        )
        for tr in all_tracks:
            enqueue_one(tr['id'], phase='full')

        print(f"и {len(all_tracks)} полных поставили в очередь")

        set_playlist_import_state(playlist_id, "done", title=title if rename_playlist else None)
        print(f"готово: {title}")
    except Exception as exc:
        print(f"импорт упал: {exc}")
        traceback.print_exc()
        set_playlist_import_state(playlist_id, "error", str(exc))


def start_async_import(url: str, playlist_id: str | None = None) -> str:
    if not url:
        raise ValueError("Вставь ссылку Яндекс Музыки.")
    if playlist_id is None:
        existing = find_playlist_by_source_url(url)
        if existing:
            playlist_id = existing["id"]
            set_playlist_import_state(playlist_id, "importing")
            rename_playlist = True
        else:
            playlist_id = make_playlist("Импортируется...", url, False, import_status="importing")
            rename_playlist = True
    else:
        set_playlist_import_state(playlist_id, "importing")
        rename_playlist = False
    threading.Thread(target=import_worker, args=(playlist_id, url, rename_playlist), daemon=True).start()
    return playlist_id
