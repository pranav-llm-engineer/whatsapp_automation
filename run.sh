#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Check if port 8000 is in use and kill if necessary (optional safeguard)
# lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "Starting FastAPI backend..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting Streamlit frontend..."
streamlit run frontend/app.py --server.port 8503

# Trap to kill background backend if script exits
trap "kill $BACKEND_PID" EXIT
