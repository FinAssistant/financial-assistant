# Deferred Architecture Implementations

This document tracks architectural components that are designed but not yet implemented, for future development phases.

## Completed Implementations

### SQLite Persistence (COMPLETED)
**Status**: ✅ Implemented  
**Date**: Current  
**Change**: Replaced in-memory storage with SQLite persistence

**Implementation Details**:
- SQLite database with async SQLAlchemy
- Maintains identical interface to previous in-memory storage
- Database file: `./financial_assistant.db`
- Auto-initialization on first use
- Sync wrapper for compatibility with existing code

**Files Modified**:
- `backend/app/core/database.py` - Complete replacement with SQLite
- `backend/app/core/database_models.py` - New SQLAlchemy models
- `backend/app/core/config.py` - Added database configuration
- `backend/pyproject.toml` - Added SQLAlchemy dependencies

## Deferred Security Implementations

### Token Encryption (cryptography.fernet)
**Status**: Designed but deferred  
**Architecture Reference**: `docs/architecture/security-and-performance.md:52-64`  
**Required Dependency**: `cryptography>=41.0.0`

**Current Implementation**: Plaid tokens stored in plain text in memory  
**Designed Implementation**: 
```python
class TokenEncryption:
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())
    
    def encrypt_token(self, token: str) -> str:
        return self.cipher.encrypt(token.encode()).decode()
```

**Migration Required When**: Moving to production environment
**Estimated Effort**: 1-2 days

## Implementation Notes

When implementing token encryption:
1. Add `cryptography>=41.0.0` to `backend/pyproject.toml`
2. Implement `TokenEncryption` class in `backend/app/core/security.py`
3. Update `backend/app/models/financial.py` to use encrypted token fields
4. Update all Plaid token storage/retrieval logic
5. Add encryption key management to environment configuration

**Security Impact**: Without encryption, Plaid access tokens are stored in plain text, creating security risk for production deployment.