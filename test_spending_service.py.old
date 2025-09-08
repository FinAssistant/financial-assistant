"""
Tests for Spending Service - Core spending analysis and categorization logic.
Story 2.3: Spending Agent - Transaction Analysis and Insights
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from app.services.spending_service import SpendingService, get_spending_service


class TestTransactionCategorization:
    """Test AI-powered transaction categorization with user feedback learning."""
    
    @pytest.fixture
    def spending_service(self):
        return SpendingService()
    
    @pytest.fixture
    def sample_transactions(self):
        return [
            {
                "transaction_id": "tx_1",
                "amount": -23.45,
                "iso_currency_code": "USD",
                "date": "2025-09-01",
                "name": "Starbucks",
                "merchant_name": "Starbucks",
                "category": None,
                "payment_channel": "in store",
                "pending": False,
                "location": {
                    "address": "123 Main St",
                    "city": "San Francisco",
                    "region": "CA",
                    "postal_code": "94105",
                    "country": "US"
                }
            },
            {
                "transaction_id": "tx_2",
                "amount": -1500.00,
                "iso_currency_code": "USD",
                "date": "2025-09-01",
                "name": "Rent Payment",
                "merchant_name": "Main Street Apartments",
                "category": None,
                "payment_channel": "online",
                "pending": False,
                "location": {
                    "address": "456 Main St",
                    "city": "New York",
                    "region": "NY",
                    "postal_code": "10001",
                    "country": "US"
                }
            },
            {
                "transaction_id": "tx_3",
                "amount": -89.99,
                "iso_currency_code": "USD",
                "date": "2025-09-02",
                "name": "Amazon Order",
                "merchant_name": "Amazon",
                "category": ["Shopping", "Online Retail"],
                "payment_channel": "online",
                "pending": False,
                "location": {
                    "address": "789 Oak Ave",
                    "city": "Seattle",
                    "region": "WA",
                    "postal_code": "98101",
                    "country": "US"
                }
            }
        ]
    
    @pytest.fixture
    def user_feedback_history(self):
        return [
            {
                "transaction_id": "tx_old_1",
                "transaction_description": "STARBUCKS COFFEE #123",
                "original_category": "Uncategorized",
                "user_corrected_category": "Coffee & Dining",
                "feedback_timestamp": "2025-08-15T10:00:00Z"
            }
        ]

    @pytest.mark.asyncio
    async def test_categorize_transactions_basic_rules(self, spending_service, sample_transactions):
        """Test rule-based categorization without AI fallback."""
        result = await spending_service.categorize_transactions(
            user_id="user_123",
            transactions=sample_transactions,
            use_ai_fallback=False
        )
        
        assert result["status"] == "success"
        assert len(result["categorized_transactions"]) == 3
        
        # Check rent categorization (should be rule-based)
        rent_tx = next(tx for tx in result["categorized_transactions"] if tx["transaction_id"] == "tx_2")
        assert rent_tx["category"] == "Housing & Rent"
        assert rent_tx["categorization_method"] == "rule_based"
        assert rent_tx["confidence_score"] >= 0.9

    @pytest.mark.asyncio
    async def test_categorize_transactions_with_ai_fallback(self, spending_service, sample_transactions):
        """Test AI-powered categorization for unclear transactions."""
        with patch.object(spending_service, '_categorize_with_llm') as mock_llm:
            mock_llm.return_value = {
                "category": "Shopping & General",
                "confidence": 0.75,
                "reasoning": "Online shopping transaction"
            }
            
            result = await spending_service.categorize_transactions(
                user_id="user_123", 
                transactions=sample_transactions,
                use_ai_fallback=True
            )
            
            # Amazon transaction should use AI categorization
            amazon_tx = next(tx for tx in result["categorized_transactions"] if tx["transaction_id"] == "tx_3")
            assert amazon_tx["category"] == "Shopping & General"
            assert amazon_tx["categorization_method"] == "ai_powered"
            assert amazon_tx["confidence_score"] == 0.75

    @pytest.mark.asyncio 
    async def test_categorize_with_user_feedback_learning(self, spending_service, sample_transactions, user_feedback_history):
        """Test that user feedback influences future categorizations."""
        result = await spending_service.categorize_transactions(
            user_id="user_123",
            transactions=sample_transactions,
            user_feedback_history=user_feedback_history
        )
        
        # Starbucks should use learned category from feedback
        starbucks_tx = next(tx for tx in result["categorized_transactions"] if tx["transaction_id"] == "tx_1")
        assert starbucks_tx["category"] == "Coffee & Dining"
        assert starbucks_tx["categorization_method"] == "user_learned"
        assert starbucks_tx["confidence_score"] >= 0.95


class TestSpendingPatternAnalysis:
    """Test comprehensive spending pattern recognition."""
    
    @pytest.fixture
    def spending_service(self):
        return SpendingService()
    
    @pytest.fixture
    def transaction_history(self):
        # Generate 90 days of transaction data with patterns
        transactions = []
        base_date = datetime(2024, 1, 1)
        
        # Monthly rent
        for month in range(3):
            transactions.append({
                "amount": -1200.00,
                "date": (base_date + timedelta(days=month*30)).isoformat(),
                "category": "Housing & Rent",
                "merchant_name": "RENT PAYMENT - MAIN ST APARTMENTS"
            })
        
        # Weekly groceries with variation
        for week in range(12):
            amount = -85 + (week % 3) * 15  # Seasonal variation
            transactions.append({
                "amount": amount,
                "date": (base_date + timedelta(days=week*7)).isoformat(),
                "category": "Food & Groceries",
                "merchant_name": "Grocery Store"
            })
            
        # Holiday spike in January - add baseline shopping first
        transactions.extend([
            {"amount": -80.00, "date": "2024-01-05", "category": "Shopping & General", "merchant_name": "Target"},
            {"amount": -75.00, "date": "2024-01-10", "category": "Shopping & General", "merchant_name": "Walmart"}, 
            {"amount": -90.00, "date": "2024-01-15", "category": "Shopping & General", "merchant_name": "Target"},
            {"amount": -450.00, "date": "2024-01-20", "category": "Shopping & General", "merchant_name": "Amazon"},
            {"amount": -85.00, "date": "2024-02-05", "category": "Shopping & General", "merchant_name": "Target"},
            {"amount": -70.00, "date": "2024-02-15", "category": "Shopping & General", "merchant_name": "Walmart"}
        ])
        
        return transactions

    def test_analyze_spending_patterns_recurring_expenses(self, spending_service, transaction_history):
        """Test identification of recurring expenses."""
        result = spending_service.analyze_spending_patterns(
            user_id="user_123",
            transaction_history=transaction_history,
            analysis_days=90
        )
        
        assert result["status"] == "success"
        assert "recurring_expenses" in result["spending_patterns"]
        
        recurring = result["spending_patterns"]["recurring_expenses"]
        assert len(recurring) >= 2  # Rent and groceries
        
        # Check rent detection
        rent_recurring = next((r for r in recurring if "RENT PAYMENT" in r["description_pattern"]), None)
        assert rent_recurring is not None
        assert rent_recurring["frequency"] == "monthly"
        assert rent_recurring["average_amount"] == 1200.00
        assert rent_recurring["confidence_score"] >= 0.9

    def test_analyze_spending_patterns_seasonal_trends(self, spending_service, transaction_history):
        """Test seasonal trend detection."""
        result = spending_service.analyze_spending_patterns(
            user_id="user_123",
            transaction_history=transaction_history,
            analysis_days=90
        )
        
        seasonal_trends = result["spending_patterns"]["seasonal_trends"]
        assert len(seasonal_trends) > 0

    def test_analyze_spending_patterns_anomaly_detection(self, spending_service, transaction_history):
        """Test anomaly detection in spending patterns."""
        result = spending_service.analyze_spending_patterns(
            user_id="user_123",
            transaction_history=transaction_history,
            analysis_days=90
        )
        
        anomalies = result["spending_patterns"]["anomalies"]
        assert isinstance(anomalies, list)
        
        # Large holiday purchase should be flagged as anomaly
        holiday_anomaly = next((a for a in anomalies if a["amount"] == -450.00), None)
        assert holiday_anomaly is not None
        assert holiday_anomaly["severity"] in ["medium", "high"]
        assert holiday_anomaly["anomaly_type"] == "amount_spike"


class TestSubscriptionDetection:
    """Test subscription service detection and optimization."""
    
    @pytest.fixture
    def spending_service(self):
        return SpendingService()
    
    @pytest.fixture
    def subscription_transactions(self):
        return [
            # Netflix subscription
            {"amount": -15.99, "date": "2024-01-15", "merchant_name": "Netflix"},
            {"amount": -15.99, "date": "2024-02-15", "merchant_name": "Netflix"},
            {"amount": -15.99, "date": "2024-03-15", "merchant_name": "Netflix"},
            
            # Duplicate music services
            {"amount": -9.99, "date": "2024-01-10", "merchant_name": "Spotify"},
            {"amount": -9.99, "date": "2024-01-12", "merchant_name": "Apple Music"},
            {"amount": -9.99, "date": "2024-02-10", "merchant_name": "Spotify"},
            {"amount": -9.99, "date": "2024-02-12", "merchant_name": "Apple Music"},
            
            # Unused gym membership (no check-ins)
            {"amount": -89.99, "date": "2024-01-01", "merchant_name": "Fitness Club"},
            {"amount": -89.99, "date": "2024-02-01", "merchant_name": "Fitness Club"},
        ]

    @pytest.mark.asyncio
    async def test_detect_subscription_services(self, spending_service, subscription_transactions):
        """Test detection of subscription services."""
        result = await spending_service.detect_subscription_services(
            user_id="user_123",
            transactions=subscription_transactions,
            analysis_months=3
        )
        
        assert result["status"] == "success"
        subscriptions = result["detected_subscriptions"]
        assert len(subscriptions) >= 3  # Netflix, Spotify, Apple Music, Gym
        
        # Check Netflix detection
        netflix = next((s for s in subscriptions if "Netflix" in s["merchant_name"]), None)
        assert netflix is not None
        assert netflix["frequency"] == "monthly"
        assert netflix["average_amount"] == 15.99
        assert netflix["category"] == "Video Streaming"

    @pytest.mark.asyncio
    async def test_detect_duplicate_services(self, spending_service, subscription_transactions):
        """Test detection of duplicate subscription services."""
        result = await spending_service.detect_subscription_services(
            user_id="user_123",
            transactions=subscription_transactions,
            analysis_months=3
        )
        
        duplicates = result["optimization_opportunities"]["duplicate_services"]
        assert len(duplicates) > 0
        
        # Should detect duplicate music streaming services
        music_duplicate = next((d for d in duplicates if "Music Streaming" in d["service_type"]), None)
        assert music_duplicate is not None
        assert music_duplicate["potential_monthly_savings"] > 0

    @pytest.mark.asyncio
    async def test_detect_unused_services(self, spending_service, subscription_transactions):
        """Test detection of potentially unused services."""
        with patch.object(spending_service, '_check_service_usage') as mock_usage:
            mock_usage.return_value = {"usage_score": 0.1, "last_activity": None}
            
            result = await spending_service.detect_subscription_services(
                user_id="user_123",
                transactions=subscription_transactions,
                analysis_months=3,
                include_usage_analysis=True
            )
            
            unused = result["optimization_opportunities"]["unused_services"]
            gym_unused = next((u for u in unused if "Fitness Club" in u["service_name"]), None)
            assert gym_unused is not None
            assert gym_unused["usage_score"] <= 0.2
            assert gym_unused["potential_monthly_savings"] == 89.99


class TestOptimizationEngine:
    """Test intelligent optimization recommendations."""
    
    @pytest.fixture
    def spending_service(self):
        return SpendingService()
    
    @pytest.fixture
    def user_spending_profile(self):
        return {
            "monthly_income": 5000.00,
            "fixed_expenses": 2800.00,
            "personality_type": "planner",
            "risk_tolerance": "medium",
            "spending_triggers": ["convenience", "time_saving"],
            "financial_goals": ["emergency_fund", "vacation_savings"]
        }

    def test_generate_optimization_opportunities(self, spending_service, user_spending_profile):
        """Test generation of personalized optimization opportunities."""
        spending_data = {
            "categories": {
                "Food Delivery": {"amount": 450.00, "transactions": 18},
                "Subscriptions": {"amount": 89.97, "transactions": 6},
                "Shopping & General": {"amount": 320.50, "transactions": 12}
            }
        }
        
        result = spending_service.generate_optimization_opportunities(
            user_id="user_123",
            spending_data=spending_data,
            user_profile=user_spending_profile
        )
        
        assert result["status"] == "success"
        assert result["personality_type"] == "planner"
        
        opportunities = result["optimization_opportunities"]
        assert len(opportunities) > 0
        assert result["total_potential_monthly_savings"] > 0
        
        # Check that opportunities have required fields
        for opp in opportunities:
            assert "opportunity_type" in opp
            assert "description" in opp
            assert "potential_monthly_savings" in opp
            assert "confidence_score" in opp

    def test_optimization_personality_awareness(self, spending_service, user_spending_profile):
        """Test that recommendations are tailored to personality type."""
        spending_data = {"categories": {"Food Delivery": {"amount": 450.00, "transactions": 18}}}
        
        result = spending_service.generate_optimization_opportunities(
            user_id="user_123",
            spending_data=spending_data, 
            user_profile=user_spending_profile
        )
        
        opportunities = result["optimization_opportunities"]
        delivery_opt = next((o for o in opportunities if "meal" in o["description"].lower() or "plans" in o["description"].lower()), None)
        
        # For planner personality, should suggest meal prep over elimination
        assert delivery_opt is not None
        assert ("meal" in delivery_opt["description"].lower() and "prep" in delivery_opt["description"].lower()) or "planning" in delivery_opt["description"].lower()
        assert delivery_opt["personality_fit"] >= 0.7  # High fit for planner


class TestBudgetManagement:
    """Test budget management and tracking functionality."""
    
    @pytest.fixture
    def spending_service(self):
        return SpendingService()
    
    @pytest.fixture
    def budget_categories(self):
        return [
            {
                "category_name": "Food & Groceries",
                "monthly_limit": 400.00,
                "alert_thresholds": [75, 90, 100]
            },
            {
                "category_name": "Transportation", 
                "monthly_limit": 200.00,
                "alert_thresholds": [80, 95, 100]
            },
            {
                "category_name": "Entertainment",
                "monthly_limit": 150.00,
                "alert_thresholds": [75, 90, 100]
            }
        ]
    
    @pytest.fixture
    def current_spending(self):
        return [
            {"amount": 320.50, "category": "Food & Groceries", "date": "2024-01-15"},
            {"amount": 190.00, "category": "Transportation", "date": "2024-01-14"},
            {"amount": 145.99, "category": "Entertainment", "date": "2024-01-13"}
        ]

    def test_manage_budget_categories(self, spending_service, budget_categories):
        """Test budget category creation and management."""
        # Test creating budget categories
        result = spending_service.manage_budget_categories(
            user_id="user_123",
            action="create",
            budget_categories=budget_categories
        )
        
        assert result["status"] == "success"
        assert result["action"] == "create"
        assert len(result["budget_categories"]) == 3
        
        created_category = result["budget_categories"][0]
        assert created_category["category_name"] == "Food & Groceries"
        assert created_category["monthly_limit"] == 400.00
        assert created_category["current_spent"] == 0.00
        assert created_category["percentage_used"] == 0.00

    def test_budget_real_time_tracking(self, spending_service, budget_categories, current_spending):
        """Test real-time budget tracking with spending updates."""
        result = spending_service.manage_budget_categories(
            user_id="user_123",
            action="update_spending",
            budget_categories=budget_categories,
            current_spending=current_spending
        )
        
        assert result["status"] == "success"
        updated_categories = result["budget_categories"]
        
        # Check Food & Groceries category update
        food_category = next(c for c in updated_categories if c["category_name"] == "Food & Groceries")
        assert food_category["current_spent"] == 320.50
        assert abs(food_category["percentage_used"] - 80.125) < 0.01
        assert food_category["remaining_budget"] == 79.50

    def test_generate_budget_alerts(self, spending_service, budget_categories, current_spending):
        """Test budget alert generation based on thresholds."""
        result = spending_service.generate_budget_alerts(
            user_id="user_123",
            budget_categories=budget_categories,
            current_spending=current_spending
        )
        
        assert result["status"] == "success"
        alerts = result["budget_alerts"]
        
        # Should generate alerts for categories near thresholds
        food_alert = next((a for a in alerts if a["category_name"] == "Food & Groceries"), None)
        assert food_alert is not None
        assert food_alert["alert_type"] == "warning_75"
        assert food_alert["severity"] == "medium"
        assert "personality_aware_message" in food_alert

    def test_budget_variance_analysis(self, spending_service, budget_categories, current_spending):
        """Test budget variance analysis and insights."""
        result = spending_service.generate_budget_alerts(
            user_id="user_123",
            budget_categories=budget_categories,
            current_spending=current_spending,
            include_variance_analysis=True
        )
        
        assert result["status"] == "success"
        assert "variance_analysis" in result
        
        variance = result["variance_analysis"]
        assert "overspending_categories" in variance
        assert "underspending_categories" in variance
        assert "adjustment_suggestions" in variance


class TestIntegrationScenarios:
    """Test complete workflow integration scenarios."""
    
    @pytest.fixture
    def spending_service(self):
        return SpendingService()
    
    @pytest.mark.asyncio
    async def test_complete_spending_analysis_workflow(self, spending_service):
        """Test complete workflow from transaction fetch to optimization."""
        user_id = "user_123"
        
        # Mock transaction data
        transactions = [
            {"transaction_id": "tx_1", "amount": -45.67, "date": "2024-01-15", "merchant_name": "Starbucks"},
            {"transaction_id": "tx_2", "amount": -1200.00, "date": "2024-01-01", "merchant_name": "Property Management Co"},
        ]
        
        # Step 1: Categorize transactions
        categorized = await spending_service.categorize_transactions(user_id, transactions)
        assert categorized["status"] == "success"
        
        # Step 2: Analyze spending patterns
        patterns = spending_service.analyze_spending_patterns(user_id, categorized["categorized_transactions"])
        assert patterns["status"] == "success"
        
        # Step 3: Generate optimization opportunities
        spending_data = {"categories": {"Food & Groceries": {"amount": 150.00, "transactions": 5}}}
        user_profile = {"personality_type": "saver"}
        optimizations = spending_service.generate_optimization_opportunities(user_id, spending_data, user_profile)
        assert optimizations["status"] == "success"

    def test_error_handling_and_graceful_degradation(self, spending_service):
        """Test error handling in various failure scenarios."""
        # Test with invalid user_id
        result_sync = spending_service.analyze_spending_patterns("", [])
        assert result_sync["status"] == "success"  # Empty transactions is valid
        
        # Test with invalid transaction data
        invalid_transactions = [{"invalid": "data"}]
        
        async def test_invalid_async():
            result_async = await spending_service.categorize_transactions("user_123", invalid_transactions)
            assert result_async["status"] == "error"
            assert "validation_errors" in result_async
        
        import asyncio
        asyncio.run(test_invalid_async())


def test_singleton_pattern():
    """Test that get_spending_service returns the same instance."""
    service1 = get_spending_service()
    service2 = get_spending_service()
    assert service1 is service2