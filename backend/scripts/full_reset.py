#!/usr/bin/env python3
"""Complete reset: Clear database AND Firebase users."""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
import firebase_admin
from firebase_admin import auth, credentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.models.tenant import Tenant
from src.models.user import User
from src.models.integration import Integration
from src.models.ticket import Ticket

def clear_database():
    """Clear all data from database."""
    print("\n" + "=" * 70)
    print("  Clearing Database")
    print("=" * 70)

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        tenant_count = db.query(Tenant).count()
        if tenant_count == 0:
            print("\n✅ Database already empty!")
        else:
            print(f"\n🗑️  Deleting {tenant_count} tenants...")
            deleted = db.query(Tenant).delete()
            db.commit()
            print(f"✅ Deleted {deleted} tenants and all related data")

        # Verify
        print("\n📊 Final database state:")
        print(f"  Tenants: {db.query(Tenant).count()}")
        print(f"  Users: {db.query(User).count()}")
        print(f"  Integrations: {db.query(Integration).count()}")
        print(f"  Tickets: {db.query(Ticket).count()}")

    except Exception as e:
        print(f"\n❌ Database Error: {e}")
        db.rollback()
    finally:
        db.close()


def clear_firebase():
    """Clear all Firebase users."""
    print("\n" + "=" * 70)
    print("  Clearing Firebase Users")
    print("=" * 70)

    # Initialize Firebase if not already initialized
    if not firebase_admin._apps:
        if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            print(f"\n❌ Firebase credentials not found at: {settings.FIREBASE_CREDENTIALS_PATH}")
            return
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)

    try:
        # List all users
        page = auth.list_users()
        users = list(page.users)

        # Get all users by iterating through pages
        while page.next_page_token:
            page = auth.list_users(page_token=page.next_page_token)
            users.extend(page.users)

        if not users:
            print("\n✅ No Firebase users to delete!")
            return

        print(f"\n📊 Found {len(users)} Firebase users:")
        for user in users:
            print(f"  - {user.email} (uid: {user.uid})")

        # Delete all users
        print(f"\n🗑️  Deleting all {len(users)} Firebase users...")

        deleted_count = 0
        for user in users:
            try:
                auth.delete_user(user.uid)
                deleted_count += 1
                print(f"  ✓ Deleted {user.email}")
            except Exception as e:
                print(f"  ✗ Failed to delete {user.email}: {e}")

        print(f"\n✅ Deleted {deleted_count}/{len(users)} Firebase users")

    except Exception as e:
        print(f"\n❌ Firebase Error: {e}")


def main():
    print("=" * 70)
    print("  FULL RESET - Database + Firebase")
    print("=" * 70)

    clear_database()
    clear_firebase()

    print("\n" + "=" * 70)
    print("✅ FULL RESET COMPLETE!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Go to http://localhost:3000")
    print("  2. Register with any email")
    print("  3. Test the complete OAuth flow")

if __name__ == "__main__":
    main()
