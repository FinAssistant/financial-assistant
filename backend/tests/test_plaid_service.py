"""
Unit tests for PlaidService.
Tests all Plaid API operations with mocked responses.
"""

from unittest.mock import Mock, patch
from datetime import datetime

from app.services.plaid_service import PlaidService
from plaid.exceptions import ApiException


class TestPlaidServiceInitialization:
    """Test PlaidService initialization and configuration."""
    
    @patch('app.services.plaid_service.settings')
    def test_init_with_valid_config(self, mock_settings):
        """Test PlaidService initialization with valid configuration."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        mock_settings.plaid_env = "sandbox"
        
        service = PlaidService()
        assert service.client is not None
    
    @patch('app.services.plaid_service.settings')
    def test_init_without_credentials(self, mock_settings):
        """Test PlaidService initialization without credentials."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        assert service.client is None
    
    @patch('app.services.plaid_service.settings')
    def test_init_with_missing_client_id(self, mock_settings):
        """Test PlaidService initialization with missing client ID."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        assert service.client is None


class TestPlaidServiceDataSanitization:
    """Test data sanitization methods."""
    
    def test_sanitize_account_data_complete(self):
        """Test sanitizing complete account data."""
        service = PlaidService()
        raw_account = {
            "account_id": "test_account_123",
            "name": "Test Checking",
            "type": "depository",
            "subtype": "checking",
            "mask": "1234",
            "balances": {
                "current": 1000.50,
                "available": 950.25,
                "limit": None,
                "iso_currency_code": "USD"
            },
            "sensitive_field": "should_be_removed"
        }
        
        sanitized = service._sanitize_account_data(raw_account)
        
        assert sanitized["account_id"] == "test_account_123"
        assert sanitized["name"] == "Test Checking"
        assert sanitized["type"] == "depository"
        assert sanitized["subtype"] == "checking"
        assert sanitized["mask"] == "1234"
        assert sanitized["balances"]["current"] == 1000.50
        assert sanitized["balances"]["available"] == 950.25
        assert sanitized["balances"]["currency"] == "USD"
        assert "sensitive_field" not in sanitized
    
    def test_sanitize_account_data_empty(self):
        """Test sanitizing empty account data."""
        service = PlaidService()
        assert service._sanitize_account_data({}) == {}
        assert service._sanitize_account_data(None) == {}
    
    def test_sanitize_transaction_data_complete(self):
        """Test sanitizing complete transaction data."""
        service = PlaidService()
        raw_transaction = {
            "transaction_id": "trans_123",
            "account_id": "acc_456",
            "amount": 25.99,
            "date": datetime.now().date(),
            "name": "Coffee Shop",
            "merchant_name": "Local Coffee",
            "category": ["Food and Drink", "Restaurants"],
            "pending": False,
            "account_owner": "should_be_removed"
        }
        
        sanitized = service._sanitize_transaction_data(raw_transaction)
        
        assert sanitized["transaction_id"] == "trans_123"
        assert sanitized["account_id"] == "acc_456"
        assert sanitized["amount"] == 25.99
        assert sanitized["name"] == "Coffee Shop"
        assert sanitized["merchant_name"] == "Local Coffee"
        assert sanitized["category"] == ["Food and Drink", "Restaurants"]
        assert sanitized["pending"] is False
        assert "account_owner" not in sanitized
    
    def test_sanitize_transaction_data_empty(self):
        """Test sanitizing empty transaction data."""
        service = PlaidService()
        assert service._sanitize_transaction_data({}) == {}
        assert service._sanitize_transaction_data(None) == {}


class TestPlaidServiceErrorHandling:
    """Test error handling methods."""
    
    def test_handle_invalid_credentials_error(self):
        """Test handling invalid credentials error."""
        service = PlaidService()
        mock_exception = Mock(spec=ApiException)
        mock_exception.code = "INVALID_CREDENTIALS"
        mock_exception.__str__ = Mock(return_value="INVALID_CREDENTIALS error")
        
        result = service._handle_plaid_error(mock_exception)
        
        assert result["status"] == "error"
        assert "Invalid Plaid credentials" in result["error"]
    
    def test_handle_rate_limit_error(self):
        """Test handling rate limit error."""
        service = PlaidService()
        mock_exception = Mock(spec=ApiException)
        mock_exception.code = "RATE_LIMIT_EXCEEDED"
        mock_exception.__str__ = Mock(return_value="RATE_LIMIT exceeded")
        
        result = service._handle_plaid_error(mock_exception)
        
        assert result["status"] == "error"
        assert "Rate limit exceeded" in result["error"]
    
    def test_handle_item_login_required_error(self):
        """Test handling item login required error."""
        service = PlaidService()
        mock_exception = Mock(spec=ApiException)
        mock_exception.code = "ITEM_LOGIN_REQUIRED"
        mock_exception.__str__ = Mock(return_value="ITEM_LOGIN_REQUIRED")
        
        result = service._handle_plaid_error(mock_exception)
        
        assert result["status"] == "error"
        assert "Bank login required" in result["error"]
    
    def test_handle_unknown_error(self):
        """Test handling unknown error."""
        service = PlaidService()
        mock_exception = Mock(spec=ApiException)
        mock_exception.code = "UNKNOWN_ERROR"
        mock_exception.__str__ = Mock(return_value="Unknown error occurred")
        
        result = service._handle_plaid_error(mock_exception)
        
        assert result["status"] == "error"
        assert "An error occurred accessing financial data" in result["error"]


class TestPlaidServiceLinkToken:
    """Test link token creation methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_create_link_token_success(self, mock_settings):
        """Test successful link token creation."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        service.client.link_token_create.return_value = {
            "link_token": "link-sandbox-test-token",
            "expiration": "2024-12-31T23:59:59Z",
            "request_id": "req_123"
        }
        
        result = service.create_link_token("user_123", ["transactions", "accounts"])
        
        assert result["status"] == "success"
        assert result["link_token"] == "link-sandbox-test-token"
        assert result["expiration"] == "2024-12-31T23:59:59Z"
        assert result["request_id"] == "req_123"
    
    @patch('app.services.plaid_service.settings')
    def test_create_link_token_no_client(self, mock_settings):
        """Test link token creation without client."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.create_link_token("user_123")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]
    
    @patch('app.services.plaid_service.settings')
    def test_create_link_token_api_exception(self, mock_settings):
        """Test link token creation with API exception."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        service.client.link_token_create.side_effect = ApiException("INVALID_CREDENTIALS")
        
        result = service.create_link_token("user_123")
        
        assert result["status"] == "error"
    
    @patch('app.services.plaid_service.settings')
    def test_create_link_token_default_products(self, mock_settings):
        """Test link token creation with default products."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        service.client.link_token_create.return_value = {
            "link_token": "link-token",
            "expiration": "2024-12-31T23:59:59Z"
        }
        
        result = service.create_link_token("user_123")  # No products specified
        
        assert result["status"] == "success"
        service.client.link_token_create.assert_called_once()


