"""
AI-powered transaction categorization service.

This service uses LLM structured output to categorize financial transactions
with dynamic batch sizing based on context window limits.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.models.plaid_models import (
    PlaidTransaction,
    TransactionBatch,
    TransactionCategorization,
    TransactionCategorizationBatch,
)
from app.utils.context_formatting import (
    LLM_CONTEXT_LIMITS,
    build_user_context_string,
    get_llm_context_limit,
)

logger = logging.getLogger(__name__)


class TransactionCategorizationService:
    """Service for AI-powered transaction categorization."""

    def __init__(self, llm, settings: Settings):
        self.llm = llm
        self.settings = settings

        # Use shared context limits from context_formatting.py
        self.context_limits = LLM_CONTEXT_LIMITS

        # Estimate tokens per transaction (conservative estimate)
        self.tokens_per_transaction = 150

        # Reserve tokens for system prompt and response
        self.reserved_tokens = 2000

        # Max completion tokens for structured output (conservative limit)
        self.max_completion_tokens = 3500  # Leave buffer below 4096 limit

    def _get_max_batch_size(self) -> int:
        """Calculate maximum batch size based on context window and completion limits."""
        llm_context = get_llm_context_limit(self.llm)

        # Calculate based on input context limit
        available_input_tokens = llm_context - self.reserved_tokens
        max_by_input = available_input_tokens // self.tokens_per_transaction

        # Calculate based on completion token limit (more restrictive)
        # Assume ~80 tokens per transaction in structured output
        tokens_per_response = 80
        max_by_completion = self.max_completion_tokens // tokens_per_response

        # Use the more restrictive limit
        max_batch_size = min(max_by_input, max_by_completion)

        # Cap at reasonable maximum based on model
        # Gemini has issues with large structured outputs despite huge context window
        model = getattr(self.llm, 'model', '').lower() if self.llm else ''
        if 'gemini' in model or 'google' in model:
            # Gemini structured output is slower and times out with large batches
            logger.info(f"Using Gemini-optimized batch size (10) for model: {model}")
            return min(max_batch_size, 10)  # Very conservative for Gemini
        else:
            # OpenAI and Anthropic handle larger batches better
            return min(max_batch_size, 25)

    def _create_categorization_prompt(self, transactions: List[PlaidTransaction]) -> str:
        """Create the system prompt for transaction categorization."""
        return f"""You are a financial transaction categorization expert. Analyze the provided transactions and categorize each one with:

1. **ai_category**: Primary spending category (e.g., "Food & Dining", "Transportation", "Shopping", "Bills & Utilities", "Entertainment", "Healthcare", "Travel", "Income", "Transfers")

2. **ai_subcategory**: More specific subcategory (e.g., "Coffee Shops", "Gas Stations", "Groceries", "Restaurants")

3. **ai_confidence**: Confidence score from 0.0 to 1.0 based on how certain you are about the categorization

4. **ai_tags**: Relevant tags that help describe the transaction (e.g., ["recurring", "subscription", "cash-withdrawal", "business-expense"])

5. **reasoning**: Brief explanation of why you categorized it this way

**Guidelines:**
- Use the transaction name, merchant name, amount, and date to make informed decisions
- For unclear transactions, provide lower confidence scores
- Be consistent with category naming
- Consider spending patterns and amounts for context
- Tag recurring transactions, subscriptions, and unusual patterns

