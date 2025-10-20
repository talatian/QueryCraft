#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
python manage.py create_superuser

echo "Seeding database with sample data..."
python manage.py seed_db --num 1000

echo "Starting the Django server..."
exec python manage.py runserver 0.0.0.0:8000