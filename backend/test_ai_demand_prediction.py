import unittest
import time
from datetime import date, timedelta, time as dtime
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestAIDemandPrediction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # 1. Master Interest & Activity (Pristine isolated domain)
        cls.pickleball_name = f"Pickleball_{ts}"
        pickleball = models.Interest(name=cls.pickleball_name, category="Racket Sports")
        cls.db.add(pickleball)
        cls.db.commit()
        cls.db.refresh(pickleball)
        cls.pickleball_id = pickleball.interest_id

        act_pickleball = models.Activity(
            interest_id=cls.pickleball_id,
            title=f"Pickleball Indiranagar Doubles {ts}",
            description="Competitive doubles pickleball session",
        )
        cls.db.add(act_pickleball)
        cls.db.commit()
        cls.db.refresh(act_pickleball)
        cls.act_pickleball_id = act_pickleball.activity_id

        cls.pwd = "password123"

        # 2. Primary Authenticated Organizer
        cls.host_email = f"pred.host.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_h = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_h = res_h["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.tok_h}"}

        host_user = cls.db.query(models.User).filter(models.User.email == cls.host_email).first()
        cls.host_id = host_user.user_id

        host_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.host_id).first()
        host_prof.display_name = "Predictor Organizer"
        host_prof.approx_locality = "Indiranagar, Bengaluru"
        cls.db.add(models.UserInterest(user_id=cls.host_id, interest_id=cls.pickleball_id))
        cls.db.add(models.UserAvailability(
            user_id=cls.host_id,
            day_of_week="Saturday",
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
        ))
        cls.db.commit()

        # 3. Seed 11 Additional Interested Users in Indiranagar on Saturday (Total 12)
        cls.player_user_ids = [cls.host_id]
        for i in range(1, 12):
            email = f"pred.pb.{i}.{ts}@vynk.com"
            client.post("/auth/register", json={"email": email, "password": cls.pwd, "confirm_password": cls.pwd})
            u = cls.db.query(models.User).filter(models.User.email == email).first()
            p = cls.db.query(models.Profile).filter(models.Profile.user_id == u.user_id).first()
            p.display_name = f"Pickleball Player {i}"
            p.approx_locality = "Indiranagar, Bengaluru"
            cls.db.add(models.UserInterest(user_id=u.user_id, interest_id=cls.pickleball_id))
            cls.db.add(models.UserAvailability(
                user_id=u.user_id,
                day_of_week="Saturday",
                start_time=dtime(18, 0),
                end_time=dtime(20, 0),
            ))
            cls.player_user_ids.append(u.user_id)
        cls.db.commit()

        # 4. Seed 1 Competing Event with Capacity 4 and 2 participants -> 2 Spots Available
        today = date.today()
        days_ahead = (5 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        sat_date = today + timedelta(days=days_ahead)

        event_pb = models.Event(
            activity_id=cls.act_pickleball_id,
            host_id=cls.host_id,
            title=f"Saturday Indiranagar Open Pickleball {ts}",
            event_date=sat_date,
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
            max_capacity=4,
            status="PUBLISHED",
        )
        cls.db.add(event_pb)
        cls.db.commit()
        cls.db.refresh(event_pb)
        cls.ev_pb_id = event_pb.event_id

        cls.db.add(models.EventParticipant(event_id=event_pb.event_id, user_id=cls.player_user_ids[1], status="CONFIRMED"))
        cls.db.add(models.EventParticipant(event_id=event_pb.event_id, user_id=cls.player_user_ids[2], status="CONFIRMED"))
        cls.db.commit()

        # 5. Seed Venue & Bookable Slot in Indiranagar (Price: ₹2400)
        venue = models.Venue(
            name=f"Indiranagar Smash Arena {ts}",
            description="Modern racket sport courts",
            address="100 Feet Road, Indiranagar",
            locality="Indiranagar",
            is_verified=True,
            status="ACTIVE",
        )
        cls.db.add(venue)
        cls.db.commit()
        cls.db.refresh(venue)
        cls.venue_id = venue.venue_id

        cls.db.add(models.VenueActivity(venue_id=venue.venue_id, activity_id=cls.act_pickleball_id))
        slot = models.VenueSlot(
            venue_id=venue.venue_id,
            slot_date=sat_date,
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
            price_total=2400.0,
            currency="INR",
            status="AVAILABLE",
        )
        cls.db.add(slot)
        cls.db.commit()
        cls.slot_id = slot.slot_id

        # 6. Seed a Low-Demand Domain (Chess in Whitefield)
        cls.chess_name = f"Chess_{ts}"
        chess = models.Interest(name=cls.chess_name, category="Board Games")
        cls.db.add(chess)
        cls.db.commit()
        cls.chess_id = chess.interest_id

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_predict_high_demand_activity_feasibility(self):
        """Test 1: Predict outcome for 12 interested users with 2 available spots (10 unmet demand)."""
        payload = {
            "activity": self.pickleball_name,
            "locality": "Indiranagar",
            "day_of_week": "Saturday",
            "preferred_time": "18:00-20:00",
        }
        res = client.post("/ai/demand-prediction", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["activity"], self.pickleball_name)
        self.assertEqual(data["locality"], "Indiranagar")
        self.assertEqual(data["day_of_week"], "Saturday")
        self.assertEqual(data["preferred_time"], "18:00-20:00")
        self.assertEqual(data["current_demand"], "HIGH")
        self.assertEqual(data["interested_users"], 12)
        self.assertEqual(data["unmet_demand"], 10)
        self.assertEqual(data["recommended_capacity"], 8)
        self.assertEqual(data["expected_participants_range"], "8-10")
        self.assertGreaterEqual(data["attendance_probability"], 80)
        self.assertGreaterEqual(data["estimated_fill_rate"], 85)
        self.assertEqual(data["suggested_price_per_person"], 300.0)  # 2400 / 8
        self.assertEqual(data["feasibility"], "HIGH")
        self.assertGreaterEqual(data["feasibility_score"], 75)
        self.assertGreaterEqual(data["venue_slots_available"], 1)
        self.assertTrue(len(data["factors"]) >= 3)

    def test_02_get_endpoint_parity(self):
        """Test 2: Verify GET endpoint produces identical prediction metrics as POST."""
        url = f"/ai/demand-prediction?locality=Indiranagar&day_of_week=Saturday&activity={self.pickleball_name}"
        res = client.get(url, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["current_demand"], "HIGH")
        self.assertEqual(data["unmet_demand"], 10)
        self.assertEqual(data["recommended_capacity"], 8)
        self.assertEqual(data["feasibility"], "HIGH")

    def test_03_custom_target_capacity_and_price_override(self):
        """Test 3: Custom target_capacity and target_price overrides are honored in prediction model."""
        payload = {
            "activity": self.pickleball_name,
            "locality": "Indiranagar",
            "day_of_week": "Saturday",
            "target_capacity": 6,
            "target_price": 450.0,
        }
        res = client.post("/ai/demand-prediction", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["recommended_capacity"], 6)
        self.assertEqual(data["suggested_price_per_person"], 450.0)

    def test_04_low_demand_activity_feasibility(self):
        """Test 4: Activity with 0 interested users produces LOW/MODERATE demand and risk evaluation."""
        payload = {
            "activity": self.chess_name,
            "locality": "Whitefield",
            "day_of_week": "Tuesday",
        }
        res = client.post("/ai/demand-prediction", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["current_demand"], "LOW")
        self.assertEqual(data["interested_users"], 0)
        self.assertEqual(data["unmet_demand"], 0)
        self.assertIn(data["feasibility"], ["LOW", "CRITICAL_RISK", "MODERATE"])
        self.assertLess(data["feasibility_score"], 60)

    def test_05_unauthenticated_request_rejected(self):
        """Test 5: Unauthenticated access is blocked with 401 Unauthorized."""
        res = client.post("/ai/demand-prediction", json={"locality": "Indiranagar", "day_of_week": "Saturday"})
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
