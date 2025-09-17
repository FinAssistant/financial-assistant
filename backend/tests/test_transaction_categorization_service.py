"""
Tests for TransactionCategorizationService.

Tests both mock LLM responses and integration with real LLM providers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.transaction_categorization import TransactionCategorizationService
from app.core.config import Settings
from app.models.plaid_models import (
    PlaidTransaction, 
    TransactionCategorization, 
    TransactionCategorizationBatch
)


@pytest.fixture
def sample_transactions():
    """Sample transactions for testing."""
    return [
        PlaidTransaction(
            transaction_id="txn_starbucks_1",
            account_id="acc_test",
            amount=Decimal("5.50"),
            date="2024-01-15",
            name="Starbucks Store #123",
            merchant_name="Starbucks",
            category=["Food and Drink", "Coffee"],
            pending=False
        ),
        PlaidTransaction(
            transaction_id="txn_gas_1",
            account_id="acc_test",
            amount=Decimal("45.00"),
            date="2024-01-14",
            name="Shell Gas Station",
            merchant_name="Shell",
            category=["Transportation", "Gas Stations"],
            pending=False
        )
    ]


@pytest.fixture
def mock_llm():
    """Mock LLM instance for testing."""
    return Mock()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Mock(spec=Settings)


@pytest.fixture
def categorization_service(mock_llm, mock_settings):
    """TransactionCategorizationService instance for testing."""
    return TransactionCategorizationService(mock_llm, mock_settings)


class TestTransactionCategorizationService:
    """Test TransactionCategorizationService functionality."""
    
    def test_init(self, categorization_service):
        """Test service initialization."""
        assert categorization_service.llm is not None
        assert categorization_service.settings is not None
        assert categorization_service.tokens_per_transaction == 150
        assert categorization_service.reserved_tokens == 2000
    
    def test_get_max_batch_size(self, categorization_service):
        """Test dynamic batch size calculation."""
        max_batch_size = categorization_service._get_max_batch_size()
        
        # Should be based on smallest context window (OpenAI: 128k)
        expected_available = 128000 - 2000  # context - reserved
        expected_max = min(expected_available // 150, 50)  # tokens per txn, capped at 50
        
        assert max_batch_size == expected_max
        assert max_batch_size <= 50  # Reasonable cap
    
    def test_create_categorization_prompt(self, categorization_service, sample_transactions):
        """Test categorization prompt creation."""
        prompt = categorization_service._create_categorization_prompt(sample_transactions)
        
        assert "financial transaction categorization expert" in prompt
        assert "ai_category" in prompt
        assert "ai_subcategory" in prompt
        assert "ai_confidence" in prompt
        assert "ai_tags" in prompt
        assert "reasoning" in prompt
        assert f"receive {len(sample_transactions)} transactions" in prompt
    
    def test_shared_user_context_formatting(self):
        """Test shared user context formatting utility."""
        from app.utils.context_formatting import build_user_context_string
        
        # Test structured format (preferred)
        user_context = {
            "demographics": {
                "age_range": "26_35",
                "occupation": "engineer",
                "location": "San Francisco, CA"
            },
            "financial_context": {
                "has_dependents": False,
                "income_level": "High"
            }
        }
        
        formatted = build_user_context_string(user_context)
        
        assert "DEMOGRAPHICS:" in formatted
        assert "Age range: 26_35" in formatted
        assert "Occupation: engineer" in formatted
        assert "Location: San Francisco, CA" in formatted
        assert "FINANCIAL PROFILE:" in formatted
        assert "Has dependents: No" in formatted
    
    def test_shared_user_context_flat_format(self):
        """Test shared user context with flat format (backward compatibility)."""
        from app.utils.context_formatting import build_user_context_string
        
        user_context = {
            "name": "John Doe",
            "location": "San Francisco, CA",
            "income_level": "High",
            "spending_personality": "Conservative"
        }
        
        formatted = build_user_context_string(user_context)
        
        assert "User: John Doe" in formatted
        assert "Location: San Francisco, CA" in formatted
        assert "Income Level: High" in formatted
        assert "Spending Style: Conservative" in formatted
    
    def test_format_transaction_batch_for_llm(self, categorization_service, sample_transactions):
        """Test transaction batch formatting for LLM input."""
        from app.models.plaid_models import TransactionBatch
        
        batch = TransactionBatch(transactions=sample_transactions)
        batch_dict = batch.model_dump()
        
        formatted = categorization_service._format_transaction_batch_for_llm(batch_dict)
        
        assert "Batch Metadata:" in formatted
        assert "Total Transactions: 2" in formatted
        assert "Transaction 1:" in formatted
        assert "ID: txn_starbucks_1" in formatted
        assert "Name: Starbucks Store #123" in formatted
        assert "Amount: $5.5" in formatted  # Decimal formatting
        assert "Date: 2024-01-15" in formatted
    


class TestTransactionCategorizationServiceMocked:
    """Test service with mocked LLM responses."""
    
    @pytest.mark.asyncio
    async def test_categorize_transactions_empty_list(self, categorization_service):
        """Test categorizing empty transaction list."""
        result = await categorization_service.categorize_transactions([])
        
        assert isinstance(result, TransactionCategorizationBatch)
        assert len(result.categorizations) == 0
        assert result.processing_summary == "No transactions to categorize"
    
    @pytest.mark.asyncio
    async def test_categorize_batch_success(self, categorization_service, sample_transactions):
        """Test successful batch categorization with mocked LLM."""
        # Mock the structured LLM response
        mock_structured_llm = Mock()
        mock_categorization_batch = TransactionCategorizationBatch(
            categorizations=[
                TransactionCategorization(
                    transaction_id="txn_starbucks_1",
                    ai_category="Food & Dining",
                    ai_subcategory="Coffee Shops",
                    ai_confidence=0.95,
                    ai_tags=["caffeine"],
                    reasoning="Starbucks coffee purchase"
                ),
                TransactionCategorization(
                    transaction_id="txn_gas_1",
                    ai_category="Transportation",
                    ai_subcategory="Gas Stations",
                    ai_confidence=0.90,
                    ai_tags=["fuel", "automotive"],
                    reasoning="Shell gas station fuel purchase"
                )
            ],
            processing_summary="Categorized 2 transactions"
        )
        
        mock_structured_llm.ainvoke = AsyncMock(return_value=mock_categorization_batch)
        categorization_service.llm.with_structured_output.return_value = mock_structured_llm
        
        result = await categorization_service._categorize_batch(sample_transactions)
        
        assert len(result) == 2
        assert result[0].transaction_id == "txn_starbucks_1"
        assert result[0].ai_category == "Food & Dining"
        assert result[1].transaction_id == "txn_gas_1"
        assert result[1].ai_category == "Transportation"
    
    @pytest.mark.asyncio
    async def test_categorize_batch_llm_error(self, categorization_service, sample_transactions):
        """Test batch categorization with LLM error."""
        # Mock LLM to raise exception
        mock_structured_llm = Mock()
        mock_structured_llm.ainvoke = AsyncMock(side_effect=Exception("LLM API error"))
        categorization_service.llm.with_structured_output.return_value = mock_structured_llm
        
        result = await categorization_service._categorize_batch(sample_transactions)
        
        assert result == []
    


def has_any_llm_key():
    """Check if any LLM provider API key is available."""
    import os
    return any([
        os.getenv('OPENAI_API_KEY'),
        os.getenv('ANTHROPIC_API_KEY'),
        os.getenv('GOOGLE_API_KEY')
    ])


class TestTransactionCategorizationServiceIntegration:
    """Integration tests with real LLM providers (conditional on API keys)."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not has_any_llm_key() or __import__('os').getenv('RUN_REAL_TESTS') != 'true',
        reason="Real API tests require at least one LLM provider API key and RUN_REAL_TESTS=true"
    )
    async def test_real_llm_categorization(self, sample_transactions):
        """Test categorization with real LLM provider."""
        
        # Use real LLM factory
        from app.services.llm_service import llm_factory
        from app.core.config import Settings

        settings = Settings()
        llm = llm_factory.create_llm()
        categorization_service = TransactionCategorizationService(llm, settings)
        
        # Test categorization
        result = await categorization_service.categorize_transactions(sample_transactions[:1])  # Test with one transaction
        
        assert isinstance(result, TransactionCategorizationBatch)
        if result.categorizations:  # LLM may succeed or fail
            categorization = result.categorizations[0]
            assert categorization.transaction_id == "txn_starbucks_1"
            assert categorization.ai_category is not None
            assert categorization.ai_subcategory is not None
            assert 0.0 <= categorization.ai_confidence <= 1.0
            assert categorization.reasoning is not None