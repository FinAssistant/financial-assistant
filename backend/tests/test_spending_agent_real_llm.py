"""
Real LLM integration tests for SpendingAgent.
These tests are SKIPPED in CI and only run locally when:
1. At least one LLM provider API key is available (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)
2. RUN_REAL_TESTS environment variable is set to 'true'

To run these tests locally:
# Test with OpenAI (default)
export RUN_REAL_TESTS=true
export OPENAI_API_KEY=sk-your-openai-key-here
pytest tests/test_spending_agent_real_llm.py -v

# Test with Anthropic Claude
export RUN_REAL_TESTS=true
export DEFAULT_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
pytest tests/test_spending_agent_real_llm.py -v

# Test with Google Gemini
export RUN_REAL_TESTS=true
export DEFAULT_LLM_PROVIDER=google
export GOOGLE_API_KEY=your-google-api-key-here
pytest tests/test_spending_agent_real_llm.py -v
"""
import pytest
import os
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage

from app.ai.spending_agent import SpendingAgent
from app.services.llm_service import LLMFactory, LLMProvider


# Skip entire module if conditions not met (same logic as test_integration_real_api.py)
def has_any_llm_key():
    """Check if any LLM provider API key is available."""
    return any([
        os.getenv('OPENAI_API_KEY'),
        os.getenv('ANTHROPIC_API_KEY'), 
        os.getenv('GOOGLE_API_KEY')
    ])

pytestmark = pytest.mark.skipif(
    not has_any_llm_key() or os.getenv('RUN_REAL_TESTS') != 'true',
    reason="Real API tests require at least one LLM provider API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY) and RUN_REAL_TESTS=true"
)


@pytest.fixture(autouse=True)
def mock_llm_factory():
    """Override the global mock_llm_factory fixture to allow real LLM calls."""
    # This autouse fixture with the same name overrides the conftest.py one
    # and does nothing, allowing real LLM calls to work
    yield None


