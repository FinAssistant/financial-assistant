"""
Shared MCP client for Graphiti graph database integration.

This module provides a reusable client for connecting to Graphiti's MCP server
and accessing its tools for storing and querying financial context and relationships.
"""

import logging
import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_RETRY_BACKOFF = [0.2, 0.5, 1.0]  # seconds


async def _call_tool_with_retries(
    tool, payload: Dict[str, Any], retry_delays: List[float] = None
):
    """
    Call MCP tool with retry logic and exponential backoff.

    Args:
        tool: MCP tool to call
        payload: Tool payload
        retry_delays: List of retry delays in seconds (default: [0.2, 0.5, 1.0])

    Returns:
        Tool response

    Raises:
        Exception: Last exception if all retries fail
    """
    retry_delays = retry_delays or DEFAULT_RETRY_BACKOFF
    last_exception = None

    for delay in retry_delays:
        try:
            return await tool.ainvoke(payload)
        except Exception as e:
            last_exception = e
            logger.warning(f"MCP tool call failed; retrying in {delay}s: {e}")
            await asyncio.sleep(delay)

    logger.error(
        f"MCP tool call failed after {len(retry_delays)} retries: {last_exception}"
    )
    raise last_exception


def canonical_hash(transaction) -> str:
    """
    Generate canonical hash for transaction deduplication from PlaidTransaction.

    Args:
        transaction: PlaidTransaction object

    Returns:
        SHA256 hash for unique transaction identification
    """
    # Static provider for Plaid transactions
    provider = "plaid"

    # Extract and normalize fields from PlaidTransaction
    provider_tx_id = transaction.transaction_id
    date = transaction.date or "unknown"
    amount = str(transaction.amount) if transaction.amount else "0.00"
    merchant_normalized = transaction.merchant_name or transaction.name or "unknown"

    s = f"{provider}|{provider_tx_id}|{date}|{amount}|{merchant_normalized}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class GraphitiMCPClient:
    """
    Shared MCP client for Graphiti database operations.

    Provides a simple interface for agents to store episodes and search
    for financial context without needing to manage MCP connections directly.
    """

    def __init__(self, graphiti_url: str = "http://localhost:8080/sse"):
        """
        Initialize Graphiti MCP client.

        Args:
            graphiti_url: URL of the Graphiti MCP server (default: docker container)
        """
        self.graphiti_url = graphiti_url
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[Any] = []
        self._connected = False

    async def connect(self) -> bool:
        """
        Connect to Graphiti MCP server and initialize tools.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = MultiServerMCPClient(
                {"graphiti": {"transport": "sse", "url": self.graphiti_url}}
            )

            # Initialize tools from Graphiti server
            self.tools = await self.client.get_tools()
            self._connected = True

            logger.info(f"Connected to Graphiti MCP server at {self.graphiti_url}")
            logger.info(f"Available tools: {[tool.name for tool in self.tools]}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Graphiti MCP server: {e}")
            self._connected = False
            return False

    def _get_tool(self, tool_name: str):
        """Get tool by name from available tools."""
        if not self._connected:
            raise RuntimeError("Client not connected. Call connect() first.")

        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(
                f"Tool '{tool_name}' not found in available tools: {[t.name for t in self.tools]}"
            )
        return tool

    async def add_episode(
        self,
        user_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        name: str = "Financial Conversation",
        source_description: str = "agent_conversation",
    ) -> Dict[str, Any]:
        """
        Store a financial conversation episode in Graphiti.

        CRITICAL: Uses user_id as group_id to ensure user data isolation.

        Args:
            user_id: Authenticated user ID (also used as group_id for isolation)
            content: Conversation content to store
            name: Episode name (default: "Financial Conversation")
            source_description: Source description for tracking (default: "agent_conversation")

        Returns:
            Response from Graphiti add_memory tool
        """
        add_memory_tool = self._get_tool("add_memory")

        # Build enhanced episode content with extraction guidance
        enhanced_content = f"""
            FINANCIAL CONVERSATION CONTEXT:
            User Message: {content}

            EXTRACTION PRIORITIES:
            - Financial goals (saving, investing, debt payoff, retirement)
            - Risk tolerance and concerns
            - Dollar amounts and timeframes
            - Family situation affecting finances
            - Values and priorities expressed
            - Constraints or limitations mentioned
            - Personal info: income range, net worth, major assets/liabilities
            - Geographic context: city/state, cost of living
            - Demographic context: age range, life stage, occupation type
            - Any other details relevant to financial planning
            """

        if context:
            enhanced_content += f"""
            ADDITIONAL CONTEXT:
            {context if context else "None"}
            """

        try:
            response = await _call_tool_with_retries(
                add_memory_tool,
                {
                    "name": name,
                    "episode_body": enhanced_content,
                    "source": "text",  # Let Graphiti handle content type classification
                    "source_description": source_description,
                    "group_id": user_id,  # CRITICAL: user_id = group_id for data isolation
                },
            )

            logger.info(f"Stored episode for user {user_id}: {name}")
            return response

        except Exception as e:
            logger.error(f"Failed to store episode for user {user_id}: {e}")
            raise

    async def search(
        self, user_id: str, query: str, max_nodes: int = 10
    ) -> Dict[str, Any]:
        """
        Search for financial context using Graphiti.

        CRITICAL: Only searches within user's group_id for data isolation.

        Args:
            user_id: Authenticated user ID (used as group_id filter)
            query: Search query for financial context
            max_nodes: Maximum number of nodes to return (default: 10)

        Returns:
            Search results from Graphiti
        """
        search_tool = self._get_tool("search_memory_nodes")

        try:
            response = await _call_tool_with_retries(
                search_tool,
                {
                    "query": query,
                    "group_ids": [user_id],  # CRITICAL: filter by user's group_id
                    "max_nodes": max_nodes,
                    "center_node_uuid": None,
                },
            )

            logger.info(f"Search completed for user {user_id}: {query}")
            return response

        except Exception as e:
            logger.error(f"Search failed for user {user_id}: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if client is connected to Graphiti server."""
        return self._connected

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools] if self.tools else []

    #
    # Transaction-specific methods
    #

    async def _find_transaction_by_hash(
        self, group_id: str, canonical_hash: str, max_nodes: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Find an existing transaction node by canonical hash.
        Specialized for transaction deduplication.
        """
        if not self._connected:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            tool = self._get_tool("search_memory_nodes")

            # Try different query formats for hash-based search
            payloads = [
                {
                    "query": canonical_hash,
                    "group_ids": [group_id],
                    "max_nodes": max_nodes,
                },
                {
                    "query": f"canonical_hash:{canonical_hash}",
                    "group_ids": [group_id],
                    "max_nodes": max_nodes,
                },
                {
                    "query": f"transaction {canonical_hash}",
                    "group_ids": [group_id],
                    "max_nodes": max_nodes,
                },
            ]

            for payload in payloads:
                try:
                    response = await _call_tool_with_retries(tool, payload)
                    # Check different response formats
                    for field in ("nodes", "results", "items"):
                        nodes = (
                            response.get(field) if isinstance(response, dict) else None
                        )
                        if nodes:
                            # Return first node that matches canonical hash
                            for node in nodes:
                                props = (
                                    node.get("properties", {})
                                    if isinstance(node, dict)
                                    else {}
                                )
                                if (
                                    props.get("canonical_hash") == canonical_hash
                                    or props.get("hash") == canonical_hash
                                ):
                                    return node
                            # If no exact match but we have nodes, return first
                            return nodes[0]
                except Exception as e:
                    logger.debug(f"Transaction search payload failed: {payload} -> {e}")
                    continue
        except Exception as e:
            logger.error(f"Failed to find transaction by hash {canonical_hash}: {e}")

        return None

    async def store_transaction_episode(
        self, user_id: str, transaction, check_duplicate: bool = True
    ) -> Dict[str, Any]:
        """
        Store a transaction episode with specialized extraction guidance.

        Args:
            user_id: User ID (used as group_id)
            transaction: PlaidTransaction object with AI categorization populated
            check_duplicate: Whether to check for existing transaction first

        Returns:
            Response from Graphiti or existing node info if duplicate found
        """
        if not self._connected:
            raise RuntimeError("Client not connected. Call connect() first.")

        # Generate canonical hash from transaction
        tx_hash = canonical_hash(transaction)

        # Check for duplicate if requested
        if check_duplicate:
            existing = await self._find_transaction_by_hash(user_id, tx_hash)
            if existing:
                logger.info(f"Found existing transaction for hash {tx_hash}")
                return {"found": True, "node": existing}

        # Build transaction-specific episode content
        episode_content = self._build_transaction_episode_content(
            transaction, user_id, tx_hash
        )

        try:
            add_memory_tool = self._get_tool("add_memory")

            response = await _call_tool_with_retries(
                add_memory_tool,
                {
                    "name": f"Transaction {tx_hash[:8]}",
                    "episode_body": episode_content,
                    "source": "transaction_ingest",
                    "source_description": "automated_transaction_categorization",
                    "group_id": user_id,
                },
            )

            logger.info(f"Stored transaction episode for user {user_id}: {tx_hash[:8]}")
            return {"found": False, "add_memory_response": response}

        except Exception as e:
            logger.error(f"Failed to store transaction episode for user {user_id}: {e}")
            raise

    async def batch_store_transaction_episodes(
        self,
        user_id: str,
        transactions: List,
        concurrency: int = 8,
        check_duplicates: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Store multiple transaction episodes in parallel with concurrency control.

        Args:
            user_id: User ID (used as group_id for all transactions)
            transactions: List of PlaidTransaction objects with AI categorization
            concurrency: Maximum concurrent operations (default: 8)
            check_duplicates: Whether to check for existing transactions first

        Returns:
            List of per-transaction results (success/error/duplicate status)
        """
        if not transactions:
            return []

        sem = asyncio.Semaphore(concurrency)
        results = []

        async def _worker(transaction):
            async with sem:
                try:
                    result = await self.store_transaction_episode(
                        user_id=user_id,
                        transaction=transaction,
                        check_duplicate=check_duplicates,
                    )
                    result["transaction_id"] = transaction.transaction_id
                    return result
                except Exception as e:
                    logger.exception(
                        f"Failed to store transaction {transaction.transaction_id}: {e}"
                    )
                    return {
                        "error": str(e),
                        "transaction_id": transaction.transaction_id,
                        "found": False,
                    }

        # Create tasks for all transactions
        tasks = [asyncio.create_task(_worker(tx)) for tx in transactions]

        # Wait for all tasks to complete
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)

        # Log summary
        success_count = sum(1 for r in results if not r.get("error"))
        duplicate_count = sum(1 for r in results if r.get("found"))
        error_count = len(results) - success_count

        logger.info(
            f"Batch transaction storage for user {user_id}: {success_count} stored, {duplicate_count} duplicates, {error_count} errors"
        )

        return results

    def _build_transaction_episode_content(
        self, transaction, user_id: str, tx_hash: str
    ) -> str:
        """
        Build specialized episode content for transaction storage with extraction guidance.

        Args:
            transaction: PlaidTransaction object with AI categorization fields populated
            user_id: User ID for data isolation
            tx_hash: Canonical hash for deduplication

        Returns:
            Formatted episode content for Graphiti storage
        """
        # Core transaction info for extraction - access PlaidTransaction fields directly
        core_data = {
            "canonical_hash": tx_hash,
            "transaction_id": transaction.transaction_id,
            "user_id": user_id,
            "date": transaction.date,
            "amount": str(transaction.amount),
            "merchant_name": transaction.merchant_name,
            "name": transaction.name,
            "category": transaction.category,
            "account_id": transaction.account_id,
            "pending": transaction.pending,
        }

        # Add AI categorization if available (fields populated by categorization service)
        if hasattr(transaction, "ai_category") and transaction.ai_category:
            core_data.update(
                {
                    "ai_category": transaction.ai_category,
                    "ai_subcategory": transaction.ai_subcategory,
                    "ai_confidence": float(transaction.ai_confidence)
                    if transaction.ai_confidence
                    else None,
                    "ai_tags": transaction.ai_tags or [],
                }
            )

        episode_content = f"""
INGESTED TRANSACTION EPISODE

TRANSACTION_DATA: {json.dumps(core_data, ensure_ascii=False)}

EXTRACTION_GUIDANCE:
- Primary entity: Transaction with canonical_hash property
- Required properties: canonical_hash, date, amount, merchant_name, category
- AI categorization properties: ai_category, ai_subcategory, ai_confidence, ai_tags
- Create Merchant node from merchant_name
- Create Category node from ai_category
- Link Transaction -> User via group_id
- Link Transaction -> Merchant via PURCHASED_FROM
- Link Transaction -> Category via HAS_CATEGORY
- Store ai_confidence and ai_reasoning as transaction properties
- Tag spending patterns if ai_tags contain 'recurring', 'subscription', etc.

SOURCE: transaction_categorization_agent
"""

        return episode_content


