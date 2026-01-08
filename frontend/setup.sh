#!/bin/bash

# GLP-1 Platform Frontend Setup Script

echo "=================================================="
echo "🚀 GLP-1 Regulatory Intelligence Platform"
echo "   Frontend Setup & Installation"
echo "=================================================="

cd "$(dirname "$0")"

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "   Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ Setup Complete!"
    echo "=================================================="
    echo ""
    echo "🎨 To start the development server:"
    echo "   npm run dev"
    echo ""
    echo "🏗️  To build for production:"
    echo "   npm run build"
    echo ""
    echo "👀 Development server will run on:"
    echo "   http://localhost:3000"
    echo ""
    echo "🔌 Make sure backend API is running on:"
    echo "   http://localhost:8000"
    echo ""
    echo "=================================================="
else
    echo ""
    echo "❌ Installation failed!"
    echo "   Please check the error messages above"
    exit 1
fi
