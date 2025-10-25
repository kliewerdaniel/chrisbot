#!/bin/bash
# Setup Coqui TTS for ChrisBot
# This script sets up the full TTS functionality after the main application is running

set -e  # Exit on any error

echo "🎵 Setting up Coqui TTS for ChrisBot..."

# Check if we're in the right directory
if [ ! -f "start.sh" ]; then
    echo "❌ Error: start.sh not found. Please run this script from the ChrisBot root directory."
    exit 1
fi

# Check if TTS directory already exists and is configured
if [ -d "TTS" ] && [ -f "TTS/venv311/bin/activate" ]; then
    echo "🎵 Checking existing TTS setup..."
    cd TTS
    if source venv311/bin/activate && python -c "from TTS.api import TTS" 2>/dev/null; then
        echo "✅ TTS is already configured and ready!"
        echo "🎵 Starting TTS server..."
        python TTS/server/server.py --model_name tts_models/en/ljspeech/tacotron2-DDC --port 8080 &
        TTS_PID=$!
        cd ..
        echo "✅ TTS server started with PID: $TTS_PID"
        echo "🎵 You can now use Coqui TTS in the ChrisBot interface!"
        echo "🛑 Press Ctrl+C to stop the TTS server"
        wait $TTS_PID
        exit 0
    else
        echo "⚠️ TTS directory exists but is not properly configured. Reinstalling..."
        cd ..
        rm -rf TTS
    fi
fi

echo "📥 Cloning Coqui TTS repository..."
if ! git clone https://github.com/coqui-ai/TTS.git; then
    echo "❌ Failed to clone TTS repository. Please check your internet connection and try again."
    exit 1
fi

echo "✅ TTS repository cloned successfully"

cd TTS

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_CMD=python3.11
elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_CMD=python3.10
elif command -v python3.9 >/dev/null 2>&1; then
    PYTHON_CMD=python3.9
else
    PYTHON_CMD=python3
fi

echo "Using Python: $PYTHON_CMD"

# Create virtual environment with error checking
if ! $PYTHON_CMD -m venv venv311; then
    echo "❌ Failed to create virtual environment. Trying with python3..."
    if ! python3 -m venv venv311; then
        echo "❌ Virtual environment creation failed. Please check Python installation."
        cd ..
        exit 1
    fi
    PYTHON_CMD=python3
fi

# Verify virtual environment was created
if [ ! -f "venv311/bin/activate" ]; then
    echo "❌ Virtual environment activation script not found."
    cd ..
    exit 1
fi

# Activate virtual environment and install dependencies
echo "🔧 Activating virtual environment and installing dependencies..."
source venv311/bin/activate

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements with better error handling
echo "📦 Installing TTS requirements..."
if ! pip install -r requirements.txt; then
    echo "❌ Failed to install TTS requirements. Please check your internet connection and Python version."
    echo "   Python version: $(python --version)"
    echo "   Pip version: $(pip --version)"
    cd ..
    exit 1
fi

# Install TTS in development mode
echo "🔨 Installing TTS package..."
if ! pip install -e .; then
    echo "❌ TTS installation failed. Please check the error messages above."
    cd ..
    exit 1
fi

# Verify TTS installation
echo "✅ Verifying TTS installation..."
if ! python -c "from TTS.api import TTS; print('✅ TTS imported successfully')" 2>/dev/null; then
    echo "❌ TTS verification failed. The installation may not be complete."
    cd ..
    exit 1
fi

# Go back to project root
cd ..

echo ""
echo "🎉 TTS setup completed successfully!"
echo "🎵 Starting TTS server..."
cd TTS
source venv311/bin/activate
python TTS/server/server.py --model_name tts_models/en/ljspeech/tacotron2-DDC --port 8080 &
TTS_PID=$!
cd ..

echo "✅ TTS server started with PID: $TTS_PID"
echo ""
echo "🎵 You can now use Coqui TTS in the ChrisBot interface!"
echo "📱 Open your browser and navigate to: http://localhost:3000"
echo "🎵 Select a TTS model from the dropdown in the chat interface"
echo ""
echo "🛑 Press Ctrl+C to stop the TTS server"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping TTS server..."
    kill $TTS_PID 2>/dev/null || true
    echo "✅ TTS server stopped. Goodbye!"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup INT TERM

# Wait for the TTS process
wait $TTS_PID
