"""
Document upload and management API endpoints.
"""

from typing import List
from pathlib import Path
import shutil
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.case_document import CaseDocument
from app.knowledge.ingestion import get_ingestion_service
from app.utils.logging.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/cases/{case_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_documents(
    case_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple documents for a case."""
    ingestion = get_ingestion_service()
    uploaded_docs = []

    for file in files:
        logger.info(f"File upload started", filename=file.filename)
        
        # Validate extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error(f"Invalid file extension", filename=file.filename, ext=ext)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {ext} not allowed. Allowed: PDF, DOCX, TXT"
            )

        # Validate size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            logger.error(f"File too large", filename=file.filename, size=len(content))
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} exceeds 10MB limit"
            )

        # Save file
        case_dir = UPLOAD_DIR / case_id
        case_dir.mkdir(exist_ok=True)
        file_path = case_dir / file.filename
        
        logger.info(f"Saving file", filename=file.filename, path=str(file_path))
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"File saved", filename=file.filename)

        # Create database record
        doc = CaseDocument(
            case_id=case_id,
            document_type="uploaded",
            title=file.filename,
            file_path=str(file_path),
            file_name=file.filename,
            file_size=len(content),
            mime_type=file.content_type,
            meta_data={"status": "processing"}
        )
        db.add(doc)
        await db.flush()

        # Trigger async ingestion
        try:
            logger.info(f"Starting ingestion", filename=file.filename, file_path=str(file_path))
            await ingestion.ingest_file(str(file_path), case_id=case_id)
            logger.info(f"Document parsed", filename=file.filename)
            logger.info(f"Chunks created", filename=file.filename)
            logger.info(f"Local embeddings generated", filename=file.filename)
            logger.info(f"Indexed in ChromaDB", filename=file.filename)
            doc.meta_data = {"status": "indexed"}
            logger.info(f"Upload completed", filename=file.filename, status="indexed")
        except Exception as e:
            logger.error(f"Ingestion failed", filename=file.filename, error=str(e), exc_info=True)
            doc.meta_data = {"status": "failed", "error": str(e)}
            logger.info(f"Upload completed", filename=file.filename, status="failed")

        uploaded_docs.append({
            "id": doc.id,
            "filename": doc.file_name,
            "size": doc.file_size,
            "status": doc.meta_data.get("status")
        })

    await db.commit()
    logger.info(f"Upload batch completed", count=len(uploaded_docs), case_id=case_id)
    
    return {"documents": uploaded_docs, "count": len(uploaded_docs)}


@router.get("/cases/{case_id}/documents")
async def list_documents(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all documents for a case."""
    result = await db.execute(
        select(CaseDocument).where(CaseDocument.case_id == case_id)
    )
    docs = result.scalars().all()
    
    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.file_name,
                "size": doc.file_size,
                "type": doc.document_type,
                "status": doc.meta_data.get("status") if doc.meta_data else "unknown",
                "created_at": doc.created_at.isoformat(),
            }
            for doc in docs
        ]
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    result = await db.execute(
        select(CaseDocument).where(CaseDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    # Delete DB record
    await db.delete(doc)
    await db.commit()


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download a document file."""
    result = await db.execute(
        select(CaseDocument).where(CaseDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type=doc.mime_type or "application/octet-stream",
    )

@router.get("/debug/chromadb/{case_id}")
async def debug_chromadb(case_id: str, db: AsyncSession = Depends(get_db)):
    """Diagnostic endpoint to check retrieval pipeline for a case."""
    from app.knowledge.chroma_service import get_chroma_service
    from app.knowledge.retrieval import get_retrieval_service
    from app.core.config import get_settings
    
    settings = get_settings()
    
    # 1. Check indexed documents in DB
    result = await db.execute(
        select(CaseDocument).where(CaseDocument.case_id == case_id)
    )
    docs = result.scalars().all()
    indexed_docs = [{"id": d.id, "filename": d.file_name, "status": d.meta_data.get("status")} for d in docs]
    
    # 2. Check ChromaDB Stats
    chroma = get_chroma_service()
    collection_name = "case_documents"
    stats = chroma.get_collection_stats(collection_name, case_id=case_id)
    
    # 3. Get exact chunk details from Chroma
    collection = chroma.get_collection(collection_name)
    raw_data = collection.get(where={"case_id": case_id}, include=["metadatas", "documents", "embeddings"])
    
    chunk_ids = raw_data.get("ids", [])
    chunk_metadatas = raw_data.get("metadatas", [])
    chunk_documents = raw_data.get("documents", [])
    chunk_embeddings = raw_data.get("embeddings", [])
    
    # 4. Perform a test retrieval
    retrieval = get_retrieval_service()
    query = "facts, evidence, events, and timeline"
    retrieved_chunks = await retrieval.retrieve(
        query=query,
        collections=[collection_name],
        top_k=5,
        filters={"case_id": case_id}
    )
    
    retrieved_data = [
        {
            "chunk_id": r.chunk_id,
            "document_id": r.document_id,
            "score": r.final_score,
            "content_preview": r.content[:100] + "..." if len(r.content) > 100 else r.content,
            "metadata": r.metadata
        } for r in retrieved_chunks
    ]
    
    return {
        "case_id": case_id,
        "collection_name": collection_name,
        "persist_directory": settings.chroma_persist_directory,
        "database_documents": indexed_docs,
        "chromadb_stats": stats,
        "chunk_count": len(chunk_ids),
        "chunk_ids": chunk_ids,
        "chunk_metadata": chunk_metadatas,
        "stored_text": chunk_documents,
        "embedding_count": len(chunk_embeddings),
        "embedding_dimensions": len(chunk_embeddings[0]) if len(chunk_embeddings) > 0 and len(chunk_embeddings[0]) > 0 else 0,
        "test_query": query,
        "retrieval_results": retrieved_data,
        "similarity_scores": [r["score"] for r in retrieved_data]
    }
