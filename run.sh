#!/bin/bash

set -e  # Зупинити скрипт у разі помилки

PROJECT_DIR="/mnt/d/MVP_2/LogTagger"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
MODE=${1:-development}

echo ">>> Запуск LogTagger MVP в режимі $MODE..."

# 1. Запуск backend
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    echo "❌ Віртуальне середовище не знайдено. Спочатку виконайте deploy.sh"
    exit 1
fi

source venv/bin/activate

# 2. Перевірка PostgreSQL
echo ">>> Перевірка з'єднання з базою даних..."
python manage.py check-env

# 3. Запуск сервера
case "$MODE" in
    "production")
        echo ">>> Запуск сервера в production режимі..."
        python -m gunicorn -b 0.0.0.0:5000 -w 4 "app:create_app('production')"
        ;;
    *)
        echo ">>> Запуск сервера в режимі розробки..."
        python manage.py runserver --mode development
        ;;
esac

# Скрипт ніколи не дійде сюди, якщо сервер запущено успішно