class TestPlaidServiceTokenExchange:
    """Test public token exchange methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_exchange_public_token_success(self, mock_settings):
        """Test successful public token exchange."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        service.client.item_public_token_exchange.return_value = {
            "access_token": "access-sandbox-test-token",
            "item_id": "item_123",
            "request_id": "req_456"
        }
        
        result = service.exchange_public_token("public-sandbox-token")
        
        assert result["status"] == "success"
        assert result["access_token"] == "access-sandbox-test-token"
        assert result["item_id"] == "item_123"
        assert result["request_id"] == "req_456"
    
    @patch('app.services.plaid_service.settings')
    def test_exchange_public_token_no_client(self, mock_settings):
        """Test public token exchange without client."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.exchange_public_token("public-token")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]


class TestPlaidServiceAccounts:
    """Test account retrieval methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_get_accounts_success(self, mock_settings):
        """Test successful account retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        # Mock account response
        mock_account = Mock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_123",
            "name": "Test Checking",
            "type": "depository",
            "subtype": "checking",
            "mask": "1234",
            "balances": {
                "current": 1000.0,
                "available": 950.0,
                "iso_currency_code": "USD"
            }
        }
        
        service.client.accounts_get.return_value = {
            "accounts": [mock_account],
            "item": {
                "institution_id": "inst_123",
                "item_id": "item_456"
            },
            "request_id": "req_789"
        }
        
        result = service.get_accounts("access-token-123")
        
        assert result["status"] == "success"
        assert len(result["accounts"]) == 1
        assert result["accounts"][0]["account_id"] == "acc_123"
        assert result["accounts"][0]["name"] == "Test Checking"
        assert result["item"]["institution_id"] == "inst_123"
    
    @patch('app.services.plaid_service.settings')
    def test_get_accounts_no_client(self, mock_settings):
        """Test account retrieval without client."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.get_accounts("access-token")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]


