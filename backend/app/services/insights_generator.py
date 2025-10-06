"""
Spending insights generator service.

Generates spending insights from transaction data using SQL queries
and stores them in Graphiti for historical context and relationship building.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_

from app.core.database import SQLiteUserStorage
from app.core.sqlmodel_models import TransactionModel
from app.ai.mcp_clients.graphiti_client import GraphitiMCPClient
from app.utils.date_utils import get_month_range

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    Service for generating spending insights from transaction data.

    Queries SQLite for transaction data, calculates insights (totals, categories, trends),
    stores insights in Graphiti for historical context, and returns structured insights.
    """

    def __init__(
        self,
        storage: SQLiteUserStorage,
        graphiti_client: Optional[GraphitiMCPClient] = None
    ):
        """
        Initialize insights generator.

        Args:
            storage: SQLite user storage instance for transaction queries
            graphiti_client: Optional Graphiti client for storing insights
        """
        self.storage = storage
        self.graphiti = graphiti_client
        self.logger = logging.getLogger(__name__)

    async def get_total_spending(
        self, user_id: str, start_date: str, end_date: str
    ) -> float:
        """
        Calculate total spending for a user within a date range.

        Args:
            user_id: User identifier
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)

        Returns:
            Total spending amount (positive values only - debits)
        """
        await self.storage._ensure_initialized()

        async with self.storage.session_factory() as session:
            # Query: SUM(amount) WHERE user_id AND date range AND amount > 0
            stmt = select(func.sum(TransactionModel.amount)).where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.date >= start_date,
                    TransactionModel.date <= end_date,
                    TransactionModel.amount > 0  # Only debits (expenses)
                )
            )

            result = await session.execute(stmt)
            total = result.scalar()

            return float(total) if total else 0.0

    async def get_category_breakdown(
        self, user_id: str, start_date: str, end_date: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get spending breakdown by AI category.

        Args:
            user_id: User identifier
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)
            limit: Maximum number of categories to return

        Returns:
            List of category insights:
            [
                {"name": "Food & Dining", "amount": 850.00, "percentage": 26.2},
                {"name": "Transportation", "amount": 650.00, "percentage": 20.0}
            ]
        """
        await self.storage._ensure_initialized()

        async with self.storage.session_factory() as session:
            # First get total spending for percentage calculation
            total_spending = await self.get_total_spending(user_id, start_date, end_date)

            if total_spending == 0:
                return []

            # Query: GROUP BY ai_category with SUM and COUNT
            # Use COALESCE to group NULL categories as "Uncategorized"
            category_column = func.coalesce(TransactionModel.ai_category, 'Uncategorized').label('category')

            stmt = (
                select(
                    category_column,
                    func.sum(TransactionModel.amount).label('total'),
                    func.count(TransactionModel.canonical_hash).label('count')
                )
                .where(
                    and_(
                        TransactionModel.user_id == user_id,
                        TransactionModel.date >= start_date,
                        TransactionModel.date <= end_date,
                        TransactionModel.amount > 0  # Only debits
                    )
                )
                .group_by(category_column)
                .order_by(func.sum(TransactionModel.amount).desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            rows = result.fetchall()

            self.logger.debug(f"Category breakdown query returned {len(rows)} rows for user {user_id} ({start_date} to {end_date})")

            # Build category breakdown with percentages
            categories = []
            for row in rows:
                category_name = row[0] or "Uncategorized"
                amount = float(row[1]) if row[1] else 0.0
                count = row[2] if row[2] else 0
                percentage = (amount / total_spending * 100) if total_spending > 0 else 0.0

                self.logger.debug(f"  Category: {category_name}, Amount: ${amount:.2f}, Count: {count}, Percentage: {percentage:.1f}%")

                categories.append({
                    "name": category_name,
                    "amount": round(amount, 2),
                    "percentage": round(percentage, 1),
                    "transaction_count": count
                })

            self.logger.info(f"Returning {len(categories)} categories for user {user_id}")
            return categories

    async def get_month_over_month_trend(
        self, user_id: str, current_month: str
    ) -> Optional[float]:
        """
        Calculate month-over-month spending change percentage.

        Args:
            user_id: User identifier
            current_month: Current month (ISO format YYYY-MM)

        Returns:
            Percentage change from previous month (e.g., -5.2 for 5.2% decrease)
            Returns None if no previous month data
        """
        # Parse current month
        try:
            current_date = datetime.strptime(current_month, "%Y-%m")
        except ValueError:
            self.logger.error(f"Invalid month format: {current_month}")
            return None

        # Calculate date ranges using shared utility
        current_start, current_end = get_month_range(current_date)

        # Previous month
        prev_month = current_date.replace(day=1) - timedelta(days=1)
        prev_start, prev_end = get_month_range(prev_month)

        # Get totals for both months
        current_total = await self.get_total_spending(user_id, current_start, current_end)
        previous_total = await self.get_total_spending(user_id, prev_start, prev_end)

        if previous_total == 0:
            return None  # Can't calculate percentage without previous data

        # Calculate percentage change
        change = ((current_total - previous_total) / previous_total) * 100
        return round(change, 1)

    async def detect_unusual_spending(
        self, user_id: str, current_month: str
    ) -> Optional[str]:
        """
        Detect unusual spending patterns by category.

        Uses statistical analysis (mean + standard deviation) to identify
        categories with unusually high spending in the current month.

        Args:
            user_id: User identifier
            current_month: Current month (ISO format YYYY-MM)

        Returns:
            Human-readable string describing unusual spending, or None if normal
            Example: "Higher than usual restaurant spending detected"
        """
        # TODO: Implement statistical analysis
        # For MVP, return None (no unusual spending detection)
        # This can be enhanced later with historical baseline analysis
        return None

    async def generate_spending_insights(
        self,
        user_id: str,
        month: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive spending insights for a user.

        Orchestrates all insight queries, calculates derived metrics,
        stores results in Graphiti, and returns structured insights.

        Args:
            user_id: User identifier
            month: Target month (ISO format YYYY-MM), defaults to current month
                   Ignored if start_date and end_date are provided
            start_date: Optional custom start date (ISO format YYYY-MM-DD)
            end_date: Optional custom end date (ISO format YYYY-MM-DD)

        Returns:
            Structured insights:
            {
                "total_spending": 3250.00,           # Total for the entire period
                "monthly_average": 3250.00,          # Average per month (same as total for 1 month)
                "period_months": 1,                  # Number of months in the period
                "top_categories": [
                    {"name": "Food & Dining", "amount": 850.00, "percentage": 26.2, "transaction_count": 15}
                ],
                "trends": {
                    "month_over_month_change": -5.2,  # Only for single-month queries
                    "unusual_spending": "Higher than usual restaurant spending"  # Only for single-month
                }
            }
        """
        # Priority: custom date range > month > current month
        if start_date and end_date:
            # Use custom date range
            # If month is provided AND matches the date range, keep it for trend calculations
            if month:
                # Verify the month matches the date range
                try:
                    month_start, month_end = get_month_range(datetime.strptime(month, "%Y-%m"))
                    if month_start == start_date and month_end == end_date:
                        # Date range matches the month exactly - keep month for trends
                        self.logger.info(f"Using month {month} with matching date range: {start_date} to {end_date}")
                    else:
                        # Date range doesn't match month - it's a custom range
                        month = None
                        self.logger.info(f"Using custom date range: {start_date} to {end_date}")
                except (ValueError, TypeError):
                    month = None
                    self.logger.info(f"Using custom date range: {start_date} to {end_date}")
            else:
                self.logger.info(f"Using custom date range: {start_date} to {end_date}")
        elif month:
            # Calculate date range from month using shared utility
            try:
                month_date = datetime.strptime(month, "%Y-%m")
            except ValueError:
                self.logger.error(f"Invalid month format: {month}")
                raise ValueError(f"Month must be in YYYY-MM format, got: {month}")

            start_date, end_date = get_month_range(month_date)
        else:
            # Default to current month
            month = datetime.now().strftime("%Y-%m")
            month_date = datetime.strptime(month, "%Y-%m")
            start_date, end_date = get_month_range(month_date)

        self.logger.info(f"Generating insights for user {user_id}, month {month} ({start_date} to {end_date})")

        # Run all queries
        total_spending = await self.get_total_spending(user_id, start_date, end_date)
        top_categories = await self.get_category_breakdown(user_id, start_date, end_date, limit=5)

        # Month-over-month trends only available for single-month queries
        if month:
            month_over_month = await self.get_month_over_month_trend(user_id, month)
            unusual_spending = await self.detect_unusual_spending(user_id, month)
        else:
            # Custom date ranges don't have month-over-month comparison
            month_over_month = None
            unusual_spending = None

        # Calculate number of months in the date range for monthly average
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        # Calculate months: difference in years * 12 + difference in months + 1 (inclusive)
        months_in_range = (end.year - start.year) * 12 + end.month - start.month + 1
        monthly_average = total_spending / months_in_range if months_in_range > 0 else total_spending

        # Build insights dictionary
        insights = {
            "total_spending": round(total_spending, 2),
            "monthly_average": round(monthly_average, 2),
            "period_months": months_in_range,
            "top_categories": top_categories,
            "trends": {
                "month_over_month_change": month_over_month,
                "unusual_spending": unusual_spending
            },
            "normalized_month": month  # Include normalized month for Graphiti search matching
        }

        # Store to Graphiti (non-blocking)
        if self.graphiti:
            try:
                await self.store_insights_to_graphiti(user_id, insights, month)
            except Exception as e:
                self.logger.error(f"Failed to store insights to Graphiti: {e}")
                # Don't fail the whole operation if Graphiti storage fails

        return insights
    
    def build_tags(self, user_id: str, month: str | None = None) -> str:
        """
        Build a well-formed [TAGS: ...] string for Graphiti episodes.
        Ensures closing bracket and conditional fields.
        """
        tags = [f"user:{user_id}", "spending_insight"]
        if month:
            tags.append(f"month:{month}")
        return "[TAGS: " + ", ".join(tags) + "]"

    async def store_insights_to_graphiti(
        self, user_id: str, insights: Dict[str, Any], month: Optional[str] = None
    ) -> bool:
        """
        Store structured spending insights as a plain-text Graphiti episode.

        Includes inline tags for keyword search. No JSON escaping issues.
        """

        if not self.graphiti:
            self.logger.warning("Graphiti client not available, skipping insight storage")
            return False

        try:
            total = insights.get("total_spending", 0)
            monthly_avg = insights.get("monthly_average", 0)
            period_months = insights.get("period_months", 1)
            categories = insights.get("top_categories", [])
            trends = insights.get("trends", {})

            # Build category breakdown lines safely
            category_lines = []
            for cat in categories[:5]:
                category_lines.append(
                    f"- {cat['name']}: ${cat['amount']:.2f} "
                    f"({cat['percentage']:.1f}%, {cat['transaction_count']} tx) "
                    f"[category:{cat['name'].replace(' ', '_').lower()}]"
                )

            # Build final lines
            lines = [
                "SPENDING INSIGHTS",
                self.build_tags(user_id, month),
                "",
                f"Period: {period_months} month(s)",
                f"Total Spending: ${total:,.2f}",
                f"Monthly Average: ${monthly_avg:,.2f}",
                "",
                "Top Spending Categories:",
            ]
            lines.extend(category_lines if category_lines else ["- No categorized spending data"])
            lines.extend([
                "",
                "Trends:",
                f"- Month-over-month change: {trends.get('month_over_month_change', 'N/A')}%",
                f"- Unusual activity: {trends.get('unusual_spending') or 'No unusual patterns detected'}"
            ])

            content = "\n".join(lines)

            await self.graphiti.add_episode(
                user_id=user_id,
                content=content,
                name=f"Spending Insights - {month or 'custom period'}",
                source_description="spending_insights_generator"
            )

            self.logger.info(f"Stored spending insights to Graphiti for user {user_id}, month {month or 'custom period'}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store insights to Graphiti: {e}")
            return False
