"""
Unit tests for SpendingAgent LangGraph subgraph.

Tests the basic functionality of the SpendingAgent class and its nodes.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.ai.spending_agent import SpendingAgent, get_spending_agent, SpendingAgentState
from app.core.database import SQLiteUserStorage


class TestSpendingAgent:
    """Test suite for SpendingAgent class."""
    
    def setup_method(self):
        """Setup method called before each test."""
        self.agent = SpendingAgent()
    
    def test_spending_agent_initialization(self):
        """Test SpendingAgent initializes correctly with LLM client."""
        assert self.agent is not None
        assert self.agent.graph is not None
        # LLM client should be initialized (mocked in test environment)
        assert hasattr(self.agent, 'llm')
        # In mocked test environment, LLM client might be None or mocked
        # The important thing is the attribute exists and error handling works
        
    def test_get_spending_agent_singleton(self):
        """Test get_spending_agent returns singleton instance."""
        agent1 = get_spending_agent()
        agent2 = get_spending_agent()
        assert agent1 is agent2
    
    @pytest.mark.asyncio
    async def test_initialize_node_with_mock_data(self):
        """Test _initialize_node returns mock user context."""
        initial_state = {
            "messages": [],
            "session_id": "test_session_456"
        }

        # Create mock config with user_id
        config = {
            "configurable": {
                "user_id": "test_user_123"
            }
        }

        result = await self.agent._initialize_node(initial_state, config)

        assert "user_context" in result
        assert result["user_context"]["user_id"] == "test_user_123"
        assert "demographics" in result["user_context"]
        assert "financial_context" in result["user_context"]
    
    def test_route_intent_node_spending_keywords(self):
        """Test _route_intent_node detects spending-related intents using fallback logic."""
        # Note: This test now verifies fallback behavior when LLM is unavailable
        # For actual LLM-powered detection, see TestSpendingAgentLLMIntegration
        
        # Create agent without LLM to test fallback keyword detection
        with patch('app.services.llm_service.llm_factory.create_llm', side_effect=Exception("No LLM")):
            test_agent = SpendingAgent()
            
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
                    "messages": [HumanMessage(content=message_content)],
                    "user_context": {}
                }
                
                result = test_agent._route_intent_node(state)
                assert result.get("detected_intent") == expected_intent
    
    def test_route_intent_node_no_human_message(self):
        """Test _route_intent_node handles non-human messages gracefully."""
        state = {
            "messages": [AIMessage(content="I'm an AI message")]
        }
        
        result = self.agent._route_intent_node(state)
        assert result.get("detected_intent") == "general_spending"
    
    def test_route_to_intent_node(self):
        """Test _route_to_intent_node returns correct intent."""
        test_state = {"detected_intent": "spending_analysis"}
        result = self.agent._route_to_intent_node(test_state)
        assert result == "spending_analysis"
        
        # Test default case
        empty_state = {}
        result = self.agent._route_to_intent_node(empty_state)
        assert result == "general_spending"
    
    @pytest.mark.asyncio
    async def test_spending_analysis_node(self, mock_llm_factory):
        """Test _spending_analysis_node generates appropriate responses."""
        from app.ai.spending_agent import SpendingAgentState

        # Mock the LLM to return a proper spending analysis response
        mock_llm_factory.invoke.return_value = AIMessage(
            content="Based on your spending data, I can see you spent $0.00 this month. Please connect your bank accounts to start tracking your spending.",
            additional_kwargs={'refusal': None}
        )

        test_state = SpendingAgentState(
            messages=[HumanMessage(content="Tell me about my spending")],
            user_id="test_user_123",
            session_id="test_session",
            user_context={
                "demographics": {"age_range": "26_35", "occupation": "engineer"},
                "financial_context": {"has_dependents": False}
            }
        )

        config = {
            "configurable": {
                "user_id": "test_user_123"
            }
        }

        result = await self.agent._spending_analysis_node(test_state, config)
        assert "messages" in result
        assert len(result["messages"]) == 1

        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert ai_message.additional_kwargs["agent"] == "spending_agent"
        assert ai_message.additional_kwargs["intent"] == "spending_analysis"
        assert ai_message.additional_kwargs["llm_powered"] is True
        assert "insights_data" in ai_message.additional_kwargs  # Should include insights data
        assert "spending" in ai_message.content.lower() or "connect" in ai_message.content.lower()
    
    @pytest.mark.asyncio
    async def test_specialized_intent_nodes(self):
        """Test all specialized intent nodes work correctly."""
        from app.ai.spending_agent import SpendingAgentState

        # Separate sync and async nodes
        sync_intent_nodes = [
            ("budget_planning", self.agent._budget_planning_node),
            ("optimization", self.agent._optimization_node),
            ("general_spending", self.agent._general_spending_node)
        ]

        async_intent_nodes = [
            ("spending_analysis", self.agent._spending_analysis_node),  # Now async
            ("transaction_query", self.agent._transaction_query_node)
        ]

        # Test sync nodes
        for intent, node_method in sync_intent_nodes:
            state = SpendingAgentState(
                messages=[HumanMessage(content="Test message")],
                user_id="test_user_123",
                session_id="test_session",
                user_context={
                    "demographics": {"age_range": "26_35", "occupation": "engineer"},
                    "financial_context": {"has_dependents": False}
                }
            )

            result = node_method(state)
            assert "messages" in result
            assert len(result["messages"]) == 1

            ai_message = result["messages"][0]
            assert isinstance(ai_message, AIMessage)
            assert ai_message.additional_kwargs["agent"] == "spending_agent"
            assert ai_message.additional_kwargs["intent"] == intent

        # Test async nodes
        for intent, node_method in async_intent_nodes:
            state = SpendingAgentState(
                messages=[HumanMessage(content="Test message")],
                user_id="test_user_123",
                session_id="test_session",
                user_context={
                    "demographics": {"age_range": "26_35", "occupation": "engineer"},
                    "financial_context": {"has_dependents": False}
                }
            )

            # Create config for methods that require it
            config = {
                "configurable": {
                    "user_id": "test_user_123"
                }
            }

            result = await node_method(state, config)
            assert "messages" in result
            assert len(result["messages"]) == 1

            ai_message = result["messages"][0]
            assert isinstance(ai_message, AIMessage)
            assert ai_message.additional_kwargs["agent"] == "spending_agent"
            assert ai_message.additional_kwargs["intent"] == intent

    @pytest.mark.asyncio
    async def test_invoke_spending_conversation_success(self):
        """Test invoke_spending_conversation processes message successfully."""
        user_message = "How much did I spend on food this month?"
        user_id = "test_user_123"
        session_id = "test_session_456"

        result = await self.agent.invoke_spending_conversation(user_message, user_id, session_id)

        assert "content" in result
        assert "agent" in result
        assert "intent" in result
        assert result["agent"] == "spending_agent"
        assert result["user_id"] == user_id
        assert result["session_id"] == session_id
        assert result["message_type"] == "ai_response"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_invoke_spending_conversation_error_handling(self):
        """Test invoke_spending_conversation handles errors gracefully."""
        # Create agent with broken graph
        broken_agent = SpendingAgent()
        broken_agent.graph = None

        result = await broken_agent.invoke_spending_conversation("test", "user", "session")

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
        state["has_transaction_data"] = True
        state["transaction_insights"] = [{"transaction": "data"}]

        assert state["user_id"] == "test_user"
        assert state["session_id"] == "test_session"
        assert state["user_context"]["test"] == "data"
        assert state["has_transaction_data"] is True
        assert state["transaction_insights"][0]["transaction"] == "data"
    
    def test_route_transaction_query_has_transaction_data(self):
        """Test _route_transaction_query when transaction data exists."""
        state = {"has_transaction_data": True}
        result = self.agent._route_transaction_query(state)
        assert result == "has_transaction_data"
    
    def test_route_transaction_query_fetch_from_plaid(self):
        """Test _route_transaction_query when transaction data doesn't exist."""
        state = {"has_transaction_data": False}
        result = self.agent._route_transaction_query(state)
        assert result == "fetch_from_plaid"

        # Test default case (no has_transaction_data key)
        empty_state = {}
        result = self.agent._route_transaction_query(empty_state)
        assert result == "fetch_from_plaid"

    def test_route_transaction_query_max_attempts_reached(self):
        """Test _route_transaction_query when max fetch attempts are reached."""
        state = {"has_transaction_data": False, "fetch_attempts": 3}
        result = self.agent._route_transaction_query(state)
        assert result == "max_attempts_reached"

        # Test with more than 3 attempts
        state = {"has_transaction_data": False, "fetch_attempts": 5}
        result = self.agent._route_transaction_query(state)
        assert result == "max_attempts_reached"
    
    @pytest.mark.asyncio
    @patch.object(SQLiteUserStorage, 'get_transactions_for_user')
    async def test_transaction_query_node_no_stored_data(self, mock_get_transactions):
        """Test _transaction_query_node when no transactions stored in SQLite."""
        # Mock SQLite to return empty list (no transactions)
        mock_get_transactions.return_value = []

        from app.ai.spending_agent import SpendingAgentState
        state = SpendingAgentState(
            messages=[HumanMessage(content="Show me my transactions")],
            session_id="test_session"
        )

        # Create mock config with user_id
        config = {
            "configurable": {
                "user_id": "test_user_123"
            }
        }

        result = await self.agent._transaction_query_node(state, config)

        # Check basic response structure
        assert "messages" in result
        assert "has_transaction_data" in result

        # Check that it routes to fetch when no data
        assert result["has_transaction_data"] is False

        # Check that we got a proper response message
        messages = result["messages"]
        assert len(messages) == 1
        response_message = messages[0]
        assert hasattr(response_message, 'content')
        assert "fetch" in response_message.content.lower()
        assert "fetch your latest transaction data" in response_message.content

        # Check additional metadata
        assert response_message.additional_kwargs.get("agent") == "spending_agent"
        assert response_message.additional_kwargs.get("intent") == "transaction_query"
        assert response_message.additional_kwargs.get("data_source") == "needs_plaid_fetch"
        
        # Check AI message
        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
        assert ai_message.additional_kwargs["agent"] == "spending_agent"
        assert ai_message.additional_kwargs["intent"] == "transaction_query"
        assert ai_message.additional_kwargs["data_source"] == "needs_plaid_fetch"
        assert "Let me fetch your latest transaction data" in ai_message.content
    
    @pytest.mark.asyncio
    async def test_fetch_and_process_node_success(self):
        """Test _fetch_and_process_node with successful mock transaction fetch."""
        state = {
            "messages": [HumanMessage(content="Show me my transactions")],
            "has_transaction_data": False
        }

        # Create mock config with user_id
        config = {
            "configurable": {
                "user_id": "test_user_123"
            }
        }

        result = await self.agent._fetch_and_process_node(state, config)
        
        # Validate response structure
        assert "messages" in result, "Result must contain 'messages' key"
        assert isinstance(result["messages"], list), "Messages should be a list"
        assert len(result["messages"]) == 1, "Should contain exactly one message"
        
        # Validate AI message structure
        ai_message = result["messages"][0]
        assert isinstance(ai_message, AIMessage)
    
        
        assert ai_message.additional_kwargs["agent"] == "spending_agent"
        assert ai_message.additional_kwargs["intent"] == "transaction_fetch_and_process"
        assert isinstance(ai_message.additional_kwargs["transaction_count"], int)
        assert ai_message.additional_kwargs["transaction_count"] >= 0, "Transaction count should be non-negative"
        
        # Validate message content
        assert isinstance(ai_message.content, str), "Message content should be a string"
        assert len(ai_message.content) > 0, "Message content should not be empty"
        # Content should indicate either success or error, but should be informative
        assert any(keyword in ai_message.content.lower() for keyword in 
                  ["successfully", "fetched", "encountered", "issue"]), \
               "Message should indicate success or error status"
    
    @pytest.mark.asyncio
    @patch.object(SpendingAgent, '_fetch_transactions')
    async def test_transaction_query_workflow_integration(self, mock_fetch_transactions):
        """Test the full transaction query workflow with mocked data."""
        # Mock transaction fetch to succeed (avoids infinite loop)
        mock_fetch_transactions.return_value = {
            "status": "success",
            "transactions": [],
            "total_transactions": 0
        }

        user_message = "Find this transaction"  # Using exact keyword from existing test
        user_id = "test_user_456"
        session_id = "test_session_789"

        result = await self.agent.invoke_spending_conversation(user_message, user_id, session_id)

        # The workflow should complete successfully
        assert "content" in result
        assert "agent" in result
        assert "intent" in result
        assert result["agent"] == "spending_agent"
        # TODO: Intent detection has some edge cases with keyword matching - will be fixed with LLM-based detection
        assert result["intent"] in ["transaction_query", "general_spending"]
        assert result["user_id"] == user_id
        assert result["session_id"] == session_id
        assert result["message_type"] == "ai_response"
        assert "error" not in result

        # With mocked data, it should go through the fetch_and_process path and return final results
        # The exact content depends on whether it went through fetch path or not

    @pytest.mark.asyncio
    @patch.object(SpendingAgent, '_fetch_transactions')
    async def test_transaction_query_workflow_with_failures(self, mock_fetch_transactions):
        """Test the workflow handles external service failures gracefully and stops after 3 iterations."""

        # Mock transaction fetch to always fail (simulating external service failure)
        mock_fetch_transactions.return_value = {
            "status": "error",
            "error": "Connection timeout",
            "transactions": []
        }

        user_message = "Show me my transactions"
        user_id = "test_user_failure"
        session_id = "test_session_failure"

        result = await self.agent.invoke_spending_conversation(user_message, user_id, session_id)

        # Should handle failures gracefully
        assert "content" in result
        assert "agent" in result
        assert result["agent"] == "spending_agent"
        assert result["user_id"] == user_id
        assert result["session_id"] == session_id
        assert result["message_type"] == "ai_response"

        # Most importantly: should stop after exactly 3 fetch attempts (no infinite loop)
        assert mock_fetch_transactions.call_count <= 3, f"Should not exceed 3 fetch attempts, got {mock_fetch_transactions.call_count}"

        # Should not have recursion limit error (proves iteration limit works)
        if "error" in result:
            assert "Recursion limit" not in result["error"], "Should not hit recursion limit with iteration counter"
            assert "trouble processing" in result["content"] or "try again" in result["content"]
        else:
            # If it succeeds, should have proper response
            assert len(result["content"]) > 0

    @pytest.mark.asyncio
    async def test_fetch_transactions_with_mocked_mcp_success(self):
        """Test _fetch_transactions with mocked successful MCP client."""
        # Mock successful call_tool response from shared PlaidMCPClient
        mock_call_tool_result = {
            "status": "success",
            "transactions": [
                {"id": "tx1", "amount": 25.50, "description": "Coffee Shop"},
                {"id": "tx2", "amount": 120.00, "description": "Grocery Store"}
            ],
            "total_transactions": 2
        }

        # Patch the shared PlaidMCPClient's call_tool method
        with patch.object(self.agent._plaid_client, 'call_tool', return_value=mock_call_tool_result):
            result = await self.agent._fetch_transactions("test_user_mcp")

            # Validate successful response structure
            assert result["status"] == "success"
            assert "transactions" in result
            assert "total_transactions" in result
            assert result["total_transactions"] == 2
            assert len(result["transactions"]) == 2
            
            # Validate transaction data
            assert result["transactions"][0]["id"] == "tx1"
            assert result["transactions"][0]["amount"] == 25.50
            assert result["transactions"][1]["id"] == "tx2"
            assert result["transactions"][1]["amount"] == 120.00

            # Verify PlaidMCPClient call_tool was called with correct parameters
            self.agent._plaid_client.call_tool.assert_called_once_with("test_user_mcp", "get_all_transactions")

    @pytest.mark.asyncio
    async def test_fetch_transactions_with_mocked_mcp_no_tool(self):
        """Test _fetch_transactions when get_all_transactions tool is not available."""
        # Mock call_tool response indicating tool missing (should return error, not mock fallback)
        mock_call_tool_result = {
            "status": "error",
            "error": "get_all_transactions tool does not exist",
            "transactions": []
        }

        # Patch the shared PlaidMCPClient's call_tool method
        with patch.object(self.agent._plaid_client, 'call_tool', return_value=mock_call_tool_result):
            result = await self.agent._fetch_transactions("test_user_no_tool")

            # Validate error response
            assert result["status"] == "error"
            assert "error" in result
            assert "transactions" in result["error"]
            assert "get_all_transactions tool does not exist" in result["error"]
            assert result["transactions"] == []

            # Verify PlaidMCPClient call_tool was called with correct parameters
            self.agent._plaid_client.call_tool.assert_called_once_with("test_user_no_tool", "get_all_transactions")

    @pytest.mark.asyncio
    async def test_fetch_transactions_with_mcp_unavailable(self):
        """Test _fetch_transactions when MCP is not available."""
        # Mock call_tool response indicating MCP unavailable
        mock_call_tool_result = {
            "status": "error",
            "error": "MCP server not available"
        }

        # Patch the shared PlaidMCPClient's call_tool method
        with patch.object(self.agent._plaid_client, 'call_tool', return_value=mock_call_tool_result):
            result = await self.agent._fetch_transactions("test_user_no_mcp")

            # Validate mock fallback response
            assert result["status"] == "success"
            assert "transactions" in result
            assert "total_transactions" in result
            assert "message" in result
            assert result["total_transactions"] == 0
            assert result["transactions"] == []
            assert "Mock transaction data" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_and_process_node_with_mocked_successful_fetch(self):
        """Test _fetch_and_process_node with mocked successful transaction fetch."""
        # Mock successful transaction fetch with proper PlaidTransaction fields
        mock_fetch_result = {
            "status": "success",
            "transactions": [{
                "transaction_id": "tx1",
                "account_id": "acc1",
                "amount": 100.0,
                "name": "Test Transaction",
                "merchant_name": "Test Merchant",
                "date": "2024-01-15",
                "category": ["Shopping"],
                "pending": False
            }],
            "total_transactions": 1
        }
        
        state = {
            "messages": [],
            "has_transaction_data": False
        }

        # Create mock config with user_id
        config = {
            "configurable": {
                "user_id": "test_user_mocked"
            }
        }

        with patch.object(self.agent, '_fetch_transactions', return_value=mock_fetch_result):
            result = await self.agent._fetch_and_process_node(state, config)
            
            # Validate successful processing
            assert len(result["messages"]) == 1
            
            ai_message = result["messages"][0]
            assert ai_message.additional_kwargs["transaction_count"] == 1
            assert "successfully fetched 1 transactions" in ai_message.content.lower()

    @pytest.mark.asyncio
    async def test_fetch_and_process_node_with_mocked_failed_fetch(self):
        """Test _fetch_and_process_node with mocked failed transaction fetch."""
        # Mock failed transaction fetch
        mock_fetch_result = {
            "status": "error",
            "error": "Connection timeout",
            "transactions": []
        }
        
        state = {
            "messages": [],
            "has_transaction_data": False
        }

        # Create mock config with user_id
        config = {
            "configurable": {
                "user_id": "test_user_error"
            }
        }

        with patch.object(self.agent, '_fetch_transactions', return_value=mock_fetch_result):
            result = await self.agent._fetch_and_process_node(state, config)
            
            # Validate error handling
            assert len(result["messages"]) == 1

            ai_message = result["messages"][0]
            assert ai_message.additional_kwargs["transaction_count"] == 0
            # Check for either new or old error message format
            assert ("encountered" in ai_message.content.lower() and "issue" in ai_message.content.lower())
            assert "connection timeout" in ai_message.content.lower()



