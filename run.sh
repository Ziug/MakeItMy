#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$(dirname "$0")"

# подхватываем .env, если есть (настоящие env-переменные главнее, их не трогаем)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if command -v pkg >/dev/null 2>&1; then
  # Avoid full pkg update on every start - it wastes space/time.
  pkg install -y python python-pip clang libjpeg-turbo zlib openssl >/dev/null
fi

PYTHON="${PYTHON:-python}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python3
fi

create_venv() {
  if [ -d .venv ] && [ -x .venv/bin/python ]; then
    return 0
  fi
  rm -rf .venv

  if "$PYTHON" -m venv .venv 2>/dev/null; then
    return 0
  fi

  echo "ensurepip unavailable - creating venv without pip..."
  "$PYTHON" -m venv --without-pip .venv

  . .venv/bin/activate
  if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    echo "Bootstrapping pip with get-pip.py..."
    GET_PIP="$(mktemp)"
    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$GET_PIP"
    .venv/bin/python "$GET_PIP"
    rm -f "$GET_PIP"
  fi
  deactivate 2>/dev/null || true
}

create_venv
. .venv/bin/activate

# Compact installs: no pip cache left on the phone.
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
python -m pip cache purge >/dev/null 2>&1 || true

# Default to lossy audio to save phone storage (override with YM_QUALITY=lossless if needed).
export YM_QUALITY="${YM_QUALITY:-nq}"
export YM_COVER_SIZE="${YM_COVER_SIZE:-200}"
export FLASK_HOST="${FLASK_HOST:-0.0.0.0}"
export FLASK_PORT="${FLASK_PORT:-5000}"

echo "Качество: ${YM_QUALITY} · обложки: ${YM_COVER_SIZE}px"
echo "Открывайте: http://127.0.0.1:${FLASK_PORT}"
echo "Если заходите с другого устройства в сети, используйте IP телефона и порт ${FLASK_PORT}."
python app.py
