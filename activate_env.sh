#!/bin/bash

# GPUStack UI Development Environment Setup Script

echo "🚀 Setting up GPUStack UI development environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating Python virtual environment..."
source venv/bin/activate

# Set Python path to include backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

echo "✅ Environment activated!"
echo ""
echo "📋 Available commands:"
echo "  • Run backend: cd backend && uvicorn main:app --reload --port 8001"
echo "  • Run tests: cd backend && python -m pytest"
echo "  • Install new packages: pip install <package_name>"
echo "  • Deactivate: deactivate"
echo ""
echo "🌐 Backend will be available at: http://localhost:8001"
echo "📚 API docs will be available at: http://localhost:8001/docs"
echo ""
echo "💡 Tip: You can now run the backend with:"
echo "    cd backend && uvicorn main:app --reload --port 8001" 