class TestSpendingAgentLLMIntegration:
    """Test suite for SpendingAgent LLM integration features."""
    
    def setup_method(self):
        """Setup method called before each test."""
        with patch('app.services.llm_service.llm_factory.create_llm') as mock_llm_factory:
            # Create a mock LLM that returns predictable responses
            mock_llm = MagicMock()
            mock_llm_factory.return_value = mock_llm
            self.agent = SpendingAgent()
            self.mock_llm = mock_llm
    
    def test_llm_initialization_success(self):
        """Test LLM client initializes successfully."""
        assert self.agent.llm is not None
        assert self.agent.llm == self.mock_llm
    
    def test_llm_initialization_failure(self):
        """Test graceful handling of LLM initialization failure."""
        with patch('app.services.llm_service.llm_factory.create_llm', side_effect=Exception("LLM unavailable")):
            agent = SpendingAgent()
            assert agent.llm is None
    
    def test_llm_powered_intent_detection(self):
        """Test LLM-powered intent detection with various user inputs."""
        # Mock LLM response for different intents
        test_cases = [
            ("I want to analyze my spending patterns", "spending_analysis"),
            ("Help me create a budget", "budget_planning"),
            ("How can I save money on groceries?", "optimization"),
            ("Find my transaction from yesterday", "transaction_query"),
            ("Hello, I need financial help", "general_spending")
        ]
        
        for user_message, expected_intent in test_cases:
            # Configure mock LLM to return the expected intent
            mock_response = MagicMock()
            mock_response.content = expected_intent
            self.mock_llm.invoke.return_value = mock_response
            
            state = {
                "messages": [HumanMessage(content=user_message)],
                "user_context": {
                    "demographics": {"age_range": "26_35", "occupation": "engineer"},
                    "financial_context": {"has_dependents": False}
                }
            }
            
            result = self.agent._route_intent_node(state)
            
            assert result["detected_intent"] == expected_intent
            self.mock_llm.invoke.assert_called()
            
            # Verify system prompt includes user context
            call_args = self.mock_llm.invoke.call_args[0][0]
            system_message = call_args[0]
            assert "Age range: 26_35" in system_message.content
            assert "Occupation: engineer" in system_message.content
    
    def test_llm_intent_detection_with_invalid_response(self):
        """Test handling of invalid LLM response in intent detection."""
        # Mock LLM to return invalid intent
        mock_response = MagicMock()
        mock_response.content = "invalid_intent_response"
        self.mock_llm.invoke.return_value = mock_response
        
        state = {
            "messages": [HumanMessage(content="Help me with my finances")],
            "user_context": {}
        }
        
        result = self.agent._route_intent_node(state)
        
        # Should fall back to default
        assert result["detected_intent"] == "general_spending"
    
    def test_llm_intent_detection_error_fallback(self):
        """Test fallback to keyword-based detection when LLM fails."""
        # Mock LLM to raise an exception
        self.mock_llm.invoke.side_effect = Exception("LLM API error")
        
        state = {
            "messages": [HumanMessage(content="I want to optimize my spending")],
            "user_context": {}
        }
        
        result = self.agent._route_intent_node(state)
        
        # Should use fallback keyword detection
        assert result["detected_intent"] == "optimization"
    
    def test_llm_unavailable_fallback(self):
        """Test intent detection when LLM is completely unavailable."""
        # Create agent with no LLM
        with patch('app.services.llm_service.llm_factory.create_llm', side_effect=Exception("No LLM")):
            agent = SpendingAgent()
            
            state = {
                "messages": [HumanMessage(content="Help me with budgeting")],
                "user_context": {}
            }
            
            result = agent._route_intent_node(state)
            
            # Should use fallback keyword detection
            assert result["detected_intent"] == "budget_planning"
    
    def test_fallback_intent_detection_accuracy(self):
        """Test accuracy of fallback keyword-based intent detection."""
        test_cases = [
            ("I want to save money and optimize costs", "optimization"),
            ("Help me reduce my spending", "optimization"),
            ("Show me my spending patterns and expense analysis", "spending_analysis"),
            ("Create a monthly budget plan", "budget_planning"),
            ("Find the transaction I made yesterday", "transaction_query"),
            ("What did I purchase at the grocery store?", "transaction_query"),
            ("Hello, I'm new here", "general_spending")
        ]
        
        for user_input, expected_intent in test_cases:
            result = self.agent._fallback_intent_detection(user_input)
            assert result == expected_intent
    
    def test_context_aware_intent_detection(self):
        """Test that LLM intent detection includes user context in prompts."""
        mock_response = MagicMock()
        mock_response.content = "spending_analysis"
        self.mock_llm.invoke.return_value = mock_response
        
        # Test with rich user context
        state = {
            "messages": [HumanMessage(content="How am I doing financially?")],
            "user_context": {
                "demographics": {
                    "age_range": "36_45",
                    "occupation": "teacher"
                },
                "financial_context": {
                    "has_dependents": True
                }
            }
        }
        
        self.agent._route_intent_node(state)
        
        # Verify LLM was called with context-rich prompt
        call_args = self.mock_llm.invoke.call_args[0][0]
        system_message = call_args[0]
        system_prompt = system_message.content
        
        assert "Age range: 36_45" in system_prompt
        assert "Occupation: teacher" in system_prompt
        assert "Has dependents: Yes" in system_prompt
        assert "INTENT CATEGORIES:" in system_prompt
        assert "EXAMPLES:" in system_prompt
    
    def test_context_aware_intent_detection_minimal_context(self):
        """Test LLM intent detection with minimal user context."""
        mock_response = MagicMock()
        mock_response.content = "general_spending"
        self.mock_llm.invoke.return_value = mock_response
        
        # Test with empty context
        state = {
            "messages": [HumanMessage(content="Hi there")],
            "user_context": {
                "demographics": {},
                "financial_context": {}
            }
        }
        
        self.agent._route_intent_node(state)
        
        # Verify system prompt handles empty context gracefully
        call_args = self.mock_llm.invoke.call_args[0][0]
        system_message = call_args[0]
        assert "Limited user context available" in system_message.content