class TestSpendingAgentRealLLM:
    """Integration tests for SpendingAgent with real LLM API calls."""
    
    def setup_method(self):
        """Setup method called before each test."""
        # Ensure no mocking interferes with real LLM calls
        with patch.object(SpendingAgent, '__init__', lambda _: None):
            # Create agent with real LLM (bypass any potential mocking)
            self.agent = SpendingAgent()
            self.agent._user_context_dao = None  # Not needed for intent tests
            self.agent._auth_service = None      # Not needed for intent tests
            self.agent._mcp_clients = {}
            
            # Initialize real LLM
            self.agent.llm = LLMFactory().create_llm()
    
    def test_real_llm_intent_detection_spending_analysis(self):
        """Test real LLM detects spending analysis intent correctly."""
        test_cases = [
            "Tell me about my spending patterns this month",
            "I want to analyze my expenses",
            "Can you help me understand my spending habits?",
            "What are my biggest expense categories?"
        ]
        
        for user_message in test_cases:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {
                    "demographics": {"age_range": "26_35", "occupation": "engineer"},
                    "financial_context": {"has_dependents": False}
                }
            }
            
            result = self.agent._route_intent_node(state)
            
            assert "detected_intent" in result
            # Real LLM should correctly identify spending analysis intent
            assert result["detected_intent"] == "spending_analysis"
            print(f"✅ Correctly detected 'spending_analysis' for: '{user_message}'")
    
    def test_real_llm_intent_detection_budget_planning(self):
        """Test real LLM detects budget planning intent correctly."""
        test_cases = [
            "Help me create a monthly budget",
            "I need assistance with budgeting",
            "Can you help me plan my finances?",
            "I want to set up a budget for my household",
            "How do I create a budget that works?"
        ]
        
        for user_message in test_cases:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {
                    "demographics": {"age_range": "36_45", "occupation": "teacher"},
                    "financial_context": {"has_dependents": True}
                }
            }
            
            result = self.agent._route_intent_node(state)
            
            assert "detected_intent" in result
            assert result["detected_intent"] == "budget_planning"
            print(f"✅ Correctly detected 'budget_planning' for: '{user_message}'")
    
    def test_real_llm_intent_detection_optimization(self):
        """Test real LLM detects optimization intent correctly."""
        test_cases = [
            "How can I save money on my monthly expenses?",
            "I want to reduce my spending",
            "Help me optimize my costs",
            "What are some ways to cut expenses?",
            "I need to find areas where I can save money"
        ]
        
        for user_message in test_cases:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {
                    "demographics": {"age_range": "18_25", "occupation": "student"},
                    "financial_context": {"has_dependents": False}
                }
            }
            
            result = self.agent._route_intent_node(state)
            
            assert "detected_intent" in result
            assert result["detected_intent"] == "optimization"
            print(f"✅ Correctly detected 'optimization' for: '{user_message}'")
    
    def test_real_llm_intent_detection_transaction_query(self):
        """Test real LLM detects transaction query intent correctly."""
        test_cases = [
            "Find my transaction from yesterday",
            "Show me my purchases from last week",
            "I'm looking for a specific transaction",
            "What did I buy at Target last month?",
            "Can you find my Amazon purchases?"
        ]
        
        for user_message in test_cases:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {
                    "demographics": {"age_range": "46_55", "occupation": "manager"},
                    "financial_context": {"has_dependents": True}
                }
            }
            
            result = self.agent._route_intent_node(state)
            
            assert "detected_intent" in result
            assert result["detected_intent"] == "transaction_query"
            print(f"✅ Correctly detected 'transaction_query' for: '{user_message}'")
    
    def test_real_llm_intent_detection_general_spending(self):
        """Test real LLM detects general spending intent correctly."""
        test_cases = [
            "Hello, I need help with my finances",
            "Hi there, what can you help me with?",
            "I'm new here, what services do you provide?",
            "Can you tell me about financial planning?",
            "What kind of financial advice can you give me?"
        ]
        
        for user_message in test_cases:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {
                    "demographics": {"age_range": "56_65", "occupation": "retired"},
                    "financial_context": {"has_dependents": False}
                }
            }
            
            result = self.agent._route_intent_node(state)
            
            assert "detected_intent" in result
            assert result["detected_intent"] == "general_spending"
            print(f"✅ Correctly detected 'general_spending' for: '{user_message}'")
    
    def test_real_llm_intent_detection_with_context_awareness(self):
        """Test that real LLM uses user context to inform intent detection."""
        # Same message but different user contexts should potentially yield different results
        user_message = "I'm worried about my financial situation"
        
        # Young professional context - might lean toward budgeting
        state_young = {
            "messages": [HumanMessage(content=user_message)],
            "user_context": {
                "demographics": {"age_range": "18_25", "occupation": "entry_level"},
                "financial_context": {"has_dependents": False}
            }
        }
        
        # Family context - might lean toward spending analysis or optimization
        state_family = {
            "messages": [HumanMessage(content=user_message)],
            "user_context": {
                "demographics": {"age_range": "36_45", "occupation": "parent"},
                "financial_context": {"has_dependents": True}
            }
        }
        
        result_young = self.agent._route_intent_node(state_young)
        result_family = self.agent._route_intent_node(state_family)
        
        # Both should be valid intents
        valid_intents = ["spending_analysis", "budget_planning", "optimization", "transaction_query", "general_spending"]
        assert result_young["detected_intent"] in valid_intents
        assert result_family["detected_intent"] in valid_intents
        
        print(f"✅ Context-aware detection - Young professional: {result_young['detected_intent']}")
        print(f"✅ Context-aware detection - Family context: {result_family['detected_intent']}")
    
    def test_real_llm_intent_detection_edge_cases(self):
        """Test real LLM handles edge cases and ambiguous inputs."""
        edge_cases = [
            "",  # Empty message
            "?",  # Just punctuation
            "I have a question about money stuff",  # Vague financial question
            "Money money money",  # Repetitive but unclear
        ]
        
        for user_message in edge_cases:
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {}
            }
            
            result = self.agent._route_intent_node(state)
            
            assert "detected_intent" in result
            # Edge cases should generally fall back to general_spending
            # but we allow flexibility for LLM interpretation
            valid_intents = ["spending_analysis", "budget_planning", "optimization", "transaction_query", "general_spending"]
            assert result["detected_intent"] in valid_intents
            print(f"✅ Handled edge case '{user_message}' -> {result['detected_intent']}")
    
    def test_real_llm_initialization_and_availability(self):
        """Test that real LLM is properly initialized and available."""
        assert self.agent.llm is not None
        
        # Test basic LLM functionality
        simple_state = {
            "messages": [HumanMessage(content="Hello")],
            "user_context": {}
        }
        
        result = self.agent._route_intent_node(state=simple_state)
        
        assert "detected_intent" in result
        valid_intents = ["spending_analysis", "budget_planning", "optimization", "transaction_query", "general_spending"]
        assert result["detected_intent"] in valid_intents
        
        print(f"✅ Real LLM is working and detected intent: {result['detected_intent']}")


