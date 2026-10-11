import unittest
from datetime import date, timedelta, time
from decimal import Decimal
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestEventVenueBooking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        # Ensure badminton and chess interests exist
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        chess = cls.db.query(models.Interest).filter(models.Interest.name == "Chess").first()
        if not chess:
            chess = models.Interest(name="Chess", category="Games")
            cls.db.add(chess)
            cls.db.commit()
            cls.db.refresh(chess)
        cls.chess_id = chess.interest_id

        # Register Host
        cls.host_email = "event.venue.host@vynk.com"
        cls.pwd = "password123"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_host = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.token_host = res_host["access_token"]
        cls.headers_host = {"Authorization": f"Bearer {cls.token_host}"}
        cls.user_host = client.get("/auth/me", headers=cls.headers_host).json()

        # Register Another User (Non-host)
        cls.other_email = "event.other.user@vynk.com"
        client.post("/auth/register", json={"email": cls.other_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_other = client.post("/auth/login", json={"email": cls.other_email, "password": cls.pwd}).json()
        cls.token_other = res_other["access_token"]
        cls.headers_other = {"Authorization": f"Bearer {cls.token_other}"}

        # Create Badminton Activity
        res_act = client.post(
            "/activities",
            json={
                "interest_id": cls.badminton_id,
                "title": "Badminton Doubles Arena",
                "description": "2v2 Doubles Badminton Tournament",
            },
            headers=cls.headers_host,
        )
        cls.badminton_act_id = res_act.json()["activity_id"]

        # Create Chess Activity
        res_chess = client.post(
            "/activities",
            json={
                "interest_id": cls.chess_id,
                "title": "Chess Blitz Tournament",
                "description": "Speed chess games",
            },
            headers=cls.headers_host,
        )
        cls.chess_act_id = res_chess.json()["activity_id"]

        # Create Badminton Venue (supports badminton only)
        res_v1 = client.post(
            "/venues",
            json={
                "name": "SmashZone Arena",
                "description": "Professional indoor badminton arena",
                "address": "Road No 36, Jubilee Hills",
                "locality": "Jubilee Hills, Hyderabad",
                "activity_ids": [cls.badminton_act_id],
            },
            headers=cls.headers_host,
        )
        cls.venue_id = res_v1.json()["venue_id"]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_successful_event_venue_booking(self):
        """Test full happy path: Event created -> compatible venue slot booked -> slot becomes BOOKED."""
        booking_date = date.today() + timedelta(days=5)

        # 1. Create Available Slot on Venue
        res_slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "17:00:00",
                "end_time": "19:00:00",
                "price_total": 1500.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        )
        self.assertEqual(res_slot.status_code, 201)
        slot = res_slot.json()
        slot_id = slot["slot_id"]
        self.assertEqual(slot["status"], "AVAILABLE")

        # 2. Create Event (without slot initially)
        res_ev = client.post(
            "/events",
            json={
                "activity_id": self.badminton_act_id,
                "title": "Friday Smash Night",
                "event_date": booking_date.isoformat(),
                "start_time": "17:00:00",
                "end_time": "19:00:00",
                "max_capacity": 4,
            },
            headers=self.headers_host,
        )
        self.assertEqual(res_ev.status_code, 201)
        event = res_ev.json()
        event_id = event["event_id"]
        self.assertIsNone(event["venue_booking"])

        # 3. Call POST /events/{event_id}/venue-book
        res_book = client.post(
            f"/events/{event_id}/venue-book",
            json={"slot_id": slot_id},
            headers=self.headers_host,
        )
        self.assertEqual(res_book.status_code, 200)
        booked_event = res_book.json()

        # 4. Verify Venue Booking Details
        vb = booked_event["venue_booking"]
        self.assertIsNotNone(vb)
        self.assertEqual(vb["slot_id"], slot_id)
        self.assertEqual(vb["venue_id"], self.venue_id)
        self.assertEqual(vb["venue_name"], "SmashZone Arena")
        self.assertEqual(vb["total_amount"], 1500.0)
        self.assertEqual(vb["status"], "CONFIRMED")
        self.assertEqual(booked_event["locality"], "Jubilee Hills, Hyderabad")
        # 1 host confirmed participant -> per person cost = 1500.0 / 1 = 1500.0
        self.assertEqual(booked_event["per_person_cost"], 1500.0)

        # 5. Verify Slot status in database is BOOKED
        db = SessionLocal()
        db_slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == slot_id).first()
        self.assertEqual(db_slot.status, "BOOKED")
        db.close()

    def test_02_duplicate_booking_rejected(self):
        """Test that attempting to book a venue on an event that already has a booking fails with 400."""
        booking_date = date.today() + timedelta(days=6)

        # Create slot 1 and slot 2
        slot1 = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "price_total": 1000.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        ).json()

        slot2 = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "price_total": 1000.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        ).json()

        # Create event
        ev = client.post(
            "/events",
            json={
                "activity_id": self.badminton_act_id,
                "title": "Weekend Shuttle Doubles",
                "event_date": booking_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "max_capacity": 4,
            },
            headers=self.headers_host,
        ).json()
        event_id = ev["event_id"]

        # First booking succeeds
        res1 = client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot1["slot_id"]}, headers=self.headers_host)
        self.assertEqual(res1.status_code, 200)

        # Second booking attempt on same event fails
        res2 = client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot2["slot_id"]}, headers=self.headers_host)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already has a venue booking", res2.json()["detail"])

    def test_03_already_booked_slot_rejected(self):
        """Test that booking an already BOOKED slot is rejected with 400."""
        booking_date = date.today() + timedelta(days=7)

        # Create slot
        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "08:00:00",
                "end_time": "10:00:00",
                "price_total": 800.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        ).json()
        slot_id = slot["slot_id"]

        # Event 1 books the slot
        ev1 = client.post(
            "/events",
            json={
                "activity_id": self.badminton_act_id,
                "title": "Morning Match 1",
                "event_date": booking_date.isoformat(),
                "start_time": "08:00:00",
                "end_time": "10:00:00",
                "max_capacity": 4,
            },
            headers=self.headers_host,
        ).json()
        res1 = client.post(f"/events/{ev1['event_id']}/venue-book", json={"slot_id": slot_id}, headers=self.headers_host)
        self.assertEqual(res1.status_code, 200)

        # Event 2 tries to book the same slot
        ev2 = client.post(
            "/events",
            json={
                "activity_id": self.badminton_act_id,
                "title": "Morning Match 2",
                "event_date": booking_date.isoformat(),
                "start_time": "08:00:00",
                "end_time": "10:00:00",
                "max_capacity": 4,
            },
            headers=self.headers_host,
        ).json()
        res2 = client.post(f"/events/{ev2['event_id']}/venue-book", json={"slot_id": slot_id}, headers=self.headers_host)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already BOOKED", res2.json()["detail"])

    def test_04_incompatible_activity_venue_rejected(self):
        """Test that booking a venue which doesn't support the event's activity is rejected with 400."""
        booking_date = date.today() + timedelta(days=8)

        # SmashZone arena only supports Badminton. Let's create a Chess event.
        chess_ev = client.post(
            "/events",
            json={
                "activity_id": self.chess_act_id,
                "title": "Jubilee Hills Chess Gathering",
                "event_date": booking_date.isoformat(),
                "start_time": "15:00:00",
                "end_time": "17:00:00",
                "max_capacity": 2,
            },
            headers=self.headers_host,
        ).json()

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "15:00:00",
                "end_time": "17:00:00",
                "price_total": 900.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        ).json()

        res = client.post(
            f"/events/{chess_ev['event_id']}/venue-book",
            json={"slot_id": slot["slot_id"]},
            headers=self.headers_host,
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("does not support the activity", res.json()["detail"])

    def test_05_non_host_forbidden(self):
        """Test that a non-host user cannot book a venue for someone else's event (403)."""
        booking_date = date.today() + timedelta(days=9)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.badminton_act_id,
                "title": "Host Exclusive Event",
                "event_date": booking_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 4,
            },
            headers=self.headers_host,
        ).json()

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "price_total": 1200.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        ).json()

        # Non-host attempts booking
        res = client.post(
            f"/events/{ev['event_id']}/venue-book",
            json={"slot_id": slot["slot_id"]},
            headers=self.headers_other,
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("host", res.json()["detail"].lower())

    def test_06_date_mismatch_rejected(self):
        """Test that date mismatch between event date and slot date is rejected (400)."""
        ev_date = date.today() + timedelta(days=10)
        slot_date = date.today() + timedelta(days=11)

        ev = client.post(
            "/events",
            json={
                "activity_id": self.badminton_act_id,
                "title": "Date Mismatch Test Event",
                "event_date": ev_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 4,
            },
            headers=self.headers_host,
        ).json()

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": slot_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "price_total": 1000.0,
                "currency": "INR",
            },
            headers=self.headers_host,
        ).json()

        res = client.post(
            f"/events/{ev['event_id']}/venue-book",
            json={"slot_id": slot["slot_id"]},
            headers=self.headers_host,
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("does not match venue slot date", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()
