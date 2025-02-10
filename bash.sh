#!/bin/bash

set -e  # Зупинити скрипт у разі помилки

#######################
#      ЗМІННІ         #
#######################
DB_NAME="mydb"
DB_USER="myuser"
DB_PASSWORD="mypassword"

REPO_URL="https://github.com/username/myproject.git"  # Заміни на свій репозиторій
PROJECT_DIR="/mnt/e/MVP"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_DIR="$PROJECT_DIR/backend"

#######################
# 1. ОНОВЛЕННЯ СИСТЕМИ #
#######################
echo ">>> Оновлюємо систему..."
sudo apt update && sudo apt upgrade -y

###########################
# 2. ВСТАНОВЛЕННЯ ЗАЛЕЖНОСТЕЙ (PYTHON, BUILD-TOOLS, GIT, ETC.) #
###########################
echo ">>> Встановлюємо необхідні пакети..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    build-essential \
    git \
    curl \
    ca-certificates

#######################
# 3. ВСТАНОВЛЕННЯ NODE.JS #
#######################
# Рекомендується встановити з NodeSource, щоб мати актуальну версію Node.js
echo ">>> Встановлюємо Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

#######################
# 4. ВСТАНОВЛЕННЯ POSTGRESQL #
#######################
echo ">>> Встановлюємо PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

echo ">>> Запускаємо та вмикаємо PostgreSQL..."
sudo systemctl enable postgresql
sudo systemctl start postgresql

#############################
# 5. НАЛАШТУВАННЯ БАЗИ ДАНИХ #
#############################
echo ">>> Створюємо користувача і базу даних PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true

# Налаштуємо дозвіл пароля (md5)
sudo sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
sudo bash -c "echo \"host all all 0.0.0.0/0 md5\" >> /etc/postgresql/*/main/pg_hba.conf"
sudo systemctl restart postgresql

#######################
# 6. КЛОНУВАННЯ РЕПОЗИТОРІЮ #
#######################
# Опціонально: Якщо вже є код на сервері, можна пропустити цей крок
#if [ ! -d "$PROJECT_DIR" ]; then
#  echo ">>> Клонуємо репозиторій у $PROJECT_DIR ..."
#  sudo mkdir -p "$PROJECT_DIR"
#  sudo chown -R $USER:$USER "$PROJECT_DIR"
#  git clone "$REPO_URL" "$PROJECT_DIR"
#else
#  echo ">>> Репозиторій уже існує, оновимо..."
#  cd "$PROJECT_DIR"
#  git pull
#fi

#######################
# 7. НАЛАШТУВАННЯ BACKEND #
#######################
echo ">>> Налаштовуємо Python-віртуальне середовище..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate

echo ">>> Встановлюємо Python-залежності..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Файл config.py повинен мати інформацію для з'єднання з PostgreSQL
# Наприклад, через змінну середовища DATABASE_URI:
export DATABASE_URI="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

# Міграції БД (якщо потрібно)
# Якщо використовуєте Flask-Migrate або Alembic, виконайте:
# flask db upgrade

deactivate

#######################
# 8. НАЛАШТУВАННЯ FRONTEND #
#######################
echo ">>> Налаштовуємо Frontend (React)"
cd "$FRONTEND_DIR"
npm install

#######################
# 9. ЗАВЕРШЕННЯ #
#######################
echo ">>> Початкова підготовка сервера завершена!"
echo ">>> Можна запускати backend і frontend за допомогою:"
echo "    1) Backend:"
echo "       cd $BACKEND_DIR"
echo "       source venv/bin/activate"
echo "       python app.py"
echo "    2) Frontend:"
echo "       cd $FRONTEND_DIR"
echo "       npm start"
echo ""
echo "Готово!"
