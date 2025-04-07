#!/bin/bash

echo "Checking all model files for syntax errors..."

# Directory for model files
MODEL_DIR="/mnt/d/MVP_2/LogTagger/backend/models"

# Fix each model file
for model_file in "$MODEL_DIR"/*.py; do
    if [ -f "$model_file" ]; then
        # Skip __init__.py
        if [[ $(basename "$model_file") == "__init__.py" ]]; then
            continue
        fi
        
        # Check if file contains the error
        if grep -q "primary key=True" "$model_file"; then
            echo "Fixing syntax in: $model_file"
            sed -i 's/primary key=True/primary_key=True/g' "$model_file"
        fi
    fi
done

# Fix deploy.sh to use correct syntax in future
DEPLOY_SCRIPT="/mnt/d/MVP_2/LogTagger/deploy.sh"
if [ -f "$DEPLOY_SCRIPT" ]; then
    echo "Updating deploy.sh script with correct syntax..."
    sed -i 's/primary key=True/primary_key=True/g' "$DEPLOY_SCRIPT"
fi

echo "Syntax check complete!"

# Verify all model files
echo "Verifying all model files..."
python3 <<EOF
import os
import re

model_dir = "$MODEL_DIR"
pattern = re.compile(r'primary\s+key\s*=')
errors_found = False

for filename in os.listdir(model_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        filepath = os.path.join(model_dir, filename)
        with open(filepath, 'r') as file:
            content = file.read()
            if pattern.search(content):
                print(f"ERROR: {filename} still contains 'primary key=' syntax")
                errors_found = True

if not errors_found:
    print("All model files use correct syntax!")
EOF
