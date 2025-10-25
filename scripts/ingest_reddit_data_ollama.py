#!/usr/bin/env python3
"""
Enhanced ingestion script for Graph RAG using Ollama.
Supports both Reddit data and Chat History ingestion.
Uses local inference for better entity extraction and embeddings.
"""

import os
import sys
import sqlite3
import frontmatter
import networkx as nx
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
import re
import ollama
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class OllamaGraphBuilder:
    def __init__(self, data_dir: str = "reddit_export", model: str = "gemma-ob.gguf:latest"):
        # Get the directory where this script is located
        script_dir = Path(__file__).parent

        # For data_dir, if it's relative, resolve relative to script directory's parent (project root)
        if data_dir == "reddit_export":
            project_root = script_dir.parent
            self.data_dir = project_root / "reddit_export"
        else:
            self.data_dir = Path(data_dir)

        self.db_path = script_dir / "data" / "knowledge_graph_ollama.db"
        self.graph_file = script_dir / "data" / "knowledge_graph_ollama.pkl"
        self.embeddings_file = script_dir / "data" / "post_embeddings.npy"
        self.entity_embeddings_file = script_dir / "data" / "entity_embeddings.npy"

        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(exist_ok=True)

        self.model = model
        self.posts_data = []
        self.post_embeddings = {}
        self.entity_embeddings = {}

        # Initialize database
        self.init_database()

        # Initialize graph
        self.graph = nx.DiGraph()

    def init_database(self):
        """Initialize SQLite database with enhanced schema for Ollama-enhanced data."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                type TEXT,
                author TEXT,
                title TEXT,
                content TEXT,
                subreddit TEXT,
                created_utc TEXT,
                score INTEGER,
                permalink TEXT,
                parent_id TEXT,
                link_id TEXT,
                url TEXT,
                num_comments INTEGER,
                entities TEXT,  -- JSON array of extracted entities
                embedding BLOB, -- Numpy array of post embedding
                sentiment REAL   -- Sentiment analysis score
            )
        """)

        # Enhanced FTS table
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
                id UNINDEXED,
                title, content, author, subreddit, entities
            )
        """)

        # Entity relationship table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_relationships (
                entity1 TEXT,
                entity2 TEXT,
                relationship TEXT,
                confidence REAL,
                post_id TEXT,
                PRIMARY KEY (entity1, entity2, post_id)
            )
        """)

        self.conn.commit()

    def parse_markdown_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a markdown file with frontmatter."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        post = frontmatter.loads(content)

        return {
            'id': post.get('id', ''),
            'type': post.get('type', ''),
            'author': post.get('author', ''),
            'title': post.get('title', ''),
            'content': post.content.strip(),
            'subreddit': post.get('subreddit', ''),
            'created_utc': post.get('created_utc', ''),
            'score': post.get('score', 0),
            'permalink': post.get('permalink', ''),
            'parent_id': post.get('parent_id', ''),
            'link_id': post.get('link_id', ''),
            'url': post.get('url', ''),
            'num_comments': post.get('num_comments', 0)
        }

    def extract_entities_with_ollama(self, text: str) -> List[Dict[str, Any]]:
        """Use Ollama to extract meaningful entities and concepts from text."""
        if not text.strip():
            return []

        prompt = f"""Extract key entities, concepts, and important terms from this text. Focus on:
- People, places, organizations, events
- Main topics and concepts discussed
- Key terms that represent the core meaning
- Important locations, products, or services mentioned

Text: {text[:2000]}  # Limit text length for efficiency

Return as a JSON array of objects with format:
[{{"entity": "entity_name", "type": "person|place|organization|concept|other", "confidence": 0.8}}]

Be precise and only extract truly relevant entities."""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.1}
            )

            response_text = response['response'].strip()

            # Extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                entities = json.loads(json_str)

                # Validate and filter entities
                valid_entities = []
                for entity in entities:
                    if isinstance(entity, dict) and 'entity' in entity:
                        valid_entity = {
                            'entity': entity['entity'].strip(),
                            'type': entity.get('type', 'concept'),
                            'confidence': float(entity.get('confidence', 0.5))
                        }
                        if valid_entity['entity'] and len(valid_entity['entity']) > 1:
                            valid_entities.append(valid_entity)

                return valid_entities

        except Exception as e:
            print(f"Error extracting entities with Ollama: {e}")

        # Fallback to basic extraction
        return self.extract_entities_basic(text)

    def extract_entities_basic(self, text: str) -> List[Dict[str, Any]]:
        """Basic entity extraction as fallback."""
        entities = []

        # Reddit mentions (@user)
        for match in re.finditer(r'@(\w+)', text):
            entities.append({
                'entity': match.group(1),
                'type': 'person',
                'confidence': 0.8
            })

        # Subreddit mentions (r/subreddit)
        for match in re.finditer(r'r/(\w+)', text):
            entities.append({
                'entity': match.group(1),
                'type': 'organization',
                'confidence': 0.8
            })

        # Hashtags
        for match in re.finditer(r'#(\w+)', text):
            entities.append({
                'entity': match.group(1),
                'type': 'concept',
                'confidence': 0.6
            })

        # All caps words (potential emphasis)
        for match in re.finditer(r'\b[A-Z]{3,}\b', text):
            word = match.group()
            if len(word) >= 3 and word.isupper():
                entities.append({
                    'entity': word.lower(),
                    'type': 'concept',
                    'confidence': 0.4
                })

        return entities

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embeddings for text using Ollama."""
        try:
            # Use Ollama's embedding capability if available
            response = ollama.embeddings(model=self.model, prompt=text[:512])
            return np.array(response['embedding'])
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(768)  # Typical embedding dimension

    def analyze_sentiment(self, text: str) -> float:
        """Use Ollama to analyze sentiment of text."""
        prompt = f"""Analyze the sentiment of this text and return a score between -1 (very negative) and 1 (very positive).
