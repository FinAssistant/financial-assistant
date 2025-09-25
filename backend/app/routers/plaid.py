"""
Plaid API router for token exchange and account management.

This router provides REST endpoints for Plaid Link integration,
including token exchange and account connection management.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.routers.auth import get_current_user
from app.core.database import user_storage
from app.core.sqlmodel_models import ConnectedAccountCreate
from app.services.plaid_service import PlaidService
from app.core.config import settings
from app.ai.conversation_handler import ConversationHandler

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/plaid", tags=["plaid"])

# Initialize PlaidService
plaid_service = PlaidService()


class PlaidTokenExchangeRequest(BaseModel):
    """Request model for exchanging Plaid public token."""
    public_token: str = Field(..., description="Public token from Plaid Link")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation resumption")


class PlaidTokenExchangeResponse(BaseModel):
    """Response model for token exchange endpoint."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")
    accounts_connected: int = Field(..., description="Number of accounts connected")
    account_ids: List[str] = Field(default_factory=list, description="List of connected account IDs")


@router.post("/exchange", response_model=PlaidTokenExchangeResponse)
async def exchange_public_token(
    request: PlaidTokenExchangeRequest,
    user_id: str = Depends(get_current_user)
) -> PlaidTokenExchangeResponse:
    """
    Exchange Plaid public token for access token and store account information.

    This endpoint:
    1. Exchanges the public token for an access token via Plaid API
    2. Retrieves account information from Plaid
    3. Stores encrypted access tokens and account data in the database
    4. Returns success confirmation with connected account details

    The frontend should call this endpoint after successful Plaid Link completion.
    """
    logger.info(f"Starting token exchange for user {user_id}")

    try:
        # Step 1: Exchange public token for access token
        exchange_result = plaid_service.exchange_public_token(request.public_token)

        if exchange_result["status"] != "success":
            logger.error(f"Token exchange failed for user {user_id}: {exchange_result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange token: {exchange_result.get('error', 'Unknown error')}"
            )

        access_token = exchange_result["access_token"]
        item_id = exchange_result["item_id"]

        logger.info(f"Successfully exchanged token for user {user_id}, item_id: {item_id}")

        # Step 2: Get account information from Plaid
        accounts_result = plaid_service.get_accounts(access_token)

        if accounts_result["status"] != "success":
            logger.error(f"Failed to get accounts for user {user_id}: {accounts_result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve account information: {accounts_result.get('error', 'Unknown error')}"
            )

        accounts = accounts_result["accounts"]
        institution = accounts_result.get("item", {})
        institution_name = institution.get("institution_name", "Unknown Institution")
        institution_id = institution.get("institution_id", "unknown")

        logger.info(f"Retrieved {len(accounts)} accounts for user {user_id}")

        # Step 3: Store account information in database
        connected_account_ids = []

        for account in accounts:
            # Create ConnectedAccount data structure
            account_data = ConnectedAccountCreate(
                plaid_account_id=account["account_id"],
                plaid_item_id=item_id,
                encrypted_access_token=access_token,  # Will be encrypted by the database layer
                account_name=account.get("name", "Unknown Account"),
                account_type=account.get("type", "unknown"),
                account_subtype=account.get("subtype"),
                institution_name=institution_name,
                institution_id=institution_id
            )

            # Check if account already exists for this user
            existing_account = user_storage.get_connected_account_by_plaid_id(
                user_id, account["account_id"]
            )

            if existing_account:
                logger.info(f"Account {account['account_id']} already exists for user {user_id}, skipping")
                connected_account_ids.append(existing_account["id"])
                continue

            # Create new connected account
            created_account = user_storage.create_connected_account(user_id, account_data)
            connected_account_ids.append(created_account["id"])

            logger.info(f"Created connected account {created_account['id']} for user {user_id}")

        logger.info(f"Successfully processed {len(connected_account_ids)} accounts for user {user_id}")

        # Inject system message to resume conversation if session_id provided
        if request.session_id:
            try:
                conversation_handler = ConversationHandler()
                system_message = f"User successfully connected {len(connected_account_ids)} bank accounts from {institution_name}. Please congratulate them and check if their profile is now complete."

                # Process system message through conversation handler
                await conversation_handler.process_message(
                    user_message=f"SYSTEM: {system_message}",
                    user_id=user_id,
                    session_id=request.session_id
                )

                logger.info(f"Injected system message for account connection completion - user {user_id}, session {request.session_id}")
            except Exception as e:
                logger.warning(f"Failed to inject system message for user {user_id}: {str(e)}")
                # Don't fail the main operation if system message injection fails

        # Return success response
        return PlaidTokenExchangeResponse(
            status="success",
            message=f"Successfully connected {len(connected_account_ids)} accounts from {institution_name}",
            accounts_connected=len(connected_account_ids),
            account_ids=connected_account_ids
        )

    except HTTPException:
        # Re-raise HTTP exceptions (these are already handled)
        raise

    except Exception as e:
        logger.error(f"Unexpected error during token exchange for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during account connection"
        )


@router.get("/accounts", response_model=List[Dict[str, Any]])
async def get_connected_accounts(
    user_id: str = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all connected accounts for the authenticated user.

    Returns a list of connected account information without sensitive data.
    """
    logger.info(f"Retrieving connected accounts for user {user_id}")

    try:
        accounts = user_storage.get_connected_accounts(user_id)

        # Remove sensitive information before returning
        safe_accounts = []
        for account in accounts:
            safe_account = {
                "id": account["id"],
                "account_name": account["account_name"],
                "account_type": account["account_type"],
                "account_subtype": account.get("account_subtype"),
                "institution_name": account["institution_name"],
                "is_active": account["is_active"],
                "created_at": account["created_at"],
                "last_sync_at": account.get("last_sync_at")
            }
            safe_accounts.append(safe_account)

        logger.info(f"Returning {len(safe_accounts)} connected accounts for user {user_id}")
        return safe_accounts

    except Exception as e:
        logger.error(f"Error retrieving connected accounts for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connected accounts"
        )


@router.delete("/accounts/{account_id}")
async def disconnect_account(
    account_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Disconnect (deactivate) a connected account.

    This soft-deletes the account by setting is_active=False.
    """
    logger.info(f"Disconnecting account {account_id} for user {user_id}")

    try:
        # Verify the account belongs to the user
        account = user_storage.get_connected_account_by_id(account_id)

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        if account["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to disconnect this account"
            )

        # Deactivate the account
        success = user_storage.deactivate_connected_account(account_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to disconnect account"
            )

        logger.info(f"Successfully disconnected account {account_id} for user {user_id}")

        return {
            "status": "success",
            "message": f"Account {account['account_name']} has been disconnected"
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error disconnecting account {account_id} for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while disconnecting the account"
        )