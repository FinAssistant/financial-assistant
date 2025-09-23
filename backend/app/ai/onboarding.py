from typing import Dict, Any, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START, add_messages
import logging
from app.services.llm_service import llm_factory
from app.core.database import user_storage
from .mcp_clients.graphiti_client import get_graphiti_client
from .mcp_clients.plaid_client import get_plaid_client


# Typed profile data model
class ExtractedProfileData(BaseModel):
    """Typed structure for profile data extraction."""

    age_range: Optional[str] = Field(None, description="Age range: under_18, 18_25, 26_35, 36_45, 46_55, 56_65, over_65")
    life_stage: Optional[str] = Field(None, description="Life stage: student, young_professional, early_career, established_career, family_building, peak_earning, pre_retirement, retirement, between_jobs")
    occupation_type: Optional[str] = Field(None, description="Job category: teacher, engineer, healthcare, unemployed, etc.")
    location_context: Optional[str] = Field(None, description="State/region with cost of living context")
    family_structure: Optional[str] = Field(None, description="Family structure: single_no_dependents, single_with_dependents, married_dual_income, married_single_income, married_no_income, etc.")
    marital_status: Optional[str] = Field(None, description="Marital status: single, married, divorced, widowed, domestic_partnership")
    total_dependents_count: Optional[int] = Field(None, description="Total number of dependents")
    children_count: Optional[int] = Field(None, description="Number of children")
    caregiving_responsibilities: Optional[str] = Field(None, description="Caregiving responsibilities: none, aging_parents, disabled_family_member, sandwich_generation")


# Structured output model for LLM responses
class ProfileDataExtraction(BaseModel):
    """Structured model for LLM to extract profile data from conversation."""

    def __init_subclass__(cls, **kwargs):
        """Configure model based on LLM provider."""
        super().__init_subclass__(**kwargs)
        from app.core.config import settings

        # Only use extra="forbid" for OpenAI structured output
        if settings.default_llm_provider == "openai":
            cls.model_config = ConfigDict(extra="forbid")
        else:
            cls.model_config = ConfigDict(extra="allow")

    extracted_data: ExtractedProfileData = Field(default_factory=ExtractedProfileData, description="Profile data extracted from user input")
    completion_status: str = Field(default="incomplete", description="Profile completion status: incomplete, complete")
    user_response: str = Field(description="Natural response to user - REQUIRED field, must always provide a helpful response")


class OnboardingState(BaseModel):
    """State for onboarding subgraph. Shares some fields with GlobalState."""
    # Shared with GlobalState
    messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Conversation messages with automatic LangGraph management"
    )
    profile_context: Optional[str] = Field(
        default=None,
        description="Cached user profile context string for LLM system prompts"
    )
    profile_context_timestamp: Optional[datetime] = Field(
        default=None,
        description="Timestamp when profile_context was last built"
    )
    
    # Internal onboarding state (NOT shared with GlobalState)
    current_step: str = Field(default="welcome", description="Current step in onboarding")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="User data collected so far")
    needs_database_update: bool = Field(default=False, description="Whether database needs updating")
    onboarding_complete: bool = Field(default=False, description="Internal flag for onboarding completion")




