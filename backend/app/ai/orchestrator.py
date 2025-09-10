from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from .langgraph_config import get_langgraph_config


class OrchestratorAgent:
    """
    Simple orchestrator agent that processes user messages and provides basic responses.
    Future: This will route messages to specialized agents (Onboarding, Spending, etc.).
    """
    
    def __init__(self):
        self.langgraph_config = get_langgraph_config()
    
    def process_message(
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
            result = self.langgraph_config.invoke_conversation(
                user_message=user_message.strip(),
                user_id=user_id,
                session_id=effective_session_id
            )
            
            return result
            
        except Exception as e:
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
    
    def health_check(self) -> Dict[str, Any]:
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
            
            if llm_available:
                # Test basic functionality if LLM is available
                test_response = self.process_message(
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