#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LogTagger cleanup process...${NC}"

# Define directories
BACKEND_DIR="./backend"
FRONTEND_DIR="./frontend"
LOG_DIR="${BACKEND_DIR}/logs"
EXPORT_DIR="${BACKEND_DIR}/exports"
DATA_DIR="${BACKEND_DIR}/data"
DB_FILE="${BACKEND_DIR}/logtagger.db"
MIGRATIONS_ARCHIVE="${BACKEND_DIR}/archive"

# Stop any running backend processes
echo -e "${YELLOW}Stopping any running backend processes...${NC}"
pkill -f "python.*app.py" || echo -e "${YELLOW}No backend processes found to stop${NC}"

# Clean database file
if [ -f "$DB_FILE" ]; then
    echo -e "${YELLOW}Removing database file: ${DB_FILE}${NC}"
    rm -f "$DB_FILE"
    echo -e "${GREEN}✓ Database file removed${NC}"
else
    echo -e "${YELLOW}No database file found to remove${NC}"
fi

# Clean logs directory
if [ -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}Cleaning logs directory...${NC}"
    rm -rf "${LOG_DIR:?}"/* || true
    echo -e "${GREEN}✓ Logs directory cleaned${NC}"
else
    echo -e "${YELLOW}Creating logs directory...${NC}"
    mkdir -p "$LOG_DIR"
    echo -e "${GREEN}✓ Logs directory created${NC}"
fi

# Clean exports directory
if [ -d "$EXPORT_DIR" ]; then
    echo -e "${YELLOW}Cleaning exports directory...${NC}"
    rm -rf "${EXPORT_DIR:?}"/* || true
    echo -e "${GREEN}✓ Exports directory cleaned${NC}"
else
    echo -e "${YELLOW}Creating exports directory...${NC}"
    mkdir -p "$EXPORT_DIR"
    echo -e "${GREEN}✓ Exports directory created${NC}"
fi

# Ensure data directory exists but preserve MITRE data if it exists
if [ -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}Checking data directory...${NC}"
    # Preserve MITRE data file if it exists
    if [ -f "${DATA_DIR}/mitre_attack.json" ]; then
        echo -e "${YELLOW}Preserving existing MITRE data...${NC}"
        mkdir -p /tmp/logtagger_tmp
        cp "${DATA_DIR}/mitre_attack.json" /tmp/logtagger_tmp/
        rm -rf "${DATA_DIR:?}"/* || true
        mkdir -p "$DATA_DIR"
        mv /tmp/logtagger_tmp/mitre_attack.json "$DATA_DIR/"
        rm -rf /tmp/logtagger_tmp
        echo -e "${GREEN}✓ Data directory cleaned, MITRE data preserved${NC}"
    else
        echo -e "${YELLOW}Cleaning data directory...${NC}"
        rm -rf "${DATA_DIR:?}"/* || true
        echo -e "${GREEN}✓ Data directory cleaned${NC}"
    fi
else
    echo -e "${YELLOW}Creating data directory...${NC}"
    mkdir -p "$DATA_DIR"
    echo -e "${GREEN}✓ Data directory created${NC}"
fi

# Create archive directory if it doesn't exist
if [ ! -d "$MIGRATIONS_ARCHIVE" ]; then
    echo -e "${YELLOW}Creating archive directory for migrations...${NC}"
    mkdir -p "$MIGRATIONS_ARCHIVE"
    echo -e "${GREEN}✓ Archive directory created${NC}"
fi

# Видалення архіву міграцій
if [ -d "$MIGRATIONS_ARCHIVE" ]; then
    echo -e "${YELLOW}Видалення архіву міграцій...${NC}"
    rm -rf "${MIGRATIONS_ARCHIVE:?}"
    echo -e "${GREEN}✓ Архів міграцій видалено${NC}"
fi

# Видалення папки міграцій, якщо вона існує
MIGRATIONS_DIR="${BACKEND_DIR}/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
    echo -e "${YELLOW}Видалення директорії міграцій...${NC}"
    rm -rf "${MIGRATIONS_DIR:?}"
    echo -e "${GREEN}✓ Директорія міграцій видалена${NC}"
fi

# Clean Python cache files
echo -e "${YELLOW}Removing Python cache files...${NC}"
find "$BACKEND_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$BACKEND_DIR" -name "*.pyc" -delete
echo -e "${GREEN}✓ Python cache files removed${NC}"

# Ask if frontend build should be cleaned
read -p "Do you want to clean frontend build files? (y/n): " clean_frontend
if [[ "$clean_frontend" =~ ^[Yy]$ ]]; then
    if [ -d "${FRONTEND_DIR}/build" ]; then
        echo -e "${YELLOW}Removing frontend build files...${NC}"
        rm -rf "${FRONTEND_DIR:?}/build"
        echo -e "${GREEN}✓ Frontend build files removed${NC}"
    else
        echo -e "${YELLOW}No frontend build directory found${NC}"
    fi
    
    # Clean node_modules if user wants to
    read -p "Do you want to remove node_modules (this will require npm install later)? (y/n): " clean_modules
    if [[ "$clean_modules" =~ ^[Yy]$ ]]; then
        if [ -d "${FRONTEND_DIR}/node_modules" ]; then
            echo -e "${YELLOW}Removing node_modules directory...${NC}"
            rm -rf "${FRONTEND_DIR:?}/node_modules"
            echo -e "${GREEN}✓ node_modules directory removed${NC}"
        else
            echo -e "${YELLOW}No node_modules directory found${NC}"
        fi
    fi
fi

# Ask if virtual environment should be recreated
read -p "Do you want to recreate the Python virtual environment? (y/n): " recreate_venv
if [[ "$recreate_venv" =~ ^[Yy]$ ]]; then
    venv_dir="${BACKEND_DIR}/venv"
    if [ -d "$venv_dir" ]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf "${venv_dir:?}"
    fi
    
    echo -e "${YELLOW}Creating new virtual environment...${NC}"
    python3 -m venv "$venv_dir"
    echo -e "${GREEN}✓ New virtual environment created${NC}"
    
    echo -e "${YELLOW}Installing dependencies...${NC}"
    source "${venv_dir}/bin/activate"
    pip install --upgrade pip
    pip install -r "${BACKEND_DIR}/requirements.txt"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

echo -e "${GREEN}Cleanup process completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Start the backend server: cd backend && python app.py"
echo -e "2. Start the frontend development server: cd frontend && npm start"
