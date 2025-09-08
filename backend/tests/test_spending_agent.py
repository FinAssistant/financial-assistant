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
        assert "financial_context" in result["user_context"]
    
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
    
    def test_route_to_intent_node(self):
        """Test _route_to_intent_node returns correct intent."""
        test_state = {"detected_intent": "spending_analysis"}
        result = self.agent._route_to_intent_node(test_state)
        assert result == "spending_analysis"
        
        # Test default case
        empty_state = {}
        result = self.agent._route_to_intent_node(empty_state)
        assert result == "general_spending"
    
    def test_spending_analysis_node(self):
        """Test _spending_analysis_node generates appropriate responses."""
        test_state = {
            "messages": [HumanMessage(content="Tell me about my spending")],
            "detected_intent": "spending_analysis"
        }
        
        result = self.agent._spending_analysis_node(test_state)
        assert "messages" in result
        assert len(result["messages"]) == 1
        
        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert ai_message.additional_kwargs["agent"] == "spending_agent"
        assert ai_message.additional_kwargs["intent"] == "spending_analysis"
        assert "analyze" in ai_message.content.lower()
    
    def test_specialized_intent_nodes(self):
        """Test all specialized intent nodes work correctly."""
        intent_nodes = [
            ("spending_analysis", self.agent._spending_analysis_node),
            ("budget_planning", self.agent._budget_planning_node),
            ("optimization", self.agent._optimization_node),
            ("transaction_query", self.agent._transaction_query_node),
            ("general_spending", self.agent._general_spending_node)
        ]
        
        for intent, node_method in intent_nodes:
            state = {
                "messages": [HumanMessage(content="Test message")],
                "detected_intent": intent
            }
            
            result = node_method(state)
            assert "messages" in result
            assert len(result["messages"]) == 1
            
            ai_message = result["messages"][0]
            assert isinstance(ai_message, AIMessage)
            assert ai_message.additional_kwargs["agent"] == "spending_agent"
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



if __name__ == "__main__":
    pytest.main([__file__])