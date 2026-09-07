import re
import shutil
import time
from pathlib import Path

from yandex_music import Track

from . import state
from .config import (
    AUDIO_SUFFIXES,
    COVER_RESOLUTION,
    COVERS_DIR,
    DATA_DIR,
    DOWNLOAD_QUALITY,
    LOSSLESS_SIZE_HINT,
    MEDIA_DIR,
    ROOT,
)
from .db import execute, row, rows
from .library import set_track_state
from .yandex import artist_names


def normalize_media_key(value: str) -> str:
    from download_tracks import core

    # приводим название к общему виду, чтобы "Ё" и "Е" считались одним и тем же
    value = value.casefold().replace("ё", "е")
    value = core.SAFE_PATH_CLEAR_RE.sub("_", value)
    value = re.sub(r"[_\s]+", " ", value).strip(" ._")
    return value


def track_media_keys(track: Track) -> set[str]:
    from download_tracks import core

    # все варианты имени, по которым ищем файл на диске
    keys: set[str] = set()
    base = str(core.prepare_base_path(Path("#track-artist - #title"), track))
    keys.add(normalize_media_key(base))
    title = core.full_title(track)
    artist = artist_names(track)
    keys.add(normalize_media_key(f"{artist} - {title}"))
    keys.add(normalize_media_key(title))
    return {k for k in keys if k}


def _cover_near(audio_path: Path) -> Path | None:
    # обложка может лежать рядом с файлом, проверяем
    for name in ("cover.jpg", "cover.png"):
        candidate = audio_path.parent / name
        if candidate.is_file():
            return candidate
    return None


def _index_audio_file(index: dict[str, tuple[Path, Path | None]], audio_path: Path) -> None:
    cover = _cover_near(audio_path)
    stem_key = normalize_media_key(audio_path.stem)
    if stem_key:
        index.setdefault(stem_key, (audio_path, cover))
    try:
        import mutagen

        # если в тегах есть артист/название - индексируем и по ним
        tags = mutagen.File(audio_path, easy=True)
        if not tags:
            return
        title = " ".join(tags.get("title", [])).strip()
        artist = " ".join(tags.get("artist", [])).strip()
        if title:
            index.setdefault(normalize_media_key(title), (audio_path, cover))
        if artist and title:
            index.setdefault(normalize_media_key(f"{artist} - {title}"), (audio_path, cover))
    except Exception:
        return


def get_media_index(force: bool = False) -> dict[str, tuple[Path, Path | None]]:
    # карта "название -> файл", чтобы по сто раз не лазить по диску
    with state.media_index_lock:
        if not force and state._media_index is not None:
            return state._media_index
        index: dict[str, tuple[Path, Path | None]] = {}
        if MEDIA_DIR.exists():
            for audio_path in MEDIA_DIR.rglob("*"):
                if audio_path.is_file() and audio_path.suffix.lower() in AUDIO_SUFFIXES:
                    _index_audio_file(index, audio_path)
        state._media_index = index
        state._media_index_mtime = time.time()
        return index


def find_local_media_for_track(track: Track) -> tuple[Path, Path | None] | None:
    index = get_media_index()
    for key in track_media_keys(track):
        found = index.get(key)
        if found and found[0].is_file():
            return found
    return None


def invalidate_media_index() -> None:
    # файлы поменялись - индекс выкидываем, в следующий раз построится заново
    with state.media_index_lock:
        state._media_index = None
        state._media_index_mtime = 0.0


def cover_path_ok(relative_or_abs: str | Path | None) -> bool:
    if not relative_or_abs:
        return False
    path = Path(relative_or_abs)
    if not path.is_absolute():
        path = ROOT / path
    return path.is_file()


