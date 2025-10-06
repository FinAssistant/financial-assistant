"""
Spending Agent - LangGraph subgraph for transaction analysis and spending insights.

This agent provides conversational financial analysis, spending patterns, and 
personalized recommendations through natural language interaction.
"""

from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START, MessagesState
from langgraph.graph.state import RunnableConfig
import logging
import json
import asyncio

from app.services.llm_service import llm_factory
from app.services.transaction_categorization import TransactionCategorizationService
from app.utils.context_formatting import build_user_context_string, format_transaction_insights_for_llm_context
from app.utils.transaction_query_parser import parse_user_query_to_intent
from app.utils.transaction_query_executor import execute_transaction_query
from app.models.transaction_query_models import QueryIntent
from langchain_core.messages import SystemMessage
from app.ai.mcp_clients.plaid_client import get_plaid_client
from app.core.database import SQLiteUserStorage

logger = logging.getLogger(__name__)

class SpendingAgentState(MessagesState):
    """Extended state for Spending Agent with additional context."""
    user_id: str = ""
    session_id: str = ""
    detected_intent: str = ""  # Intent detected by route_intent node
    has_transaction_data: bool = False  # Whether transaction data exists or query was handled
    fetch_attempts: int = 0  # Track number of fetch attempts to prevent infinite loops
    user_context: Dict[str, Any] = {}  # SQLite demographics data

