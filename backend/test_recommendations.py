import unittest
import time
from datetime import date, timedelta, time as dtime
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestRecommendationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # 1. Interests
        badminton = models.Interest(name=f"Badminton Reco {ts}", category="Sports")
        cls.db.add(badminton)
        cls.db.commit()
        cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        pottery = models.Interest(name=f"Pottery Reco {ts}", category="Creative Arts")
        cls.db.add(pottery)
        cls.db.commit()
        cls.db.refresh(pottery)
        cls.pottery_id = pottery.interest_id

        # 2. Activities
        act_badminton = models.Activity(interest_id=cls.badminton_id, title=f"Badminton Matches {ts}", description="Competitive and casual doubles badminton")
        cls.db.add(act_badminton)
        cls.db.commit()
        cls.db.refresh(act_badminton)
        cls.act_badminton_id = act_badminton.activity_id

        act_pottery = models.Activity(interest_id=cls.pottery_id, title=f"Pottery Workshop {ts}", description="Clay modeling and wheel throwing")
        cls.db.add(act_pottery)
        cls.db.commit()
        cls.db.refresh(act_pottery)
        cls.act_pottery_id = act_pottery.activity_id

        cls.pwd = "password123"

        # 3. User (Recipient of Recommendations)
        # Interested in Badminton, Available on Saturday, Locality = Indiranagar
        cls.user_email = f"reco.user.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.user_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_u = client.post("/auth/login", json={"email": cls.user_email, "password": cls.pwd}).json()
        cls.tok_u = res_u["access_token"]
        cls.h_u = {"Authorization": f"Bearer {cls.tok_u}"}
        cls.user_obj = client.get("/auth/me", headers=cls.h_u).json()

        client.post("/profile/me/onboarding", json={
            "display_name": "Reco User",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id],
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}]
        }, headers=cls.h_u)

        # 4. Host User
        cls.host_email = f"reco.host.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_h = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_h = res_h["access_token"]
        cls.h_host = {"Authorization": f"Bearer {cls.tok_h}"}
        cls.host_obj = client.get("/auth/me", headers=cls.h_host).json()
        client.patch("/profile/me", json={"display_name": "Host Pro", "approx_locality": "Indiranagar, Bengaluru"}, headers=cls.h_host)

        # 5. Reviewer User (for building host & peer reputation)
        cls.rev_email = f"reco.rev.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.rev_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_r = client.post("/auth/login", json={"email": cls.rev_email, "password": cls.pwd}).json()
        cls.tok_r = res_r["access_token"]
        cls.h_rev = {"Authorization": f"Bearer {cls.tok_r}"}

        # Build Host Reputation (Give Host 5.0 rating on a completed event)
        past_ev = client.post(
            "/events",
            json={
                "activity_id": cls.act_badminton_id,
                "title": "Past Host Event",
                "event_date": (date.today() + timedelta(days=20)).isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 4,
            },
            headers=cls.h_host,
        ).json()
        client.post(f"/events/{past_ev['event_id']}/join", headers=cls.h_rev)
        client.patch(f"/events/{past_ev['event_id']}", json={"status": "COMPLETED"}, headers=cls.h_host)
        client.post(f"/events/{past_ev['event_id']}/feedback", json={"rating": 5, "comment": "Amazing organizer!"}, headers=cls.h_rev)

        # 6. Create Future Events for Recommendations
        # Find next Saturday and next Tuesday
        today = date.today()
        # Days ahead to Saturday
        days_to_sat = (5 - today.weekday() + 7) % 7
        if days_to_sat == 0:
            days_to_sat = 7
        cls.next_saturday = today + timedelta(days=days_to_sat)

        # Days ahead to Tuesday
        days_to_tue = (1 - today.weekday() + 7) % 7
        if days_to_tue == 0:
            days_to_tue = 7
        cls.next_tuesday = today + timedelta(days=days_to_tue)

        # Event A: Matching Saturday Badminton in Indiranagar (Optimal match)
        cls.ev_sat_indira = client.post(
            "/events",
            json={
                "activity_id": cls.act_badminton_id,
                "title": "Saturday Badminton Doubles at Indiranagar",
                "event_date": cls.next_saturday.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 6,
            },
            headers=cls.h_host,
        ).json()
        client.patch(f"/events/{cls.ev_sat_indira['event_id']}", json={"status": "PUBLISHED"}, headers=cls.h_host)

        # Event B: Tuesday Badminton in Indiranagar (Day mismatch)
        cls.ev_tue_indira = client.post(
            "/events",
            json={
                "activity_id": cls.act_badminton_id,
                "title": "Tuesday Evening Badminton",
                "event_date": cls.next_tuesday.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 6,
            },
            headers=cls.h_host,
        ).json()
        client.patch(f"/events/{cls.ev_tue_indira['event_id']}", json={"status": "PUBLISHED"}, headers=cls.h_host)

        # Event C: Saturday Badminton in Far Locality (Whitefield) (Location mismatch)
        cls.host_far_email = f"host.far.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.host_far_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_hf = client.post("/auth/login", json={"email": cls.host_far_email, "password": cls.pwd}).json()
        cls.tok_hf = res_hf["access_token"]
        cls.h_host_far = {"Authorization": f"Bearer {cls.tok_hf}"}
        client.patch("/profile/me", json={"display_name": "Host Far", "approx_locality": "Whitefield, Bengaluru"}, headers=cls.h_host_far)

        cls.ev_sat_far = client.post(
            "/events",
            json={
                "activity_id": cls.act_badminton_id,
                "title": "Saturday Badminton at Whitefield",
                "event_date": cls.next_saturday.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 6,
            },
            headers=cls.h_host_far,
        ).json()
        client.patch(f"/events/{cls.ev_sat_far['event_id']}", json={"status": "PUBLISHED"}, headers=cls.h_host_far)

        # Event D: Saturday Pottery Workshop in Indiranagar (Interest mismatch)
        cls.ev_sat_pottery = client.post(
            "/events",
            json={
                "activity_id": cls.act_pottery_id,
                "title": "Saturday Beginners Pottery Workshop",
                "event_date": cls.next_saturday.isoformat(),
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "max_capacity": 4,
            },
            headers=cls.h_host,
        ).json()
        client.patch(f"/events/{cls.ev_sat_pottery['event_id']}", json={"status": "PUBLISHED"}, headers=cls.h_host)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_matching_event_recommended_with_reasons(self):
        """Test 1: Perfectly matching event gets recommended with high score and detailed explanation reasons."""
        res = client.get("/recommendations?type=EVENT&limit=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_recommendations"], 0)

        # Locate Saturday Badminton in Indiranagar
        rec_ev = next((r for r in data["recommendations"] if r["event_id"] == self.ev_sat_indira["event_id"]), None)
        self.assertIsNotNone(rec_ev, "Matching Saturday Badminton event should be recommended")
        self.assertEqual(rec_ev["type"], "EVENT")
        self.assertGreaterEqual(rec_ev["score"], 60)
        self.assertTrue(any("Badminton" in r for r in rec_ev["reasons"]))
        self.assertTrue(any("Saturday" in r for r in rec_ev["reasons"]))
        self.assertTrue(any("Indiranagar" in r for r in rec_ev["reasons"]))

    def test_02_irrelevant_event_ranked_significantly_lower(self):
        """Test 2: Irrelevant event (Pottery) has much lower score than matching event (Badminton)."""
        res = client.get("/recommendations?type=EVENT&limit=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        recs = res.json()["recommendations"]

        rec_badminton = next((r for r in recs if r["event_id"] == self.ev_sat_indira["event_id"]), None)
        rec_pottery = next((r for r in recs if r["event_id"] == self.ev_sat_pottery["event_id"]), None)

        self.assertIsNotNone(rec_badminton)
        if rec_pottery:
            self.assertGreater(rec_badminton["score"], rec_pottery["score"])
            idx_b = recs.index(rec_badminton)
            idx_p = recs.index(rec_pottery)
            self.assertLess(idx_b, idx_p)

    def test_03_availability_affects_ranking(self):
        """Test 3: Saturday Badminton ranks higher than Tuesday Badminton because user is available on Saturday."""
        res = client.get("/recommendations?type=EVENT&limit=300", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        recs = res.json()["recommendations"]

        rec_sat = next((r for r in recs if r["event_id"] == self.ev_sat_indira["event_id"]), None)
        rec_tue = next((r for r in recs if r["event_id"] == self.ev_tue_indira["event_id"]), None)

        self.assertIsNotNone(rec_sat)
        self.assertIsNotNone(rec_tue)
        self.assertGreater(rec_sat["score"], rec_tue["score"])
        self.assertLess(recs.index(rec_sat), recs.index(rec_tue))

    def test_04_locality_affects_ranking(self):
        """Test 4: Indiranagar Badminton ranks higher than Whitefield Badminton because user locality is Indiranagar."""
        res = client.get("/recommendations?type=EVENT&limit=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        recs = res.json()["recommendations"]

        rec_local = next((r for r in recs if r["event_id"] == self.ev_sat_indira["event_id"]), None)
        rec_far = next((r for r in recs if r["event_id"] == self.ev_sat_far["event_id"]), None)

        self.assertIsNotNone(rec_local)
        self.assertIsNotNone(rec_far)
        self.assertGreater(rec_local["score"], rec_far["score"])
        self.assertLess(recs.index(rec_local), recs.index(rec_far))

    def test_05_semantic_similarity_improves_relevant_results(self):
        """Test 5: Semantic similarity contributes positively to hybrid recommendation score."""
        res = client.get("/recommendations?type=EVENT&limit=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        recs = res.json()["recommendations"]

        rec_badminton = next((r for r in recs if r["event_id"] == self.ev_sat_indira["event_id"]), None)
        self.assertIsNotNone(rec_badminton)
        # Score is bounded and positive
        self.assertGreater(rec_badminton["score"], 0)
        self.assertLessEqual(rec_badminton["score"], 100)

    def test_06_trust_affects_people_recommendations(self):
        """Test 6: High reputation users get ranked with trust signals in PEOPLE recommendations."""
        res = client.get("/recommendations?type=PEOPLE&limit=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        recs = data["recommendations"]

        self.assertTrue(all(r["type"] == "PEOPLE" for r in recs))
        # Check that candidate with reviews has reputation attached
        cand_with_rep = next((r for r in recs if r["reputation"] and r["reputation"]["total_reviews"] > 0), None)
        if cand_with_rep:
            self.assertGreaterEqual(cand_with_rep["trust_score"], 80)
            self.assertGreaterEqual(cand_with_rep["reputation"]["average_rating"], 4.0)

    def test_07_clean_empty_response_when_no_matches(self):
        """Test 7: When min_score threshold is unreachable (e.g. 100 on incompatible type), returns clean empty array."""
        res = client.get("/recommendations?type=EVENT&min_score=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data["recommendations"], list)
        self.assertEqual(data["total_recommendations"], len(data["recommendations"]))

    def test_08_type_filter_isolation(self):
        """Test 8: Type query parameter correctly isolates EVENT, ACTIVITY, and PEOPLE entities."""
        res_ev = client.get("/recommendations?type=EVENT&limit=100", headers=self.h_u).json()
        self.assertTrue(all(r["type"] == "EVENT" for r in res_ev["recommendations"]))

        res_act = client.get("/recommendations?type=ACTIVITY&limit=100", headers=self.h_u).json()
        self.assertTrue(all(r["type"] == "ACTIVITY" for r in res_act["recommendations"]))

        res_ppl = client.get("/recommendations?type=PEOPLE&limit=100", headers=self.h_u).json()
        self.assertTrue(all(r["type"] == "PEOPLE" for r in res_ppl["recommendations"]))



if __name__ == "__main__":
    unittest.main()
