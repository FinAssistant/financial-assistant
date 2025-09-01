# API Specification

## REST API Design

Based on RESTful principles with clear resource boundaries, enhanced for Story 2.3 advanced spending analysis:

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
                  enum: [onboarding, general]
      responses:
        200:
          description: AI response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConversationResponse'

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

  # Enhanced Analysis Endpoints for Story 2.3
  /analysis/spending-patterns/{user_id}:
    get:
      summary: Get comprehensive spending pattern analysis with behavioral insights
      security:
        - bearerAuth: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Spending patterns with behavioral analysis
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SpendingAnalysis'

  /analysis/personality-profile:
    post:
      summary: Generate or update spending personality profile
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PersonalityProfileRequest'
      responses:
        200:
          description: Personality profile generated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PersonalityProfile'

  /analysis/anomaly-detection/{user_id}:
    get:
      summary: Detect unusual transactions and spending spikes
      security:
        - bearerAuth: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Anomaly detection results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnomalyDetectionResult'

  /analysis/optimization-opportunities/{user_id}:
    get:
      summary: Get personality-tailored cost reduction opportunities
      security:
        - bearerAuth: []
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Optimization opportunities
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/OptimizationOpportunity'

  /budget/categories:
    post:
      summary: Create or update budget categories with personality adjustments
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BudgetCategoryRequest'
      responses:
        201:
          description: Budget category created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BudgetCategory'

    get:
      summary: Get all budget categories with real-time tracking
      security:
        - bearerAuth: []
      responses:
        200:
          description: Budget categories with current status
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BudgetCategory'

  /budget/alerts:
    get:
      summary: Get budget variance alerts and notifications
      security:
        - bearerAuth: []
      responses:
        200:
          description: Active budget alerts
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BudgetAlert'

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

    # Enhanced schemas for Story 2.3
    SpendingAnalysis:
      type: object
      properties:
        user_id:
          type: string
        spending_patterns:
          type: object
          properties:
            recurring_expenses:
              type: array
              items:
                type: object
            seasonal_trends:
              type: array
              items:
                type: object
            anomalies:
              type: array
              items:
                type: object
        behavioral_insights:
          type: object
          properties:
            spending_triggers:
              type: array
              items:
                type: string
            timing_patterns:
              type: object
            personality_indicators:
              type: object

    PersonalityProfile:
      type: object
      properties:
        user_id:
          type: string
        primary_type:
          type: string
          enum: [saver, spender, planner, impulse, convenience]
        secondary_type:
          type: string
          enum: [saver, spender, planner, impulse, convenience]
        confidence_score:
          type: number
          minimum: 0
          maximum: 1
        spending_triggers:
          type: array
          items:
            type: string
        risk_tolerance:
          type: string
          enum: [high, medium, low]
        communication_style:
          type: string
          enum: [gentle, direct, encouraging, analytical, balanced]
        behavioral_insights:
          type: object

    PersonalityProfileRequest:
      type: object
      properties:
        transaction_history_days:
          type: integer
          default: 90
        include_behavioral_analysis:
          type: boolean
          default: true

    AnomalyDetectionResult:
      type: object
      properties:
        user_id:
          type: string
        anomalies:
          type: array
          items:
            type: object
            properties:
              transaction_id:
                type: string
              anomaly_type:
                type: string
              severity:
                type: string
                enum: [low, medium, high]
              explanation:
                type: string
              confidence_score:
                type: number

    OptimizationOpportunity:
      type: object
      properties:
        opportunity_type:
          type: string
        description:
          type: string
        potential_monthly_savings:
          type: number
        confidence_score:
          type: number
        personality_fit:
          type: number
        implementation_difficulty:
          type: string
          enum: [easy, medium, complex]

    BudgetCategory:
      type: object
      properties:
        id:
          type: string
        category_name:
          type: string
        monthly_limit:
          type: number
        current_spent:
          type: number
        percentage_used:
          type: number
        alert_thresholds:
          type: array
          items:
            type: string
        personality_adjusted:
          type: boolean

    BudgetCategoryRequest:
      type: object
      properties:
        category_name:
          type: string
        monthly_limit:
          type: number
        alert_thresholds:
          type: array
          items:
            type: string
        personality_adjustment:
          type: boolean
          default: true

    BudgetAlert:
      type: object
      properties:
        id:
          type: string
        category_name:
          type: string
        alert_type:
          type: string
          enum: [warning_75, alert_90, exceeded_100, anomaly]
        severity:
          type: string
          enum: [low, medium, high]
        message:
          type: string
        personality_aware_message:
          type: string
        created_at:
          type: string

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```
