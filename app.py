# тонкая обёртка: вся логика в ym_player, тут только запуск
# run.sh и старые импорты вида `import app` продолжают работать
from ym_player import app, create_app 
from ym_player.config import FLASK_HOST, FLASK_PORT, MEDIA_DIR
from ym_player.db import db, execute, init_db, row, rows 
from ym_player.downloads import ensure_resumed 

__all__ = ["app", "create_app"]


if __name__ == "__main__":
    init_db()
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    ensure_resumed()
    app.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True)