class TestPlaidServiceTransactions:
    """Test transaction retrieval methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_get_transactions_success(self, mock_settings):
        """Test successful transaction retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        # Mock transaction response
        mock_transaction = Mock()
        mock_transaction.to_dict.return_value = {
            "transaction_id": "trans_123",
            "account_id": "acc_456",
            "amount": 25.99,
            "date": datetime.now().date(),
            "name": "Coffee Shop",
            "category": ["Food and Drink"]
        }
        
        service.client.transactions_get.return_value = {
            "transactions": [mock_transaction],
            "total_transactions": 1,
            "request_id": "req_123"
        }
        
        result = service.get_transactions("access-token-123")
        
        assert result["status"] == "success"
        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["transaction_id"] == "trans_123"
        assert result["transactions"][0]["amount"] == 25.99
        assert result["total_transactions"] == 1
    
    @patch('app.services.plaid_service.settings')
    def test_get_transactions_with_date_range(self, mock_settings):
        """Test transaction retrieval with custom date range."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        mock_transaction = Mock()
        mock_transaction.to_dict.return_value = {
            "transaction_id": "trans_123",
            "account_id": "acc_456",
            "amount": 25.99,
            "name": "Coffee Shop"
        }
        
        service.client.transactions_get.return_value = {
            "transactions": [mock_transaction],
            "total_transactions": 1
        }
        
        result = service.get_transactions(
            "access-token-123", 
            start_date="2024-01-01", 
            end_date="2024-01-31"
        )
        
        assert result["status"] == "success"
        assert result["date_range"]["start"] == "2024-01-01"
        assert result["date_range"]["end"] == "2024-01-31"
    
    @patch('app.services.plaid_service.settings')
    def test_get_transactions_with_account_filter(self, mock_settings):
        """Test transaction retrieval with account filter."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        mock_transaction = Mock()
        mock_transaction.to_dict.return_value = {
            "transaction_id": "trans_123",
            "account_id": "acc_456",
            "amount": 25.99
        }
        
        service.client.transactions_get.return_value = {
            "transactions": [mock_transaction],
            "total_transactions": 1
        }
        
        result = service.get_transactions("access-token-123", account_id="acc_456")
        
        assert result["status"] == "success"
        service.client.transactions_get.assert_called_once()


class TestPlaidServiceBalances:
    """Test balance retrieval methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_get_balances_success(self, mock_settings):
        """Test successful balance retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        # Mock balance response
        mock_account = Mock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_123",
            "name": "Test Checking",
            "mask": "1234",
            "type": "depository",
            "balances": {
                "current": 1500.75,
                "available": 1450.25,
                "limit": None,
                "iso_currency_code": "USD"
            }
        }
        
        service.client.accounts_balance_get.return_value = {
            "accounts": [mock_account],
            "request_id": "req_balance_123"
        }
        
        result = service.get_balances("access-token-123")
        
        assert result["status"] == "success"
        assert len(result["balances"]) == 1
        assert result["balances"][0]["account_id"] == "acc_123"
        assert result["balances"][0]["balances"]["current"] == 1500.75
        assert result["balances"][0]["balances"]["available"] == 1450.25
        assert result["balances"][0]["balances"]["currency"] == "USD"
    
    @patch('app.services.plaid_service.settings')
    def test_get_balances_with_account_filter(self, mock_settings):
        """Test balance retrieval with account filter."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        mock_account = Mock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_specific",
            "balances": {"current": 1000.0}
        }
        
        service.client.accounts_balance_get.return_value = {
            "accounts": [mock_account]
        }
        
        result = service.get_balances("access-token-123", account_id="acc_specific")
        
        assert result["status"] == "success"
        service.client.accounts_balance_get.assert_called_once()
    
    @patch('app.services.plaid_service.settings')
    def test_get_balances_no_client(self, mock_settings):
        """Test balance retrieval without client."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.get_balances("access-token")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]


