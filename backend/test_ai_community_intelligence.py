import time
import unittest
from datetime import date, time as dt_time
from fastapi.testclient import TestClient

from database import SessionLocal
import models
from main import app

client = TestClient(app)


class TestAICommunityIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = client
        cls.db = SessionLocal()
        cls.ts = int(time.time() * 1000)
        cls.pwd = "password123"

        # 1. Create unique test interest
        cls.interest_name = f"Badminton_Comm_{cls.ts}"
        cls.interest = models.Interest(name=cls.interest_name, category="Sports")
        cls.db.add(cls.interest)
        cls.db.commit()
        cls.db.refresh(cls.interest)

        # 2. Register & authenticate primary user
        cls.user_email = f"lead_comm_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": cls.user_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_login = cls.client.post("/auth/login", json={"email": cls.user_email, "password": cls.pwd}).json()
        cls.token = res_login["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

        cls.user = cls.db.query(models.User).filter(models.User.email == cls.user_email).first()
        cls.user_profile = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.user.user_id).first()
        cls.user_profile.display_name = "Rahul Captain"
        cls.user_profile.approx_locality = "Indiranagar, Bengaluru"

        cls.db.add(models.UserInterest(user_id=cls.user.user_id, interest_id=cls.interest.interest_id))
        cls.db.add(
            models.UserAvailability(
                user_id=cls.user.user_id,
                day_of_week="Saturday",
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
            )
        )
        cls.db.commit()

        # 3. Create 5 cohort peers in same locality & interest
        cls.peer_ids = []
        for i in range(5):
            peer_email = f"peer_{i}_{cls.ts}@test.com"
            cls.client.post("/auth/register", json={"email": peer_email, "password": cls.pwd, "confirm_password": cls.pwd})
            peer = cls.db.query(models.User).filter(models.User.email == peer_email).first()
            cls.peer_ids.append(peer.user_id)

            prof = cls.db.query(models.Profile).filter(models.Profile.user_id == peer.user_id).first()
            prof.display_name = f"Peer Player {i}"
            prof.approx_locality = "Indiranagar, Bengaluru"

            cls.db.add(models.UserInterest(user_id=peer.user_id, interest_id=cls.interest.interest_id))
            cls.db.add(
                models.UserAvailability(
                    user_id=peer.user_id,
                    day_of_week="Saturday",
                    start_time=dt_time(18, 0),
                    end_time=dt_time(20, 0),
                )
            )
        cls.db.commit()

        # 4. Create an activity and simulated past event with repeated participations
        cls.activity = models.Activity(
            title=f"Weekend {cls.interest_name} Meet",
            interest_id=cls.interest.interest_id,
            created_by=cls.user.user_id,
        )
        cls.db.add(cls.activity)
        cls.db.commit()
        cls.db.refresh(cls.activity)

        cls.past_event = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.user.user_id,
            title="Past Indiranagar Badminton Session",
            event_date=date(2026, 10, 3),
            start_time=dt_time(18, 0),
            end_time=dt_time(20, 0),
            max_capacity=8,
            status="COMPLETED",
        )
        cls.db.add(cls.past_event)
        cls.db.commit()
        cls.db.refresh(cls.past_event)

        # Enroll peers in past event to test repeated participation signals
        for pid in cls.peer_ids[:3]:
            cls.db.add(
                models.EventParticipant(
                    event_id=cls.past_event.event_id,
                    user_id=pid,
                    status="CONFIRMED",
                )
            )
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_detect_community_proposals_create_action(self):
        """Verify recurring group pattern detection proposes a community with CREATE_COMMUNITY action."""
        response = self.client.get(
            f"/ai/community-intelligence?locality=Indiranagar&activity={self.interest_name}&day=Saturday",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()

        self.assertGreaterEqual(data["total_proposals"], 1)
        prop = next((p for p in data["proposals"] if p["activity"] == self.interest_name), None)
        self.assertIsNotNone(prop, "Expected proposal for created interest")

        self.assertEqual(prop["community_type"], "SPORTS")
        self.assertEqual(prop["locality"], "Indiranagar")
        self.assertEqual(prop["day_of_week"], "Saturday")
        self.assertIn("Saturday", prop["recurring_pattern"])
        self.assertGreaterEqual(prop["member_candidates"], 4)
        self.assertGreaterEqual(prop["compatibility_score"], 80)
        self.assertGreaterEqual(prop["community_opportunity_score"], 80)
        self.assertEqual(prop["suggested_action"], "CREATE_COMMUNITY")
        self.assertIsNone(prop["existing_community_id"])

        # Check action_payload readiness
        self.assertIsNotNone(prop["action_payload"])
        self.assertIn(self.interest_name, prop["action_payload"]["name"])
        self.assertIn("initial_member_ids", prop["action_payload"])
        self.assertGreaterEqual(len(prop["action_payload"]["initial_member_ids"]), 4)

        # Verify reasons include cohesion factors
        reasons_text = " ".join(prop["reasons"])
        self.assertIn("Indiranagar", reasons_text)
        self.assertIn("compatibility", reasons_text.lower())

    def test_existing_community_triggers_join_action(self):
        """Verify that when a community already exists in database, suggested_action pivots to JOIN_COMMUNITY."""
        comm_name = f"Indiranagar Weekend {self.interest_name}"
        create_res = self.client.post(
            "/communities",
            json={"name": comm_name, "description": "Existing established badminton circle"},
            headers=self.headers,
        )
        self.assertEqual(create_res.status_code, 201, create_res.text)
        comm_id = create_res.json()["community_id"]

        # Call community intelligence
        response = self.client.get(
            f"/ai/community-proposals?locality=Indiranagar&activity={self.interest_name}&day=Saturday",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        prop = next((p for p in data["proposals"] if p["activity"] == self.interest_name), None)
        self.assertIsNotNone(prop)
        self.assertEqual(prop["suggested_action"], "JOIN_COMMUNITY")
        self.assertEqual(prop["existing_community_id"], comm_id)

    def test_execute_community_creation_with_seeded_members(self):
        """Verify that the suggested action_payload can be executed against POST /communities to form the circle."""
        new_comm_name = f"Circle_{self.ts}_Actionable"
        payload = {
            "name": new_comm_name,
            "description": f"Created from AI community proposal for {self.interest_name}",
            "initial_member_ids": self.peer_ids[:3],
        }

        res = self.client.post("/communities", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201, res.text)
        comm_data = res.json()

        self.assertEqual(comm_data["name"], new_comm_name)
        self.assertEqual(comm_data["created_by"], self.user.user_id)
        # 1 Admin creator + 3 seeded peers = 4 members
        self.assertEqual(comm_data["member_count"], 4)

    def test_community_intelligence_filters_and_auth(self):
        """Verify token authentication, nonexistent locality filtering, and score thresholds."""
        # 1. Unauthenticated request blocked
        unauth_res = self.client.get("/ai/community-intelligence")
        self.assertEqual(unauth_res.status_code, 401)

        # 2. Non-existent locality yields 0 results
        empty_res = self.client.get(
            "/ai/community-intelligence?locality=NonExistentHimalayanValley999",
            headers=self.headers,
        )
        self.assertEqual(empty_res.status_code, 200)
        self.assertEqual(empty_res.json()["total_proposals"], 0)

        # 3. High min_opportunity_score threshold filters out lower scores
        high_thresh_res = self.client.get(
            f"/ai/community-intelligence?locality=Indiranagar&min_opportunity_score=100",
            headers=self.headers,
        )
        self.assertEqual(high_thresh_res.status_code, 200)
        for p in high_thresh_res.json()["proposals"]:
            self.assertGreaterEqual(p["community_opportunity_score"], 100)


if __name__ == "__main__":
    unittest.main()
