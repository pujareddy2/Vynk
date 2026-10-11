import unittest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestPaymentCollection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        # Ensure badminton interest exists
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        # 1. Setup Host (Pooja)
        cls.host_email = "pooja.payhost@vynk.com"
        cls.pwd = "password123"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_host = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_host = res_host["access_token"]
        cls.h_host = {"Authorization": f"Bearer {cls.tok_host}"}
        cls.user_host = client.get("/auth/me", headers=cls.h_host).json()
        client.put("/profiles/me", json={"display_name": "Pooja Hegde", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_host)

        # 2. Setup Participant 2 (Rahul)
        cls.p2_email = "rahul.payp2@vynk.com"
        client.post("/auth/register", json={"email": cls.p2_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p2 = client.post("/auth/login", json={"email": cls.p2_email, "password": cls.pwd}).json()
        cls.tok_p2 = res_p2["access_token"]
        cls.h_p2 = {"Authorization": f"Bearer {cls.tok_p2}"}
        cls.user_p2 = client.get("/auth/me", headers=cls.h_p2).json()
        client.put("/profiles/me", json={"display_name": "Rahul Sharma", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_p2)

        # 3. Setup Participant 3 (Amit)
        cls.p3_email = "amit.payp3@vynk.com"
        client.post("/auth/register", json={"email": cls.p3_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p3 = client.post("/auth/login", json={"email": cls.p3_email, "password": cls.pwd}).json()
        cls.tok_p3 = res_p3["access_token"]
        cls.h_p3 = {"Authorization": f"Bearer {cls.tok_p3}"}
        cls.user_p3 = client.get("/auth/me", headers=cls.h_p3).json()
        client.put("/profiles/me", json={"display_name": "Amit Kumar", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_p3)

        # 4. Setup Outsider (Sneha)
        cls.outsider_email = "sneha.outsider@vynk.com"
        client.post("/auth/register", json={"email": cls.outsider_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_out = client.post("/auth/login", json={"email": cls.outsider_email, "password": cls.pwd}).json()
        cls.tok_out = res_out["access_token"]
        cls.h_out = {"Authorization": f"Bearer {cls.tok_out}"}

        # Activity & Venue setup
        act = client.post(
            "/activities",
            json={
                "interest_id": cls.badminton_id,
                "title": "Badminton Split Payment Tournament",
                "description": "3-player badminton practice session",
            },
            headers=cls.h_host,
        ).json()
        cls.activity_id = act["activity_id"]

        venue = client.post(
            "/venues",
            json={
                "name": "Smash & Groove Pay Arena",
                "description": "Indoor synthetic badminton arena",
                "address": "100 Feet Road, Indiranagar",
                "locality": "Indiranagar, Bengaluru",
                "activity_ids": [cls.activity_id],
            },
            headers=cls.h_host,
        ).json()
        cls.venue_id = venue["venue_id"]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_target_split_payment_collection_journey(self):
        """
        Target test flow:
        ₹1,200 booking with 3 participants (Host, Rahul, Amit) -> ₹400 each
        Participant 1 pays -> ₹400 collected
        Participant 2 pays -> ₹800 collected
        Participant 3 pays -> ₹1,200 collected -> FULLY PAID
        """
        booking_date = date.today() + timedelta(days=4)

        # 1. Create Slot (₹1,200 total)
        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "price_total": 1200.0,
                "currency": "INR",
            },
            headers=self.h_host,
        ).json()
        slot_id = slot["slot_id"]

        # 2. Create Event (Capacity = 3)
        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Saturday Badminton 3-Way Split Match",
                "event_date": booking_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 3,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        # 3. Rahul (P2) and Amit (P3) join the event
        client.post(f"/events/{event_id}/join", headers=self.h_p2)
        client.post(f"/events/{event_id}/join", headers=self.h_p3)

        # 4. Host books the venue slot (₹1,200 total)
        booked_ev = client.post(
            f"/events/{event_id}/venue-book",
            json={"slot_id": slot_id},
            headers=self.h_host,
        ).json()

        self.assertEqual(booked_ev["participant_count"], 3)
        self.assertEqual(booked_ev["per_person_cost"], 400.0)
        self.assertEqual(booked_ev["venue_booking"]["total_amount"], 1200.0)
        self.assertEqual(booked_ev["venue_booking"]["amount_collected"], 0.0)

        # Verify initial payment statuses: all 3 UNPAID
        for p in booked_ev["participants"]:
            self.assertEqual(p["payment_status"], "UNPAID")
            self.assertEqual(p["paid_amount"], 0.0)

        # 5. Participant 1 (Host - Pooja) pays exact split share (₹400)
        pay1 = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)
        self.assertEqual(pay1.status_code, 200)
        self.assertEqual(pay1.json()["amount"], 400.0)
        self.assertEqual(pay1.json()["status"], "SUCCESS")

        ev_state_1 = client.get(f"/events/{event_id}", headers=self.h_host).json()
        self.assertEqual(ev_state_1["venue_booking"]["amount_collected"], 400.0)
        p1_roster = next(p for p in ev_state_1["participants"] if p["user_id"] == self.user_host["user_id"])
        self.assertEqual(p1_roster["payment_status"], "PAID")
        self.assertEqual(p1_roster["paid_amount"], 400.0)

        # 6. Participant 2 (Rahul) pays exact split share (₹400)
        pay2 = client.post(f"/events/{event_id}/pay", json={"amount": 400.0}, headers=self.h_p2)
        self.assertEqual(pay2.status_code, 200)
        self.assertEqual(pay2.json()["amount"], 400.0)
        self.assertEqual(pay2.json()["status"], "SUCCESS")

        ev_state_2 = client.get(f"/events/{event_id}", headers=self.h_host).json()
        self.assertEqual(ev_state_2["venue_booking"]["amount_collected"], 800.0)
        p2_roster = next(p for p in ev_state_2["participants"] if p["user_id"] == self.user_p2["user_id"])
        self.assertEqual(p2_roster["payment_status"], "PAID")
        self.assertEqual(p2_roster["paid_amount"], 400.0)

        # 7. Participant 3 (Amit) pays remaining share (₹400) -> FULLY COLLECTED (₹1,200)
        pay3 = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_p3)
        self.assertEqual(pay3.status_code, 200)
        self.assertEqual(pay3.json()["amount"], 400.0)
        self.assertEqual(pay3.json()["status"], "SUCCESS")

        ev_state_3 = client.get(f"/events/{event_id}", headers=self.h_host).json()
        self.assertEqual(ev_state_3["venue_booking"]["amount_collected"], 1200.0)
        self.assertEqual(ev_state_3["venue_booking"]["status"], "CONFIRMED")
        for p in ev_state_3["participants"]:
            self.assertEqual(p["payment_status"], "PAID")
            self.assertEqual(p["paid_amount"], 400.0)

    def test_02_duplicate_payment_rejected(self):
        """Test that a participant who already fully paid cannot pay again (400)."""
        booking_date = date.today() + timedelta(days=12)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "price_total": 800.0,
                "currency": "INR",
            },
            headers=self.h_host,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Duplicate Payment Test Event",
                "event_date": booking_date.isoformat(),
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)

        # First payment succeeds
        res1 = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)
        self.assertEqual(res1.status_code, 200)

        # Second payment fails
        res2 = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already fully paid", res2.json()["detail"])

    def test_03_outsider_payment_rejected(self):
        """Test that non-participants cannot pay for someone else's event (403)."""
        booking_date = date.today() + timedelta(days=13)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "16:00:00",
                "end_time": "18:00:00",
                "price_total": 600.0,
                "currency": "INR",
            },
            headers=self.h_host,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Outsider Payment Test Event",
                "event_date": booking_date.isoformat(),
                "start_time": "16:00:00",
                "end_time": "18:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)

        # Outsider attempts payment
        res = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_out)
        self.assertEqual(res.status_code, 403)
        self.assertIn("participant", res.json()["detail"])

    def test_04_overpayment_rejected(self):
        """Test that paying more than individual share is rejected (400)."""
        booking_date = date.today() + timedelta(days=14)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "price_total": 1000.0,
                "currency": "INR",
            },
            headers=self.h_host,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Overpayment Test Event",
                "event_date": booking_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/join", headers=self.h_p2)
        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)

        # Share is 500. Attempting to pay 600 fails
        res = client.post(f"/events/{event_id}/pay", json={"amount": 600.0}, headers=self.h_host)
        self.assertEqual(res.status_code, 400)
        self.assertIn("exceeds", res.json()["detail"].lower())

    def test_05_payment_on_event_without_venue_rejected(self):
        """Test that paying for an event without a venue booking is rejected (400)."""
        booking_date = date.today() + timedelta(days=15)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "No Venue Event",
                "event_date": booking_date.isoformat(),
                "start_time": "11:00:00",
                "end_time": "13:00:00",
                "max_capacity": 4,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        res = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)
        self.assertEqual(res.status_code, 400)
        self.assertIn("venue booking", res.json()["detail"].lower())

    def test_06_payment_on_cancelled_event_rejected(self):
        """Test that paying for a cancelled event is rejected (400)."""
        booking_date = date.today() + timedelta(days=16)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "price_total": 700.0,
                "currency": "INR",
            },
            headers=self.h_host,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Cancelled Match",
                "event_date": booking_date.isoformat(),
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "max_capacity": 2,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)

        # Cancel event
        client.patch(f"/events/{event_id}", json={"status": "CANCELLED"}, headers=self.h_host)

        # Attempt payment
        res = client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)
        self.assertEqual(res.status_code, 400)
        self.assertIn("CANCELLED", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()
