"""
Execution context for agent orchestration.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.schemas.agent import AgentResponse, ExecutionTrace


class ExecutionContext:
    """
    Shared execution context passed between agents.
    
    Contains all state needed for agent execution.
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        case_id: Optional[str] = None,
        user_id: Optional[str] = None,
        domain: str = "general",
        workflow: str = "default",
        input_data: Optional[Dict[str, Any]] = None,
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.case_id = case_id
        self.user_id = user_id
        self.domain = domain
        self.workflow = workflow
        self.input_data = input_data or {}
        
        # Execution state
        self.planner_state: Dict[str, Any] = {}
        self.agent_outputs: Dict[str, AgentResponse] = {}
        self.execution_trace: List[ExecutionTrace] = []
        self.shared_context: Dict[str, Any] = {}
        self.errors: List[Dict[str, Any]] = []
        
        # Timestamps
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        
        # Memory references (interfaces only)
        self.memory: Dict[str, Any] = {}

    def add_agent_output(self, agent_id: str, response: AgentResponse) -> None:
        """Add agent output to context."""
        self.agent_outputs[agent_id] = response

    def get_agent_output(self, agent_id: str) -> Optional[AgentResponse]:
        """Get output from specific agent."""
        return self.agent_outputs.get(agent_id)

    def add_trace(self, trace: ExecutionTrace) -> None:
        """Add execution trace."""
        self.execution_trace.append(trace)

    def add_error(self, agent_id: str, error: str) -> None:
        """Add error to context."""
        self.errors.append({
            "agent_id": agent_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def set_shared(self, key: str, value: Any) -> None:
        """Set shared context value."""
        self.shared_context[key] = value

    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get shared context value."""
        return self.shared_context.get(key, default)

    def has_errors(self) -> bool:
        """Check if execution has errors."""
        return len(self.errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "request_id": self.request_id,
            "case_id": self.case_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "workflow": self.workflow,
            "planner_state": self.planner_state,
            "shared_context": self.shared_context,
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }
