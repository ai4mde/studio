import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.services.vector_store import QdrantManager
from app.services.chat.chat_manager import LangChainChatManager

async def test_vector_store():
    # Initialize managers
    vector_store = QdrantManager()
    chat_manager = LangChainChatManager(session_id="test_session")

    # Test adding and searching messages
    test_messages = [
        "How do I implement a REST API?",
        "What are the best practices for database design?",
        "How do I handle authentication in FastAPI?"
    ]

    # Add messages
    for msg in test_messages:
        print(f"\nProcessing message: {msg}")
        response = await chat_manager.process_message(msg)
        print(f"AI Response: {response[:100]}...")  # Print first 100 chars

    # Test similarity search
    query = "How do I secure my API?"
    print(f"\nSearching for: {query}")
    results = await chat_manager.find_similar_messages(query)
    
    print("\nSimilar messages found:")
    for doc, score in results:
        print(f"Score: {score:.4f}")
        print(f"Content: {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}\n")

if __name__ == "__main__":
    asyncio.run(test_vector_store()) 