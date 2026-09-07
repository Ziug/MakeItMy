import concurrent.futures
import threading
from pathlib import Path
from typing import Any

from .config import MAX_WORKERS

# общее состояние в одном месте: локи, очереди, кеши
# так модули не тянут друг друга по кругу
executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
priority_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

db_lock = threading.RLock()
client_lock = threading.RLock()
enqueue_lock = threading.Lock()
media_index_lock = threading.Lock()

# что уже качается, чтобы дважды одну задачу не пихать
inflight_downloads: set[str] = set()
priority_inflight: set[str] = set()

# клиент яндекса один на всех, создаём лениво
ym_client: Any | None = None

_resume_started = False
_resume_lock = threading.Lock()

_media_index: dict[str, tuple[Path, Path | None]] | None = None
_media_index_mtime: float = 0.0

# album_id -> байты обложки, чтобы не качать одну и ту же по сто раз
_covers_cache: dict[int, Any] = {}
