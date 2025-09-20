"""
Tests for AI-powered transaction categorization using LLM structured output.
Includes both mock LLM tests (fast) and real LLM integration tests.
"""

import os
import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.plaid_models import (
    PlaidTransaction,
    TransactionCategorization,
    TransactionCategorizationBatch
)
from app.services.llm_service import LLMFactory


# Mock LLM Tests (Fast, always run)
class TestTransactionCategorizationMockLLM:
    """Test transaction categorization with mock LLM calls."""
    
    @pytest.fixture
    def mock_transactions(self):
        """Sample transactions for testing."""
        return [
            PlaidTransaction(
                transaction_id='txn_starbucks_1',
                account_id='acc_123',
                amount='4.75',
                date='2024-01-15',
                name='STARBUCKS STORE #1234',
                merchant_name='Starbucks',
                category=['Food and Drink'],
                pending=False
            ),
            PlaidTransaction(
                transaction_id='txn_shell_1',
                account_id='acc_123',
                amount='45.50',
                date='2024-01-14',
                name='SHELL GAS STATION',
                merchant_name='Shell',
                category=['Transportation', 'Gas Stations'],
                pending=False
            ),
            PlaidTransaction(
                transaction_id='txn_amazon_1',
                account_id='acc_456',
                amount='89.99',
                date='2024-01-13',
                name='AMAZON.COM',
                merchant_name='Amazon',
                category=['Shops'],
                pending=False
            )
        ]
    
    @pytest.fixture
    def mock_llm_categorization_response(self):
        """Mock LLM response for transaction categorization."""
        # Simulate structured output that would come from an LLM
        mock_response_content = {
            "categorizations": [
                {
                    "transaction_id": "txn_starbucks_1",
                    "ai_category": "Food & Dining",
                    "ai_subcategory": "Coffee Shops",
                    "ai_confidence": 0.95,
                    "ai_tags": ["caffeine", "quick-service", "daily-habit"],
                    "reasoning": "Starbucks is clearly a coffee shop purchase with high confidence based on merchant name"
                },
                {
                    "transaction_id": "txn_shell_1", 
                    "ai_category": "Transportation",
                    "ai_subcategory": "Gas Stations",
                    "ai_confidence": 0.92,
                    "ai_tags": ["fuel", "automotive", "necessity"],
                    "reasoning": "Shell gas station purchase for vehicle fuel, common transportation expense"
                },
                {
                    "transaction_id": "txn_amazon_1",
                    "ai_category": "Shopping",
                    "ai_subcategory": "Online Retail",
                    "ai_confidence": 0.88,
                    "ai_tags": ["e-commerce", "general-merchandise", "online"],
                    "reasoning": "Amazon purchase - online retail, medium confidence due to broad category range"
                }
            ],
            "processing_summary": "Successfully categorized 3 transactions with high confidence scores"
        }
        return mock_response_content
    
    def test_mock_llm_single_transaction_categorization(self, mock_transactions):
        """Test categorizing a single transaction with mock LLM."""
        transaction = mock_transactions[0]  # Starbucks transaction
        
        # Mock LLM response for single transaction
        mock_categorization_data = {
            "transaction_id": "txn_starbucks_1",
            "ai_category": "Food & Dining",
            "ai_subcategory": "Coffee Shops", 
            "ai_confidence": 0.95,
            "ai_tags": ["caffeine", "quick-service"],
            "reasoning": "Starbucks transaction clearly indicates coffee purchase"
        }
        
        # Create categorization from mock LLM output
        categorization = TransactionCategorization(**mock_categorization_data)
        
        # Verify categorization matches transaction
        assert categorization.transaction_id == transaction.transaction_id
        assert categorization.ai_category == "Food & Dining"
        assert categorization.ai_subcategory == "Coffee Shops"
        assert categorization.ai_confidence == 0.95
        assert "caffeine" in categorization.ai_tags
        assert "coffee" in categorization.reasoning.lower()
    
    def test_mock_llm_batch_categorization(self, mock_llm_categorization_response):
        """Test batch categorization with mock LLM response."""
        # Create batch from mock LLM output
        batch = TransactionCategorizationBatch(**mock_llm_categorization_response)
        
        # Verify batch structure
        assert len(batch.categorizations) == 3
        assert batch.processing_summary == "Successfully categorized 3 transactions with high confidence scores"
        
        # Verify specific categorizations
        starbucks_cat = next(c for c in batch.categorizations if c.transaction_id == "txn_starbucks_1")
        assert starbucks_cat.ai_category == "Food & Dining"
        assert starbucks_cat.ai_confidence == 0.95
        
        shell_cat = next(c for c in batch.categorizations if c.transaction_id == "txn_shell_1")
        assert shell_cat.ai_category == "Transportation"
        assert shell_cat.ai_confidence == 0.92
        
        amazon_cat = next(c for c in batch.categorizations if c.transaction_id == "txn_amazon_1")
        assert amazon_cat.ai_category == "Shopping"
        assert amazon_cat.ai_confidence == 0.88
    
    def test_mock_llm_categorization_error_handling(self):
        """Test error handling in categorization with mock LLM."""
        # Test with invalid confidence score (should be clamped)
        invalid_data = {
            "transaction_id": "txn_1",
            "ai_category": "Food",
            "ai_subcategory": "Coffee",
            "ai_confidence": 1.5,  # Invalid - should be clamped to 1.0
            "reasoning": "Test"
        }
        
        categorization = TransactionCategorization(**invalid_data)
        assert categorization.ai_confidence == 1.0  # Should be clamped
        
        # Test with empty required fields (should raise error)
        with pytest.raises(ValueError):
            TransactionCategorization(
                transaction_id="txn_1",
                ai_category="",  # Empty - should raise error
                ai_subcategory="Coffee",
                ai_confidence=0.9,
                reasoning="Test"
            )
    
    def test_mock_llm_structured_output_compatibility(self):
        """Test that Pydantic models work correctly for LLM structured output."""
        # Simulate what an LLM would generate as structured output
        mock_llm_output_data = {
            "transaction_id": "txn_starbucks_1",
            "ai_category": "Food & Dining", 
            "ai_subcategory": "Coffee Shops",
            "ai_confidence": 0.95,
            "ai_tags": ["caffeine", "quick-service"],
            "reasoning": "Starbucks transaction clearly indicates coffee purchase"
        }
        
        # Test that our Pydantic model can handle LLM output
        categorization = TransactionCategorization(**mock_llm_output_data)
        
        # Verify the model structure is correct
        assert categorization.transaction_id == "txn_starbucks_1"
        assert categorization.ai_category == "Food & Dining"
        assert categorization.ai_subcategory == "Coffee Shops"
        assert categorization.ai_confidence == 0.95
        assert "caffeine" in categorization.ai_tags
        assert "starbucks" in categorization.reasoning.lower()
        
        # Test JSON schema generation for LLM (this is what LLMs need)
        schema = TransactionCategorization.model_json_schema()
        assert "properties" in schema
        assert "required" in schema
        assert set(schema["required"]) == {"transaction_id", "ai_category", "ai_subcategory", "ai_confidence", "reasoning"}
        
        # Test serialization (what we'd send as response)
        json_output = categorization.model_dump()
        assert json_output["ai_confidence"] == 0.95
        assert json_output["ai_tags"] == ["caffeine", "quick-service"]
        
        # Test round-trip (LLM output -> Pydantic -> JSON -> Pydantic)
        recreated = TransactionCategorization(**json_output)
        assert recreated.transaction_id == categorization.transaction_id
        assert recreated.ai_confidence == categorization.ai_confidence
        
        print("✅ Pydantic model is fully compatible with LLM structured output")


