"""
Spending Agent - LangGraph subgraph for transaction analysis and spending insights.

This agent provides conversational financial analysis, spending patterns, and 
personalized recommendations through natural language interaction.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START, MessagesState
import logging

from app.services.user_context_dao import UserContextDAOSync

logger = logging.getLogger(__name__)


class SpendingAgentState(MessagesState):
    """Extended state for Spending Agent with additional context."""
    user_id: str = ""
    session_id: str = ""
    # FIXME: Replace Dict[str, Any] with proper TypedDict if needed
    user_context: Dict[str, Any] = {}  # SQLite demographics data
    # FIXME: Replace Dict[str, Any] with proper TypedDict if needed  
    spending_insights: Dict[str, Any] = {}  # Graphiti insights cache


class SpendingAgent:
    """
    LangGraph subgraph for spending analysis and financial insights.
    
    Follows the established pattern from LangGraphConfig but implements
    specialized nodes for spending-related conversations.
    """
    
    def __init__(self):
        self.graph = None
        self._user_context_dao = UserContextDAOSync()
        self._setup_graph()
    
    def _setup_graph(self) -> None:
        """Create and configure the spending agent subgraph."""
        workflow = StateGraph(SpendingAgentState)
        
        # Add core nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("route_intent", self._route_intent_node)
        
        # Add specialized intent-handling nodes
        workflow.add_node("spending_analysis", self._spending_analysis_node)
        workflow.add_node("budget_planning", self._budget_planning_node)
        workflow.add_node("optimization", self._optimization_node)
        workflow.add_node("transaction_query", self._transaction_query_node)
        workflow.add_node("general_spending", self._general_spending_node)
        
        # Define the graph flow with conditional routing
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "route_intent")
        
        # Add conditional edges based on detected intent
        workflow.add_conditional_edges(
            "route_intent",
            self._route_to_intent_node,
            {
                "spending_analysis": "spending_analysis",
                "budget_planning": "budget_planning", 
                "optimization": "optimization",
                "transaction_query": "transaction_query",
                "general_spending": "general_spending"
            }
        )
        
        # All specialized nodes lead to END
        workflow.add_edge("spending_analysis", END)
        workflow.add_edge("budget_planning", END)
        workflow.add_edge("optimization", END)
        workflow.add_edge("transaction_query", END)
        workflow.add_edge("general_spending", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        
        logger.info("SpendingAgent subgraph initialized with conditional routing")
    
    def _route_to_intent_node(self, state: SpendingAgentState) -> str:
        """
        Router function to determine which intent-specific node to route to.
        
        Returns the name of the node to route to based on detected intent.
        """
        detected_intent = state.get("detected_intent", "general_spending")
        logger.info(f"Routing to intent node: {detected_intent}")
        return detected_intent
    
    def _initialize_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Initialize agent with SQLite context retrieval.
        
        Subtask: Implement agent initialization node with SQLite context retrieval
        """
        user_id = state.get("user_id", "")
        logger.info(f"Initializing SpendingAgent for user: {user_id}")
        
        try:
            # Retrieve user context from SQLite via DAO
            user_context = self._user_context_dao.get_user_context(user_id)
            
            if not user_context:
                # User not found - return default context
                logger.warning(f"User context not found for user_id: {user_id}")
                user_context = {
                    "user_id": user_id,
                    "demographics": {},
                    "financial_context": {}
                }
            else:
                logger.info(f"Successfully retrieved user context for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error retrieving user context for {user_id}: {str(e)}")
            # Fallback to empty context on error
            user_context = {
                "user_id": user_id,
                "demographics": {},
                "financial_context": {}
            }
        
        # Update state with retrieved context
        return {
            "user_context": user_context,
            "spending_insights": {}  # Will be populated by Graphiti later
        }
    
    def _route_intent_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Route conversation based on intent detection.
        
        Subtask: Implement agent workflow routing based on conversation intent
        """
        last_message = state["messages"][-1] if state["messages"] else None
        
        if not isinstance(last_message, HumanMessage):
            return {}
        
        user_input = last_message.content.lower()
        
        # FIXME: Implement LLM-based intent classification for more accurate routing
        # Current: Simple keyword matching - replace with LLM call for proper intent detection
        # Consider: OpenAI/Claude API call with predefined intent categories and examples
        # This is a simple keyword-based routing - replace with proper intent detection
        detected_intent = "general_spending"  # Default intent
        
        if any(keyword in user_input for keyword in ["save", "saving", "optimize"]):
            detected_intent = "optimization"
        elif any(keyword in user_input for keyword in ["spend", "spending", "expense"]):
            detected_intent = "spending_analysis"
        elif any(keyword in user_input for keyword in ["budget", "budgeting"]):
            detected_intent = "budget_planning"
        elif any(keyword in user_input for keyword in ["transaction", "purchase"]):
            detected_intent = "transaction_query"
        
        logger.info(f"Detected intent: {detected_intent}")
        
        # Store intent for response generation
        return {
            "detected_intent": detected_intent
        }
    
    def _spending_analysis_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for spending analysis intent.
        
        FIXME: Implement real spending analysis with transaction data integration
        and use LLM-based response generation with professional tone
        """
        response_content = "I'll analyze your spending patterns and provide insights based on your transaction history. Please allow me a moment to process your financial data."
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "spending_analysis"
            }
        )
        return {"messages": [response]}
    
    def _budget_planning_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for budget planning intent.
        
        FIXME: Implement real budget planning algorithms
        and use LLM-based response generation with professional tone
        """
        response_content = "I can assist with budget planning by analyzing your income, expenses, and financial goals to create a suitable budget framework."
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "budget_planning"
            }
        )
        return {"messages": [response]}
    
    def _optimization_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for spending optimization intent.
        
        FIXME: Implement real optimization algorithms and recommendations
        and use LLM-based response generation with professional tone
        """
        response_content = "I'll analyze your spending patterns to identify optimization opportunities and provide cost reduction recommendations."
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "optimization"
            }
        )
        return {"messages": [response]}
    
    def _transaction_query_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for transaction query intent.
        
        FIXME: Implement real transaction querying with database integration
        and use LLM-based response generation with professional tone
        """
        response_content = "I can help you query and analyze your transaction data. Please specify what information you're looking for."
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "transaction_query"
            }
        )
        return {"messages": [response]}
    
    def _general_spending_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for general spending inquiries (default).
        
        FIXME: Implement context-aware general responses
        and use LLM-based response generation with professional tone
        """
        response_content = "I'm your spending analysis agent. I can provide insights on spending patterns, budget planning, optimization recommendations, and transaction analysis. How may I assist you?"
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "general_spending"
            }
        )
        return {"messages": [response]}
    
    def invoke_spending_conversation(self, user_message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user message through the spending agent subgraph.
        
        FIXME: Integrate with main orchestrator in /conversation/send API endpoint
        Currently used for testing - needs integration with LangGraphConfig orchestrator_node
        
        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user  
            session_id: Unique identifier for the conversation session
            
        Returns:
            Dict containing the AI response and metadata
        """
        if not self.graph:
            return {
                "content": "I apologize, but I'm having trouble processing your spending-related request right now. Please try again.",
                "agent": "spending_agent",
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "ai_response",
                "error": "SpendingAgent graph not initialized"
            }
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_id": user_id,
            "session_id": session_id,
            "user_context": {},
            "spending_insights": {}
        }
        
        try:
            # Process through subgraph
            result = self.graph.invoke(initial_state)
            
            # Extract the AI response
            ai_message = result["messages"][-1]
            
            return {
                "content": ai_message.content,
                "agent": ai_message.additional_kwargs.get("agent", "spending_agent"),
                "intent": ai_message.additional_kwargs.get("intent", "general_spending"),
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "ai_response"
            }
            
        except Exception as e:
            logger.error(f"Error in SpendingAgent processing: {str(e)}")
            return {
                "content": "I apologize, but I'm having trouble processing your spending-related request right now. Please try again.",
                "agent": "spending_agent",
                "session_id": session_id,
                "user_id": user_id,
                "message_type": "ai_response",
                "error": str(e)
            }


# Global instance - following the established pattern
_spending_agent = None

def get_spending_agent() -> SpendingAgent:
    """Get or create the global SpendingAgent instance."""
    global _spending_agent
    if _spending_agent is None:
        _spending_agent = SpendingAgent()
    return _spending_agent
