"""
Shared test fixtures for transaction-related tests.
"""

import pytest
from decimal import Decimal
from app.models.plaid_models import PlaidTransaction


@pytest.fixture
def sample_transactions():
    """Sample transactions for testing (service and basic LLM tests)."""
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
def clear_transactions_for_llm():
    """Clear, easily categorizable transactions optimized for real LLM testing."""
    return [
        PlaidTransaction(
            transaction_id='txn_coffee_1',
            account_id='acc_test',
            amount=Decimal('5.75'),
            date='2024-01-15',
            name='Starbucks #1234',
            merchant_name='Starbucks',
            category=['Food and Drink'],
            pending=False
        ),
        PlaidTransaction(
            transaction_id='txn_gas_1',
            account_id='acc_test',
            amount=Decimal('42.50'),
            date='2024-01-14',
            name='Shell Gas Station',
            merchant_name='Shell',
            category=['Transportation'],
            pending=False
        )
    ]


@pytest.fixture
def mock_transactions_with_amazon():
    """Sample transactions including Amazon for batch testing."""
    return [
        PlaidTransaction(
            transaction_id='txn_starbucks_1',
            account_id='acc_123',
            amount=Decimal('4.75'),
            date='2024-01-15',
            name='STARBUCKS STORE #1234',
            merchant_name='Starbucks',
            category=['Food and Drink'],
            pending=False
        ),
        PlaidTransaction(
            transaction_id='txn_shell_1',
            account_id='acc_123',
            amount=Decimal('45.50'),
            date='2024-01-14',
            name='SHELL GAS STATION',
            merchant_name='Shell',
            category=['Transportation', 'Gas Stations'],
            pending=False
        ),
        PlaidTransaction(
            transaction_id='txn_amazon_1',
            account_id='acc_456',
            amount=Decimal('89.99'),
            date='2024-01-13',
            name='AMAZON.COM',
            merchant_name='Amazon',
            category=['Shops'],
            pending=False
        )
    ]