# Real LLM Integration Tests (Conditional)
@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY') and 
    not os.getenv('ANTHROPIC_API_KEY') and 
    not os.getenv('GOOGLE_API_KEY'),
    reason="No LLM API key available - set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
)
@pytest.mark.skipif(
    os.getenv('RUN_REAL_TESTS') != 'true',
    reason="Real API tests disabled - set RUN_REAL_TESTS=true to enable"
)
class TestTransactionCategorizationRealLLM:
    """Test transaction categorization with real LLM API calls."""
    
    @pytest.fixture
    def real_llm(self):
        """Create real LLM client for testing."""
        factory = LLMFactory()
        return factory.create_llm()
    
    @pytest.fixture
    def sample_transactions(self):
        """Clear, easily categorizable transactions for real LLM testing."""
        return [
            PlaidTransaction(
                transaction_id='txn_coffee_1',
                account_id='acc_test',
                amount='5.75',
                date='2024-01-15',
                name='Starbucks #1234',
                merchant_name='Starbucks',
                category=['Food and Drink'],
                pending=False
            ),
            PlaidTransaction(
                transaction_id='txn_gas_1', 
                account_id='acc_test',
                amount='42.50',
                date='2024-01-14',
                name='Shell Gas Station',
                merchant_name='Shell',
                category=['Transportation'],
                pending=False
            )
        ]
    
    def test_real_llm_single_transaction_categorization(self, real_llm, sample_transactions):
        """Test real LLM categorizing a single clear transaction."""
        transaction = sample_transactions[0]  # Starbucks
        
        # Create structured LLM for transaction categorization
        structured_llm = real_llm.with_structured_output(TransactionCategorization)
        
        # Create prompt for categorization
        system_prompt = """You are an expert at categorizing financial transactions.
        Analyze the transaction details and provide a structured categorization.
        
        Categories should be clear and specific (e.g., "Food & Dining", "Transportation", "Shopping").
        Subcategories should be more specific (e.g., "Coffee Shops", "Gas Stations", "Grocery Stores").
        Confidence should reflect how certain you are about the categorization (0.0 to 1.0).
        Tags should be relevant descriptive terms.
        Provide clear reasoning for your categorization."""
        
        transaction_details = f"""
        Transaction ID: {transaction.transaction_id}
        Name: {transaction.name}
        Merchant: {transaction.merchant_name}
        Amount: ${transaction.amount}
        Date: {transaction.date}
        Existing Categories: {transaction.category}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=transaction_details)
        ]
        
        # Call real LLM
        result = structured_llm.invoke(messages)
        
        # Verify result structure and content
        assert isinstance(result, TransactionCategorization)
        assert result.transaction_id == transaction.transaction_id
        assert result.ai_category  # Should not be empty
        assert result.ai_subcategory  # Should not be empty
        assert 0.0 <= result.ai_confidence <= 1.0
        assert result.reasoning  # Should provide reasoning
        
        # For Starbucks, expect high-confidence food/coffee categorization
        assert result.ai_confidence > 0.8  # Should be very confident
        assert any(word in result.ai_category.lower() for word in ['food', 'dining', 'coffee'])
        assert any(word in result.ai_subcategory.lower() for word in ['coffee', 'cafe'])
        
        print(f"✅ Real LLM categorized Starbucks: {result.ai_category} > {result.ai_subcategory} ({result.ai_confidence:.2f})")
        print(f"   Reasoning: {result.reasoning}")
    
    def test_real_llm_batch_categorization(self, real_llm, sample_transactions):
        """Test real LLM categorizing multiple transactions."""
        # Create structured LLM for batch categorization
        structured_llm = real_llm.with_structured_output(TransactionCategorizationBatch)
        
        system_prompt = """You are an expert at categorizing financial transactions.
        You will receive multiple transactions to categorize. Analyze each one and provide
        structured categorizations for all transactions.
        
        For each transaction:
        - Use clear, specific categories (e.g., "Food & Dining", "Transportation", "Shopping")
        - Provide specific subcategories (e.g., "Coffee Shops", "Gas Stations")
        - Set confidence based on how certain you are (0.0 to 1.0)
        - Add relevant tags
        - Explain your reasoning
        
        Provide a processing summary of your analysis."""
        
        transactions_text = "Transactions to categorize:\\n"
        for tx in sample_transactions:
            transactions_text += f"""