class TestPlaidServiceIdentity:
    """Test identity information retrieval methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_get_identity_success(self, mock_settings):
        """Test successful identity retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        mock_account = Mock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_123",
            "name": "Test Account",
            "mask": "0000",
            "owners": [
                {
                    "names": ["John Doe"],
                    "emails": [{"data": "john@example.com", "primary": True}],
                    "phone_numbers": [{"data": "555-0123", "primary": True}],
                    "addresses": [{"city": "San Francisco", "region": "CA", "postal_code": "94105", "country": "US"}]
                }
            ]
        }
        
        service.client.identity_get.return_value = {
            "accounts": [mock_account]
        }
        
        result = service.get_identity("access-token")
        
        assert result["status"] == "success"
        assert len(result["identities"]) == 1
        assert result["identities"][0]["account_id"] == "acc_123"
        assert len(result["identities"][0]["owners"]) == 1
        assert result["identities"][0]["owners"][0]["names"] == ["John Doe"]
    
    @patch('app.services.plaid_service.settings')
    def test_get_identity_no_config(self, mock_settings):
        """Test identity retrieval with missing configuration."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.get_identity("access-token")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]


class TestPlaidServiceLiabilities:
    """Test liability accounts retrieval methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_get_liabilities_success(self, mock_settings):
        """Test successful liability retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "accounts": [
                {
                    "account_id": "acc_123",
                    "name": "Credit Card",
                    "mask": "0000",
                    "type": "credit",
                    "subtype": "credit_card",
                    "balances": {
                        "current": -1500.0,
                        "limit": 5000.0,
                        "available": 3500.0,
                        "iso_currency_code": "USD"
                    }
                }
            ],
            "liabilities": {
                "credit": [
                    {
                        "account_id": "acc_123",
                        "apr_percentage": 18.5,
                        "apr_type": "variable_apr"
                    }
                ],
                "mortgage": [],
                "student": []
            }
        }
        
        service.client.liabilities_get.return_value = mock_response
        
        result = service.get_liabilities("access-token")
        
        assert result["status"] == "success"
        assert len(result["liabilities"]["accounts"]) == 1
        assert len(result["liabilities"]["credit"]) == 1
        assert result["liabilities"]["accounts"][0]["account_id"] == "acc_123"
    
    @patch('app.services.plaid_service.settings')
    def test_get_liabilities_no_config(self, mock_settings):
        """Test liability retrieval with missing configuration."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.get_liabilities("access-token")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]


class TestPlaidServiceInvestments:
    """Test investment accounts and holdings retrieval methods."""
    
    @patch('app.services.plaid_service.settings')
    def test_get_investments_success(self, mock_settings):
        """Test successful investment retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "accounts": [
                {
                    "account_id": "acc_123",
                    "name": "Investment Account",
                    "mask": "0000",
                    "type": "investment",
                    "subtype": "401k",
                    "balances": {
                        "current": 50000.0,
                        "available": 50000.0,
                        "iso_currency_code": "USD"
                    }
                }
            ],
            "holdings": [
                {
                    "account_id": "acc_123",
                    "security_id": "sec_123",
                    "institution_value": 10000.0,
                    "institution_price": 100.0,
                    "quantity": 100.0,
                    "cost_basis": 9000.0,
                    "iso_currency_code": "USD"
                }
            ],
            "securities": [
                {
                    "security_id": "sec_123",
                    "name": "Apple Inc.",
                    "ticker_symbol": "AAPL",
                    "type": "equity",
                    "close_price": 100.0,
                    "iso_currency_code": "USD"
                }
            ]
        }
        
        service.client.investments_holdings_get.return_value = mock_response
        
        result = service.get_investments("access-token")
        
        assert result["status"] == "success"
        assert len(result["investments"]["accounts"]) == 1
        assert len(result["investments"]["holdings"]) == 1
        assert len(result["investments"]["securities"]) == 1
        assert result["investments"]["accounts"][0]["account_id"] == "acc_123"
        assert result["investments"]["holdings"][0]["security_id"] == "sec_123"
        assert result["investments"]["securities"][0]["ticker_symbol"] == "AAPL"
    
    @patch('app.services.plaid_service.settings')
    def test_get_investments_no_config(self, mock_settings):
        """Test investment retrieval with missing configuration."""
        mock_settings.plaid_client_id = None
        mock_settings.plaid_secret = None
        
        service = PlaidService()
        
        result = service.get_investments("access-token")
        
        assert result["status"] == "error"
        assert "Plaid not configured" in result["error"]


class TestPlaidServiceIntegration:
    """Test integration scenarios."""
    
    @patch('app.services.plaid_service.settings')
    def test_full_flow_simulation(self, mock_settings):
        """Test a complete flow from link token to data retrieval."""
        mock_settings.plaid_client_id = "test_client_id"
        mock_settings.plaid_secret = "test_secret"
        
        service = PlaidService()
        service.client = Mock()
        
        # Mock the complete flow
        service.client.link_token_create.return_value = {
            "link_token": "link-token",
            "expiration": "2024-12-31T23:59:59Z"
        }
        
        service.client.item_public_token_exchange.return_value = {
            "access_token": "access-token",
            "item_id": "item_123"
        }
        
        mock_account = Mock()
        mock_account.to_dict.return_value = {
            "account_id": "acc_123",
            "name": "Test Account",
            "balances": {"current": 1000.0}
        }
        
        service.client.accounts_get.return_value = {
            "accounts": [mock_account],
            "item": {"item_id": "item_123"}
        }
        
        # Test the flow
        link_result = service.create_link_token("user_123")
        assert link_result["status"] == "success"
        
        exchange_result = service.exchange_public_token("public-token")
        assert exchange_result["status"] == "success"
        
        accounts_result = service.get_accounts(exchange_result["access_token"])
        assert accounts_result["status"] == "success"
        assert len(accounts_result["accounts"]) == 1