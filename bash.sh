#!/bin/bash

set -e  # Зупинити скрипт у разі помилки

#######################
#    УТИЛІТИ         #
#######################
# Функція для виведення повідомлень
log_message() {
    echo ">>> $1"
}

# Функція для обробки помилок
handle_error() {
    echo "ПОМИЛКА: $1"
    exit 1
}

# Перевірка існування директорії
check_directory() {
    if [ ! -d "$1" ]; then
        handle_error "Директорія $1 не існує!"
    fi
}

#######################
#      ЗМІННІ         #
#######################
DB_NAME="logtagger"
DB_USER="logtagger"
DB_PASSWORD="logtagger"  # В реальному середовищі використовуйте більш безпечний пароль

# Шляхи до директорій
PROJECT_DIR="/mnt/d/MVP_2/LogTagger"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_DIR="$PROJECT_DIR/backend"
MODE=${1:-development}

# Встановлення прав виконання для скриптів
for script in "$PROJECT_DIR"/{clean_deploy.sh,deploy.sh,run.sh,backend/manage.py}; do
    chmod +x "$script" 2>/dev/null || true
done

# Перевірка необхідних директорій
check_directory "$BACKEND_DIR"

#######################
# 1. ОНОВЛЕННЯ СИСТЕМИ #
#######################
log_message "Оновлюємо систему..."
sudo apt update && sudo apt upgrade -y

###########################
# 2. ВСТАНОВЛЕННЯ ЗАЛЕЖНОСТЕЙ #
###########################
log_message "Встановлюємо необхідні пакети..."
sudo apt install -y python3 python3-venv python3-pip build-essential \
    git curl ca-certificates postgresql postgresql-contrib libpq-dev python3-dev

#######################
# 3. ВСТАНОВЛЕННЯ NODE.JS #
#######################
log_message "Встановлюємо Node.js версії 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Перевірка версії Node.js
node_version=$(node -v)
log_message "Встановлено версію Node.js: $node_version"
if [[ ! $node_version == v20* ]]; then
    echo "УВАГА: Встановлена версія Node.js ($node_version) не є версією 20.x"
    echo "Це може викликати проблеми із залежностями frontend-частини"
fi

#######################
# 4. НАЛАШТУВАННЯ POSTGRESQL #
#######################
log_message "Налаштування PostgreSQL..."
# Запуск і налаштування PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Створення користувача та бази даних
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER $DB_USER WITH SUPERUSER;" 2>/dev/null || true

# Налаштування доступу
sudo sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
sudo bash -c "echo \"host all all 0.0.0.0/0 md5\" >> /etc/postgresql/*/main/pg_hba.conf"
sudo systemctl restart postgresql

#######################
# 5. НАЛАШТУВАННЯ BACKEND #
#######################
log_message "Налаштування Backend..."
cd "$BACKEND_DIR" || handle_error "Неможливо перейти в директорію $BACKEND_DIR"

# Створюємо віртуальне середовище
if [ -d "venv" ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate

# Встановлення залежностей
log_message "Встановлюємо Python-залежності..."
pip install --upgrade pip setuptools wheel

# Встановлення основних залежностей
pip install sqlalchemy==1.4.46 Werkzeug==2.2.2 Flask==2.2.2 \
    flask-sqlalchemy==3.0.3 Flask-Cors==3.0.10 psycopg2-binary \
    tabulate requests python-dateutil pandas pyyaml

# Створення конфігурації, якщо потрібно
CONFIG_FILE="$BACKEND_DIR/config.py"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << EOF
class Config:
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = "app.log"
    LOG_LEVEL = "INFO"
    EXPORT_DIR = "exports"

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/${DB_NAME}_test"

def get_config(env_name):
    if env_name == 'production':
        return ProductionConfig
    elif env_name == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
EOF
    log_message "Створено конфігураційний файл"
fi

# Налаштування змінних середовища
export FLASK_APP="$BACKEND_DIR/app.py"
export FLASK_DEBUG=$([[ "$MODE" == "development" ]] && echo 1 || echo 0)

# Застосування міграцій
log_message "Застосування міграцій..."
python manage.py db-init --mode $MODE || handle_error "Не вдалося ініціалізувати базу даних"
python manage.py migrate --mode $MODE || handle_error "Не вдалося застосувати міграції"

# Видалення надлишкових файлів авторизації
for file in services/auth.py routes/auth_routes.py routes/users_routes.py tools/check_users.py; do
    if [ -f "$BACKEND_DIR/$file" ]; then
        rm -f "$BACKEND_DIR/$file"
        log_message "Видалено: $file"
    fi
done

# Створення необхідних директорій
mkdir -p "$BACKEND_DIR/logs" "$BACKEND_DIR/exports"

#######################
# 6. НАЛАШТУВАННЯ FRONTEND #
#######################
if [ -d "$FRONTEND_DIR" ]; then
    log_message "Налаштування Frontend..."
    cd "$FRONTEND_DIR" || handle_error "Неможливо перейти в директорію $FRONTEND_DIR"
    npm install
    
    if [ "$MODE" == "production" ]; then
        # Production режим - будуємо статичну версію та налаштовуємо Nginx
        log_message "Будуємо production-версію frontend..."
        npm run build
        
        sudo apt install -y nginx
        
        # Конфігурація Nginx
        sudo bash -c "cat > /etc/nginx/sites-available/logtagger << EOF
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

        sudo ln -sf /etc/nginx/sites-available/logtagger /etc/nginx/sites-enabled/
        sudo nginx -t && sudo systemctl restart nginx
    else
        # Development режим - додаємо проксі в package.json
        if ! grep -q '"proxy":' package.json; then
            sed -i '$ s/}$/,\n  "proxy": "http:\/\/localhost:5000"\n}/' package.json
            log_message "Додано проксі до package.json"
        fi
    fi
else
    log_message "Директорія фронтенду не знайдена. Пропускаємо налаштування фронтенду."
fi

#######################
# 7. ЗАПУСК СЕРВІСІВ #
#######################
if [ "$MODE" == "production" ]; then
    # Налаштування production-сервера
    pip install gunicorn
    
    # Створення systemd-сервісу
    sudo bash -c "cat > /etc/systemd/system/logtagger-backend.service << EOF
[Unit]
Description=LogTagger Backend Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment=FLASK_DEBUG=0
ExecStart=$BACKEND_DIR/venv/bin/gunicorn -b 0.0.0.0:5000 -w 4 app:create_app('production')
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

    sudo systemctl daemon-reload
    sudo systemctl enable logtagger-backend
    sudo systemctl restart logtagger-backend
    
    log_message "Сервіси запущено в production режимі"
    log_message "Бек-енд працює через systemd, фронт-енд через Nginx"
else
    # Запуск development-сервера
    cd "$BACKEND_DIR" || handle_error "Неможливо перейти в директорію $BACKEND_DIR"
    source venv/bin/activate
    log_message "Запускаємо сервер в режимі розробки..."
    python manage.py runserver --mode development
fi

log_message "Готово! LogTagger MVP успішно встановлено."
