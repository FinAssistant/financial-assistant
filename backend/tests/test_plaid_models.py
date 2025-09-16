"""
Unit tests for Pydantic models used for Plaid transaction data.
Tests both basic model functionality and LLM integration scenarios.
"""

import pytest
from decimal import Decimal

from app.models.plaid_models import (
    PlaidTransaction,
    TransactionBatch,
    TransactionCategorization,
    TransactionCategorizationBatch
)


class TestPlaidTransaction:
    """Test PlaidTransaction Pydantic model."""
    
    def test_create_transaction_with_valid_data(self):
        """Test creating a PlaidTransaction with valid data."""
        data = {
            'transaction_id': 'txn_123456',
            'account_id': 'acc_789123',
            'amount': '25.50',
            'date': '2024-01-15',
            'name': 'Starbucks Coffee',
            'merchant_name': 'Starbucks',
            'category': ['Food and Drink', 'Coffee'],
            'pending': False
        }
        
        transaction = PlaidTransaction(**data)
        
        assert transaction.transaction_id == 'txn_123456'
        assert transaction.account_id == 'acc_789123'
        assert transaction.amount == Decimal('25.50')
        assert transaction.date == '2024-01-15'
        assert transaction.name == 'Starbucks Coffee'
        assert transaction.merchant_name == 'Starbucks'
        assert transaction.category == ['Food and Drink', 'Coffee']
        assert transaction.pending is False
    
    def test_transaction_amount_conversion(self):
        """Test that amount is properly converted to Decimal."""
        # Test with string
        transaction1 = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_1', 
            amount='123.45',
            name='Test'
        )
        assert isinstance(transaction1.amount, Decimal)
        assert transaction1.amount == Decimal('123.45')
        
        # Test with float
        transaction2 = PlaidTransaction(
            transaction_id='txn_2',
            account_id='acc_1',
            amount=123.45,
            name='Test'
        )
        assert isinstance(transaction2.amount, Decimal)
        assert transaction2.amount == Decimal('123.45')
        
        # Test with None (should default to 0.00)
        transaction3 = PlaidTransaction(
            transaction_id='txn_3',
            account_id='acc_1',
            amount=None,
            name='Test'
        )
        assert transaction3.amount == Decimal('0.00')
    
    def test_transaction_date_handling(self):
        """Test date field handling for LLM compatibility."""
        # Test with string date
        transaction1 = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_1',
            amount='10.00',
            name='Test',
            date='2024-01-15'
        )
        assert transaction1.date == '2024-01-15'
        
        # Test with None
        transaction2 = PlaidTransaction(
            transaction_id='txn_2',
            account_id='acc_1',
            amount='10.00',
            name='Test',
            date=None
        )
        assert transaction2.date is None
    
    def test_transaction_name_cleaning(self):
        """Test transaction name cleaning and validation."""
        # Test normal name
        transaction1 = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_1',
            amount='10.00',
            name='  Starbucks Coffee  '
        )
        assert transaction1.name == 'Starbucks Coffee'
        
        # Test empty name
        transaction2 = PlaidTransaction(
            transaction_id='txn_2',
            account_id='acc_1',
            amount='10.00',
            name=''
        )
        assert transaction2.name == 'Unknown Transaction'
    
    def test_transaction_category_handling(self):
        """Test category list handling."""
        # Test with list
        transaction1 = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_1',
            amount='10.00',
            name='Test',
            category=['Food', 'Restaurant']
        )
        assert transaction1.category == ['Food', 'Restaurant']
        
        # Test with string (should convert to list)
        transaction2 = PlaidTransaction(
            transaction_id='txn_2',
            account_id='acc_1',
            amount='10.00',
            name='Test',
            category='Food'
        )
        assert transaction2.category == ['Food']
        
        # Test with None (should default to empty list)
        transaction3 = PlaidTransaction(
            transaction_id='txn_3',
            account_id='acc_1',
            amount='10.00',
            name='Test',
            category=None
        )
        assert transaction3.category == []
    
    def test_ai_categorization_fields(self):
        """Test AI categorization fields are properly handled."""
        transaction = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_1',
            amount='10.00',
            name='Test',
            ai_category='Food & Dining',
            ai_subcategory='Coffee Shops',
            ai_confidence=0.95,
            ai_tags=['quick-service', 'caffeine']
        )
        
        assert transaction.ai_category == 'Food & Dining'
        assert transaction.ai_subcategory == 'Coffee Shops'
        assert transaction.ai_confidence == 0.95
        assert transaction.ai_tags == ['quick-service', 'caffeine']


