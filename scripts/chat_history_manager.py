#!/usr/bin/env python3
"""
Chat History Manager for JSON-based RAG persistence.
Manages chat conversation storage, retrieval, and RAG querying.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
import ollama
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import hashlib

class ChatHistoryManager:
    def __init__(self, data_dir: str = "data/chat_history"):
        # Get the directory where this script is located
        script_dir = Path(__file__).parent

        # Set up data directories
        self.data_dir = script_dir / data_dir
        self.conversations_dir = self.data_dir / "conversations"
        self.embeddings_dir = self.data_dir / "embeddings"

        # Create directories if they don't exist
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

        self.default_model = 'mistral-small3.2:latest'

    def _get_conversation_path(self, session_id: str) -> Path:
        """Get the file path for a conversation."""
        return self.conversations_dir / f"{session_id}.json"

    def _get_embedding_path(self, session_id: str) -> Path:
        """Get the file path for conversation embeddings."""
        return self.embeddings_dir / f"{session_id}_embeddings.npy"

    def _hash_content(self, content: str) -> str:
        """Generate a hash for content to detect changes."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def save_conversation(self, session: Dict[str, Any]) -> bool:
        """Save a chat conversation as JSON."""
        try:
            session_id = session.get('id', '')
            if not session_id:
                return False

            # Add/update timestamps
            now = datetime.now(timezone.utc).isoformat()
            session['updatedAt'] = now
            if 'createdAt' not in session:
                session['createdAt'] = now

            # Save to JSON file
            conversation_path = self._get_conversation_path(session_id)
            with open(conversation_path, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)

            print(f"Saved conversation {session_id} with {len(session.get('messages', []))} messages", file=sys.stderr)
            return True

        except Exception as e:
            print(f"Error saving conversation: {e}", file=sys.stderr)
            return False

    def load_conversation(self, session_id: str) -> Dict[str, Any]:
        """Load a chat conversation from JSON."""
        try:
            conversation_path = self._get_conversation_path(session_id)
            if not conversation_path.exists():
                return {}

            with open(conversation_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading conversation {session_id}: {e}", file=sys.stderr)
            return {}

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations with basic metadata."""
        conversations = []

        try:
            for json_file in self.conversations_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        session = json.load(f)

                    # Get basic info
                    conversations.append({
                        'id': session.get('id', ''),
                        'title': session.get('title', 'Untitled'),
                        'messages_count': len(session.get('messages', [])),
                        'model': session.get('model', ''),
                        'createdAt': session.get('createdAt', ''),
                        'updatedAt': session.get('updatedAt', '')
                    })

                except Exception as e:
                    print(f"Error reading {json_file}: {e}", file=sys.stderr)
                    continue

        except Exception as e:
            print(f"Error listing conversations: {e}", file=sys.stderr)

        # Sort by creation date (newest first)
        conversations.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        return conversations

    def generate_embeddings_for_conversation(self, session_id: str, model: str = None) -> bool:
        """Generate embeddings for all messages in a conversation."""
        try:
            conversation = self.load_conversation(session_id)
            if not conversation or 'messages' not in conversation:
                return False

            model = model or conversation.get('model', self.default_model)
            messages = conversation['messages']

            embeddings_data = {
                'session_id': session_id,
                'model': model,
                'message_embeddings': [],
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            # Generate embeddings for each message
            for i, message in enumerate(messages):
                content = message.get('content', '').strip()
                if content:
                    try:
                        # Create a unique identifier for each message
                        message_id = f"{session_id}_{i}"

                        # Generate embedding using nomic-embed-text for consistency
                        try:
                            response = ollama.embeddings(model='nomic-embed-text:latest', prompt=content[:512])
                            embedding = np.array(response['embedding'])
                        except Exception:
                            # Fallback to original model if embeddings don't work
                            response = ollama.embeddings(model=model, prompt=content[:512])
                            embedding = np.array(response['embedding'])

                        # Store message data
                        embeddings_data['message_embeddings'].append({
                            'message_index': i,
                            'message_id': message_id,
                            'role': message.get('role', 'unknown'),
                            'content': content,
                            'content_hash': self._hash_content(content),
                            'embedding': embedding.tolist()
                        })

                    except Exception as e:
                        print(f"Error generating embedding for message {i}: {e}", file=sys.stderr)
                        continue

            # Save embeddings
            embedding_path = self._get_embedding_path(session_id)
            np.save(embedding_path, embeddings_data)

            print(f"Generated embeddings for conversation {session_id} with {len(embeddings_data['message_embeddings'])} messages", file=sys.stderr)
            return True

        except Exception as e:
            print(f"Error generating embeddings for conversation {session_id}: {e}", file=sys.stderr)
            return False

    def load_embeddings_for_conversation(self, session_id: str) -> Dict[str, Any]:
        """Load pre-computed embeddings for a conversation."""
        try:
            embedding_path = self._get_embedding_path(session_id)
            if not embedding_path.exists():
                return {}

            # Load numpy array and convert to dict
            embeddings_data = np.load(embedding_path, allow_pickle=True).item()
            return embeddings_data

        except Exception as e:
            print(f"Error loading embeddings for {session_id}: {e}", file=sys.stderr)
            return {}

    def retrieve_relevant_messages(self, query: str, limit: int = 10, model: str = None) -> List[Dict[str, Any]]:
        """Retrieve relevant chat messages using semantic search."""
        try:
            model = model or self.default_model

            # Generate embedding for the query using nomic-embed-text
            try:
                response = ollama.embeddings(model='nomic-embed-text:latest', prompt=query[:512])
                query_embedding = np.array(response['embedding'])
            except Exception:
                # Fallback to original model if embeddings don't work
                response = ollama.embeddings(model=model, prompt=query[:512])
                query_embedding = np.array(response['embedding'])

            all_results = []

            # Get all conversations
            conversations = self.list_conversations()

            for conv_info in conversations:
                session_id = conv_info['id']

                # Load embeddings for this conversation
                embeddings_data = self.load_embeddings_for_conversation(session_id)
                if not embeddings_data:
                    continue

                # Get conversation details
                conversation = self.load_conversation(session_id)
                if not conversation:
                    continue

                # Extract embeddings matrix
                message_embeddings = embeddings_data.get('message_embeddings', [])
                if not message_embeddings:
                    continue

                # Convert to numpy array for similarity calculation
                embedding_matrix = np.array([msg['embedding'] for msg in message_embeddings])

                # Calculate similarities
                similarities = cosine_similarity([query_embedding], embedding_matrix)[0]

                # Get top results from this conversation
                top_indices = np.argsort(similarities)[::-1][:limit]

                for idx in top_indices:
                    if idx < len(message_embeddings):
                        message_data = message_embeddings[idx]
                        similarity_score = float(similarities[idx])

                        # Only include results above a threshold
                        if similarity_score > 0.1:  # Adjustable similarity threshold
                            result = {
                                'session_id': session_id,
                                'session_title': conv_info['title'],
                                'message_index': message_data['message_index'],
                                'message_id': message_data['message_id'],
                                'role': message_data['role'],
                                'content': message_data['content'],
                                'relevance_score': similarity_score,
                                'model': embeddings_data.get('model', ''),
                                'created_at': embeddings_data.get('created_at', ''),
                                'conversation_created': conv_info.get('createdAt', '')
                            }
                            all_results.append(result)

            # Sort all results by relevance score
            all_results.sort(key=lambda x: x['relevance_score'], reverse=True)

            # Return top results
            return all_results[:limit]

        except Exception as e:
            print(f"Error retrieving relevant messages: {e}", file=sys.stderr)
            return []

    def ingest_conversations(self, chat_sessions: List[Dict[str, Any]]) -> int:
        """Ingest multiple chat conversations."""
        processed_count = 0

        for session in chat_sessions:
            if self.save_conversation(session):
                # Generate embeddings for the conversation
                session_id = session.get('id', '')
                if session_id:
                    self.generate_embeddings_for_conversation(session_id, session.get('model'))
                processed_count += 1

        return processed_count

    def delete_conversation(self, session_id: str) -> bool:
        """Delete a conversation and its embeddings."""
        try:
            # Remove JSON file
            json_path = self._get_conversation_path(session_id)
            if json_path.exists():
                json_path.unlink()

            # Remove embeddings
            embedding_path = self._get_embedding_path(session_id)
            if embedding_path.exists():
                embedding_path.unlink()

            print(f"Deleted conversation {session_id}", file=sys.stderr)
            return True

        except Exception as e:
            print(f"Error deleting conversation {session_id}: {e}", file=sys.stderr)
            return False

def main():
    """Command-line interface for chat history management."""
    if len(sys.argv) < 2:
        print("Usage: python chat_history_manager.py <command> [args...]")
        print("Commands:")
        print("  list                    - List all conversations")
        print("  save <session_json>     - Save a conversation from JSON string")
        print("  load <session_id>       - Load a conversation")
        print("  search <query> [limit]  - Search for relevant messages")
        print("  delete <session_id>     - Delete a conversation")
        print("  ingest <file_path>      - Ingest conversations from JSON file")
        return

    manager = ChatHistoryManager()
    command = sys.argv[1]

    try:
        if command == 'list':
            conversations = manager.list_conversations()
            print(json.dumps(conversations, indent=2))

        elif command == 'save':
            if len(sys.argv) < 3:
                print("Error: session JSON required")
                return

            session_json = sys.argv[2]
            session = json.loads(session_json)
            success = manager.save_conversation(session)

            if success:
                session_id = session.get('id', '')
                manager.generate_embeddings_for_conversation(session_id, session.get('model'))
                print(f"Successfully saved conversation {session_id}")
            else:
                print("Failed to save conversation")

        elif command == 'load':
            if len(sys.argv) < 3:
                print("Error: session_id required")
                return

            session_id = sys.argv[2]
            conversation = manager.load_conversation(session_id)
            print(json.dumps(conversation, indent=2))

        elif command == 'search':
            if len(sys.argv) < 3:
                print("Error: query required")
                return

            query = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            results = manager.retrieve_relevant_messages(query, limit)
            print(json.dumps(results, indent=2))

        elif command == 'delete':
            if len(sys.argv) < 3:
                print("Error: session_id required")
                return

            session_id = sys.argv[2]
            success = manager.delete_conversation(session_id)
            print(f"{'Successfully' if success else 'Failed to'} delete conversation {session_id}")

        elif command == 'ingest':
            if len(sys.argv) < 3:
                print("Error: file path required")
                return

            file_path = sys.argv[2]
            if not os.path.exists(file_path):
                print(f"Error: file not found: {file_path}")
                return

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_sessions = json.load(f)

                if not isinstance(chat_sessions, list):
                    print("Error: file must contain a JSON array of chat sessions")
                    return

                processed_count = manager.ingest_conversations(chat_sessions)
                print(f"Successfully ingested {processed_count} conversations")

            except Exception as e:
                print(f"Error reading or parsing file: {e}")
                return

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
