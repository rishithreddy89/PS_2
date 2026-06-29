"""
Tests for CaseDocument repository JSON filtering.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_document import CaseDocument
from app.repositories.case_document import CaseDocumentRepository


class TestCaseDocumentRepository:
    """Test CaseDocument repository operations."""

    @pytest.mark.asyncio
    async def test_get_indexed_documents(self, db: AsyncSession):
        """Test retrieving indexed documents."""
        repo = CaseDocumentRepository(db)
        
        # Create test case
        case_id = "test-case-123"
        
        # Create indexed document
        indexed_doc = CaseDocument(
            case_id=case_id,
            document_type="uploaded",
            title="Indexed Doc",
            file_path="/path/to/doc1.pdf",
            file_name="doc1.pdf",
            file_size=1000,
            meta_data={"status": "indexed"}
        )
        db.add(indexed_doc)
        
        # Create processing document
        processing_doc = CaseDocument(
            case_id=case_id,
            document_type="uploaded",
            title="Processing Doc",
            file_path="/path/to/doc2.pdf",
            file_name="doc2.pdf",
            file_size=2000,
            meta_data={"status": "processing"}
        )
        db.add(processing_doc)
        
        # Create failed document
        failed_doc = CaseDocument(
            case_id=case_id,
            document_type="uploaded",
            title="Failed Doc",
            file_path="/path/to/doc3.pdf",
            file_name="doc3.pdf",
            file_size=3000,
            meta_data={"status": "failed"}
        )
        db.add(failed_doc)
        
        await db.commit()
        
        # Test get_indexed_documents
        indexed = await repo.get_indexed_documents(case_id)
        assert len(indexed) == 1
        assert indexed[0].title == "Indexed Doc"
        assert indexed[0].meta_data["status"] == "indexed"
    
    @pytest.mark.asyncio
    async def test_count_indexed_documents(self, db: AsyncSession):
        """Test counting indexed documents."""
        repo = CaseDocumentRepository(db)
        
        case_id = "test-case-456"
        
        # Create multiple indexed documents
        for i in range(3):
            doc = CaseDocument(
                case_id=case_id,
                document_type="uploaded",
                title=f"Doc {i}",
                file_path=f"/path/to/doc{i}.pdf",
                file_name=f"doc{i}.pdf",
                file_size=1000 * (i + 1),
                meta_data={"status": "indexed"}
            )
            db.add(doc)
        
        # Add processing doc
        doc = CaseDocument(
            case_id=case_id,
            document_type="uploaded",
            title="Processing",
            file_path="/path/to/processing.pdf",
            file_name="processing.pdf",
            file_size=5000,
            meta_data={"status": "processing"}
        )
        db.add(doc)
        
        await db.commit()
        
        # Test count
        count = await repo.count_indexed_documents(case_id)
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_get_by_status(self, db: AsyncSession):
        """Test retrieving documents by status."""
        repo = CaseDocumentRepository(db)
        
        case_id = "test-case-789"
        
        # Create documents with different statuses
        statuses = ["indexed", "processing", "failed", "indexed"]
        for i, status in enumerate(statuses):
            doc = CaseDocument(
                case_id=case_id,
                document_type="uploaded",
                title=f"Doc {i}",
                file_path=f"/path/to/doc{i}.pdf",
                file_name=f"doc{i}.pdf",
                file_size=1000,
                meta_data={"status": status}
            )
            db.add(doc)
        
        await db.commit()
        
        # Test get by status
        indexed = await repo.get_by_status(case_id, "indexed")
        assert len(indexed) == 2
        
        processing = await repo.get_by_status(case_id, "processing")
        assert len(processing) == 1
        
        failed = await repo.get_by_status(case_id, "failed")
        assert len(failed) == 1
    
    @pytest.mark.asyncio
    async def test_no_indexed_documents(self, db: AsyncSession):
        """Test when no indexed documents exist."""
        repo = CaseDocumentRepository(db)
        
        case_id = "test-case-empty"
        
        # Create only processing documents
        doc = CaseDocument(
            case_id=case_id,
            document_type="uploaded",
            title="Processing",
            file_path="/path/to/doc.pdf",
            file_name="doc.pdf",
            file_size=1000,
            meta_data={"status": "processing"}
        )
        db.add(doc)
        await db.commit()
        
        # Test - should return empty list
        indexed = await repo.get_indexed_documents(case_id)
        assert len(indexed) == 0
        
        count = await repo.count_indexed_documents(case_id)
        assert count == 0


@pytest.fixture
async def db():
    """Database fixture for testing."""
    from app.database.session import get_db
    
    async for session in get_db():
        yield session
        await session.rollback()
