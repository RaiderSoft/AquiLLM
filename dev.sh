#!/bin/bash

# Function to cleanup background processes on exit
cleanup() {
    echo "Cleaning up..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

echo "Starting development environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Start Django server in the background
echo "Starting Django server..."
docker compose --env-file .env up web &

# Wait for Django to start (check if the server is responding)
echo "Waiting for Django server to start..."
timeout=30
while ! curl -s http://localhost:8080 > /dev/null; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -le 0 ]; then
        echo "Timeout waiting for Django server"
        exit 1
    fi
done

# Navigate to React directory and start development server
echo "Starting React development server..."
cd react || exit 1

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the development server
echo "Starting Vite dev server..."
npm run dev

# Keep the script running
wait 