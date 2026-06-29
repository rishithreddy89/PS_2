"""ChromaDB vector store service."""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.core.config import get_settings
from app.knowledge.models import DocumentChunk, RetrievalResult
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChromaDBService:
    """ChromaDB vector database service."""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self._init_collections()
    
    def _init_collections(self):
        """Initialize collection names."""
        self.collection_names = {
            "statutes": "legal_statutes",
            "precedents": "case_precedents",
            "playbooks": "internal_playbooks",
            "templates": "legal_templates",
            "cases": "sample_cases"
        }
    
    def get_collection(self, collection_name: str):
        """Get or create collection."""
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    async def insert(
        self,
        collection_name: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ):
        """Insert chunks with embeddings."""
        collection = self.get_collection(collection_name)
        
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            }
            for chunk in chunks
        ]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Inserted chunks", collection=collection_name, count=len(chunks))
    
    async def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Search collection by embedding."""
        collection = self.get_collection(collection_name)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        retrieval_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                retrieval_results.append(
                    RetrievalResult(
                        document_id=results["metadatas"][0][i].get("document_id", ""),
                        chunk_id=chunk_id,
                        content=results["documents"][0][i],
                        score=1.0 - results["distances"][0][i],
                        metadata=results["metadatas"][0][i]
                    )
                )
        
        return retrieval_results
    
    async def delete_document(self, collection_name: str, document_id: str):
        """Delete all chunks for a document."""
        collection = self.get_collection(collection_name)
        collection.delete(where={"document_id": document_id})
        logger.info(f"Deleted document", collection=collection_name, document_id=document_id)
    
    async def update(
        self,
        collection_name: str,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """Update existing chunks."""
        collection = self.get_collection(collection_name)
        collection.update(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def get_collection_stats(self, collection_name: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a collection."""
        collection = self.get_collection(collection_name)
        
        where = {"case_id": case_id} if case_id else None
        
        if where:
            data = collection.get(where=where, include=["metadatas"])
        else:
            data = collection.get(include=["metadatas"])
            
        metadatas = data.get("metadatas", [])
        
        doc_ids = set()
        case_ids = set()
        
        for meta in metadatas:
            if meta:
                if "document_id" in meta:
                    doc_ids.add(str(meta["document_id"]))
                if "case_id" in meta:
                    case_ids.add(str(meta["case_id"]))
                    
        stats = {
            "collection_name": collection_name,
            "chunk_count": len(metadatas),
            "document_count": len(doc_ids),
            "case_ids": list(case_ids),
            "sample_metadata": metadatas[:5] if metadatas else []
        }
        
        logger.info(
            "ChromaDB statistics",
            collection=collection_name,
            chunk_count=stats["chunk_count"],
            document_count=stats["document_count"],
            case_ids_count=len(stats["case_ids"])
        )
        return stats

    def get_collection_size(self, collection_name: str) -> int:
        """Get total number of embeddings in a collection."""
        collection = self.get_collection(collection_name)
        return collection.count()

    def get_items_by_ids(self, collection_name: str, ids: List[str]) -> Dict[str, Any]:
        """Retrieve specific items by their IDs."""
        collection = self.get_collection(collection_name)
        return collection.get(ids=ids, include=["metadatas", "documents"])


_chroma_service: Optional[ChromaDBService] = None


def get_chroma_service() -> ChromaDBService:
    """Get singleton ChromaDB service."""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaDBService()
    return _chroma_service
