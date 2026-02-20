#!/bin/bash

# OpenMesh Quick Start Script

echo "Starting OpenMesh v0.1..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Warning: Redis is not running. Please start Redis first."
    echo "  Linux/Mac: redis-server"
    echo "  Docker: docker run -d -p 6379:6379 redis:alpine"
    exit 1
fi

# Initialize database if it doesn't exist
if [ ! -f "openmesh.db" ]; then
    echo "Initializing database..."
    python init_db.py
fi

# Start API server in background
echo "Starting API server..."
python main.py &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Celery worker in background
echo "Starting Celery worker..."
python run_celery.py &
CELERY_PID=$!

echo ""
echo "OpenMesh is running!"
echo "  API Server: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Celery Worker: Running"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $API_PID $CELERY_PID 2>/dev/null; exit" INT TERM
wait

