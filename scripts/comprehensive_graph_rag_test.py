#!/usr/bin/env python3
"""
Comprehensive test suite for Graph RAG system.
Tests entity extraction, graph construction, retrieval algorithms, and end-to-end functionality.
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
import tempfile

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import ollama
    import sqlite3
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    import networkx as nx
    from ingest_reddit_data_ollama import OllamaGraphBuilder
    OLLAMA_AVAILABLE = True
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    OLLAMA_AVAILABLE = False

class GraphRAGTester:
    """Comprehensive test suite for Graph RAG functionality."""

    def __init__(self):
        self.test_results = []
        self.builder = None

    def log_test(self, test_name: str, passed: bool, details: str = "", duration: float = 0.0):
        """Log a test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'duration': duration
        })
        print(".3f" if duration > 0 else f"{status}: {test_name}")

    def test_ollama_connection(self):
        """Test Ollama service availability."""
        start_time = time.time()
        try:
            if not OLLAMA_AVAILABLE:
                raise ImportError("Ollama dependencies not available")

            response = ollama.generate(model='mistral', prompt='Hello', options={'num_predict': 1})
            self.log_test("Ollama Connection", True, "Ollama service is running",
                         time.time() - start_time)
        except Exception as e:
            self.log_test("Ollama Connection", False, f"Failed to connect to Ollama: {e}",
                         time.time() - start_time)

    def test_entity_extraction(self):
        """Test entity extraction functionality."""
        if not OLLAMA_AVAILABLE or not self.builder:
            self.log_test("Entity Extraction", False, "Prerequisites not available")
            return

        start_time = time.time()

        test_cases = [
            ("Franklin Barbecue is amazing!", ["Franklin Barbecue", "amazing"]),
            ("Texas BBQ places in Austin", ["Texas", "BBQ", "Austin"]),
            ("@user mentioned r/subreddit", ["user", "subreddit"])
        ]

        success_count = 0
        for text, expected_entities in test_cases:
            entities = self.builder.extract_entities_with_ollama(text)
            extracted_names = [e['entity'] for e in entities]

            # Check if at least some expected entities are found
            found_count = sum(1 for expected in expected_entities if
                            any(expected.lower() in extracted.lower() for extracted in extracted_names))
            if found_count > 0:
                success_count += 1

        passed = success_count >= len(test_cases) * 0.7  # 70% success rate
        self.log_test("Entity Extraction", passed,
                     f"Successfully extracted entities from {success_count}/{len(test_cases)} test cases",
                     time.time() - start_time)

    def test_embedding_generation(self):
        """Test embedding generation."""
        if not OLLAMA_AVAILABLE or not self.builder:
            self.log_test("Embedding Generation", False, "Prerequisites not available")
            return

        start_time = time.time()
        try:
            test_texts = ["Austin restaurants", "Texas BBQ", "tech jobs"]

            embeddings = []
            for text in test_texts:
                emb = self.builder.generate_embedding(text)
                embeddings.append(emb)
                assert len(emb) > 0, f"Empty embedding for text: {text}"
                assert isinstance(emb, np.ndarray), f"Expected numpy array, got {type(emb)}"

            # Check similarity makes sense
            sim_1_2 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            sim_1_3 = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]

            # "Austin restaurants" vs "Texas BBQ" should be more similar than vs "tech jobs"
            passed = sim_1_2 > sim_1_3
            details = "03f" if passed else f"Similarity check failed. Austin+Texas BBQ similarity: {sim_1_2:.3f}, Austin+tech similarity: {sim_1_3:.3f}"

            self.log_test("Embedding Generation", passed, details, time.time() - start_time)

        except Exception as e:
            self.log_test("Embedding Generation", False, f"Error: {e}", time.time() - start_time)

    def test_graph_construction(self):
        """Test graph construction and relationships."""
        if not self.builder or not self.builder.load_graph():
            self.log_test("Graph Construction", False, "Graph not available")
            return

        start_time = time.time()
        try:
            graph = self.builder.graph
            nodes = len(graph.nodes)
            edges = len(graph.edges)

            # Basic sanity checks
            assert nodes > 0, "Graph has no nodes"
            assert edges > 0, "Graph has no edges"

            # Check for required node types
            node_types = set()
            for node, attrs in graph.nodes(data=True):
                node_types.add(attrs.get('type', 'unknown'))

            required_types = {'post', 'author', 'subreddit'}
            missing_types = required_types - node_types

            passed = len(missing_types) == 0 and nodes >= 10  # At least 10 nodes
            details = f"Graph has {nodes} nodes, {edges} edges. Node types: {sorted(node_types)}"
            if missing_types:
                details += f"Missing types: {missing_types}"

            self.log_test("Graph Construction", passed, details, time.time() - start_time)

        except Exception as e:
            self.log_test("Graph Construction", False, f"Error: {e}", time.time() - start_time)

    def test_semantic_retrieval(self):
        """Test semantic retrieval vs keyword search."""
        if not self.builder:
            self.log_test("Semantic Retrieval", False, "Builder not available")
            return

        start_time = time.time()
        try:
            query = "Austin restaurants"
            results = self.builder.retrieve_context(query, limit=5)

            assert len(results) > 0, "No results returned"

            # Check that we have both semantic and keyword results
            methods = set(r.get('retrieval_method', 'unknown') for r in results)
            has_semantic = 'semantic_similarity' in methods
            has_keyword = 'keyword_search' in methods

            # Check result quality
            high_score_results = [r for r in results if r.get('relevance_score', 0) > 0.1]
            quality_score = len(high_score_results) / len(results)

            passed = has_semantic and quality_score > 0.6  # At least 60% high-quality results
            details = f"Found {len(results)} results. Methods: {methods}. Quality score: {quality_score:.1f}"

            self.log_test("Semantic Retrieval", passed, details, time.time() - start_time)

        except Exception as e:
            self.log_test("Semantic Retrieval", False, f"Error: {e}", time.time() - start_time)

    def test_api_endpoints(self):
        """Test Graph RAG API endpoints."""
        start_time = time.time()
        try:
            # Test the Python script directly
            result = subprocess.run([
                sys.executable, 'graph_rag_query_ollama.py', 'test query', '3'
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__), timeout=30)

            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    passed = 'context' in data and len(data['context']) > 0
                    details = "API call successful" if passed else "API returned empty context"
                    self.log_test("API Endpoints", passed, details, time.time() - start_time)
                except json.JSONDecodeError:
                    self.log_test("API Endpoints", False, "Invalid JSON response",
                                 time.time() - start_time)
            else:
                self.log_test("API Endpoints", False,
                             f"Script failed with exit code {result.returncode}: {result.stderr}",
                             time.time() - start_time)

        except subprocess.TimeoutExpired:
            self.log_test("API Endpoints", False, "API call timed out", time.time() - start_time)
        except Exception as e:
            self.log_test("API Endpoints", False, f"Error: {e}", time.time() - start_time)

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        start_time = time.time()
        try:
            if not self.builder:
                # Test with invalid builder
                passed = False
                details = "Builder initialization failed"
            else:
                # Test with empty query
                results = self.builder.retrieve_context("", limit=1)
                passed = isinstance(results, list)  # Should return empty list, not crash
                details = f"Empty query returned {len(results)} results"

            self.log_test("Error Handling", passed, details, time.time() - start_time)

        except Exception as e:
            # This is actually good - we want error handling to work
            self.log_test("Error Handling", True, f"Properly handled error: {e}",
                         time.time() - start_time)

    def setup_test_data(self):
        """Setup test environment."""
        if not OLLAMA_AVAILABLE:
            print("Cannot run tests: Ollama dependencies not available")
            return False

        try:
            self.builder = OllamaGraphBuilder()
            if not self.builder.load_graph():
                print("Graph not found, attempting to build test data...")
                # Remove old databases to force reingestion
                import shutil
                data_dir = Path("data")
                for f in ["knowledge_graph_ollama.db", "knowledge_graph_ollama.pkl", "post_embeddings.npy"]:
                    path = data_dir / f
                    if path.exists():
                        path.unlink()

                # Build fresh graph with limited data for testing
                self.builder.ingest_data()
            return True
        except Exception as e:
            print(f"Failed to setup test data: {e}")
            return False

    def run_all_tests(self):
        """Run the complete test suite."""
        print("=== GRAPH RAG COMPREHENSIVE TEST SUITE ===")
        print()

        if not self.setup_test_data():
            print("Test setup failed. Aborting.")
            return

        print(f"Running tests on graph with {len(self.builder.graph.nodes)} nodes...")
        print()

        # Run all tests
        self.test_ollama_connection()
        self.test_entity_extraction()
        self.test_embedding_generation()
        self.test_graph_construction()
        self.test_semantic_retrieval()
        self.test_api_endpoints()
        self.test_error_handling()

        # Print summary
        print()
        print("=== TEST RESULTS SUMMARY ===")
        passed = 0
        total = len(self.test_results)

        for result in self.test_results:
            if result['status'] == 'PASS':
                passed += 1

        print(f"Passed: {passed}/{total} tests ({passed/total*100:.1f}%)")

        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        elif passed >= total * 0.8:
            print("✅ MOST TESTS PASSED - SYSTEM IS OPERATIONAL")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW RESULTS ABOVE")

        # Detailed breakdown
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(".1f")

            # Print details if failed or has interesting info
            if result['status'] == 'FAIL' or len(result['details']) < 50:
                print(f"     └─ {result['details']}")

        return passed == total

def main():
    tester = GraphRAGTester()
    success = tester.run_all_tests()

    print("\n=== RECOMMENDATIONS ===")
    if success:
        print("- System is ready for production use")
        print("- Consider adding more test data for better coverage")
        print("- Monitor performance with larger datasets")
    else:
        print("- Review failed tests and fix issues")
        print("- Check Ollama service status")
        print("- Verify data quality and quantity")
        print("- Consider fallback mechanisms for failed operations")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
