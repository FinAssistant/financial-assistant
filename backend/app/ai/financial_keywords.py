"""
Financial keywords for detecting conversation content that should be stored in Graphiti.

This module contains comprehensive lists of financial terms that indicate when a user
conversation contains financial context worth storing for future reference and analysis.
"""

# Core financial concepts and goals
FINANCIAL_GOALS = {
    "save", "saving", "savings", "emergency fund", "rainy day fund",
    "retirement", "retire", "401k", "403b", "ira", "roth ira", "pension",
    "vacation fund", "travel fund", "education fund", "college fund",
    "house fund", "home fund", "down payment", "mortgage",
    "car fund", "vehicle fund", "wedding fund", "baby fund",
    "debt payoff", "pay off debt", "debt free", "financial independence",
    "fire", "early retirement", "nest egg", "financial goal", "goal",
    "target", "plan", "planning", "financial planning"
}

# Income and earnings
INCOME_KEYWORDS = {
    "income", "salary", "wage", "wages", "paycheck", "pay", "earnings",
    "bonus", "commission", "tips", "freelance", "gig work", "side hustle",
    "raise", "promotion", "overtime", "hourly", "annual", "monthly income",
    "gross income", "net income", "take home", "after tax",
    "unemployment", "disability", "social security", "pension income"
}

# Spending and expenses
EXPENSE_KEYWORDS = {
    "spend", "spending", "expense", "expenses", "cost", "costs",
    "budget", "budgeting", "bills", "bill", "payment", "payments",
    "rent", "mortgage payment", "utilities", "groceries", "gas",
    "insurance", "car payment", "student loan", "credit card payment",
    "subscription", "netflix", "spotify", "gym membership",
    "dining out", "restaurants", "entertainment", "shopping",
    "medical expenses", "healthcare", "prescription", "doctor",
    "childcare", "daycare", "school", "tuition"
}

# Debt and credit
DEBT_KEYWORDS = {
    "debt", "loan", "loans", "credit", "credit card", "balance",
    "owe", "owing", "borrowed", "borrow", "borrowing",
    "student loan", "car loan", "personal loan", "mortgage",
    "credit score", "credit report", "interest", "interest rate",
    "apr", "principal", "minimum payment", "late fee",
    "default", "bankruptcy", "consolidation", "refinance",
    "pay off", "payoff", "debt free"
}

# Investment and wealth building
INVESTMENT_KEYWORDS = {
    "invest", "investing", "investment", "investments", "portfolio",
    "stocks", "stock", "shares", "etf", "mutual fund", "index fund",
    "bonds", "treasury", "cd", "certificate of deposit",
    "cryptocurrency", "crypto", "bitcoin", "ethereum",
    "real estate", "reit", "property", "rental property",
    "dividend", "dividends", "capital gains", "appreciation",
    "risk", "risk tolerance", "volatility", "market",
    "bull market", "bear market", "recession", "inflation",
    "diversification", "asset allocation", "rebalancing"
}

# Banking and accounts
BANKING_KEYWORDS = {
    "bank", "banking", "account", "checking", "savings account",
    "money market", "high yield", "interest rate", "apy",
    "deposit", "withdrawal", "transfer", "atm", "debit card",
    "online banking", "mobile banking", "branch", "teller",
    "overdraft", "fee", "maintenance fee", "minimum balance",
    "direct deposit", "automatic payment", "bill pay"
}

# Financial amounts and metrics
AMOUNT_KEYWORDS = {
    "$", "dollar", "dollars", "cent", "cents", "money", "cash",
    "thousand", "k", "million", "billion", "percent", "%",
    "monthly", "annual", "yearly", "weekly", "daily",
    "per month", "per year", "per week", "each month", "every month"
}

# Financial status and situations
FINANCIAL_STATUS = {
    "broke", "tight budget", "financial stress", "money problems",
    "can't afford", "struggling", "financial difficulty",
    "living paycheck to paycheck", "behind on bills",
    "wealthy", "rich", "well off", "comfortable", "secure",
    "financial security", "financial freedom", "financially independent",
    "good shape", "doing well", "stable", "financially stable"
}

# Insurance and protection
INSURANCE_KEYWORDS = {
    "insurance", "health insurance", "life insurance", "auto insurance",
    "home insurance", "renters insurance", "disability insurance",
    "umbrella policy", "deductible", "premium", "copay", "coinsurance",
    "coverage", "claim", "beneficiary", "policy"
}

# Tax-related terms
TAX_KEYWORDS = {
    "tax", "taxes", "taxable", "tax return", "refund", "irs",
    "deduction", "deductible", "write off", "tax bracket",
    "withholding", "w2", "1099", "itemize", "standard deduction",
    "tax planning", "tax strategy", "capital gains tax"
}

# Combine all keyword sets into one comprehensive list
FINANCIAL_KEYWORDS = (
    FINANCIAL_GOALS | INCOME_KEYWORDS | EXPENSE_KEYWORDS | DEBT_KEYWORDS |
    INVESTMENT_KEYWORDS | BANKING_KEYWORDS | AMOUNT_KEYWORDS | 
    FINANCIAL_STATUS | INSURANCE_KEYWORDS | TAX_KEYWORDS
)

def contains_financial_keywords(text: str, threshold: int = 1) -> bool:
    """
    Check if text contains financial keywords above the specified threshold.
    
    Args:
        text: Text to analyze for financial keywords
        threshold: Minimum number of financial keywords required (default: 1)
        
    Returns:
        True if text contains at least 'threshold' financial keywords
    """
    if not text:
        return False
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Count matching keywords
    keyword_count = 0
    for keyword in FINANCIAL_KEYWORDS:
        if keyword in text_lower:
            keyword_count += 1
            if keyword_count >= threshold:
                return True
    
    return False