import unittest
import time
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestUserReputation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)
        # Interest setup
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        cls.pwd = "password123"

        # 1. Target User (Rahul)
        cls.target_email = f"rahul.rep.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.target_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_target = client.post("/auth/login", json={"email": cls.target_email, "password": cls.pwd}).json()
        cls.tok_target = res_target["access_token"]
        cls.h_target = {"Authorization": f"Bearer {cls.tok_target}"}
        cls.user_target = client.get("/auth/me", headers=cls.h_target).json()
        client.patch("/profile/me", json={"display_name": "Rahul Reputation", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_target)

        # 2. Peer User 1 (Pooja)
        cls.peer1_email = f"pooja.rep.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.peer1_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p1 = client.post("/auth/login", json={"email": cls.peer1_email, "password": cls.pwd}).json()
        cls.tok_p1 = res_p1["access_token"]
        cls.h_p1 = {"Authorization": f"Bearer {cls.tok_p1}"}
        cls.user_p1 = client.get("/auth/me", headers=cls.h_p1).json()

        # 3. Peer User 2 (Amit)
        cls.peer2_email = f"amit.rep.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.peer2_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p2 = client.post("/auth/login", json={"email": cls.peer2_email, "password": cls.pwd}).json()
        cls.tok_p2 = res_p2["access_token"]
        cls.h_p2 = {"Authorization": f"Bearer {cls.tok_p2}"}
        cls.user_p2 = client.get("/auth/me", headers=cls.h_p2).json()

        # 4. Fresh User with No Events (Fresh User)
        cls.fresh_email = f"fresh.rep.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.fresh_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_fresh = client.post("/auth/login", json={"email": cls.fresh_email, "password": cls.pwd}).json()
        cls.tok_fresh = res_fresh["access_token"]
        cls.h_fresh = {"Authorization": f"Bearer {cls.tok_fresh}"}
        cls.user_fresh = client.get("/auth/me", headers=cls.h_fresh).json()

        # Activity
        act = client.post(
            "/activities",
            json={
                "interest_id": cls.badminton_id,
                "title": "Reputation Test Activity",
                "description": "Activity for reputation calculation tests",
            },
            headers=cls.h_target,
        ).json()
        cls.activity_id = act["activity_id"]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_user_with_no_feedback_empty_reputation(self):
        """Test case 2: Fresh user with no feedback returns empty/zero reputation."""
        res = client.get(f"/users/{self.user_fresh['user_id']}/reputation")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["average_rating"], 0.0)
        self.assertEqual(data["total_reviews"], 0)
        self.assertEqual(data["feedback_count"], 0)
        self.assertEqual(data["five_star_count"], 0)
        self.assertEqual(data["four_star_count"], 0)
        self.assertEqual(data["three_star_count"], 0)
        self.assertEqual(data["two_star_count"], 0)
        self.assertEqual(data["one_star_count"], 0)
        self.assertEqual(data["completed_events"], 0)

    def test_02_user_with_feedback_and_completed_events(self):
        """Test cases 1, 3 & 4: User with multiple reviews and completed events gets accurate reputation calculation."""
        ev_date1 = date.today() + timedelta(days=40)
        ev_date2 = date.today() + timedelta(days=41)

        # Event 1 (Rahul hosts, Pooja & Amit join)
        ev1 = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Reputation Event 1",
                "event_date": ev_date1.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 3,
            },
            headers=self.h_target,
        ).json()
        ev1_id = ev1["event_id"]

        client.post(f"/events/{ev1_id}/join", headers=self.h_p1)
        client.post(f"/events/{ev1_id}/join", headers=self.h_p2)

        # Complete Event 1
        client.patch(f"/events/{ev1_id}", json={"status": "COMPLETED"}, headers=self.h_target)

        # Peer 1 gives 5 stars, Peer 2 gives 4 stars
        client.post(f"/events/{ev1_id}/feedback", json={"rating": 5, "comment": "Great host!"}, headers=self.h_p1)
        client.post(f"/events/{ev1_id}/feedback", json={"rating": 4, "comment": "Solid game"}, headers=self.h_p2)

        # Event 2 (Pooja hosts, Rahul joins)
        ev2 = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Reputation Event 2",
                "event_date": ev_date2.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=self.h_p1,
        ).json()
        ev2_id = ev2["event_id"]

        client.post(f"/events/{ev2_id}/join", headers=self.h_target)

        # Complete Event 2
        client.patch(f"/events/{ev2_id}", json={"status": "COMPLETED"}, headers=self.h_p1)

        # Pooja gives 4 stars on Event 2
        client.post(f"/events/{ev2_id}/feedback", json={"rating": 4, "comment": "Fun match"}, headers=self.h_p1)

        # Now check Rahul's reputation:
        # Reviews received from peers: 5 (Event 1 Pooja), 4 (Event 1 Amit), 4 (Event 2 Pooja) -> Total = 3 reviews
        # Average rating: (5 + 4 + 4) / 3 = 13 / 3 = 4.33
        # 5-star count: 1, 4-star count: 2
        # Completed events: 2 (Event 1 + Event 2)
        res = client.get(f"/users/{self.user_target['user_id']}/reputation")
        self.assertEqual(res.status_code, 200)
        rep = res.json()

        self.assertEqual(rep["user_id"], self.user_target["user_id"])
        self.assertEqual(rep["display_name"], "Rahul Reputation")
        self.assertEqual(rep["total_reviews"], 3)
        self.assertEqual(rep["average_rating"], 4.33)
        self.assertEqual(rep["five_star_count"], 1)
        self.assertEqual(rep["four_star_count"], 2)
        self.assertEqual(rep["three_star_count"], 0)
        self.assertEqual(rep["completed_events"], 2)

    def test_03_get_my_reputation_endpoint(self):
        """Test authenticated GET /users/me/reputation."""
        res = client.get("/users/me/reputation", headers=self.h_target)
        self.assertEqual(res.status_code, 200)
        rep = res.json()
        self.assertEqual(rep["user_id"], self.user_target["user_id"])
        self.assertEqual(rep["total_reviews"], 3)

    def test_04_non_existent_user_reputation_404(self):
        """Test case 5: Querying reputation for non-existent user returns 404."""
        res = client.get("/users/999999/reputation")
        self.assertEqual(res.status_code, 404)
        self.assertIn("User not found", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()
