#!/bin/bash
# Initialize knowledge graph script

echo "Initializing Reddit knowledge graph..."

# Check if Python dependencies are installed (including Ollama)
python3 -c "
import sys
try:
    import frontmatter
    import networkx
    import sqlite3
    import ollama
    import numpy
    import sklearn
    print('All Python dependencies found including Ollama.')
except ImportError as e:
    print(f'Missing dependency: {e}')
    print('Please install dependencies with: pip install -r requirements.txt')
    print('Also ensure Ollama is installed and running: https://ollama.ai')
    sys.exit(1)
"

# Check if Ollama is running
echo "Checking Ollama connection..."
if ! python3 -c "
import ollama
try:
    ollama.generate(model='mistral', prompt='test', options={'num_predict': 1})
    print('Ollama is running.')
except Exception as e:
    print(f'Ollama connection failed: {e}')
    print('Please start Ollama with: ollama serve')
    print('And ensure mistral model is available: ollama pull mistral')
    import sys
    sys.exit(1)
"; then
    echo "Ollama check failed. Please ensure Ollama is running."
    exit 1
fi

# Run the enhanced ingestion script with Ollama
cd scripts
echo "Running enhanced data ingestion with Ollama..."
python3 ingest_reddit_data_ollama.py

if [ $? -eq 0 ]; then
    echo "Knowledge graph initialization complete!"
    echo "You can now use Graph RAG in the chat application."
else
    echo "Knowledge graph initialization failed!"
    exit 1
fi
