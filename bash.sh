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

# Установка режиму роботи: development або production
MODE=${1:-development}

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
#if [ ! -д "$PROJECT_DIR" ]; then
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
pip install --upgrade pip setuptools wheel
# Встановлюємо необхідні інструменти для збірки пакетів
pip install pip-tools

# Встановлюємо базові пакети із фіксованими версіями для сумісності
echo "Встановлення основних пакетів Flask із фіксованими версіями..."
pip install Werkzeug==2.2.3
pip install Flask==2.2.3
pip install Flask-Cors==3.0.10
pip install Flask-SQLAlchemy==3.0.3
pip install flask-jwt-extended==4.4.4

# Встановлюємо додаткові пакети з requirements.txt
if [ -f "requirements.txt" ]; then
    # Встановлюємо пакети по одному, щоб уникнути проблем зі збіркою
    while IFS= read -r package || [[ -n "$package" ]]; do
        # Skip comments, empty lines and already installed packages
        [[ $package =~ ^#.* ]] || [[ -z "$package" ]] || [[ $package =~ ^Flask ]] || [[ $package =~ ^Flask- ]] && continue
        echo "Встановлення $package..."
        pip install "$package" || echo "Помилка встановлення $package, продовжуємо..."
    done < "requirements.txt"
fi

# Додаємо Flask-Migrate та Gunicorn для production
pip install Flask-Migrate gunicorn

# Переконаємось, що flask-jwt-extended встановлено
pip install flask-jwt-extended==4.4.4 --force-reinstall

# Файл config.py повинен мати інформацію для з'єднання з PostgreSQL
# Наприклад, через змінну середовища DATABASE_URI:
export DATABASE_URI="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
export FLASK_APP=app.py
export FLASK_ENV=$MODE

# Міграції БД
flask db init || true
flask db migrate -m "Initial migration" || true
flask db upgrade || true

# Перевірка стану бек-енду
echo ">>> Тестуємо backend..."
python -m pytest tests/ || echo "Тести не знайдено або вони не пройшли"

#######################
# 8. НАЛАШТУВАННЯ FRONTEND #
#######################
echo ">>> Налаштовуємо Frontend (React)"
cd "$FRONTEND_DIR"
npm install

# Налаштування середовища для frontend
if [ "$MODE" == "production" ]; then
  echo ">>> Будуємо production-версію frontend..."
  npm run build

  # Встановлюємо Nginx якщо production
  sudo apt install -y nginx
  
  # Налаштовуємо Nginx для React застосунку
  sudo bash -c "cat > /etc/nginx/sites-available/mvp-frontend << EOF
server {
    listen 80;
    root $FRONTEND_DIR/build;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF"

  sudo ln -sf /etc/nginx/sites-available/mvp-frontend /etc/nginx/sites-enabled/
  sudo nginx -t && sudo systemctl restart nginx
fi

#######################
# 9. ЗАПУСК СЕРВІСІВ #
#######################
if [ "$MODE" == "production" ]; then
  # Створюємо systemd сервіс для бек-енду
  sudo bash -c "cat > /etc/systemd/system/mvp-backend.service << EOF
[Unit]
Description=MVP Backend Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment=DATABASE_URI=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
Environment=FLASK_ENV=production
ExecStart=$BACKEND_DIR/venv/bin/gunicorn -b 0.0.0.0:5000 -w 4 app:create_app('production')
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

  sudo systemctl daemon-reload
  sudo systemctl enable mvp-backend
  sudo systemctl restart mvp-backend
  
  echo ">>> Сервіси запущено в production режимі"
  echo ">>> Бек-енд працює через systemd, фронт-енд через Nginx"
else
  # Повертаємось до venv бек-енду та запускаємо його в development режимі
  cd "$BACKEND_DIR"
  source venv/bin/activate
  
  echo ">>> Запускаємо backend в development режимі (окремий термінал)..."
  # В реальному випадку запустити в окремому терміналі через tmux або screen
  # Для прикладу просто показуємо команду
  echo "     cd $BACKEND_DIR && source venv/bin/activate && python app.py"
  
  echo ">>> Запускаємо frontend в development режимі (окремий термінал)..."
  echo "     cd $FRONTEND_DIR && npm start"
fi

#######################
# 10. ЗАВЕРШЕННЯ #
#######################
echo ">>> Підготовка сервера завершена!"
echo ">>> MVP готовий до використання!"
if [ "$MODE" == "development" ]; then
  echo ">>> Режим розробки. Запустіть окремо:"
  echo "    1) Backend: cd $BACKEND_DIR && source venv/bin/activate && python app.py"
  echo "    2) Frontend: cd $FRONTEND_DIR && npm start"
else
  echo ">>> Production режим активовано."
  echo "    Backend запущено як сервіс: sudo systemctl status mvp-backend"
  echo "    Frontend доступний через Nginx на порту 80"
fi
echo ""
echo "Готово!"
