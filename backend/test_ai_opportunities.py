import unittest
import time
from datetime import date, timedelta, time as dtime
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestAIOpportunities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # 1. Master Interest & Activity for CREATE_EVENT Opportunity (Squash in Indiranagar)
        cls.squash_name = f"Squash_{ts}"
        squash = models.Interest(name=cls.squash_name, category="Racket Sports")
        cls.db.add(squash)
        cls.db.commit()
        cls.db.refresh(squash)
        cls.squash_id = squash.interest_id

        act_squash = models.Activity(
            interest_id=cls.squash_id,
            title=f"Squash Championship {ts}",
            description="Competitive squash doubles and singles",
        )
        cls.db.add(act_squash)
        cls.db.commit()
        cls.db.refresh(act_squash)
        cls.act_squash_id = act_squash.activity_id

        # 2. Master Interest for VENUE_PARTNERSHIP Opportunity (Bouldering in Whitefield, no venues)
        cls.bouldering_name = f"Bouldering_{ts}"
        bouldering = models.Interest(name=cls.bouldering_name, category="Adventure Sports")
        cls.db.add(bouldering)
        cls.db.commit()
        cls.db.refresh(bouldering)
        cls.bouldering_id = bouldering.interest_id

        act_bouldering = models.Activity(
            interest_id=cls.bouldering_id,
            title=f"Bouldering Session {ts}",
            description="Rock climbing & bouldering challenge",
        )
        cls.db.add(act_bouldering)
        cls.db.commit()
        cls.db.refresh(act_bouldering)
        cls.act_bouldering_id = act_bouldering.activity_id

        cls.pwd = "password123"

        # 3. Authenticated Organizer
        cls.host_email = f"opp.host.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_h = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_h = res_h["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.tok_h}"}

        host_user = cls.db.query(models.User).filter(models.User.email == cls.host_email).first()
        cls.host_id = host_user.user_id

        host_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.host_id).first()
        host_prof.display_name = "Opportunities Organizer"
        host_prof.approx_locality = "Indiranagar, Bengaluru"
        cls.db.add(models.UserInterest(user_id=cls.host_id, interest_id=cls.squash_id))
        cls.db.add(models.UserAvailability(
            user_id=cls.host_id,
            day_of_week="Saturday",
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
        ))
        cls.db.commit()

        # 4. Seed 11 Additional Squash Users in Indiranagar on Saturday (Total 12)
        cls.squash_user_ids = [cls.host_id]
        for i in range(1, 12):
            email = f"opp.sq.{i}.{ts}@vynk.com"
            client.post("/auth/register", json={"email": email, "password": cls.pwd, "confirm_password": cls.pwd})
            u = cls.db.query(models.User).filter(models.User.email == email).first()
            p = cls.db.query(models.Profile).filter(models.Profile.user_id == u.user_id).first()
            p.display_name = f"Squash Player {i}"
            p.approx_locality = "Indiranagar, Bengaluru"
            cls.db.add(models.UserInterest(user_id=u.user_id, interest_id=cls.squash_id))
            cls.db.add(models.UserAvailability(
                user_id=u.user_id,
                day_of_week="Saturday",
                start_time=dtime(18, 0),
                end_time=dtime(20, 0),
            ))
            cls.squash_user_ids.append(u.user_id)
        cls.db.commit()

        # 5. Seed 1 Competing Squash Event (Capacity 4, 2 confirmed -> 2 Spots Available)
        today = date.today()
        days_ahead = (5 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        sat_date = today + timedelta(days=days_ahead)

        event_sq = models.Event(
            activity_id=cls.act_squash_id,
            host_id=cls.host_id,
            title=f"Saturday Indiranagar Open Squash {ts}",
            event_date=sat_date,
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
            max_capacity=4,
            status="PUBLISHED",
        )
        cls.db.add(event_sq)
        cls.db.commit()
        cls.db.refresh(event_sq)
        cls.ev_sq_id = event_sq.event_id

        cls.db.add(models.EventParticipant(event_id=event_sq.event_id, user_id=cls.squash_user_ids[1], status="CONFIRMED"))
        cls.db.add(models.EventParticipant(event_id=event_sq.event_id, user_id=cls.squash_user_ids[2], status="CONFIRMED"))
        cls.db.commit()

        # 6. Seed Active Venue & Slot in Indiranagar (Price: ₹2400)
        venue = models.Venue(
            name=f"Indiranagar Squash Club {ts}",
            description="Professional glass-back squash courts",
            address="Double Road, Indiranagar",
            locality="Indiranagar",
            is_verified=True,
            status="ACTIVE",
        )
        cls.db.add(venue)
        cls.db.commit()
        cls.db.refresh(venue)
        cls.venue_id = venue.venue_id

        cls.db.add(models.VenueActivity(venue_id=venue.venue_id, activity_id=cls.act_squash_id))
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

        # 7. Seed 6 Users for Bouldering in Whitefield on Saturday (No Venues)
        cls.bouldering_user_ids = []
        for i in range(1, 7):
            email = f"opp.bould.{i}.{ts}@vynk.com"
            client.post("/auth/register", json={"email": email, "password": cls.pwd, "confirm_password": cls.pwd})
            u = cls.db.query(models.User).filter(models.User.email == email).first()
            p = cls.db.query(models.Profile).filter(models.Profile.user_id == u.user_id).first()
            p.display_name = f"Climber {i}"
            p.approx_locality = "Whitefield, Bengaluru"
            cls.db.add(models.UserInterest(user_id=u.user_id, interest_id=cls.bouldering_id))
            cls.db.add(models.UserAvailability(
                user_id=u.user_id,
                day_of_week="Saturday",
                start_time=dtime(18, 0),
                end_time=dtime(20, 0),
            ))
            cls.bouldering_user_ids.append(u.user_id)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_create_event_opportunity_detected(self):
        """Test 1: High demand + venue available -> CREATE_EVENT opportunity with high score."""
        res = client.get(f"/ai/opportunities?locality=Indiranagar&activity={self.squash_name}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_opportunities"], 0)

        opp = next((o for o in data["opportunities"] if self.squash_name in o["activity"]), None)
        self.assertIsNotNone(opp)
        self.assertEqual(opp["opportunity_type"], "CREATE_EVENT")
        self.assertEqual(opp["action"], "CREATE_EVENT")
        self.assertEqual(opp["locality"], "Indiranagar")
        self.assertEqual(opp["day"], "Saturday")
        self.assertEqual(opp["time"], "18:00-20:00")
        self.assertGreaterEqual(opp["demand_score"], 85)
        self.assertGreaterEqual(opp["feasibility_score"], 75)
        self.assertEqual(opp["expected_participants"], "8-10")
        self.assertEqual(opp["recommended_capacity"], 8)
        self.assertTrue(opp["venue_available"])
        self.assertEqual(opp["suggested_price_per_person"], 300.0)
        self.assertGreaterEqual(opp["opportunity_score"], 85)
        self.assertIsNotNone(opp["action_payload"])
        self.assertEqual(opp["action_payload"]["action"], "CREATE_EVENT")
        self.assertTrue(len(opp["reasons"]) >= 3)

    def test_02_venue_partnership_opportunity_detected(self):
        """Test 2: High demand + no local venue -> VENUE_PARTNERSHIP opportunity."""
        res = client.get(f"/ai/opportunities?locality=Whitefield&activity={self.bouldering_name}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        opp = next((o for o in data["opportunities"] if self.bouldering_name in o["activity"]), None)
        self.assertIsNotNone(opp)
        self.assertEqual(opp["opportunity_type"], "VENUE_PARTNERSHIP")
        self.assertEqual(opp["action"], "PARTNER_VENUE")
        self.assertFalse(opp["venue_available"])
        self.assertIn("Whitefield", opp["locality"])

    def test_03_ranking_and_score_filtering(self):
        """Test 3: Verify monotonic ranking and min_opportunity_score threshold."""
        res = client.get("/ai/opportunities?min_opportunity_score=50", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        opps = res.json()["opportunities"]

        for o in opps:
            self.assertGreaterEqual(o["opportunity_score"], 50)

        scores = [o["opportunity_score"] for o in opps]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_04_auth_and_limit_enforced(self):
        """Test 4: Unauthenticated access blocked and limit enforced."""
        res_no_auth = client.get("/ai/opportunities")
        self.assertEqual(res_no_auth.status_code, 401)

        res_limit = client.get("/ai/opportunities?limit=1", headers=self.headers)
        self.assertEqual(res_limit.status_code, 200)
        self.assertLessEqual(len(res_limit.json()["opportunities"]), 1)


if __name__ == "__main__":
    unittest.main()
