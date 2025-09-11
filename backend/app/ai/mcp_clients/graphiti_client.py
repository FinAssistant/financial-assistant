"""
Shared MCP client for Graphiti graph database integration.

This module provides a reusable client for connecting to Graphiti's MCP server
and accessing its tools for storing and querying financial context and relationships.
"""

import logging
from typing import Dict, Any, Optional, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphitiMCPClient:
    """
    Shared MCP client for Graphiti database operations.
    
    Provides a simple interface for agents to store episodes and search
    for financial context without needing to manage MCP connections directly.
    """
    
    def __init__(self, graphiti_url: str = "http://localhost:8080/sse"):
        """
        Initialize Graphiti MCP client.
        
        Args:
            graphiti_url: URL of the Graphiti MCP server (default: docker container)
        """
        self.graphiti_url = graphiti_url
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[Any] = []
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Connect to Graphiti MCP server and initialize tools.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = MultiServerMCPClient({
                "graphiti": {
                    "transport": "sse",
                    "url": self.graphiti_url
                }
            })
            
            # Initialize tools from Graphiti server
            self.tools = await self.client.get_tools()
            self._connected = True
            
            logger.info(f"Connected to Graphiti MCP server at {self.graphiti_url}")
            logger.info(f"Available tools: {[tool.name for tool in self.tools]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Graphiti MCP server: {e}")
            self._connected = False
            return False
    
    def _get_tool(self, tool_name: str):
        """Get tool by name from available tools."""
        if not self._connected:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in available tools: {[t.name for t in self.tools]}")
        return tool
    
    async def add_episode(
        self, 
        user_id: str, 
        content: str, 
        name: str = "Financial Conversation",
        source_description: str = "agent_conversation"
    ) -> Dict[str, Any]:
        """
        Store a financial conversation episode in Graphiti.
        
        CRITICAL: Uses user_id as group_id to ensure user data isolation.
        
        Args:
            user_id: Authenticated user ID (also used as group_id for isolation)
            content: Conversation content to store
            name: Episode name (default: "Financial Conversation")
            source_description: Source description for tracking (default: "agent_conversation")
            
        Returns:
            Response from Graphiti add_memory tool
        """
        add_memory_tool = self._get_tool("add_memory")
        
        try:
            response = await add_memory_tool.ainvoke({
                "name": name,
                "episode_body": content,
                "source": "text",  # Let Graphiti handle content type classification
                "source_description": source_description,
                "group_id": user_id,  # CRITICAL: user_id = group_id for data isolation
            })
            
            logger.info(f"Stored episode for user {user_id}: {name}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to store episode for user {user_id}: {e}")
            raise
    
    async def search(self, user_id: str, query: str, max_nodes: int = 10) -> Dict[str, Any]:
        """
        Search for financial context using Graphiti.
        
        CRITICAL: Only searches within user's group_id for data isolation.
        
        Args:
            user_id: Authenticated user ID (used as group_id filter)
            query: Search query for financial context
            max_nodes: Maximum number of nodes to return (default: 10)
            
        Returns:
            Search results from Graphiti
        """
        search_tool = self._get_tool("search_memory_nodes")
        
        try:
            response = await search_tool.ainvoke({
                "query": query,
                "group_ids": [user_id],  # CRITICAL: filter by user's group_id
                "max_nodes": max_nodes,
                "center_node_uuid": None,
            })
            
            logger.info(f"Search completed for user {user_id}: {query}")
            return response
            
        except Exception as e:
            logger.error(f"Search failed for user {user_id}: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if client is connected to Graphiti server."""
        return self._connected
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools] if self.tools else []


# Global instance for reuse across agents
_graphiti_client: Optional[GraphitiMCPClient] = None


async def get_graphiti_client(graphiti_url: Optional[str] = None) -> GraphitiMCPClient:
    """
    Get or create shared Graphiti MCP client instance.
    
    Args:
        graphiti_url: URL of Graphiti MCP server (defaults to config value)
        
    Returns:
        Connected GraphitiMCPClient instance
    """
    global _graphiti_client
    
    # Use config URL if not provided
    url = graphiti_url or settings.mcp_graphiti_server_url
    
    if _graphiti_client is None or not _graphiti_client.is_connected():
        _graphiti_client = GraphitiMCPClient(url)
        await _graphiti_client.connect()
    
    return _graphiti_client