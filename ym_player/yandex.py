import os
from typing import Iterator
from urllib.parse import urlparse, urlunparse

from yandex_music import Album, Client, Playlist, Track

from . import state
from .config import (
    ALBUM_RE,
    FETCH_PAGE_SIZE,
    PLAYLIST_RE,
    PLAYLIST_UUID_RE,
    TOKEN_PATHS,
    TRACK_RE,
    URL_RE,
)


def token() -> str:
    # сначала смотрим env, если пусто - читаем файл
    env_token = os.environ.get("YANDEX_MUSIC_TOKEN", "").strip()
    if env_token:
        return env_token
    for path in TOKEN_PATHS:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    raise RuntimeError("Не найден токен. Укажи YANDEX_MUSIC_TOKEN или создай very_secret.txt.")


def client() -> Client:
    # клиент один на всех, создаём при первом обращении
    with state.client_lock:
        if state.ym_client is None:
            from download_tracks import core

            state.ym_client = core.init_client(token(), timeout=30, max_try_count=10, retry_delay=3)
        return state.ym_client


def playlist_tracks_gen(playlist: Playlist, ym: Client) -> Iterator[Track]:
    shorts = playlist.fetch_tracks()
    for i in range(0, len(shorts), FETCH_PAGE_SIZE):
        # короткий id иногда врёт, поэтому берём полный track_id
        for track in ym.tracks([track.track_id for track in shorts[i : i + FETCH_PAGE_SIZE]]):
            yield track


def extract_source_url(value: str) -> str:
    # юзер может вставить ссылку с мусором вокруг - выковыриваем саму ссылку
    value = value.strip()
    if match := URL_RE.search(value):
        return match.group(0).rstrip("\n\r\t \"'>)")
    return value


def album_tracks_gen(album: Album) -> Iterator[Track]:
    import itertools

    if album.volumes:
        for track in itertools.chain.from_iterable(album.volumes):
            yield track


def resolve_url(url: str) -> tuple[str, Iterator[Track]]:
    parsed = urlparse(url.strip())
    path = parsed.path
    url = extract_source_url(url)

    print(f"разбираем ссылку: {url}")

    if match := TRACK_RE.search(path):
        track_id = match.group(1)
        print(f"похоже на трек, id={track_id}")
        ym = client()
        tracks = list(ym.tracks([track_id]))
        title = tracks[0].title if tracks else "Новый трек"
        print(f"нашли трек: {title}")
        return title, iter(tracks)

    if match := PLAYLIST_UUID_RE.search(path):
        raw_match = match.group(0)
        playlist_uuid = match.group(1)
        print(f"похоже на плейлист, uuid={playlist_uuid}")

        ym = client()
        print("спрашиваем плейлист у яндекса...")
        playlist = None

        # первая попытка: по чистому uuid
        try:
            playlist = ym.playlist(playlist_uuid)
        except Exception as e:
            print(f"не вышло по uuid: {e}")

        # вторая попытка: со всей строкой (иногда нужен префикс типа lk.)
        if not playlist and "lk." in raw_match:
            full_kind = raw_match.split("playlists/")[-1].strip("/")
            print(f"пробуем ещё раз как {full_kind}")
            try:
                playlist = ym.playlist(full_kind)
            except Exception as e:
                print(f"и так не вышло: {e}")

        if not playlist:
            print("яндекс ничего не вернул по этому плейлисту")
            raise ValueError(f"Плейлист ({playlist_uuid}) не найден или доступ ограничен.")

        title = playlist.title or "Плейлист"
        track_count = playlist.track_count if hasattr(playlist, 'track_count') else 'неизвестно'
        print(f"нашли плейлист: {title}, треков у яндекса: {track_count}")

        print("тянем список треков...")
        gen = playlist_tracks_gen(playlist, ym)
        return title, gen

    if match := ALBUM_RE.search(path):
        album_id = match.group(1)
        print(f"похоже на альбом, id={album_id}")
        ym = client()
        album = ym.albums_with_tracks(album_id)
        if not album:
            print(f"альбом {album_id} не нашёлся")
            raise ValueError("Альбом не найден.")
        title = album.title or "Альбом"
        print(f"нашли альбом: {title}")
        return title, album_tracks_gen(album)

    if match := PLAYLIST_RE.search(path):
        user, kind = match.groups()
        print(f"похоже на плейлист юзера {user}, kind={kind}")
        ym = client()
        playlist = ym.users_playlists(kind, user)
        if not playlist:
            print("такой плейлист у юзера не нашёлся")
            raise ValueError("Плейлист не найден.")
        title = playlist.title or "Плейлист"
        print(f"нашли плейлист: {title}")
        return title, playlist_tracks_gen(playlist, ym)

    print(f"ссылка не подошла ни под что: {path}")
    raise ValueError("Поддерживаются ссылки на трек, альбом или плейлист Яндекс Музыки.")


def artist_names(track: Track) -> str:
    return ", ".join(a.name for a in track.artists if a.name) or "Неизвестный исполнитель"


def album_title(track: Track) -> str:
    from download_tracks import core

    return core.full_title(track.albums[0]) if track.albums else ""


def track_url(track: Track) -> str:
    album_id = track.albums[0].id if track.albums else ""
    if album_id:
        return f"https://music.yandex.com/album/{album_id}/track/{track.id}"
    return f"https://music.yandex.com/track/{track.id}"


def playlist_yandex_id(source_url: str | None) -> str | None:
    if not source_url:
        return None
    match = PLAYLIST_RE.search(urlparse(source_url).path)
    if not match:
        return None
    user, kind = match.groups()
    return f"{user}/{kind}"


def normalize_source_url(url: str) -> str:
    url = extract_source_url(url)
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    # хвост типа ?... и #... отрезаем, чтобы один и тот же плейлист всегда одинаково выглядел
    return urlunparse((parsed.scheme or "https", parsed.netloc.lower(), path, "", "", ""))
