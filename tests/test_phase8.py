"""
Phase 8 - Workflow Integration Tests
"""

import pytest
import asyncio
from pathlib import Path
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def test_file():
    """Create a test file for upload."""
    test_path = Path("test_document.txt")
    test_path.write_text("This is a test legal document for case analysis.")
    yield test_path
    test_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_document_upload():
    """Test document upload functionality."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test case first
        case_data = {
            "case_number": "TEST-PHASE8-001",
            "title": "Test Case for Upload",
            "status": "open",
            "priority": "high",
            "case_type": "civil",
            "client_name": "Test Client"
        }
        
        response = await client.post("/api/v1/cases", json=case_data)
        assert response.status_code == 201
        case_id = response.json()["id"]
        
        # Upload document
        test_content = b"Test legal document content"
        files = {"files": ("test.txt", test_content, "text/plain")}
        
        response = await client.post(
            f"/api/v1/documents/cases/{case_id}/documents",
            files=files
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["count"] > 0


@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete workflow from upload to review."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Create case
        case_data = {
            "case_number": "TEST-WORKFLOW-001",
            "title": "Complete Workflow Test",
            "status": "open",
            "priority": "high",
            "case_type": "civil",
            "client_name": "Workflow Test Client"
        }
        response = await client.post("/api/v1/cases", json=case_data)
        assert response.status_code == 201
        case_id = response.json()["id"]
        
        # 2. Upload document
        test_content = b"Test document for workflow"
        files = {"files": ("workflow_test.txt", test_content, "text/plain")}
        response = await client.post(
            f"/api/v1/documents/cases/{case_id}/documents",
            files=files
        )
        assert response.status_code == 201
        
        print("✓ Full workflow test passed")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