def find_existing_cover_path(track: Track, track_row_id: str | None = None) -> Path | None:
    # ищем готовую обложку без сети: сначала общая на альбом, потом у треков-близнецов
    album = track.albums[0] if track.albums else None
    if album and album.id:
        shared = COVERS_DIR / f"{album.id}.jpg"
        if shared.is_file():
            return shared
    source_track_id = str(track.id)
    sibling = row(
        """
        SELECT cover_path FROM tracks
        WHERE source_track_id = ?
          AND cover_path IS NOT NULL AND cover_path != ''
          AND (? IS NULL OR id != ?)
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (source_track_id, track_row_id, track_row_id),
    )
    if sibling and cover_path_ok(sibling.get("cover_path")):
        return ROOT / sibling["cover_path"]
    return None


def save_shared_cover(track: Track, resolution: int) -> Path | None:
    # качаем обложку один раз на альбом и кладём в общую папку
    if track.cover_uri is None:
        return None
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    album = track.albums[0] if track.albums else None
    key = str(album.id) if album and album.id else str(track.id)
    cover_path = COVERS_DIR / f"{key}.jpg"
    if cover_path.is_file():
        return cover_path
    cached = state._covers_cache.get(album.id) if album and album.id else None
    if cached is not None:
        cover_path.write_bytes(cached.data)
        return cover_path
    try:
        data = track.download_cover_bytes(size=f"{resolution}x{resolution}")
        tmp = cover_path.with_suffix(".jpg.tmp")
        tmp.write_bytes(data)
        tmp.replace(cover_path)
        return cover_path
    except Exception:
        return None


def ensure_track_cover(track_row_id: str, track: Track) -> Path | None:
    # цепляем обложку к треку, из сети тянем только если ничего нет
    current = row("SELECT cover_path FROM tracks WHERE id = ?", (track_row_id,))
    if current and cover_path_ok(current.get("cover_path")):
        return ROOT / current["cover_path"]
    cover = find_existing_cover_path(track, track_row_id)
    if cover is None:
        cover = save_shared_cover(track, COVER_RESOLUTION)
    if cover is not None:
        set_track_state(track_row_id, "done", cover_path=cover)
    return cover


def backfill_covers_from_siblings() -> int:
    # трекам без обложки подкидываем её от близнецов (та же аудиодорожка или тот же трек)
    updated = 0
    missing = rows(
        """
        SELECT id, source_track_id, audio_path FROM tracks
        WHERE status IN ('done', 'done_short')
          AND (cover_path IS NULL OR cover_path = '')
        """
    )
    for track in missing:
        cover = None
        if track.get("audio_path"):
            donor = row(
                """
                SELECT cover_path FROM tracks
                WHERE audio_path = ?
                  AND cover_path IS NOT NULL AND cover_path != ''
                  AND id != ?
                LIMIT 1
                """,
                (track["audio_path"], track["id"]),
            )
            if donor and cover_path_ok(donor.get("cover_path")):
                cover = ROOT / donor["cover_path"]
        if cover is None and track.get("source_track_id"):
            donor = row(
                """
                SELECT cover_path FROM tracks
                WHERE source_track_id = ?
                  AND cover_path IS NOT NULL AND cover_path != ''
                  AND id != ?
                LIMIT 1
                """,
                (track["source_track_id"], track["id"]),
            )
            if donor and cover_path_ok(donor.get("cover_path")):
                cover = ROOT / donor["cover_path"]
        if cover is None:
            continue
        set_track_state(track["id"], "done", cover_path=cover)
        updated += 1
    return updated


def attach_local_media(track_row_id: str, track: Track) -> bool:
    # если файл уже валяется на диске - просто привязываем его, качать не надо
    local = find_local_media_for_track(track)
    if not local:
        return False
    audio_path, cover_path = local
    # жирные лосслессы не тащим - удаляем и качаем лёгкую версию
    if is_bulky_audio(audio_path):
        try:
            audio_path.unlink(missing_ok=True)
        except OSError:
            pass
        invalidate_media_index()
        return False
    if not cover_path_ok(cover_path):
        cover_path = find_existing_cover_path(track, track_row_id)
    if not cover_path_ok(cover_path):
        cover_path = save_shared_cover(track, COVER_RESOLUTION)
    set_track_state(
        track_row_id,
        "done",
        error=None,
        audio_path=audio_path,
        cover_path=cover_path,
    )
    return True


def is_bulky_audio(path: Path) -> bool:
    # палим flac и прочее жирное, что жрёт место на телефоне
    if not path.is_file():
        return False
    suffix = path.suffix.lower()
    if suffix == ".flac":
        return True
    try:
        size = path.stat().st_size
    except OSError:
        return False
    if size >= LOSSLESS_SIZE_HINT:
        return True
    if suffix != ".m4a":
        return False
    try:
        import mutagen

        audio = mutagen.File(path)
        info = getattr(audio, "info", None) if audio else None
        bitrate = int(getattr(info, "bitrate", 0) or 0)
        # лосслесс в m4a-обёртке и просто дикий битрейт
        if bitrate >= 500_000:
            return True
        codec = str(getattr(info, "codec", "") or "").lower()
        if "flac" in codec or "alac" in codec:
            return True
    except Exception:
        return size >= LOSSLESS_SIZE_HINT
    return False


def to_best_available_downloadable(track: Track, base_path: Path):
    from download_tracks import core

    # пробуем качество получше, если не вышло - скатываемся на попроще
    quality_map = {
        "lq": (core.CoreTrackQuality.LOW,),
        "low": (core.CoreTrackQuality.LOW,),
        "nq": (core.CoreTrackQuality.NORMAL, core.CoreTrackQuality.LOW),
        "normal": (core.CoreTrackQuality.NORMAL, core.CoreTrackQuality.LOW),
        "hq": (core.CoreTrackQuality.NORMAL, core.CoreTrackQuality.LOW),
        "lossless": (
            core.CoreTrackQuality.LOSSLESS,
            core.CoreTrackQuality.NORMAL,
            core.CoreTrackQuality.LOW,
        ),
    }
    qualities = quality_map.get(DOWNLOAD_QUALITY, quality_map["nq"])
    last_error = None
    for quality in qualities:
        try:
            return core.to_downloadable_track(track, quality, base_path)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Не вышло получить ссылку на скачивание: {last_error}")


def bytes_to_human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            continue
    return total


def cleanup_storage(aggressive: bool = False, vacuum: bool = True) -> dict:
    # чистим мусор: папки без плейлиста, файлы без строк в базе, времянки
    from .db import db as db_ctx

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    before = dir_size(DATA_DIR)
    removed_files = 0
    freed = 0
    notes: list[str] = []

    referenced = set()
    for track in rows("SELECT audio_path, cover_path, playlist_id FROM tracks"):
        if track.get("audio_path"):
            referenced.add(str((ROOT / track["audio_path"]).resolve()))
        if track.get("cover_path"):
            referenced.add(str((ROOT / track["cover_path"]).resolve()))

    playlist_ids = {p["id"] for p in rows("SELECT id FROM playlists")}

    # папки плейлистов, которых уже нет в базе - сносим
    if MEDIA_DIR.exists():
        for child in list(MEDIA_DIR.iterdir()):
            if child.name == "_covers":
                continue
            if child.is_dir() and child.name not in playlist_ids:
                size = dir_size(child)
                shutil.rmtree(child, ignore_errors=True)
                freed += size
                removed_files += 1
                notes.append(f"снесли папку без плейлиста: {child.name}")

    # файлы, на которые никто не ссылается - туда же
    if MEDIA_DIR.exists():
        for path in list(MEDIA_DIR.rglob("*")):
            if not path.is_file():
                continue
            if path.name.startswith(".") or path.suffix == ".tmp":
                try:
                    size = path.stat().st_size
                    path.unlink(missing_ok=True)
                    freed += size
                    removed_files += 1
                except OSError:
                    pass
                continue
            resolved = str(path.resolve())
            if resolved not in referenced and path.suffix.lower() in AUDIO_SUFFIXES | {".jpg", ".png", ".lrc"}:
                if path.parent == COVERS_DIR and not aggressive:
                    continue
                try:
                    size = path.stat().st_size
                    path.unlink(missing_ok=True)
                    freed += size
                    removed_files += 1
                except OSError:
                    pass

    # пустые папки подтираем
    if MEDIA_DIR.exists():
        for path in sorted(MEDIA_DIR.rglob("*"), reverse=True):
            if path.is_dir() and path != COVERS_DIR and path != MEDIA_DIR:
                try:
                    next(path.iterdir())
                except StopIteration:
                    path.rmdir()
                except OSError:
                    pass

    if aggressive:
        # тут импорт ленивый, иначе media и downloads тянут друг друга по кругу
        from .downloads import enqueue_one

        # жирное аудио сносим и ставим в очередь заново в лёгком качестве
        heavy_tracks = rows(
            """
            SELECT id, audio_path FROM tracks
            WHERE status IN ('done', 'done_short') AND audio_path IS NOT NULL
            """
        )
        recompressed = 0
        for track in heavy_tracks:
            audio = ROOT / track["audio_path"]
            if not is_bulky_audio(audio):
                continue
            try:
                freed += audio.stat().st_size
                audio.unlink(missing_ok=True)
                removed_files += 1
            except OSError:
                pass
            execute(
                """
                UPDATE tracks
                SET status = 'queued', error = NULL, audio_path = NULL, updated_at = ?
                WHERE id = ?
                """,
                (int(time.time()), track["id"]),
            )
            enqueue_one(track["id"], phase='full')
            recompressed += 1
        if recompressed:
            notes.append(f"отправили {recompressed} жирных треков перекачиваться в лёгком качестве")

        # старые cover.jpg рядом с треками (раньше так хранили) - удаляем
        if MEDIA_DIR.exists():
            for path in list(MEDIA_DIR.rglob("cover.jpg")) + list(MEDIA_DIR.rglob("cover.png")):
                if path.parent == COVERS_DIR:
                    continue
                try:
                    size = path.stat().st_size
                    path.unlink(missing_ok=True)
                    freed += size
                    removed_files += 1
                except OSError:
                    pass
            notes.append("удалили старые обложки рядом с треками")

    if vacuum:
        with state.db_lock, db_ctx() as conn:
            conn.execute("VACUUM")

    after = dir_size(DATA_DIR)
    return {
        "before_bytes": before,
        "after_bytes": after,
        "freed_bytes": max(0, before - after) if after <= before else freed,
        "freed_human": bytes_to_human(max(0, before - after) if after <= before else freed),
        "removed_entries": removed_files,
        "data_human": bytes_to_human(after),
        "notes": notes,
        "quality": DOWNLOAD_QUALITY,
        "cover_size": COVER_RESOLUTION,
    }
