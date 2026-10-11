import unittest
import time
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestTrustAwareMatching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # Interest setup
        badminton = models.Interest(name=f"Badminton Trust {ts}", category="Sports")
        cls.db.add(badminton)
        cls.db.commit()
        cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        cls.pwd = "password123"

        # 1. Searcher User (Me)
        cls.me_email = f"me.trust.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.me_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_me = client.post("/auth/login", json={"email": cls.me_email, "password": cls.pwd}).json()
        cls.tok_me = res_me["access_token"]
        cls.h_me = {"Authorization": f"Bearer {cls.tok_me}"}
        cls.user_me = client.get("/auth/me", headers=cls.h_me).json()
        client.patch("/profile/me", json={"display_name": "Me Searcher", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_me)

        # Set searcher interest & Saturday availability
        client.post("/profile/me/onboarding", json={
            "display_name": "Me Searcher",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id],
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}]
        }, headers=cls.h_me)

        # 2. Candidate A: High Compatibility (Badminton + Saturday + Indiranagar) + HIGH Reputation (5.0 rating)
        cls.cand_a_email = f"cand.a.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.cand_a_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_a = client.post("/auth/login", json={"email": cls.cand_a_email, "password": cls.pwd}).json()
        cls.tok_a = res_a["access_token"]
        cls.h_a = {"Authorization": f"Bearer {cls.tok_a}"}
        cls.user_a = client.get("/auth/me", headers=cls.h_a).json()
        client.post("/profile/me/onboarding", json={
            "display_name": "Candidate A (High Rep)",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id],
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}]
        }, headers=cls.h_a)

        # 3. Candidate B: SAME High Compatibility + NO Reviews (Fresh User)
        cls.cand_b_email = f"cand.b.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.cand_b_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_b = client.post("/auth/login", json={"email": cls.cand_b_email, "password": cls.pwd}).json()
        cls.tok_b = res_b["access_token"]
        cls.h_b = {"Authorization": f"Bearer {cls.tok_b}"}
        cls.user_b = client.get("/auth/me", headers=cls.h_b).json()
        client.post("/profile/me/onboarding", json={
            "display_name": "Candidate B (No Reviews)",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id],
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}]
        }, headers=cls.h_b)

        # 4. Candidate C: LOWER Compatibility (Different locality / no Saturday) + HIGH Reputation (5.0 rating)
        cls.cand_c_email = f"cand.c.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.cand_c_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_c = client.post("/auth/login", json={"email": cls.cand_c_email, "password": cls.pwd}).json()
        cls.tok_c = res_c["access_token"]
        cls.h_c = {"Authorization": f"Bearer {cls.tok_c}"}
        cls.user_c = client.get("/auth/me", headers=cls.h_c).json()
        client.post("/profile/me/onboarding", json={
            "display_name": "Candidate C (Low Comp, High Rep)",
            "approx_locality": "Gachibowli, Hyderabad",
            "interest_ids": [],
            "skills": [],
            "availability": [{"day_of_week": "Monday", "start_time": "09:00:00", "end_time": "11:00:00"}]
        }, headers=cls.h_c)

        # Peer Reviewer (to give ratings to Candidate A and Candidate C)
        cls.reviewer_email = f"reviewer.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.reviewer_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_rev = client.post("/auth/login", json={"email": cls.reviewer_email, "password": cls.pwd}).json()
        cls.h_rev = {"Authorization": f"Bearer {res_rev['access_token']}"}

        # Setup Activity
        act = client.post(
            "/activities",
            json={
                "interest_id": cls.badminton_id,
                "title": "Trust Match Badminton Activity",
                "description": "Activity for trust-aware matching tests",
            },
            headers=cls.h_me,
        ).json()
        cls.activity_id = act["activity_id"]

        # Seed Completed Event & 5-Star Feedback for Candidate A
        ev_a = client.post(
            "/events",
            json={
                "activity_id": cls.activity_id,
                "title": "Candidate A Event",
                "event_date": (date.today() + timedelta(days=50)).isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=cls.h_a,
        ).json()
        client.post(f"/events/{ev_a['event_id']}/join", headers=cls.h_rev)
        client.patch(f"/events/{ev_a['event_id']}", json={"status": "COMPLETED"}, headers=cls.h_a)
        client.post(f"/events/{ev_a['event_id']}/feedback", json={"rating": 5, "comment": "Excellent team player!"}, headers=cls.h_rev)

        # Seed Completed Event & 5-Star Feedback for Candidate C
        ev_c = client.post(
            "/events",
            json={
                "activity_id": cls.activity_id,
                "title": "Candidate C Event",
                "event_date": (date.today() + timedelta(days=51)).isoformat(),
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "max_capacity": 2,
            },
            headers=cls.h_c,
        ).json()
        client.post(f"/events/{ev_c['event_id']}/join", headers=cls.h_rev)
        client.patch(f"/events/{ev_c['event_id']}", json={"status": "COMPLETED"}, headers=cls.h_c)
        client.post(f"/events/{ev_c['event_id']}/feedback", json={"rating": 5, "comment": "Great person!"}, headers=cls.h_rev)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_high_compatibility_high_reputation_ranked_top(self):
        """Test case 1: Candidate A (High compatibility + 5-star reputation) gets high match_score & trust_score."""
        res = client.get(f"/matches?interest_id={self.badminton_id}&day_of_week=Saturday&locality=Indiranagar&limit=100", headers=self.h_me)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        matches = data["matches"]

        # Find Candidate A
        cand_a = next((m for m in matches if m["user_id"] == self.user_a["user_id"]), None)
        self.assertIsNotNone(cand_a)
        self.assertEqual(cand_a["trust_score"], 100)
        self.assertEqual(cand_a["reputation"]["average_rating"], 5.0)
        self.assertEqual(cand_a["reputation"]["total_reviews"], 1)
        self.assertTrue(any("★" in r for r in cand_a["match_reasons"]))

    def test_02_high_compatibility_no_reviews_still_eligible(self):
        """Test case 2: Candidate B (High compatibility + 0 reviews) is still eligible with neutral trust baseline."""
        res = client.get(f"/matches?interest_id={self.badminton_id}&day_of_week=Saturday&locality=Indiranagar&limit=100", headers=self.h_me)
        self.assertEqual(res.status_code, 200)
        matches = res.json()["matches"]

        cand_b = next((m for m in matches if m["user_id"] == self.user_b["user_id"]), None)
        self.assertIsNotNone(cand_b)
        self.assertEqual(cand_b["trust_score"], 75)
        self.assertEqual(cand_b["reputation"]["total_reviews"], 0)
        self.assertEqual(cand_b["reputation"]["average_rating"], 0.0)
        self.assertGreaterEqual(cand_b["match_score"], 60)

    def test_03_same_compatibility_better_reputation_ranked_higher(self):
        """Test case 3: Candidate A & B have same compatibility, but Candidate A (5.0 rating) ranks higher than Candidate B (0 reviews)."""
        res = client.get(f"/matches?interest_id={self.badminton_id}&day_of_week=Saturday&locality=Indiranagar&limit=100", headers=self.h_me)
        self.assertEqual(res.status_code, 200)
        matches = res.json()["matches"]

        cand_a = next((m for m in matches if m["user_id"] == self.user_a["user_id"]), None)
        cand_b = next((m for m in matches if m["user_id"] == self.user_b["user_id"]), None)
        self.assertIsNotNone(cand_a)
        self.assertIsNotNone(cand_b)

        idx_a = matches.index(cand_a)
        idx_b = matches.index(cand_b)
        self.assertLess(idx_a, idx_b, "Candidate A with higher reputation should be ranked before Candidate B")

    def test_04_reputation_cannot_dominate_compatibility(self):
        """Test case 4: Candidate B (high compatibility, 0 reviews) outranks Candidate C (low compatibility, 5.0 rating)."""
        res = client.get(f"/matches?interest_id={self.badminton_id}&day_of_week=Saturday&locality=Indiranagar&limit=100", headers=self.h_me)
        self.assertEqual(res.status_code, 200)
        matches = res.json()["matches"]

        cand_b = next((m for m in matches if m["user_id"] == self.user_b["user_id"]), None)
        cand_c = next((m for m in matches if m["user_id"] == self.user_c["user_id"]), None)

        self.assertIsNotNone(cand_b)
        # If cand_c is present, cand_b should have a higher match_score and appear earlier in ranking
        if cand_c:
            self.assertGreater(cand_b["match_score"], cand_c["match_score"])
            idx_b = matches.index(cand_b)
            idx_c = matches.index(cand_c)
            self.assertLess(idx_b, idx_c, "Higher compatibility candidate should outrank lower compatibility candidate regardless of reputation")


if __name__ == "__main__":
    unittest.main()
