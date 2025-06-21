#!/bin/bash
# Start MCP server (background)
echo "Starting MCP server..."
cd "$(dirname "$0")/mcp_server" || exit 1
pip install -r requirements.txt
echo "Launching MCP server (Payments)..."
python main.py &
MCP_PID=$!
cd ..

# Start backend (background)
echo "Starting backend..."
cd backend || exit 1
pip install -r requirements.txt
echo "Launching backend (AI Agent)..."
export ANTHROPIC_API_KEY=sk-your-anthropic-key-here
uvicorn main:app --reload --port 8080 &
BACKEND_PID=$!
cd ..

# Start frontend (foreground)
echo "Starting frontend (React)..."
cd frontend || exit 1
npm install
npm start

# Cleanup on exit
trap "kill $MCP_PID $BACKEND_PID" EXIT
