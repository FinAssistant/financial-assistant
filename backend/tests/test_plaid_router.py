"""
Unit tests for Plaid router - specifically testing multiple account creation scenarios.
Tests the race condition fix for duplicate account creation.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.routers.plaid import PlaidTokenExchangeRequest, exchange_public_token
from app.core.sqlmodel_models import ConnectedAccountCreate


class TestPlaidRouterMultipleAccounts:
    """Test multiple account creation scenarios."""

    @pytest.mark.asyncio
    async def test_exchange_token_multiple_accounts_success(self):
        """Test successful token exchange with multiple accounts (no duplicates)."""

        # Mock Plaid service responses
        mock_exchange_result = {
            "status": "success",
            "access_token": "access-sandbox-12345",
            "item_id": "item-sandbox-67890"
        }

        mock_accounts_result = {
            "status": "success",
            "accounts": [
                {
                    "account_id": "account_1",
                    "name": "Checking Account",
                    "type": "depository",
                    "subtype": "checking"
                },
                {
                    "account_id": "account_2",
                    "name": "Savings Account",
                    "type": "depository",
                    "subtype": "savings"
                },
                {
                    "account_id": "account_3",
                    "name": "Credit Card",
                    "type": "credit",
                    "subtype": "credit_card"
                }
            ],
            "item": {
                "institution_name": "Test Bank",
                "institution_id": "inst_123456"
            }
        }

        with patch('app.routers.plaid.plaid_service') as mock_plaid_service, \
             patch('app.routers.plaid.user_storage') as mock_user_storage, \
             patch('app.routers.plaid.ConversationHandler'):

            # Setup mocks
            mock_plaid_service.exchange_public_token.return_value = mock_exchange_result
            mock_plaid_service.get_accounts.return_value = mock_accounts_result

            # Mock sync database storage methods
            mock_user_storage.get_connected_account_by_plaid_id.return_value = None
            mock_user_storage.create_connected_account.side_effect = [
                {"id": "db_account_1"},
                {"id": "db_account_2"},
                {"id": "db_account_3"}
            ]

            # Test request
            request = PlaidTokenExchangeRequest(
                public_token="public-sandbox-token",
                session_id="test_session_123"
            )

            # Execute
            result = await exchange_public_token(request, "test_user_123")

            # Verify results
            assert result.status == "success"
            assert result.accounts_connected == 3
            assert len(result.account_ids) == 3
            assert result.account_ids == ["db_account_1", "db_account_2", "db_account_3"]

            # Verify database calls were made sequentially for each account
            assert mock_user_storage.get_connected_account_by_plaid_id.call_count == 3
            assert mock_user_storage.create_connected_account.call_count == 3

            # Verify the calls were made with correct account IDs
            get_calls = mock_user_storage.get_connected_account_by_plaid_id.call_args_list
            create_calls = mock_user_storage.create_connected_account.call_args_list

            assert get_calls[0][0] == ("test_user_123", "account_1")
            assert get_calls[1][0] == ("test_user_123", "account_2")
            assert get_calls[2][0] == ("test_user_123", "account_3")

    @pytest.mark.asyncio
    async def test_exchange_token_with_existing_accounts(self):
        """Test token exchange where some accounts already exist."""

        mock_exchange_result = {
            "status": "success",
            "access_token": "access-sandbox-12345",
            "item_id": "item-sandbox-67890"
        }

        mock_accounts_result = {
            "status": "success",
            "accounts": [
                {"account_id": "account_1", "name": "Checking Account", "type": "depository"},
                {"account_id": "account_2", "name": "Savings Account", "type": "depository"},
                {"account_id": "account_3", "name": "Credit Card", "type": "credit"}
            ],
            "item": {
                "institution_name": "Test Bank",
                "institution_id": "inst_123456"
            }
        }

        with patch('app.routers.plaid.plaid_service') as mock_plaid_service, \
             patch('app.routers.plaid.user_storage') as mock_user_storage, \
             patch('app.routers.plaid.ConversationHandler'):

            mock_plaid_service.exchange_public_token.return_value = mock_exchange_result
            mock_plaid_service.get_accounts.return_value = mock_accounts_result

            # Mock sync database storage methods - account_1 and account_3 already exist
            mock_user_storage.get_connected_account_by_plaid_id.side_effect = [
                {"id": "existing_account_1"},  # account_1 exists
                None,                          # account_2 doesn't exist
                {"id": "existing_account_3"}   # account_3 exists
            ]
            mock_user_storage.create_connected_account.return_value = {"id": "new_account_2"}

            request = PlaidTokenExchangeRequest(public_token="public-sandbox-token")

            # Execute
            result = await exchange_public_token(request, "test_user_123")

            # Verify results
            assert result.status == "success"
            assert result.accounts_connected == 3
            assert result.account_ids == ["existing_account_1", "new_account_2", "existing_account_3"]

            # Verify database calls
            assert mock_user_storage.get_connected_account_by_plaid_id.call_count == 3
            assert mock_user_storage.create_connected_account.call_count == 1  # Only called for account_2

    @pytest.mark.asyncio
    async def test_exchange_token_duplicate_creation_fails_without_handling(self):
        """Test that ValueError from duplicate creation causes HTTPException (current behavior before fix)."""

        mock_exchange_result = {
            "status": "success",
            "access_token": "access-sandbox-12345",
            "item_id": "item-sandbox-67890"
        }

        mock_accounts_result = {
            "status": "success",
            "accounts": [
                {"account_id": "account_1", "name": "Checking Account", "type": "depository"}
            ],
            "item": {
                "institution_name": "Test Bank",
                "institution_id": "inst_123456"
            }
        }

        with patch('app.routers.plaid.plaid_service') as mock_plaid_service, \
             patch('app.routers.plaid.user_storage') as mock_user_storage, \
             patch('app.routers.plaid.ConversationHandler'):

            mock_plaid_service.exchange_public_token.return_value = mock_exchange_result
            mock_plaid_service.get_accounts.return_value = mock_accounts_result

            # Mock sync database storage methods to simulate race condition:
            # 1. First check: account doesn't exist
            # 2. Create attempt: fails with "already exists"
            mock_user_storage.get_connected_account_by_plaid_id.return_value = None  # First check: not found
            mock_user_storage.create_connected_account.side_effect = ValueError(
                "Connected account with Plaid ID account_1 already exists for user test_user_123"
            )

            request = PlaidTokenExchangeRequest(public_token="public-sandbox-token")

            # This should raise an HTTPException with our current implementation
            # because we don't handle the ValueError from duplicate creation yet
            with pytest.raises(HTTPException) as exc_info:
                await exchange_public_token(request, "test_user_123")

            assert exc_info.value.status_code == 500
            assert "An unexpected error occurred during account connection" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_plaid_service_error_handling(self):
        """Test error handling when Plaid service fails."""

        with patch('app.routers.plaid.plaid_service') as mock_plaid_service:
            mock_plaid_service.exchange_public_token.return_value = {
                "status": "error",
                "error": "Invalid public token"
            }

            request = PlaidTokenExchangeRequest(public_token="invalid-token")

            with pytest.raises(HTTPException) as exc_info:
                await exchange_public_token(request, "test_user_123")

            assert exc_info.value.status_code == 400
            assert "Failed to exchange token" in str(exc_info.value.detail)