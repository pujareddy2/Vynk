import unittest
import time
from datetime import date, timedelta, time as dtime
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestAIDemandRadar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # 1. Master Interests (Pristine isolated categories)
        cls.padel_name = f"Padel_{ts}"
        padel = models.Interest(name=cls.padel_name, category="Racket Sports")
        cls.db.add(padel)
        cls.db.commit()
        cls.db.refresh(padel)
        cls.padel_id = padel.interest_id

        cls.ceramics_name = f"Ceramics_{ts}"
        ceramics = models.Interest(name=cls.ceramics_name, category="Creative Arts")
        cls.db.add(ceramics)
        cls.db.commit()
        cls.db.refresh(ceramics)
        cls.ceramics_id = ceramics.interest_id
        # 2. Activities (Dedicated to this test run's interests)
        act_padel = models.Activity(
            interest_id=cls.padel_id,
            title=f"Radar Padel Doubles {ts}",
            description="Community padel league",
        )
        cls.db.add(act_padel)
        cls.db.commit()
        cls.db.refresh(act_padel)
        cls.act_padel_id = act_padel.activity_id

        act_ceramics = models.Activity(
            interest_id=cls.ceramics_id,
            title=f"Radar Ceramics Workshop {ts}",
            description="Creative pottery session",
        )
        cls.db.add(act_ceramics)
        cls.db.commit()
        cls.db.refresh(act_ceramics)
        cls.act_ceramics_id = act_ceramics.activity_id

        cls.pwd = "password123"

        # 3. Primary Authenticated User
        cls.host_email = f"radar.host.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_h = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_h = res_h["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.tok_h}"}

        host_user = cls.db.query(models.User).filter(models.User.email == cls.host_email).first()
        cls.host_id = host_user.user_id

        # Update host profile & availability
        host_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.host_id).first()
        host_prof.display_name = "Host Radar Organizer"
        host_prof.approx_locality = "Indiranagar, Bengaluru"
        cls.db.add(models.UserInterest(user_id=cls.host_id, interest_id=cls.padel_id))
        cls.db.add(models.UserAvailability(
            user_id=cls.host_id,
            day_of_week="Saturday",
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
        ))
        cls.db.commit()

        # 4. Seed 11 Additional Users interested in Padel in Indiranagar on Saturday (Total 12)
        cls.padel_user_ids = [cls.host_id]
        for i in range(1, 12):
            email = f"radar.padel.{i}.{ts}@vynk.com"
            client.post("/auth/register", json={"email": email, "password": cls.pwd, "confirm_password": cls.pwd})
            u = cls.db.query(models.User).filter(models.User.email == email).first()
            p = cls.db.query(models.Profile).filter(models.Profile.user_id == u.user_id).first()
            p.display_name = f"Padel Player {i}"
            p.approx_locality = "Indiranagar, Bengaluru"
            cls.db.add(models.UserInterest(user_id=u.user_id, interest_id=cls.padel_id))
            cls.db.add(models.UserAvailability(
                user_id=u.user_id,
                day_of_week="Saturday",
                start_time=dtime(18, 0),
                end_time=dtime(20, 0),
            ))
            cls.padel_user_ids.append(u.user_id)
        cls.db.commit()

        # 5. Seed 1 Active Event in Indiranagar on a Saturday: Capacity 4, with 2 Participants -> 2 Spots Available
        today = date.today()
        days_ahead = (5 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        sat_date = today + timedelta(days=days_ahead)

        event_padel = models.Event(
            activity_id=cls.act_padel_id,
            host_id=cls.host_id,
            title="Saturday Indiranagar Open Padel",
            event_date=sat_date,
            start_time=dtime(18, 0),
            end_time=dtime(20, 0),
            max_capacity=4,
            status="PUBLISHED",
        )
        cls.db.add(event_padel)
        cls.db.commit()
        cls.db.refresh(event_padel)
        cls.ev_padel_id = event_padel.event_id

        # Add 2 participants to leave 2 spots
        cls.db.add(models.EventParticipant(event_id=event_padel.event_id, user_id=cls.padel_user_ids[1], status="CONFIRMED"))
        cls.db.add(models.EventParticipant(event_id=event_padel.event_id, user_id=cls.padel_user_ids[2], status="CONFIRMED"))
        cls.db.commit()

        # 6. Seed a Balanced Cluster: Ceramics in Koramangala on Sunday
        # 2 interested users, 1 event with capacity 10 -> unmet demand = 0 -> BALANCED
        cls.ceramics_user_ids = []
        for i in range(1, 3):
            email = f"radar.ceramics.{i}.{ts}@vynk.com"
            client.post("/auth/register", json={"email": email, "password": cls.pwd, "confirm_password": cls.pwd})
            u = cls.db.query(models.User).filter(models.User.email == email).first()
            p = cls.db.query(models.Profile).filter(models.Profile.user_id == u.user_id).first()
            p.display_name = f"Ceramics Crafter {i}"
            p.approx_locality = "Koramangala, Bengaluru"
            cls.db.add(models.UserInterest(user_id=u.user_id, interest_id=cls.ceramics_id))
            cls.db.add(models.UserAvailability(
                user_id=u.user_id,
                day_of_week="Sunday",
                start_time=dtime(11, 0),
                end_time=dtime(13, 0),
            ))
            cls.ceramics_user_ids.append(u.user_id)
        cls.db.commit()

        sun_days = (6 - today.weekday()) % 7
        if sun_days == 0:
            sun_days = 7
        sun_date = today + timedelta(days=sun_days)

        event_ceramics = models.Event(
            activity_id=cls.act_ceramics_id,
            host_id=cls.ceramics_user_ids[0],
            title="Koramangala Sunday Ceramics Workshop",
            event_date=sun_date,
            start_time=dtime(11, 0),
            end_time=dtime(13, 0),
            max_capacity=10,
            status="PUBLISHED",
        )
        cls.db.add(event_ceramics)
        cls.db.commit()
        cls.db.refresh(event_ceramics)
        cls.ev_ceramics_id = event_ceramics.event_id

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_high_unmet_demand_cluster_detected(self):
        """Test 1: Detect 12 interested users with 2 available spots -> 10 unmet demand -> HIGH_DEMAND (score >= 85)."""
        res = client.get(f"/ai/demand-radar?locality=Indiranagar&activity={self.padel_name}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_clusters"], 0)
        clusters = data["clusters"]

        padel_cluster = next((c for c in clusters if self.padel_name in c["activity"] and c["locality"] == "Indiranagar"), None)
        self.assertIsNotNone(padel_cluster)
        self.assertEqual(padel_cluster["preferred_day"], "Saturday")
        self.assertEqual(padel_cluster["preferred_time"], "18:00-20:00")
        self.assertEqual(padel_cluster["interested_users"], 12)
        self.assertEqual(padel_cluster["active_events"], 1)
        self.assertEqual(padel_cluster["available_spots"], 2)
        self.assertEqual(padel_cluster["estimated_unmet_demand"], 10)
        self.assertGreaterEqual(padel_cluster["demand_score"], 85)
        self.assertEqual(padel_cluster["status"], "HIGH_DEMAND")
        self.assertIn("Indiranagar", padel_cluster["suggested_action"])

    def test_02_balanced_capacity_cluster_detected(self):
        """Test 2: When open event capacity exceeds interested users -> unmet demand is 0 and status is BALANCED."""
        res = client.get(f"/ai/demand-radar?locality=Koramangala&activity={self.ceramics_name}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        clusters = data["clusters"]

        ceramics_cluster = next((c for c in clusters if self.ceramics_name in c["activity"]), None)
        self.assertIsNotNone(ceramics_cluster)
        self.assertEqual(ceramics_cluster["preferred_day"], "Sunday")
        self.assertEqual(ceramics_cluster["estimated_unmet_demand"], 0)
        self.assertGreaterEqual(ceramics_cluster["available_spots"], 10)
        self.assertEqual(ceramics_cluster["status"], "BALANCED")
        self.assertIn("balanced", ceramics_cluster["suggested_action"].lower())

    def test_03_query_filters_and_demand_ranking(self):
        """Test 3: Query filters (day_of_week, min_demand_score) and verify monotonic score ranking."""
        res = client.get("/ai/demand-radar?day_of_week=Saturday&min_demand_score=50", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        clusters = data["clusters"]

        for c in clusters:
            self.assertEqual(c["preferred_day"], "Saturday")
            self.assertGreaterEqual(c["demand_score"], 50)

        # Check descending order by demand_score
        scores = [c["demand_score"] for c in clusters]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_04_auth_and_limit_enforcement(self):
        """Test 4: Verify authentication requirement and limit parameter."""
        # Unauthenticated request rejected
        res_no_auth = client.get("/ai/demand-radar")
        self.assertEqual(res_no_auth.status_code, 401)

        # Limit parameter enforced
        res_limit = client.get("/ai/demand-radar?limit=1", headers=self.headers)
        self.assertEqual(res_limit.status_code, 200)
        data = res_limit.json()
        self.assertLessEqual(len(data["clusters"]), 1)


if __name__ == "__main__":
    unittest.main()
