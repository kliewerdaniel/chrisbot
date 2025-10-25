#!/bin/bash
# Start ChrisBot application
# This script sets up and starts the full application including Next.js and TTS

set -e  # Exit on any error

echo "🚀 Starting ChrisBot setup..."

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Please install Node.js 18+ first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed. Please install Python 3.8+ first."; exit 1; }

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Set up TTS (Coqui)
echo "🎵 Setting up Text-to-Speech (TTS)..."

if [ -d "TTS" ]; then
    echo "Removing existing TTS directory..."
    rm -rf TTS
fi
echo "Cloning Coqui TTS repository..."
git clone https://github.com/coqui-ai/TTS.git

cd TTS
echo "Patching requirements.txt for Python compatibility..."
sed -i '' '/trainer>=0.0.36/s/^/# /' requirements.txt
if [ ! -d "venv311" ]; then
    echo "Creating TTS virtual environment..."
    # Use Python 3.11 if available, otherwise fall back to python3
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_CMD=python3.11
    else
        PYTHON_CMD=python3
    fi
    $PYTHON_CMD -m venv venv311
fi
echo "Activating virtual environment..."
source venv311/bin/activate
echo "Installing TTS dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
pip install trainer
python3 server.py