class SpendingAgent:
    """
    LangGraph subgraph for spending analysis and financial insights.
    
    Follows the established pattern from OrchestratorAgent but implements
    specialized nodes for spending-related conversations.
    """
    
    def __init__(self, test_transaction_limit: Optional[int] = None):
        self.graph = None
        self._plaid_client = get_plaid_client()  # Use shared Plaid MCP client
        self.test_transaction_limit = test_transaction_limit  # Hard limit for testing

        # Initialize SQLite storage for both transactions and user context
        self._storage = SQLiteUserStorage()
        logger.info("SQLite storage initialized for SpendingAgent (transactions + user context)")

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
                "has_transaction_data": END,
                "fetch_from_plaid": "fetch_and_process",
                "max_attempts_reached": END
            }
        )
        
        # After fetching and processing, route back to transaction_query for results
        workflow.add_edge("fetch_and_process", "transaction_query")
        
        # Compile the graph
        self.graph = workflow.compile()
        
        logger.info("SpendingAgent subgraph initialized with conditional routing")

    def graph_compile(self):
        """
        Return the compiled graph for integration with orchestrator.
        Follows the same pattern as onboarding agent.
        """
        if not self.graph:
            raise RuntimeError("SpendingAgent graph not initialized")
        return self.graph
    

    def _route_to_intent_node(self, state: SpendingAgentState) -> str:
        """
        Router function to determine which intent-specific node to route to.
        
        Returns the name of the node to route to based on detected intent.
        """
        detected_intent = state.get("detected_intent", "general_spending")
        logger.debug(f"🔀 ROUTER: Current state keys: {list(state.keys())}")
        logger.debug(f"🔀 ROUTER: Full detected_intent value: {repr(state.get('detected_intent'))}")
        logger.info(f"Routing to intent node: {detected_intent}")
        return detected_intent
    
    def _route_transaction_query(self, state: SpendingAgentState) -> str:
        """
        Router function for transaction query conditional routing.

        Returns routing decision based on whether transaction data exists or query was handled
        and the number of fetch attempts to prevent infinite loops.
        """
        has_transaction_data = state.get("has_transaction_data", False)
        fetch_attempts = state.get("fetch_attempts", 0)

        if has_transaction_data:
            logger.info("Transaction data available or query handled, routing to END")
            return "has_transaction_data"
        elif fetch_attempts >= 3:
            logger.info(f"Maximum fetch attempts ({fetch_attempts}) reached, routing to END to prevent infinite loop")
            return "max_attempts_reached"
        else:
            logger.info(f"Transaction data not available, routing to fetch from Plaid (attempt {fetch_attempts + 1})")
            return "fetch_from_plaid"
    
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

    def _convert_to_transaction_create(
        self,
        transaction,
        user_id: str
    ):
        """
        Convert PlaidTransaction to TransactionCreate for SQLite storage.

        Args:
            transaction: PlaidTransaction object (categorized)
            user_id: User ID for the transaction

        Returns:
            TransactionCreate object for database storage
        """
        from app.core.sqlmodel_models import TransactionCreate
        import json
        import hashlib

        # Generate canonical hash for deduplication
        hash_input = f"{user_id}:{transaction.transaction_id}:{transaction.account_id}:{transaction.date}:{transaction.amount}"
        canonical_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Convert category list to JSON string if needed
        category_str = json.dumps(transaction.category) if isinstance(transaction.category, list) else transaction.category

        # Convert AI tags to JSON string if it's a list
        ai_tags_str = None
        if hasattr(transaction, 'ai_tags') and transaction.ai_tags:
            if isinstance(transaction.ai_tags, list):
                ai_tags_str = json.dumps(transaction.ai_tags)
            else:
                ai_tags_str = transaction.ai_tags

        return TransactionCreate(
            canonical_hash=canonical_hash,
            user_id=user_id,
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            amount=float(transaction.amount),
            date=str(transaction.date),
            name=transaction.name,
            merchant_name=transaction.merchant_name,
            category=category_str,
            pending=transaction.pending,
            ai_category=getattr(transaction, 'ai_category', None),
            ai_subcategory=getattr(transaction, 'ai_subcategory', None),
            ai_confidence=getattr(transaction, 'ai_confidence', None),
            ai_tags=ai_tags_str
        )

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

    async def _fetch_transactions(self, user_id: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Fetch transactions from Plaid via shared MCP client with timeout.

        Implements the first phase: fetch fresh transaction data from Plaid

        Args:
            user_id: User identifier
            timeout_seconds: Maximum time to wait for Plaid response (default 30s)

        Returns:
            Dict with transaction data or error information
        """
        try:
            # Use the shared Plaid MCP client with timeout
            result = await asyncio.wait_for(
                self._plaid_client.call_tool(user_id, "get_all_transactions"),
                timeout=timeout_seconds
            )

             # Parse the JSON response if needed
            if isinstance(result, str):
                parsed_result = json.loads(result)
            else:
                parsed_result = result

            # Handle mock fallback when MCP is not available
            if parsed_result.get("status") == "error" and "not available" in parsed_result.get("error", ""):
                logger.info(f"Using mock transactions for user {user_id}")
                return {
                    "status": "success",
                    "transactions": [],
                    "total_transactions": 0,
                    "message": "Mock transaction data (MCP not available)"
                }

            # Apply test transaction limit if configured (just for testing)
            if hasattr(self, 'test_transaction_limit') and self.test_transaction_limit and parsed_result.get('transactions'):
                original_count = len(parsed_result['transactions'])
                if original_count > self.test_transaction_limit:
                    parsed_result['transactions'] = parsed_result['transactions'][:self.test_transaction_limit]
                    parsed_result['total_transactions'] = self.test_transaction_limit
                    logger.info(f"Limited transactions from {original_count} to {self.test_transaction_limit} for testing")

            logger.info(f"Fetched {parsed_result.get('total_transactions', 0)} transactions for user {user_id}")
            return parsed_result

        except asyncio.TimeoutError:
            logger.error(f"Timeout ({timeout_seconds}s) fetching transactions for user {user_id}")
            return {
                "status": "error",
                "error": f"Request timed out after {timeout_seconds} seconds. Please try again.",
                "transactions": []
            }
        except Exception as e:
            logger.error(f"Error fetching transactions for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "transactions": []
            }
    
    async def _initialize_node(self, state: SpendingAgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Initialize agent with SQLite context retrieval.

        Subtask: Implement agent initialization node with SQLite context retrieval
        """
        user_id = config["configurable"]["user_id"]
        logger.info(f"Initializing SpendingAgent for user: {user_id}")

        try:
            # Retrieve user context from SQLite
            user_context = await self._storage.get_user_context(user_id)
            
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
        }
    
    def _route_intent_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Route conversation based on LLM-powered intent detection.
        
        Uses LLM to accurately classify user intent with context awareness.
        """
        logger.debug(f"🧠 INTENT_NODE: Starting intent detection with state keys: {list(state.keys())}")

        last_human_message = self._get_last_human_message(state)
        logger.debug(f"🧠 INTENT_NODE: Last message type: {type(last_human_message)}")

        if last_human_message == "":
            logger.debug("🧠 INTENT_NODE: Not a HumanMessage, defaulting to general_spending")
            return {"detected_intent": "general_spending"}

        user_input = last_human_message
        user_context = state.get("user_context", {})
        logger.debug(f"🧠 INTENT_NODE: User input: {repr(user_input)}")
        logger.debug(f"🧠 INTENT_NODE: User context keys: {list(user_context.keys()) if user_context else 'None'}")
        
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
                logger.debug(f"🧠 INTENT_NODE: Raw LLM response: {repr(response.content)}")
                logger.debug(f"🧠 INTENT_NODE: Processed intent: {repr(detected_intent)}")

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
        
        logger.debug(f"🧠 INTENT_NODE: Returning intent result: {{'detected_intent': {repr(detected_intent)}}}")
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
        
        # FIXME:
        # 1. Real processed insights from historical transaction analysis
        # 2. Historical patterns and categorization data from SQLite
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
        
        # FIXME:
        # 1. Current spending patterns from SQLite transaction analysis
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

        # FIXME:
        # 1. Spending patterns from SQLite transaction analysis
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
    
    async def _transaction_query_node(self, state: SpendingAgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Specialized node for transaction query intent with LLM-driven SQL query execution.

        Uses LLM to parse natural language query into structured intent, then executes
        SQL query against SQLite transaction storage and presents results conversationally.
        """
        user_id = config["configurable"]["user_id"]
        logger.debug(f"📊 TRANSACTION_QUERY_NODE: Starting with user_id: {user_id}")

        # Get user's query from the original human message
        user_query = self._get_last_human_message(state)
        logger.debug(f"📊 TRANSACTION_QUERY_NODE: User query: {repr(user_query)}")

        # Check if we have transactions stored in SQLite
        has_stored_data = False
        try:
            # Quick check if user has any transactions
            user_transactions = await self._storage.get_transactions_for_user(user_id, limit=1)
            has_stored_data = len(user_transactions) > 0
            logger.info(f"📊 TRANSACTION_QUERY_NODE: SQLite has data: {has_stored_data}")
        except Exception as e:
            logger.error(f"Error checking for stored transactions: {e}")

        # Build user context string from state
        user_context_str = build_user_context_string(state.get("user_context", {}))

        if not has_stored_data:
            # No transactions stored - route to fetch_and_process
            response_content = "Let me fetch your latest transaction data and analyze it for you. This will take a moment to process."
            logger.info(f"No transactions found in SQLite for user {user_id}, routing to Plaid fetch")

            response = AIMessage(
                content=response_content,
                additional_kwargs={
                    "agent": "spending_agent",
                    "intent": "transaction_query",
                    "data_source": "needs_plaid_fetch",
                    "llm_powered": False
                }
            )

            return {
                "messages": [response],
                "has_transaction_data": False
            }

        # Parse user query to structured intent using LLM
        try:
            if not self.llm:
                raise ValueError("LLM not available for query parsing")

            query_intent = parse_user_query_to_intent(
                user_query=user_query,
                llm=self.llm,
                user_id=user_id
            )
            logger.info(f"📊 TRANSACTION_QUERY_NODE: Parsed intent: {query_intent.intent}, confidence: {query_intent.confidence}")

            # Handle unknown intent
            if query_intent.intent == QueryIntent.UNKNOWN:
                response_content = "I couldn't quite understand your transaction query. Could you try rephrasing? For example:\n\n- 'Show me spending at Starbucks last month'\n- 'How much did I spend on groceries?'\n- 'Find all transactions over $100 this week'\n- 'What's my total spending by category?'"
                logger.warning(f"Unknown query intent for user {user_id}")

                response = AIMessage(
                    content=response_content,
                    additional_kwargs={
                        "agent": "spending_agent",
                        "intent": "transaction_query",
                        "query_intent": "unknown",
                        "llm_powered": True
                    }
                )

                return {
                    "messages": [response],
                    "has_transaction_data": True  # Mark as handled to prevent fetch routing
                }

            # Execute SQL query against SQLite
            query_result = await execute_transaction_query(
                intent=query_intent,
                user_id=user_id,
                storage=self._storage
            )

            logger.info(f"📊 TRANSACTION_QUERY_NODE: Query executed - success: {query_result.success}, count: {query_result.total_count}")

            if not query_result.success:
                response_content = query_result.message or "I encountered an issue executing your transaction query. Please try rephrasing your question."

                response = AIMessage(
                    content=response_content,
                    additional_kwargs={
                        "agent": "spending_agent",
                        "intent": "transaction_query",
                        "query_intent": query_intent.intent.value,
                        "llm_powered": True
                    }
                )

                return {
                    "messages": [response],
                    "has_transaction_data": True
                }

            # Format results for LLM presentation
            logger.debug(f"📊 Raw transaction data (first item): {query_result.data[0] if query_result.data else 'No data'}")

            transaction_data = format_transaction_insights_for_llm_context(
                data_items=query_result.data,
                llm=self.llm,
                reserved_tokens=1500,
                query_intent=query_result.intent.value
            )

            logger.debug(f"📊 Formatted transaction data: {transaction_data[:500]}...")

            # Build time range context if available
            time_range_info = ""
            if query_intent.start_date or query_intent.end_date:
                if query_intent.start_date and query_intent.end_date:
                    time_range_info = f"\nTIME RANGE: {query_intent.start_date} to {query_intent.end_date}"
                elif query_intent.start_date:
                    time_range_info = f"\nTIME RANGE: From {query_intent.start_date} onwards"
                elif query_intent.end_date:
                    time_range_info = f"\nTIME RANGE: Up to {query_intent.end_date}"
            elif query_intent.days_back:
                time_range_info = f"\nTIME RANGE: Last {query_intent.days_back} days"

            system_prompt = f"""You are a transaction analysis expert presenting query results to the user.

USER CONTEXT:
{user_context_str}

QUERY INTENT: {query_intent.intent.value}{time_range_info}
RESULTS: {query_result.total_count} tuples found
EXECUTION TIME: {query_result.execution_time_ms:.2f}ms

TRANSACTION DATA:
{transaction_data}

INSTRUCTIONS:
1. Present the transaction data in a clear, conversational format
2. Focus on answering the user's specific query: "{user_query}"
3. Use specific amounts, merchants, dates, and categories from the data
4. Highlight key insights and patterns relevant to their query
5. If the results are empty, explain what was searched for
6. Maintain a professional yet approachable tone
7. Keep response informative and personalized (2-4 paragraphs)

Generate a personalized transaction query response now."""

            logger.debug(f"📊 System prompt length: {len(system_prompt)} chars")
            logger.debug(f"📊 System prompt:\n{system_prompt}")

            # Create messages for LLM
            llm_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]

            # Generate LLM response with error handling
            response_content = self._invoke_llm_with_fallback(llm_messages, "transaction query analysis")

            response = AIMessage(
                content=response_content,
                additional_kwargs={
                    "agent": "spending_agent",
                    "intent": "transaction_query",
                    "query_intent": query_intent.intent.value,
                    "result_count": query_result.total_count,
                    "execution_time_ms": query_result.execution_time_ms,
                    "data_source": "sqlite",
                    "llm_powered": True
                }
            )

            return {
                "messages": [response],
                "has_transaction_data": True  # Mark as handled to prevent fetch routing
            }

        except Exception as e:
            logger.error(f"Error in transaction query execution: {e}", exc_info=True)
            response_content = "I encountered an issue processing your transaction query. Please try rephrasing your question or check back shortly."

            response = AIMessage(
                content=response_content,
                additional_kwargs={
                    "agent": "spending_agent",
                    "intent": "transaction_query",
                    "error": str(e),
                    "llm_powered": False
                }
            )

            return {
                "messages": [response],
                "has_transaction_data": True  # Mark as handled to prevent fetch routing
            }

    def _general_spending_node(self, state: SpendingAgentState) -> Dict[str, Any]:
        """
        Specialized node for general spending inquiries and introductory guidance.
        Uses LLM to provide personalized welcome and guidance based on user context.
        """
        logger.debug(f"💬 GENERAL_SPENDING_NODE: Starting with state keys: {list(state.keys())}")

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
    
    async def _fetch_and_process_node(self, state: SpendingAgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Fetch fresh transactions from Plaid and process them for SQLite storage.

        Fetches transactions, applies AI categorization, and stores in SQLite canonical ledger.
        """
        user_id = config["configurable"]["user_id"]
        current_attempts = state.get("fetch_attempts", 0) + 1
        is_final_attempt = current_attempts >= 3
        logger.info(f"Fetching fresh transaction data from Plaid for user {user_id} (attempt {current_attempts}/3)")

        # Fetch transactions from Plaid via MCP tools
        transaction_result = await self._fetch_transactions(user_id)

        if transaction_result["status"] == "error":
            error_message = transaction_result.get('error', 'Unknown error')

            # Provide context-aware error messages based on attempt number
            if is_final_attempt:
                response_content = (
                    f"I've attempted to fetch your transaction data 3 times but encountered persistent issues: {error_message}. "
                    f"Please check your account connections in settings or try again later. "
                    f"If this continues, you may need to reconnect your financial accounts."
                )
            elif current_attempts == 1:
                response_content = f"Encountered a temporary issue fetching your transactions: {error_message}. Retrying..."
            else:
                response_content = f"Still having trouble fetching transactions (attempt {current_attempts}/3): {error_message}. Retrying..."

            logger.error(f"Transaction fetch failed for user {user_id} (attempt {current_attempts}/3): {error_message}")
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

                    # Store categorized transactions in SQLite (canonical transaction ledger)
                    sqlite_stored = 0
                    sqlite_duplicates = 0
                    sqlite_errors = 0
                    try:
                        # Convert PlaidTransactions to TransactionCreate objects
                        transaction_creates = [
                            self._convert_to_transaction_create(txn, user_id)
                            for txn in categorized_transactions
                        ]

                        # Batch store in SQLite
                        sqlite_result = await self._storage.batch_create_transactions(transaction_creates)
                        sqlite_stored = sqlite_result.get("stored", 0)
                        sqlite_duplicates = sqlite_result.get("duplicates", 0)
                        sqlite_errors = sqlite_result.get("errors", 0)

                        logger.info(f"SQLite storage: {sqlite_stored} new, {sqlite_duplicates} duplicates, {sqlite_errors} errors")
                    except Exception as sqlite_error:
                        logger.error(f"Failed to store transactions in SQLite: {sqlite_error}")
                        sqlite_errors = len(categorized_transactions)

                    # Generate success response
                    response_content = f"Successfully fetched {total_count} transactions, categorized {categorized_count} with AI insights, and stored {sqlite_stored} in database. Processing complete!"
                    logger.info(f"Fetched {total_count} transactions, categorized {categorized_count}, stored {sqlite_stored} for user {user_id}")
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
            "messages": [response],
            "fetch_attempts": current_attempts
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
        }

        try:
            # Create config with user_id for proper node access
            config = {
                "configurable": {
                    "user_id": user_id
                }
            }

            # Process through subgraph
            result = await self.graph.ainvoke(initial_state, config)

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
