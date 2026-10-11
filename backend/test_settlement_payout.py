import unittest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestSettlementPayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        # Ensure Badminton interest
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        cls.pwd = "password123"

        # 1. Setup Venue Owner (Vikram)
        cls.owner_email = "vikram.owner@vynk.com"
        client.post("/auth/register", json={"email": cls.owner_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_owner = client.post("/auth/login", json={"email": cls.owner_email, "password": cls.pwd}).json()
        cls.tok_owner = res_owner["access_token"]
        cls.h_owner = {"Authorization": f"Bearer {cls.tok_owner}"}
        cls.user_owner = client.get("/auth/me", headers=cls.h_owner).json()
        client.put("/profiles/me", json={"display_name": "Vikram Venue Owner", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_owner)

        # Register Payout Account for Venue Owner
        res_acc = client.post(
            "/payment-accounts",
            json={"provider": "razorpay", "provider_account_id": "acc_razorpay_vikram_9988"},
            headers=cls.h_owner,
        )
        cls.owner_acc_id = res_acc.json()["payment_account_id"]

        # 2. Setup Event Host (Pooja)
        cls.host_email = "pooja.settlehost@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_host = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_host = res_host["access_token"]
        cls.h_host = {"Authorization": f"Bearer {cls.tok_host}"}
        cls.user_host = client.get("/auth/me", headers=cls.h_host).json()
        client.put("/profiles/me", json={"display_name": "Pooja Hegde", "locality": "Indiranagar, Bengaluru"}, headers=cls.h_host)

        # 3. Setup Participant 2 (Rahul)
        cls.p2_email = "rahul.settlep2@vynk.com"
        client.post("/auth/register", json={"email": cls.p2_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p2 = client.post("/auth/login", json={"email": cls.p2_email, "password": cls.pwd}).json()
        cls.tok_p2 = res_p2["access_token"]
        cls.h_p2 = {"Authorization": f"Bearer {cls.tok_p2}"}
        cls.user_p2 = client.get("/auth/me", headers=cls.h_p2).json()

        # 4. Setup Participant 3 (Amit)
        cls.p3_email = "amit.settlep3@vynk.com"
        client.post("/auth/register", json={"email": cls.p3_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p3 = client.post("/auth/login", json={"email": cls.p3_email, "password": cls.pwd}).json()
        cls.tok_p3 = res_p3["access_token"]
        cls.h_p3 = {"Authorization": f"Bearer {cls.tok_p3}"}
        cls.user_p3 = client.get("/auth/me", headers=cls.h_p3).json()

        # 5. Setup Outsider (Sneha)
        cls.outsider_email = "sneha.settleout@vynk.com"
        client.post("/auth/register", json={"email": cls.outsider_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_out = client.post("/auth/login", json={"email": cls.outsider_email, "password": cls.pwd}).json()
        cls.tok_out = res_out["access_token"]
        cls.h_out = {"Authorization": f"Bearer {cls.tok_out}"}

        # Activity
        act = client.post(
            "/activities",
            json={
                "interest_id": cls.badminton_id,
                "title": "Badminton Championship Settle",
                "description": "Championship with payout settlement",
            },
            headers=cls.h_host,
        ).json()
        cls.activity_id = act["activity_id"]

        # Venue Owned by Vikram
        db_venue = models.Venue(
            owner_user_id=cls.user_owner["user_id"],
            name="Indiranagar Grand Sports Complex",
            description="Premium badminton courts",
            address="100 Feet Road, Indiranagar",
            locality="Indiranagar, Bengaluru",
            status="ACTIVE",
        )
        cls.db.add(db_venue)
        cls.db.flush()

        cls.db.add(models.VenueActivity(venue_id=db_venue.venue_id, activity_id=cls.activity_id))
        cls.db.commit()
        cls.db.refresh(db_venue)
        cls.venue_id = db_venue.venue_id

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_target_settlement_payout_journey(self):
        """
        Target test journey:
        ₹1,200 venue + 3 participants paying ₹400 each
        -> ₹1,200 collected
        -> POST /events/{id}/payout
        -> Payout ₹1,200 created with status COMPLETED
        """
        booking_date = date.today() + timedelta(days=20)

        # 1. Create slot (₹1,200 total)
        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "price_total": 1200.0,
                "currency": "INR",
            },
            headers=self.h_owner,
        ).json()
        slot_id = slot["slot_id"]

        # 2. Create Event (Capacity = 3)
        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Grand Championship Final",
                "event_date": booking_date.isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "max_capacity": 3,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        # 3. Rahul & Amit join
        client.post(f"/events/{event_id}/join", headers=self.h_p2)
        client.post(f"/events/{event_id}/join", headers=self.h_p3)

        # 4. Host books venue slot
        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot_id}, headers=self.h_host)

        # 5. All 3 participants pay ₹400
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_p2)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_p3)

        # 6. Host triggers payout settlement: POST /events/{event_id}/payout
        res_payout = client.post(f"/events/{event_id}/payout", headers=self.h_host)
        self.assertEqual(res_payout.status_code, 200)
        payout = res_payout.json()

        self.assertEqual(payout["amount"], 1200.0)
        self.assertEqual(payout["currency"], "INR")
        self.assertEqual(payout["status"], "COMPLETED")
        self.assertEqual(payout["payment_account_id"], self.owner_acc_id)
        self.assertTrue(payout["provider_transfer_id"].startswith("TRF_SIM_"))

    def test_02_payout_before_fully_paid_rejected(self):
        """Test that payout fails if venue booking is not fully collected (400)."""
        booking_date = date.today() + timedelta(days=21)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "price_total": 900.0,
                "currency": "INR",
            },
            headers=self.h_owner,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Unpaid Payout Test Event",
                "event_date": booking_date.isoformat(),
                "start_time": "14:00:00",
                "end_time": "16:00:00",
                "max_capacity": 3,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/join", headers=self.h_p2)
        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)

        # Only Host pays (₹450 paid out of ₹900)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)

        # Trigger payout attempt fails
        res = client.post(f"/events/{event_id}/payout", headers=self.h_host)
        self.assertEqual(res.status_code, 400)
        self.assertIn("not fully paid", res.json()["detail"])

    def test_03_duplicate_payout_rejected(self):
        """Test that duplicate payout on the same booking fails (400)."""
        booking_date = date.today() + timedelta(days=22)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "price_total": 600.0,
                "currency": "INR",
            },
            headers=self.h_owner,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Duplicate Payout Test Event",
                "event_date": booking_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "max_capacity": 1,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)

        # First payout succeeds
        res1 = client.post(f"/events/{event_id}/payout", headers=self.h_host)
        self.assertEqual(res1.status_code, 200)

        # Second payout fails
        res2 = client.post(f"/events/{event_id}/payout", headers=self.h_host)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already been processed", res2.json()["detail"])

    def test_04_no_venue_owner_account_rejected(self):
        """Test that payout fails if venue has no registered owner or owner has no payout account (400)."""
        booking_date = date.today() + timedelta(days=23)

        # Register venue without owner
        db = SessionLocal()
        unowned_venue = models.Venue(
            owner_user_id=None,
            name="Unowned Public Court",
            address="Koramangala, Bengaluru",
            locality="Koramangala, Bengaluru",
            status="ACTIVE",
        )
        db.add(unowned_venue)
        db.flush()
        db.add(models.VenueActivity(venue_id=unowned_venue.venue_id, activity_id=self.activity_id))
        db.commit()
        db.refresh(unowned_venue)
        venue_id = unowned_venue.venue_id

        slot = models.VenueSlot(
            venue_id=venue_id,
            slot_date=booking_date,
            start_time="11:00:00",
            end_time="13:00:00",
            price_total=Decimal("500.0"),
            currency="INR",
            status="AVAILABLE",
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
        slot_id = slot.slot_id
        db.close()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Unowned Venue Payout Test",
                "event_date": booking_date.isoformat(),
                "start_time": "11:00:00",
                "end_time": "13:00:00",
                "max_capacity": 1,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot_id}, headers=self.h_host)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)

        # Payout fails because no owner account
        res = client.post(f"/events/{event_id}/payout", headers=self.h_host)
        self.assertEqual(res.status_code, 400)
        self.assertIn("registered owner", res.json()["detail"])

    def test_05_cancelled_event_rejected(self):
        """Test that payout fails for a cancelled event (400)."""
        booking_date = date.today() + timedelta(days=24)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "16:00:00",
                "end_time": "18:00:00",
                "price_total": 600.0,
                "currency": "INR",
            },
            headers=self.h_owner,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Cancelled Payout Event",
                "event_date": booking_date.isoformat(),
                "start_time": "16:00:00",
                "end_time": "18:00:00",
                "max_capacity": 1,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)

        # Cancel event
        client.patch(f"/events/{event_id}", json={"status": "CANCELLED"}, headers=self.h_host)

        res = client.post(f"/events/{event_id}/payout", headers=self.h_host)
        self.assertEqual(res.status_code, 400)
        self.assertIn("CANCELLED", res.json()["detail"])

    def test_06_non_host_outsider_forbidden(self):
        """Test that a non-host outsider cannot trigger payout (403)."""
        booking_date = date.today() + timedelta(days=25)

        slot = client.post(
            f"/venues/{self.venue_id}/slots",
            json={
                "slot_date": booking_date.isoformat(),
                "start_time": "19:00:00",
                "end_time": "21:00:00",
                "price_total": 700.0,
                "currency": "INR",
            },
            headers=self.h_owner,
        ).json()

        ev = client.post(
            "/events",
            json={
                "activity_id": self.activity_id,
                "title": "Outsider Payout Forbidden Test",
                "event_date": booking_date.isoformat(),
                "start_time": "19:00:00",
                "end_time": "21:00:00",
                "max_capacity": 1,
            },
            headers=self.h_host,
        ).json()
        event_id = ev["event_id"]

        client.post(f"/events/{event_id}/venue-book", json={"slot_id": slot["slot_id"]}, headers=self.h_host)
        client.post(f"/events/{event_id}/pay", json={}, headers=self.h_host)

        # Outsider triggers payout
        res = client.post(f"/events/{event_id}/payout", headers=self.h_out)
        self.assertEqual(res.status_code, 403)
        self.assertIn("host", res.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
