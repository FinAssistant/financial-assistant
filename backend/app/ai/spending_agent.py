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
from app.services.llm_service import llm_factory
from app.services.transaction_categorization import TransactionCategorizationService
from app.utils.context_formatting import build_user_context_string
from langchain_core.messages import SystemMessage
from app.ai.mcp_clients.graphiti_client import get_graphiti_client

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
    
    Follows the established pattern from OrchestratorAgent but implements
    specialized nodes for spending-related conversations.
    """
    
    def __init__(self):
        self.graph = None
        self._user_context_dao = UserContextDAOSync()
        self._auth_service = AuthService()
        self._mcp_clients = {}  # Cache MCP clients per user_id
        
        # Initialize LLM client for intelligent responses and analysis
        try:
            self.llm = llm_factory.create_llm()
            logger.info("LLM client initialized for SpendingAgent")

            # Initialize transaction categorization service
            if self.llm:
                from app.core.config import settings
                self.categorization_service = TransactionCategorizationService(self.llm, settings)
                logger.info("Transaction categorization service initialized")
            else:
                self.categorization_service = None

        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.llm = None
            self.categorization_service = None
            
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

    def _apply_categorization_to_transaction(
        self,
        transaction,
        categorization
    ):
        """
        Apply categorization results to a transaction.

        Args:
            transaction: Original PlaidTransaction
            categorization: TransactionCategorization to apply

        Returns:
            Updated transaction with AI categorization fields
        """
        # Create a copy of the transaction with updated AI fields
        updated_data = transaction.model_dump() if hasattr(transaction, 'model_dump') else transaction.__dict__.copy()
        updated_data.update({
            "ai_category": categorization.ai_category,
            "ai_subcategory": categorization.ai_subcategory,
            "ai_confidence": categorization.ai_confidence,
            "ai_tags": categorization.ai_tags
        })

        # Return updated transaction (assuming PlaidTransaction constructor)
        from app.models.plaid_models import PlaidTransaction
        return PlaidTransaction(**updated_data)

    async def _categorize_and_apply_transactions(
        self,
        transactions,
        user_context = None
    ):
        """
        Categorize transactions and apply results to them.

        Args:
            transactions: List of transactions to categorize
            user_context: Optional user context

        Returns:
            Tuple of (updated_transactions, categorization_batch)
        """
        if not self.categorization_service or not transactions:
            return transactions, None

        # Get categorizations
        categorization_batch = await self.categorization_service.categorize_transactions(transactions, user_context)

        # Create lookup for categorizations by transaction_id
        categorization_lookup = {
            cat.transaction_id: cat
            for cat in categorization_batch.categorizations
        }

        # Apply categorizations to transactions
        updated_transactions = []
        for transaction in transactions:
            transaction_id = getattr(transaction, 'transaction_id', transaction.get('transaction_id') if isinstance(transaction, dict) else None)
            if transaction_id and transaction_id in categorization_lookup:
                categorization = categorization_lookup[transaction_id]
                updated_transaction = self._apply_categorization_to_transaction(
                    transaction, categorization
                )
                updated_transactions.append(updated_transaction)
            else:
                # Keep original transaction if categorization failed
                updated_transactions.append(transaction)

        return updated_transactions, categorization_batch

    def _get_last_human_message(self, state: SpendingAgentState) -> str:
        """Extract the last human message from state."""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg.content
        return ""

    def _invoke_llm_with_fallback(self, messages, intent_name: str, fallback_message: str = None) -> str:
        """
        Helper method to invoke LLM with consistent error handling and fallback.

        Args:
            messages: List of messages for LLM
            intent_name: Name of the intent for error logging
            fallback_message: Custom fallback message (optional)

        Returns:
            LLM response content or fallback message
        """
        if fallback_message is None:
            fallback_message = f"I apologize, but my {intent_name} service is temporarily unavailable. Please try again in a few moments, or feel free to ask me about other aspects of your finances."

        if self.llm is None:
            return fallback_message

        try:
            llm_response = self.llm.invoke(messages)
            return llm_response.content
        except Exception as e:
            logger.error(f"LLM call failed in {intent_name}: {e}")
            return fallback_message
    
    async def _fetch_transactions(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch transactions from Plaid via MCP tools.

        Fetches fresh transaction data from Plaid for processing and storage.
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
            # FIXME we should use the cursor/pagination parameters
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
        Route conversation based on LLM-powered intent detection.
        
        Uses LLM to accurately classify user intent with context awareness.
        """
        last_message = state["messages"][-1] if state["messages"] else None
        
        if not isinstance(last_message, HumanMessage):
            return {"detected_intent": "general_spending"}
        
        user_input = last_message.content
        user_context = state.get("user_context", {})
        
        # Build context-aware intent detection prompt using shared utility
        context_str = build_user_context_string(user_context)
        
        system_prompt = f"""You are an intent classifier for a financial spending assistant.
Your task is to classify the user's intent into exactly ONE of these categories:

INTENT CATEGORIES:
1. spending_analysis - User wants to understand their spending patterns, analyze expenses, or review spending habits
2. budget_planning - User wants to create, modify, or discuss budgets and financial planning
3. optimization - User wants recommendations to reduce costs, save money, or optimize spending
4. transaction_query - User wants to find specific transactions, purchases, or account activity
5. general_spending - Default for general questions, greetings, or unclear financial topics

USER CONTEXT: {context_str}

EXAMPLES:
- "How much did I spend on groceries?" → transaction_query
- "I want to save money on my monthly expenses" → optimization  
- "Help me create a monthly budget" → budget_planning
- "What are my spending patterns this month?" → spending_analysis
- "Hi, I need help with my finances" → general_spending

Respond with exactly ONE word: spending_analysis, budget_planning, optimization, transaction_query, or general_spending."""

        try:
            if self.llm:
                # Use LLM for intelligent intent detection - proper conversation format for all providers
                llm_messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_input)
                ]
                response = self.llm.invoke(llm_messages)
                detected_intent = response.content.strip().lower()
                
                # Validate response is one of expected intents
                valid_intents = ["spending_analysis", "budget_planning", "optimization", "transaction_query", "general_spending"]
                if detected_intent not in valid_intents:
                    logger.warning(f"LLM returned invalid intent: {detected_intent}, using fallback detection")
                    detected_intent = self._fallback_intent_detection(user_input)
                    logger.info(f"Fallback detected intent: {detected_intent}")
                    
                logger.info(f"LLM detected intent: {detected_intent}")
            else:
                # Fallback to keyword-based detection if LLM unavailable
                detected_intent = self._fallback_intent_detection(user_input)
                logger.info(f"Fallback detected intent: {detected_intent}")
                
        except Exception as e:
            logger.error(f"Error in LLM intent detection: {e}")
            detected_intent = self._fallback_intent_detection(user_input)
            logger.info(f"Fallback detected intent after error: {detected_intent}")
        
        return {"detected_intent": detected_intent}
    
    def _fallback_intent_detection(self, user_input: str) -> str:
        """Fallback keyword-based intent detection when LLM is unavailable."""
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["save", "saving", "optimize", "reduce", "cheaper"]):
            return "optimization"
        elif any(keyword in user_input_lower for keyword in ["spend", "spending", "expense", "pattern", "analysis"]):
            return "spending_analysis"
        elif any(keyword in user_input_lower for keyword in ["budget", "budgeting", "plan", "planning"]):
            return "budget_planning"
        elif any(keyword in user_input_lower for keyword in ["transaction", "purchase", "bought", "paid", "find"]):
            return "transaction_query"
        else:
            return "general_spending"
    
    def _spending_analysis_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for spending analysis intent.
        Uses LLM to generate personalized spending analysis based on available data.
        """
        
        # Build user context string from state
        user_context_str = build_user_context_string(state.get("user_context", {}))
        
        # FIXME: Integrate processed insights from state.spending_insights (Graphiti cache)
        # 1. Processed insights from state.spending_insights (Graphiti cache)
        # 2. Historical patterns and categorization data
        # 3. Budget vs actual spending comparisons
        
        # For now, use mock data structure to demonstrate LLM integration
        mock_spending_data = {
            "total_monthly_spending": 3250.00,
            "top_categories": [
                {"name": "Food & Dining", "amount": 850.00, "percentage": 26.2},
                {"name": "Transportation", "amount": 650.00, "percentage": 20.0},
                {"name": "Shopping", "amount": 420.00, "percentage": 12.9}
            ],
            "trends": {
                "month_over_month_change": -5.2,
                "unusual_spending": "Higher than usual restaurant spending detected"
            }
        }
        
        # Build comprehensive system prompt
        system_prompt = f"""You are a professional financial advisor providing personalized spending analysis.

