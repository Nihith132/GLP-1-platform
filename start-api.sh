#!/bin/bash
# Start FastAPI Development Server

echo "Starting GLP-1 Drug Label Platform API..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt --quiet

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "Warning: backend/.env file not found!"
    echo "Please create one with your database credentials."
    exit 1
fi

# Start server
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/api/docs"
echo ""

cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
