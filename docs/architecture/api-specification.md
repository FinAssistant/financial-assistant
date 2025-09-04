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

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```
