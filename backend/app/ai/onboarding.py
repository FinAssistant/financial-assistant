from typing import Dict, Any, Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AnyMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START, add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from app.services.llm_service import llm_factory
from app.core.database import user_storage
from app.core.sqlmodel_models import (
    UserModel, PersonalContextModel, PersonalContextCreate, PersonalContextUpdate,
    FamilyStructure, EducationLevel, CaregivingResponsibility
)


# Structured output model for LLM responses
class ProfileDataExtraction(BaseModel):
    """Structured model for LLM to extract profile data from conversation."""
    model_config = ConfigDict(extra="forbid")  # Required for OpenAI structured output
    
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Profile data extracted from user input")
    next_questions: list[str] = Field(default_factory=list, description="Follow-up questions to ask user")
    completion_status: str = Field(default="incomplete", description="Profile completion status: incomplete, partial, complete")
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
    
    def _read_db(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Read user and personal context data from SQLite database."""
        user_id = config["configurable"]["user_id"]
        
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
        except Exception as e:
            # Log error and continue with empty state
            return {
                "collected_data": {},
                "current_step": "welcome"
                # Don't return empty messages - let LangGraph handle it
            }

    def _call_llm(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Call LLM to process user message and extract profile data."""
        llm = llm_factory.create_llm()
        
        # Build system prompt for structured data extraction
        system_prompt = """You are an onboarding assistant with TWO important jobs:
        1. Extract profile data from user messages into the extracted_data field
        2. Generate a helpful response to the user in the user_response field

        CRITICAL REQUIREMENTS:
        - ALWAYS provide a helpful, natural response to the user in user_response field
        - Extract ANY profile data mentioned by the user into the extracted_data field
        - NEVER echo or repeat the user's message - always generate your own response

        Extract these exact fields when mentioned:
        - age_range: under_18, 18_25, 26_35, 36_45, 46_55, 56_65, over_65
        - life_stage: student, young_professional, early_career, established_career, family_building, peak_earning, pre_retirement, retirement  
        - occupation_type: job category (teacher, engineer, healthcare, etc.)
        - location_context: state/region with cost of living
        - family_structure: single_no_dependents, single_with_dependents, married_dual_income, etc.
        - marital_status: single, married, divorced, widowed, domestic_partnership
        - total_dependents_count: number (integer)
        - children_count: number (integer) 
        - caregiving_responsibilities: none, aging_parents, disabled_family_member, sandwich_generation

        EXTRACTION EXAMPLES:
        - Age "25" or "18-25" → "age_range": "18_25"
        - Job "teacher" → "occupation_type": "teacher" 
        - Job "software engineer" → "occupation_type": "engineer"
        - Location "California" → "location_context": "California, high cost of living"
        - "married" → "marital_status": "married"
        - "two kids" → "children_count": 2
        - "caring for elderly parents" → "caregiving_responsibilities": "aging_parents"

        Extract data when present. Set completion_status to "complete" when you have all 9 fields.
        
        EXAMPLES:
        
        Example 1 - User provides profile data:
        User: "I'm 30 years old, work as a nurse in Florida, single with no kids"
        Response: {
          "extracted_data": {
            "age_range": "26_35",
            "life_stage": "early_career", 
            "occupation_type": "healthcare",
            "location_context": "Florida, moderate cost of living",
            "family_structure": "single_no_dependents",
            "marital_status": "single",
            "total_dependents_count": 0,
            "children_count": 0,
            "caregiving_responsibilities": "none"
          },
          "completion_status": "complete",
          "user_response": "Your profile is now complete! Our financial advisors can help with your specific needs."
        }
        
        Example 2 - User asks question but provides NO profile data:
        User: "How should I invest my money?"
        Response: {
          "extracted_data": {},
          "completion_status": "incomplete",
          "user_response": "I'd be happy to help with investment advice! First, I need to understand your personal situation. Could you tell me your age range and occupation?"
        }
        
        REMEMBER: Always provide a helpful user_response. Never echo the user's message."""
        
        # Get current collected data context
        collected_context = f"Already collected: {state.collected_data}" if state.collected_data else "No data collected yet"
        
        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content=collected_context)
        ] + state.messages[:-1]  # Exclude last message (orchestrator routing decision)
        
        # Use structured output with the ProfileDataExtraction model
        structured_llm = llm.with_structured_output(ProfileDataExtraction, method="function_calling")
        
        response = structured_llm.invoke(messages)
        
        # Create AI message with natural response
        ai_message = AIMessage(
            content=response.user_response,
            additional_kwargs={"agent": "onboarding"}
        )
        
        # Merge extracted data with existing collected data
        updated_collected = dict(state.collected_data)
        updated_collected.update(response.extracted_data)
        
        
        return {
            "messages": [ai_message],
            "collected_data": updated_collected,
            "needs_database_update": bool(response.extracted_data),
            "onboarding_complete": response.completion_status == "complete"
        }

    def _update_db(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Update database with collected profile data."""
        if not state.needs_database_update and not state.onboarding_complete:
            return {"needs_database_update": False}  # Still need to return a valid state field
        
        user_id = config["configurable"]["user_id"]
        
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
                # Save to structured PersonalContextModel table
                user_storage.create_or_update_personal_context(user_id, filtered_data)
            
            # Update user's profile_complete flag if onboarding is complete
            if state.onboarding_complete:
                user_storage.update_user(user_id, {"profile_complete": True})
            
            return {"needs_database_update": False}
            
        except Exception as e:
            # Log error but don't break the flow
            return {"needs_database_update": False}

    def _update_main_graph(self, state: OnboardingState, config: RunnableConfig) -> Dict[str, Any]:
        """Update shared fields with GlobalState when onboarding is complete."""
        if not state.onboarding_complete:
            return {"onboarding_complete": False}  # Still need to return a valid state field
        
        user_id = config["configurable"]["user_id"]
        
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
    
    def graph_compile(self) -> StateGraph:
        """Compile and return the onboarding subgraph."""
        if self._graph is None:
            onb_builder = StateGraph(OnboardingState)
            
            # Add nodes
            onb_builder.add_node("read_database", self._read_db)
            onb_builder.add_node("call_llm", self._call_llm)
            onb_builder.add_node("update_database", self._update_db)
            onb_builder.add_node("update_global_state", self._update_main_graph)

            # Add edges - always update database first, then check completion
            onb_builder.add_edge(START, "read_database")
            onb_builder.add_edge("read_database", "call_llm")
            onb_builder.add_edge("call_llm", "update_database")  # Always update DB first
            onb_builder.add_conditional_edges(
                "update_database",  # Check completion AFTER database update
                self._check_profile_complete, 
                {"update_global_state": "update_global_state", "end": END}
            )
            onb_builder.add_edge("update_global_state", END)

            self._graph = onb_builder.compile()
        
        return self._graph

    


def create_onboarding_node():
    """Factory function to create onboarding node for LangGraph integration."""
    return OnboardingAgent()