USER CONTEXT:
{user_context_str}

SPENDING DATA ANALYSIS:
- Total Monthly Spending: ${mock_spending_data['total_monthly_spending']:,.2f}
- Top Spending Categories:
  * {mock_spending_data['top_categories'][0]['name']}: ${mock_spending_data['top_categories'][0]['amount']:.2f} ({mock_spending_data['top_categories'][0]['percentage']:.1f}%)
  * {mock_spending_data['top_categories'][1]['name']}: ${mock_spending_data['top_categories'][1]['amount']:.2f} ({mock_spending_data['top_categories'][1]['percentage']:.1f}%)
  * {mock_spending_data['top_categories'][2]['name']}: ${mock_spending_data['top_categories'][2]['amount']:.2f} ({mock_spending_data['top_categories'][2]['percentage']:.1f}%)
- Month-over-Month Change: {mock_spending_data['trends']['month_over_month_change']:+.1f}%
- Notable Trend: {mock_spending_data['trends']['unusual_spending']}

INSTRUCTIONS:
1. Provide a conversational, personalized analysis of their spending patterns
2. Highlight key insights and trends specific to their financial situation
3. Consider their user context (age, occupation, family status) in your analysis
4. Offer 2-3 actionable recommendations for improvement
5. Maintain a professional yet approachable tone
6. Keep response concise but informative (3-4 paragraphs)
7. Use specific numbers and percentages from the data

