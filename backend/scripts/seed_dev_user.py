"""
Explicit CLI Development User Seeding Script for ChargeShield.
Executes user account seeding using environment variables DEV_ADMIN_USERNAME and DEV_ADMIN_PASSWORD.
Usage: python -m backend.scripts.seed_dev_user
"""

import sys
import os
from backend.core.config import settings
from backend.db.database import get_db_session, init_db
from backend.services.user_service import seed_dev_users
from backend.core.logging import logger

def main():
    print("=" * 60)
    print(" CHARGESHIELD — EXPLICIT DEVELOPMENT USER SEEDING")
    print("=" * 60)

    admin_username = settings.DEV_ADMIN_USERNAME or os.getenv("DEV_ADMIN_USERNAME", "admin")
    admin_password = settings.DEV_ADMIN_PASSWORD or os.getenv("DEV_ADMIN_PASSWORD")

    if not admin_password:
        print("[ERROR] DEV_ADMIN_PASSWORD environment variable is not set!")
        print("Provide credentials via environment variable before running:")
        print("  set DEV_ADMIN_USERNAME=admin")
        print("  set DEV_ADMIN_PASSWORD=YourSecurePassword123!")
        print("  python -m backend.scripts.seed_dev_user")
        sys.exit(1)

    init_db()

    with get_db_session() as db:
        users = seed_dev_users(
            db=db,
            admin_username=admin_username,
            admin_password=admin_password
        )
        print(f"[SUCCESS] Explicit seeding completed. Created {len(users)} user account(s).")
        print("Available accounts:")
        print(f"  - ADMIN:    username='{admin_username}', role='ADMIN'")
        print("  - ANALYST:  username='analyst', role='ANALYST'")
        print("  - REVIEWER: username='reviewer', role='REVIEWER'")
        print("  - AUDITOR:  username='auditor', role='AUDITOR'")
        print("=" * 60)

if __name__ == "__main__":
    main()
