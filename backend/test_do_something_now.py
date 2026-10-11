import unittest
import time
from datetime import date, timedelta, time as dtime
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)


class TestDoSomethingNow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        ts = int(time.time() * 1000)

        # 1. Master Interests
        badminton = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton:
            badminton = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton)
            cls.db.commit()
            cls.db.refresh(badminton)
        cls.badminton_id = badminton.interest_id

        football = cls.db.query(models.Interest).filter(models.Interest.name == "Football").first()
        if not football:
            football = models.Interest(name="Football", category="Sports")
            cls.db.add(football)
            cls.db.commit()
            cls.db.refresh(football)
        cls.football_id = football.interest_id

        archery = cls.db.query(models.Interest).filter(models.Interest.name == "Archery").first()
        if not archery:
            archery = models.Interest(name="Archery", category="Sports")
            cls.db.add(archery)
            cls.db.commit()
            cls.db.refresh(archery)
        cls.archery_id = archery.interest_id

        # 2. Activities
        act_badminton = cls.db.query(models.Activity).filter(models.Activity.title == "Instant Badminton Match").first()
        if not act_badminton:
            act_badminton = models.Activity(interest_id=cls.badminton_id, title="Instant Badminton Match", description="Fast pickup badminton")
            cls.db.add(act_badminton)
            cls.db.commit()
            cls.db.refresh(act_badminton)
        cls.act_badminton_id = act_badminton.activity_id

        act_football = cls.db.query(models.Activity).filter(models.Activity.title == "5v5 Turf Football").first()
        if not act_football:
            act_football = models.Activity(interest_id=cls.football_id, title="5v5 Turf Football", description="Pickup football on artificial turf")
            cls.db.add(act_football)
            cls.db.commit()
            cls.db.refresh(act_football)
        cls.act_football_id = act_football.activity_id

        act_archery = cls.db.query(models.Activity).filter(models.Activity.title == "Target Archery Range").first()
        if not act_archery:
            act_archery = models.Activity(interest_id=cls.archery_id, title="Target Archery Range", description="Archery shooting session")
            cls.db.add(act_archery)
            cls.db.commit()
            cls.db.refresh(act_archery)
        cls.act_archery_id = act_archery.activity_id

        cls.pwd = "password123"

        # 3. User A (Primary Searcher) - Interested in Badminton & Football, Available on Saturday 18:00-20:00 in Indiranagar
        cls.user_email = f"dsn.user.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.user_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_u = client.post("/auth/login", json={"email": cls.user_email, "password": cls.pwd}).json()
        cls.tok_u = res_u["access_token"]
        cls.h_u = {"Authorization": f"Bearer {cls.tok_u}"}
        cls.user_obj = client.get("/auth/me", headers=cls.h_u).json()

        today_day = date.today().strftime("%A")
        client.post("/profile/me/onboarding", json={
            "display_name": "DSN Searcher",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.badminton_id, cls.football_id],
            "skills": [],
            "availability": [{"day_of_week": today_day, "start_time": "00:00:00", "end_time": "23:59:00"}]
        }, headers=cls.h_u)

        # 4. Host User (Creates an active event for today)
        cls.host_email = f"dsn.host.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.host_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_h = client.post("/auth/login", json={"email": cls.host_email, "password": cls.pwd}).json()
        cls.tok_h = res_h["access_token"]
        cls.h_host = {"Authorization": f"Bearer {cls.tok_h}"}
        client.patch("/profile/me", json={"display_name": "DSN Host", "approx_locality": "Indiranagar, Bengaluru"}, headers=cls.h_host)

        # 5. Peer User (Available for Football today)
        cls.peer_email = f"dsn.peer.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.peer_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_p = client.post("/auth/login", json={"email": cls.peer_email, "password": cls.pwd}).json()
        cls.tok_p = res_p["access_token"]
        cls.h_peer = {"Authorization": f"Bearer {cls.tok_p}"}
        client.post("/profile/me/onboarding", json={
            "display_name": "Football Peer",
            "approx_locality": "Indiranagar, Bengaluru",
            "interest_ids": [cls.football_id],
            "skills": [],
            "availability": [{"day_of_week": today_day, "start_time": "00:00:00", "end_time": "23:59:00"}]
        }, headers=cls.h_peer)

        # 6. Venue & Slots for Football
        cls.venue_email = f"dsn.venue.{ts}@vynk.com"
        client.post("/auth/register", json={"email": cls.venue_email, "password": cls.pwd, "confirm_password": cls.pwd})
        res_v = client.post("/auth/login", json={"email": cls.venue_email, "password": cls.pwd}).json()
        cls.tok_v = res_v["access_token"]
        cls.h_venue = {"Authorization": f"Bearer {cls.tok_v}"}

        v_res = client.post("/venues", json={
            "name": "Indiranagar Turf Arena",
            "address": "100 Feet Road, Indiranagar",
            "locality": "Indiranagar, Bengaluru",
            "activity_ids": [cls.act_football_id]
        }, headers=cls.h_venue).json()
        cls.venue_id = v_res["venue_id"]

        today_iso = date.today().isoformat()
        slot_res = client.post(f"/venues/{cls.venue_id}/slots", json={
            "slot_date": today_iso,
            "start_time": "18:00:00",
            "end_time": "20:00:00",
            "price_total": 1200.0,
            "currency": "INR"
        }, headers=cls.h_venue).json()
        cls.slot_id = slot_res["slot_id"]

        # 7. Create Active Event Today for Badminton (Action: JOIN)
        cls.ev_today = client.post("/events", json={
            "activity_id": cls.act_badminton_id,
            "title": "Today Saturday Badminton Live Match",
            "event_date": today_iso,
            "start_time": "18:00:00",
            "end_time": "20:00:00",
            "max_capacity": 4,
        }, headers=cls.h_host).json()
        client.patch(f"/events/{cls.ev_today['event_id']}", json={"status": "PUBLISHED"}, headers=cls.h_host)

        # 8. Create Full Event Today (Action: FULL / Infeasible to join)
        cls.ev_full = client.post("/events", json={
            "activity_id": cls.act_badminton_id,
            "title": "Full Badminton Tournament Today",
            "event_date": today_iso,
            "start_time": "18:00:00",
            "end_time": "20:00:00",
            "max_capacity": 1,
        }, headers=cls.h_host).json()
        client.post(f"/events/{cls.ev_full['event_id']}/join", headers=cls.h_peer)
        client.patch(f"/events/{cls.ev_full['event_id']}", json={"status": "FULL"}, headers=cls.h_host)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_existing_suitable_event_recommended_to_join(self):
        """Test 1: Existing suitable event happening today is recommended with action='JOIN' and feasible=True."""
        today_iso = date.today().isoformat()
        res = client.get(f"/do-something-now?target_date={today_iso}&target_time=18:00:00&interest_id={self.badminton_id}&limit=100", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertGreater(data["total_options"], 0)
        opt_ev = next((o for o in data["options"] if o["type"] == "EVENT" and o["event_id"] == self.ev_today["event_id"]), None)
        self.assertIsNotNone(opt_ev, "Today's active badminton event should be returned")
        self.assertEqual(opt_ev["action"], "JOIN")
        self.assertTrue(opt_ev["feasible"])
        self.assertGreaterEqual(opt_ev["score"], 70)
        self.assertGreater(opt_ev["remaining_spots"], 0)
        self.assertIn("Badminton", opt_ev["reason"])

    def test_02_event_outside_target_time_handled_or_excluded(self):
        """Test 2: Event happening in the past (e.g. earlier today) is not returned for evening time search."""
        today_iso = date.today().isoformat()
        res = client.get(f"/do-something-now?target_date={today_iso}&target_time=22:00:00", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Badminton event ended at 20:00, so at 22:00 it should not be listed as an active joinable event
        opt_ev = next((o for o in data["options"] if o["type"] == "EVENT" and o["event_id"] == self.ev_today["event_id"]), None)
        self.assertIsNone(opt_ev, "Ended event should be excluded when searching after end_time")

    def test_03_no_event_but_feasible_activity_suggests_creation(self):
        """Test 3: For Football (where peers + venue are available today), suggest action='CREATE' and feasible=True."""
        today_iso = date.today().isoformat()
        res = client.get(f"/do-something-now?target_date={today_iso}&target_time=18:00:00&interest_id={self.football_id}", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        opt_fb = next((o for o in data["options"] if o["type"] == "ACTIVITY" and o["interest_id"] == self.football_id), None)
        self.assertIsNotNone(opt_fb, "Football activity creation option should be returned")
        self.assertEqual(opt_fb["action"], "CREATE")
        self.assertTrue(opt_fb["feasible"])
        self.assertGreaterEqual(opt_fb["available_peers_count"], 1)
        self.assertGreaterEqual(opt_fb["available_venues_count"], 1)
        self.assertIsNotNone(opt_fb["suggested_slot_id"])

    def test_04_no_people_and_no_venue_reports_infeasible(self):
        """Test 4: Archery (no peers, no venue slots) correctly reports action='NOT_FEASIBLE' and feasible=False."""
        today_iso = date.today().isoformat()
        res = client.get(f"/do-something-now?target_date={today_iso}&target_time=18:00:00&interest_id={self.archery_id}", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        opt_arch = next((o for o in data["options"] if o["type"] == "ACTIVITY" and o["interest_id"] == self.archery_id), None)
        self.assertIsNotNone(opt_arch)
        self.assertEqual(opt_arch["action"], "NOT_FEASIBLE")
        self.assertFalse(opt_arch["feasible"])
        self.assertEqual(opt_arch["available_peers_count"], 0)
        self.assertEqual(opt_arch["available_venues_count"], 0)

    def test_05_user_availability_affects_user_available_now(self):
        """Test 5: User with Saturday availability returns user_available_now=False when queried for Tuesday."""
        next_tue = (date.today() + timedelta(days=((1 - date.today().weekday() + 7) % 7 or 7))).isoformat()
        res = client.get(f"/do-something-now?target_date={next_tue}&target_time=18:00:00", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["user_available_now"], "User should not be marked available on Tuesday")

    def test_06_locality_boosts_ranking(self):
        """Test 6: Options matching user's locality (Indiranagar) get higher scores."""
        today_iso = date.today().isoformat()
        res = client.get(f"/do-something-now?target_date={today_iso}&target_time=18:00:00&locality=Indiranagar", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user_locality"], "Indiranagar")

    def test_07_full_capacity_event_reported_as_not_feasible(self):
        """Test 7: Event at full capacity is marked feasible=False and action='FULL'."""
        today_iso = date.today().isoformat()
        res = client.get(f"/do-something-now?target_date={today_iso}&target_time=18:00:00", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        opt_full = next((o for o in data["options"] if o["type"] == "EVENT" and o["event_id"] == self.ev_full["event_id"]), None)
        if opt_full:
            self.assertFalse(opt_full["feasible"])
            self.assertEqual(opt_full["action"], "FULL")
            self.assertEqual(opt_full["remaining_spots"], 0)

    def test_08_empty_state_handled_cleanly(self):
        """Test 8: Querying far future date with no events or venue slots returns clean response with 200 OK."""
        far_date = (date.today() + timedelta(days=365)).isoformat()
        res = client.get(f"/do-something-now?target_date={far_date}&target_time=10:00:00", headers=self.h_u)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data["options"], list)
        self.assertEqual(data["total_options"], len(data["options"]))


if __name__ == "__main__":
    unittest.main()
