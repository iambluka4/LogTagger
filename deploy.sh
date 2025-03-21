#!/bin/bash

set -e  # Зупиняти скрипт при помилках

# Додаємо права виконання для manage.py
chmod +x "$(dirname "$0")/backend/manage.py" 2>/dev/null || true

PROJECT_DIR="/mnt/d/MVP_2/LogTagger"
BACKEND_DIR="$PROJECT_DIR/backend"
DB_NAME="logtagger"
DB_USER="logtagger"
DB_PASSWORD="logtagger"
MODE=${1:-development}

echo ">>> Розгортання проєкту LogTagger MVP в режимі $MODE..."

# 1. Перевірка наявності PostgreSQL
echo ">>> Перевірка PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL не встановлено. Встановлення..."
    sudo apt install -y postgresql postgresql-contrib libpq-dev
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
fi

# 2. Створення бази даних та користувача
echo ">>> Налаштування бази даних..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true
sudo -u postgres psql -c "ALTER USER $DB_USER WITH SUPERUSER;" || true

# 3. Встановлення залежностей Python
echo ">>> Встановлення залежностей Python..."
cd "$BACKEND_DIR"

# Перевірка наявності venv
if [ ! -d "venv" ]; then
    echo ">>> Створення нового віртуального середовища..."
    python3 -m venv venv
fi

# Активація venv і перевірка успішності
source venv/bin/activate
if ! python -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)"; then
    echo "ПОМИЛКА: Не вдалося активувати віртуальне середовище. Перевірте наявність python3-venv."
    exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

# Переконуємося, що модуль click встановлено для manage.py
if ! python -c "import click" 2>/dev/null; then
    echo ">>> Встановлення мінімальних залежностей для manage.py..."
    pip install click sqlalchemy flask flask-sqlalchemy
fi

# 4. Ініціалізація бази даних (якщо вона нова)
echo ">>> Ініціалізація бази даних..."
cd "$BACKEND_DIR"
python3 manage.py db-init --mode $MODE

# 5. Застосування міграцій
echo ">>> Застосування міграцій..."
python3 manage.py migrate --mode $MODE

# 6. Перевірка стану бази даних
echo ">>> Перевірка стану бази даних..."
python3 manage.py check-db --mode $MODE

# Зміна шляху до файлу правил Nginx в production режимі
if [ "$MODE" == "production" ]; then
    echo ">>> Розгортання MVP версії завершено! Бекенд запущено в режимі production."
    echo ">>> API доступне за адресою: http://localhost:5000"
    echo ">>> Фронтенд доступний за адресою: http://localhost"
else
    echo ">>> Розгортання MVP версії завершено! Запустіть сервер вручну:"
    echo ">>> cd $BACKEND_DIR && source venv/bin/activate && python manage.py runserver"
fi