Generate a comprehensive spending analysis response now."""

        # Create messages for LLM
        last_human_message = self._get_last_human_message(state)
        llm_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_human_message or "Please analyze my spending patterns")
        ]
        
        # Generate LLM response with fallback handling
        response_content = self._invoke_llm_with_fallback(llm_messages, "spending analysis")
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "spending_analysis",
                "llm_powered": True
            }
        )
        return {"messages": [response]}
    
    def _budget_planning_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for budget planning intent.
        Uses LLM to generate personalized budget planning guidance based on user context.
        """
        
        # Build user context string from state
        user_context_str = build_user_context_string(state.get("user_context", {}))
        
        # FIXME: Integrate real financial data from these sources:
        # 1. Current spending patterns from state.spending_insights
        # 2. Income information from user financial context
        # 3. Existing budget data if available
        # 4. Financial goals and priorities
        
        # For now, use mock data to demonstrate LLM integration
        mock_financial_data = {
            "monthly_income": 5500.00,
            "current_spending": 3250.00,
            "available_for_budget": 2250.00,
            "debt_payments": 450.00,
            "emergency_fund_target": 16500.00  # 3 months expenses
        }
        
        # Build comprehensive system prompt for budget planning
        system_prompt = f"""You are a professional financial advisor providing personalized budget planning guidance.

USER CONTEXT:
{user_context_str}

FINANCIAL SITUATION:
- Monthly Income: ${mock_financial_data['monthly_income']:,.2f}
- Current Monthly Spending: ${mock_financial_data['current_spending']:,.2f}
- Available for Budgeting: ${mock_financial_data['available_for_budget']:,.2f}
- Current Debt Payments: ${mock_financial_data['debt_payments']:,.2f}
- Emergency Fund Target: ${mock_financial_data['emergency_fund_target']:,.2f}

INSTRUCTIONS:
1. Provide personalized budget planning advice based on their financial situation
2. Consider their user context (age, occupation, family status) in your recommendations
3. Suggest specific budget categories and allocation percentages
4. Address emergency fund building, debt management, and savings goals
5. Offer 2-3 actionable next steps for implementing their budget
6. Maintain a supportive and encouraging tone
7. Keep response comprehensive but digestible (4-5 paragraphs)
8. Use specific dollar amounts and percentages from the data

Generate personalized budget planning guidance now."""

        # Create messages for LLM
        last_human_message = self._get_last_human_message(state)
        llm_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_human_message or "Help me create a budget")
        ]

        # Generate LLM response with error handling
        response_content = self._invoke_llm_with_fallback(llm_messages, "budget planning")
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "budget_planning",
                "llm_powered": True
            }
        )
        return {"messages": [response]}
    
    def _optimization_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for spending optimization intent.
        Uses LLM to generate personalized cost reduction and optimization recommendations.
        """
        
        # Build user context string from state
        user_context_str = build_user_context_string(state.get("user_context", {}))
        
        # FIXME: Integrate real optimization data from these sources:
        # 1. Spending patterns and categories from state.spending_insights
        # 2. Subscription and recurring payment analysis
        # 3. Historical spending trends and outliers
        # 4. Category-wise optimization opportunities
        
        # For now, use mock data to demonstrate LLM integration
        mock_optimization_data = {
            "monthly_spending": 3250.00,
            "optimization_opportunities": [
                {"category": "Food & Dining", "current": 850.00, "potential_savings": 200.00, "optimization": "meal planning"},
                {"category": "Subscriptions", "current": 89.00, "potential_savings": 35.00, "optimization": "cancel unused services"},
                {"category": "Transportation", "current": 650.00, "potential_savings": 150.00, "optimization": "carpooling/transit"}
            ],
            "total_potential_savings": 385.00,
            "highest_impact": "Food & Dining"
        }
        
        # Build comprehensive system prompt for optimization
        system_prompt = f"""You are a financial optimization expert providing personalized cost-saving recommendations.