class TestSpendingAgentRealLLMResponseGeneration:
    """Integration tests for SpendingAgent LLM-powered response generation with real LLM API calls."""
    
    def setup_method(self):
        """Setup method called before each test."""
        with patch.object(SpendingAgent, '__init__', lambda _: None):
            self.agent = SpendingAgent()
            self.agent._user_context_dao = None
            self.agent._auth_service = None  
            self.agent._mcp_clients = {}
            
            # Initialize real LLM
            self.agent.llm = LLMFactory().create_llm()
    
    def test_real_llm_spending_analysis_response(self):
        """Test real LLM generates personalized spending analysis responses."""
        from app.ai.spending_agent import SpendingAgentState
        
        state = SpendingAgentState(
            messages=[HumanMessage(content="I want to understand my spending patterns")],
            user_id="test_user_123",
            session_id="test_session", 
            user_context={
                "demographics": {"age_range": "26_35", "occupation": "engineer"},
                "financial_context": {"has_dependents": False}
            }
        )
        
        result = self.agent._spending_analysis_node(state)
        
        # Verify response structure
        assert "messages" in result
        assert len(result["messages"]) == 1
        
        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert ai_message.additional_kwargs["agent"] == "spending_agent"
        assert ai_message.additional_kwargs["intent"] == "spending_analysis"
        assert ai_message.additional_kwargs["llm_powered"] is True
        
        # Verify response contains financial context
        response_content = ai_message.content.lower()
        assert len(response_content) > 50  # Should be substantial response
        assert any(word in response_content for word in ["spending", "expense", "financial", "budget", "money"])
        
        print(f"✅ Real LLM generated spending analysis response: {len(ai_message.content)} chars")
    
    def test_real_llm_budget_planning_response(self):
        """Test real LLM generates personalized budget planning responses.""" 
        from app.ai.spending_agent import SpendingAgentState
        
        state = SpendingAgentState(
            messages=[HumanMessage(content="Help me create a monthly budget")],
            user_id="test_user_456",
            session_id="test_session",
            user_context={
                "demographics": {"age_range": "36_45", "occupation": "teacher"},
                "financial_context": {"has_dependents": True}
            }
        )
        
        result = self.agent._budget_planning_node(state)
        
        # Verify response structure
        assert "messages" in result
        ai_message = result["messages"][0]
        assert ai_message.additional_kwargs["intent"] == "budget_planning"
        assert ai_message.additional_kwargs["llm_powered"] is True
        
        # Verify response contains budget context
        response_content = ai_message.content.lower()
        assert len(response_content) > 50
        assert any(word in response_content for word in ["budget", "income", "expense", "allocation", "planning"])
        
        print(f"✅ Real LLM generated budget planning response: {len(ai_message.content)} chars")
    
    def test_real_llm_optimization_response(self):
        """Test real LLM generates personalized optimization responses."""
        from app.ai.spending_agent import SpendingAgentState
        
        state = SpendingAgentState(
            messages=[HumanMessage(content="How can I save money on my expenses?")],
            user_id="test_user_789", 
            session_id="test_session",
            user_context={
                "demographics": {"age_range": "18_25", "occupation": "student"},
                "financial_context": {"has_dependents": False}
            }
        )
        
        result = self.agent._optimization_node(state)
        
        # Verify response structure
        ai_message = result["messages"][0]
        assert ai_message.additional_kwargs["intent"] == "optimization" 
        assert ai_message.additional_kwargs["llm_powered"] is True
        
        # Verify response contains optimization context
        response_content = ai_message.content.lower()
        assert len(response_content) > 50
        assert any(word in response_content for word in ["save", "reduce", "optimize", "cost", "expense"])
        
        print(f"✅ Real LLM generated optimization response: {len(ai_message.content)} chars")
    
    def test_real_llm_general_spending_response(self):
        """Test real LLM generates personalized general spending responses."""
        from app.ai.spending_agent import SpendingAgentState
        
        state = SpendingAgentState(
            messages=[HumanMessage(content="Hi, I need help with my finances")],
            user_id="test_user_101",
            session_id="test_session", 
            user_context={
                "demographics": {"age_range": "46_55", "occupation": "manager"},
                "financial_context": {"has_dependents": True}
            }
        )
        
        result = self.agent._general_spending_node(state)
        
        # Verify response structure  
        ai_message = result["messages"][0]
        assert ai_message.additional_kwargs["intent"] == "general_spending"
        assert ai_message.additional_kwargs["llm_powered"] is True
        
        # Verify response is welcoming and informative
        response_content = ai_message.content.lower()
        assert len(response_content) > 50
        assert any(word in response_content for word in ["help", "financial", "assist", "guidance", "analysis"])
        
        print(f"✅ Real LLM generated general spending response: {len(ai_message.content)} chars")

    def test_real_llm_user_context_integration(self):
        """Test that real LLM responses are personalized based on user context."""
        from app.ai.spending_agent import SpendingAgentState
        
        # Test with young professional context
        state_young = SpendingAgentState(
            messages=[HumanMessage(content="Help me with budgeting")],
            user_id="young_professional", 
            session_id="test_session",
            user_context={
                "demographics": {"age_range": "18_25", "occupation": "entry_level"},
                "financial_context": {"has_dependents": False}
            }
        )
        
        # Test with family context
        state_family = SpendingAgentState(
            messages=[HumanMessage(content="Help me with budgeting")],
            user_id="family_person",
            session_id="test_session",
            user_context={
                "demographics": {"age_range": "36_45", "occupation": "parent"},
                "financial_context": {"has_dependents": True}
            }
        )
        
        result_young = self.agent._budget_planning_node(state_young)
        result_family = self.agent._budget_planning_node(state_family)
        
        # Both should be valid responses but potentially different
        young_content = result_young["messages"][0].content
        family_content = result_family["messages"][0].content
        
        assert len(young_content) > 50
        assert len(family_content) > 50
        assert isinstance(young_content, str)
        assert isinstance(family_content, str)
        
        print(f"✅ Young professional response: {len(young_content)} chars")
        print(f"✅ Family context response: {len(family_content)} chars")


