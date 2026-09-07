import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_dotenv(path: Path) -> None:
    # .env подхватываем сами, без левых зависимостей
    # настоящий env всегда главнее — .env только подставляет то, чего нет
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(ROOT / ".env")

# сюда складываем базу и музыку
DATA_DIR = ROOT / "data"
MEDIA_DIR = DATA_DIR / "media"
# база обычно лежит рядом с кодом (её синкаем с телефона), если нет - берём старую в data/
DB_PATH = ROOT / "library.sqlite3" if (ROOT / "library.sqlite3").is_file() else DATA_DIR / "library.sqlite3"
# токен ищем так: env (или .env) -> very_secret.txt, что первое нашлось — то и берём
TOKEN_PATHS = (ROOT / "very_secret.txt",)
# общие обложки, одна на альбом
COVERS_DIR = MEDIA_DIR / "_covers"

# вытаскиваем id трека/альбома/плейлиста из ссылки (долго парился с regex, вроде работает быстро, менять не буду:) )
TRACK_RE = re.compile(r"track/(\d+)")
ALBUM_RE = re.compile(r"album/(\d+)(?:/)?$")
PLAYLIST_RE = re.compile(r"([\w\-._@]+)/playlists/(\d+)(?:/)?$")
PLAYLIST_UUID_RE = re.compile(r"playlists/(?:[\w\-._@]+\.)?([0-9a-fA-F-]{8,})(?:/)?$")
URL_RE = re.compile(r"https?://[^\s<>'\"]+")

# если аппка тормозит или яндекс ругается - крутим эти цифры через env (тут мой конфиг под redmi note 9 pro)
FETCH_PAGE_SIZE = int(os.environ.get("YM_TRACK_FETCH_BATCH", "20"))
MAX_WORKERS = int(os.environ.get("YM_MAX_WORKERS", "4"))
TRACK_PAGE_SIZE = int(os.environ.get("YM_UI_PAGE_SIZE", "50"))
AUDIO_SUFFIXES = {".mp3", ".m4a", ".flac"}
DEV_PERF = os.environ.get("YM_DEV_PERF", "1") != "0"
# по дефолту жмём в лёгкое качество, чтобы место на телефоне не жрало (YM_QUALITY=nq - получше звук)
DOWNLOAD_QUALITY = os.environ.get("YM_QUALITY", "lq").strip().lower()
COVER_RESOLUTION = int(os.environ.get("YM_COVER_SIZE", "200"))
LOSSLESS_SIZE_HINT = int(os.environ.get("YM_LOSSLESS_MIN_BYTES", str(6 * 1024 * 1024)))

FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
