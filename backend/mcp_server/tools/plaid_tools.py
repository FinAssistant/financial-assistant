"""
Plaid API tools for MCP server.
Provides secure access to Plaid financial data through MCP tools using PlaidService.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token, AccessToken

from app.services.plaid_service import PlaidService

logger = logging.getLogger(__name__)

# In-memory storage for user access tokens (replace with database in production)
_user_access_tokens: Dict[str, List[str]] = {}


def _get_user_access_tokens(user_id: str) -> List[str]:
    """
    Get all access tokens for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of access tokens for the user
    """
    return _user_access_tokens.get(user_id, [])


def _store_user_access_token(user_id: str, access_token: str) -> None:
    """
    Store an access token for a user.
    
    Args:
        user_id: User identifier
        access_token: Plaid access token to store
    """
    if user_id not in _user_access_tokens:
        _user_access_tokens[user_id] = []
    
    if access_token not in _user_access_tokens[user_id]:
        _user_access_tokens[user_id].append(access_token)
        logger.info(f"Stored access token for user {user_id}")


def register_plaid_tools(mcp: FastMCP, plaid_service: PlaidService):
    """
    Register Plaid-related tools with the MCP server using PlaidService.
    
    Args:
        mcp: FastMCP server instance
        plaid_service: PlaidService instance for API operations
    """
    
    @mcp.tool
    def create_link_token(user_id: str, products: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a Plaid Link token for user authentication.
        
        Args:
            user_id: User identifier  
            products: List of Plaid products to enable
            
        Returns:
            Link token and expiration information
        """
        try:
            result = plaid_service.create_link_token(user_id, products)
            logger.info(f"Created link token for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error creating link token: {str(e)}")
            return {"status": "error", "error": "Failed to create link token"}
    
    @mcp.tool
    def exchange_public_token(public_token: str) -> Dict[str, Any]:
        """
        Exchange Plaid public token for access token and store it for the authenticated user.
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            Success status and item information
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Exchange token using PlaidService
            result = plaid_service.exchange_public_token(public_token)
            
            if result["status"] == "success":
                # Store the access token for this user
                access_token = result["access_token"]
                _store_user_access_token(user_id, access_token)
                
                # Remove access token from response for security
                del result["access_token"]
                result["message"] = "Account successfully connected"
                logger.info(f"Exchanged token and stored access token for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error exchanging public token: {str(e)}")
            return {"status": "error", "error": "Failed to exchange token"}
    
    @mcp.tool
    def get_accounts() -> Dict[str, Any]:
        """
        Get authenticated user's connected bank accounts from all institutions.
        
        Returns:
            Aggregated list of connected accounts
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Get user's access tokens
            access_tokens = _get_user_access_tokens(user_id)
            if not access_tokens:
                return {"status": "error", "error": "No connected accounts. Please connect your bank account first."}
            
            # Aggregate accounts from all institutions
            all_accounts = []
            institution_info = []
            
            for access_token in access_tokens:
                result = plaid_service.get_accounts(access_token)
                
                if result["status"] == "success":
                    all_accounts.extend(result["accounts"])
                    institution_info.append(result["item"])
                else:
                    logger.warning(f"Failed to get accounts for one access token: {result.get('error')}")
            
            logger.info(f"Retrieved {len(all_accounts)} accounts for user {user_id}")
            
            return {
                "status": "success",
                "accounts": all_accounts,
                "institutions": institution_info,
                "total_accounts": len(all_accounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve accounts"}
    
    @mcp.tool
    def get_all_transactions(
        cursor: Optional[str] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Get ALL transactions for authenticated user using sync endpoint with pagination.
        This is the recommended approach per Plaid documentation.
        
        Args:
            cursor: Starting cursor for pagination (optional)
            max_iterations: Maximum number of sync calls to prevent infinite loops
            
        Returns:
            All transactions across all connected accounts
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Get user's access tokens
            access_tokens = _get_user_access_tokens(user_id)
            if not access_tokens:
                return {"status": "error", "error": "No connected accounts. Please connect your bank account first."}
            
            # Aggregate all transactions from all institutions
            all_transactions = []
            
            for access_token in access_tokens:
                current_cursor = cursor
                iterations = 0
                
                while iterations < max_iterations:
                    result = plaid_service.sync_transactions(access_token, current_cursor)
                    
                    if result["status"] == "success":
                        # Add all transactions from this sync
                        all_transactions.extend(result.get("added", []))
                        all_transactions.extend(result.get("modified", []))
                        
                        # Check if we need to continue syncing
                        if not result.get("has_more", False):
                            break
                            
                        current_cursor = result.get("next_cursor")
                        if not current_cursor:
                            break
                            
                        iterations += 1
                    else:
                        logger.warning(f"Failed to sync transactions for one access token: {result.get('error')}")
                        break
            
            # Sort transactions by date (newest first)
            all_transactions.sort(key=lambda t: t.get("date", ""), reverse=True)
            
            logger.info(f"Retrieved {len(all_transactions)} total transactions for user {user_id}")
            
            return {
                "status": "success",
                "transactions": all_transactions,
                "total_transactions": len(all_transactions),
                "message": f"Retrieved {len(all_transactions)} transactions using sync endpoint"
            }
            
        except Exception as e:
            logger.error(f"Error getting all transactions: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve transactions"}
    
    @mcp.tool
    def get_balances(account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time account balances for authenticated user.
        
        Args:
            account_id: Optional specific account ID
            
        Returns:
            Aggregated account balances
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Get user's access tokens
            access_tokens = _get_user_access_tokens(user_id)
            if not access_tokens:
                return {"status": "error", "error": "No connected accounts. Please connect your bank account first."}
            
            # Aggregate balances from all institutions
            all_balances = []
            
            for access_token in access_tokens:
                result = plaid_service.get_balances(access_token, account_id)
                
                if result["status"] == "success":
                    all_balances.extend(result["balances"])
                else:
                    logger.warning(f"Failed to get balances for one access token: {result.get('error')}")
            
            logger.info(f"Retrieved balances for {len(all_balances)} accounts for user {user_id}")
            
            return {
                "status": "success",
                "balances": all_balances,
                "timestamp": datetime.now().isoformat(),
                "total_accounts": len(all_balances)
            }
            
        except Exception as e:
            logger.error(f"Error getting balances: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve balances"}
    
    @mcp.tool
    def get_identity(account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get identity information for authenticated user's connected accounts.
        
        Args:
            account_id: Optional specific account ID
            
        Returns:
            Identity information including names, emails, addresses
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Get user's access tokens
            access_tokens = _get_user_access_tokens(user_id)
            if not access_tokens:
                return {"status": "error", "error": "No connected accounts. Please connect your bank account first."}
            
            # Aggregate identity from all institutions
            all_identities = []
            
            for access_token in access_tokens:
                result = plaid_service.get_identity(access_token, account_id)
                
                if result["status"] == "success":
                    all_identities.extend(result["identities"])
                else:
                    logger.warning(f"Failed to get identity for one access token: {result.get('error')}")
            
            logger.info(f"Retrieved identity information for {len(all_identities)} accounts for user {user_id}")
            
            return {
                "status": "success",
                "identities": all_identities,
                "timestamp": datetime.now().isoformat(),
                "total_accounts": len(all_identities)
            }
            
        except Exception as e:
            logger.error(f"Error getting identity: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve identity information"}
    
    @mcp.tool
    def get_liabilities(account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get liability accounts for authenticated user's connected institutions.
        
        Args:
            account_id: Optional specific account ID
            
        Returns:
            Liability information including credit cards, mortgages, student loans
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Get user's access tokens
            access_tokens = _get_user_access_tokens(user_id)
            if not access_tokens:
                return {"status": "error", "error": "No connected accounts. Please connect your bank account first."}
            
            # Aggregate liabilities from all institutions
            all_accounts = []
            all_credit = []
            all_mortgage = []
            all_student = []
            
            for access_token in access_tokens:
                result = plaid_service.get_liabilities(access_token, account_id)
                
                if result["status"] == "success":
                    liabilities = result["liabilities"]
                    all_accounts.extend(liabilities["accounts"])
                    all_credit.extend(liabilities["credit"])
                    all_mortgage.extend(liabilities["mortgage"])
                    all_student.extend(liabilities["student"])
                else:
                    logger.warning(f"Failed to get liabilities for one access token: {result.get('error')}")
            
            logger.info(f"Retrieved liability information for {len(all_accounts)} accounts for user {user_id}")
            
            return {
                "status": "success",
                "liabilities": {
                    "accounts": all_accounts,
                    "credit": all_credit,
                    "mortgage": all_mortgage,
                    "student": all_student
                },
                "timestamp": datetime.now().isoformat(),
                "total_accounts": len(all_accounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting liabilities: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve liability information"}
    
    @mcp.tool
    def get_investments(account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get investment accounts and holdings for authenticated user.
        
        Args:
            account_id: Optional specific account ID
            
        Returns:
            Investment information including accounts, holdings, securities
        """
        try:
            # Get authenticated user from JWT context
            token: AccessToken = get_access_token()
            if not token:
                return {"status": "error", "error": "Authentication required"}
            
            user_id = token.claims.get("sub", {}).get("user_id")
            if not user_id:
                return {"status": "error", "error": "User ID not found in token"}
            
            # Get user's access tokens
            access_tokens = _get_user_access_tokens(user_id)
            if not access_tokens:
                return {"status": "error", "error": "No connected accounts. Please connect your bank account first."}
            
            # Aggregate investments from all institutions
            all_accounts = []
            all_holdings = []
            all_securities = []
            
            for access_token in access_tokens:
                result = plaid_service.get_investments(access_token, account_id)
                
                if result["status"] == "success":
                    investments = result["investments"]
                    all_accounts.extend(investments["accounts"])
                    all_holdings.extend(investments["holdings"])
                    all_securities.extend(investments["securities"])
                else:
                    logger.warning(f"Failed to get investments for one access token: {result.get('error')}")
            
            logger.info(f"Retrieved investment information for {len(all_accounts)} accounts with {len(all_holdings)} holdings for user {user_id}")
            
            return {
                "status": "success",
                "investments": {
                    "accounts": all_accounts,
                    "holdings": all_holdings,
                    "securities": all_securities
                },
                "timestamp": datetime.now().isoformat(),
                "total_accounts": len(all_accounts),
                "total_holdings": len(all_holdings)
            }
            
        except Exception as e:
            logger.error(f"Error getting investments: {str(e)}")
            return {"status": "error", "error": "Failed to retrieve investment information"}
    
    logger.info("Plaid MCP tools registered successfully")