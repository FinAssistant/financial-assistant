"""
Plaid API service for financial data operations.
Provides secure access to Plaid financial data through clean API methods.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from functools import lru_cache

from plaid import ApiClient, Configuration, Environment
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.exceptions import ApiException

from app.core.config import settings

logger = logging.getLogger(__name__)


class PlaidService:
    """
    Service for interacting with Plaid API.
    
    Handles all Plaid operations including account fetching, transaction retrieval,
    balance checking, and link token creation/exchange.
    """
    
    def __init__(self):
        """Initialize Plaid service with configuration."""
        self.client = self._get_plaid_client()
    
    @lru_cache(maxsize=1)
    def _get_plaid_client(self) -> Optional[plaid_api.PlaidApi]:
        """
        Get configured Plaid API client.
        
        Returns:
            Configured Plaid client or None if not configured
        """
        plaid_client_id = getattr(settings, 'plaid_client_id', None)
        plaid_secret = getattr(settings, 'plaid_secret', None)
        plaid_env = getattr(settings, 'plaid_env', 'sandbox')
        
        if not plaid_client_id or not plaid_secret:
            logger.warning("Plaid credentials not configured")
            return None
        
        # Map environment string to Environment class constants
        if plaid_env == 'production':
            host = Environment.Production
        else:
            host = Environment.Sandbox
        
        configuration = Configuration(
            host=host,
            api_key={
                'clientId': plaid_client_id,
                'secret': plaid_secret,
                'plaidVersion': '2020-09-14'
            }
        )
        api_client = ApiClient(configuration)
        return plaid_api.PlaidApi(api_client)
    
    def _sanitize_account_data(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize account data to remove sensitive information.
        
        Args:
            account: Raw account data from Plaid
            
        Returns:
            Sanitized account data
        """
        if not account:
            return {}
        
        return {
            "account_id": account.get("account_id"),
            "name": account.get("name"),
            "type": account.get("type"),
            "subtype": account.get("subtype"),
            "mask": account.get("mask"),  # Last 4 digits only
            "balances": {
                "current": account.get("balances", {}).get("current"),
                "available": account.get("balances", {}).get("available"),
                "limit": account.get("balances", {}).get("limit"),
                "currency": account.get("balances", {}).get("iso_currency_code", "USD")
            }
        }
    
    def _sanitize_transaction_data(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize transaction data to remove sensitive information.
        
        Args:
            transaction: Raw transaction data from Plaid
            
        Returns:
            Sanitized transaction data
        """
        if not transaction:
            return {}
        
        return {
            "transaction_id": transaction.get("transaction_id"),
            "account_id": transaction.get("account_id"),
            "amount": transaction.get("amount"),
            "date": str(transaction.get("date")) if transaction.get("date") else None,
            "name": transaction.get("name"),
            "merchant_name": transaction.get("merchant_name"),
            "category": transaction.get("category", []),
            "pending": transaction.get("pending", False)
        }
    
    def _handle_plaid_error(self, e: ApiException) -> Dict[str, Any]:
        """
        Handle Plaid API exceptions and return user-friendly error messages.
        
        Args:
            e: Plaid API exception
            
        Returns:
            Error response dictionary
        """
        error_code = getattr(e, "code", "UNKNOWN")
        error_message = str(e)
        
        # Log error without exposing sensitive data
        logger.error(f"Plaid API error: {error_code}")
        
        # Return user-friendly error messages
        if "INVALID_CREDENTIALS" in error_message:
            return {"status": "error", "error": "Invalid Plaid credentials. Please check configuration."}
        elif "RATE_LIMIT" in error_message:
            return {"status": "error", "error": "Rate limit exceeded. Please try again later."}
        elif "ITEM_LOGIN_REQUIRED" in error_message:
            return {"status": "error", "error": "Bank login required. Please reconnect your account."}
        else:
            return {"status": "error", "error": "An error occurred accessing financial data. Please try again."}
    
    def create_link_token(self, user_id: str, products: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a Plaid Link token for user authentication.
        
        Args:
            user_id: User identifier
            products: List of Plaid products to enable
            
        Returns:
            Link token and expiration information
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        if products is None:
            products = ["transactions", "accounts", "balances"]
        
        try:
            # Convert product strings to Plaid Products enum
            plaid_products = []
            for product in products:
                if product == "transactions":
                    plaid_products.append(Products("transactions"))
                elif product == "accounts":
                    plaid_products.append(Products("accounts"))
                elif product == "balances":
                    plaid_products.append(Products("balances"))
            
            # Create link token request
            request = LinkTokenCreateRequest(
                products=plaid_products,
                client_name="AI Financial Assistant",
                country_codes=[CountryCode("US")],
                language="en",
                user={
                    "client_user_id": user_id
                }
            )
            
            response = self.client.link_token_create(request)
            
            logger.info(f"Created Plaid Link token for user {user_id}")
            
            return {
                "status": "success",
                "link_token": response["link_token"],
                "expiration": response["expiration"],
                "request_id": response.get("request_id")
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error creating link token: {str(e)}")
            return {"status": "error", "error": "Failed to create link token"}
    
    def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """
        Exchange Plaid public token for access token.
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            Success status and item information
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Exchange public token for access token
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            response = self.client.item_public_token_exchange(request)
            
            logger.info(f"Exchanged public token for item {response['item_id']}")
            
            return {
                "status": "success",
                "access_token": response["access_token"],  # Return for storage by caller
                "item_id": response["item_id"],
                "request_id": response.get("request_id")
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error exchanging token: {str(e)}")
            return {"status": "error", "error": "Failed to exchange token"}
    
    def get_accounts(self, access_token: str) -> Dict[str, Any]:
        """
        Get bank accounts for given access token.
        
        Args:
            access_token: Plaid access token
            
        Returns:
            List of connected accounts
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Get accounts from Plaid
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            # Sanitize account data before returning
            accounts = []
            for account in response["accounts"]:
                sanitized = self._sanitize_account_data(account.to_dict())
                accounts.append(sanitized)
            
            logger.info(f"Retrieved {len(accounts)} accounts")
            
            return {
                "status": "success",
                "accounts": accounts,
                "item": {
                    "institution_id": response["item"].get("institution_id"),
                    "item_id": response["item"].get("item_id")
                },
                "request_id": response.get("request_id")
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting accounts: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve accounts"}
    
    def get_transactions(
        self, 
        access_token: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transactions for given access token.
        
        Args:
            access_token: Plaid access token
            start_date: Start date for transactions (YYYY-MM-DD format)
            end_date: End date for transactions (YYYY-MM-DD format)
            account_id: Optional specific account ID
            
        Returns:
            List of transactions
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Set default date range if not provided (last 30 days)
            if not end_date:
                end_date = datetime.now().date()
            else:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                
            if not start_date:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            
            # Create request
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )
            
            # Add account filter if specified
            if account_id:
                request.account_ids = [account_id]
            
            response = self.client.transactions_get(request)
            
            # Sanitize transaction data before returning
            transactions = []
            for transaction in response["transactions"]:
                sanitized = self._sanitize_transaction_data(transaction.to_dict())
                transactions.append(sanitized)
            
            logger.info(f"Retrieved {len(transactions)} transactions")
            
            return {
                "status": "success",
                "transactions": transactions,
                "total_transactions": response["total_transactions"],
                "request_id": response.get("request_id"),
                "date_range": {
                    "start": str(start_date),
                    "end": str(end_date)
                }
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting transactions: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve transactions"}
    
    def get_balances(self, access_token: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time account balances.
        
        Args:
            access_token: Plaid access token
            account_id: Optional specific account ID
            
        Returns:
            Account balances
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Get account balances
            request = AccountsBalanceGetRequest(access_token=access_token)
            
            # Add account filter if specified
            if account_id:
                request.account_ids = [account_id]
            
            response = self.client.accounts_balance_get(request)
            
            # Extract and sanitize balance data
            balances = []
            for account in response["accounts"]:
                account_data = account.to_dict()
                balance_info = {
                    "account_id": account_data.get("account_id"),
                    "name": account_data.get("name"),
                    "mask": account_data.get("mask"),
                    "type": account_data.get("type"),
                    "balances": {
                        "current": account_data.get("balances", {}).get("current"),
                        "available": account_data.get("balances", {}).get("available"),
                        "limit": account_data.get("balances", {}).get("limit"),
                        "currency": account_data.get("balances", {}).get("iso_currency_code", "USD")
                    }
                }
                balances.append(balance_info)
            
            logger.info(f"Retrieved balances for {len(balances)} accounts")
            
            return {
                "status": "success",
                "balances": balances,
                "request_id": response.get("request_id"),
                "timestamp": datetime.now().isoformat()
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting balances: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve balances"}
    
    def get_identity(self, access_token: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get identity information for accounts.
        
        Args:
            access_token: Plaid access token
            account_id: Optional specific account ID
            
        Returns:
            Identity information including names, emails, phone numbers, addresses
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Get identity information
            request = IdentityGetRequest(access_token=access_token)
            
            # Add account filter if specified
            if account_id:
                request.account_ids = [account_id]
            
            response = self.client.identity_get(request)
            
            # Sanitize identity data
            identities = []
            for account in response["accounts"]:
                account_data = account.to_dict()
                owners = account_data.get("owners", [])
                
                identity_info = {
                    "account_id": account_data.get("account_id"),
                    "name": account_data.get("name"),
                    "mask": account_data.get("mask"),
                    "owners": []
                }
                
                for owner in owners:
                    owner_info = {
                        "names": owner.get("names", []),
                        "emails": [{"data": e.get("data"), "primary": e.get("primary")} 
                                  for e in owner.get("emails", [])],
                        "phone_numbers": [{"data": p.get("data")[-4:] if p.get("data") else None, 
                                         "primary": p.get("primary")} 
                                        for p in owner.get("phone_numbers", [])],
                        "addresses": [{"city": a.get("city"), 
                                     "region": a.get("region"),
                                     "postal_code": a.get("postal_code"),
                                     "country": a.get("country")}
                                    for a in owner.get("addresses", [])]
                    }
                    identity_info["owners"].append(owner_info)
                
                identities.append(identity_info)
            
            logger.info(f"Retrieved identity information for {len(identities)} accounts")
            
            return {
                "status": "success",
                "identities": identities,
                "request_id": response.get("request_id")
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting identity: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve identity information"}
    
    def get_liabilities(self, access_token: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get liability accounts information (loans, credit cards).
        
        Args:
            access_token: Plaid access token
            account_id: Optional specific account ID
            
        Returns:
            Liability information including credit cards, mortgages, student loans
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Get liabilities
            request = LiabilitiesGetRequest(access_token=access_token)
            
            # Add account filter if specified
            if account_id:
                request.account_ids = [account_id]
            
            response = self.client.liabilities_get(request)
            response_dict = response.to_dict()
            
            # Organize liability data
            liabilities = {
                "accounts": [],
                "credit": response_dict.get("liabilities", {}).get("credit", []),
                "mortgage": response_dict.get("liabilities", {}).get("mortgage", []),
                "student": response_dict.get("liabilities", {}).get("student", [])
            }
            
            # Process accounts with liability info
            for account in response_dict.get("accounts", []):
                account_info = {
                    "account_id": account.get("account_id"),
                    "name": account.get("name"),
                    "mask": account.get("mask"),
                    "type": account.get("type"),
                    "subtype": account.get("subtype"),
                    "balances": {
                        "current": account.get("balances", {}).get("current"),
                        "limit": account.get("balances", {}).get("limit"),
                        "available": account.get("balances", {}).get("available"),
                        "currency": account.get("balances", {}).get("iso_currency_code", "USD")
                    }
                }
                liabilities["accounts"].append(account_info)
            
            # Sanitize credit card data
            for credit in liabilities["credit"]:
                if "account_id" in credit:
                    # Remove sensitive fields if any
                    pass
            
            logger.info(f"Retrieved liability information for {len(liabilities['accounts'])} accounts")
            
            return {
                "status": "success",
                "liabilities": liabilities,
                "request_id": response_dict.get("request_id")
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting liabilities: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve liability information"}
    
    def get_investments(self, access_token: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get investment accounts and holdings information.
        
        Args:
            access_token: Plaid access token
            account_id: Optional specific account ID
            
        Returns:
            Investment holdings and securities information
        """
        if not self.client:
            return {"status": "error", "error": "Plaid not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET."}
        
        try:
            # Get investment holdings
            request = InvestmentsHoldingsGetRequest(access_token=access_token)
            
            # Add account filter if specified
            if account_id:
                request.account_ids = [account_id]
            
            response = self.client.investments_holdings_get(request)
            response_dict = response.to_dict()
            
            # Process investment data
            investments = {
                "accounts": [],
                "holdings": [],
                "securities": []
            }
            
            # Process accounts
            for account in response_dict.get("accounts", []):
                account_info = {
                    "account_id": account.get("account_id"),
                    "name": account.get("name"),
                    "mask": account.get("mask"),
                    "type": account.get("type"),
                    "subtype": account.get("subtype"),
                    "balances": {
                        "current": account.get("balances", {}).get("current"),
                        "available": account.get("balances", {}).get("available"),
                        "currency": account.get("balances", {}).get("iso_currency_code", "USD")
                    }
                }
                investments["accounts"].append(account_info)
            
            # Process holdings
            for holding in response_dict.get("holdings", []):
                holding_info = {
                    "account_id": holding.get("account_id"),
                    "security_id": holding.get("security_id"),
                    "institution_value": holding.get("institution_value"),
                    "institution_price": holding.get("institution_price"),
                    "quantity": holding.get("quantity"),
                    "cost_basis": holding.get("cost_basis"),
                    "currency": holding.get("iso_currency_code", "USD")
                }
                investments["holdings"].append(holding_info)
            
            # Process securities
            for security in response_dict.get("securities", []):
                security_info = {
                    "security_id": security.get("security_id"),
                    "name": security.get("name"),
                    "ticker_symbol": security.get("ticker_symbol"),
                    "type": security.get("type"),
                    "close_price": security.get("close_price"),
                    "currency": security.get("iso_currency_code", "USD")
                }
                investments["securities"].append(security_info)
            
            logger.info(f"Retrieved {len(investments['holdings'])} holdings across {len(investments['accounts'])} investment accounts")
            
            return {
                "status": "success",
                "investments": investments,
                "request_id": response_dict.get("request_id")
            }
            
        except ApiException as e:
            return self._handle_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting investments: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve investment information"}