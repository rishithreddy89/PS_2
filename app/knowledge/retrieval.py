"""Hybrid retrieval combining vector and BM25 search."""

from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

from app.knowledge.models import HybridRetrievalResult, RetrievalResult
from app.knowledge.local_embedding import get_local_embedding_service
from app.knowledge.chroma_service import get_chroma_service
from app.core.config import get_settings
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class HybridRetrievalService:
    """Hybrid retrieval with vector + BM25 search."""
    
    def __init__(self):
        self.embedding_service = get_local_embedding_service()
        self.chroma_service = get_chroma_service()
        self.bm25_index: Dict[str, BM25Okapi] = {}
        self.documents_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    async def retrieve(
        self,
        query: str,
        collections: List[str],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4
    ) -> List[HybridRetrievalResult]:
        """Perform hybrid retrieval."""
        top_k = top_k or settings.top_k_results
        
        # Sanitize filters for ChromaDB
        if filters:
            filters = {k: v for k, v in filters.items() if v is not None}
            if not filters:
                filters = None
                
        query_embedding = await self.embedding_service.embed_query(query)
        
        all_results = []
        
        for collection in collections:
            vector_results = await self._vector_search(
                collection, query_embedding, top_k * 2, filters
            )
            
            bm25_results = await self._bm25_search(
                collection, query, top_k * 2, filters
            )
            
            fused = self._fuse_results(
                vector_results, bm25_results, vector_weight, bm25_weight
            )
            
            all_results.extend(fused)
        
        all_results = self._deduplicate(all_results)
        all_results = sorted(all_results, key=lambda x: x.final_score, reverse=True)
        final_results = all_results[:top_k]
        
        avg_sim = sum([r.final_score for r in final_results]) / len(final_results) if final_results else 0.0
        
        logger.info(
            "Retrieval pipeline complete",
            query=query,
            collections=collections,
            filters=filters,
            retrieved_chunk_ids=[r.chunk_id for r in final_results],
            total_chunks=len(final_results),
            average_similarity=round(avg_sim, 4),
            retrieved_context_length=sum(len(r.content) for r in final_results)
        )
        
        return final_results
    
    async def _vector_search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """Vector similarity search."""
        return await self.chroma_service.search(
            collection_name=collection,
            query_embedding=query_embedding,
            n_results=top_k,
            where=filters
        )
    
    async def _bm25_search(
        self,
        collection: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """BM25 keyword search."""
        if collection not in self.bm25_index:
            await self._build_bm25_index(collection)
        
        if collection not in self.bm25_index:
            return []
        
        bm25 = self.bm25_index[collection]
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        docs = self.documents_cache[collection]
        scored_docs = []
        for doc, score in zip(docs, scores):
            # Apply metadata filters
            if filters:
                match = True
                for k, v in filters.items():
                    if doc.get("metadata", {}).get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            scored_docs.append({"doc": doc, "score": score})
            
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_docs[:top_k]
    
    async def _build_bm25_index(self, collection: str):
        """Build BM25 index for collection."""
        try:
            chroma_collection = self.chroma_service.get_collection(collection)
            data = chroma_collection.get()
            
            if not data["documents"]:
                return
            
            docs = [
                {
                    "chunk_id": data["ids"][i],
                    "document_id": data["metadatas"][i].get("document_id", ""),
                    "content": data["documents"][i],
                    "metadata": data["metadatas"][i]
                }
                for i in range(len(data["ids"]))
            ]
            
            tokenized_corpus = [doc["content"].lower().split() for doc in docs]
            self.bm25_index[collection] = BM25Okapi(tokenized_corpus)
            self.documents_cache[collection] = docs
            
            logger.info(f"Built BM25 index", collection=collection, docs=len(docs))
        except Exception as e:
            logger.error(f"BM25 index build failed", collection=collection, error=str(e))
    
    def _fuse_results(
        self,
        vector_results: List[RetrievalResult],
        bm25_results: List[Dict[str, Any]],
        vector_weight: float,
        bm25_weight: float
    ) -> List[HybridRetrievalResult]:
        """Fuse vector and BM25 results."""
        scores_map: Dict[str, Dict[str, Any]] = {}
        
        for result in vector_results:
            scores_map[result.chunk_id] = {
                "vector_score": result.score,
                "bm25_score": 0.0,
                "content": result.content,
                "document_id": result.document_id,
                "metadata": result.metadata
            }
        
        max_bm25 = max([r["score"] for r in bm25_results], default=1.0)
        
        for result in bm25_results:
            chunk_id = result["doc"]["chunk_id"]
            normalized_score = result["score"] / max_bm25 if max_bm25 > 0 else 0
            
            if chunk_id in scores_map:
                scores_map[chunk_id]["bm25_score"] = normalized_score
            else:
                scores_map[chunk_id] = {
                    "vector_score": 0.0,
                    "bm25_score": normalized_score,
                    "content": result["doc"]["content"],
                    "document_id": result["doc"]["document_id"],
                    "metadata": result["doc"]["metadata"]
                }
        
        hybrid_results = []
        for chunk_id, data in scores_map.items():
            final_score = (
                vector_weight * data["vector_score"] +
                bm25_weight * data["bm25_score"]
            )
            
            hybrid_results.append(
                HybridRetrievalResult(
                    chunk_id=chunk_id,
                    document_id=data["document_id"],
                    content=data["content"],
                    vector_score=data["vector_score"],
                    bm25_score=data["bm25_score"],
                    final_score=final_score,
                    metadata=data["metadata"]
                )
            )
        
        return hybrid_results
    
    def _deduplicate(self, results: List[HybridRetrievalResult]) -> List[HybridRetrievalResult]:
        """Remove duplicate chunks."""
        seen = set()
        unique = []
        
        for result in results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                unique.append(result)
        
        return unique


_retrieval_service: Optional[HybridRetrievalService] = None


def get_retrieval_service() -> HybridRetrievalService:
    """Get singleton retrieval service."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = HybridRetrievalService()
    return _retrieval_service