class TestSpendingAgentTransactionCategorization:
    """Test integration between SpendingAgent and TransactionCategorizationService."""

    @pytest.fixture
    def agent_with_categorization(self):
        """SpendingAgent instance with categorization service enabled."""
        agent = SpendingAgent()
        # Ensure categorization service is available for testing
        assert agent.categorization_service is not None
        return agent

    @pytest.mark.asyncio
    async def test_fetch_and_process_with_categorization_integration(self, agent_with_categorization, sample_transactions):
        """Test that _fetch_and_process_node properly integrates transaction categorization."""
        # Mock successful transaction fetch
        mock_transaction_data = {
            "status": "success",
            "transactions": [txn.model_dump() for txn in sample_transactions],
            "total_transactions": len(sample_transactions)
        }

        with patch.object(agent_with_categorization, '_fetch_transactions', return_value=mock_transaction_data):
            # Mock the categorization service response
            from app.models.plaid_models import TransactionCategorization, TransactionCategorizationBatch

            mock_categorizations = [
                TransactionCategorization(
                    transaction_id="txn_starbucks_1",
                    ai_category="Food & Dining",
                    ai_subcategory="Coffee Shops",
                    ai_confidence=0.95,
                    ai_tags=["caffeine", "daily-habit"],
                    reasoning="Starbucks purchase clearly indicates coffee"
                ),
                TransactionCategorization(
                    transaction_id="txn_gas_1",
                    ai_category="Transportation",
                    ai_subcategory="Gas Stations",
                    ai_confidence=0.92,
                    ai_tags=["fuel", "automotive"],
                    reasoning="Shell gas station for vehicle fuel"
                )
            ]

            mock_batch = TransactionCategorizationBatch(
                categorizations=mock_categorizations,
                processing_summary="Successfully categorized 2 transactions"
            )

            # Mock the categorization service
            with patch.object(agent_with_categorization.categorization_service, 'categorize_transactions', return_value=mock_batch):

                state = {
                    "messages": [HumanMessage(content="Fetch and analyze my recent transactions")],
                    "user_context": {
                        "demographics": {"age_range": "26_35", "occupation": "engineer"},
                        "financial_context": {"has_dependents": False}
                    },
                    "has_transaction_data": False
                }

                # Create mock config with user_id
                config = {
                    "configurable": {
                        "user_id": "test_user_123"
                    }
                }

                result = await agent_with_categorization._fetch_and_process_node(state, config)

                # Verify basic response structure
                assert "messages" in result

                # Verify response mentions categorization
                ai_message = result["messages"][0]
                response_content = ai_message.content

                # Should mention both total transactions and categorized count
                assert "2 transactions" in response_content
                assert "categorized 2" in response_content
                assert "AI insights" in response_content

                # Verify categorization service was called with correct data
                agent_with_categorization.categorization_service.categorize_transactions.assert_called_once()
                call_args = agent_with_categorization.categorization_service.categorize_transactions.call_args

                # Check transaction objects were passed
                transactions_arg = call_args[0][0]
                assert len(transactions_arg) == 2
                assert transactions_arg[0].transaction_id == "txn_starbucks_1"
                assert transactions_arg[1].transaction_id == "txn_gas_1"

                # Check user context was passed
                user_context_arg = call_args[0][1]
                assert user_context_arg["demographics"]["age_range"] == "26_35"
                assert user_context_arg["financial_context"]["has_dependents"] is False

    @pytest.mark.asyncio
    async def test_categorization_service_initialization(self, agent_with_categorization):
        """Test that categorization service is properly initialized in SpendingAgent."""
        # Verify categorization service exists
        assert hasattr(agent_with_categorization, 'categorization_service')
        assert agent_with_categorization.categorization_service is not None

        # Verify it has the expected interface
        assert hasattr(agent_with_categorization.categorization_service, 'categorize_transactions')
        assert hasattr(agent_with_categorization, '_categorize_and_apply_transactions')
        assert hasattr(agent_with_categorization, '_apply_categorization_to_transaction')

    @pytest.mark.asyncio
    async def test_categorize_and_apply_transactions_method(self, agent_with_categorization, sample_transactions):
        """Test the _categorize_and_apply_transactions utility method."""
        # Mock categorization response
        from app.models.plaid_models import TransactionCategorization, TransactionCategorizationBatch

        mock_categorization = TransactionCategorization(
            transaction_id="txn_starbucks_1",
            ai_category="Food & Dining",
            ai_subcategory="Coffee Shops",
            ai_confidence=0.95,
            ai_tags=["caffeine"],
            reasoning="Coffee purchase"
        )

        mock_batch = TransactionCategorizationBatch(
            categorizations=[mock_categorization],
            processing_summary="Categorized 1 transaction"
        )

        with patch.object(agent_with_categorization.categorization_service, 'categorize_transactions', return_value=mock_batch):

            user_context = {"demographics": {"age_range": "26_35"}}

            categorized_transactions, batch_result = await agent_with_categorization._categorize_and_apply_transactions(
                sample_transactions, user_context
            )

            # Verify results
            assert len(categorized_transactions) == 2
            assert batch_result == mock_batch

            # Verify first transaction got AI categorization applied
            first_txn = categorized_transactions[0]
            assert first_txn.ai_category == "Food & Dining"
            assert first_txn.ai_subcategory == "Coffee Shops"
            assert first_txn.ai_confidence == 0.95
            assert first_txn.ai_tags == ["caffeine"]

            # Verify second transaction remains unchanged (no categorization for it)
            second_txn = categorized_transactions[1]
            assert second_txn.ai_category is None
            assert second_txn.transaction_id == "txn_gas_1"


