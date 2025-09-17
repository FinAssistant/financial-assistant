from typing import Dict, Any, Optional
import logging
from .orchestrator_agent import get_orchestrator_agent


class ConversationHandler:
    """
    Interface layer that handles conversation requests and delegates to the OrchestratorAgent.
    This class provides a clean API for conversation handling without containing routing logic.
    """
    
    def __init__(self):
        self.orchestrator_agent = get_orchestrator_agent()
        self.logger = logging.getLogger(__name__)
        self.logger.info("ConversationHandler initialized")
    
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
            # Process through OrchestratorAgent
            result = await self.orchestrator_agent.invoke_conversation(
                user_message=user_message.strip(),
                user_id=user_id,
                session_id=effective_session_id
            )
            
            
            return result
            
        except Exception as e:
            self.logger.error(f"ConversationHandler processing error: {e}")
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
            
            # Stream through OrchestratorAgent
            async for chunk in self.orchestrator_agent.stream_conversation(
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
            graph_initialized = self.orchestrator_agent.graph is not None
            
            if not graph_initialized:
                return {
                    "status": "unhealthy",
                    "graph_initialized": False,
                    "test_response_received": False,
                    "error": "OrchestratorAgent not initialized"
                }
            
            # Check if LLM is available
            llm_available = self.orchestrator_agent.llm is not None
            
            
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
            
            # System is healthy if graph is initialized, regardless of LLM availability
            return {
                "status": "healthy" if graph_initialized else "unhealthy",
                "graph_initialized": graph_initialized,
                "llm_available": llm_available,
                "test_response_received": test_response_received,
                "error": error
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "graph_initialized": False,
                "test_response_received": False,
                "error": str(e)
            }