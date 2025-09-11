from typing import Dict, Any, Optional
import logging
from .langgraph_config import get_langgraph_config
from .financial_keywords import contains_financial_keywords
from .mcp_clients.graphiti_client import get_graphiti_client


class OrchestratorAgent:
    """
    Simple orchestrator agent that processes user messages and provides basic responses.
    Future: This will route messages to specialized agents (Onboarding, Spending, etc.).
    """
    
    def __init__(self):
        self.langgraph_config = get_langgraph_config()
        self.logger = logging.getLogger(__name__)
        self.logger.info("OrchestratorAgent initialized")
    
    async def process_message(
        self, 
        user_message: str, 
        user_id: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the LangGraph orchestrator.
        
        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user
            session_id: Optional session identifier
            
        Returns:
            Dict containing the AI response and metadata
        """
        # Use session_id or generate a default one
        effective_session_id = session_id or f"session_{user_id}"
        
        if not user_message or not user_message.strip():
            return {
                "content": "I'm here to help! Please let me know what you'd like to discuss about your finances.",
                "agent": "orchestrator",
                "session_id": effective_session_id,
                "user_id": user_id,
                "message_type": "ai_response",
                "error": None
            }
        
        try:
            # Process through LangGraph
            result = await self.langgraph_config.invoke_conversation(
                user_message=user_message.strip(),
                user_id=user_id,
                session_id=effective_session_id
            )
            
            # Check for financial keywords and store in Graphiti if detected
            await self._store_financial_context_if_relevant(
                user_message=user_message.strip(),
                user_id=user_id,
                session_id=effective_session_id,
                agent_response=result.get("agent", "orchestrator")
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Orchestrator processing error: {e}")
            # Error handling - return graceful fallback
            return {
                "content": "I apologize, but I'm having trouble processing your message right now. Please try again.",
                "agent": "orchestrator",
                "session_id": effective_session_id,  # Use effective_session_id instead of session_id
                "user_id": user_id,
                "message_type": "ai_response",
                "error": str(e)
            }
    
    async def stream_message(
        self, 
        user_message: str, 
        user_id: str, 
        session_id: Optional[str] = None
    ):
        """
        Stream a message response through the LangGraph orchestrator.
        
        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user
            session_id: Optional session identifier
            
        Yields:
            Streaming chunks from the conversation
        """
        if not user_message or not user_message.strip():
            yield {
                "content": "I'm here to help! Please let me know what you'd like to discuss about your finances.",
                "agent": "orchestrator",
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "ai_response",
                "error": None
            }
            return
        
        try:
            # Use session_id or generate a default one
            effective_session_id = session_id or f"session_{user_id}"
            
            # Stream through LangGraph
            async for chunk in self.langgraph_config.stream_conversation(
                user_message=user_message.strip(),
                user_id=user_id,
                session_id=effective_session_id
            ):
                yield chunk
            
        except Exception as e:
            # Error handling - yield graceful fallback
            yield {
                "content": "I apologize, but I'm having trouble processing your message right now. Please try again.",
                "agent": "orchestrator",
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "ai_response",
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Simple health check for the orchestrator agent.
        
        Returns:
            Dict with health status information
        """
        try:
            # Check if graph is initialized
            graph_initialized = self.langgraph_config.graph is not None
            
            if not graph_initialized:
                return {
                    "status": "unhealthy",
                    "graph_initialized": False,
                    "test_response_received": False,
                    "error": "LangGraph not initialized"
                }
            
            # Check if LLM is available
            llm_available = self.langgraph_config.llm is not None
            
            # Check Graphiti MCP server connectivity
            graphiti_available = False
            graphiti_error = None
            try:
                graphiti_client = await get_graphiti_client()
                graphiti_available = graphiti_client.is_connected()
                if not graphiti_available:
                    graphiti_error = "Graphiti MCP server not connected"
            except Exception as e:
                graphiti_error = f"Graphiti MCP server error: {str(e)}"
            
            if llm_available:
                # Test basic functionality if LLM is available
                test_response = await self.process_message(
                    user_message="health check",
                    user_id="system",
                    session_id="health_check"
                )
                test_response_received = test_response.get("content") is not None and test_response.get("error") is None
                error = test_response.get("error")
            else:
                # If LLM is not available, skip the test but still report healthy system
                test_response_received = False
                error = "LLM not configured - API key missing"
            
            # System is healthy if graph is initialized, regardless of LLM/Graphiti availability
            return {
                "status": "healthy" if graph_initialized else "unhealthy",
                "graph_initialized": graph_initialized,
                "llm_available": llm_available,
                "graphiti_available": graphiti_available,
                "test_response_received": test_response_received,
                "error": error,
                "graphiti_error": graphiti_error
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "graph_initialized": False,
                "test_response_received": False,
                "error": str(e)
            }
    
    async def _store_financial_context_if_relevant(
        self,
        user_message: str,
        user_id: str,
        session_id: str,
        agent_response: str
    ) -> None:
        """
        Store user message in Graphiti if it contains financial keywords.
        
        CRITICAL: Uses user_id as group_id for user data isolation.
        Handles Graphiti storage errors gracefully without breaking conversation flow.
        
        Args:
            user_message: The user's message to analyze
            user_id: Authenticated user ID (used as group_id for isolation)
            session_id: Conversation session identifier  
            agent_response: The responding agent name
        """
        try:
            # Check if message contains financial keywords
            if not contains_financial_keywords(user_message):
                self.logger.debug(f"No financial keywords detected in message from user {user_id}")
                return
            
            # Get Graphiti client
            graphiti_client = await get_graphiti_client()
            
            if not graphiti_client.is_connected():
                self.logger.warning("Graphiti client not connected - skipping context storage")
                return
            
            # Store episode with conversation context metadata
            episode_metadata = f"agent_conversation | agent: {agent_response} | session: {session_id}"
            
            await graphiti_client.add_episode(
                user_id=user_id,  # CRITICAL: user_id also used as group_id for data isolation
                content=user_message,
                name="Financial Conversation Context",
                source_description=episode_metadata
            )
            
            self.logger.info(f"Stored financial context for user {user_id} in session {session_id}")
            
        except Exception as e:
            # Log error but don't break conversation flow
            self.logger.error(f"Failed to store financial context for user {user_id}: {e}")
            # Gracefully continue - Graphiti storage failure shouldn't break conversations