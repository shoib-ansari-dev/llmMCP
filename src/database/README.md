# Database Schema

## Overview

PostgreSQL database with SQLAlchemy ORM for the Document Analysis application.

## Tables

### Users & Authentication

| Table | Purpose |
|-------|---------|
| `users` | User accounts, profiles, authentication |
| `password_reset_tokens` | Short-lived tokens for password reset |
| `refresh_tokens` | JWT refresh tokens for session management |

### Subscriptions & Billing

| Table | Purpose |
|-------|---------|
| `subscriptions` | User subscription tier, limits, Stripe integration |

### Documents

| Table | Purpose |
|-------|---------|
| `documents` | Document metadata, Azure Blob reference |
| `document_chunks` | Chunked content for RAG, embedding IDs |

### API & Usage

| Table | Purpose |
|-------|---------|
| `api_keys` | Programmatic API access keys |
| `usage_logs` | Usage tracking for billing & analytics |

## Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USERS                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  users                                                                   │
│  ├── id (UUID, PK)                                                      │
│  ├── email (unique, indexed)                                            │
│  ├── name                                                                │
│  ├── password_hash                                                       │
│  ├── provider (email|google)                                            │
│  ├── google_id (unique, indexed)                                        │
│  ├── is_active, is_verified, is_admin                                   │
│  ├── avatar_url, timezone                                                │
│  └── created_at, updated_at, last_login_at                              │
│                                                                          │
│  ┌─────────────────────────────────────────────┐                        │
│  │ password_reset_tokens                       │                        │
│  │ ├── user_id (FK → users)                    │                        │
│  │ ├── token_hash (unique)                     │                        │
│  │ └── expires_at, used_at                     │                        │
│  └─────────────────────────────────────────────┘                        │
│                                                                          │
│  ┌─────────────────────────────────────────────┐                        │
│  │ refresh_tokens                              │                        │
│  │ ├── user_id (FK → users)                    │                        │
│  │ ├── token_hash (unique)                     │                        │
│  │ ├── device_info, ip_address                 │                        │
│  │ └── expires_at, revoked_at                  │                        │
│  └─────────────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          SUBSCRIPTIONS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  subscriptions                                                           │
│  ├── user_id (FK → users, unique)                                       │
│  ├── tier (free|pro|business|enterprise)                                │
│  ├── status (active|cancelled|past_due|trialing)                        │
│  ├── stripe_customer_id, stripe_subscription_id                         │
│  ├── docs_per_month, pages_per_doc, api_calls_per_month (limits)        │
│  ├── docs_used_this_month, api_calls_this_month (usage)                 │
│  └── current_period_start, current_period_end                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           DOCUMENTS                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  documents                                                               │
│  ├── id (UUID, PK)                                                      │
│  ├── owner_id (FK → users, indexed)                                     │
│  ├── filename, original_filename                                         │
│  ├── file_type (pdf|excel|csv|word|web|text)                            │
│  ├── file_size, mime_type                                                │
│  ├── blob_name (Azure Blob path, unique)                                │
│  ├── status (pending|processing|completed|failed)                       │
│  ├── page_count, word_count                                              │
│  ├── summary, key_insights (JSON), extracted_entities (JSON)            │
│  └── created_at, processed_at                                           │
│                                                                          │
│  ┌─────────────────────────────────────────────┐                        │
│  │ document_chunks                             │                        │
│  │ ├── document_id (FK → documents)            │                        │
│  │ ├── chunk_index (unique per document)       │                        │
│  │ ├── content (text)                          │                        │
│  │ ├── page_number, section_title              │                        │
│  │ └── embedding_id (ChromaDB reference)       │                        │
│  └─────────────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           API & USAGE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  api_keys                                                                │
│  ├── user_id (FK → users)                                               │
│  ├── name, key_prefix, key_hash (unique)                                │
│  ├── scopes (array: read, write, admin)                                 │
│  ├── rate_limit_per_minute, rate_limit_per_day                          │
│  └── is_active, expires_at, last_used_at                                │
│                                                                          │
│  usage_logs                                                              │
│  ├── user_id (FK → users, nullable)                                     │
│  ├── action (upload|analyze|query|etc.)                                 │
│  ├── resource_type, resource_id                                         │
│  ├── tokens_used, pages_processed, processing_time_ms                   │
│  ├── cost_usd (estimated)                                                │
│  └── ip_address, user_agent, api_key_id                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## File Storage

Documents are stored in **Azure Blob Storage**:
- Path: `users/{user_id}/documents/{uuid}_{filename}`
- SAS URLs generated for temporary access
- Metadata stored in PostgreSQL, binary in Azure

## Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=docanalysis
POSTGRES_PASSWORD=your_password
POSTGRES_DB=docanalysis

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
# OR
AZURE_STORAGE_ACCOUNT_NAME=your_account
AZURE_STORAGE_ACCOUNT_KEY=your_key
AZURE_STORAGE_CONTAINER=documents
```

## Usage

```python
from src.database import get_db, UserRepository, DocumentRepository

# In FastAPI endpoint
@app.post("/documents")
async def upload(db: AsyncSession = Depends(get_db)):
    doc_repo = DocumentRepository(db)
    document = await doc_repo.create(...)
```

