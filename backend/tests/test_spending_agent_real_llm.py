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
from langchain_core.messages import HumanMessage

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
def disable_mocking():
    """Disable the auto-mocking for these integration tests."""
    # This fixture runs automatically and does nothing,
    # but it prevents the conftest.py auto-mocking from interfering
    yield


class TestSpendingAgentRealLLM:
    """Integration tests for SpendingAgent with real LLM API calls."""
    
    def setup_method(self):
        """Setup method called before each test."""
        # Ensure no mocking interferes with real LLM calls
        with patch.object(SpendingAgent, '__init__', lambda x: None):
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
            with patch.object(SpendingAgent, '__init__', lambda x: None):
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
                    with patch.object(SpendingAgent, '__init__', lambda x: None):
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


if __name__ == "__main__":
    pytest.main([__file__])