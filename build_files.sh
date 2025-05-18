#!/bin/bash
set -e

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations (optional but generally useful)
python manage.py migrate --noinput

echo "Build completed successfully"