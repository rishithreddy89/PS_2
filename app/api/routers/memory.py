"""
Memory API endpoints.

Full CRUD implementation for memory management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.models.memory import Memory
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_memories(
    memory_type: Optional[str] = None,
    case_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    List all memory entries with optional filters.

    Args:
        memory_type: Filter by memory type (SHORT_TERM, LONG_TERM, CONVERSATION, CASE)
        case_id: Filter by case ID
        db: Database session

    Returns:
        List of memory entries
    """
    query = select(Memory)

    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
    if case_id:
        query = query.where(Memory.case_id == case_id)

    query = query.order_by(Memory.created_at.desc())

    result = await db.execute(query)
    memories = result.scalars().all()

    return [
        {
            "id": mem.id,
            "memory_type": mem.memory_type,
            "key": mem.key,
            "content": _parse_memory_content(mem),
            "case_id": mem.case_id,
            "metadata": mem.meta_data,
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
            "updated_at": mem.updated_at.isoformat() if mem.updated_at else None,
        }
        for mem in memories
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new memory entry.

    Args:
        data: Memory data including memory_type, key, value, and optional case_id
        db: Database session

    Returns:
        Created memory entry
    """
    memory = Memory(
        memory_type=data.get("memory_type", "SHORT_TERM"),
        key=data.get("key", ""),
        value=str(data.get("value", data.get("content", ""))),
        case_id=data.get("case_id"),
        meta_data=data.get("metadata", data.get("meta_data")),
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)

    return {
        "id": memory.id,
        "memory_type": memory.memory_type,
        "key": memory.key,
        "content": _parse_memory_content(memory),
        "case_id": memory.case_id,
        "metadata": memory.meta_data,
        "created_at": memory.created_at.isoformat() if memory.created_at else None,
    }


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a memory entry.

    Args:
        memory_id: Memory ID
        db: Database session

    Raises:
        HTTPException: If memory not found
    """
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found",
        )

    await db.delete(memory)
    await db.commit()


@router.post("/{memory_id}/reindex", status_code=status.HTTP_200_OK)
async def reindex_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Re-index a memory entry in the vector store.

    Args:
        memory_id: Memory ID
        db: Database session

    Returns:
        Re-index status
    """
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found",
        )

    # Update metadata to reflect re-indexing
    memory.meta_data = memory.meta_data or {}
    memory.meta_data["reindex_requested"] = True

    try:
        from app.knowledge.ingestion import get_ingestion_service
        ingestion = get_ingestion_service()
        # Re-index the memory content as a document chunk
        await ingestion.index_text(
            text=memory.value,
            metadata={
                "memory_id": memory.id,
                "memory_type": memory.memory_type,
                "key": memory.key,
            }
        )
        memory.meta_data["reindex_status"] = "completed"
    except Exception as e:
        logger.error("Re-index failed", memory_id=memory_id, error=str(e))
        memory.meta_data["reindex_status"] = "failed"
        memory.meta_data["reindex_error"] = str(e)

    await db.commit()

    return {
        "id": memory.id,
        "status": memory.meta_data.get("reindex_status", "unknown"),
        "message": "Re-index completed" if memory.meta_data.get("reindex_status") == "completed" else "Re-index failed",
    }


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_memory_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get memory statistics."""
    total = await db.execute(select(func.count(Memory.id)))
    total_count = total.scalar() or 0

    type_counts = {}
    for mtype in ["SHORT_TERM", "LONG_TERM", "CONVERSATION", "CASE"]:
        result = await db.execute(
            select(func.count(Memory.id)).where(Memory.memory_type == mtype)
        )
        type_counts[mtype] = result.scalar() or 0

    return {
        "total": total_count,
        "by_type": type_counts,
    }


def _parse_memory_content(memory: Memory) -> dict:
    """Parse memory value into a content dict for frontend consumption."""
    import json
    try:
        return json.loads(memory.value)
    except (json.JSONDecodeError, TypeError):
        return {"value": memory.value}
