"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    auth_provider = postgresql.ENUM('email', 'google', name='authprovider', create_type=False)
    auth_provider.create(op.get_bind(), checkfirst=True)

    subscription_tier = postgresql.ENUM('free', 'pro', 'business', 'enterprise', name='subscriptiontier', create_type=False)
    subscription_tier.create(op.get_bind(), checkfirst=True)

    subscription_status = postgresql.ENUM('active', 'cancelled', 'past_due', 'trialing', name='subscriptionstatus', create_type=False)
    subscription_status.create(op.get_bind(), checkfirst=True)

    document_status = postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='documentstatus', create_type=False)
    document_status.create(op.get_bind(), checkfirst=True)

    document_type = postgresql.ENUM('pdf', 'excel', 'csv', 'word', 'web', 'text', name='documenttype', create_type=False)
    document_type.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('provider', auth_provider, nullable=False, server_default='email'),
        sa.Column('google_id', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('timezone', sa.String(50), server_default='UTC'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )

    # Password reset tokens
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_password_reset_tokens_expires', 'password_reset_tokens', ['expires_at'])

    # Refresh tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_refresh_tokens_expires', 'refresh_tokens', ['expires_at'])

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('tier', subscription_tier, nullable=False, server_default='free'),
        sa.Column('status', subscription_status, nullable=False, server_default='active'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), server_default='false'),
        sa.Column('docs_per_month', sa.Integer(), server_default='5'),
        sa.Column('pages_per_doc', sa.Integer(), server_default='10'),
        sa.Column('api_calls_per_month', sa.Integer(), server_default='100'),
        sa.Column('docs_used_this_month', sa.Integer(), server_default='0'),
        sa.Column('api_calls_this_month', sa.Integer(), server_default='0'),
        sa.Column('usage_reset_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Documents
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_type', document_type, nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('blob_name', sa.String(500), nullable=False, unique=True),
        sa.Column('blob_url', sa.String(1000), nullable=True),
        sa.Column('status', document_status, nullable=False, server_default='pending', index=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_insights', postgresql.JSON(), nullable=True),
        sa.Column('extracted_entities', postgresql.JSON(), nullable=True),
        sa.Column('source_url', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_documents_owner_created', 'documents', ['owner_id', 'created_at'])

    # Document chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_title', sa.String(500), nullable=True),
        sa.Column('char_count', sa.Integer(), nullable=False),
        sa.Column('embedding_id', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_document_chunks_doc_index', 'document_chunks', ['document_id', 'chunk_index'])
    op.create_unique_constraint('uq_document_chunk_index', 'document_chunks', ['document_id', 'chunk_index'])

    # API Keys
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('key_prefix', sa.String(10), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), server_default='{"read", "write"}'),
        sa.Column('rate_limit_per_minute', sa.Integer(), server_default='60'),
        sa.Column('rate_limit_per_day', sa.Integer(), server_default='10000'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
    )

    # Usage logs
    op.create_table(
        'usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0'),
        sa.Column('pages_processed', sa.Integer(), server_default='0'),
        sa.Column('processing_time_ms', sa.Integer(), server_default='0'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cost_usd', sa.Float(), server_default='0.0'),
        sa.Column('success', sa.Boolean(), server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )
    op.create_index('ix_usage_logs_user_action', 'usage_logs', ['user_id', 'action'])


def downgrade() -> None:
    op.drop_table('usage_logs')
    op.drop_table('api_keys')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('subscriptions')
    op.drop_table('refresh_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_table('users')

    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS documenttype')
    op.execute('DROP TYPE IF EXISTS documentstatus')
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS authprovider')

