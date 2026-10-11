"""
Vynk (Localy) - Hybrid Semantic & Deterministic Matching Test Suite
Validates:
1. Generation and PostgreSQL pgvector storage of 1536-dim embeddings on profiles.
2. Hybrid scoring formula: Final Score = round(Deterministic Score * 0.70 + (Semantic Sim * 100) * 0.30)
3. GET /matches with hybrid ranking and breakdown.
4. POST /ai/intent/search with natural language query semantic similarity.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
import models
from embedding_service import update_user_embedding, update_activity_embedding, backfill_all_embeddings, compute_cosine_similarity

client = TestClient(app)


class TestHybridSemanticMatching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = SessionLocal()
        try:
            # Seed and backfill embeddings
            backfill_all_embeddings(db)
        finally:
            db.close()

    def test_01_profile_onboarding_generates_pgvector_embedding(self):
        """Verify that completing user onboarding automatically generates and saves 1536-dim vector."""
        email = "semantic.tester1@vynk.com"
        client.post("/auth/register", json={"email": email, "password": "password123", "confirm_password": "password123"})
        login_resp = client.post("/auth/login", json={"email": email, "password": "password123"})
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Submit onboarding
        onboard_payload = {
            "display_name": "Karthik Racket Coach",
            "bio": "Certified badminton trainer and racket sports enthusiast with 5 years experience coaching beginners.",
            "approx_locality": "Indiranagar, Bengaluru",
            "budget_preference": "moderate",
            "interest_ids": [1], # Badminton
            "skills": [{"skill_id": 14, "skill_level": "Advanced", "is_offering": True}],
            "availability": [{"day_of_week": "Saturday", "start_time": "17:00:00", "end_time": "20:00:00"}],
        }
        resp = client.post("/profile/me/onboarding", json=onboard_payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        user_id = resp.json()["user_id"]

        # Inspect database directly to verify pgvector column
        db = SessionLocal()
        try:
            profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
            self.assertIsNotNone(profile)
            self.assertIsNotNone(profile.embedding)
            # Embedding should be 1536 dimensions
            self.assertEqual(len(profile.embedding), 1536)
            print(f"\n[PASS] User #{user_id} ({profile.display_name}) embedding verified with {len(profile.embedding)} dimensions.")
        finally:
            db.close()

    def test_02_get_matches_hybrid_scoring(self):
        """Verify GET /matches returns deterministic_score, semantic_similarity, and hybrid match_score."""
        # Register Seeker
        seeker_email = "seeker.badminton@vynk.com"
        client.post("/auth/register", json={"email": seeker_email, "password": "password123", "confirm_password": "password123"})
        tok_resp = client.post("/auth/login", json={"email": seeker_email, "password": "password123"})
        token = tok_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        client.post("/profile/me/onboarding", json={
            "display_name": "Rohan Sports Seeker",
            "bio": "Looking for friendly badminton doubles and coaching on weekends.",
            "approx_locality": "Indiranagar, Bengaluru",
            "budget_preference": "flexible",
            "interest_ids": [1], # Badminton
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}],
        }, headers=headers)

        # Execute GET /matches?interest_id=1
        match_resp = client.get("/matches?interest_id=1", headers=headers)
        self.assertEqual(match_resp.status_code, 200)
        data = match_resp.json()

        self.assertIn("matches", data)
        self.assertGreater(data["total_candidates"], 0)

        top_match = data["matches"][0]
        print(f"\n[MATCH RESULT] Top Match: {top_match['display_name']}")
        print(f"  Final Hybrid Score:       {top_match['match_score']}/100")
        print(f"  Deterministic Score:      {top_match['deterministic_score']}/100")
        print(f"  Semantic Similarity:      {top_match['semantic_similarity']}")
        print(f"  Breakdown:                {top_match['match_breakdown']}")
        print(f"  Reasons:                  {top_match['match_reasons']}")

        self.assertIsNotNone(top_match["deterministic_score"])
        self.assertIsNotNone(top_match["semantic_similarity"])
        self.assertIn("semantic", top_match["match_breakdown"])
        self.assertIn("deterministic_total", top_match["match_breakdown"])

        # Validate scoring formula
        expected_hybrid = min(100, max(0, round((top_match["deterministic_score"] * 0.70) + ((top_match["semantic_similarity"] * 100.0) * 0.30))))
        self.assertEqual(top_match["match_score"], expected_hybrid)

    def test_03_ai_intent_search_hybrid_matching(self):
        """Verify POST /ai/intent/search performs AI intent parsing + hybrid semantic retrieval."""
        query = "I want someone who plays badminton and teaches beginners in Indiranagar on Saturday evening"
        resp = client.post("/ai/intent/search", json={"query": query, "limit": 5})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("intent_understood", data)
        self.assertIn("people_matches", data)
        self.assertGreater(len(data["people_matches"]), 0)

        top_cand = data["people_matches"][0]
        print(f"\n[AI SEARCH RESULT] Query: '{query}'")
        print(f"  Top Candidate:            {top_cand['display_name']}")
        print(f"  Final Hybrid Score:       {top_cand['match_score']}/100")
        print(f"  Deterministic Score:      {top_cand['deterministic_score']}/100")
        print(f"  Semantic Similarity:      {top_cand['semantic_similarity']}")
        print(f"  Match Breakdown:          {top_cand['match_breakdown']}")

        self.assertGreaterEqual(top_cand["match_score"], 10)
        self.assertIsNotNone(top_cand["semantic_similarity"])
        self.assertIn("semantic", top_cand["match_breakdown"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
