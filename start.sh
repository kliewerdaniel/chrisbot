#!/bin/bash
# Start ChrisBot08 application
# This script sets up and starts the full application including Next.js, TTS, and Python services

set -e  # Exit on any error

echo "🚀 Starting ChrisBot08 setup..."

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Please install Node.js 18+ first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed. Please install Python 3.8+ first."; exit 1; }

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Set up TTS (Coqui) - assuming already cloned in TTS/
echo "🎵 Setting up Text-to-Speech (TTS)..."

if [ ! -d "venv311" ]; then
    echo "Creating TTS virtual environment..."
    python3.11 -m venv venv311
fi
source venv311/bin/activate
git clone https://github.com/coqui-ai/TTS.git
echo "Installing TTS dependencies..."
cd TTS
pip install --upgrade pip
pip install -r requirements.txt
pip install trainer
pip install -e .

echo "Starting TTS server in background..."
python3 TTS/server/server.py --model_name tts_models/en/ljspeech/tacotron2-DDC --port 8080 &
TTS_PID=$!
cd ..
echo "TTS server started with PID: $TTS_PID"


