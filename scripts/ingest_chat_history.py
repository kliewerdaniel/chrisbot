#!/usr/bin/env python3
"""
Chat history ingestion script for Graph RAG using Ollama.
Specifically handles ingesting chat history from the Next.js frontend.
This script supports the same RAG On functionality but ingests chat history instead of Reddit data.
"""

import sys
import json
from ingest_reddit_data_ollama import OllamaGraphBuilder

def main():
    import sys
    import json

    # Redirect all print statements to stderr for logging
    global print
    original_print = print
    def print_to_stderr(*args, **kwargs):
        kwargs.setdefault('file', sys.stderr)
        original_print(*args, **kwargs)
    print = print_to_stderr

    print("Starting chat history ingestion script...")

    # Read JSON input from stdin
    print("Reading input from stdin...")
    input_data = sys.stdin.read()
    print(f"Read {len(input_data)} characters from stdin")

    if not input_data:
        print(json.dumps({"error": "No input data received"}))
        sys.exit(1)

    try:
        print("Parsing JSON input...")
        data = json.loads(input_data)
        chat_sessions = data.get('chat_sessions', [])
        print(f"Found {len(chat_sessions)} chat sessions")
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    if not chat_sessions:
        print(json.dumps({"error": "No chat sessions provided"}))
        sys.exit(1)

    print(f"Processing {len(chat_sessions)} chat sessions...")

    try:
        # Extract the model from the first chat session (they should all be the same)
        model_to_use = 'mistral'  # default fallback
        if chat_sessions and len(chat_sessions) > 0:
            model_to_use = chat_sessions[0].get('model', 'mistral')
            # Remove .gguf extension if present (Ollama might handle this internally)
            model_to_use = model_to_use.replace('.gguf:latest', '').replace('.gguf', '')
            print(f"Using model: {model_to_use} (extracted from chat session)", file=sys.stderr)

        # Initialize the enhanced graph builder with the extracted model
        from ingest_reddit_data_ollama import OllamaGraphBuilder
        print("Initializing OllamaGraphBuilder...", file=sys.stderr)
        builder = OllamaGraphBuilder(model=model_to_use)
        print("✓ OllamaGraphBuilder initialized", file=sys.stderr)

        # Test Ollama connection with the actual model being used
        import ollama
        print(f"Testing Ollama connection with '{model_to_use}' model...", file=sys.stderr)
        try:
            response = ollama.generate(model=model_to_use, prompt='Hello', options={'num_predict': 1})
            print("✓ Ollama is running and model is available", file=sys.stderr)
        except Exception as e:
            print(f"Ollama connection test failed: {e}", file=sys.stderr)
            original_print(json.dumps({"error": f"Ollama connection failed: {e}. Please ensure Ollama is running and the model '{model_to_use}' is available with 'ollama pull {model_to_use}' if needed."}))
            sys.exit(1)

        # Ingest chat history
        print("Starting ingestion of chat history...", file=sys.stderr)
        processed_count = builder.ingest_chat_history(chat_sessions)
        print(f"✓ Processed {processed_count} conversations successfully", file=sys.stderr)

        # Output the result to stdout (this should NOT be redirected)
        original_print(json.dumps({
            "processed_count": processed_count,
            "message": f"Successfully ingested {processed_count} chat conversations"
        }))

    except Exception as e:
        import traceback
        print(f"Error during ingestion: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        original_print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
