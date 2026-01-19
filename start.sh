#!/bin/bash

# Kindle Sender - Quick Start Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/server"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           Kindle Sender - Setup & Start                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

cd "$SERVER_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "   Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit server/.env with your settings:"
    echo "   - SMTP_USERNAME: Your email address"
    echo "   - SMTP_PASSWORD: Your email app password"
    echo "   - KINDLE_EMAIL: Your Kindle email address"
    echo ""
    read -p "Press Enter to open .env in your editor, or Ctrl+C to exit..."
    ${EDITOR:-nano} .env
fi

echo ""
echo "🚀 Starting Kindle Sender server..."
echo "   Press Ctrl+C to stop"
echo ""

python app.py