Return only the number.

Text: {text[:1000]}"""

        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0.1}
            )

            score_text = response['response'].strip()
            # Extract the first number found
            match = re.search(r'-?\d*\.?\d+', score_text)
            if match:
                return float(match.group())
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")

        return 0.0  # Neutral fallback

    def extract_entity_relationships(self, entities: List[Dict], post_id: str):
        """Extract relationships between entities within a post."""
        entity_names = [e['entity'] for e in entities]

        # Simple co-occurrence relationships
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                if entity1['entity'] != entity2['entity']:
                    confidence = min(entity1['confidence'], entity2['confidence'])
                    self.conn.execute("""
                        INSERT OR REPLACE INTO entity_relationships
                        (entity1, entity2, relationship, confidence, post_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        entity1['entity'],
                        entity2['entity'],
                        'co_occurs_with',
                        confidence,
                        post_id
                    ))

        self.conn.commit()

    def build_graph(self):
        """Build the knowledge graph with enhanced semantic relationships."""
        print("Building enhanced knowledge graph...", file=sys.stderr)

        # Get all posts from database
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, content, author, subreddit, entities FROM posts")
        posts = cursor.fetchall()

        for post in posts:
            post_id = post[0]
            title = post[1] or ""
            content = post[2] or ""
            author = post[3]
            subreddit = post[4]
            entities_json = post[5] or "[]"

            try:
                entities = json.loads(entities_json)
            except:
                entities = []

            # Add post node with enhanced content
            self.graph.add_node(post_id, **{
                'type': 'post',
                'title': title,
                'content': content,
                'author': author,
                'subreddit': subreddit,
                'entities': [e['entity'] for e in entities]
            })

            # Add entity nodes and post-entity relationships
            for entity in entities:
                entity_name = entity['entity']
                entity_type = entity['type']
                confidence = entity['confidence']

                # Add entity node if not exists
                if not self.graph.has_node(entity_name):
                    self.graph.add_node(entity_name, **{
                        'type': entity_type,
                        'occurrences': 0,
                        'avg_confidence': 0.0
                    })

                # Update entity statistics
                if self.graph.has_node(entity_name):
                    curr_occurrences = self.graph.nodes[entity_name].get('occurrences', 0)
                    curr_avg_conf = self.graph.nodes[entity_name].get('avg_confidence', 0.0)
                    new_occurrences = curr_occurrences + 1
                    new_avg_conf = (curr_avg_conf * curr_occurrences + confidence) / new_occurrences

                    self.graph.nodes[entity_name]['occurrences'] = new_occurrences
                    self.graph.nodes[entity_name]['avg_confidence'] = new_avg_conf

                # Add post-entity relationship
                self.graph.add_edge(post_id, entity_name,
                                  relationship='mentions',
                                  confidence=confidence)

            # Add author and subreddit relationships
            if author:
                author_node_id = f"author_{author}"
                if not self.graph.has_node(author_node_id):
                    self.graph.add_node(author_node_id,
                                      type='author',
                                      name=author,
                                      post_count=0)
                self.graph.add_edge(author_node_id, post_id, relationship='authored')

            if subreddit:
                subreddit_node_id = f"subreddit_{subreddit}"
                if not self.graph.has_node(subreddit_node_id):
                    self.graph.add_node(subreddit_node_id,
                                      type='subreddit',
                                      name=subreddit,
                                      post_count=0)
                self.graph.add_edge(subreddit_node_id, post_id, relationship='belongs_to')

    def save_graph(self):
        """Save the graph to a file."""
        import pickle
        with open(self.graph_file, 'wb') as f:
            pickle.dump(self.graph, f)

        # Save embeddings
        np.save(self.embeddings_file, self.post_embeddings)
        if self.entity_embeddings:
            np.save(self.entity_embeddings_file, self.entity_embeddings)

    def load_graph(self) -> bool:
        """Load the graph from file if it exists."""
        import pickle
        if self.graph_file.exists():
            with open(self.graph_file, 'rb') as f:
                self.graph = pickle.load(f)

            # Load embeddings
            if self.embeddings_file.exists():
                loaded = np.load(self.embeddings_file, allow_pickle=True)
                self.post_embeddings = loaded.item() if loaded.ndim == 0 else loaded
            if self.entity_embeddings_file.exists():
                loaded_entity = np.load(self.entity_embeddings_file, allow_pickle=True)
                self.entity_embeddings = loaded_entity.item() if loaded_entity.ndim == 0 else loaded_entity

            return True
        return False

    def ingest_data(self):
        """Main ingestion function with Ollama-enhanced processing."""
        print("Starting enhanced Reddit data ingestion with Ollama...")

        # Check if we already have data
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts")
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"Enhanced database already has {count} posts. Use existing data.")
            # Don't force rebuild, use existing data

        processed_count = 0

        # Process all markdown files in the data directory
        print(f"Looking for data in: {self.data_dir}")
        print(f"Data directory exists: {self.data_dir.exists()}")

        if self.data_dir.exists():
            # Look for all .md files in reddit_export
            md_files = list(self.data_dir.glob("*.md"))
            print(f"Found {len(md_files)} markdown files")
            if md_files:
                print(f"First few files: {[f.name for f in md_files[:3]]}")

            # Process all files (or limit for testing speed)
            files_to_process = md_files[:50]  # Process first 50 files for reasonable testing

            for file_path in files_to_process:
                try:
                    post_data = self.parse_markdown_file(file_path)
                    self.process_post_ollama(post_data)
                    processed_count += 1
                    print(f"Processed file {processed_count}/{len(files_to_process)}: {file_path.name}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
        else:
            print("Data directory not found!")

        print(f"Building enhanced knowledge graph from {processed_count} posts...")
        self.build_graph()

        print("Saving enhanced graph and embeddings...")
        self.save_graph()

        print("Enhanced ingestion complete!")

    def ingest_chat_history(self, chat_sessions: List[Dict[str, Any]]):
        """Ingest chat history from Next.js frontend sessions."""
        import sys
        print("Starting chat history ingestion with Ollama...", file=sys.stderr)

        # Clear existing chat data (optional - could merge instead)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM posts WHERE type = 'chat_message'")
        cursor.execute("DELETE FROM entity_relationships WHERE post_id LIKE 'chat_%'")
        self.conn.commit()

        processed_count = 0

        for session in chat_sessions:
            session_id = session.get('id', '')
            session_title = session.get('title', 'Chat Session')
            messages = session.get('messages', [])

            print(f"Processing session: {session_id} - {len(messages)} messages", file=sys.stderr)

            # Debug: Print all messages to understand the structure
            for idx, msg in enumerate(messages):
                print(f"  Message {idx}: role={msg.get('role')}, content={msg.get('content', '')[:50]}...", file=sys.stderr)

            # Process all messages, not just pairs
            for i, message in enumerate(messages):
                # Process any message that has content
                if message.get('content', '').strip():
                    role = message.get('role', 'unknown')
                    conversation_id = f"chat_{session_id}_{i}"

                    # Format content based on role
                    if role == 'user':
                        full_content = f"User: {message['content']}"
                    elif role == 'assistant':
                        full_content = f"Assistant: {message['content']}"
                    else:
                        full_content = f"{role.capitalize()}: {message['content']}"

                    # Create post data structure for each chat message
                    chat_data = {
                        'id': conversation_id,
                        'type': 'chat_message',
                        'author': role,  # Use the actual role as author
                        'title': f"Chat: {session_title} - {role.capitalize()}",
                        'content': full_content,
                        'subreddit': 'chat_history',
                        'created_utc': datetime.now(timezone.utc).isoformat(),
                        'score': 1,
                        'permalink': '',
                        'parent_id': '',
                        'link_id': '',
                        'url': '',
                        'num_comments': 0,
                        'session_id': session_id,
                        'session_title': session_title
                    }

                    try:
                        self.process_post_ollama(chat_data)
                        processed_count += 1
                        print(f"Processed message {processed_count}: {conversation_id} ({role})", file=sys.stderr)
                    except Exception as e:
                        print(f"Error processing message {conversation_id}: {e}", file=sys.stderr)
                        continue
                else:
                    print(f"Skipping empty message at index {i}", file=sys.stderr)

        print(f"Building knowledge graph from {processed_count} chat conversations...", file=sys.stderr)
        self.build_graph()

        print("Saving enhanced graph and embeddings...", file=sys.stderr)
        self.save_graph()

        print("Chat history ingestion complete!", file=sys.stderr)
        return processed_count

    def process_post_ollama(self, post_data: Dict[str, Any]):
        """Process a single post with Ollama enhancement."""
        # Extract entities using Ollama
        full_text = f"{post_data.get('title', '')} {post_data['content']}".strip()
        entities = self.extract_entities_with_ollama(full_text)

        # Generate embedding
        embedding = self.generate_embedding(full_text)
        embedding_blob = embedding.tobytes()

        # Analyze sentiment
        sentiment = self.analyze_sentiment(full_text)

        # Store entities as JSON
        entities_json = json.dumps(entities)

        # Insert into database
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO posts
            (id, type, author, title, content, subreddit, created_utc, score, permalink,
             parent_id, link_id, url, num_comments, entities, embedding, sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_data['id'],
            post_data['type'],
            post_data['author'],
            post_data['title'],
            post_data['content'],
            post_data['subreddit'],
            post_data['created_utc'],
            post_data['score'],
            post_data['permalink'],
            post_data['parent_id'],
            post_data['link_id'],
            post_data['url'],
            post_data['num_comments'],
            entities_json,
            embedding_blob,
            sentiment
        ))

        # Insert into FTS table (include entities for search)
        entities_text = " ".join([e['entity'] for e in entities])
        cursor.execute("""
            INSERT OR REPLACE INTO posts_fts
            (id, title, content, author, subreddit, entities)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            post_data['id'],
            post_data.get('title', ''),
            post_data['content'],
            post_data['author'],
            post_data['subreddit'],
            entities_text
        ))

        # Store embedding in memory
        self.post_embeddings[post_data['id']] = embedding

        # Extract and store entity relationships
        self.extract_entity_relationships(entities, post_data['id'])

        self.conn.commit()

    def retrieve_context(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Enhanced retrieval using embeddings and semantic search."""
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)

        # Calculate semantic similarity with all posts
        post_ids = list(self.post_embeddings.keys())
        semantic_results = []  # Initialize outside the if block
        if post_ids:
            post_embeddings_matrix = np.array([self.post_embeddings[pid] for pid in post_ids])
            similarities = cosine_similarity([query_embedding], post_embeddings_matrix)[0]

            # Get top similar posts by embedding similarity
            top_embedding_indices = np.argsort(similarities)[::-1][:limit*2]

            for idx in top_embedding_indices[:limit]:
                post_id = post_ids[idx]
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT title, content, author, subreddit, score, entities, sentiment
                    FROM posts WHERE id = ?
                """, (post_id,))

                row = cursor.fetchone()
                if row:
                    try:
                        entities = json.loads(row[5] or "[]")
                    except:
                        entities = []

                    semantic_results.append({
                        'id': post_id,
                        'title': row[0],
                        'content': row[1],
                        'author': row[2],
                        'subreddit': row[3],
                        'score': row[4],
                        'entities': entities,
                        'sentiment': row[6],
                        'relevance_score': float(similarities[idx]),
                        'retrieval_method': 'semantic_similarity'
                    })

        # Also get FTS results for comparison
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT posts.id, posts.title, posts.content, posts.author, posts.subreddit,
                   posts.score, posts.entities, posts.sentiment
            FROM posts_fts
            JOIN posts ON posts_fts.id = posts.id
            WHERE posts_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit // 2))

        fts_results = []
        for row in cursor.fetchall():
            try:
                entities = json.loads(row[6] or "[]")
            except:
                entities = []

            fts_results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'author': row[3],
                'subreddit': row[4],
                'score': row[5],
                'entities': entities,
                'sentiment': row[7],
                'relevance_score': 0.8,  # FTS is also relevant
                'retrieval_method': 'keyword_search'
            })

        # Combine and deduplicate results
        all_results = (semantic_results or []) + fts_results
        seen_ids = set()
        unique_results = []

        for result in all_results:
            if result['id'] not in seen_ids and len(unique_results) < limit:
                seen_ids.add(result['id'])
                unique_results.append(result)

        # Sort by relevance score
        unique_results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return unique_results[:limit]

def main():
    builder = OllamaGraphBuilder()

    # Test Ollama connection
    try:
        print("Testing Ollama connection...")
        response = ollama.generate(model='mistral', prompt='Hello', options={'num_predict': 1})
        print("✓ Ollama is running")
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        print("Please ensure Ollama is running with 'ollama serve' and the mistral model is available")
        return

    builder.ingest_data()

    # Test retrieval
    print("\nTesting enhanced retrieval...")
    results = builder.retrieve_context("Austin Texas restaurants", limit=3)
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result.get('retrieval_method', 'unknown')} - Score: {result['relevance_score']:.3f}")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Content: {result['content'][:150]}...")
        if result.get('entities'):
            print(f"Entities: {[e['entity'] for e in result['entities']]}")

if __name__ == "__main__":
    main()
