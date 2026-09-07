import sqlite3
from contextlib import contextmanager

from . import state
from .config import DATA_DIR, DB_PATH


@contextmanager
def db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with state.db_lock, db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_url TEXT,
                is_custom INTEGER NOT NULL DEFAULT 0,
                import_status TEXT NOT NULL DEFAULT 'done',
                import_error TEXT,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
                source_track_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                album TEXT,
                duration_ms INTEGER,
                status TEXT NOT NULL,
                error TEXT,
                audio_path TEXT,
                cover_path TEXT,
                source_url TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tracks_playlist ON tracks(playlist_id, position);
            CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);
            """
        )
        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(playlists)").fetchall()
        }
        if "import_status" not in existing_columns:
            conn.execute("ALTER TABLE playlists ADD COLUMN import_status TEXT NOT NULL DEFAULT 'done'")
        if "import_error" not in existing_columns:
            conn.execute("ALTER TABLE playlists ADD COLUMN import_error TEXT")
        try:
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_playlist_source
                ON tracks(playlist_id, source_track_id)
                """
            )
        except sqlite3.OperationalError:
            # дубликаты скипаем, если те есть - всё равно в add_track_record проверяем
            pass

        existing_track_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(tracks)").fetchall()
        }
        # короткие превьюшки доклеиваем миграцией, чтобы старую базу не сносить
        if "short_audio_path" not in existing_track_columns:
            conn.execute("ALTER TABLE tracks ADD COLUMN short_audio_path TEXT")


def rows(sql: str, args: tuple = ()) -> list[dict]:
    with state.db_lock, db() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def row(sql: str, args: tuple = ()) -> dict | None:
    result = rows(sql, args)
    return result[0] if result else None


def execute(sql: str, args: tuple = ()) -> None:
    with state.db_lock, db() as conn:
        conn.execute(sql, args)