USER CONTEXT:
{user_context_str}

SPENDING OPTIMIZATION ANALYSIS:
- Current Monthly Spending: ${mock_optimization_data['monthly_spending']:,.2f}
- Total Potential Savings: ${mock_optimization_data['total_potential_savings']:,.2f}
- Highest Impact Category: {mock_optimization_data['highest_impact']}

OPTIMIZATION OPPORTUNITIES:
1. {mock_optimization_data['optimization_opportunities'][0]['category']}: ${mock_optimization_data['optimization_opportunities'][0]['current']:,.2f} → Save ${mock_optimization_data['optimization_opportunities'][0]['potential_savings']:,.2f} through {mock_optimization_data['optimization_opportunities'][0]['optimization']}
2. {mock_optimization_data['optimization_opportunities'][1]['category']}: ${mock_optimization_data['optimization_opportunities'][1]['current']:,.2f} → Save ${mock_optimization_data['optimization_opportunities'][1]['potential_savings']:,.2f} through {mock_optimization_data['optimization_opportunities'][1]['optimization']}  
3. {mock_optimization_data['optimization_opportunities'][2]['category']}: ${mock_optimization_data['optimization_opportunities'][2]['current']:,.2f} → Save ${mock_optimization_data['optimization_opportunities'][2]['potential_savings']:,.2f} through {mock_optimization_data['optimization_opportunities'][2]['optimization']}

INSTRUCTIONS:
1. Provide personalized cost-saving recommendations based on their spending patterns
2. Consider their user context (age, occupation, family status) when suggesting optimizations
3. Prioritize recommendations by potential impact and ease of implementation
4. Offer specific, actionable strategies for each optimization opportunity
5. Include both immediate cost-cutting and long-term saving strategies
6. Maintain an encouraging and practical tone
7. Keep response focused and actionable (3-4 paragraphs)
8. Use specific dollar amounts and percentages from the data

