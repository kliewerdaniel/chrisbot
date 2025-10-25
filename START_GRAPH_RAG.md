# How to Start the Graph RAG System

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js 18+** installed
3. **Ollama** installed and running

## Step 1: Install Ollama

```bash
# On macOS
brew install ollama

# On Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

In another terminal, pull the required model:
```bash
ollama pull mistral
```

## Step 2: Install Python Dependencies

```bash
# In the project root directory
pip3 install --break-system-packages -r requirements.txt
```

## Step 3: Build Initial Knowledge Graph

```bash
# Process Reddit data and create the knowledge graph
cd scripts
python3 ingest_reddit_data_ollama.py

# This will:
# - Extract entities using Ollama
# - Generate embeddings for posts
# - Build the knowledge graph
# - Save to data/knowledge_graph_ollama.db and .pkl
```

## Step 4: Start the Next.js Application

```bash
# In the project root directory
npm install
npm run dev
```

The application will be available at `http://localhost:3000`

## Step 5: Test Graph RAG Functionality

### Option 1: Run Comprehensive Tests
```bash
cd scripts
python3 comprehensive_graph_rag_test.py
```

### Option 2: Test Individual Components

#### Test Entity Extraction
```bash
cd scripts
python3 -c "
from ingest_reddit_data_ollama import OllamaGraphBuilder
builder = OllamaGraphBuilder()
entities = builder.extract_entities_with_ollama('Franklin Barbecue is amazing BBQ in Austin!')
print('Entities:', entities)
"
```

#### Test Graph RAG Query
```bash
cd scripts
python3 graph_rag_query_ollama.py "Austin restaurants" 3
```

#### Test API Endpoints
```bash
# Test Graph RAG API
curl -X POST http://localhost:3000/api/graph-rag \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Austin restaurants", "limit": 3}'

# Test Chat API with Graph RAG enabled
curl -X POST http://localhost:3000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "What restaurants are good in Austin?",
    "model": "mistral-small3.2:latest",
    "promptId": "default",
    "graphRAG": true
  }'
```

## Step 6: Use the Chat Interface

1. Open `http://localhost:3000` in your browser
2. Look for the **"🧠 RAG Off"** button in the chat header
3. Click it to toggle to **"🧠 RAG On"**
4. Start chatting - the system will now use Graph RAG for context

## Example Queries to Try

- "What are good restaurants in Austin Texas?"
- "Tell me about Franklin Barbecue"
- "What tech companies are in Austin?"
- "What's the homeless situation like in Austin?"

## Troubleshooting

### Ollama Not Running
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# In another terminal
ollama pull mistral
```

### Missing Dependencies
```bash
pip3 install ollama networkx scikit-learn numpy
```

### Database Issues
```bash
# Force rebuild the knowledge graph
cd scripts
rm -f ../data/knowledge_graph_ollama.*
python3 ingest_reddit_data_ollama.py
```

### Next.js Build Issues
```bash
# Clear Next.js cache and rebuild
rm -rf .next
npm run build
npm run dev
```

## Production Deployment

For production use:

1. **Scale the data**: Process more Reddit posts for better coverage
2. **Optimize performance**: Implement caching and batch processing
3. **Add monitoring**: Track query performance and accuracy
4. **Enable error handling**: Add graceful fallbacks when Ollama is unavailable

## Quick Start Script

Create a `start.sh` script for easy startup:

```bash
#!/bin/bash
echo "Starting Graph RAG System..."

# Check Ollama
if ! ollama list | grep -q mistral; then
    echo "Pulling Mistral model..."
    ollama pull mistral
fi

# Start Ollama in background if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Install Python dependencies
pip3 install --break-system-packages -r requirements.txt

# Build knowledge graph
cd scripts
python3 ingest_reddit_data_ollama.py

# Start the application
cd ..
npm run dev
```

Make it executable and run:
```bash
chmod +x start.sh
./start.sh
```

## System Status

After following these steps, you should have:
- ✅ Ollama running with Mistral model
- ✅ Knowledge graph built from Reddit data
- ✅ Next.js application serving at localhost:3000
- ✅ Graph RAG enabled chat functionality
- ✅ 100% of tests passing

The system is now ready to extract entities, crawl the vector database, and provide RAG-enhanced chat responses! 🚀
