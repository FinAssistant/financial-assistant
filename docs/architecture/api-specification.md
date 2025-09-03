# API Specification

## REST API Design

Based on RESTful principles with clear resource boundaries:

```yaml
openapi: 3.0.0
info:
  title: AI Financial Assistant API
  version: 1.0.0
  description: POC API for AI-powered financial assistant
servers:
  - url: http://localhost:8000/api
    description: Development server

paths:
  /auth/register:
    post:
      summary: User registration
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
                name:
                  type: string
      responses:
        201:
          description: Registration successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  user:
                    $ref: '#/components/schemas/User'
  
  /auth/login:
    post:
      summary: User login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  user:
                    $ref: '#/components/schemas/User'

  /conversation/send:
    post:
      summary: Send message to AI assistant
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                session_id:
                  type: string
                session_type:
                  type: string
                  enum: [onboarding, general, investment]
      responses:
        200:
          description: AI response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConversationResponse'

  /investment/recommendations:
    post:
      summary: Get personalized investment recommendations
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                include_rationale:
                  type: boolean
                  default: true
                investment_amount:
                  type: number
                  description: Optional specific amount user wants to invest
      responses:
        200:
          description: Investment recommendations generated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InvestmentRecommendations'

  /investment/risk-assessment:
    post:
      summary: Submit or update risk tolerance assessment
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RiskAssessment'
      responses:
        200:
          description: Risk assessment saved
          content:
            application/json:
              schema:
                type: object
                properties:
                  risk_profile:
                    $ref: '#/components/schemas/RiskProfile'
                  
  /investment/market-data/{symbol}:
    get:
      summary: Get current market data for specific stock/ETF
      security:
        - bearerAuth: []
      parameters:
        - name: symbol
          in: path
          required: true
          schema:
            type: string
          description: Stock or ETF symbol (e.g., AAPL, VTI)
      responses:
        200:
          description: Market data retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MarketData'

  /investment/portfolio-analysis:
    get:
      summary: Analyze user's current investment capacity and allocation
      security:
        - bearerAuth: []
      responses:
        200:
          description: Portfolio analysis completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PortfolioAnalysis'

  /plaid/link-token:
    post:
      summary: Create Plaid Link token
      security:
        - bearerAuth: []
      responses:
        200:
          description: Link token created
          content:
            application/json:
              schema:
                type: object
                properties:
                  link_token:
                    type: string

  /plaid/exchange:
    post:
      summary: Exchange public token for access token
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                public_token:
                  type: string
      responses:
        200:
          description: Accounts connected successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  accounts:
                    type: array
                    items:
                      $ref: '#/components/schemas/PlaidAccount'

  /accounts:
    get:
      summary: Get user's connected accounts
      security:
        - bearerAuth: []
      responses:
        200:
          description: List of connected accounts
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PlaidAccount'

  /transactions/{account_id}:
    get:
      summary: Get transactions for account
      security:
        - bearerAuth: []
      parameters:
        - name: account_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Account transactions
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Transaction'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
        createdAt:
          type: string
        profileComplete:
          type: boolean
    
    PlaidAccount:
      type: object
      properties:
        id:
          type: string
        accountName:
          type: string
        accountType:
          type: string
          enum: [checking, savings, credit, loan, mortgage]
        balance:
          type: number
        lastSynced:
          type: string
    
    Transaction:
      type: object
      properties:
        id:
          type: string
        amount:
          type: number
        category:
          type: string
        description:
          type: string
        date:
          type: string
        pending:
          type: boolean
    
    ConversationResponse:
      type: object
      properties:
        message:
          type: string
        session_id:
          type: string
        current_step:
          type: string
        metadata:
          type: object

    RiskAssessment:
      type: object
      properties:
        volatility_comfort:
          type: integer
          minimum: 1
          maximum: 10
          description: Comfort level with market volatility (1=very conservative, 10=very aggressive)
        investment_timeline:
          type: string
          enum: [short-term, medium-term, long-term]
          description: Investment time horizon
        investment_percentage:
          type: number
          minimum: 0
          maximum: 100
          description: Percentage of savings to allocate to investments
        previous_experience:
          type: string
          enum: [none, basic, intermediate, advanced]
          description: Previous investment experience level

    RiskProfile:
      type: object
      properties:
        level:
          type: string
          enum: [conservative, moderate, aggressive]
        volatility_comfort:
          type: integer
        investment_timeline:
          type: string
        investment_percentage:
          type: number
        last_assessed:
          type: string
          format: date-time

    InvestmentRecommendation:
      type: object
      properties:
        symbol:
          type: string
          description: Stock or ETF symbol
        name:
          type: string
          description: Asset name
        allocation_percentage:
          type: number
          description: Recommended portfolio allocation percentage
        current_price:
          type: number
          description: Current market price
        recommendation_rationale:
          type: string
          description: Explanation for recommendation
        sector:
          type: string
          description: Asset sector or category
        risk_level:
          type: string
          enum: [low, moderate, high]

    InvestmentRecommendations:
      type: object
      properties:
        recommendations:
          type: array
          items:
            $ref: '#/components/schemas/InvestmentRecommendation'
        total_allocation:
          type: number
          description: Total recommended investment amount
        risk_warnings:
          type: array
          items:
            type: string
        rationale:
          type: string
          description: Overall portfolio rationale
        generated_at:
          type: string
          format: date-time

    MarketData:
      type: object
      properties:
        symbol:
          type: string
        current_price:
          type: number
        price_change:
          type: number
        price_change_percent:
          type: number
        volume:
          type: number
        market_cap:
          type: number
        pe_ratio:
          type: number
        sector:
          type: string
        last_updated:
          type: string
          format: date-time

    PortfolioAnalysis:
      type: object
      properties:
        investment_capacity:
          type: number
          description: Available funds for investment based on cash flow
        current_savings_rate:
          type: number
          description: Monthly savings rate percentage
        recommended_investment_amount:
          type: number
          description: Suggested monthly investment amount
        risk_profile:
          $ref: '#/components/schemas/RiskProfile'
        analysis_summary:
          type: string
          description: Summary of financial analysis

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```
