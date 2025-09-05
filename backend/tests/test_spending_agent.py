"""
Unit tests for SpendingAgent LangGraph subgraph.

Tests the basic functionality of the SpendingAgent class and its nodes.
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from app.ai.spending_agent import SpendingAgent, get_spending_agent, SpendingAgentState


class TestSpendingAgent:
    """Test suite for SpendingAgent class."""
    
    def setup_method(self):
        """Setup method called before each test."""
        self.agent = SpendingAgent()
    
    def test_spending_agent_initialization(self):
        """Test SpendingAgent initializes correctly."""
        assert self.agent is not None
        assert self.agent.graph is not None
        
    def test_get_spending_agent_singleton(self):
        """Test get_spending_agent returns singleton instance."""
        agent1 = get_spending_agent()
        agent2 = get_spending_agent()
        assert agent1 is agent2
    
    def test_initialize_node_with_mock_data(self):
        """Test _initialize_node returns mock user context."""
        initial_state = {
            "messages": [],
            "user_id": "test_user_123",
            "session_id": "test_session_456"
        }
        
        result = self.agent._initialize_node(initial_state)
        
        assert "user_context" in result
        assert "spending_insights" in result
        assert result["user_context"]["user_id"] == "test_user_123"
        assert "demographics" in result["user_context"]
        assert "preferences" in result["user_context"]
    
    def test_route_intent_node_spending_keywords(self):
        """Test _route_intent_node detects spending-related intents."""
        test_cases = [
            ("Tell me about my spending", "spending_analysis"),
            ("How much did I spend this month?", "spending_analysis"),
            ("Show me my expenses", "spending_analysis"),
            ("Help me create a budget", "budget_planning"),
            ("I need budgeting help", "budget_planning"),
            ("How can I save money?", "optimization"),
            ("Optimize my spending", "optimization"),
            ("Find this transaction", "transaction_query"),
            ("Show me my purchases", "transaction_query"),
            ("Hello there", "general_spending")  # Default case
        ]
        
        for message_content, expected_intent in test_cases:
            state = {
                "messages": [HumanMessage(content=message_content)]
            }
            
            result = self.agent._route_intent_node(state)
            assert result.get("detected_intent") == expected_intent
    
    def test_route_intent_node_no_human_message(self):
        """Test _route_intent_node handles non-human messages gracefully."""
        state = {
            "messages": [AIMessage(content="I'm an AI message")]
        }
        
        result = self.agent._route_intent_node(state)
        assert result == {}
    
    def test_generate_response_node_personality_styles(self):
        """Test _generate_response_node adapts to different personality styles."""
        # Test friendly style
        friendly_state = {
            "messages": [HumanMessage(content="Tell me about my spending")],
            "user_context": {
                "preferences": {"communication_style": "friendly"}
            },
            "detected_intent": "spending_analysis"
        }
        
        result = self.agent._generate_response_node(friendly_state)
        assert "messages" in result
        assert len(result["messages"]) == 1
        
        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert "🏦" in ai_message.content or "Hey!" in ai_message.content
        assert ai_message.additional_kwargs["agent"] == "spending_agent"
        assert ai_message.additional_kwargs["intent"] == "spending_analysis"
        assert ai_message.additional_kwargs["personality_style"] == "friendly"
        
        # Test professional style
        professional_state = {
            "messages": [HumanMessage(content="Tell me about my spending")],
            "user_context": {
                "preferences": {"communication_style": "professional"}
            },
            "detected_intent": "spending_analysis"
        }
        
        result = self.agent._generate_response_node(professional_state)
        ai_message = result["messages"][0]
        assert "analyze" in ai_message.content.lower()
        assert ai_message.additional_kwargs["personality_style"] == "professional"
    
    def test_generate_response_node_different_intents(self):
        """Test _generate_response_node handles different intents correctly."""
        intents_to_test = [
            "spending_analysis",
            "budget_planning", 
            "optimization",
            "transaction_query",
            "general_spending"
        ]
        
        for intent in intents_to_test:
            state = {
                "messages": [HumanMessage(content="Test message")],
                "user_context": {"preferences": {"communication_style": "professional"}},
                "detected_intent": intent
            }
            
            result = self.agent._generate_response_node(state)
            assert "messages" in result
            assert len(result["messages"]) == 1
            
            ai_message = result["messages"][0]
            assert isinstance(ai_message, AIMessage)
            assert ai_message.additional_kwargs["intent"] == intent
    
    def test_invoke_spending_conversation_success(self):
        """Test invoke_spending_conversation processes message successfully."""
        user_message = "How much did I spend on food this month?"
        user_id = "test_user_123"
        session_id = "test_session_456"
        
        result = self.agent.invoke_spending_conversation(user_message, user_id, session_id)
        
        assert "content" in result
        assert "agent" in result
        assert "intent" in result
        assert "personality_style" in result
        assert result["agent"] == "spending_agent"
        assert result["user_id"] == user_id
        assert result["session_id"] == session_id
        assert result["message_type"] == "ai_response"
        assert "error" not in result
    
    def test_invoke_spending_conversation_error_handling(self):
        """Test invoke_spending_conversation handles errors gracefully."""
        # Create agent with broken graph
        broken_agent = SpendingAgent()
        broken_agent.graph = None
        
        result = broken_agent.invoke_spending_conversation("test", "user", "session")
        
        assert "error" in result
        assert result["agent"] == "spending_agent"
        assert "trouble processing" in result["content"]
    
    def test_spending_agent_state_structure(self):
        """Test SpendingAgentState has required fields."""
        # Always provide 'messages' to ensure attribute exists
        state = SpendingAgentState(messages=[])

        # Check that 'messages' key exists
        assert 'messages' in state  # Inherited from MessagesState

        # Check additional fields are accessible and assignable as dict keys
        state["user_id"] = "test_user"
        state["session_id"] = "test_session"
        state["user_context"] = {"test": "data"}
        state["spending_insights"] = {"insights": "data"}

        assert state["user_id"] == "test_user"
        assert state["session_id"] == "test_session"
        assert state["user_context"]["test"] == "data"
        assert state["spending_insights"]["insights"] == "data"

class TestSpendingAgentResponseGeneration:
    """Separate test class for response generation methods."""
    
    def setup_method(self):
        """Setup method called before each test."""
        self.agent = SpendingAgent()
    
    def test_generate_spending_analysis_response_styles(self):
        """Test spending analysis response generation with different styles."""
        friendly_response = self.agent._generate_spending_analysis_response("friendly")
        professional_response = self.agent._generate_spending_analysis_response("professional")
        
        assert "🏦" in friendly_response or "Hey!" in friendly_response
        assert "analyze" in professional_response.lower()
        assert friendly_response != professional_response
    
    def test_generate_budget_response_styles(self):
        """Test budget response generation with different styles."""
        friendly_response = self.agent._generate_budget_response("friendly")
        professional_response = self.agent._generate_budget_response("professional")
        
        assert "💰" in friendly_response or "Great" in friendly_response
        assert "budget" in professional_response.lower()
        assert friendly_response != professional_response
    
    def test_generate_optimization_response_styles(self):
        """Test optimization response generation with different styles."""
        friendly_response = self.agent._generate_optimization_response("friendly")
        professional_response = self.agent._generate_optimization_response("professional")
        
        assert "✨" in friendly_response or "love" in friendly_response.lower()
        assert "optimization" in professional_response.lower()
        assert friendly_response != professional_response
    
    def test_generate_transaction_response_styles(self):
        """Test transaction response generation with different styles."""
        friendly_response = self.agent._generate_transaction_response("friendly")
        professional_response = self.agent._generate_transaction_response("professional")
        
        assert "🔍" in friendly_response or "Sure" in friendly_response
        assert "transaction" in professional_response.lower()
        assert friendly_response != professional_response
    
    def test_generate_default_response_styles(self):
        """Test default response generation with different styles."""
        friendly_response = self.agent._generate_default_response("friendly")
        professional_response = self.agent._generate_default_response("professional")
        
        assert "😊" in friendly_response or "Hi there" in friendly_response
        assert "analysis agent" in professional_response
        assert friendly_response != professional_response


if __name__ == "__main__":
    pytest.main([__file__])