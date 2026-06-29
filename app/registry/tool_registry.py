"""
Tool Registry for dynamic tool discovery and execution.

Provides centralized registry for all tools available to agents.
"""

from typing import Any, Callable, Dict, List, Optional

from app.core.enums import ToolStatus
from app.utils.logging.logger import get_logger

logger = get_logger(__name__)


class ToolMetadata:
    """Tool metadata structure."""

    def __init__(
        self,
        tool_id: str,
        tool_name: str,
        tool_type: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        version: str = "1.0.0",
        status: ToolStatus = ToolStatus.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize tool metadata.

        Args:
            tool_id: Unique tool identifier
            tool_name: Human-readable tool name
            tool_type: Tool type classification
            description: Tool description
            input_schema: Expected input schema
            output_schema: Expected output schema
            version: Tool version
            status: Tool status
            metadata: Additional metadata
        """
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.tool_type = tool_type
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.version = version
        self.status = status
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "tool_type": self.tool_type,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "version": self.version,
            "status": self.status,
            "metadata": self.metadata,
        }


class ToolRegistry:
    """
    Tool Registry for managing tool lifecycle.
    
    Provides:
    - Tool registration
    - Tool discovery
    - Tool execution
    - Tool metadata management
    """

    def __init__(self) -> None:
        """Initialize tool registry."""
        self._tools: Dict[str, ToolMetadata] = {}
        self._executors: Dict[str, Callable] = {}
        logger.info("Tool Registry initialized")

    def register_tool(
        self, metadata: ToolMetadata, executor: Callable[[Dict[str, Any]], Any]
    ) -> bool:
        """
        Register a tool in the registry.

        Args:
            metadata: Tool metadata
            executor: Tool execution function

        Returns:
            True if registered successfully
        """
        if metadata.tool_id in self._tools:
            logger.warning(
                "Tool already registered, updating",
                tool_id=metadata.tool_id,
            )

        self._tools[metadata.tool_id] = metadata
        self._executors[metadata.tool_id] = executor

        logger.info(
            "Tool registered",
            tool_id=metadata.tool_id,
            tool_name=metadata.tool_name,
            tool_type=metadata.tool_type,
        )
        return True

    def remove_tool(self, tool_id: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            tool_id: Tool ID

        Returns:
            True if removed successfully
        """
        if tool_id in self._tools:
            del self._tools[tool_id]
            del self._executors[tool_id]
            logger.info("Tool removed", tool_id=tool_id)
            return True

        logger.warning("Tool not found for removal", tool_id=tool_id)
        return False

    def get_tool(self, tool_id: str) -> Optional[ToolMetadata]:
        """
        Get tool metadata by ID.

        Args:
            tool_id: Tool ID

        Returns:
            Tool metadata or None
        """
        return self._tools.get(tool_id)

    def discover_tools(self, tool_type: Optional[str] = None) -> List[ToolMetadata]:
        """
        Discover tools by type.

        Args:
            tool_type: Tool type filter

        Returns:
            List of matching tools
        """
        tools = list(self._tools.values())

        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]

        tools = [t for t in tools if t.status == ToolStatus.ACTIVE]

        logger.info(
            "Tools discovered",
            count=len(tools),
            tool_type=tool_type,
        )
        return tools

    def list_tools(self, status: Optional[ToolStatus] = None) -> List[ToolMetadata]:
        """
        List all tools with optional status filter.

        Args:
            status: Tool status filter

        Returns:
            List of tools
        """
        tools = list(self._tools.values())

        if status:
            tools = [t for t in tools if t.status == status]

        return tools

    async def execute_tool(self, tool_id: str, input_data: Dict[str, Any]) -> Any:
        """
        Execute a tool by ID.

        Args:
            tool_id: Tool ID
            input_data: Tool input data

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or inactive
        """
        if tool_id not in self._tools:
            raise ValueError(f"Tool not found: {tool_id}")

        tool = self._tools[tool_id]

        if tool.status != ToolStatus.ACTIVE:
            raise ValueError(f"Tool is not active: {tool_id}")

        executor = self._executors[tool_id]

        logger.info("Executing tool", tool_id=tool_id, tool_name=tool.tool_name)

        try:
            result = await executor(input_data) if callable(executor) else executor(input_data)
            logger.info("Tool executed successfully", tool_id=tool_id)
            return result
        except Exception as e:
            logger.error("Tool execution failed", tool_id=tool_id, error=str(e))
            raise

    def update_tool_status(self, tool_id: str, status: ToolStatus) -> bool:
        """
        Update tool status.

        Args:
            tool_id: Tool ID
            status: New status

        Returns:
            True if updated successfully
        """
        if tool_id in self._tools:
            self._tools[tool_id].status = status
            logger.info("Tool status updated", tool_id=tool_id, status=status)
            return True

        logger.warning("Tool not found for status update", tool_id=tool_id)
        return False

    def get_tool_count(self) -> int:
        """
        Get total number of registered tools.

        Returns:
            Tool count
        """
        return len(self._tools)

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._executors.clear()
        logger.info("Tool registry cleared")


tool_registry = ToolRegistry()