Generate personalized spending optimization recommendations now."""

        # Create messages for LLM
        last_human_message = self._get_last_human_message(state)
        llm_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_human_message or "Help me optimize my spending and reduce costs")
        ]

        # Generate LLM response with error handling
        response_content = self._invoke_llm_with_fallback(llm_messages, "spending optimization")
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "optimization",
                "llm_powered": True
            }
        )
        return {"messages": [response]}
    
    async def _transaction_query_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for transaction query intent with Graphiti checking.

        First checks Graphiti for existing transaction insights. If found, returns results.
        If not found, sets state flag for conditional routing to fetch from Plaid.

        Uses message history to determine if this is a second call (after fetch_and_process).
        """
        user_id = state.get("user_id", "")

        # Check if we've already been through fetch_and_process by looking for its AIMessage
        messages = state.get("messages", [])
        has_fetched_data = any(
            isinstance(msg, AIMessage) and msg.additional_kwargs.get("intent") == "transaction_fetch_and_process"
            for msg in reversed(messages)
        )
        if has_fetched_data:
            logger.info("Found fetch_and_process message in history - this is second call to transaction_query")

        # Get user's query from the original human message
        user_query = self._get_last_human_message(state)

        # Search Graphiti for transaction insights
        found_in_graphiti = False
        transaction_insights = []

        try:
            graphiti_client = await get_graphiti_client()
            if graphiti_client and graphiti_client.is_connected():
                # Search for transaction insights based on user query
                search_results = await graphiti_client.search(
                    user_id=user_id,
                    query=user_query,
                    max_nodes=10
                )

                # Parse search results
                if search_results and isinstance(search_results, dict):
                    nodes = search_results.get("nodes", [])
                    if nodes:
                        found_in_graphiti = True
                        transaction_insights = nodes
                        logger.info(f"Found {len(nodes)} transaction insights in Graphiti for user {user_id}")
                    else:
                        logger.info(f"No transaction insights found in Graphiti for user {user_id}")
                else:
                    logger.info(f"Empty search results from Graphiti for user {user_id}")
            else:
                logger.warning("Graphiti client not available - cannot search for transaction insights")

        except Exception as e:
            logger.error(f"Error searching Graphiti for transaction insights: {e}")

        # Build user context string from state
        user_context_str = build_user_context_string(state.get("user_context", {}))
        
        if found_in_graphiti:
            # Generate LLM-powered response for existing transaction insights
            logger.info(f"Returning {len(transaction_insights)} transaction insights from Graphiti for user {user_id}")

            system_prompt = f"""You are a transaction analysis expert presenting transaction insights to the user.

USER CONTEXT:
{user_context_str}

AVAILABLE DATA:
- Found {len(transaction_insights)} transaction insights in user's history
- Data was previously processed and stored in your knowledge base

INSTRUCTIONS:
1. Provide a comprehensive analysis of their transaction data relevant to their query
2. Use specific details from the transaction insights where available
3. Consider their user context when presenting the information
4. Offer actionable insights and patterns you notice
5. Maintain a professional yet approachable tone
6. Keep response informative and personalized (2-3 paragraphs)

Generate a personalized transaction analysis response now."""

            # Create messages for LLM
            llm_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query or "Show me my transaction data")
            ]

            # Generate LLM response with error handling
            response_content = self._invoke_llm_with_fallback(llm_messages, "transaction analysis")
        elif has_fetched_data:
            # Second call after fetch_and_process - provide simple static response
            logger.info(f"Second call to transaction_query after fetch_and_process for user {user_id}")

            response_content = "I've processed your latest transaction data and updated your financial profile. No specific insights were found matching your current query, but your transaction history has been categorized and stored for future analysis."
        else:
            # First call, no data in Graphiti - need to fetch from Plaid
            response_content = "Let me fetch your latest transaction data and analyze it for you. This will take a moment to process."
            logger.info(f"No transaction insights found in Graphiti for user {user_id}, routing to Plaid fetch")
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "transaction_query",
                "data_source": "graphiti" if found_in_graphiti else "needs_plaid_fetch",
                "llm_powered": True
            }
        )
        
        return {
            "messages": [response],
            "found_in_graphiti": found_in_graphiti,
            "transaction_insights": transaction_insights
        }
    
    def _general_spending_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for general spending inquiries and introductory guidance.
        Uses LLM to provide personalized welcome and guidance based on user context.
        """
        
        # Build user context string from state
        user_context_str = build_user_context_string(state.get("user_context", {}))
        
        # Build comprehensive system prompt for general guidance
        system_prompt = f"""You are a friendly and professional financial advisor providing general guidance and introductions to financial services.

USER CONTEXT:
{user_context_str}

YOUR CAPABILITIES:
- Spending Pattern Analysis: Analyze transaction history and spending habits
- Budget Planning: Help create personalized budgets based on income and expenses
- Spending Optimization: Identify opportunities to reduce costs and save money  
- Transaction Queries: Help find and analyze specific transactions or purchases