class TestSpendingAgentMultiProviderRealLLM:
    """Test SpendingAgent intent detection across all available LLM providers."""
    
    @pytest.mark.parametrize("provider,env_key", [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GOOGLE, "GOOGLE_API_KEY"),
    ])
    def test_intent_detection_across_providers(self, provider, env_key):
        """Test intent detection works consistently across different LLM providers."""
        if not os.getenv(env_key):
            pytest.skip(f"Skipping {provider.value} test - {env_key} not set")
        
        # Temporarily override the default provider for this test
        original_provider = os.getenv('DEFAULT_LLM_PROVIDER')
        
        try:
            # Set the provider for this test
            os.environ['DEFAULT_LLM_PROVIDER'] = provider.value
            
            # Create agent with specific provider
            with patch.object(SpendingAgent, '__init__', lambda _: None):
                agent = SpendingAgent()
                agent._user_context_dao = None
                agent._auth_service = None
                agent._mcp_clients = {}
                
                # Initialize LLM with specific provider
                factory = LLMFactory()
                agent.llm = factory.create_llm(provider=provider)
            
            # Test a clear spending analysis case
            state = {
                "messages": [HumanMessage(content="I want to analyze my spending patterns")],
                "user_context": {
                    "demographics": {"age_range": "26_35", "occupation": "engineer"},
                    "financial_context": {"has_dependents": False}
                }
            }
            
            result = agent._route_intent_node(state)
            
            assert "detected_intent" in result
            # All providers should correctly identify this as spending analysis
            assert result["detected_intent"] == "spending_analysis"
            
            print(f"✅ {provider.value} correctly detected spending_analysis intent")
            
        finally:
            # Restore original provider
            if original_provider:
                os.environ['DEFAULT_LLM_PROVIDER'] = original_provider
            elif 'DEFAULT_LLM_PROVIDER' in os.environ:
                del os.environ['DEFAULT_LLM_PROVIDER']
    
    def test_provider_consistency_comparison(self):
        """Compare intent detection consistency across available providers."""
        available_providers = []
        
        if os.getenv('OPENAI_API_KEY'):
            available_providers.append(LLMProvider.OPENAI)
        if os.getenv('ANTHROPIC_API_KEY'):
            available_providers.append(LLMProvider.ANTHROPIC)
        if os.getenv('GOOGLE_API_KEY'):
            available_providers.append(LLMProvider.GOOGLE)
        
        if len(available_providers) < 2:
            pytest.skip("Need at least 2 providers configured to test consistency")
        
        test_cases = [
            "I want to create a budget",
            "Help me save money on expenses",
            "Show me my recent transactions",
            "What are my spending patterns?"
        ]
        
        original_provider = os.getenv('DEFAULT_LLM_PROVIDER')
        
        try:
            for test_message in test_cases:
                results = {}
                
                for provider in available_providers:
                    # Set provider
                    os.environ['DEFAULT_LLM_PROVIDER'] = provider.value
                    
                    # Create agent with this provider
                    with patch.object(SpendingAgent, '__init__', lambda _: None):
                        agent = SpendingAgent()
                        agent._user_context_dao = None
                        agent._auth_service = None
                        agent._mcp_clients = {}
                        
                        factory = LLMFactory()
                        agent.llm = factory.create_llm(provider=provider)
                    
                    state = {
                        "messages": [HumanMessage(content=test_message)],
                        "user_context": {
                            "demographics": {"age_range": "26_35"},
                            "financial_context": {"has_dependents": False}
                        }
                    }
                    
                    result = agent._route_intent_node(state)
                    results[provider.value] = result["detected_intent"]
                
                print(f"Message: '{test_message}'")
                for provider, intent in results.items():
                    print(f"  {provider}: {intent}")
                
                # All results should be valid intents
                valid_intents = ["spending_analysis", "budget_planning", "optimization", "transaction_query", "general_spending"]
                for intent in results.values():
                    assert intent in valid_intents
                
                print("✅ All providers returned valid intents")
                print()
                
        finally:
            # Restore original provider
            if original_provider:
                os.environ['DEFAULT_LLM_PROVIDER'] = original_provider
            elif 'DEFAULT_LLM_PROVIDER' in os.environ:
                del os.environ['DEFAULT_LLM_PROVIDER']


