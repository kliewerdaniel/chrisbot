#!/usr/bin/env python3
"""
Graph RAG query script.
Called by the Next.js API to perform RAG queries on the knowledge graph.
"""

import sys
import json
import os
from pathlib import Path

# Add the current directory to the path so we can import the RedditGraphBuilder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest_reddit_data import RedditGraphBuilder

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
        # Initialize the graph builder (will load from cache if available)
        builder = RedditGraphBuilder()

        # Load the graph
        if not builder.load_graph():
            # If no cached graph, try to build it
            builder.ingest_data()

        # Perform the query
        context = builder.retrieve_context(query, limit)

        # Format the context for the LLM
        formatted_context = []
        for item in context:
            if item.get('title'):
                formatted_context.append(f"Title: {item['title']}\nContent: {item['content'][:500]}...")
            else:
                formatted_context.append(f"Content: {item['content'][:500]}...")

        print(json.dumps({
            "context": formatted_context,
            "metadata": context
        }))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