# Global instances for reuse across agents
_graphiti_client: Optional[GraphitiMCPClient] = None
_graphiti_tools = None
_graphiti_tool_node = None


async def setup_graphiti_tools():
    """Setup Graphiti MCP tools during FastAPI startup."""
    from langgraph.prebuilt import ToolNode

    global _graphiti_tools, _graphiti_tool_node

    try:
        # Get Graphiti MCP client and tools
        graphiti_client = await get_graphiti_client()

        if not graphiti_client or not graphiti_client.is_connected():
            raise RuntimeError(
                "Graphiti MCP client not connected - Graphiti is required for financial assistant"
            )

        _graphiti_tools = graphiti_client.tools
        if not _graphiti_tools:
            raise RuntimeError(
                "No Graphiti tools available - Graphiti tools are required for financial context storage"
            )

        _graphiti_tool_node = ToolNode(_graphiti_tools)
        logger.info(
            f"Graphiti ToolNode initialized with tools: {[tool.name for tool in _graphiti_tools]}"
        )
        return _graphiti_tool_node

    except Exception as e:
        logger.error(f"Failed to setup Graphiti tools: {e}")
        _graphiti_tools = None
        _graphiti_tool_node = None
        raise RuntimeError(
            f"Graphiti tools setup failed - this is a critical error: {e}"
        ) from e


def get_graphiti_tool_node():
    """Get the initialized Graphiti ToolNode."""
    if _graphiti_tool_node is None:
        raise RuntimeError(
            "Graphiti ToolNode not initialized - setup_graphiti_tools() must be called during startup"
        )
    return _graphiti_tool_node


def get_graphiti_tools() -> list:
    """Get the Graphiti MCP tools list."""
    if _graphiti_tools is None:
        raise RuntimeError(
            "Graphiti tools not initialized - setup_graphiti_tools() must be called during startup"
        )
    return _graphiti_tools


async def get_graphiti_client(graphiti_url: Optional[str] = None) -> GraphitiMCPClient:
    """
    Get or create shared Graphiti MCP client instance.

    Args:
        graphiti_url: URL of Graphiti MCP server (defaults to config value)

    Returns:
        Connected GraphitiMCPClient instance
    """
    global _graphiti_client

    # Use config URL if not provided
    url = graphiti_url or settings.mcp_graphiti_server_url

    if _graphiti_client is None or not _graphiti_client.is_connected():
        _graphiti_client = GraphitiMCPClient(url)
        await _graphiti_client.connect()

    return _graphiti_client