class TestSpendingAgentRealLLMTransactionCategorization:
    """Integration tests for SpendingAgent + TransactionCategorizationService with real LLMs."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not has_any_llm_key() or __import__('os').getenv('RUN_REAL_TESTS') != 'true',
        reason="Real API tests require at least one LLM provider API key and RUN_REAL_TESTS=true"
    )
    async def test_real_llm_transaction_categorization_integration(self, clear_transactions_for_llm):
        """Test end-to-end transaction categorization with real LLM in SpendingAgent."""
        # Create SpendingAgent with real LLM (skip if no LLM available)
        agent = SpendingAgent()

        if agent.llm is None:
            pytest.skip("No LLM available for real integration test")

        if agent.categorization_service is None:
            pytest.skip("Transaction categorization service not available")

        # Mock successful transaction fetch to isolate categorization testing
        mock_transaction_data = {
            "status": "success",
            "transactions": [txn.model_dump() for txn in clear_transactions_for_llm],
            "total_transactions": len(clear_transactions_for_llm)
        }

        with patch.object(agent, '_fetch_transactions', return_value=mock_transaction_data):
            state = {
                "messages": [HumanMessage(content="Analyze my recent coffee and gas transactions")],
                "user_id": "test_user_real_llm",
                "user_context": {
                    "demographics": {"age_range": "26_35", "occupation": "software_engineer"},
                    "financial_context": {"has_dependents": False}
                },
                "found_in_graphiti": False
            }

            # Execute the real LLM integration
            result = await agent._fetch_and_process_node(state)

            # Verify basic response structure (fetch_and_process_node only returns messages)
            assert "messages" in result
            assert isinstance(result["messages"], list)
            assert len(result["messages"]) == 1

            # Verify response content mentions categorization
            ai_message = result["messages"][0]
            response_content = ai_message.content.lower()

            # Should mention transaction processing and categorization
            assert any(keyword in response_content for keyword in ["transaction", "categoriz", "analyz"]), \
                f"Response should mention transaction processing: {response_content}"

            # Should mention count of transactions
            assert any(num in response_content for num in ["2", "two"]), \
                f"Response should mention transaction count: {response_content}"

            print(f"✅ Real LLM transaction categorization integration test passed")
            print(f"   Response: {response_content[:200]}...")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not has_any_llm_key() or __import__('os').getenv('RUN_REAL_TESTS') != 'true',
        reason="Real API tests require at least one LLM provider API key and RUN_REAL_TESTS=true"
    )
    async def test_real_llm_categorization_service_quality(self, clear_transactions_for_llm):
        """Test that real LLM produces high-quality categorizations."""
        agent = SpendingAgent()

        if agent.categorization_service is None:
            pytest.skip("Transaction categorization service not available")

        # Test categorization directly with user context
        user_context = {
            "demographics": {"age_range": "26_35", "occupation": "software_engineer"},
            "financial_context": {"has_dependents": False}
        }

        result = await agent.categorization_service.categorize_transactions(
            clear_transactions_for_llm, user_context
        )

        # Verify batch result structure
        assert hasattr(result, 'categorizations')
        assert hasattr(result, 'processing_summary')
        assert len(result.categorizations) <= len(clear_transactions_for_llm)

        # If we got categorizations, verify quality
        if result.categorizations:
            for categorization in result.categorizations:
                # Verify required fields are present and non-empty
                assert categorization.transaction_id
                assert categorization.ai_category
                assert categorization.ai_subcategory
                assert categorization.reasoning

                # Verify confidence is reasonable
                assert 0.0 <= categorization.ai_confidence <= 1.0

                # For clear transactions like Starbucks and Shell, expect high confidence
                if "coffee" in categorization.transaction_id.lower():
                    assert categorization.ai_confidence > 0.7, \
                        f"Expected high confidence for coffee shop: {categorization.ai_confidence}"
                    assert "food" in categorization.ai_category.lower() or "dining" in categorization.ai_category.lower(), \
                        f"Expected food/dining category for coffee: {categorization.ai_category}"

                if "gas" in categorization.transaction_id.lower():
                    assert categorization.ai_confidence > 0.7, \
                        f"Expected high confidence for gas station: {categorization.ai_confidence}"
                    assert "transport" in categorization.ai_category.lower(), \
                        f"Expected transportation category for gas: {categorization.ai_category}"

                print(f"✅ Categorized {categorization.transaction_id}: {categorization.ai_category} > {categorization.ai_subcategory} (confidence: {categorization.ai_confidence:.2f})")

        print(f"✅ Real LLM categorization quality test passed with {len(result.categorizations)} categorizations")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not has_any_llm_key() or __import__('os').getenv('RUN_REAL_TESTS') != 'true',
        reason="Real API tests require at least one LLM provider API key and RUN_REAL_TESTS=true"
    )
    async def test_real_llm_categorization_utility_methods(self, clear_transactions_for_llm):
        """Test the utility methods with real LLM categorization."""
        agent = SpendingAgent()

        if agent.categorization_service is None:
            pytest.skip("Transaction categorization service not available")

        user_context = {"demographics": {"age_range": "26_35"}}

        # Test the full categorize_and_apply workflow
        categorized_transactions, batch_result = await agent._categorize_and_apply_transactions(
            clear_transactions_for_llm, user_context
        )

        # Verify results
        assert len(categorized_transactions) == len(clear_transactions_for_llm)
        assert batch_result is not None

        # Check that AI fields were applied to transactions that got categorized
        categorized_count = 0
        for txn in categorized_transactions:
            # If this transaction was categorized, it should have AI fields
            if txn.ai_category is not None:
                categorized_count += 1
                assert txn.ai_subcategory is not None
                assert txn.ai_confidence is not None
                assert 0.0 <= txn.ai_confidence <= 1.0
                print(f"✅ Transaction {txn.transaction_id} categorized as: {txn.ai_category} > {txn.ai_subcategory}")

        print(f"✅ Real LLM utility methods test passed - {categorized_count} transactions categorized")


if __name__ == "__main__":
    pytest.main([__file__])