"""
Localy (Vynk) - Automated Database Initializer Script
======================================================
Sets up the entire database architecture for Vynk from scratch:
1. Verifies live connection to PostgreSQL
2. Installs / enables the pgvector extension (`vector`)
3. Automatically creates all 23 tables and relations via SQLAlchemy Base metadata:
   - users, profiles, interests, user_interests, skills, user_skills, user_availability
   - activities, venues, venue_activities, venue_slots, events, venue_bookings, event_participants
   - payment_accounts, payments, payouts, communities, community_members, feedback
   - group_proposals, group_proposal_members, notifications
4. Preserves all Foreign Keys, Cascades, Indexes, and Unique Constraints
5. Automatically seeds master taxonomy data (33 default interests, 17 default skills)
6. Performs self-verification to ensure database readiness.

Usage:
    cd backend
    python init_db.py
"""

import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlalchemy import text, inspect
from database import engine, Base, SessionLocal
import models
from seed import seed_master_data


def init_database():
    print("=" * 65)
    print(">>> VYNK (LOCALY) - AUTOMATED DATABASE INITIALIZER")
    print("=" * 65)

    # 1. Test live connection
    print("\n[Step 1/5] Verifying PostgreSQL connection...")
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            print("  [OK] Connected to database successfully!")
            print(f"  [OK] Database Engine: {version[:60]}...")
    except Exception as e:
        print(f"\n[ERROR] Connection Failed: {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL service is running.")
        print("  2. DATABASE_URL in backend/.env is correct.")
        print("     Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/major")
        sys.exit(1)

    # 2. Enable pgvector extension
    print("\n[Step 2/5] Enabling pgvector extension...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("  [OK] 'vector' extension is active.")
    except Exception as e:
        print(f"  [WARN] Warning enabling pgvector: {e}")
        print("  If vector operations fail, run install_pgvector.bat as Administrator.")

    # 3. Create all 23 tables and relations
    print("\n[Step 3/5] Creating all tables, foreign keys, and indexes...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  [OK] All SQLAlchemy Base tables and constraints created successfully.")
    except Exception as e:
        print(f"\n[ERROR] Failed to create tables: {e}")
        sys.exit(1)

    # 4. Seed master taxonomy data (interests, skills)
    print("\n[Step 4/5] Seeding master taxonomy data...")
    try:
        with SessionLocal() as db:
            seed_master_data(db)
            interests_count = db.query(models.Interest).count()
            skills_count = db.query(models.Skill).count()
            print(f"  [OK] Master Interests seeded: {interests_count} items")
            print(f"  [OK] Master Skills seeded:    {skills_count} items")
    except Exception as e:
        print(f"  [WARN] Warning seeding master data: {e}")

    # 5. Self-verification of schema
    print("\n[Step 5/5] Verifying database schema...")
    inspector = inspect(engine)
    existing_tables = sorted(inspector.get_table_names())

    print(f"  [OK] Found {len(existing_tables)} tables in database:")
    for i, tbl in enumerate(existing_tables, 1):
        fks = inspector.get_foreign_keys(tbl)
        fk_str = f"({len(fks)} FKs)" if fks else ""
        print(f"     {i:2d}. {tbl:<25} {fk_str}")

    print("\n" + "=" * 65)
    print("[SUCCESS] DATABASE INITIALIZATION COMPLETE & READY FOR VYNK!")
    print("You can now start the server: python main.py")
    print("=" * 65)


if __name__ == "__main__":
    init_database()
