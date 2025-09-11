"""
Spending Agent - LangGraph subgraph for transaction analysis and spending insights.

This agent provides conversational financial analysis, spending patterns, and 
personalized recommendations through natural language interaction.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START, MessagesState
import logging
import json

from app.services.user_context_dao import UserContextDAOSync
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("langchain-mcp-adapters not available - MCP tools will be mocked")

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
        self._auth_service = AuthService()
        self._mcp_clients = {}  # Cache MCP clients per user_id
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
        
        # Add fetch_and_process node for transaction fetching
        workflow.add_node("fetch_and_process", self._fetch_and_process_node)
        
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
        
        # Most specialized nodes lead to END
        workflow.add_edge("spending_analysis", END)
        workflow.add_edge("budget_planning", END)
        workflow.add_edge("optimization", END)
        workflow.add_edge("general_spending", END)
        
        # Transaction query has conditional routing
        workflow.add_conditional_edges(
            "transaction_query",
            self._route_transaction_query,
            {
                "found_in_graphiti": END,
                "fetch_from_plaid": "fetch_and_process"
            }
        )
        
        # After fetching and processing, route back to transaction_query for results
        workflow.add_edge("fetch_and_process", "transaction_query")
        
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
    
    def _route_transaction_query(self, state: SpendingAgentState) -> str:
        """
        Router function for transaction query conditional routing.
        
        Returns routing decision based on whether data was found in Graphiti.
        """
        found_in_graphiti = state.get("found_in_graphiti", False)
        if found_in_graphiti:
            logger.info("Transaction data found in Graphiti, routing to END")
            return "found_in_graphiti"
        else:
            logger.info("Transaction data not found in Graphiti, routing to fetch from Plaid")
            return "fetch_from_plaid"
    
    async def _get_mcp_client(self, user_id: str) -> MultiServerMCPClient:
        """
        Get or create MCP client with real JWT authentication for the user.
        
        Each user gets their own MCP client with a personalized JWT token.
        Generates a proper JWT token using AuthService for secure MCP server access.
        """
        if not MCP_AVAILABLE:
            logger.warning("MCP library not available - transaction fetching will be mocked")
            return None
        
        # Check if we already have a client for this user
        if user_id not in self._mcp_clients:
            try:
                # Generate real JWT token for the specific user
                jwt_token = self._auth_service.generate_access_token(user_id)
                logger.info(f"Generated JWT token for MCP authentication (user: {user_id})")
                
                self._mcp_clients[user_id] = MultiServerMCPClient({
                    "mcp": {
                        "transport": "streamable_http", 
                        "url": "http://localhost:8000/mcp/",
                        "headers": {
                            "Authorization": f"Bearer {jwt_token}"
                        }
                    }
                })
                logger.info(f"MCP client initialized with real JWT authentication for user: {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to create MCP client with JWT authentication for user {user_id}: {str(e)}")
                return None
        
        return self._mcp_clients[user_id]
    
    async def _fetch_transactions(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch transactions from Plaid via MCP tools.
        
        Implements the first phase: fetch fresh transaction data from Plaid
        FIXME: Add Graphiti integration for Phase 2 (store processed insights)
        """
        try:
            mcp_client = await self._get_mcp_client(user_id)
            if not mcp_client:
                # Mock fallback when MCP is not available
                logger.info(f"Using mock transactions for user {user_id}")
                return {
                    "status": "success",
                    "transactions": [],
                    "total_transactions": 0,
                    "message": "Mock transaction data (MCP not available)"
                }
            
            # Get all available tools
            tools = await mcp_client.get_tools()
            
            # Find the get_all_transactions tool
            transaction_tool = None
            for tool in tools:
                if getattr(tool, 'name', '') == 'get_all_transactions':
                    transaction_tool = tool
                    break
            
            if not transaction_tool:
                logger.error("get_all_transactions tool not found")
                return {
                    "status": "error", 
                    "error": "Transaction fetching tool not available",
                    "transactions": []
                }
            
            # Fetch transactions using the MCP tool
            result = await transaction_tool.ainvoke({})
            
            # Parse the JSON response
            if isinstance(result, str):
                parsed_result = json.loads(result)
            else:
                parsed_result = result
            
            logger.info(f"Fetched {parsed_result.get('total_transactions', 0)} transactions for user {user_id}")
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error fetching transactions for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "transactions": []
            }
    
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
        Specialized node for transaction query intent with Graphiti checking.
        
        First checks Graphiti for existing transaction insights. If found, returns results.
        If not found, sets state flag for conditional routing to fetch from Plaid.
        
        FIXME: Implement real Graphiti integration via MCP tools
        FIXME: Implement real transaction querying with database integration
        FIXME: Use LLM-based response generation with professional tone
        """
        user_id = state.get("user_id", "")
        
        # FIXME: Check Graphiti for existing transaction insights via MCP tools
        # For now, mock the Graphiti check - assume no data found initially
        found_in_graphiti = False
        transaction_insights = []
        
        if found_in_graphiti:
            # Return results from Graphiti
            response_content = f"I found {len(transaction_insights)} transaction insights in your history. Here's your transaction analysis based on previous processing."
            logger.info(f"Returning {len(transaction_insights)} transaction insights from Graphiti for user {user_id}")
        else:
            # No data in Graphiti - need to fetch from Plaid
            response_content = "Let me fetch your latest transaction data and analyze it for you. This will take a moment to process."
            logger.info(f"No transaction insights found in Graphiti for user {user_id}, routing to Plaid fetch")
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "transaction_query",
                "data_source": "graphiti" if found_in_graphiti else "needs_plaid_fetch"
            }
        )
        
        return {
            "messages": [response],
            "found_in_graphiti": found_in_graphiti,
            "transaction_insights": transaction_insights
        }
    
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
    
    async def _fetch_and_process_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Fetch fresh transactions from Plaid and process them for Graphiti storage.
        
        FIXME: Implement Graphiti storage via MCP tools after transaction processing
        FIXME: Implement real transaction processing and categorization
        FIXME: Add error handling for Plaid API failures
        """
        user_id = state.get("user_id", "")
        logger.info(f"Fetching fresh transaction data from Plaid for user {user_id}")
        
        # Fetch transactions from Plaid via MCP tools
        transaction_result = await self._fetch_transactions(user_id)
        
        if transaction_result["status"] == "error":
            response_content = f"I encountered an issue while fetching your transaction data: {transaction_result.get('error', 'Unknown error')}"
            logger.error(f"Transaction fetch failed for user {user_id}: {transaction_result.get('error')}")
        else:
            transactions = transaction_result.get("transactions", [])
            total_count = transaction_result.get("total_transactions", len(transactions))
            
            # FIXME: Process transactions and store insights in Graphiti via MCP tools
            # For now, just acknowledge the fetch
            response_content = f"Successfully fetched {total_count} transactions from your connected accounts. Processing and analyzing this data now."
            logger.info(f"Fetched {total_count} transactions for user {user_id}, ready for Graphiti processing")
            
            # FIXME: Store processed insights in Graphiti here
            # After storing, set found_in_graphiti=True for next transaction_query call
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "transaction_fetch_and_process",
                "transaction_count": transaction_result.get("total_transactions", 0)
            }
        )
        
        return {
            "messages": [response],
            # FIXME: CRITICAL - Only set found_in_graphiti=True if BOTH conditions succeed:
            # 1. Plaid fetch succeeds AND 2. Graphiti storage succeeds
            # Current mock always sets True - will cause infinite loops with real implementations
            # if either Plaid or Graphiti operations fail
            "found_in_graphiti": True  # After processing, data will be in Graphiti
        }
    
    async def invoke_spending_conversation(self, user_message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user message through the spending agent subgraph.
        
        This method is async to support MCP tool calls for Plaid transaction fetching.
        
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
            result = await self.graph.ainvoke(initial_state)
            
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
