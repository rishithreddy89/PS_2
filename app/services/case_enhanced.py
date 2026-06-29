"""
Enhanced case service with workflow integration.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.repositories.case import CaseRepository
from app.services.base import BaseService
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class EnhancedCaseService(BaseService[Case]):
    """Enhanced case service with automatic workflow triggering."""

    def __init__(self, db: AsyncSession):
        self.repository = CaseRepository(db)
        self.db = db

    async def create_with_workflow(self, data: Dict[str, Any]) -> tuple[Case, str]:
        """
        Create case and automatically trigger workflow.
        
        Args:
            data: Case creation data
            
        Returns:
            Tuple of (case, execution_id)
        """
        # Create case
        case = await self.repository.create(data)
        logger.info("Case created", case_id=case.id)
        
        # Trigger workflow
        from app.services.workflow import WorkflowExecutionService
        workflow_service = WorkflowExecutionService(self.db)
        
        execution_id = await workflow_service.trigger_workflow_on_case_creation(
            case_id=case.id,
            case_data=data,
        )
        
        logger.info("Workflow triggered", case_id=case.id, execution_id=execution_id)
        
        return case, execution_id

    async def create(self, data: Dict[str, Any]) -> Case:
        """Create a new case."""
        return await self.repository.create(data)

    async def get_by_id(self, id: str) -> Optional[Case]:
        """Get case by ID."""
        return await self.repository.get_by_id(id)

    async def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[Case]:
        """Get multiple cases."""
        return await self.repository.get_multi(skip=skip, limit=limit, filters=filters)

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Case]:
        """Update a case."""
        return await self.repository.update(id, data)

    async def delete(self, id: str) -> bool:
        """Delete a case."""
        return await self.repository.delete(id)

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count cases."""
        return await self.repository.count(filters)
