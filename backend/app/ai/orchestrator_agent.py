from typing import Dict, Any, Optional, List, Annotated
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.core.config import settings
from app.services.llm_service import llm_factory
from app.core.database import user_storage
from .onboarding import create_onboarding_node
from .spending_agent import SpendingAgent

class GlobalState(BaseModel):
    """
    GlobalState model for shared agent context across LangGraph workflow.
    
    Contains conversation history and shared data for agent coordination.
    User/session context is passed via config, not stored in state.
    """
    
    # Messages (LangGraph standard pattern)
    messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Conversation messages with automatic LangGraph management"
    )
    
    # Shared Data (lightweight references for conversation context)
    connected_account_ids: List[str] = Field(
        default_factory=list,
        description="List of connected account IDs for conversation context"
    )
    
    # Profile context (lazy-loaded and cached)
    profile_context: Optional[str] = Field(
        default=None,
        description="Cached user profile context string for LLM system prompts"
    )
    profile_context_timestamp: Optional[datetime] = Field(
        default=None,
        description="Timestamp when profile_context was last built"
    )
    profile_complete: bool = Field(
        default=False,
        description="Whether the user has completed their profile setup"
    )
    
    
    def get_profile_context(self, user_id: str) -> str:
        """
        Get profile context string, building it if empty or stale.
        This method is called during graph runs to ensure fresh context.
        Now takes user_id as parameter since it's not in state.
        """
        if self.profile_context is None:
            self._build_profile_context(user_id)
        return self.profile_context or "User profile not available."
    
    def _build_profile_context(self, user_id: str) -> None:
        """
        Build profile context string from database and cache it.
        Called when profile_context is None or needs refresh.
        Now takes user_id as parameter since it's not in state.
        """
        try:
            # Get structured personal context data (single source of truth for completion)
            personal_context = user_storage.get_personal_context(user_id)

            # Check completion status from PersonalContext.is_complete (not deprecated User.profile_complete)
            is_complete = personal_context.get("is_complete", False) if personal_context else False

            # Update GlobalState profile_complete to match authoritative source
            self.profile_complete = is_complete

            # Build context from PersonalContextModel even if not complete (partial demographic data is still useful)
            if personal_context:
                # Build context from PersonalContextModel
                context_parts = []
                
                if personal_context.get("age_range"):
                    context_parts.append(f"Age range: {personal_context['age_range']}")
                
                if personal_context.get("life_stage"):
                    context_parts.append(f"Life stage: {personal_context['life_stage']}")
                
                if personal_context.get("occupation_type"):
                    context_parts.append(f"Occupation: {personal_context['occupation_type']}")
                
                if personal_context.get("location_context"):
                    context_parts.append(f"Location: {personal_context['location_context']}")
                
                if personal_context.get("family_structure"):
                    context_parts.append(f"Family structure: {personal_context['family_structure']}")
                
                if personal_context.get("marital_status"):
                    context_parts.append(f"Marital status: {personal_context['marital_status']}")
                
                if personal_context.get("total_dependents_count", 0) > 0:
                    context_parts.append(f"Has {personal_context['total_dependents_count']} dependents")
                
                if personal_context.get("caregiving_responsibilities") and personal_context["caregiving_responsibilities"] != "none":
                    context_parts.append(f"Caregiving: {personal_context['caregiving_responsibilities']}")
                
                # Build final context string
                if context_parts:
                    self.profile_context = f"User profile: {'; '.join(context_parts)}."
                else:
                    self.profile_context = "User profile is incomplete. Provide general financial guidance."
            else:
                # No PersonalContext exists yet
                self.profile_context = "User profile is incomplete. Provide general financial guidance."
                
            self.profile_context_timestamp = datetime.now()
                
        except Exception:
            # Log error but don't break the conversation flow
            self.profile_context = "Unable to load user profile. Provide general financial guidance."
            self.profile_context_timestamp = datetime.now()
    
    def check_and_refresh_profile_context(self, user_id: str) -> bool:
        """
        Check if profile context needs refresh based on database changes.
        Returns True if context was refreshed, False if no changes.
        Call this at the end of graph runs to prepare for next run.
        Now takes user_id as parameter since it's not in state.
        """
        if self.profile_context_timestamp is None:
            # No context built yet, will be built on next get_profile_context()
            return False

        try:
            # Check PersonalContext updates (authoritative source for completion status)
            personal_context = user_storage.get_personal_context(user_id)
            if personal_context:
                personal_updated_at = personal_context.get("updated_at")
                if personal_updated_at and isinstance(personal_updated_at, datetime):
                    if personal_updated_at > self.profile_context_timestamp:
                        # PersonalContext has been updated, rebuild context
                        self._build_profile_context(user_id)
                        return True

            # Also check user data for any other updates
            user_data = user_storage.get_user_by_id(user_id)
            if user_data:
                user_updated_at = user_data.get("updated_at")
                if user_updated_at and isinstance(user_updated_at, datetime):
                    if user_updated_at > self.profile_context_timestamp:
                        # User data has been updated, rebuild context
                        self._build_profile_context(user_id)
                        return True

            return False

        except Exception:
            # If we can't check, assume no changes
            return False

    def refresh_connected_accounts(self, user_id: str) -> None:
        """
        Refresh connected account IDs from database.
        Called when accounts are added/removed to keep conversation context current.
        """
        try:
            accounts = user_storage.get_accounts_for_conversation_context(user_id)
            self.connected_account_ids = [account['id'] for account in accounts]
        except Exception:
            # Log error but don't break conversation flow
            self.connected_account_ids = []

    def has_connected_accounts(self, user_id: str) -> bool:
        """
        Check if user has any connected accounts.
        Refreshes account list if empty to ensure current data.
        """
        if not self.connected_account_ids:
            self.refresh_connected_accounts(user_id)
        return len(self.connected_account_ids) > 0



