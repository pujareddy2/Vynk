"""
Vynk (Localy) - Database Vector Column Migration
Adds vector(1536) columns to profiles and activities tables.
"""

from sqlalchemy import text
from database import SessionLocal

def run_migration():
    print("=" * 70)
    print("APPLYING VECTOR(1536) EMBEDDING SCHEMA MIGRATION")
    print("=" * 70)

    db = SessionLocal()
    try:
        # 1. Ensure vector extension is enabled
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # 2. Add embedding column to profiles
        print("\n1. Adding 'embedding vector(1536)' to 'profiles' table...")
        db.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS embedding vector(1536);"))

        # 3. Add embedding column to activities
        print("2. Adding 'embedding vector(1536)' to 'activities' table...")
        db.execute(text("ALTER TABLE activities ADD COLUMN IF NOT EXISTS embedding vector(1536);"))

        db.commit()

        # 4. Verify columns
        p_col = db.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'profiles' AND column_name = 'embedding';
        """)).fetchall()

        a_col = db.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'activities' AND column_name = 'embedding';
        """)).fetchall()

        print(f"\n[OK] profiles.embedding column:   {p_col}")
        print(f"[OK] activities.embedding column: {a_col}")

        print("\n" + "=" * 70)
        print("SUCCESS: Embedding columns added and verified in PostgreSQL!")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
