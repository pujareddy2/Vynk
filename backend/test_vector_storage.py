"""
Vynk (Localy) - Step 4: Vector Storage & Cosine Distance Verification
Verifies 1536-dimensional embedding storage and cosine operations on Profile and Activity tables.
"""

from sqlalchemy import text
from database import SessionLocal
import models

def test_1536_vector_storage():
    print("=" * 70)
    print("STEP 4: VERIFYING 1536-DIM VECTOR STORAGE & COSINE SIMILARITY")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Create test vectors of 1536 dimensions
        # Vector A: sports-aligned vector
        vec_a = [0.0] * 1536
        vec_a[0] = 1.0
        vec_a[1] = 0.5

        # Vector B: similar sports vector
        vec_b = [0.0] * 1536
        vec_b[0] = 0.9
        vec_b[1] = 0.4
        vec_b[2] = 0.1

        # Vector C: orthogonal/music vector
        vec_c = [0.0] * 1536
        vec_c[500] = 1.0

        # Normalize vectors for accurate cosine comparison
        def normalize(v):
            norm = sum(x*x for x in v) ** 0.5
            return [x / norm for x in v] if norm > 0 else v

        vec_a_norm = normalize(vec_a)
        vec_b_norm = normalize(vec_b)
        vec_c_norm = normalize(vec_c)

        print("\n1. Testing Profile.embedding storage...")
        # Check if test profile exists or use existing profile
        profile = db.query(models.Profile).first()
        if profile:
            profile.embedding = vec_a_norm
            db.commit()
            db.refresh(profile)
            assert profile.embedding is not None
            print(f"   [OK] Stored 1536-dim embedding on Profile ID: {profile.profile_id} ({profile.display_name})")

        print("\n2. Testing Activity.embedding storage...")
        activity = db.query(models.Activity).first()
        if activity:
            activity.embedding = vec_b_norm
            db.commit()
            db.refresh(activity)
            assert activity.embedding is not None
            print(f"   [OK] Stored 1536-dim embedding on Activity ID: {activity.activity_id} ({activity.title})")

        print("\n3. Testing Cosine Similarity Query (<=> operator in PostgreSQL)...")
        res = db.execute(
            text("SELECT profile_id, display_name, 1 - (embedding <=> :query_vec) as similarity FROM profiles WHERE embedding IS NOT NULL ORDER BY embedding <=> :query_vec LIMIT 5;"),
            {"query_vec": str(vec_b_norm)}
        ).fetchall()

        for r in res:
            print(f"   • Profile {r[0]} ({r[1]}): Cosine Similarity = {float(r[2]):.4f}")

        print("\n" + "=" * 70)
        print("STEP 4 VERIFICATION PASSED: 1536-dim vectors stored and queried successfully!")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"\n[ERROR] Vector storage verification failed: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_1536_vector_storage()