class OnboardingAgent:
    """
    OnboardingAgent handles user profile setup and completion.
    
    Implements a LangGraph subgraph for structured profile data collection.
    """
    
    def __init__(self):
        """Initialize the onboarding agent."""
        self._graph = None
        self.logger = logging.getLogger(__name__)
        self._plaid_client = get_plaid_client()
        self.logger.info("OnboardingAgent initialized")

    def _has_connected_accounts(self, user_id: str) -> bool:
        """Check if user has any connected accounts."""
        try:
            accounts_count = user_storage.get_connected_accounts_count(user_id)
            return accounts_count > 0
        except Exception as e:
            self.logger.warning(f"Failed to check connected accounts for user {user_id}: {e}")
            return False
    
    def _read_db(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Read user and personal context data from SQLite database."""
        user_id = config["configurable"]["user_id"]

        self.logger.info(f"Reading onboarding database for user {user_id}")
        
        try:
            # Get user data to check if user exists
            user_data = user_storage.get_user_by_id(user_id)
            if not user_data:
                return {
                    "collected_data": {},
                    "current_step": "welcome",
                    "messages": []  # Ensure messages field is updated
                }
            
            # Get structured personal context data
            personal_context = user_storage.get_personal_context(user_id)
            
            if personal_context:
                # Convert PersonalContextModel data to dict for collected_data
                collected_data = {
                    key: value for key, value in personal_context.items() 
                    if key not in ['user_id', 'created_at', 'updated_at'] and value is not None
                }
            else:
                # No personal context exists yet
                collected_data = {}
            
            return {
                "collected_data": collected_data,
                "current_step": "continue" if collected_data else "welcome"
                # Don't return empty messages - let LangGraph handle it
            }
        except Exception:
            # Log error and continue with empty state
            return {
                "collected_data": {},
                "current_step": "welcome"
                # Don't return empty messages - let LangGraph handle it
            }

    def _call_llm(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Call LLM to process user message and extract profile data."""
        llm = llm_factory.create_llm()
        
        # No tool binding for simplified workflow - memory storage handled in separate node

        self.logger.info(f"Onboarding LLM invoked with messages: {[msg.content for msg in state.messages]}")
        
        # Check if user has connected accounts
        user_id = config["configurable"]["user_id"]
        has_accounts = self._has_connected_accounts(user_id)

        # Build system prompt for structured data extraction
        account_guidance = "" if has_accounts else """

            IMPORTANT: After collecting demographic information, guide users to connect their bank accounts for personalized financial insights.
            This is essential for providing accurate spending analysis and budgeting advice."""

        system_prompt = f"""You are an onboarding assistant that extracts user profile information and provides helpful responses.

            Your job is to:
            1. Fill in any profile fields mentioned by the user
            2. Provide a natural, helpful response that guides them toward completing their profile
            3. After collecting demographic info, guide users to connect their bank accounts for personalized insights{account_guidance}

            PROFILE FIELDS (set to null if not mentioned):
            - age_range: under_18, 18_25, 26_35, 36_45, 46_55, 56_65, over_65
            - life_stage: student, young_professional, early_career, established_career, family_building, peak_earning, pre_retirement, retirement, between_jobs
            - occupation_type: job category (teacher, engineer, healthcare, unemployed, etc.)
            - location_context: state/region with cost of living
            - family_structure: single_no_dependents, single_with_dependents, married_dual_income, married_single_income, married_no_income
            - marital_status: single, married, divorced, widowed, domestic_partnership
            - total_dependents_count: integer count
            - children_count: integer count
            - caregiving_responsibilities: none, aging_parents, disabled_family_member, sandwich_generation

            Set completion_status to "complete" only when all 9 demographic fields are provided AND user has connected bank accounts.

            EXAMPLES:
            - "I'm 30, work as a nurse" → age_range: "26_35", occupation_type: "healthcare"
            - "I left my job" → occupation_type: "unemployed", life_stage: "between_jobs"
            - "I live in California with my spouse" → location_context: "California, high cost of living", marital_status: "married"

            Always provide a helpful user_response that acknowledges their input and guides next steps."""

        # Get current collected data context
        collected_context = f"Already collected: {state.collected_data}" if state.collected_data else "No data collected yet"
        
        # Filter out orchestrator routing decisions specifically
        filtered_messages = []
        for msg in state.messages:
            if isinstance(msg, AIMessage) and len(msg.content.strip()) <= 20 and msg.content.strip().upper() in ["ONBOARDING", "SMALLTALK", "INVESTMENT", "SPENDING"]:
                continue  # Skip orchestrator routing
            filtered_messages.append(msg)

        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content=collected_context)
        ] + filtered_messages  # Use filtered messages

        self.logger.info(f"Onboarding LLM messages: {[msg.content for msg in messages]}")
        
        # Use structured output with the ProfileDataExtraction model
        structured_llm = llm.with_structured_output(ProfileDataExtraction, method="function_calling")
        
        response = structured_llm.invoke(messages)

        self.logger.info(f"Onboarding LLM response: {response}")
        
        # Create AI message with natural response
        ai_message = AIMessage(
            content=response.user_response,
            additional_kwargs={"agent": "onboarding"}
        )
        
        # Merge extracted data with existing collected data
        updated_collected = dict(state.collected_data)
        # Convert ExtractedProfileData to dict, excluding None values
        extracted_dict = {k: v for k, v in response.extracted_data.model_dump().items() if v is not None}
        updated_collected.update(extracted_dict)

        # Determine true completion status (demographics + accounts)
        # DESIGN DECISION: LLM only checks demographic fields and returns completion_status="complete"
        # when all 9 fields are provided. Our business logic then adds the account requirement.
        # This separation keeps LLM focused on data extraction while business logic handles completion rules.
        demographic_complete = response.completion_status == "complete"
        has_accounts = self._has_connected_accounts(user_id)
        truly_complete = demographic_complete and has_accounts

        data =  {
            "messages": [ai_message],
            "collected_data": updated_collected,
            "needs_database_update": bool(extracted_dict),
            "onboarding_complete": truly_complete  # Override LLM completion with business logic
        }

        self.logger.info(f"Onboarding LLM response and collected data: {data}")

        return data

    async def _store_memory(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Explicitly store conversation in Graphiti after LLM processing."""
        user_id = config["configurable"]["user_id"]

        self.logger.info(f"Storing onboarding memory for user {user_id}")
        
        # Get the latest human message and AI response
        human_message = None
        ai_response = None
        
        for msg in reversed(state.messages):
            if isinstance(msg, AIMessage) and not ai_response:
                ai_response = msg.content
            elif isinstance(msg, HumanMessage) and not human_message:
                human_message = msg.content
                break
        
        if human_message and ai_response:
            # Use GraphitiMCPClient directly for guaranteed storage
            try:
                graphiti_client = await get_graphiti_client()
                self.logger.info(f"Storing onboarding memory for user {user_id}: {human_message}")
                await graphiti_client.add_episode(
                    user_id=user_id,
                    content=human_message,
                    context={"assistant_response": ai_response}, 
                    name="Onboarding Conversation",
                    source_description="onboarding_agent"
                )
                
                self.logger.info(f"Stored onboarding memory for user {user_id}")
            except Exception as e:
                self.logger.warning(f"Failed to store memory for user {user_id}: {e}")
                # Don't break flow - memory storage failure shouldn't stop onboarding
        else:
            self.logger.warning(f"Insufficient messages to store memory for user {user_id}")
        
        return {}  # No state changes needed

    def _update_db(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Update database with collected profile data."""

        user_id = config["configurable"]["user_id"]

        self.logger.info(f"Updating onboarding database for user {user_id}: needs_update={state.needs_database_update}, complete={state.onboarding_complete}, collected_data={state.collected_data}")

        # Always try to update if we have collected data - don't check flags
        # People's situations change (new kids, job changes, moves, etc.)
                
        try:
            # Filter collected_data to only include fields that exist in PersonalContextModel
            valid_fields = {
                'age_range', 'life_stage', 'occupation_type', 'location_context',
                'family_structure', 'marital_status', 'total_dependents_count', 
                'children_count', 'caregiving_responsibilities'
            }
            
            # Only include fields that are in the PersonalContextModel and have values
            filtered_data = {
                key: value for key, value in state.collected_data.items() 
                if key in valid_fields and value is not None
            }
            
            if filtered_data:
                self.logger.info(f"Saving filtered data to database for user {user_id}: {filtered_data}")
                # Save to structured PersonalContextModel table
                user_storage.create_or_update_personal_context(user_id, filtered_data)
            else:
                self.logger.info(f"No valid data to save for user {user_id}")
            
            # Update PersonalContext.is_complete as single source of truth for completion state
            # This consolidates both demographic completion and account connection status
            completion_update = {'is_complete': state.onboarding_complete}
            user_storage.create_or_update_personal_context(user_id, completion_update)
            self.logger.info(f"Updated PersonalContext.is_complete={state.onboarding_complete} for user {user_id}")

            # DEPRECATED: Update user's profile_complete flag for backward compatibility only
            # TODO: Remove User.profile_complete field entirely - PersonalContext.is_complete is the single source of truth
            if state.onboarding_complete:
                user_storage.update_user(user_id, {"profile_complete": True})
                self.logger.info(f"DEPRECATED: Updated User.profile_complete for backward compatibility")
            
            return {"needs_database_update": False}
            
        except Exception:
            # Log error but don't break the flow
            self.logger.error(f"Failed to update database for user {user_id} with data {state.collected_data}")
            return {"needs_database_update": False}

    def _update_main_graph(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Update shared fields with GlobalState when onboarding is complete."""
        if not state.onboarding_complete:
            return {"onboarding_complete": False}  # Still need to return a valid state field
        
        # Build profile context string from collected data
        context_parts = []
        
        if state.collected_data.get("age_range"):
            context_parts.append(f"Age range: {state.collected_data['age_range']}")
        
        if state.collected_data.get("life_stage"):
            context_parts.append(f"Life stage: {state.collected_data['life_stage']}")
        
        if state.collected_data.get("occupation_type"):
            context_parts.append(f"Occupation: {state.collected_data['occupation_type']}")
        
        if state.collected_data.get("location_context"):
            context_parts.append(f"Location: {state.collected_data['location_context']}")
        
        if state.collected_data.get("family_structure"):
            context_parts.append(f"Family structure: {state.collected_data['family_structure']}")
        
        if state.collected_data.get("marital_status"):
            context_parts.append(f"Marital status: {state.collected_data['marital_status']}")
        
        if state.collected_data.get("total_dependents_count", 0) > 0:
            context_parts.append(f"Has {state.collected_data['total_dependents_count']} dependents")
        
        if state.collected_data.get("caregiving_responsibilities") and state.collected_data["caregiving_responsibilities"] != "none":
            context_parts.append(f"Caregiving: {state.collected_data['caregiving_responsibilities']}")
        
        # Build profile context
        profile_context = f"User profile: {'; '.join(context_parts)}." if context_parts else None
        
        return {
            "profile_context": profile_context,
            "profile_context_timestamp": datetime.now()
        }

    def _check_all_fields_present(self, collected_data: Dict[str, Any]) -> bool:
        """Check if all 9 required fields are present and not None."""
        required_fields = {
            'age_range', 'life_stage', 'occupation_type', 'location_context',
            'family_structure', 'marital_status', 'total_dependents_count', 
            'children_count', 'caregiving_responsibilities'
        }
        
        for field in required_fields:
            if field not in collected_data or collected_data[field] is None or collected_data[field] == '':
                return False
        return True

    def _check_profile_complete(self, state: OnboardingState) -> str:
        """Check if profile is complete and route accordingly."""
        if state.onboarding_complete:
            return "update_global_state"
        else:
            return "end"
    
    def _should_use_tools(self, state: OnboardingState) -> str:
        """Determine if the LLM wants to use tools based on the last message."""
        last_message = state.messages[-1]
        
        # Check if the LLM made tool calls
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            self.logger.info("LLM requested tool usage")
            return "tools"
        else:
            return "update_database"
    
    def graph_compile(self) -> StateGraph:
        """Compile and return the onboarding subgraph."""
        if self._graph is None:
            onb_builder = StateGraph(OnboardingState)
            
            # Add nodes - simplified linear workflow
            onb_builder.add_node("read_database", self._read_db)
            onb_builder.add_node("call_llm", self._call_llm)
            onb_builder.add_node("store_memory", self._store_memory)
            onb_builder.add_node("update_database", self._update_db)
            onb_builder.add_node("update_global_state", self._update_main_graph)

            # Add linear edges - ReadDB -> Call LLM -> Store Memory -> Update DB -> Update Global -> END
            onb_builder.add_edge(START, "read_database")
            onb_builder.add_edge("read_database", "call_llm")
            onb_builder.add_edge("call_llm", "store_memory")
            onb_builder.add_edge("store_memory", "update_database")            
            onb_builder.add_edge("update_database", "update_global_state")
            onb_builder.add_edge("update_global_state", END)

            self._graph = onb_builder.compile()
        
        return self._graph

    


def create_onboarding_node():
    """Factory function to create onboarding node for LangGraph integration."""
    return OnboardingAgent()