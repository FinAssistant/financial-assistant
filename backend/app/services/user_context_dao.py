"""
User Context Data Access Object (DAO).
Provides clean interface for accessing user demographic and context data from SQLite.
"""

import asyncio
import concurrent.futures
from typing import Dict, Any, Optional
from sqlalchemy.future import select

from ..core.database import SQLiteUserStorage
from ..core.sqlmodel_models import UserModel, PersonalContextModel

class UserContextDAO:
    """
    Data Access Object for user context information.
    Handles both basic user info and personal demographic context.
    """
    
    def __init__(self):
        self._storage = SQLiteUserStorage()
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context including basic info and personal demographics.
        Uses a single JOIN query for efficiency.
        Returns agent-ready context dict.
        """
        await self._storage._ensure_initialized()
        
        async with self._storage.session_factory() as session:
            # Single query with LEFT JOIN to get user + personal context
            stmt = (
                select(UserModel, PersonalContextModel)
                .outerjoin(PersonalContextModel, UserModel.id == PersonalContextModel.user_id)
                .where(UserModel.id == user_id)
            )
            
            result = await session.execute(stmt)
            row = result.first()
            
            if not row:
                return {}  # User not found
            
            user_model, personal_context_model = row
            
            # Build agent-ready context structure
            context = {
                "user_id": user_id,
                "name": user_model.name or "User",
                "email": user_model.email,
                "profile_complete": user_model.profile_complete,
                "demographics": {},
                "financial_context": {}
            }
            
            # Add personal context demographics if available
            if personal_context_model:
                pc_dict = personal_context_model.to_dict()
                
                # Map demographics
                demographics = {}
                if pc_dict.get("age_range"):
                    demographics["age_range"] = pc_dict["age_range"]
                if pc_dict.get("life_stage"):
                    demographics["life_stage"] = pc_dict["life_stage"]
                if pc_dict.get("marital_status"):
                    demographics["marital_status"] = pc_dict["marital_status"]
                if pc_dict.get("state"):
                    demographics["location"] = pc_dict["state"]
                if pc_dict.get("cost_of_living_index"):
                    demographics["cost_of_living_index"] = pc_dict["cost_of_living_index"]
                
                context["demographics"] = demographics
                
                # Map financial context
                financial_context = {}
                if pc_dict.get("has_emergency_fund") is not None:
                    financial_context["has_emergency_fund"] = pc_dict["has_emergency_fund"]
                if pc_dict.get("has_retirement_savings") is not None:
                    financial_context["has_retirement_savings"] = pc_dict["has_retirement_savings"]
                if pc_dict.get("has_investment_experience") is not None:
                    financial_context["has_investment_experience"] = pc_dict["has_investment_experience"]
                if pc_dict.get("has_dependents") is not None:
                    financial_context["has_dependents"] = pc_dict["has_dependents"]
                    financial_context["dependent_count"] = pc_dict.get("dependent_count", 0)
                if pc_dict.get("spouse_income") is not None:
                    financial_context["spouse_income"] = pc_dict["spouse_income"]
                
                context["financial_context"] = financial_context
            
            return context
    
    async def get_basic_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get basic user information only."""
        return await self._storage.get_user_by_id(user_id)
    
    async def get_personal_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get personal context (demographics) only."""
        await self._storage._ensure_initialized()
        
        async with self._storage.session_factory() as session:
            stmt = select(PersonalContextModel).where(PersonalContextModel.user_id == user_id)
            result = await session.execute(stmt)
            context = result.first()
            return context[0].to_dict() if context else None

class UserContextDAOSync:
    """
    Synchronous wrapper for UserContextDAO to work with LangGraph agents.
    Handles async-to-sync conversion properly.
    """
    
    def __init__(self):
        self._async_dao = UserContextDAO()
    
    def _run_async(self, coro):
        """Run async function in sync context with proper thread handling."""
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context - use thread pool
                def run_in_new_loop():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                        asyncio.set_event_loop(None)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    return future.result()
            else:
                # We're not in an async context - use current loop
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop - create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get complete user context including basic info and demographics."""
        return self._run_async(self._async_dao.get_user_context(user_id))
    
    def get_basic_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get basic user information only."""
        return self._run_async(self._async_dao.get_basic_user_info(user_id))
    
    def get_personal_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get personal context (demographics) only."""
        return self._run_async(self._async_dao.get_personal_context(user_id))
