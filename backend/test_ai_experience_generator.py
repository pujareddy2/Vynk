import unittest
import time
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestAIExperienceGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # 1. Interests
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        # 2. Activity
        act = cls.db.query(models.Activity).filter(models.Activity.title == "Badminton Doubles League").first()
        if not act:
            act = models.Activity(interest_id=cls.badminton_id, title="Badminton Doubles League", description="Fast doubles sets")
            cls.db.add(act)
            cls.db.commit()
            cls.db.refresh(act)
        cls.activity_id = act.activity_id

        cls.pwd = "password123"

        # 3. User (Initiator)
        cls.user_email = f"exp.user.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.user_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_u = client.post("/auth/login", json={"email": cls.user_email, "password": cls.pwd}).json()
        cls.tok_u = res_u["access_token"]
        cls.h_u = {"Authorization": f"Bearer {cls.tok_u}"}

        client.post("/profile/me/onboarding", json={
            "display_name": "Experience Initiator",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id],
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}]
        }, headers=cls.h_u)

        # 4. Peer Candidate (To ensure verified candidate exists)
        cls.peer_email = f"exp.peer.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.peer_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p = client.post("/auth/login", json={"email": cls.peer_email, "password": cls.pwd}).json()
        cls.tok_p = res_p["access_token"]
        cls.h_p = {"Authorization": f"Bearer {cls.tok_p}"}

        client.post("/profile/me/onboarding", json={
            "display_name": "Badminton Champion Peer",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id],
            "skills": [],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "20:00:00"}]
        }, headers=cls.h_p)

        # 5. Verified Venue & Slot
        cls.venue_email = f"exp.venue.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.venue_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_v = client.post("/auth/login", json={"email": cls.venue_email, "password": cls.pwd}).json()
        cls.tok_v = res_v["access_token"]
        cls.h_v = {"Authorization": f"Bearer {cls.tok_v}"}

        v_res = client.post("/venues", json={
            "name": "Indiranagar Smash Arena",
            "address": "12th Main Road, Indiranagar",
            "locality": "Indiranagar, Bengaluru",
            "activity_ids": [cls.activity_id]
        }, headers=cls.h_v).json()
        cls.venue_id = v_res["venue_id"]

        next_sat = date.today() + timedelta(days=((5 - date.today().weekday() + 7) % 7 or 7))
        cls.slot_date_iso = next_sat.isoformat()

        slot_res = client.post(f"/venues/{cls.venue_id}/slots", json={
            "slot_date": cls.slot_date_iso,
            "start_time": "18:00:00",
            "end_time": "20:00:00",
            "price_total": 1200.0,
            "currency": "INR"
        }, headers=cls.h_v).json()
        cls.slot_id = slot_res["slot_id"]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_generate_experience_plan_from_natural_language_query(self):
        """Test 1: Generate structured experience plan from query 'Play badminton with 4 people Saturday evening in Indiranagar'."""
        res = client.post(
            "/ai/experiences/generate",
            json={"query": "Play badminton with 4 people Saturday evening in Indiranagar"},
            headers=self.h_u,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check required structured schema keys
        self.assertIn("experience_title", data)
        self.assertIn("tagline", data)
        self.assertIn("badminton", data["activity_name"].lower())
        self.assertEqual(data["target_size"], 4)
        self.assertIn("Indiranagar", data["locality"])

        # Check rich plan components
        self.assertGreaterEqual(len(data["why_this_works"]), 2)
        self.assertGreaterEqual(len(data["agenda"]), 2)
        self.assertGreaterEqual(len(data["preparation_checklist"]), 2)
        self.assertIn("action_type", data)
        self.assertEqual(data["action_type"], "CREATE_PROPOSAL")
        self.assertIn("activity_id", data["action_payload"])

    def test_02_explicit_parameter_overrides_respected(self):
        """Test 2: Explicit parameter overrides (activity_id, venue_id, slot_id, target_size) are strictly honored."""
        res = client.post(
            "/ai/experiences/generate",
            json={
                "query": "General evening sports meetup",
                "activity_id": self.activity_id,
                "venue_id": self.venue_id,
                "slot_id": self.slot_id,
                "target_size": 2,
            },
            headers=self.h_u,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["activity_id"], self.activity_id)
        self.assertEqual(data["venue_id"], self.venue_id)
        self.assertEqual(data["slot_id"], self.slot_id)
        self.assertEqual(data["target_size"], 2)
        self.assertEqual(data["per_person_cost"], 600.0)  # 1200 / 2

    def test_03_action_payload_can_directly_trigger_group_proposal(self):
        """Test 3: Generated action_payload is directly compatible with POST /ai/groups/propose."""
        res_exp = client.post(
            "/ai/experiences/generate",
            json={"query": "Play badminton with 4 people Saturday evening in Indiranagar"},
            headers=self.h_u,
        ).json()

        payload = res_exp["action_payload"]
        res_prop = client.post("/ai/groups/propose", json=payload, headers=self.h_u)
        self.assertEqual(res_prop.status_code, 201)
        prop_data = res_prop.json()
        self.assertEqual(prop_data["target_size"], payload["target_size"])
        self.assertEqual(prop_data["activity_id"], payload["activity_id"])


if __name__ == "__main__":
    unittest.main()
