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
cd TTS
if [ ! -d "venv311" ]; then
    echo "Creating TTS virtual environment..."
    python3.11 -m venv venv311
fi
source venv311/bin/activate
git clone https://github.com/coqui-ai/TTS.git
echo "Installing TTS dependencies..."
pip install --upgrade pip
pip install -r TTS/requirements.txt
pip install trainer
pip install -e .

echo "Starting TTS server in background..."
python3 TTS/server/server.py --model_name tts_models/en/ljspeech/tacotron2-DDC --port 8080 &
TTS_PID=$!
cd ..
echo "TTS server started with PID: $TTS_PID"

# Check if Ollama is running
echo "🤖 Checking Ollama status..."
if ! python3 -c "
import ollama
try:
    ollama.generate(model='mistral', prompt='test', options={'num_predict': 1})
    print('✅ Ollama is running and accessible.')
except Exception as e:
    print(f'⚠️  Ollama connection test failed: {e}')
    echo 'Please ensure Ollama is running with: ollama serve'
    echo 'And pull a model with: ollama pull mistral'
    echo 'You can continue without it, but Graph RAG features will not work.'
"
# Optional: Initialize knowledge graph (comment out if not needed)
# echo "🧠 Initializing knowledge graph (this may take several minutes)..."
# bash scripts/init-knowledge-graph.sh

# Start the Next.js development server
echo "🌐 Starting Next.js development server..."
npm run dev

# When Next.js is stopped, also kill TTS server
echo "Stopping TTS server..."
kill $TTS_PID 2>/dev/null

echo "✅ ChrisBot08 stopped."