class OrchestratorAgent:
    """
    Orchestrator agent that manages conversation routing and workflow coordination.

    Contains the actual routing logic and manages the LangGraph workflow
    using GlobalState for cross-agent data sharing.
    """
    
    def __init__(self, checkpointer: Optional[AsyncSqliteSaver] = None):
        """Initialize LangGraph configuration."""
        self.logger = logging.getLogger(__name__)
        self.checkpointer = checkpointer
        self.graph = None
        self.compiled_graph = None

        self.onb_agent = create_onboarding_node()
        self.spending_agent = SpendingAgent()
        self._setup_graph()
        self.llm = llm_factory.create_llm()

        if self.llm is None:
            self.logger.warning("LLM not available - no API key configured. Graph will fail on LLM calls.")
    
    
    
    def _setup_graph(self) -> None:
        """
        Create and configure the conversation graph with GlobalState.
        This is the main graph, whose main functionality is routing/orchestration.
        TODO: requires a message summarization element 
        """
        workflow = StateGraph(GlobalState)
        
        # Add the nodes
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("small_talk", self._small_talk_node) #TODO: wrap small_talk into orch llm call
        workflow.add_node("Investment_Agent", self._dummy_inv_agent) #TODO:replace with subgraph
        workflow.add_node("Spending_Agent", self.spending_agent.graph_compile())
        workflow.add_node("Onboarding_Agent", self.onb_agent.graph_compile())

        
        # Define the graph flow
        workflow.add_edge(START, "orchestrator")
        
        workflow.add_conditional_edges(
            "orchestrator",
            self.find_route,
            {"SMALLTALK": "small_talk", 
             "INVESTMENT" : "Investment_Agent",
             "SPENDING" : "Spending_Agent",
             "ONBOARDING": "Onboarding_Agent" }
        )
        
        workflow.add_edge("small_talk", END)
        workflow.add_edge("Investment_Agent", END)
        workflow.add_edge("Spending_Agent", END)
        workflow.add_edge("Onboarding_Agent", END)


        # Compile the graph with checkpointer if available
        try:
            if self.checkpointer:
                self.graph = workflow.compile(checkpointer=self.checkpointer)
                self.logger.info("Graph compiled with SQLite checkpointer")
            else:
                self.graph = workflow.compile()
                self.logger.info("Graph compiled without checkpointer")
        except Exception as e:
            self.logger.error(f"Failed to compile graph: {e}")
            raise
    
    def _orchestrator_node(self, state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Orchestrator that uses user profile context from config.
        Demonstrates proper LangGraph pattern with config usage.
        """
        # Get user context from config (standard LangGraph pattern)
        user_id = config["configurable"]["user_id"]

        # Get profile context (lazy loaded and cached) - this also updates state.profile_complete
        profile_context = state.get_profile_context(user_id)

        # Build consolidated system prompt with all context
        profile_status = "COMPLETE" if state.profile_complete else "INCOMPLETE"
        profile_info = state.profile_context if state.profile_complete and state.profile_context else "No profile information available"

        self.logger.debug(f"Orchestrator: User profile status: {profile_status}")
        self.logger.debug(f"Orchestrator: User profile context: {profile_info}")
        self.logger.debug(f"Orchestrator: Full profile context: {profile_context}")

        system_prompt = f"""You are an Orchestrator for a financial assistant agent.
Your job is to analyze the input query and choose exactly one of 4 routing options.

USER PROFILE STATUS: {profile_status}
USER PROFILE: {profile_info}

ROUTING RULES:

1. ONBOARDING:  
   - If the user profile is INCOMPLETE, ALWAYS route to ONBOARDING.
   - If the user input contains any information about their personal situation, demographics, geography, occupation, age, family, or financial goals, ALWAYS route to ONBOARDING,  regardless of whether the profile is COMPLETE or INCOMPLETE.  

2. SPENDING:  
   - If the user profile is COMPLETE and the query is about:  
     - Budgeting, expenses, spending tracking  
     - Account balances, transactions  
     - Personal finance management (non-investment)  
     - Financial planning and cash flow  

3. INVESTMENT:  
   - If the user profile is COMPLETE and the query is about:  
     - Investment strategies, portfolio management  
     - Stocks, bonds, mutual funds, ETFs  
     - Retirement planning, 401k, IRA  
     - Asset allocation and investment advice  

4. SMALLTALK (catch-all):  
   - If none of the above rules apply and the input is purely casual (greetings, goodbyes, jokes, unrelated chit-chat), choose SMALLTALK.  

CRITICAL:  
You must respond with exactly ONE word: SMALLTALK, SPENDING, INVESTMENT, or ONBOARDING.  

Examples:  
- "Hello!" → SMALLTALK  
- "I am 35 and want to start saving for a vacation." → ONBOARDING  
- "How should I budget?" (profile incomplete) → ONBOARDING  
- "How should I budget?" (profile complete) → SPENDING  
- "What stocks should I buy?" (profile incomplete) → ONBOARDING  
- "What stocks should I buy?" (profile complete) → INVESTMENT  
"""

        messages = [SystemMessage(content=system_prompt)] + state.messages

        if self.llm is None:
            from app.services.llm_service import LLMError
            raise LLMError("LLM not available - API key not configured")
            
        response = self.llm.invoke(messages)

        self.logger.info(f"Orchestrator: LLM response for routing decision: {response.content}")
        
        # Update state with new message
        return {
            "messages": [response]
        }
    
    def _small_talk_node(self, state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
        """LLM-powered small talk agent for casual conversation."""

        system_prompt = """You are a friendly AI financial assistant engaging in small talk.
        Be warm, conversational, and personable. If the user's profile is incomplete, 
        gently nudge them to complete it for better personalized advice. 
        Otherwise, naturally steer toward how you can help with their financial needs 
        when appropriate.

        Keep responses friendly, brief, and engaging."""

        # Use existing messages from state and add system prompt at the beginning
        messages = [SystemMessage(content=system_prompt)] + state.messages
        
        # Call LLM and add agent metadata
        if self.llm is None:
            from app.services.llm_service import LLMError
            raise LLMError("LLM not available - API key not configured")
            
        response = self.llm.invoke(messages)
        response.additional_kwargs["agent"] = "small_talk"
        
        return {"messages": [response]}
    
    def _dummy_inv_agent(self, state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
        """Dummy investment agent - placeholder implementation."""
        response = AIMessage(
            content="I can help with investment questions, but this feature is still being developed. Please check back soon!",
            additional_kwargs={"agent": "investment"}
        )
        return {"messages": [response]}
    
    def _dummy_spend_agent(self, state: GlobalState, config: RunnableConfig) -> Dict[str, Any]:
        """Dummy spending agent - placeholder implementation."""
        response = AIMessage(
            content="I can help analyze your spending patterns, but this feature is still being developed. Please check back soon!",
            additional_kwargs={"agent": "spending"}
        )
        return {"messages": [response]}
    
    def find_route(self, state: GlobalState):
        last_message = state.messages[-1]
        self.logger.debug(f"Orchestrator: Last result from LLM : {last_message.content}")

        # Handle case where LLM returns a list instead of a string
        content = last_message.content
        if isinstance(content, list):
            # If it's a list, take the first element which should be the route
            if len(content) > 0:
                destination = str(content[0]).strip().upper()
                self.logger.warning(f"LLM returned list instead of string. Using first element: {destination}")
            else:
                self.logger.error("LLM returned empty list. Defaulting to SMALLTALK")
                destination = "SMALLTALK"
        else:
            # Normal case - content is a string
            destination = content.strip().upper()

        # Validate that we got a proper routing decision
        valid_routes = {"SMALLTALK", "SPENDING", "INVESTMENT", "ONBOARDING"}
        if destination not in valid_routes:
            self.logger.warning(f"Invalid routing decision: '{destination}'. Defaulting to SMALLTALK for safety")
            # Default to small talk for graceful degradation
            destination = "SMALLTALK"

        return destination
    
    async def invoke_conversation(self, user_message: str, user_id: str, session_id: str) -> dict:
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
        
        # Prepare config with user context (standard LangGraph pattern)
        config = {
            "configurable": {
                "thread_id": session_id,
                "user_id": user_id
            }
        }
        
        # Input data - just the new message (LangGraph + checkpointer handle state)
        input_data = {
            "messages": [HumanMessage(content=user_message)]
        }

        self.logger.info(f"Invoking graph for user_id={user_id}, session_id={session_id} with message: {user_message}")

        # Process through graph - checkpointer automatically manages state persistence
        result = await self.graph.ainvoke(input_data, config)
        
        # Extract AI messages that were generated after the last user message
        all_messages = result["messages"]

        # Find the last user message index
        last_user_message_idx = -1
        for i in reversed(range(len(all_messages))):
            if isinstance(all_messages[i], HumanMessage):
                last_user_message_idx = i
                break

        # Get all AI messages and tool messages after the last user message
        ai_messages = []
        for msg in all_messages[last_user_message_idx + 1:]:
            if isinstance(msg, (AIMessage, ToolMessage)):
                ai_messages.append(msg)

        # Fallback: if no AI/Tool messages found after user message, return all remaining messages
        if not ai_messages and all_messages and last_user_message_idx >= 0:
            ai_messages = all_messages[last_user_message_idx + 1:]

        # Simple message formatting for non-streaming responses
        processed_messages = [{
            "content": msg.content,
            "agent": msg.additional_kwargs.get("agent", "orchestrator"),
            "message_type": "tool_response" if isinstance(msg, ToolMessage) else "ai_response"
        } for msg in ai_messages]

        return {
            "messages": processed_messages,
            "session_id": session_id,
            "user_id": user_id
        }
    
    def stream_conversation(self, user_message: str, user_id: str, session_id: str):
        """
        Stream a conversation through the graph for real-time responses.
        
        Args:
            user_message: The user's input message
            user_id: Unique identifier for the user  
            session_id: Unique identifier for the conversation session
            
        Yields:
            Streaming conversation updates
        """
        if not self.graph:
            raise RuntimeError("Graph not initialized")
        
        
        # Prepare config with user context (standard LangGraph pattern)
        config = {
            "configurable": {
                "thread_id": session_id,
                "user_id": user_id
            }
        }
        
        # Input data - just the new message (LangGraph + checkpointer handle state)
        input_data = {
            "messages": [HumanMessage(content=user_message)]
        }
        
        # Stream through graph - checkpointer automatically manages state persistence
        for chunk in self.graph.stream(input_data, config):
            yield chunk
    
    def validate_configuration(self) -> bool:
        """Validate LangGraph configuration."""
        try:
            # Check if LLM factory is working
            if not llm_factory.validate_configuration():
                return False
            
            # Check if graph is compiled
            if not self.graph:
                return False
            
            self.logger.info("LangGraph configuration validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"LangGraph configuration validation failed: {e}")
            return False


# Global instance
_langgraph_config = None
_checkpointer = None
_checkpointer_context = None


async def setup_checkpointer() -> Optional[AsyncSqliteSaver]:
    """Setup AsyncSqliteSaver during FastAPI startup."""
    global _checkpointer, _checkpointer_context
    
    if settings.langgraph_memory_type == "sqlite":
        try:
            # Create AsyncSqliteSaver from connection string and enter context
            _checkpointer_context = AsyncSqliteSaver.from_conn_string(settings.langgraph_db_path)
            _checkpointer = await _checkpointer_context.__aenter__()
            logging.getLogger(__name__).info(f"AsyncSqliteSaver initialized at {settings.langgraph_db_path}")
            return _checkpointer
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to initialize AsyncSqliteSaver: {e}")
            logging.getLogger(__name__).info("Falling back to in-memory conversation storage")
            _checkpointer = None
            _checkpointer_context = None
            return None
    else:
        logging.getLogger(__name__).info("Using in-memory conversation storage")
        return None


async def cleanup_checkpointer() -> None:
    """Cleanup AsyncSqliteSaver during FastAPI shutdown."""
    global _checkpointer, _checkpointer_context
    if _checkpointer_context:
        try:
            await _checkpointer_context.__aexit__(None, None, None)
            logging.getLogger(__name__).info("AsyncSqliteSaver cleaned up")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error cleaning up AsyncSqliteSaver: {e}")
        finally:
            _checkpointer = None
            _checkpointer_context = None

def get_orchestrator_agent() -> OrchestratorAgent:
    """Get or create the global orchestrator agent instance."""
    logging.getLogger(__name__).info("Getting LangGraph configuration")
    global _langgraph_config, _checkpointer
    if _langgraph_config is None:
        _langgraph_config = OrchestratorAgent(checkpointer=_checkpointer)
    return _langgraph_config