#!/usr/bin/env python3
"""
Reddit data ingestion script for Graph RAG.
Processes markdown files from reddit_export and builds a knowledge graph.
"""

import os
import sqlite3
import frontmatter
import networkx as nx
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
import re

class RedditGraphBuilder:
    def __init__(self, data_dir: str = "reddit_export"):
        self.data_dir = Path(data_dir)
        self.db_path = Path("data/knowledge_graph.db")
        self.graph_file = Path("data/knowledge_graph.pkl")

        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(exist_ok=True)

        # Initialize database
        self.init_database()

        # Initialize graph
        self.graph = nx.DiGraph()

    def init_database(self):
        """Initialize SQLite database with schema for Reddit data."""
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
                num_comments INTEGER
            )
        """)

        # Create full-text search table
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
                id UNINDEXED,
                title, content, author, subreddit
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

    def extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction - can be enhanced with NLP later."""
        entities = []

        # Reddit mentions (@user)
        entities.extend(re.findall(r'@(\w+)', text))

        # Subreddit mentions (r/subreddit)
        entities.extend(re.findall(r'r/(\w+)', text))

        # URLs
        entities.extend(re.findall(r'https?://[^\s]+', text))

        # Hashtags
        entities.extend(re.findall(r'#(\w+)', text))

        # All caps words (potential emphasis)
        entities.extend([word for word in re.findall(r'\b[A-Z]{2,}\b', text) if len(word) > 3])

        return list(set(entities))

    def build_graph(self):
        """Build the knowledge graph from Reddit data."""
        # Get all posts from database
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM posts")
        posts = cursor.fetchall()

        # Create nodes and edges
        post_nodes = {}
        entity_nodes = {}

        for post in posts:
            post_id = post[0]
            title = post[3] or ""
            content = post[4] or ""
            author = post[2]
            subreddit = post[5]

            # Add post node
            post_nodes[post_id] = {
                'id': post_id,
                'type': 'post',
                'title': title,
                'content': content,
                'author': author,
                'subreddit': subreddit,
                'score': post[7]
            }

            # Extract entities and add entity nodes
            full_text = f"{title} {content}"
            entities = self.extract_entities(full_text)

            for entity in entities:
                if entity not in entity_nodes:
                    entity_nodes[entity] = {
                        'id': entity,
                        'type': 'entity',
                        'name': entity,
                        'occurrences': 0
                    }
                entity_nodes[entity]['occurrences'] += 1

                # Create edge between post and entity
                self.graph.add_edge(post_id, entity, relationship='mentions')

            # Add author and subreddit nodes
            if author:
                author_node_id = f"author_{author}"
                if author_node_id not in self.graph:
                    self.graph.add_node(author_node_id,
                                      type='author',
                                      name=author,
                                      post_count=0)
                self.graph.add_edge(author_node_id, post_id, relationship='authored')

            if subreddit:
                subreddit_node_id = f"subreddit_{subreddit}"
                if subreddit_node_id not in self.graph:
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

    def load_graph(self) -> bool:
        """Load the graph from file if it exists."""
        import pickle
        if self.graph_file.exists():
            with open(self.graph_file, 'rb') as f:
                self.graph = pickle.load(f)
            return True
        return False

    def ingest_data(self):
        """Main ingestion function."""
        print("Starting Reddit data ingestion...")

        # Check if we already have data
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts")
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"Database already has {count} posts. Skipping ingestion.")
            if self.load_graph():
                print("Graph loaded from cache.")
                return

        # Process comments
        comments_dir = self.data_dir / "comments"
        if comments_dir.exists():
            print("Processing comments...")
            for file_path in comments_dir.glob("*.md"):
                try:
                    post_data = self.parse_markdown_file(file_path)
                    self.insert_post(post_data)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

        # Process submissions
        submissions_dir = self.data_dir / "submissions"
        if submissions_dir.exists():
            print("Processing submissions...")
            for file_path in submissions_dir.glob("*.md"):
                try:
                    post_data = self.parse_markdown_file(file_path)
                    self.insert_post(post_data)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

        print("Building knowledge graph...")
        self.build_graph()

        print("Saving graph...")
        self.save_graph()

        print("Ingestion complete!")

    def insert_post(self, post_data: Dict[str, Any]):
        """Insert a post into the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO posts
            (id, type, author, title, content, subreddit, created_utc, score, permalink,
             parent_id, link_id, url, num_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            post_data['num_comments']
        ))

        # Insert into FTS table
        cursor.execute("""
            INSERT OR REPLACE INTO posts_fts
            (id, title, content, author, subreddit)
            VALUES (?, ?, ?, ?, ?)
        """, (
            post_data['id'],
            post_data.get('title', ''),
            post_data['content'],
            post_data['author'],
            post_data['subreddit']
        ))

        self.conn.commit()

    def search_similar_content(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for semantically similar content."""
        cursor = self.conn.cursor()

        # Use FTS for initial search
        cursor.execute("""
            SELECT posts_fts.id, posts.title, posts.content, posts.author, posts.subreddit, posts.score, posts.permalink
            FROM posts_fts
            JOIN posts ON posts_fts.id = posts.id
            WHERE posts_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'author': row[3],
                'subreddit': row[4],
                'score': row[5],
                'permalink': row[6],
                'relevance_score': 1.0  # For now, using FTS rank
            })

        return results

    def get_connected_content(self, post_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Get content connected in the graph."""
        if not self.graph.has_node(post_id):
            return []

        connected_posts = set()
        visited = set()

        def traverse(node, depth):
            if depth > max_depth or node in visited:
                return
            visited.add(node)

            for neighbor in self.graph.neighbors(node):
                if neighbor in self.graph and self.graph.nodes[neighbor].get('type') == 'post':
                    connected_posts.add(neighbor)
                    traverse(neighbor, depth + 1)

        traverse(post_id, 0)

        # Get post details
        if connected_posts:
            placeholders = ','.join(['?'] * len(connected_posts))
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT id, title, content, author, subreddit, score
                FROM posts
                WHERE id IN ({placeholders})
            """, list(connected_posts))

            return [{
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'author': row[3],
                'subreddit': row[4],
                'score': row[5],
                'relevance_score': 0.8  # Lower relevance for connected content
            } for row in cursor.fetchall()]

        return []

    def retrieve_context(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve relevant context for RAG."""
        # Get direct matches
        direct_matches = self.search_similar_content(query, limit // 2)

        # Get connected content from top matches
        connected_content = []
        for match in direct_matches[:2]:  # Get connections from top 2 results
            connected = self.get_connected_content(match['id'])
            connected_content.extend(connected)

        # Combine and deduplicate
        all_results = direct_matches + connected_content
        seen_ids = set()
        unique_results = []

        for result in all_results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)

        # Sort by relevance score and return top results
        unique_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return unique_results[:limit]

def main():
    builder = RedditGraphBuilder()
    builder.ingest_data()

    # Test retrieval
    print("\nTesting retrieval...")
    results = builder.retrieve_context("Austin Texas weather")
    for result in results[:3]:
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Content: {result['content'][:100]}...")
        print(f"Score: {result['relevance_score']}")
        print("---")

if __name__ == "__main__":
    main()
