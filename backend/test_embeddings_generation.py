"""
Vynk (Localy) - Step 6 & 7: Embeddings Generation & Semantic Similarity Test
Generates real embeddings for users and activities, and tests cosine similarity queries.
"""

from sqlalchemy import text
from database import SessionLocal
import models
from embedding_service import (
    backfill_all_embeddings,
    generate_embedding,
    build_user_semantic_text,
    build_activity_semantic_text,
)

def test_embeddings_generation_and_search():
    print("=" * 70)
    print("STEP 6 & 7: EMBEDDINGS GENERATION & SEMANTIC SIMILARITY SEARCH")
    print("=" * 70)

    db = SessionLocal()
    try:
        # 1. Backfill embeddings for all users and activities
        print("\n1. Generating and storing embeddings for all users & activities...")
        stats = backfill_all_embeddings(db)
        print(f"   [OK] Embedded {stats['users_embedded']} users and {stats['activities_embedded']} activities.")

        # 2. Verify all profiles have embeddings
        profiles_with_emb = db.query(models.Profile).filter(models.Profile.embedding.isnot(None)).count()
        activities_with_emb = db.query(models.Activity).filter(models.Activity.embedding.isnot(None)).count()
        print(f"   [OK] Stored in DB: {profiles_with_emb} profile embeddings, {activities_with_emb} activity embeddings.")
        assert profiles_with_emb > 0
        assert activities_with_emb > 0

        # 3. Test Semantic Query Similarity: "I want a badminton partner this Saturday"
        query_text = "I want someone to play casual badminton with this Saturday evening"
        print(f"\n2. Semantic Search Query: \"{query_text}\"")
        query_vec = generate_embedding(query_text)
        assert len(query_vec) == 1536

        # Query top matching users using pgvector cosine distance: 1 - (embedding <=> :query_vec)
        raw_results = db.execute(
            text("""
                SELECT p.user_id, p.display_name, p.approx_locality, 
                       1 - (p.embedding <=> :qvec) AS semantic_similarity
                FROM profiles p
                WHERE p.embedding IS NOT NULL
                ORDER BY p.embedding <=> :qvec
                LIMIT 5;
            """),
            {"qvec": str(query_vec)}
        ).fetchall()

        print("\n3. Semantic Matching Ranked Users:")
        for idx, (u_id, d_name, loc, sim) in enumerate(raw_results, start=1):
            print(f"   Rank #{idx}: {d_name} ({loc}) — Semantic Similarity = {float(sim):.4f}")

        # 4. Test Semantic Query for Tech: "Python AI study group"
        tech_query = "Need someone for Python coding and machine learning study sessions"
        print(f"\n4. Tech Semantic Search Query: \"{tech_query}\"")
        tech_vec = generate_embedding(tech_query)
        tech_results = db.execute(
            text("""
                SELECT p.user_id, p.display_name, p.approx_locality, 
                       1 - (p.embedding <=> :qvec) AS semantic_similarity
                FROM profiles p
                WHERE p.embedding IS NOT NULL
                ORDER BY p.embedding <=> :qvec
                LIMIT 5;
            """),
            {"qvec": str(tech_vec)}
        ).fetchall()

        print("\n5. Tech Semantic Matching Ranked Users:")
        for idx, (u_id, d_name, loc, sim) in enumerate(tech_results, start=1):
            print(f"   Rank #{idx}: {d_name} ({loc}) — Semantic Similarity = {float(sim):.4f}")

        print("\n" + "=" * 70)
        print("SUCCESS: Semantic Embeddings Generation & Similarity Search Verified!")
        print("=" * 70)
        return True
    finally:
        db.close()

if __name__ == "__main__":
    test_embeddings_generation_and_search()
