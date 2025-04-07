#!/bin/bash

set -e

DB_NAME="logtagger"
DB_USER="logtagger"

echo "WARNING: This will delete ALL data in the $DB_NAME database."
read -p "Are you sure you want to continue? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Dropping database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "Creating fresh database..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "Database reset complete. Now run deploy.sh to initialize the schema."
