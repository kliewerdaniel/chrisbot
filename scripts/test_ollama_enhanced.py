#!/usr/bin/env python3
"""
Test script for enhanced Ollama GraphRAG functionality.
Creates sample data and tests entity extraction, embeddings, and retrieval.
"""

import ollama
import json
from pathlib import Path
import sys
sys.path.append('.')

from ingest_reddit_data_ollama import OllamaGraphBuilder

def create_sample_data():
    """Create sample Reddit posts for testing."""
    sample_posts = [
        {
            'id': 'sample_1',
            'type': 'submission',
            'author': 'testuser1',
            'title': 'Best restaurants in Austin Texas',
            'content': 'Looking for recommendations on great restaurants in Austin. We love BBQ places, food trucks, and some good Tex-Mex. Any suggestions for places like Franklin Barbecue or Torchys Tacos?',
            'subreddit': 'r/Austin',
            'created_utc': '2024-01-15T10:30:00Z',
            'score': 25,
            'permalink': '/r/Austin/comments/sample1/',
            'parent_id': None,
            'link_id': None,
            'url': None,
            'num_comments': 15
        },
        {
            'id': 'sample_2',
            'type': 'comment',
            'author': 'testuser2',
            'title': '',
            'content': 'Franklin Barbecue is amazing! The brisket is incredible. Also check out Barton Springs for swimming after eating too much BBQ.',
            'subreddit': 'r/Austin',
            'created_utc': '2024-01-15T11:45:00Z',
            'score': 12,
            'permalink': '/r/Austin/comments/sample1/comment1/',
            'parent_id': 'sample_1',
            'link_id': 'sample_1',
            'url': None,
            'num_comments': 0
        },
        {
            'id': 'sample_3',
            'type': 'submission',
            'author': 'testuser3',
            'title': 'Tech jobs in Silicon Hills',
            'content': 'Moving to Austin for tech work. What companies are hiring software engineers? Heard about Google, Apple, Oracle offices here. Any tips on the tech scene?',
            'subreddit': 'r/austincirclejerk',
            'created_utc': '2024-01-16T14:20:00Z',
            'score': 8,
            'permalink': '/r/austincirclejerk/comments/sample2/',
            'parent_id': None,
            'link_id': None,
            'url': None,
            'num_comments': 6
        }
    ]

    return sample_posts

def test_entity_extraction():
    """Test Ollama entity extraction."""
    print("Testing Ollama entity extraction...")

    test_text = "Franklin Barbecue is the best BBQ place in Austin Texas. Make sure to visit Barton Springs Pool afterwards."

    builder = OllamaGraphBuilder()
    entities = builder.extract_entities_with_ollama(test_text)

    print(f"Extracted {len(entities)} entities:")
    for entity in entities:
        print(f"  - {entity['entity']} ({entity['type']}, confidence: {entity['confidence']:.2f})")

    return entities

def test_embedding_generation():
    """Test embedding generation."""
    print("\nTesting embedding generation...")

    builder = OllamaGraphBuilder()
    test_text = "Austin Texas restaurants and BBQ"

    embedding = builder.generate_embedding(test_text)
    print(f"Generated embedding with shape: {embedding.shape}")
    print(f"First 5 values: {embedding[:5]}")

    return embedding

def test_sentiment_analysis():
    """Test sentiment analysis."""
    print("\nTesting sentiment analysis...")

    builder = OllamaGraphBuilder()

    test_texts = [
        "Franklin Barbecue is amazing! Best brisket ever.",
        "This restaurant was terrible, food was cold and service slow.",
        "The tech job market in Austin seems okay, nothing special."
    ]

    for text in test_texts:
        sentiment = builder.analyze_sentiment(text)
        print(f"Text: '{text[:50]}...' -> Sentiment: {sentiment:.2f}")

def test_full_ingestion():
    """Test full ingestion pipeline with sample data."""
    print("\nTesting full ingestion pipeline...")

    builder = OllamaGraphBuilder()

    # Create sample data (without using reddit_export folder)
    sample_posts = create_sample_data()

    print(f"Processing {len(sample_posts)} sample posts...")

    for i, post_data in enumerate(sample_posts, 1):
        print(f"Processing post {i}: {post_data['id']}")
        builder.process_post_ollama(post_data)

    print("Building knowledge graph...")
    builder.build_graph()

    print("Saving enhanced graph and embeddings...")
    builder.save_graph()

    print("Testing retrieval...")

    # Test different queries
    queries = [
        "Austin restaurants",
        "BBQ places",
        "Tech jobs Austin",
        "Franklin Barbecue"
    ]

    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        results = builder.retrieve_context(query, limit=3)

        for i, result in enumerate(results, 1):
            print(f"{i}. [{result.get('retrieval_method', 'unknown')}] Score: {result['relevance_score']:.3f}")
            if result.get('title'):
                print(f"   Title: {result['title']}")
            print(f"   Content: {result['content'][:100]}...")
            if result.get('entities'):
                entities = [e['entity'] for e in result['entities'] if isinstance(e, dict)]
                if entities:
                    print(f"   Entities: {', '.join(entities)}")
            print()

def main():
    print("Testing Enhanced Ollama GraphRAG System")
    print("=" * 50)

    # Test Ollama connection
    try:
        print("Testing Ollama connection...")
        response = ollama.generate(model='mistral', prompt='Hello', options={'num_predict': 1})
        print("✓ Ollama is running")
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        print("Please ensure Ollama is running with 'ollama serve' and the mistral model is available")
        return

    # Run individual tests
    test_entity_extraction()
    test_embedding_generation()
    test_sentiment_analysis()

    # Test full pipeline
    test_full_ingestion()

    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
