# MakeItMy

Personal music streaming and library service for importing, storing, and playing music from Yandex Music through a local web interface.

MakeItMy runs as a personal server on your device. You can import a track, album, or playlist by URL, store the audio locally, and stream it directly from the browser.

The primary use case is running the service on an Android smartphone through Termux, where the phone acts as both the server and the music storage.

> The web interface and `run.sh` were developed with assistance from Claude. Music access is provided through the `yandex-music-api` project.

## Features

- Import individual tracks, albums, or entire playlists from a Yandex Music URL.
- Real-time import progress using Server-Sent Events (SSE).
- Tracks appear in the interface as they are processed instead of waiting for the entire import to finish.
- Two-stage downloads: a compact version is downloaded first for fast playback, followed by the full-quality version in the background.
- HTTP Range / `206 Partial Content` support for streaming and seeking before the full download is complete.
- Automatic deduplication of tracks and downloaded files.
- Reuse of previously downloaded files.
- Shared album artwork with automatic recovery of missing covers.
- Storage cleanup for orphaned files, temporary files, stale covers, and oversized lossless audio.
- Optional transcoding/requeueing of oversized lossless files into a compact format.
- Virtualized track lists for large playlists.
- Automatic recovery of unfinished downloads and imports after restart.

## Requirements

- Python 3.10+
- Yandex Music access token
- Internet connection
- Approximately 100 MB of free space for the Python environment, plus storage for music

For Android/Termux:

- Termux
- Android device with internet access

Python dependencies are listed in `requirements.txt`:

- Flask - web server and HTTP API
- yandex-music - Yandex Music API client
- mutagen - audio metadata handling
- pycryptodome and strenum - supporting dependencies

## Installation

### Termux

Run:

```bash
bash run.sh
```

The script automatically:

1. Installs system packages via `pkg` (on the first launch): `python`, `python-pip`, `clang`, `libjpeg-turbo`, `zlib`, `openssl`.
2. Creates virtual environment `.venv`.
3. Dwonloads requirements from `requirements.txt` without pip cache.
4. Load configuration from `.env`, if the file exists.
5. Launches server via `python app.py`.

To accees the server:

- on the device: `http://127.0.0.1:5000`;
- from another device on the local network: `http://<device id>:5000`.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The server will be available at: `http://127.0.0.1:5000`. The host and port can be configured through environment variables.

## Configuration

Configuration is provided through environment variables or a .env file in the project root.

Environment variables take precedence over .env values.

Example:

``` dotenv
YANDEX_MUSIC_TOKEN=...
YM_QUALITY=lq
YM_COVER_SIZE=200
YM_MAX_WORKERS=4
FLASK_PORT=5000
```

### Yandex Music token

The service requires a Yandex Music access token.

The token can be provided through: `YANDEX_MUSIC_TOKEN`. Methods for obtaining it are described in the documentation of the `yandex-music` library (extraction from the official app or web version of the service).

The token is looked up in the following order:

1. Environment variable `YANDEX_MUSIC_TOKEN` (including the value from `.env`).
2. `very_secret.txt` file in the project root (supported for backward compatibility).

The `.env` and `very_secret.txt` files are excluded from version control (see `.gitignore`) and must not be committed to the repository.

### Parameters

| Variable | Default | Description |
|---|---|---|
| `YANDEX_MUSIC_TOKEN` | — | Yandex Music access token. Required parameter. |
| `YM_QUALITY` | `lq` | Audio quality: `lq` (compact), `nq` / `hq` (standard), `lossless` (lossless, with fallback to standard when unavailable). |
| `YM_COVER_SIZE` | `200` | Resolution of downloaded covers in pixels. |
| `YM_MAX_WORKERS` | `4` | Number of parallel track download threads. |
| `YM_TRACK_FETCH_BATCH` | `20` | Batch size when requesting track metadata from the API. |
| `YM_UI_PAGE_SIZE` | `50` | Number of tracks returned by the API per request. |
| `YM_LOSSLESS_MIN_BYTES` | `6291456` | File size threshold in bytes above which audio is considered excessively heavy and is subject to re-download in compact quality. |
| `YM_DEV_PERF` | `1` | `1` — include server processing time (`server_ms`) in API responses; `0` — disable. |
| `FLASK_HOST` | `0.0.0.0` | Network interface to listen on. |
| `FLASK_PORT` | `5000` | Web server port. |

Example `.env` file (template in `.env.example`, copy it: `cp .env.example .env`):

```dotenv
YANDEX_MUSIC_TOKEN=...
YM_QUALITY=lq
YM_COVER_SIZE=200
YM_MAX_WORKERS=4
FLASK_PORT=5000
```

## Usage

### Importing music

1. Open the main page. Paste a Yandex Music track, album, or playlist link into the import field and submit the form.
2. The service will create (or reuse) a playlist entry and start background parsing of the link.
3. Tracks are added to the database and queued for download as they arrive; the playlist page updates automatically via the SSE stream.
4. Additional links are added to an existing playlist from the playlist page ("Add" action).

### Playback

The playlist page contains a built-in player. Audio is streamed from the local device; when a track whose full download is not yet complete is selected, playback starts from the compact version, while the full version is downloaded with priority.

### Deletion

- Deleting a track (API) removes the database entry and associated files (if they are not used by other entries).
- Deleting a playlist removes its media file directory and all associated entries.