Transaction ID: {tx.transaction_id}
Name: {tx.name}
Merchant: {tx.merchant_name or 'N/A'}
Amount: ${tx.amount}
Date: {tx.date}
Existing Categories: {tx.category}
---"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=transactions_text)
        ]
        
        # Call real LLM for batch categorization
        result = structured_llm.invoke(messages)
        
        # Verify batch structure
        assert isinstance(result, TransactionCategorizationBatch)
        assert len(result.categorizations) == len(sample_transactions)
        assert result.processing_summary  # Should have summary
        
        # Verify each categorization
        for categorization in result.categorizations:
            assert categorization.transaction_id in [tx.transaction_id for tx in sample_transactions]
            assert categorization.ai_category
            assert categorization.ai_subcategory
            assert 0.0 <= categorization.ai_confidence <= 1.0
            assert categorization.reasoning
        
        # Find specific categorizations
        starbucks_cat = next(c for c in result.categorizations if c.transaction_id == 'txn_coffee_1')
        gas_cat = next(c for c in result.categorizations if c.transaction_id == 'txn_gas_1')
        
        # Verify Starbucks categorization
        assert starbucks_cat.ai_confidence > 0.8
        assert any(word in starbucks_cat.ai_category.lower() for word in ['food', 'dining'])
        
        # Verify gas station categorization  
        assert gas_cat.ai_confidence > 0.8
        assert 'transport' in gas_cat.ai_category.lower()
        
        print(f"✅ Real LLM batch categorized {len(result.categorizations)} transactions")
        print(f"   Starbucks: {starbucks_cat.ai_category} > {starbucks_cat.ai_subcategory}")
        print(f"   Gas: {gas_cat.ai_category} > {gas_cat.ai_subcategory}")
        print(f"   Summary: {result.processing_summary}")
    
    def test_real_llm_categorization_edge_cases(self, real_llm):
        """Test real LLM with edge cases and ambiguous transactions."""
        # Create an ambiguous transaction
        ambiguous_transaction = PlaidTransaction(
            transaction_id='txn_ambiguous_1',
            account_id='acc_test',
            amount='25.00',
            date='2024-01-15', 
            name='PAYMENT THANK YOU',
            merchant_name=None,
            category=['Payment'],
            pending=False
        )
        
        structured_llm = real_llm.with_structured_output(TransactionCategorization)
        
        system_prompt = """You are categorizing a financial transaction. Even for ambiguous 
        transactions, provide your best categorization with appropriate confidence level.
        For unclear transactions, use lower confidence scores and explain the ambiguity."""
        
        transaction_details = f"""
        Transaction ID: {ambiguous_transaction.transaction_id}
        Name: {ambiguous_transaction.name}
        Merchant: {ambiguous_transaction.merchant_name or 'None'}
        Amount: ${ambiguous_transaction.amount}
        Date: {ambiguous_transaction.date}
        Existing Categories: {ambiguous_transaction.category}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=transaction_details)
        ]
        
        result = structured_llm.invoke(messages)
        
        # Verify the LLM handled ambiguity appropriately
        assert isinstance(result, TransactionCategorization)
        assert result.transaction_id == ambiguous_transaction.transaction_id
        assert result.ai_confidence < 0.8  # Should have lower confidence for ambiguous transaction
        # Check for ambiguity-related terms in reasoning
        reasoning_lower = result.reasoning.lower()
        ambiguity_terms = ['ambiguous', 'unclear', 'ambiguity', 'uncertain', 'difficult to be certain']
        assert any(term in reasoning_lower for term in ambiguity_terms), f"Expected ambiguity terms in reasoning: {result.reasoning}"
        
        print(f"✅ Real LLM handled ambiguous transaction with confidence: {result.ai_confidence:.2f}")
        print(f"   Category: {result.ai_category} > {result.ai_subcategory}")
        print(f"   Reasoning: {result.reasoning}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])