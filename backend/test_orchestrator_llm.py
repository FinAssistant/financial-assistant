#! /usr/bin/env python3
"""
Tests Orchestrator agent using a real LLM (e.g., GPT-4) for integration testing.
This script is intended for integration testing and should be run only when the LLM service is accessible.
"""

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.ai.langgraph_config import LangGraphConfig
from app.services.llm_service import llm_factory


class TestOrchestratorLLM:
    @pytest.mark.asyncio
    @pytest.mark.parametrize('execution_number', range(10))
    async def test_orchestrator_routes_to_onboarding(self, execution_number):
        """
        Test that user messages get routed to Onboarding agent.
        """
        # Skip test if LLM is not available
        if not llm_factory.validate_configuration():
            pytest.skip("LLM not available - API key not configured")
        
        # Create LangGraphConfig with in-memory checkpointer
        memory_checkpointer = MemorySaver()
        langgraph_config = LangGraphConfig(checkpointer=memory_checkpointer)
        
        # First sentence from example-conversation.txt
        user_message = "Hello, I am Matteo a 39 yrs old Software Engineer in San Francisco, CA. I am married and I have a one year old kid. I am planning to save for a 5 months long trip."
        
        # Test data
        user_id = "test_user_matteo"
        session_id = "test_session_123"
        
        # Process the message through the orchestrator
        result = await langgraph_config.invoke_conversation(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id
        )
        
        # Validate that the message was routed to the Onboarding agent
        print(f"Orchestrator result: {result}")
        assert result is not None
        assert "agent" in result
        assert result["agent"] == "onboarding", f"Expected 'onboarding' agent, got '{result['agent']}'"