Deletion via the interface requires confirmation.

## Architecture

The application is built on Flask and SQLite. The SQLite database is the source of truth: the `playlists` and `tracks` tables store metadata, download statuses (`queued`, `downloading_short`, `done_short`, `downloading_full`, `done`, `error`), and relative file paths.

Downloading is performed by a pool of background threads: short (compact) versions are processed first, full versions are queued next (FIFO). A separate single-threaded executor handles priority requests (track click). Re-submitting an already running task is ignored (`inflight` tracking).

Logic is distributed across the `ym_player` package modules:

| Module | Purpose |
|---|---|
| `config.py` | Paths, regular expressions, environment variables, `.env` loading. |
| `state.py` | Shared mutable state: locks, executors, caches, API client. |
| `db.py` | SQLite connection, schema initialization and migrations, helper queries. |
| `yandex.py` | Yandex Music client, link parsing, metadata helper functions. |
| `library.py` | Playlist and track record operations, summary statistics. |
| `media.py` | Local file index, covers, reuse, storage cleanup. |
| `downloads.py` | Background download tasks, queueing, recovery after restart. |
| `imports.py` | Link-based playlist import (synchronous core, background handler, asynchronous entry). |
| `routes/` | HTTP layer: pages (`pages`), playlist and track API (`playlists`), storage (`storage`), streaming (`media`). |

The `app.py` entry point is a thin wrapper: it re-exports the Flask application object and starts the server, so existing scenarios (`python app.py`, `run.sh`, `import app`) continue to work unchanged.

## API Reference

### Pages

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Main page with playlist list. |
| `GET` | `/playlist/<playlist_id>` | Playlist page with player. |

### Import and playlists

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/import` | Start import from a link in the `url` form field. Redirects to the playlist page. |
| `POST` | `/api/playlists` | Create an empty playlist (`title` form field). |
| `POST` | `/api/playlists/<playlist_id>/rename` | Rename playlist (`title` form field). |
| `POST` | `/api/playlists/<playlist_id>/add` | Add a link to an existing playlist (`url` form field). |
| `POST` | `/api/playlists/<playlist_id>/delete` | Delete playlist along with files. |
| `GET` | `/api/playlists/<playlist_id>` | JSON summary: title, statuses, track counters. |
| `GET` | `/api/playlists/<playlist_id>/events` | SSE stream of import and download progress. Closes when transitioning to idle. |
| `GET` | `/api/playlists/<playlist_id>/tracks?offset=&limit=` | Paginated track list (maximum 100 per request). |

### Tracks

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/tracks/<track_id>/prioritize_full` | Priority download of the full track version. |
| `DELETE` | `/api/tracks/<track_id>` | Delete track and its files. Returns `{"ok": true}`. |

### Storage

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/storage` | Space usage statistics (media, covers, database, heavy file counters). |
| `POST` | `/api/storage/cleanup` | Cleanup. The `aggressive=1` parameter enables removal of excessively heavy files with re-queueing. Returns a report for JSON requests; otherwise redirects to the main page. |

### Media

| Method | Path | Description |
|---|---|---|
| `GET` | `/media/<track_id>/audio` | Audio stream with Range request support. Prefers the full version, falls back to the compact version when unavailable. |
| `GET` | `/media/<track_id>/cover` | Track cover. Returns an SVG placeholder when missing. |

## Storage maintenance

On each startup, a safe cleanup runs automatically (without touching heavy files, without `VACUUM`): it removes playlist directories without database entries, unreferenced files, temporary files, and empty directories.

Aggressive cleanup (`POST /api/storage/cleanup` with `aggressive=1`) additionally:

- removes excessively heavy audio files and re-queues the corresponding tracks for re-download in compact quality;
- removes stale cover files next to tracks (the shared `_covers` storage is used);
- runs database `VACUUM`.

## Troubleshooting

| Symptom | Likely cause and solution |
|---|---|
| `Token not found` at startup | `YANDEX_MUSIC_TOKEN` is not set: add it to `.env` or the environment, or create `very_secret.txt`. |
| `Playlist not found` error | The link points to a private/unavailable playlist or has an invalid link format. Tracks, albums, and playlists are supported. |
| Tracks stuck in `queued` status | Check the token and internet access; the queue is restored automatically after restart. |
| Out of space on device | Run aggressive cleanup; make sure `YM_QUALITY` is set to `lq` or `nq`, not `lossless`. |
| Port in use | Change `FLASK_PORT` in `.env`. |

## Project structure

```
app.py             — entry point (app creation, server startup)
run.sh             — launch under Termux: environment, dependencies, server
requirements.txt   — Python dependencies
.env               — environment variables (not committed)
ym_player/
  __init__.py      — Flask application factory
  config.py        — configuration and .env loading
  state.py         — shared state (locks, queues, caches)
  db.py            — SQLite layer
  yandex.py        — Yandex Music client and link parsing
  library.py       — playlist and track records
  media.py         — files, covers, cleanup
  downloads.py     — background downloading
  imports.py       — link-based import
  routes/          — HTTP routes (pages, playlists, storage, media)
download_tracks/   — low-level download from Yandex Music
static/ templates/ — web interface
data/media/        — downloaded files (not committed)
library.sqlite3    — library database
```