class TestTransactionCategorization:
    """Test TransactionCategorization model for LLM structured output."""
    
    def test_create_categorization_valid_data(self):
        """Test creating a TransactionCategorization with valid data."""
        data = {
            'transaction_id': 'txn_123',
            'ai_category': 'Food & Dining',
            'ai_subcategory': 'Coffee Shops',
            'ai_confidence': 0.95,
            'ai_tags': ['caffeine', 'quick-service', 'daily-habit'],
            'reasoning': 'Transaction at Starbucks clearly indicates coffee purchase'
        }
        
        categorization = TransactionCategorization(**data)
        
        assert categorization.transaction_id == 'txn_123'
        assert categorization.ai_category == 'Food & Dining'
        assert categorization.ai_subcategory == 'Coffee Shops'
        assert categorization.ai_confidence == 0.95
        assert categorization.ai_tags == ['caffeine', 'quick-service', 'daily-habit']
        assert categorization.reasoning == 'Transaction at Starbucks clearly indicates coffee purchase'
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Test valid confidence
        categorization1 = TransactionCategorization(
            transaction_id='txn_1',
            ai_category='Food',
            ai_subcategory='Coffee',
            ai_confidence=0.85,
            reasoning='Valid confidence'
        )
        assert categorization1.ai_confidence == 0.85
        
        # Test confidence > 1.0 (should be clamped to 1.0)
        categorization2 = TransactionCategorization(
            transaction_id='txn_2',
            ai_category='Food',
            ai_subcategory='Coffee',
            ai_confidence=1.5,
            reasoning='High confidence'
        )
        assert categorization2.ai_confidence == 1.0
        
        # Test confidence < 0.0 (should be clamped to 0.0)
        categorization3 = TransactionCategorization(
            transaction_id='txn_3',
            ai_category='Food',
            ai_subcategory='Coffee',
            ai_confidence=-0.5,
            reasoning='Low confidence'
        )
        assert categorization3.ai_confidence == 0.0
    
    def test_string_field_validation(self):
        """Test string field validation."""
        # Test with whitespace (should be stripped)
        categorization = TransactionCategorization(
            transaction_id='txn_1',
            ai_category='  Food & Dining  ',
            ai_subcategory='  Coffee  ',
            ai_confidence=0.9,
            reasoning='  Valid reasoning  '
        )
        
        assert categorization.ai_category == 'Food & Dining'
        assert categorization.ai_subcategory == 'Coffee'
        assert categorization.reasoning == 'Valid reasoning'
        
        # Test with empty strings (should raise error)
        with pytest.raises(ValueError, match="Field cannot be empty"):
            TransactionCategorization(
                transaction_id='txn_1',
                ai_category='',
                ai_subcategory='Coffee',
                ai_confidence=0.9,
                reasoning='Valid'
            )
    
    def test_tags_validation(self):
        """Test tags list validation."""
        # Test with valid tags
        categorization1 = TransactionCategorization(
            transaction_id='txn_1',
            ai_category='Food',
            ai_subcategory='Coffee',
            ai_confidence=0.9,
            ai_tags=['tag1', '  tag2  ', 'tag3'],
            reasoning='Valid'
        )
        assert categorization1.ai_tags == ['tag1', 'tag2', 'tag3']
        
        # Test with empty list
        categorization2 = TransactionCategorization(
            transaction_id='txn_2',
            ai_category='Food',
            ai_subcategory='Coffee',
            ai_confidence=0.9,
            ai_tags=[],
            reasoning='Valid'
        )
        assert categorization2.ai_tags == []
        
        # Test with None (should default to empty list)
        categorization3 = TransactionCategorization(
            transaction_id='txn_3',
            ai_category='Food',
            ai_subcategory='Coffee',
            ai_confidence=0.9,
            reasoning='Valid'
        )
        assert categorization3.ai_tags == []
    
    def test_llm_json_schema_generation(self):
        """Test JSON schema generation for LLM structured output."""
        schema = TransactionCategorization.model_json_schema()
        
        # Verify schema structure
        assert 'properties' in schema
        assert 'required' in schema
        
        # Check required fields
        required_fields = schema['required']
        expected_required = ['transaction_id', 'ai_category', 'ai_subcategory', 'ai_confidence', 'reasoning']
        for field in expected_required:
            assert field in required_fields
        
        # Check specific field properties
        properties = schema['properties']
        
        # Check confidence field type
        confidence_field = properties['ai_confidence']
        assert confidence_field['type'] == 'number'
        # Note: We use field validators instead of schema constraints for flexibility
        
        # Check tags field is array
        tags_field = properties['ai_tags']
        assert tags_field['type'] == 'array'
        assert tags_field['items']['type'] == 'string'


