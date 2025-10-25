#!/bin/bash
# Start ChrisBot application
# This script sets up and starts the application with TTS support

echo "🚀 Starting ChrisBot setup..."

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Please install Node.js 18+ first."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed. Please install Python 3.8+ first."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Git is required but not installed. Please install Git first."; exit 1; }

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local file..."
    cp .env.example .env.local
fi

# Try to set up TTS (Coqui) - Optional, will use browser TTS as fallback
echo "🎵 Setting up Text-to-Speech (TTS)..."

# Clean up existing TTS setup if it exists
if [ -d "TTS" ]; then
    echo "🧹 Removing existing TTS directory..."
    rm -rf TTS
fi

echo "📥 Cloning Coqui TTS repository..."
# Try to clone TTS repo, but continue if it fails
TTS_SETUP_SUCCESS=true
if ! git clone https://github.com/coqui-ai/TTS.git 2>/dev/null; then
    echo "⚠️ TTS repository clone failed - will use browser TTS as fallback"
    TTS_SETUP_SUCCESS=false
fi

if [ "$TTS_SETUP_SUCCESS" = true ]; then
    cd TTS

    echo "🐍 Creating Python virtual environment..."
    # Try different Python versions
    PYTHON_CMD=""
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

    # Create virtual environment
    if ! $PYTHON_CMD -m venv venv311 2>/dev/null; then
        echo "❌ Failed to create virtual environment - will use browser TTS as fallback"
        TTS_SETUP_SUCCESS=false
        cd ..
    fi

    if [ "$TTS_SETUP_SUCCESS" = true ]; then
        # Activate virtual environment
        source venv311/bin/activate

        echo "📦 Installing TTS requirements..."
        if ! pip install -r requirements.txt >/dev/null 2>&1; then
            echo "❌ Failed to install TTS requirements - will use browser TTS as fallback"
            TTS_SETUP_SUCCESS=false
            cd ..
        fi

        if [ "$TTS_SETUP_SUCCESS" = true ]; then
            echo "🔨 Installing TTS package..."
            if ! pip install -e . >/dev/null 2>&1; then
                echo "❌ Failed to install TTS package - will use browser TTS as fallback"
                TTS_SETUP_SUCCESS=false
                cd ..
            fi
        fi
    fi

    if [ "$TTS_SETUP_SUCCESS" = true ]; then
        # Try to start TTS server in background (optional)
        echo "🎵 Starting TTS server..."
        cd ..
        nohup bash -c "cd TTS && source venv311/bin/activate && python TTS/server/server.py --model_name tts_models/en/ljspeech/tacotron2-DDC --port 8080" >/dev/null 2>&1 &
        TTS_PID=$!

        # Wait for TTS server to be ready
        echo "⏳ Waiting for TTS server..."
        SERVER_READY=false
        for i in {1..20}; do
          echo "   Checking TTS server (attempt $i/20)..."
          # Try checking if server responds to any request
          if curl -s --max-time 5 http://localhost:8080/ > /dev/null 2>&1 2>/dev/null; then
            echo "✅ TTS server is ready!"
            SERVER_READY=true
            break
          fi
          sleep 2
        done

        if [ "$SERVER_READY" = false ]; then
            echo "❌ TTS server failed to start within expected time"
            echo "   This might be due to model download issues or missing dependencies"
            echo "   The application will still work with browser TTS fallback"
            kill $TTS_PID 2>/dev/null || true
            TTS_PID=""
            TTS_SETUP_SUCCESS=false
        fi
    fi
fi

# Start the Next.js development server
echo "🌐 Starting Next.js development server..."
npm run dev &
NEXTJS_PID=$!

# Wait a moment for the server to start
echo "⏳ Waiting for Next.js to start..."
sleep 5

# Check if Next.js is running
if ! kill -0 $NEXTJS_PID 2>/dev/null; then
    echo "❌ Next.js failed to start. Check the logs above."
    # Kill TTS server if it was started
    kill $TTS_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 ChrisBot is running successfully!"
echo "📱 Open your browser and navigate to: http://localhost:3000"
echo ""

if [ "$TTS_SETUP_SUCCESS" = true ] && [ -n "$TTS_PID" ]; then
    echo "🎵 TTS functionality:"
    echo "   ✅ Coqui TTS server is running on port 8080"
    echo "   ✅ Frontend will use Coqui TTS for high-quality speech synthesis"
    echo "   ✅ Browser TTS available as fallback"
else
    echo "🎵 TTS functionality:"
    echo "   ⚠️ Coqui TTS setup failed - using browser TTS"
    echo "   ✅ Browser TTS is available and working"
    echo "   📝 You can try running 'bash setup-tts.sh' to set up Coqui TTS later"
fi

echo ""
echo "🛑 Press Ctrl+C to stop the server"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $NEXTJS_PID 2>/dev/null || true
    kill $TTS_PID 2>/dev/null || true
    echo "✅ Servers stopped. Goodbye!"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup INT TERM

# Wait for the Next.js process
wait $NEXTJS_PID
