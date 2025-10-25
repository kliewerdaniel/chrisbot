#!/bin/bash
# Test script to verify ChrisBot setup

echo "🧪 Testing ChrisBot setup..."

# Check if we're in the right directory
if [ ! -f "start.sh" ]; then
    echo "❌ Error: start.sh not found. Please run this script from the ChrisBot root directory."
    exit 1
fi

echo "✅ Found start.sh script"

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Git is required but not installed."; exit 1; }

echo "✅ All prerequisites are installed"

# Check if TTS directory exists
if [ -d "TTS" ]; then
    echo "✅ TTS directory exists"
else
    echo "⚠️ TTS directory not found. The start.sh script will clone it."
fi

# Check if .env.local exists
if [ -f ".env.local" ]; then
    echo "✅ .env.local file exists"
else
    echo "📝 .env.local not found. The start.sh script will create it from .env.example"
fi

# Check if node_modules exists
if [ -d "node_modules" ]; then
    echo "✅ Node.js dependencies are installed"
else
    echo "📦 Node.js dependencies not installed. The start.sh script will install them."
fi

echo ""
echo "🎉 Setup verification complete!"
echo "You can now run: bash start.sh"
echo ""
echo "This will:"
echo "  1. Install any missing dependencies"
echo "  2. Set up the Coqui TTS environment"
echo "  3. Start the TTS server on port 8080"
echo "  4. Start the Next.js development server on port 3000"
echo ""
echo "Make sure to also run 'ollama serve' in another terminal for AI functionality."
