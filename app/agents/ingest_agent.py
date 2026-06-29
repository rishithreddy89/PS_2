"""
Ingest Agent - Document ingestion and normalization.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.context import ExecutionContext
from app.schemas.agent import AgentExecutionStatus, AgentResponse
from app.schemas.specialized_agents import (
    DocumentCategory,
    DocumentMetadata,
    DocumentSummary,
    Entity,
    EntityType,
    Event,
)
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class IngestAgent(BaseAgent):
    """
    Ingest Agent for document ingestion and normalization.
    
    Accepts various document formats and extracts structured information
    without performing AI reasoning.
    """

    def __init__(self):
        super().__init__(
            agent_id="ingest_agent",
            name="Document Ingest Agent",
            description="Ingests and normalizes documents into structured format",
            version="1.0.0",
            supported_domains=["legal", "healthcare", "insurance", "finance", "*"],
            priority=10,
        )

    @property
    def capabilities(self) -> List[str]:
        return [
            "document_ingestion",
            "metadata_extraction",
            "entity_extraction",
            "event_extraction",
            "normalization",
        ]

    @property
    def required_tools(self) -> List[str]:
        return []

    @property
    def required_memory(self) -> List[str]:
        return []

    async def execute(self, context: ExecutionContext) -> AgentResponse:
        """Execute document ingestion."""
        start_time = datetime.utcnow()
        
        try:
            await self._validate_execution(context)
            
            documents = context.input_data.get("documents", [])
            if not documents:
                documents = [context.input_data]
            
            summaries = []
            for doc in documents:
                summary = await self._ingest_document(doc, context)
                summaries.append(summary)
            
            context.set_shared("ingested_documents", summaries)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.COMPLETED,
                output={
                    "document_summaries": [s.dict() for s in summaries],
                    "total_documents": len(summaries),
                },
                duration_ms=duration,
                metadata={"documents_processed": len(summaries)},
            )
            
        except Exception as e:
            logger.error("Ingest agent failed", error=str(e), request_id=context.request_id)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                status=AgentExecutionStatus.FAILED,
                error=str(e),
                duration_ms=duration,
            )

    async def validate(self, context: ExecutionContext) -> bool:
        """Validate execution context."""
        documents = context.input_data.get("documents")
        if not documents and not context.input_data.get("content"):
            return False
        return True

    async def _validate_execution(self, context: ExecutionContext) -> None:
        """Validate before execution."""
        if not await self.validate(context):
            raise ValueError("Invalid input: No documents or content provided")

    async def _ingest_document(
        self, doc: Dict[str, Any], context: ExecutionContext
    ) -> DocumentSummary:
        """Ingest single document."""
        content = doc.get("content", "")
        title = doc.get("title", "Untitled Document")
        
        doc_id = doc.get("document_id", str(uuid.uuid4()))
        category = self._detect_category(doc)
        entities = self._extract_entities(content)
        events = self._extract_events(content)
        
        people = [e.value for e in entities if e.entity_type == EntityType.PERSON]
        organizations = [e.value for e in entities if e.entity_type == EntityType.ORGANIZATION]
        dates = [e.value for e in entities if e.entity_type == EntityType.DATE]
        
        metadata = DocumentMetadata(
            document_id=doc_id,
            title=title,
            category=category,
            source=doc.get("source"),
            created_at=doc.get("created_at"),
            file_type=doc.get("file_type"),
            file_size=doc.get("file_size"),
            page_count=doc.get("page_count"),
        )
        
        return DocumentSummary(
            document_id=doc_id,
            title=title,
            category=category,
            case_type=doc.get("case_type"),
            entities=entities,
            people=people,
            organizations=organizations,
            dates=dates,
            events=events,
            metadata=metadata,
            content_summary=content[:500] if content else None,
        )

    def _detect_category(self, doc: Dict[str, Any]) -> DocumentCategory:
        """Detect document category."""
        doc_type = doc.get("type", "").lower()
        content = doc.get("content", "").lower()
        
        if doc_type == "email" or "from:" in content[:200]:
            return DocumentCategory.EMAIL
        elif doc_type == "contract" or "agreement" in content[:500]:
            return DocumentCategory.CONTRACT
        elif "court" in content[:300] or "notice" in doc.get("title", "").lower():
            return DocumentCategory.COURT_NOTICE
        elif "witness" in content[:300] or "statement" in doc.get("title", "").lower():
            return DocumentCategory.WITNESS_STATEMENT
        elif doc_type == "evidence":
            return DocumentCategory.EVIDENCE
        elif "meeting" in doc.get("title", "").lower():
            return DocumentCategory.MEETING_NOTES
        elif doc.get("file_type") == "pdf":
            return DocumentCategory.PDF
        elif doc.get("file_type") in ["txt", "text"]:
            return DocumentCategory.TEXT
        else:
            return DocumentCategory.OTHER

    def _extract_entities(self, content: str) -> List[Entity]:
        """Extract entities from content (simplified)."""
        entities = []
        
        # Simplified entity extraction (placeholder for real NER)
        words = content.split()
        for i, word in enumerate(words[:100]):
            if word and word[0].isupper() and len(word) > 2:
                entities.append(
                    Entity(
                        entity_type=EntityType.PERSON,
                        value=word,
                        confidence=0.6,
                    )
                )
        
        return entities[:10]

    def _extract_events(self, content: str) -> List[Event]:
        """Extract events from content (simplified)."""
        events = []
        
        # Simplified event extraction
        keywords = ["meeting", "hearing", "filed", "signed", "agreed"]
        sentences = content.split(".")
        
        for sentence in sentences[:20]:
            for keyword in keywords:
                if keyword in sentence.lower():
                    events.append(
                        Event(
                            description=sentence.strip()[:200],
                            date=None,
                            participants=[],
                        )
                    )
                    break
        
        return events[:5]
