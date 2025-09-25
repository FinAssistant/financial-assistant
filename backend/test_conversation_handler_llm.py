#! /usr/bin/env python3
"""
Tests ConversationHandler using a real LLM (e.g., GPT-4) for integration testing.
This script is intended for integration testing and should be run only when the LLM service is accessible.
"""

from time import sleep
import pytest
from langgraph.checkpoint.memory import MemorySaver
from app.core.config import settings

from app.ai.orchestrator_agent import OrchestratorAgent
from app.services.llm_service import llm_factory


class TestConversationHandlerLLM:
    @pytest.mark.asyncio
    @pytest.mark.parametrize('execution_number', range(10))
    async def test_orchestrator_routes_to_onboarding(self, execution_number):
        """
        Test that user messages get routed to Onboarding agent.
        """
        # Skip test if LLM is not available
        if not llm_factory.validate_configuration():
            pytest.skip("LLM not available - API key not configured")
        
        # Create OrchestratorAgent with in-memory checkpointer
        memory_checkpointer = MemorySaver()
        orchestrator_agent = OrchestratorAgent(checkpointer=memory_checkpointer)
        
        # First sentence from example-conversation.txt
        user_message = "Hello, I am Matteo a 39 yrs old Software Engineer in San Francisco, CA. I am married and I have a one year old kid. I am planning to save for a 5 months long trip."
        
        # Test data
        user_id = "test_user_matteo"
        session_id = "test_session_123"
        
        # Process the message through the orchestrator
        result = await orchestrator_agent.invoke_conversation(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id
        )
        
        # Validate that the message was routed to the Onboarding agent
        print(f"ConversationHandler result: {result}")
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert last_message["agent"] == "onboarding", f"Expected 'onboarding' agent, got '{last_message['agent']}'"
        
        if settings.default_llm_provider == "google":
            # Sleep to avoid rate limiting (specifically with Gemini free tier)
            sleep(10)  