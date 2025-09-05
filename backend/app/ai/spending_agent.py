"""
Spending Agent - LangGraph subgraph for transaction analysis and spending insights.

This agent provides conversational financial analysis, spending patterns, and 
personalized recommendations through natural language interaction.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START, MessagesState
import logging

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
        logger.info(f"Initializing SpendingAgent for user: {state.get('user_id', 'unknown')}")
        
        # FIXME: Implement actual SQLite service integration
        # This is a mock implementation - replace with real SQLite service call
        mock_user_context = {
            "user_id": state.get("user_id", ""),
            "demographics": {
                "age_group": "25-34",
                "income_level": "middle", 
                "location": "urban"
            },
            "preferences": {
                "communication_style": "friendly",
                "financial_goals": ["save_money", "budget_better"]
            }
        }
        
        # Update state with context
        return {
            "user_context": mock_user_context,
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
        user_context = state.get("user_context", {})
        detected_intent = state.get("detected_intent", "general_spending")
        
        # FIXME: Implement actual personality-aware response generation
        # This is a mock implementation - replace with proper personality adaptation
        communication_style = user_context.get("preferences", {}).get("communication_style", "professional")
        
        # Generate response based on intent and personality
        if detected_intent == "spending_analysis":
            response_content = self._generate_spending_analysis_response(communication_style)
        elif detected_intent == "budget_planning":
            response_content = self._generate_budget_response(communication_style)
        elif detected_intent == "optimization":
            response_content = self._generate_optimization_response(communication_style)
        elif detected_intent == "transaction_query":
            response_content = self._generate_transaction_response(communication_style)
        else:
            response_content = self._generate_default_response(communication_style)
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": detected_intent,
                "personality_style": communication_style
            }
        )
        
        return {"messages": [response]}
    
    def _generate_spending_analysis_response(self, style: str) -> str:
        """Generate spending analysis response with personality adaptation."""
        # FIXME: Implement real spending analysis with transaction data
        if style == "friendly":
            return "Hey! I'd love to help you understand your spending patterns! 🏦 Let me analyze your recent transactions and give you some personalized insights."
        else:
            return "I'll analyze your spending patterns and provide insights based on your transaction history. Please allow me a moment to process your financial data."
    
    def _generate_budget_response(self, style: str) -> str:
        """Generate budget planning response with personality adaptation."""
        # FIXME: Implement real budget analysis
        if style == "friendly":
            return "Great question about budgeting! 💰 I can help you create a personalized budget based on your spending habits and goals."
        else:
            return "I can assist with budget planning by analyzing your income, expenses, and financial goals to create a suitable budget framework."
    
    def _generate_optimization_response(self, style: str) -> str:
        """Generate optimization recommendations response."""
        # FIXME: Implement real optimization algorithms
        if style == "friendly":
            return "I love helping people save money! ✨ Let me look for opportunities to optimize your spending and boost your savings."
        else:
            return "I'll analyze your spending patterns to identify optimization opportunities and provide cost reduction recommendations."
    
    def _generate_transaction_response(self, style: str) -> str:
        """Generate transaction query response."""
        # FIXME: Implement real transaction querying
        if style == "friendly":
            return "Sure thing! I can help you find and understand any transaction. What would you like to know? 🔍"
        else:
            return "I can help you query and analyze your transaction data. Please specify what information you're looking for."
    
    def _generate_default_response(self, style: str) -> str:
        """Generate default spending agent response."""
        if style == "friendly":
            return "Hi there! I'm your spending assistant! 😊 I can help analyze your spending, create budgets, find ways to save money, and answer questions about your transactions. What would you like to explore today?"
        else:
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
                "personality_style": ai_message.additional_kwargs.get("personality_style", "professional"),
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