You will receive {len(transactions)} transactions to categorize. Provide structured output for each transaction."""

    async def categorize_transactions(
        self,
        transactions: List[PlaidTransaction],
        user_context: Optional[Dict[str, Any]] = None
    ) -> TransactionCategorizationBatch:
        """
        Categorize a list of transactions using AI.
        
        Args:
            transactions: List of transactions to categorize
            user_context: Optional user context for personalized categorization
            
        Returns:
            TransactionCategorizationBatch with categorization results
        """
        if not transactions:
            return TransactionCategorizationBatch(
                categorizations=[],
                processing_summary="No transactions to categorize"
            )

        try:
            # Dynamic batch sizing
            max_batch_size = self._get_max_batch_size()
            all_categorizations = []

            # Process transactions in batches
            for i in range(0, len(transactions), max_batch_size):
                batch = transactions[i:i + max_batch_size]
                batch_categorizations = await self._categorize_batch(batch, user_context)
                all_categorizations.extend(batch_categorizations)

            summary = f"Successfully categorized {len(all_categorizations)} of {len(transactions)} transactions"
            if len(all_categorizations) < len(transactions):
                failed_count = len(transactions) - len(all_categorizations)
                summary += f" ({failed_count} failed)"

            return TransactionCategorizationBatch(
                categorizations=all_categorizations,
                processing_summary=summary
            )

        except Exception as e:
            logger.error(f"Error categorizing transactions: {e}")
            return TransactionCategorizationBatch(
                categorizations=[],
                processing_summary=f"Categorization failed: {str(e)}"
            )

    async def _categorize_batch(
        self,
        transactions: List[PlaidTransaction],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[TransactionCategorization]:
        """Categorize a single batch of transactions."""
        logger.info(f"Starting categorization of {len(transactions)} transactions")
        try:
            # Create transaction batch for structured input
            transaction_batch = TransactionBatch(transactions=transactions)

            # Create system prompt
            system_prompt = self._create_categorization_prompt(transactions)

            # Add user context if available
            if user_context:
                context_str = build_user_context_string(user_context)
                system_prompt += f"\n\n**User Context:**\n{context_str}"

            # Use structured output to get categorizations
            structured_llm = self.llm.with_structured_output(
                TransactionCategorizationBatch
            )

            # Create input message using the structured transaction batch
            batch_dict = transaction_batch.model_dump()
            input_content = f"""Categorize these transactions:

{self._format_transaction_batch_for_llm(batch_dict)}

Provide categorization results in the required structured format."""

            # Get LLM response
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=input_content)
            ]

            logger.debug(f"Calling structured LLM for {len(transactions)} transactions")
            result = await structured_llm.ainvoke(messages)
            logger.debug(f"LLM returned type: {type(result)}")

            # Validate and return categorizations
            if isinstance(result, TransactionCategorizationBatch):
                logger.info(f"Successfully categorized {len(result.categorizations)} out of {len(transactions)} transactions")
                return result.categorizations
            elif result is None:
                logger.error(f"LLM returned None for {len(transactions)} transactions. Possible causes: structured output not supported, API failure, or context limit exceeded")
                logger.error(f"Model: {getattr(self.llm, 'model_name', 'unknown')}, Batch size: {len(transactions)}")
                return []
            else:
                logger.error(f"Unexpected LLM response type: {type(result)}, value: {result}")
                return []

        except Exception as e:
            logger.error(f"Error in batch categorization: {e}", exc_info=True)
            return []

    def _format_transaction_batch_for_llm(self, batch_dict: Dict[str, Any]) -> str:
        """Format transaction batch data for LLM input."""
        transactions = batch_dict.get('transactions', [])

        # Add batch metadata
        metadata = f"""Batch Metadata:
- Total Transactions: {batch_dict.get('total_count', 0)}
- Date Range: {batch_dict.get('date_range_start', 'N/A')} to {batch_dict.get('date_range_end', 'N/A')}
- Accounts: {', '.join(batch_dict.get('accounts_included', []))}

Transactions:"""

        formatted_txns = [metadata]

        for i, txn in enumerate(transactions, 1):
            formatted = f"""
Transaction {i}:
- ID: {txn['transaction_id']}
- Name: {txn['name']}
- Merchant: {txn.get('merchant_name', 'N/A')}
- Amount: ${txn['amount']}
- Date: {txn.get('date', 'N/A')}
- Plaid Category: {txn.get('category', [])}
- Pending: {txn.get('pending', False)}"""
            formatted_txns.append(formatted)

        return "\n".join(formatted_txns)

