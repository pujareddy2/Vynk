"""
Vynk (Localy) - pgvector Verification Script
Tests PostgreSQL vector extension and cosine similarity operations.
"""

import sys
from sqlalchemy import text
from database import SessionLocal

def verify_pgvector():
    print("=" * 70)
    print("VERIFYING PGVECTOR EXTENSION IN VYNK POSTGRESQL DATABASE")
    print("=" * 70)

    db = SessionLocal()
    try:
        # 1. Enable extension
        print("\n1. Enabling 'vector' extension...")
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        db.commit()
        print("   [OK] Extension enabled successfully!")

        # 2. Check extension version
        ext_info = db.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchone()
        print(f"   [OK] Detected: {ext_info[0]} version {ext_info[1]}")

        # 3. Create a temporary vector test table
        print("\n2. Testing vector column creation and cosine similarity...")
        db.execute(text("DROP TABLE IF EXISTS _test_vector_probe;"))
        db.execute(text("CREATE TABLE _test_vector_probe (id serial primary key, name text, embedding vector(3));"))
        db.execute(text("INSERT INTO _test_vector_probe (name, embedding) VALUES ('Badminton Seeker', '[1, 0, 0]'), ('Amit Badminton Pro', '[0.9, 0.1, 0]'), ('Sneha Partial', '[0.5, 0.5, 0]');"))
        db.commit()

        # 4. Perform cosine similarity query (<=> operator)
        results = db.execute(text("""
            SELECT name, 1 - (embedding <=> '[1, 0, 0]') AS cosine_similarity
            FROM _test_vector_probe
            ORDER BY embedding <=> '[1, 0, 0]';
        """)).fetchall()

        print("\n3. Cosine Similarity Query Results:")
        for r in results:
            print(f"   • {r[0]}: Similarity = {float(r[1]):.4f}")

        # 5. Cleanup probe table
        db.execute(text("DROP TABLE IF EXISTS _test_vector_probe;"))
        db.commit()

        print("\n" + "=" * 70)
        print("SUCCESS: pgvector is enabled and fully operational in PostgreSQL!")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"\n[ERROR] pgvector verification failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_pgvector()
    sys.exit(0 if success else 1)