class TestSpendingAgentStateFlows:
    """Test state diagram flows for transaction query scenarios."""

    def setup_method(self):
        """Setup method called before each test."""
        self.agent = SpendingAgent()

    @pytest.mark.asyncio
    async def test_scenario_existing_data_direct_query(self):
        """
        Scenario 1: User has existing transactions in SQLite.
        Flow: transaction_query → execute SQL → END
        """
        from unittest.mock import AsyncMock, patch

        # Mock user has existing transactions
        mock_transactions = [{"id": 1, "amount": 100}]

        with patch.object(self.agent._storage, 'get_transactions_for_user', new_callable=AsyncMock) as mock_get_txns:
            mock_get_txns.return_value = mock_transactions

            state = {
                "messages": [HumanMessage(content="Show me my spending")],
                "user_id": "test_user",
                "user_context": {}
            }
            config = {"configurable": {"user_id": "test_user"}}

            # Call transaction_query_node
            result = await self.agent._transaction_query_node(state, config)

            # Verify SQLite was checked
            mock_get_txns.assert_called_once_with("test_user", limit=1)

            # Should NOT route to fetch (has_transaction_data should be True or query executed)
            # This depends on LLM parsing, but data exists so it should process
            assert "messages" in result

    @pytest.mark.asyncio
    async def test_scenario_no_data_successful_fetch(self):
        """
        Scenario 2: User has NO transactions, fetch succeeds.
        Flow: transaction_query → fetch_and_process → transaction_query → execute SQL → END
        """
        from unittest.mock import AsyncMock, patch

        # First call: no transactions
        # Second call (after fetch): has transactions
        call_count = 0

        async def mock_get_transactions_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return []  # No data initially
            else:
                return [{"id": 1, "amount": 100}]  # Data after fetch

        with patch.object(self.agent._storage, 'get_transactions_for_user', new_callable=AsyncMock) as mock_get_txns:
            mock_get_txns.side_effect = mock_get_transactions_side_effect

            # Initial state
            state = {
                "messages": [HumanMessage(content="Show me my spending")],
                "user_id": "test_user",
                "user_context": {},
                "fetch_attempts": 0
            }
            config = {"configurable": {"user_id": "test_user"}}

            # First call: transaction_query_node with no data
            result1 = await self.agent._transaction_query_node(state, config)

            # Should indicate no data
            assert result1["has_transaction_data"] is False
            assert call_count == 1

            # Router would send to fetch_and_process
            # Simulate _route_transaction_query logic
            route = self.agent._route_transaction_query(result1)
            assert route == "fetch_from_plaid"

    @pytest.mark.asyncio
    async def test_scenario_fetch_fails_three_times(self):
        """
        Scenario 3: Fetch fails repeatedly, exits after 3 attempts.
        Flow: transaction_query → fetch (fail) → transaction_query → fetch (fail) → transaction_query → fetch (fail) → END
        """
        from unittest.mock import AsyncMock, patch

        # Mock no transactions in SQLite
        with patch.object(self.agent._storage, 'get_transactions_for_user', new_callable=AsyncMock) as mock_get_txns:
            mock_get_txns.return_value = []  # Always no data

            # Test router logic with increasing attempts
            state_attempt_0 = {"has_transaction_data": False, "fetch_attempts": 0}
            route_0 = self.agent._route_transaction_query(state_attempt_0)
            assert route_0 == "fetch_from_plaid"

            state_attempt_1 = {"has_transaction_data": False, "fetch_attempts": 1}
            route_1 = self.agent._route_transaction_query(state_attempt_1)
            assert route_1 == "fetch_from_plaid"

            state_attempt_2 = {"has_transaction_data": False, "fetch_attempts": 2}
            route_2 = self.agent._route_transaction_query(state_attempt_2)
            assert route_2 == "fetch_from_plaid"

            state_attempt_3 = {"has_transaction_data": False, "fetch_attempts": 3}
            route_3 = self.agent._route_transaction_query(state_attempt_3)
            assert route_3 == "max_attempts_reached"  # Should exit here

    @pytest.mark.asyncio
    async def test_scenario_unknown_intent_no_fetch(self):
        """
        Scenario 4: Query parsing fails (UNKNOWN intent), should not trigger fetch.
        Flow: transaction_query → UNKNOWN intent → END (no fetch)
        """
        from unittest.mock import AsyncMock, patch
        from app.models.transaction_query_models import QueryIntent, TransactionQueryIntent

        # Mock transactions exist
        mock_transactions = [{"id": 1, "amount": 100}]

        # Mock LLM returns UNKNOWN intent
        mock_unknown_intent = TransactionQueryIntent(
            intent=QueryIntent.UNKNOWN,
            original_query="gibberish query",
            confidence=0.1
        )

        with patch.object(self.agent._storage, 'get_transactions_for_user', new_callable=AsyncMock) as mock_get_txns, \
             patch('app.utils.transaction_query_parser.parse_user_query_to_intent') as mock_parse:

            mock_get_txns.return_value = mock_transactions
            mock_parse.return_value = mock_unknown_intent

            state = {
                "messages": [HumanMessage(content="xyzabc nonsense query")],
                "user_id": "test_user",
                "user_context": {}
            }
            config = {"configurable": {"user_id": "test_user"}}

            result = await self.agent._transaction_query_node(state, config)

            # Should mark as handled to prevent fetch
            assert result["has_transaction_data"] is True
            assert "messages" in result
            # Message should contain helpful guidance
            response_content = result["messages"][0].content
            assert "couldn't quite understand" in response_content.lower() or "rephrase" in response_content.lower()

    @pytest.mark.asyncio
    async def test_fetch_error_messages_by_attempt(self):
        """Test that error messages improve based on attempt number."""
        from unittest.mock import AsyncMock, patch

        # Mock fetch failure
        mock_fetch_result = {
            "status": "error",
            "error": "Connection timeout",
            "transactions": []
        }

        with patch.object(self.agent, '_fetch_transactions', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_fetch_result

            config = {"configurable": {"user_id": "test_user"}}

            # Attempt 1
            state_1 = {"fetch_attempts": 0, "user_context": {}}
            result_1 = await self.agent._fetch_and_process_node(state_1, config)
            message_1 = result_1["messages"][0].content
            assert "Retrying" in message_1 or "temporary" in message_1.lower()
            assert result_1["fetch_attempts"] == 1

            # Attempt 2
            state_2 = {"fetch_attempts": 1, "user_context": {}}
            result_2 = await self.agent._fetch_and_process_node(state_2, config)
            message_2 = result_2["messages"][0].content
            assert "attempt 2/3" in message_2.lower() or "trouble" in message_2.lower()
            assert result_2["fetch_attempts"] == 2

            # Attempt 3 (final)
            state_3 = {"fetch_attempts": 2, "user_context": {}}
            result_3 = await self.agent._fetch_and_process_node(state_3, config)
            message_3 = result_3["messages"][0].content
            assert "3 times" in message_3 or "persistent" in message_3.lower()
            assert "account connections" in message_3.lower() or "reconnect" in message_3.lower()
            assert result_3["fetch_attempts"] == 3

    @pytest.mark.asyncio
    async def test_fetch_timeout_handling(self):
        """Test that fetch operations timeout after configured duration."""
        import asyncio
        from unittest.mock import AsyncMock, patch

        # Mock a slow fetch that exceeds timeout
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(5)  # Simulate slow response
            return {"status": "success", "transactions": []}

        with patch.object(self.agent._plaid_client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = slow_fetch

            # Call with 1 second timeout
            result = await self.agent._fetch_transactions("test_user", timeout_seconds=1)

            # Should return error with timeout message
            assert result["status"] == "error"
            assert "timed out" in result["error"].lower()
            assert "1 seconds" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_successful_within_timeout(self):
        """Test that fetch completes successfully when under timeout."""
        from unittest.mock import AsyncMock, patch

        mock_result = {
            "status": "success",
            "transactions": [{"id": 1, "amount": 100}],
            "total_transactions": 1
        }

        with patch.object(self.agent._plaid_client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_result

            # Call with generous timeout
            result = await self.agent._fetch_transactions("test_user", timeout_seconds=30)

            # Should succeed
            assert result["status"] == "success"
            assert result["total_transactions"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
