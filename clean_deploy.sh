#!/bin/bash

set -e  # Зупинити скрипт у разі помилки

#######################
#      ЗМІННІ         #
#######################
DB_NAME="logtagger"
DB_USER="logtagger"
DB_PASSWORD="logtagger"  # В реальному середовищі використовуйте безпечніший пароль

PROJECT_DIR="/mnt/d/MVP_2/LogTagger"
BACKEND_DIR="$PROJECT_DIR/backend"

echo ">>> Очищення попереднього розгортання..."

# 1. Зупиняємо сервіси, якщо вони запущені
echo ">>> Зупиняємо сервіси..."
sudo systemctl stop logtagger-backend 2>/dev/null || true
sudo systemctl disable logtagger-backend 2>/dev/null || true
sudo rm -f /etc/systemd/system/logtagger-backend.service 2>/dev/null || true
sudo systemctl daemon-reload 2>/dev/null || true

# 2. Видаляємо базу даних
echo ">>> Видаляємо базу даних..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" || true
sudo -u postgres psql -c "DROP TYPE IF EXISTS userrole CASCADE;" || true  # Видаляємо залишковий enum тип

# 3. Видаляємо віртуальне середовище
echo ">>> Видаляємо віртуальне середовище Python..."
if [ -d "$BACKEND_DIR/venv" ]; then
    rm -rf "$BACKEND_DIR/venv"
fi

# 4. Видаляємо тимчасові файли
echo ">>> Видаляємо тимчасові файли і логи..."
rm -rf "$BACKEND_DIR/logs"/* 2>/dev/null || true
rm -rf "$BACKEND_DIR/exports"/* 2>/dev/null || true
rm -f "$BACKEND_DIR"/*.log 2>/dev/null || true
rm -f "$BACKEND_DIR"/*.pyc 2>/dev/null || true
rm -rf "$BACKEND_DIR"/__pycache__ 2>/dev/null || true
find "$BACKEND_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Видаляємо залишки файлів аутентифікації
echo ">>> Видаляємо файли аутентифікації..."
rm -f "$BACKEND_DIR/services/auth.py" 2>/dev/null || true
rm -f "$BACKEND_DIR/routes/auth_routes.py" 2>/dev/null || true
rm -f "$BACKEND_DIR/routes/users_routes.py" 2>/dev/null || true
rm -f "$BACKEND_DIR/tools/check_users.py" 2>/dev/null || true
rm -f "$FRONTEND_DIR/src/components/Auth/Login.jsx" 2>/dev/null || true
rm -f "$FRONTEND_DIR/src/contexts/AuthContext.jsx" 2>/dev/null || true

echo ">>> Очищення завершено, тепер можна запустити bash.sh для чистового розгортання MVP версії без логіну"
