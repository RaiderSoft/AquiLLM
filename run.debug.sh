# start.sh
#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $POSTGRES_HOST 5432; do
  sleep 1
done
echo "Database is up"

# Run migrations
echo "Running migrations..."
./manage.py migrate

# Start the application
echo "Starting application..."
exec python manage.py runserver 0.0.0.0:${PORT:-8080}
