#!/bin/bash

# Start StatEdge Servers
echo "Starting StatEdge servers..."

# Create Python virtual environment if it doesn't exist
if [ ! -d "/home/jeffreyconboy/StatEdge/python-service/venv" ]; then
    echo "Creating Python virtual environment..."
    cd /home/jeffreyconboy/StatEdge/python-service
    python3 -m venv venv
    source venv/bin/activate
    pip install uvicorn fastapi sqlalchemy asyncpg redis
else
    echo "Using existing Python virtual environment..."
    cd /home/jeffreyconboy/StatEdge/python-service
    source venv/bin/activate
fi

# Start backend API server
echo "Starting backend API server on port 8001..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Test backend API
echo "Testing backend API..."
curl -s http://localhost:8001/api/players/trending?limit=2 | head -c 100
echo ""

# Start frontend development server
echo "Starting frontend development server..."
cd /home/jeffreyconboy/StatEdge/frontends/agent-b-recreation
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo "Backend API: http://localhost:8001"
echo "Frontend: http://localhost:3002 (or next available port)"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop servers:"
echo "kill $BACKEND_PID $FRONTEND_PID"