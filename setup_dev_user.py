#!/usr/bin/env python3
"""
Setup Default User for Local Development
Creates a test user in SQLite database for local development.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def setup_default_user():
    """Create a default test user for development."""
    print("=" * 70)
    print("Local Development User Setup")
    print("=" * 70)

    # Import after path is set
    from src.database.config import get_db_settings
    from src.database.connection import init_db
    from src.auth.store import get_user_store, reset_user_store

    # Check environment
    settings = get_db_settings()
    print(f"\n✓ Environment: {settings.ENVIRONMENT}")
    print(f"✓ Database Type: {settings.db_type.value}")

    if settings.is_sqlite:
        print(f"✓ SQLite Path: {settings.SQLITE_PATH}")

    # Initialize database
    print("\n▶ Initializing database...")
    try:
        await init_db()
        print("✓ Database tables created/verified")
    except Exception as e:
        print(f"✗ Database init failed: {e}")
        return False

    # Get user store
    print("\n▶ Creating user store...")
    reset_user_store()
    store = get_user_store()
    print(f"✓ Using {type(store).__name__}")

    # Create test user
    print("\n▶ Creating default test user...")
    test_user_email = "test@example.com"
    test_user_password = "Test@123456"
    test_user_name = "Test User"

    try:
        # Check if user already exists
        existing = await store.get_by_email(test_user_email)
        if existing:
            print(f"✓ User already exists: {test_user_email}")
            print(f"  ID: {existing.id}")
        else:
            # Create new user
            user = await store.create_user(
                email=test_user_email,
                password=test_user_password,
                name=test_user_name,
                is_verified=True
            )
            print(f"✓ Default user created: {user.email}")
            print(f"  ID: {user.id}")
            print(f"  Name: {user.name}")
    except Exception as e:
        print(f"✗ User creation failed: {e}")
        return False

    # Verify password
    print("\n▶ Verifying credentials...")
    from src.auth.password import verify_password

    user = await store.get_by_email(test_user_email)
    if user and user.password_hash:
        is_valid = verify_password(test_user_password, user.password_hash)
        if is_valid:
            print("✓ Password verification successful")
        else:
            print("✗ Password verification failed")
            return False

    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print("\n📝 Login Credentials for Local Development:")
    print(f"   Email: {test_user_email}")
    print(f"   Password: {test_user_password}")
    print("\n💡 Tips:")
    print("   1. AUTH_DEV_MODE=true in .env bypasses login completely")
    print("   2. If login is required, use above credentials")
    print("   3. Dev mode auto-creates a temporary user")
    print("\n▶ To start the app:")
    print("   ./start.sh")
    print("\n" + "=" * 70)

    return True


if __name__ == "__main__":
    success = asyncio.run(setup_default_user())
    sys.exit(0 if success else 1)

