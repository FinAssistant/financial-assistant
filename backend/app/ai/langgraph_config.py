from typing import Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START, MessagesState
import os


class LangGraphConfig:
    """LangGraph configuration for the AI conversation orchestrator."""
    
    def __init__(self):
        self.graph = None
        self._setup_graph()
    
    def _setup_graph(self) -> None:
        """Create and configure the conversation graph."""
        workflow = StateGraph(MessagesState)
        
        # Add the orchestrator node
        workflow.add_node("orchestrator", self._orchestrator_node)
        
        # Define the graph flow
        workflow.add_edge(START, "orchestrator")
        workflow.add_edge("orchestrator", END)
        
        # Compile the graph
        self.graph = workflow.compile()
    
    def _orchestrator_node(self, state: MessagesState) -> Dict[str, Any]:
        """
        Simple orchestrator that acknowledges messages.
        Future: This will route to specialized agents.
        """
        last_message = state["messages"][-1]
        
        if isinstance(last_message, HumanMessage):
            # Handle welcome nudge from frontend
            if last_message.content == "__WELCOME_NUDGE__":
                response_content = (
                    "👋 Welcome to your AI Financial Assistant! I'm here to help you manage your finances more effectively.\n\n"
                    "I can assist you with:\n"
                    "• Budgeting and expense tracking\n"
                    "• Analyzing your spending patterns\n"
                    "• Financial planning and goal setting\n"
                    "• Investment insights and recommendations\n"
                    "• Answering questions about your transactions\n\n"
                    "What would you like to explore today?"
                )
            else:
                # Simple echo/acknowledgment response for regular messages
                response_content = f"I understand you said: '{last_message.content}'. I'm here to help with your financial needs!"
        else:
            # Default response for non-human messages
            response_content = "I'm ready to help you with your financial questions."
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "orchestrator"
            }
        )
        
        return {"messages": [response]}
    
    def invoke_conversation(self, user_message: str, user_id: str, session_id: str) -> dict:
        """
        Process a user message through the conversation graph.
        
        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Returns:
            Dict containing the AI response and metadata
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized")
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_message)]
        }
        
        # Process through graph
        result = self.graph.invoke(initial_state)
        
        # Extract the AI response
        ai_message = result["messages"][-1]
        
        return {
            "content": ai_message.content,
            "agent": ai_message.additional_kwargs.get("agent", "orchestrator"),
            "session_id": session_id,
            "user_id": user_id,
            "message_type": "ai_response"
        }


# Global instance
_langgraph_config = None


def get_langgraph_config() -> LangGraphConfig:
    """Get or create the global LangGraph configuration instance."""
    global _langgraph_config
    if _langgraph_config is None:
        _langgraph_config = LangGraphConfig()
    return _langgraph_config