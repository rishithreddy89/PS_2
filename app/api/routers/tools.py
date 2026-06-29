"""
Tool Registry API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.registry.tool_registry import tool_registry
from app.core.enums import ToolStatus

router = APIRouter(prefix="/tools", tags=["Tool Registry"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_tools(tool_status: Optional[str] = None) -> dict:
    """
    List all registered tools.

    Args:
        tool_status: Optional status filter

    Returns:
        List of tools
    """
    status_filter = ToolStatus(tool_status) if tool_status else None
    tools = tool_registry.list_tools(status=status_filter)

    return {
        "tools": [tool.to_dict() for tool in tools],
        "count": len(tools),
    }


@router.get("/discover", status_code=status.HTTP_200_OK)
async def discover_tools(tool_type: Optional[str] = None) -> dict:
    """
    Discover tools by type.

    Args:
        tool_type: Tool type filter

    Returns:
        Matching tools
    """
    tools = tool_registry.discover_tools(tool_type=tool_type)

    return {
        "tools": [tool.to_dict() for tool in tools],
        "count": len(tools),
    }


@router.get("/{tool_id}", status_code=status.HTTP_200_OK)
async def get_tool(tool_id: str) -> dict:
    """
    Get tool metadata by ID.

    Args:
        tool_id: Tool ID

    Returns:
        Tool metadata

    Raises:
        HTTPException: If tool not found
    """
    tool = tool_registry.get_tool(tool_id)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}",
        )

    return tool.to_dict()


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_tool_stats() -> dict:
    """
    Get tool registry statistics.

    Returns:
        Registry statistics
    """
    return {
        "total_tools": tool_registry.get_tool_count(),
        "active_tools": len(tool_registry.list_tools(status=ToolStatus.ACTIVE)),
        "inactive_tools": len(tool_registry.list_tools(status=ToolStatus.INACTIVE)),
    }
