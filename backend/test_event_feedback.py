import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestEventFeedback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        # Interest setup
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        cls.pwd = "password123"

        # 1. Setup Host (Pooja)
        cls.host_email = "pooja.feedbackhost@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_host = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_host = res_host["access_token"]
        cls.h_host = {"Authorization": f"Bearer {cls.tok_host}"}
        cls.user_host = client.get("/auth/me", headers=cls.h_host).json()
        client.patch("/profile/me", json={"display_name": "Pooja Hegde", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_host)

        # 2. Setup Participant 2 (Rahul)
        cls.p2_email = "rahul.feedbackp2@vynk.com"
        client.post("/auth/register", json={"email": cls.p2_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p2 = client.post("/auth/login", json={"email": cls.p2_email, "password": cls.pwd}).json()
        cls.tok_p2 = res_p2["access_token"]
        cls.h_p2 = {"Authorization": f"Bearer {cls.tok_p2}"}
        cls.user_p2 = client.get("/auth/me", headers=cls.h_p2).json()
        client.patch("/profile/me", json={"display_name": "Rahul Sharma", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_p2)

        # 3. Setup Outsider (Sneha)
        cls.outsider_email = "sneha.feedbackout@vynk.com"
        client.post("/auth/register", json={"email": cls.outsider_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_out = client.post("/auth/login", json={"email": cls.outsider_email, "password": cls.pwd}).json()
        cls.tok_out = res_out["access_token"]
        cls.h_out = {"Authorization": f"Bearer {cls.tok_out}"}
        cls.user_out = client.get("/auth/me", headers=cls.h_out).json()

        # Activity
        act = client.post(
            "/activities",
            json={
                "interest_id": cls.badminton_id,
                "title": "Badminton Feedback Match",
                "description": "Activity for feedback validation",
            },
            headers=cls.h_host,
        ).json()
        cls.activity_id = act["activity_id"]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_completed_event_feedback_success(self):
        """Test happy path: Event is completed -> participants submit rating & comment -> retrieved via GET."""
        event_date = date.today() + timedelta(days=30)

        # 1. Host creates event
        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Completed Badminton Showdown",
                "event_date": event_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        # 2. Rahul joins
        client.post(f"/events/{event_id}/join", headers=self.h_p2)

        # 3. Mark event as COMPLETED
        client.patch(f"/events/{event_id}", json={"status": "COMPLETED"}, headers=self.h_host)

        # 4. Rahul submits feedback
        res_fb_p2 = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 5, "comment": "Amazing game! Great court and competitive doubles."},
            headers=self.h_p2,
        )
        self.assertEqual(res_fb_p2.status_code, 201)
        fb_p2 = res_fb_p2.json()
        self.assertEqual(fb_p2["rating"], 5)
        self.assertEqual(fb_p2["reviewer_name"], "Rahul Sharma")
        self.assertEqual(fb_p2["comment"], "Amazing game! Great court and competitive doubles.")

        # 5. Host (Pooja) also submits feedback
        res_fb_host = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 4, "comment": "Great teamwork and prompt arrival."},
            headers=self.h_host,
        )
        self.assertEqual(res_fb_host.status_code, 201)
        fb_host = res_fb_host.json()
        self.assertEqual(fb_host["rating"], 4)
        self.assertEqual(fb_host["reviewer_name"], "Pooja Hegde")

        # 6. Retrieve all feedback for event
        all_fb = client.get(f"/events/{event_id}/feedback").json()
        self.assertEqual(len(all_fb), 2)
        ratings = [f["rating"] for f in all_fb]
        self.assertIn(5, ratings)
        self.assertIn(4, ratings)

    def test_02_non_participant_blocked(self):
        """Test that non-participants / outsiders cannot submit feedback (403)."""
        event_date = date.today() + timedelta(days=31)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Private Match",
                "event_date": event_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.patch(f"/events/{event_id}", json={"status": "COMPLETED"}, headers=self.h_host)

        # Outsider (Sneha) attempts feedback
        res = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 5, "comment": "I was never invited"},
            headers=self.h_out,
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("participant", res.json()["detail"].lower())

    def test_03_event_not_completed_blocked(self):
        """Test that feedback cannot be submitted on an active/ongoing event before completion (400)."""
        event_date = date.today() + timedelta(days=32)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Future Ongoing Match",
                "event_date": event_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        # Status is PUBLISHED (not COMPLETED)
        res = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 5, "comment": "Game hasn't happened yet"},
            headers=self.h_host,
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("COMPLETED", res.json()["detail"])

    def test_04_duplicate_feedback_blocked(self):
        """Test that a participant cannot submit feedback more than once for the same event (400)."""
        event_date = date.today() + timedelta(days=33)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Duplicate Feedback Match",
                "event_date": event_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.patch(f"/events/{event_id}", json={"status": "COMPLETED"}, headers=self.h_host)

        # First feedback succeeds
        res1 = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 5, "comment": "First review"},
            headers=self.h_host,
        )
        self.assertEqual(res1.status_code, 201)

        # Second feedback fails
        res2 = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 4, "comment": "Second review attempt"},
            headers=self.h_host,
        )
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already submitted feedback", res2.json()["detail"])

    def test_05_invalid_rating_rejected(self):
        """Test that ratings outside the 1-5 range are rejected (422)."""
        event_date = date.today() + timedelta(days=34)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Rating Validation Match",
                "event_date": event_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.patch(f"/events/{event_id}", json={"status": "COMPLETED"}, headers=self.h_host)

        # Rating 0 (too low)
        res_zero = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 0, "comment": "Too low"},
            headers=self.h_host,
        )
        self.assertEqual(res_zero.status_code, 422)

        # Rating 6 (too high)
        res_high = client.post(
            f"/events/{event_id}/feedback",
            json={"rating": 6, "comment": "Too high"},
            headers=self.h_host,
        )
        self.assertEqual(res_high.status_code, 422)


if __name__ == "__main__":
    unittest.main()
