#!/usr/bin/env python3
"""
Enhanced Graph RAG query script using Ollama for semantic search.
Called by the Next.js API to perform RAG queries on the enhanced knowledge graph.
"""

import sys
import json
import os
from pathlib import Path

# Add the current directory to the path so we can import the enhanced builder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest_reddit_data_ollama import OllamaGraphBuilder

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Query and limit parameters required"}))
        sys.exit(1)

    query = sys.argv[1]
    try:
        limit = int(sys.argv[2])
    except ValueError:
        print(json.dumps({"error": "Limit must be an integer"}))
        sys.exit(1)

    try:
        # Initialize the enhanced graph builder
        builder = OllamaGraphBuilder()

        # Load the enhanced graph and embeddings
        if not builder.load_graph():
            # If no cached enhanced data, return error with instructions
            print(json.dumps({
                "error": "Enhanced knowledge graph not found. Please run the enhanced ingestion script first.",
                "instructions": "Run 'cd scripts && python3 ingest_reddit_data_ollama.py' to create the enhanced graph with Ollama."
            }))
            sys.exit(1)

        # Perform enhanced retrieval with Ollama
        context = builder.retrieve_context(query, limit)

        # Format the context for the LLM with enhanced information
        formatted_context = []
        metadata = []

        for item in context:
            # Enhanced formatting with entities and sentiment
            formatted_item = ""
            if item.get('title'):
                formatted_item += f"Title: {item['title']}\n"

            # Add entity information
            if item.get('entities') and len(item['entities']) > 0:
                entity_names = [e['entity'] for e in item['entities'] if isinstance(e, dict)]
                if entity_names:
                    formatted_item += f"Key Topics: {', '.join(entity_names)}\n"

            # Add sentiment if available
            if item.get('sentiment') is not None and abs(item['sentiment']) > 0.1:
                sentiment_desc = "positive" if item['sentiment'] > 0 else "negative"
                formatted_item += f"Tone: {sentiment_desc}\n"

            formatted_item += f"Content: {item['content'][:600]}..."

            formatted_context.append(formatted_item)

            # Enhanced metadata
            metadata.append({
                'id': item['id'],
                'title': item.get('title'),
                'author': item.get('author'),
                'subreddit': item.get('subreddit'),
                'score': item.get('score'),
                'entities': item.get('entities', []),
                'sentiment': item.get('sentiment'),
                'relevance_score': item['relevance_score'],
                'retrieval_method': item.get('retrieval_method', 'unknown'),
                'content_preview': item['content'][:300] + "..." if len(item['content']) > 300 else item['content']
            })

        print(json.dumps({
            "context": formatted_context,
            "metadata": metadata,
            "query": query,
            "limit": limit,
            "enhancement": "ollama_semantic_search",
            "total_results": len(context)
        }))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
