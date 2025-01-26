from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from app.core.config import settings
from typing import List, Optional, Dict, Any
import logging
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self):
        self.collection_name = "chat_messages"
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            # Test connection
            self.client.get_collections()
            logger.info("Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise
        self.embeddings = OpenAIEmbeddings(
            api_key="sk-pro..." # move to env-file
        )
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the collection exists with the correct settings"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI embeddings dimension
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {str(e)}")
            raise

    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[dict]] = None
    ) -> List[str]:
        """Add texts to the vector store"""
        try:
            vector_store = Qdrant(
                client=self.client,
                collection_name=self.collection_name,
                embeddings=self.embeddings
            )
            
            ids = await vector_store.aadd_texts(
                texts=texts,
                metadatas=metadatas or [{}] * len(texts)
            )
            return ids
        except Exception as e:
            logger.error(f"Error adding texts: {str(e)}")
            raise

    async def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ):
        """Search for similar texts"""
        try:
            vector_store = Qdrant(
                client=self.client,
                collection_name=self.collection_name,
                embeddings=self.embeddings
            )
            
            results = await vector_store.asimilarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise

    async def delete_by_metadata(self, filter_metadata: Dict[str, Any]):
        """Delete vectors by metadata"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                            for key, value in filter_metadata.items()
                        ]
                    )
                )
            )
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            raise

    async def search_similar(self, text: str) -> str:
        try:
            # Get embeddings for the search text
            embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
            vector = await embeddings.aembed_query(text)
            
            # Search for similar vectors
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=5  # Return top 5 similar results
            )
            
            # Format results into a string
            context = " ".join([hit.payload.get("text", "") for hit in search_result])
            return context

        except Exception as e:
            logger.error(f"Error searching similar texts: {str(e)}", exc_info=True)
            return ""  # Return empty context on error
