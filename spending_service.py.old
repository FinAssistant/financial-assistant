"""
Spending Service - Core spending analysis and categorization logic.
Story 2.3: Spending Agent - Transaction Analysis and Insights
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import re
import statistics

logger = logging.getLogger(__name__)

# Category mapping rules for basic categorization
CATEGORY_RULES = {
    # Housing & Utilities
    r'(?i)(rent|mortgage|property|landlord|utilities|electric|gas|water|sewer|internet|cable)': 'Housing & Rent',
    
    # Food & Dining
    r'(?i)(grocery|supermarket|food|restaurant|cafe|starbucks|mcdonald|subway|pizza)': 'Food & Groceries',
    r'(?i)(doordash|ubereats|grubhub|delivery|takeout)': 'Food Delivery',
    
    # Transportation
    r'(?i)(gas|fuel|uber|lyft|taxi|parking|metro|bus|train|car\s*payment|insurance.*auto)': 'Transportation',
    
    # Shopping
    r'(?i)(walmart|target|shopping|retail|clothing|electronics)': 'Shopping & General',
    
    # Entertainment & Streaming
    r'(?i)(netflix|spotify|apple\s*music|disney|hulu|movie|theater|concert|entertainment)': 'Entertainment & Streaming',
    
    # Health & Fitness
    r'(?i)(pharmacy|medical|doctor|dental|gym|fitness|yoga|health)': 'Health & Fitness',
    
    # Financial Services
    r'(?i)(bank|fee|interest|credit\s*card|loan|insurance)': 'Financial Services',
}

# Subscription service patterns
SUBSCRIPTION_PATTERNS = {
    r'(?i)(netflix|hulu|disney|prime\s*video|apple\s*tv)': 'Video Streaming',
    r'(?i)(spotify|apple\s*music|youtube\s*music|tidal)': 'Music Streaming', 
    r'(?i)(gym|fitness|yoga|peloton)': 'Fitness & Health',
    r'(?i)(office\s*365|adobe|dropbox|google\s*drive)': 'Productivity Software',
    r'(?i)(news|magazine|newspaper|subscription)': 'News & Media',
}

# Personality-based optimization strategies
OPTIMIZATION_STRATEGIES = {
    'saver': {
        'food_delivery': 'Consider meal prep and batch cooking to reduce delivery costs',
        'subscriptions': 'Review and cancel unused subscriptions monthly',
        'shopping': 'Use price comparison tools and wait 24h before non-essential purchases'
    },
    'planner': {
        'food_delivery': 'Create weekly meal plans and prep schedules to avoid last-minute orders',
        'subscriptions': 'Set calendar reminders to review subscription usage quarterly',
        'shopping': 'Make detailed shopping lists and stick to planned purchases'
    },
    'convenience': {
        'food_delivery': 'Try grocery pickup services or healthy meal delivery subscriptions',
        'subscriptions': 'Bundle services where possible for easier management',
        'shopping': 'Use auto-subscription for regular items to avoid emergency purchases'
    },
    'impulse': {
        'food_delivery': 'Set daily/weekly delivery budgets with automatic cutoffs',
        'subscriptions': 'Use annual plans to reduce monthly decision fatigue',
        'shopping': 'Implement waiting periods and budget alerts for discretionary spending'
    },
    'spender': {
        'food_delivery': 'Find premium meal delivery options that provide better value',
        'subscriptions': 'Upgrade to family plans or premium tiers for better cost-per-use',
        'shopping': 'Focus on quality purchases that last longer'
    }
}


class SpendingService:
    """Core spending analysis service."""
    
    def __init__(self):
        pass
    
    async def categorize_transactions(
        self,
        user_id: str,
        transactions: List[Dict[str, Any]],
        use_ai_fallback: bool = True,
        user_feedback_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Categorize transactions using rules, user feedback learning, and AI fallback.
        ASYNC: Will call LLM API in the future (currently mocked).
        """
        try:
            if not user_id:
                return {"status": "error", "error_message": "user_id is required"}
            
            # Validate transaction data
            validation_errors = []
            for i, tx in enumerate(transactions):
                if not isinstance(tx, dict):
                    validation_errors.append(f"Transaction {i} must be a dictionary")
                elif 'merchant_name' not in tx or 'amount' not in tx:
                    validation_errors.append(f"Transaction {i} missing required fields")
            
            if validation_errors:
                return {"status": "error", "validation_errors": validation_errors}
            
            # Build user feedback lookup
            feedback_lookup = {}
            if user_feedback_history:
                for feedback in user_feedback_history:
                    key = self._extract_merchant_key(feedback.get('transaction_description', ''))
                    feedback_lookup[key] = feedback.get('user_corrected_category')
            
            categorized_transactions = []
            
            for tx in transactions:
                # Get description from multiple possible fields
                description = tx.get('original_description') or tx.get('name') or tx.get('merchant_name', '')
                merchant_name = tx.get('merchant_name', '')
                merchant_key = self._extract_merchant_key(merchant_name)

                # Method 1: Check user feedback learning first
                if merchant_key in feedback_lookup:
                    category = feedback_lookup[merchant_key]
                    method = "user_learned"
                    confidence = 0.95
                
                # Method 2: Rule-based categorization
                else:
                    category = self._categorize_with_rules(description)
                    if category:
                        method = "rule_based"
                        confidence = 0.9
                    else:
                        # Method 3: AI fallback for unclear transactions
                        if use_ai_fallback:
                            ai_result = await self._categorize_with_llm(description, merchant_name, tx.get('amount', 0))
                            category = ai_result.get('category', 'Uncategorized')
                            method = "ai_powered"
                            confidence = ai_result.get('confidence', 0.5)
                        else:
                            category = 'Uncategorized'
                            method = "unclassified"
                            confidence = 0.0
                
                categorized_tx = {
                    **tx,
                    'category': category,
                    'categorization_method': method,
                    'confidence_score': confidence,
                    'auto_categorized': True
                }
                categorized_transactions.append(categorized_tx)
            
            return {
                "status": "success",
                "categorized_transactions": categorized_transactions,
                "categorization_summary": {
                    "total_transactions": len(transactions),
                    "rule_based": len([tx for tx in categorized_transactions if tx['categorization_method'] == 'rule_based']),
                    "ai_powered": len([tx for tx in categorized_transactions if tx['categorization_method'] == 'ai_powered']),
                    "user_learned": len([tx for tx in categorized_transactions if tx['categorization_method'] == 'user_learned'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error categorizing transactions for user {user_id}: {e}")
            return {"status": "error", "error_message": str(e)}

    def analyze_spending_patterns(
        self,
        user_id: str,
        transaction_history: List[Dict[str, Any]],
        analysis_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze spending patterns to identify recurring expenses, trends, and anomalies.
        SYNC: Pure data processing, no I/O operations.
        """
        try:
            if not transaction_history:
                return {"status": "success", "spending_patterns": {"recurring_expenses": [], "seasonal_trends": [], "anomalies": []}}
            
            # Detect recurring expenses
            recurring_expenses = self._detect_recurring_expenses(transaction_history)
            
            # Detect seasonal trends
            seasonal_trends = self._detect_seasonal_trends(transaction_history)
            
            # Detect anomalies
            anomalies = self._detect_spending_anomalies(transaction_history)
            
            return {
                "status": "success",
                "user_id": user_id,
                "analysis_period_days": analysis_days,
                "spending_patterns": {
                    "recurring_expenses": recurring_expenses,
                    "seasonal_trends": seasonal_trends,
                    "anomalies": anomalies
                },
                "behavioral_insights": self._generate_behavioral_insights(transaction_history)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending patterns for user {user_id}: {e}")
            return {"status": "error", "error_message": str(e)}

    async def detect_subscription_services(
        self,
        user_id: str,
        transactions: List[Dict[str, Any]],
        analysis_months: int = 3,
        include_usage_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Detect subscription services and recurring payments with optimization opportunities.
        ASYNC: May call external APIs for usage analysis in the future.
        """
        try:
            subscriptions = self._detect_subscriptions(transactions)
            duplicate_services = self._detect_duplicate_services(subscriptions)
            unused_services = []
            
            if include_usage_analysis:
                for subscription in subscriptions:
                    # This will be async API call in the future (Netflix API, Spotify API, etc.)
                    usage_data = await self._check_service_usage(user_id, subscription['merchant_name'])
                    if usage_data['usage_score'] <= 0.2:
                        unused_services.append({
                            "service_name": subscription['merchant_name'],
                            "monthly_cost": subscription['average_amount'],
                            "usage_score": usage_data['usage_score'],
                            "last_activity": usage_data['last_activity'],
                            "potential_monthly_savings": subscription['average_amount']
                        })
            
            return {
                "status": "success",
                "user_id": user_id,
                "analysis_months": analysis_months,
                "detected_subscriptions": subscriptions,
                "optimization_opportunities": {
                    "duplicate_services": duplicate_services,
                    "unused_services": unused_services,
                    "total_potential_monthly_savings": sum(d['potential_monthly_savings'] for d in duplicate_services) + 
                                                      sum(u['potential_monthly_savings'] for u in unused_services)
                }
            }
            
        except Exception as e:
            logger.error(f"Error detecting subscriptions for user {user_id}: {e}")
            return {"status": "error", "error_message": str(e)}

    def generate_optimization_opportunities(
        self,
        user_id: str,
        spending_data: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personality-tailored expense reduction strategies.
        SYNC: Pure data processing and rule-based recommendations.
        """
        try:
            personality_type = user_profile.get('personality_type', 'planner').lower()
            opportunities = []
            
            categories = spending_data.get('categories', {})
            
            for category, data in categories.items():
                amount = data.get('amount', 0)
                transaction_count = data.get('transactions', 0)
                
                # Generate category-specific opportunities
                if 'delivery' in category.lower() or 'takeout' in category.lower():
                    opportunity = self._generate_delivery_optimization(amount, transaction_count, personality_type)
                    if opportunity:
                        opportunities.append(opportunity)
                
                elif 'subscription' in category.lower() or 'streaming' in category.lower():
                    opportunity = self._generate_subscription_optimization(amount, personality_type)
                    if opportunity:
                        opportunities.append(opportunity)
                
                elif 'shopping' in category.lower():
                    opportunity = self._generate_shopping_optimization(amount, transaction_count, personality_type)
                    if opportunity:
                        opportunities.append(opportunity)
            
            return {
                "status": "success",
                "user_id": user_id,
                "personality_type": personality_type,
                "optimization_opportunities": opportunities,
                "total_potential_monthly_savings": sum(op['potential_monthly_savings'] for op in opportunities)
            }
            
        except Exception as e:
            logger.error(f"Error generating optimizations for user {user_id}: {e}")
            return {"status": "error", "error_message": str(e)}

    def manage_budget_categories(
        self,
        user_id: str,
        action: str,
        budget_categories: Optional[List[Dict[str, Any]]] = None,
        current_spending: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create, update, and track category-wise budget limits.
        SYNC: Pure data processing and calculations.
        """
        try:
            if action == "create":
                created_categories = []
                for category in budget_categories or []:
                    category_id = f"{user_id}_{category['category_name'].replace(' ', '_').lower()}"
                    created_category = {
                        "category_id": category_id,
                        "category_name": category['category_name'],
                        "monthly_limit": category['monthly_limit'],
                        "current_spent": 0.00,
                        "percentage_used": 0.00,
                        "remaining_budget": category['monthly_limit'],
                        "alert_thresholds": category.get('alert_thresholds', [75, 90, 100]),
                        "personality_adjusted": category.get('personality_adjustment', True)
                    }
                    created_categories.append(created_category)
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "action": action,
                    "budget_categories": created_categories
                }
            
            elif action == "update_spending":
                # Update spending amounts in real-time
                spending_by_category = {}
                for spending in current_spending or []:
                    category = spending['category']
                    amount = abs(spending['amount'])  # Make positive
                    spending_by_category[category] = spending_by_category.get(category, 0) + amount
                
                updated_categories = []
                for category in budget_categories or []:
                    spent = spending_by_category.get(category['category_name'], 0)
                    limit = category['monthly_limit']
                    percentage = (spent / limit * 100) if limit > 0 else 0
                    
                    updated_category = {
                        **category,
                        "current_spent": spent,
                        "percentage_used": round(percentage, 3),
                        "remaining_budget": max(0, limit - spent)
                    }
                    updated_categories.append(updated_category)
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "action": action,
                    "budget_categories": updated_categories
                }
            
            else:
                return {"status": "error", "error_message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error managing budget categories for user {user_id}: {e}")
            return {"status": "error", "error_message": str(e)}

    def generate_budget_alerts(
        self,
        user_id: str,
        budget_categories: List[Dict[str, Any]],
        current_spending: List[Dict[str, Any]],
        include_variance_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Generate budget variance alerts and notifications.
        SYNC: Pure data processing and alert generation.
        """
        try:
            # Update budget with current spending first
            budget_result = self.manage_budget_categories(
                user_id, "update_spending", budget_categories, current_spending
            )
            updated_categories = budget_result['budget_categories']
            
            alerts = []
            for category in updated_categories:
                percentage = category['percentage_used']
                thresholds = category.get('alert_thresholds', [75, 90, 100])
                
                alert_type = None
                severity = "low"
                
                if percentage >= 100:
                    alert_type = "exceeded_100"
                    severity = "high"
                elif percentage >= thresholds[1] if len(thresholds) > 1 else 90:
                    alert_type = "alert_90"
                    severity = "high"
                elif percentage >= thresholds[0] if len(thresholds) > 0 else 75:
                    alert_type = "warning_75"
                    severity = "medium"
                
                if alert_type:
                    alert = {
                        "id": f"{user_id}_{category['category_name']}_{alert_type}",
                        "category_name": category['category_name'],
                        "alert_type": alert_type,
                        "severity": severity,
                        "current_spent": category['current_spent'],
                        "monthly_limit": category['monthly_limit'],
                        "percentage_used": percentage,
                        "message": f"You've used {percentage:.1f}% of your {category['category_name']} budget",
                        "personality_aware_message": self._generate_personality_aware_alert(category, alert_type),
                        "created_at": datetime.now().isoformat()
                    }
                    alerts.append(alert)
            
            result = {
                "status": "success",
                "user_id": user_id,
                "budget_alerts": alerts
            }
            
            if include_variance_analysis:
                variance_analysis = self._generate_variance_analysis(updated_categories)
                result["variance_analysis"] = variance_analysis
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating budget alerts for user {user_id}: {e}")
            return {"status": "error", "error_message": str(e)}

    # Helper methods (all sync - pure data processing)
    
    def _extract_merchant_key(self, description: str) -> str:
        """Extract a key for merchant matching from transaction description."""
        cleaned = re.sub(r'[#*]\w+', '', description)
        cleaned = re.sub(r'\d+', '', cleaned)
        cleaned = re.sub(r'(COFFEE|ORDER|INC|LLC|CO\.)', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()[:20].upper()

    def _categorize_with_rules(self, description: str) -> Optional[str]:
        """Apply rule-based categorization to transaction description."""
        for pattern, category in CATEGORY_RULES.items():
            if re.search(pattern, description):
                return category
        return None

    async def _categorize_with_llm(self, description: str, merchant_name: str, amount: float) -> Dict[str, Any]:
        """
        Use LLM to categorize unclear transactions.
        ASYNC: Will call OpenAI/Anthropic API in the future (currently mocked).
        """
        # Mock AI categorization - in real implementation, this would call an LLM
        # await openai.chat.completions.create(...)
        desc_lower = description.lower()
        
        if 'amazon' in desc_lower or 'shop' in desc_lower:
            return {"category": "Shopping & General", "confidence": 0.75, "reasoning": "Online shopping transaction"}
        elif 'food' in desc_lower or 'eat' in desc_lower:
            return {"category": "Food & Dining", "confidence": 0.8, "reasoning": "Food-related transaction"}
        else:
            return {"category": "Other", "confidence": 0.5, "reasoning": "Unclear transaction type"}

    async def _check_service_usage(self, user_id: str, service_name: str) -> Dict[str, Any]:
        """
        Check service usage patterns.
        ASYNC: Will call external service APIs in the future (Netflix API, Spotify API, etc.).
        """
        # Mock usage analysis - in real implementation:
        # - Netflix API to check viewing history
        # - Spotify API to check listening patterns
        # - Gym app APIs to check check-ins
        return {
            "usage_score": 0.1,  # Low usage score for testing
            "last_activity": None
        }

    def _detect_recurring_expenses(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect recurring expenses in transaction history."""
        merchant_groups = defaultdict(list)
        
        for tx in transactions:
            merchant_key = self._extract_merchant_key(tx.get('merchant_name', ''))
            if merchant_key:
                merchant_groups[merchant_key].append(tx)
        
        recurring_expenses = []
        for merchant_key, txs in merchant_groups.items():
            if len(txs) >= 2:  # At least 2 transactions to be considered recurring
                amounts = [abs(tx.get('amount', 0)) for tx in txs]
                if amounts and max(amounts) - min(amounts) < max(amounts) * 0.4:
                    avg_amount = statistics.mean(amounts)
                    
                    # Estimate frequency
                    if len(txs) >= 3:
                        dates = [datetime.fromisoformat(tx.get('date', '2024-01-01')) for tx in txs if tx.get('date')]
                        if dates:
                            dates.sort()
                            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                            avg_interval = statistics.mean(intervals) if intervals else 30
                            
                            if avg_interval <= 7:
                                frequency = "weekly"
                            elif avg_interval <= 35:
                                frequency = "monthly"
                            else:
                                frequency = "occasional"
                        else:
                            frequency = "monthly"
                    else:
                        frequency = "monthly"
                    
                    recurring_expenses.append({
                        "description_pattern": merchant_key,
                        "frequency": frequency,
                        "average_amount": round(avg_amount, 2),
                        "transaction_count": len(txs),
                        "confidence_score": min(0.9, len(txs) * 0.2 + 0.5),
                        "category": txs[0].get('category', 'Uncategorized')
                    })
        
        return recurring_expenses

    def _detect_seasonal_trends(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect seasonal spending trends."""
        trends = []
        
        # Group by category and month
        monthly_spending = defaultdict(lambda: defaultdict(float))
        
        for tx in transactions:
            try:
                date = datetime.fromisoformat(tx.get('date', '2024-01-01'))
                month_key = f"{date.year}-{date.month:02d}"
                category = tx.get('category', 'Other')
                amount = abs(tx.get('amount', 0))
                monthly_spending[category][month_key] += amount
            except:
                continue
        
        # Analyze trends
        for category, months in monthly_spending.items():
            if len(months) >= 2:
                amounts = list(months.values())
                avg_amount = statistics.mean(amounts)
                max_amount = max(amounts)
                
                # Detect spikes
                if max_amount > avg_amount * 1.5:
                    trends.append({
                        "category": category,
                        "trend_type": "spike",
                        "peak_month": max(months.keys(), key=lambda k: months[k]),
                        "peak_amount": max_amount,
                        "average_amount": round(avg_amount, 2)
                    })
        
        return trends

    def _detect_spending_anomalies(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in spending patterns."""
        anomalies = []
        
        # Group by category for context
        category_amounts = defaultdict(list)
        for tx in transactions:
            category = tx.get('category', 'Other')
            amount = abs(tx.get('amount', 0))
            category_amounts[category].append((amount, tx))
        
        # Find anomalies per category
        for category, amounts_and_txs in category_amounts.items():
            amounts = [amt for amt, _ in amounts_and_txs]
            if len(amounts) >= 3:
                avg_amount = statistics.mean(amounts)
                std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
                
                for amount, tx in amounts_and_txs:
                    # Flag as anomaly if more than 2 standard deviations from mean
                    if std_amount > 0 and abs(amount - avg_amount) > 2 * std_amount:
                        severity = "high" if amount > avg_amount + 3 * std_amount else "medium"
                        
                        anomalies.append({
                            "transaction_id": tx.get('transaction_id', ''),
                            "amount": -amount,  # Negative for expenses
                            "description": tx.get('original_description') or tx.get('name') or tx.get('merchant_name', ''),
                            "date": tx.get('date', ''),
                            "category": category,
                            "anomaly_type": "amount_spike",
                            "severity": severity,
                            "explanation": f"Amount ${amount:.2f} is significantly higher than average ${avg_amount:.2f} for {category}",
                            "confidence_score": min(0.9, abs(amount - avg_amount) / (std_amount + 1))
                        })
        
        return anomalies

    def _generate_behavioral_insights(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate behavioral insights from transaction patterns."""
        insights = {
            "spending_triggers": [],
            "timing_patterns": {},
            "personality_indicators": {}
        }
        
        # Analyze timing patterns
        weekday_spending = defaultdict(float)
        weekend_spending = 0
        weekday_count = defaultdict(int)
        
        for tx in transactions:
            try:
                date = datetime.fromisoformat(tx.get('date', '2024-01-01'))
                amount = abs(tx.get('amount', 0))
                weekday = date.weekday()  # 0 = Monday, 6 = Sunday
                
                weekday_spending[weekday] += amount
                weekday_count[weekday] += 1
                
                if weekday >= 5:  # Weekend
                    weekend_spending += amount
            except:
                continue
        
        # Find peak spending days
        if weekday_spending:
            peak_day = max(weekday_spending.keys(), key=lambda d: weekday_spending[d])
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            insights["timing_patterns"]["peak_spending_day"] = days[peak_day]
            insights["timing_patterns"]["weekend_vs_weekday_ratio"] = weekend_spending / sum(weekday_spending.values()) if sum(weekday_spending.values()) > 0 else 0
        
        return insights

    def _detect_subscriptions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect subscription services from transaction patterns."""
        merchant_transactions = defaultdict(list)
        
        for tx in transactions:
            merchant_key = self._extract_merchant_key(tx.get('merchant_name', ''))
            merchant_transactions[merchant_key].append(tx)
        
        subscriptions = []
        for merchant_key, txs in merchant_transactions.items():
            if len(txs) >= 2:  # Multiple transactions
                amounts = [abs(tx.get('amount', 0)) for tx in txs]
                
                # Check if amounts are consistent (subscription pattern)
                if amounts and max(amounts) - min(amounts) < max(amounts) * 0.05:
                    # Classify subscription type
                    service_type = "Other"
                    for pattern, svc_type in SUBSCRIPTION_PATTERNS.items():
                        if re.search(pattern, merchant_key):
                            service_type = svc_type
                            break
                    
                    subscriptions.append({
                        "merchant_name": txs[0].get('merchant_name', ''),
                        "service_type": service_type,
                        "frequency": "monthly",  # Simplified
                        "average_amount": round(statistics.mean(amounts), 2),
                        "transaction_count": len(txs),
                        "category": service_type,
                        "first_charge_date": min(tx.get('date', '') for tx in txs),
                        "last_charge_date": max(tx.get('date', '') for tx in txs)
                    })
        
        return subscriptions

    def _detect_duplicate_services(self, subscriptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect duplicate subscription services."""
        service_groups = defaultdict(list)
        
        for sub in subscriptions:
            service_type = sub['service_type']
            service_groups[service_type].append(sub)
        
        duplicates = []
        for service_type, services in service_groups.items():
            if len(services) > 1:
                costs = [s['average_amount'] for s in services]
                potential_savings = sum(costs) - max(costs)  # Keep the most expensive one
                
                duplicates.append({
                    "service_type": service_type,
                    "conflicting_services": [s['merchant_name'] for s in services],
                    "monthly_costs": costs,
                    "potential_monthly_savings": round(potential_savings, 2),
                    "recommendation": f"Consider keeping only one {service_type.lower()} service"
                })
        
        return duplicates

    def _generate_delivery_optimization(self, amount: float, transactions: int, personality_type: str) -> Dict[str, Any]:
        """Generate delivery-specific optimization recommendations."""
        if amount <= 50:  # Not worth optimizing small amounts
            return None
        
        strategies = OPTIMIZATION_STRATEGIES.get(personality_type, OPTIMIZATION_STRATEGIES['planner'])
        strategy = strategies.get('food_delivery', strategies.get('subscriptions', 'Reduce delivery frequency'))
        
        # Calculate potential savings (conservative estimate)
        potential_savings = amount * 0.3  # 30% reduction
        
        return {
            "opportunity_type": "Food Delivery Optimization",
            "description": strategy,
            "current_monthly_spend": amount,
            "transaction_frequency": transactions,
            "potential_monthly_savings": round(potential_savings, 2),
            "confidence_score": 0.8,
            "personality_fit": self._calculate_personality_fit(personality_type, "food_delivery"),
            "implementation_difficulty": "easy" if personality_type in ['planner', 'saver'] else "medium"
        }

    def _generate_subscription_optimization(self, amount: float, personality_type: str) -> Dict[str, Any]:
        """Generate subscription-specific optimization."""
        if amount <= 20:
            return None
        
        strategies = OPTIMIZATION_STRATEGIES.get(personality_type, OPTIMIZATION_STRATEGIES['planner'])
        strategy = strategies.get('subscriptions', 'Review subscription usage')
        
        potential_savings = amount * 0.25  # 25% reduction
        
        return {
            "opportunity_type": "Subscription Optimization",
            "description": strategy,
            "current_monthly_spend": amount,
            "potential_monthly_savings": round(potential_savings, 2),
            "confidence_score": 0.7,
            "personality_fit": self._calculate_personality_fit(personality_type, "subscriptions"),
            "implementation_difficulty": "easy"
        }

    def _generate_shopping_optimization(self, amount: float, transactions: int, personality_type: str) -> Dict[str, Any]:
        """Generate shopping-specific optimization."""
        if amount <= 100:
            return None
        
        strategies = OPTIMIZATION_STRATEGIES.get(personality_type, OPTIMIZATION_STRATEGIES['planner'])
        strategy = strategies.get('shopping', 'Make planned purchases')
        
        potential_savings = amount * 0.15  # 15% reduction
        
        return {
            "opportunity_type": "Shopping Optimization", 
            "description": strategy,
            "current_monthly_spend": amount,
            "transaction_frequency": transactions,
            "potential_monthly_savings": round(potential_savings, 2),
            "confidence_score": 0.6,
            "personality_fit": self._calculate_personality_fit(personality_type, "shopping"),
            "implementation_difficulty": "medium"
        }

    def _calculate_personality_fit(self, personality_type: str, optimization_type: str) -> float:
        """Calculate how well an optimization fits the user's personality."""
        fit_matrix = {
            'saver': {'food_delivery': 0.9, 'subscriptions': 0.9, 'shopping': 0.8},
            'planner': {'food_delivery': 0.8, 'subscriptions': 0.7, 'shopping': 0.9},
            'convenience': {'food_delivery': 0.4, 'subscriptions': 0.6, 'shopping': 0.5},
            'impulse': {'food_delivery': 0.6, 'subscriptions': 0.8, 'shopping': 0.3},
            'spender': {'food_delivery': 0.3, 'subscriptions': 0.4, 'shopping': 0.2}
        }
        
        return fit_matrix.get(personality_type, {}).get(optimization_type, 0.5)

    def _generate_personality_aware_alert(self, category: Dict[str, Any], alert_type: str) -> str:
        """Generate personality-aware alert messages."""
        category_name = category['category_name']
        percentage = category['percentage_used']
        
        # Simplified personality-aware messaging
        if alert_type == "exceeded_100":
            return f"You've exceeded your {category_name} budget by {percentage - 100:.1f}%. Consider reviewing your spending patterns."
        elif alert_type == "alert_90":
            return f"You're close to your {category_name} budget limit at {percentage:.1f}%. Time to slow down spending in this area."
        else:
            return f"You've used {percentage:.1f}% of your {category_name} budget. You're on track but keep an eye on it."

    def _generate_variance_analysis(self, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate budget variance analysis."""
        overspending = [c for c in categories if c['percentage_used'] > 100]
        underspending = [c for c in categories if c['percentage_used'] < 50]
        
        suggestions = []
        if overspending:
            suggestions.append("Consider reallocating budget from underspent categories to overspent ones")
        if underspending:
            suggestions.append("You have room to spend more in these categories or reallocate the budget")
        
        return {
            "overspending_categories": [{"category": c['category_name'], "overage": c['percentage_used'] - 100} for c in overspending],
            "underspending_categories": [{"category": c['category_name'], "unused": 100 - c['percentage_used']} for c in underspending],
            "adjustment_suggestions": suggestions
        }


# Singleton instance
_spending_service = None


def get_spending_service() -> SpendingService:
    """Get or create the global spending service instance."""
    global _spending_service
    if _spending_service is None:
        _spending_service = SpendingService()
    return _spending_service