INSTRUCTIONS:
1. Provide a warm, personalized welcome based on their user context
2. Briefly introduce your capabilities in an approachable way
3. Consider their demographic context when tailoring your introduction
4. Ask an engaging follow-up question to understand their specific financial needs
5. Keep the tone conversational, helpful, and encouraging
6. Keep response concise but comprehensive (2-3 paragraphs)
7. Make them feel comfortable asking about any financial topic

Generate a personalized introduction and guidance now."""

        # Create messages for LLM
        last_human_message = self._get_last_human_message(state)
        llm_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_human_message or "Hello, I need help with my finances")
        ]

        # Generate LLM response with error handling
        response_content = self._invoke_llm_with_fallback(llm_messages, "financial guidance")
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "general_spending",
                "llm_powered": True
            }
        )
        return {"messages": [response]}
    
    async def _fetch_and_process_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Fetch fresh transactions from Plaid and process them for Graphiti storage.

        Fetches transactions, applies AI categorization, and stores results in Graphiti.
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

            # Process transactions with AI categorization
            user_context = state.get("user_context", {})

            try:
                if self.categorization_service and transactions:
                    # Convert raw transaction data to PlaidTransaction objects if needed
                    from app.models.plaid_models import PlaidTransaction
                    transaction_objects = []
                    for txn in transactions:
                        if isinstance(txn, dict):
                            transaction_objects.append(PlaidTransaction(**txn))
                        else:
                            transaction_objects.append(txn)

                    # Categorize and apply AI insights
                    categorized_transactions, categorization_batch = await self._categorize_and_apply_transactions(
                        transaction_objects, user_context
                    )

                    categorized_count = len(categorization_batch.categorizations) if categorization_batch else 0

                    # Store categorized transactions in Graphiti
                    try:
                        graphiti_client = await get_graphiti_client()
                        if graphiti_client and graphiti_client.is_connected():
                            # Batch store transactions with AI categorization
                            storage_results = await graphiti_client.batch_store_transaction_episodes(
                                user_id=user_id,
                                transactions=categorized_transactions,
                                concurrency=8,
                                check_duplicates=True
                            )

                            # Count successful storage vs duplicates vs errors
                            stored_count = sum(1 for r in storage_results if not r.get('error') and not r.get('found'))
                            duplicate_count = sum(1 for r in storage_results if r.get('found'))
                            error_count = sum(1 for r in storage_results if r.get('error'))

                            logger.info(f"Graphiti storage: {stored_count} new, {duplicate_count} duplicates, {error_count} errors")
                            response_content = f"Successfully fetched {total_count} transactions, categorized {categorized_count} with AI insights, and stored {stored_count} new transactions in your knowledge base. Processing complete!"
                        else:
                            logger.warning("Graphiti client not available - transactions categorized but not stored")
                            response_content = f"Successfully fetched {total_count} transactions and categorized {categorized_count} with AI insights. Note: Knowledge base storage temporarily unavailable."

                    except Exception as graphiti_error:
                        logger.error(f"Failed to store transactions in Graphiti: {graphiti_error}")
                        response_content = f"Successfully fetched {total_count} transactions and categorized {categorized_count} with AI insights. Note: There was an issue storing to your knowledge base, but the data is still available."

                    logger.info(f"Fetched {total_count} transactions, categorized {categorized_count} for user {user_id}")
                else:
                    response_content = f"Successfully fetched {total_count} transactions, or AI categorization service is unavailable."
                    logger.info(f"Fetched {total_count} transactions for user {user_id}, or AI categorization service is unavailable.")

            except Exception as e:
                logger.error(f"Error processing transactions with AI categorization: {e}")
                response_content = f"Successfully fetched {total_count} transactions, but encountered an issue with AI categorization. Data is still available for analysis."
        
        response = AIMessage(
            content=response_content,
            additional_kwargs={
                "agent": "spending_agent",
                "intent": "transaction_fetch_and_process",
                "transaction_count": transaction_result.get("total_transactions", 0)
            }
        )
        
        return {
            "messages": [response]
        }
    
    async def invoke_spending_conversation(self, user_message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user message through the spending agent subgraph.

        This method is async to support MCP tool calls for Plaid transaction fetching.

        TODO: Integrate with main orchestrator in /conversation/send API endpoint
        Currently used for testing - needs integration with OrchestratorAgent orchestrator_node
        
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
