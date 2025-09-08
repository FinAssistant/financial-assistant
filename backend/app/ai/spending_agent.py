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
        
        # Add nodes following the story requirements
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("route_intent", self._route_intent_node) 
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Define the graph flow - simple linear for now
        # FIXME: Implement conditional edges for intent-based routing to specialized nodes
        # Should route to: spending_analysis_node, budget_planning_node, optimization_node, etc.
        # Instead of single generate_response_node handling all intents
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "route_intent")
        workflow.add_edge("route_intent", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        
        logger.info("SpendingAgent subgraph initialized")
    
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
    
    def _generate_response_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Generate conversational response with personality awareness.
        
        Subtask: Implement conversational response generation node with personality awareness
        """
        detected_intent = state.get("detected_intent", "general_spending")
        
        # FIXME: Implement actual personality-aware response generation and tell LLM
        # to be professional in response generation when implementing real LLM calls

        # Generate response based on intent
        if detected_intent == "spending_analysis":
            response_content = self._generate_spending_analysis_response()
        elif detected_intent == "budget_planning":
            response_content = self._generate_budget_response()
        elif detected_intent == "optimization":
            response_content = self._generate_optimization_response()
        elif detected_intent == "transaction_query":
            response_content = self._generate_transaction_response()
        else:
            response_content = self._generate_default_response()
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": detected_intent
            }
        )
        
        return {"messages": [response]}
    
    def _generate_spending_analysis_response(self) -> str:
        """Generate spending analysis response."""
        # FIXME: Implement real spending analysis with transaction data
        return "I'll analyze your spending patterns and provide insights based on your transaction history. Please allow me a moment to process your financial data."
    
    def _generate_budget_response(self) -> str:
        """Generate budget planning response."""
        # FIXME: Implement real budget analysis
        return "I can assist with budget planning by analyzing your income, expenses, and financial goals to create a suitable budget framework."
    
    def _generate_optimization_response(self) -> str:
        """Generate optimization recommendations response."""
        # FIXME: Implement real optimization algorithms
        return "I'll analyze your spending patterns to identify optimization opportunities and provide cost reduction recommendations."
    
    def _generate_transaction_response(self) -> str:
        """Generate transaction query response."""
        # FIXME: Implement real transaction querying
        return "I can help you query and analyze your transaction data. Please specify what information you're looking for."
    
    def _generate_default_response(self) -> str:
        """Generate default spending agent response."""
        return "I'm your spending analysis agent. I can provide insights on spending patterns, budget planning, optimization recommendations, and transaction analysis. How may I assist you?"
    
    def invoke_spending_conversation(self, user_message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user message through the spending agent subgraph.
        
        FIXME: This method is not yet integrated - will be called by orchestrator_node
        in LangGraphConfig when routing spending-related queries to this subgraph.
        Integration happens in later subtask: "Integrate Spending Agent with existing /conversation/send API endpoint"
        
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