class TestTransactionBatch:
    """Test TransactionBatch model."""
    
    def test_create_batch_with_transactions(self):
        """Test creating TransactionBatch with automatic metadata calculation."""
        # Create sample transactions
        transaction1 = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_123',
            amount='25.50',
            date='2024-01-15',
            name='Starbucks'
        )
        
        transaction2 = PlaidTransaction(
            transaction_id='txn_2',
            account_id='acc_456',
            amount='15.75',
            date='2024-01-14',
            name='Subway'
        )
        
        batch = TransactionBatch(transactions=[transaction1, transaction2])
        
        # Check automatic metadata calculation
        assert batch.total_count == 2
        assert set(batch.accounts_included) == {'acc_123', 'acc_456'}
        assert batch.date_range_start == '2024-01-14'  # Earlier date
        assert batch.date_range_end == '2024-01-15'    # Later date
    
    def test_empty_batch(self):
        """Test empty TransactionBatch."""
        batch = TransactionBatch(transactions=[])
        
        assert batch.total_count == 0
        assert batch.accounts_included == []
        assert batch.date_range_start is None
        assert batch.date_range_end is None
    
    def test_batch_with_none_dates(self):
        """Test batch with transactions that have None dates."""
        transaction = PlaidTransaction(
            transaction_id='txn_1',
            account_id='acc_123',
            amount='25.50',
            date=None,
            name='Test'
        )
        
        batch = TransactionBatch(transactions=[transaction])
        
        assert batch.total_count == 1
        assert batch.accounts_included == ['acc_123']
        assert batch.date_range_start is None
        assert batch.date_range_end is None


class TestTransactionCategorizationBatch:
    """Test TransactionCategorizationBatch for batch LLM output."""
    
    def test_create_categorization_batch(self):
        """Test creating batch of categorizations."""
        categorization1 = TransactionCategorization(
            transaction_id='txn_1',
            ai_category='Food & Dining',
            ai_subcategory='Coffee',
            ai_confidence=0.95,
            reasoning='Starbucks transaction'
        )
        
        categorization2 = TransactionCategorization(
            transaction_id='txn_2',
            ai_category='Transportation',
            ai_subcategory='Gas',
            ai_confidence=0.90,
            reasoning='Shell gas station'
        )
        
        batch = TransactionCategorizationBatch(
            categorizations=[categorization1, categorization2],
            processing_summary='Successfully categorized 2 transactions'
        )
        
        assert len(batch.categorizations) == 2
        assert batch.processing_summary == 'Successfully categorized 2 transactions'
        assert batch.categorizations[0].transaction_id == 'txn_1'
        assert batch.categorizations[1].transaction_id == 'txn_2'
    
    def test_empty_summary_default(self):
        """Test default summary when empty."""
        batch = TransactionCategorizationBatch(
            categorizations=[],
            processing_summary=''
        )
        
        assert batch.processing_summary == 'Categorization completed'


class TestLLMCompatibility:
    """Test models work correctly with LLM libraries."""
    
    def test_transaction_categorization_serialization(self):
        """Test that TransactionCategorization can be serialized for LLM output."""
        categorization = TransactionCategorization(
            transaction_id='txn_123',
            ai_category='Food & Dining',
            ai_subcategory='Coffee Shops',
            ai_confidence=0.95,
            ai_tags=['caffeine', 'quick-service'],
            reasoning='Clear coffee purchase at Starbucks'
        )
        
        # Test JSON serialization (what LLMs would output)
        json_dict = categorization.model_dump()
        
        expected_keys = {
            'transaction_id', 'ai_category', 'ai_subcategory', 
            'ai_confidence', 'ai_tags', 'reasoning'
        }
        assert set(json_dict.keys()) == expected_keys
        assert json_dict['ai_confidence'] == 0.95
        assert json_dict['ai_tags'] == ['caffeine', 'quick-service']
        
        # Test round-trip deserialization
        recreated = TransactionCategorization(**json_dict)
        assert recreated.transaction_id == categorization.transaction_id
        assert recreated.ai_confidence == categorization.ai_confidence
    
    def test_batch_categorization_for_llm_output(self):
        """Test batch categorization model for structured LLM output."""
        # Simulate what an LLM might generate as structured output
        llm_output_data = {
            'categorizations': [
                {
                    'transaction_id': 'txn_1',
                    'ai_category': 'Food & Dining',
                    'ai_subcategory': 'Coffee Shops',
                    'ai_confidence': 0.95,
                    'ai_tags': ['caffeine'],
                    'reasoning': 'Starbucks purchase'
                },
                {
                    'transaction_id': 'txn_2', 
                    'ai_category': 'Transportation',
                    'ai_subcategory': 'Gas Stations',
                    'ai_confidence': 0.88,
                    'ai_tags': ['fuel', 'automotive'],
                    'reasoning': 'Shell gas station fill-up'
                }
            ],
            'processing_summary': 'Analyzed 2 transactions with high confidence'
        }
        
        batch = TransactionCategorizationBatch(**llm_output_data)
        
        assert len(batch.categorizations) == 2
        assert batch.categorizations[0].ai_category == 'Food & Dining'
        assert batch.categorizations[1].ai_category == 'Transportation'
        assert batch.processing_summary == 'Analyzed 2 transactions with high confidence'
        
        # Test that it can be converted back to dict (for storage/API responses)
        output_dict = batch.model_dump()
        assert 'categorizations' in output_dict
        assert 'processing_summary' in output_dict
        assert len(output_dict['categorizations']) == 2