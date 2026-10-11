import json
import time
import unittest
from datetime import date, time as dt_time, timedelta
from unittest.mock import patch

from database import SessionLocal
import models
from main import (
    _compute_community_health,
    _compute_community_health_trend,
    _generate_community_action_recommendations,
    _generate_community_lifecycle_insight,
    app,
)
from auth import create_access_token
from fastapi.testclient import TestClient

client = TestClient(app)


class TestCommunityHealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.ts = int(time.time() * 1000)
        cls.pwd = "password123"

        # Unique interest & activity
        cls.interest = models.Interest(name=f"Health_Interest_{cls.ts}", category="Sports")
        cls.db.add(cls.interest)
        cls.db.commit()
        cls.db.refresh(cls.interest)

        cls.activity = models.Activity(
            title=f"Health Activity {cls.ts}",
            interest_id=cls.interest.interest_id,
        )
        cls.db.add(cls.activity)
        cls.db.commit()
        cls.db.refresh(cls.activity)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _create_user(self, email_prefix: str) -> models.User:
        email = f"{email_prefix}_{self.ts}_{time.time()}@test.com"
        client.post("/auth/register", json={"email": email, "password": self.pwd, "confirm_password": self.pwd})
        u = self.db.query(models.User).filter(models.User.email == email).first()
        prof = self.db.query(models.Profile).filter(models.Profile.user_id == u.user_id).first()
        prof.display_name = f"User {email_prefix}"
        prof.approx_locality = "Indiranagar, Bengaluru"
        self.db.commit()
        return u

    def test_healthy_community_calculation(self):
        """Test a vibrant, highly active community with recent events and reviews scores as HEALTHY."""
        creator = self._create_user("healthy_creator")
        comm = models.Community(name=f"Healthy_Comm_{self.ts}", description="Active club", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        # Add 10 members
        members = [creator]
        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        for i in range(9):
            u = self._create_user(f"healthy_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # Create 4 events (3 recent in last 10 days, all completed)
        today = date.today()
        for idx in range(4):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Healthy Event {idx}",
                event_date=today - timedelta(days=idx * 2),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=8,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)

            # Add 6 participants (~75% fill rate)
            for m in members[:6]:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            
            # Add reviews
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5, comment="Super!"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[2].user_id, rating=4, comment="Great!"))
            self.db.commit()

        metrics = _compute_community_health(comm, self.db)

        self.assertEqual(metrics["community_id"], comm.community_id)
        self.assertEqual(metrics["member_count"], 10)
        self.assertGreaterEqual(metrics["active_member_count"], 6)
        self.assertEqual(metrics["events_created"], 4)
        self.assertEqual(metrics["completed_events"], 4)
        self.assertGreaterEqual(metrics["recent_event_count"], 3)
        self.assertGreaterEqual(metrics["average_event_participation"], 70)
        self.assertGreaterEqual(metrics["average_feedback_rating"], 4.0)
        self.assertGreaterEqual(metrics["health_score"], 75)
        self.assertEqual(metrics["health_status"], "HEALTHY")

    def test_growing_community_calculation(self):
        """Test a developing community with emerging activity scores as GROWING."""
        creator = self._create_user("growing_creator")
        comm = models.Community(name=f"Growing_Comm_{self.ts}", description="Growing club", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        # 4 members
        members = [creator]
        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        for i in range(3):
            u = self._create_user(f"growing_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # 1 recent event
        ev = models.Event(
            activity_id=self.activity.activity_id,
            host_id=creator.user_id,
            title="Growing First Session",
            event_date=date.today() - timedelta(days=5),
            start_time=dt_time(18, 0),
            end_time=dt_time(20, 0),
            max_capacity=6,
            status="COMPLETED",
        )
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)

        for m in members[:3]:
            self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
        self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=4))
        self.db.commit()

        metrics = _compute_community_health(comm, self.db)

        self.assertGreaterEqual(metrics["health_score"], 50)
        self.assertLess(metrics["health_score"], 75)
        self.assertEqual(metrics["health_status"], "GROWING")

    def test_inactive_community_calculation(self):
        """Test a community with no events and no participation scores as INACTIVE."""
        creator = self._create_user("inactive_creator")
        comm = models.Community(name=f"Inactive_Comm_{self.ts}", description="Stale club", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        metrics = _compute_community_health(comm, self.db)

        self.assertEqual(metrics["events_created"], 0)
        self.assertEqual(metrics["completed_events"], 0)
        self.assertEqual(metrics["recent_event_count"], 0)
        self.assertEqual(metrics["average_event_participation"], 0)
        self.assertEqual(metrics["average_feedback_rating"], 0.0)
        self.assertLess(metrics["health_score"], 30)
        self.assertEqual(metrics["health_status"], "INACTIVE")

    def test_compute_by_community_id(self):
        """Verify _compute_community_health can be called directly with an integer ID."""
        creator = self._create_user("id_creator")
        comm = models.Community(name=f"ID_Comm_{self.ts}", description="Lookup by ID", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        metrics = _compute_community_health(comm.community_id, self.db)
        self.assertEqual(metrics["community_id"], comm.community_id)
        self.assertIn("health_score", metrics)
        self.assertIn("health_status", metrics)


    def _get_headers_for_user(self, user: models.User) -> dict:
        token = create_access_token(data={"sub": str(user.user_id)})
        return {"Authorization": f"Bearer {token}"}

    def test_member_can_retrieve_community_health(self):
        """1. Member can retrieve community health via GET /communities/{community_id}/health."""
        creator = self._create_user("api_member_creator")
        comm = models.Community(name=f"API_Member_Comm_{self.ts}", description="Member API Test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        res = client.get(f"/communities/{comm.community_id}/health", headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()

        self.assertEqual(data["community_id"], comm.community_id)
        self.assertIn("member_count", data)
        self.assertIn("health_score", data)
        self.assertIn("health_status", data)

    def test_non_member_is_rejected(self):
        """2. Non-member request to GET /communities/{community_id}/health is rejected with 403."""
        creator = self._create_user("api_non_member_owner")
        comm = models.Community(name=f"API_NonMember_Comm_{self.ts}", description="Private circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        outsider = self._create_user("api_outsider")
        outsider_headers = self._get_headers_for_user(outsider)

        res = client.get(f"/communities/{comm.community_id}/health", headers=outsider_headers)
        self.assertEqual(res.status_code, 403, res.text)
        self.assertIn("member of this community", res.json()["detail"])

    def test_missing_community_returns_404(self):
        """3. Missing community returns 404 Not Found."""
        creator = self._create_user("api_404_user")
        headers = self._get_headers_for_user(creator)

        res = client.get("/communities/99999999/health", headers=headers)
        self.assertEqual(res.status_code, 404, res.text)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_unauthenticated_request_is_rejected(self):
        """4. Unauthenticated request without JWT header is rejected with 401."""
        creator = self._create_user("api_unauth_creator")
        comm = models.Community(name=f"API_Unauth_Comm_{self.ts}", description="Protected", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        res = client.get(f"/communities/{comm.community_id}/health")
        self.assertEqual(res.status_code, 401, res.text)

    def test_health_response_matches_deterministic_calculation(self):
        """5. Health API response matches the direct internal deterministic calculation exactly."""
        creator = self._create_user("api_match_creator")
        comm = models.Community(name=f"API_Match_Comm_{self.ts}", description="Match test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        api_res = client.get(f"/communities/{comm.community_id}/health", headers=headers).json()
        direct_calc = _compute_community_health(comm, self.db)

        self.assertEqual(api_res["community_id"], direct_calc["community_id"])
        self.assertEqual(api_res["member_count"], direct_calc["member_count"])
        self.assertEqual(api_res["active_member_count"], direct_calc["active_member_count"])
        self.assertEqual(api_res["events_created"], direct_calc["events_created"])
        self.assertEqual(api_res["completed_events"], direct_calc["completed_events"])
        self.assertEqual(api_res["recent_event_count"], direct_calc["recent_event_count"])
        self.assertEqual(api_res["average_event_participation"], direct_calc["average_event_participation"])
        self.assertEqual(api_res["average_feedback_rating"], direct_calc["average_feedback_rating"])
        self.assertEqual(api_res["health_score"], direct_calc["health_score"])
        self.assertEqual(api_res["health_status"], direct_calc["health_status"])

    def test_trend_improving(self):
        """Verify _compute_community_health_trend identifies IMPROVING when recent activity exceeds previous period."""
        creator = self._create_user("trend_imp_creator")
        comm = models.Community(name=f"Trend_Imp_Comm_{self.ts}", description="Improving circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        # Add 5 members
        members = [creator]
        for i in range(4):
            u = self._create_user(f"trend_imp_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # In current period (e.g. 5 days ago): 3 completed events with full attendance
        today = date.today()
        for idx in range(3):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Recent Event {idx}",
                event_date=today - timedelta(days=idx * 2 + 2),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)

            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5, comment="Awesome!"))
            self.db.commit()

        trend_res = _compute_community_health_trend(comm, self.db, window_days=30)

        self.assertEqual(trend_res["community_id"], comm.community_id)
        self.assertGreaterEqual(trend_res["current_health_score"], 70)
        self.assertLess(trend_res["previous_health_score"], 30)
        self.assertGreaterEqual(trend_res["score_change"], 10)
        self.assertEqual(trend_res["trend"], "IMPROVING")
        self.assertIn("metrics_comparison", trend_res)

    def test_trend_declining(self):
        """Verify _compute_community_health_trend identifies DECLINING when activity dropped compared to previous period."""
        creator = self._create_user("trend_dec_creator")
        comm = models.Community(name=f"Trend_Dec_Comm_{self.ts}", description="Declining circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"trend_dec_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # In previous period (e.g. 45 days ago): 3 completed events with full attendance
        today = date.today()
        for idx in range(3):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Old Event {idx}",
                event_date=today - timedelta(days=40 + idx * 2),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)

            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        trend_res = _compute_community_health_trend(comm, self.db, window_days=30)

        self.assertEqual(trend_res["community_id"], comm.community_id)
        self.assertLess(trend_res["current_health_score"], 30)
        self.assertGreaterEqual(trend_res["previous_health_score"], 70)
        self.assertLessEqual(trend_res["score_change"], -10)
        self.assertEqual(trend_res["trend"], "DECLINING")

    def test_trend_stable(self):
        """Verify _compute_community_health_trend identifies STABLE when activity change is between -10 and +10."""
        creator = self._create_user("trend_stb_creator")
        comm = models.Community(name=f"Trend_Stb_Comm_{self.ts}", description="Stable circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        trend_res = _compute_community_health_trend(comm, self.db, window_days=30)

        self.assertEqual(trend_res["community_id"], comm.community_id)
        self.assertLess(abs(trend_res["score_change"]), 10)
        self.assertEqual(trend_res["trend"], "STABLE")

    def test_member_can_retrieve_health_trend(self):
        """1. Member can retrieve community health trend via GET /communities/{community_id}/health/trend."""
        creator = self._create_user("api_trend_creator")
        comm = models.Community(name=f"API_Trend_Comm_{self.ts}", description="Trend API Test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        res = client.get(f"/communities/{comm.community_id}/health/trend", headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()

        self.assertEqual(data["community_id"], comm.community_id)
        self.assertIn("current_health_score", data)
        self.assertIn("previous_health_score", data)
        self.assertIn("score_change", data)
        self.assertIn("trend", data)
        self.assertIn("metrics_comparison", data)
        self.assertIn("active_members", data["metrics_comparison"])

    def test_non_member_trend_is_rejected(self):
        """2. Non-member request to GET /communities/{community_id}/health/trend is rejected with 403."""
        creator = self._create_user("api_trend_owner")
        comm = models.Community(name=f"API_Trend_NonMem_{self.ts}", description="Private", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        outsider = self._create_user("api_trend_outsider")
        outsider_headers = self._get_headers_for_user(outsider)

        res = client.get(f"/communities/{comm.community_id}/health/trend", headers=outsider_headers)
        self.assertEqual(res.status_code, 403, res.text)
        self.assertIn("member of this community", res.json()["detail"])

    def test_missing_community_trend_returns_404(self):
        """3. Missing community returns 404 for trend."""
        creator = self._create_user("api_trend_404_user")
        headers = self._get_headers_for_user(creator)

        res = client.get("/communities/99999999/health/trend", headers=headers)
        self.assertEqual(res.status_code, 404, res.text)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_unauthenticated_trend_is_rejected(self):
        """4. Unauthenticated request to trend endpoint returns 401."""
        creator = self._create_user("api_trend_unauth")
        comm = models.Community(name=f"API_Trend_Unauth_{self.ts}", description="Protected", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        res = client.get(f"/communities/{comm.community_id}/health/trend")
        self.assertEqual(res.status_code, 401, res.text)

    def test_trend_api_matches_deterministic_calculation(self):
        """5. Health trend API output exactly matches internal _compute_community_health_trend calculation."""
        creator = self._create_user("api_trend_match")
        comm = models.Community(name=f"API_Trend_Match_{self.ts}", description="Match", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        api_res = client.get(f"/communities/{comm.community_id}/health/trend?window_days=30", headers=headers).json()
        direct_calc = _compute_community_health_trend(comm, self.db, window_days=30)

        self.assertEqual(api_res["community_id"], direct_calc["community_id"])
        self.assertEqual(api_res["current_health_score"], direct_calc["current_health_score"])
        self.assertEqual(api_res["previous_health_score"], direct_calc["previous_health_score"])
        self.assertEqual(api_res["score_change"], direct_calc["score_change"])
        self.assertEqual(api_res["trend"], direct_calc["trend"])
        self.assertEqual(api_res["current_status"], direct_calc["current_status"])
        self.assertEqual(api_res["previous_status"], direct_calc["previous_status"])
        self.assertEqual(api_res["metrics_comparison"], direct_calc["metrics_comparison"])

    def test_lifecycle_insight_healthy_improving(self):
        """1. Healthy + improving -> appropriate lifecycle insight."""
        creator = self._create_user("lc_hi_creator")
        comm = models.Community(name=f"LC_HI_Comm_{self.ts}", description="Thriving community", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"lc_hi_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # Add 3 completed events with high attendance in current period
        today = date.today()
        for idx in range(3):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"LC HI Event {idx}",
                event_date=today - timedelta(days=idx * 2 + 1),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5, comment="Super!"))
            self.db.commit()

        insight = _generate_community_lifecycle_insight(comm, self.db, window_days=30)
        self.assertEqual(insight["community_id"], comm.community_id)
        self.assertEqual(insight["health_status"], "HEALTHY")
        self.assertEqual(insight["trend"], "IMPROVING")
        self.assertIn(insight["lifecycle_stage"], ["GROWING", "HEALTHY"])
        self.assertTrue(len(insight["insight"]) > 10)
        self.assertTrue(len(insight["recommended_focus"]) > 10)
        self.assertTrue(any(w in insight["insight"].lower() for w in ["active", "increas", "grow", "participat", "momentum", "thriv"]))

    def test_lifecycle_insight_healthy_stable(self):
        """2. Healthy + stable -> appropriate insight."""
        creator = self._create_user("lc_hs_creator")
        comm = models.Community(name=f"LC_HS_Comm_{self.ts}", description="Consistent circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"lc_hs_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # Both current period and previous period have 2 events with high attendance
        today = date.today()
        for idx in range(2):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"LC HS Curr Event {idx}",
                event_date=today - timedelta(days=idx * 3 + 2),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        for idx in range(2):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"LC HS Prev Event {idx}",
                event_date=today - timedelta(days=40 + idx * 3),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        insight = _generate_community_lifecycle_insight(comm, self.db, window_days=30)
        self.assertEqual(insight["community_id"], comm.community_id)
        self.assertEqual(insight["health_status"], "HEALTHY")
        self.assertEqual(insight["trend"], "STABLE")
        self.assertEqual(insight["lifecycle_stage"], "HEALTHY")
        self.assertTrue(len(insight["insight"]) > 10)
        self.assertTrue(len(insight["recommended_focus"]) > 10)
        self.assertTrue(any(w in insight["insight"].lower() for w in ["consist", "reliab", "stable", "maintain", "health"]))

    def test_lifecycle_insight_at_risk_declining(self):
        """3. At-risk + declining -> risk-focused insight."""
        creator = self._create_user("lc_ard_creator")
        comm = models.Community(name=f"LC_ARD_Comm_{self.ts}", description="Dipping community", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"lc_ard_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # Activity in previous window, 0 events in current window
        today = date.today()
        for idx in range(3):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"LC ARD Prev Event {idx}",
                event_date=today - timedelta(days=40 + idx * 3),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        insight = _generate_community_lifecycle_insight(comm, self.db, window_days=30)
        self.assertEqual(insight["community_id"], comm.community_id)
        self.assertEqual(insight["trend"], "DECLINING")
        self.assertIn(insight["lifecycle_stage"], ["AT_RISK", "INACTIVE"])
        self.assertTrue(len(insight["insight"]) > 10)
        self.assertTrue(any(w in insight["insight"].lower() for w in ["declin", "risk", "disengag", "dormant", "decreas"]))
        self.assertTrue(any(w in insight["recommended_focus"].lower() for w in ["poll", "re-engag", "reactivat", "outreach", "meetup"]))

    def test_lifecycle_insight_inactive(self):
        """4. Inactive -> reactivation-focused insight."""
        creator = self._create_user("lc_inact_creator")
        comm = models.Community(name=f"LC_Inact_Comm_{self.ts}", description="Dormant circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        insight = _generate_community_lifecycle_insight(comm, self.db, window_days=30)
        self.assertEqual(insight["community_id"], comm.community_id)
        self.assertEqual(insight["health_status"], "INACTIVE")
        self.assertIn(insight["lifecycle_stage"], ["INACTIVE", "NEW"])
        self.assertTrue(len(insight["insight"]) > 10)
        self.assertTrue(any(w in insight["recommended_focus"].lower() for w in ["kickoff", "reactivat", "poll", "reboot", "founding"]))

    def test_lifecycle_insight_ai_failure_fallback(self):
        """5. AI failure -> deterministic fallback."""
        creator = self._create_user("lc_fail_creator")
        comm = models.Community(name=f"LC_Fail_Comm_{self.ts}", description="Fallback test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        with patch("ai_service.httpx.Client.post", side_effect=Exception("OpenAI API unreachable")):
            insight = _generate_community_lifecycle_insight(comm, self.db, window_days=30)

        self.assertEqual(insight["community_id"], comm.community_id)
        self.assertIn(insight["lifecycle_stage"], ["NEW", "GROWING", "HEALTHY", "AT_RISK", "INACTIVE"])
        self.assertTrue(len(insight["insight"]) > 0)
        self.assertTrue(len(insight["recommended_focus"]) > 0)

    def test_lifecycle_insight_invalid_ai_output_fallback(self):
        """6. Invalid AI output -> rejected/fallback to deterministic."""
        creator = self._create_user("lc_invalid_creator")
        comm = models.Community(name=f"LC_Invalid_Comm_{self.ts}", description="Invalid AI test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        invalid_mock_response = unittest.mock.MagicMock()
        invalid_mock_response.status_code = 200
        invalid_mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "lifecycle_stage": "SUPER_DUPER_UNKNOWN",
                        "insight": "",
                        "recommended_focus": ""
                    })
                }
            }]
        }

        with patch("ai_service.httpx.Client.post", return_value=invalid_mock_response):
            insight = _generate_community_lifecycle_insight(comm, self.db, window_days=30)

        self.assertEqual(insight["community_id"], comm.community_id)
        self.assertIn(insight["lifecycle_stage"], ["NEW", "GROWING", "HEALTHY", "AT_RISK", "INACTIVE"])
        self.assertNotEqual(insight["lifecycle_stage"], "SUPER_DUPER_UNKNOWN")
        self.assertTrue(len(insight["insight"]) > 0)
        self.assertTrue(len(insight["recommended_focus"]) > 0)

    def test_lifecycle_insight_no_database_mutation(self):
        """7. No database mutation occurs during insight generation."""
        creator = self._create_user("lc_nomut_creator")
        comm = models.Community(name=f"LC_NoMut_Comm_{self.ts}", description="Read-only check", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        c_count_before = self.db.query(models.Community).count()
        m_count_before = self.db.query(models.CommunityMember).count()
        e_count_before = self.db.query(models.Event).count()
        p_count_before = self.db.query(models.EventParticipant).count()
        f_count_before = self.db.query(models.Feedback).count()

        _ = _generate_community_lifecycle_insight(comm, self.db, window_days=30)

        self.assertEqual(self.db.query(models.Community).count(), c_count_before)
        self.assertEqual(self.db.query(models.CommunityMember).count(), m_count_before)
        self.assertEqual(self.db.query(models.Event).count(), e_count_before)
        self.assertEqual(self.db.query(models.EventParticipant).count(), p_count_before)
        self.assertEqual(self.db.query(models.Feedback).count(), f_count_before)

    def test_lifecycle_api_member_access(self):
        """1. Community member can retrieve lifecycle insight via GET /communities/{community_id}/lifecycle -> 200."""
        creator = self._create_user("api_lc_member")
        comm = models.Community(name=f"API_LC_Mem_{self.ts}", description="Lifecycle member test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        res = client.get(f"/communities/{comm.community_id}/lifecycle", headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()

        self.assertEqual(data["community_id"], comm.community_id)
        self.assertIn("health_score", data)
        self.assertIn("health_status", data)
        self.assertIn("trend", data)
        self.assertIn("score_change", data)
        self.assertIn("lifecycle_stage", data)
        self.assertIn("insight", data)
        self.assertIn("recommended_focus", data)

    def test_lifecycle_api_non_member_rejected(self):
        """2. Non-member request to GET /communities/{community_id}/lifecycle is rejected with 403."""
        creator = self._create_user("api_lc_owner")
        comm = models.Community(name=f"API_LC_NonMem_{self.ts}", description="Private circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        outsider = self._create_user("api_lc_outsider")
        outsider_headers = self._get_headers_for_user(outsider)

        res = client.get(f"/communities/{comm.community_id}/lifecycle", headers=outsider_headers)
        self.assertEqual(res.status_code, 403, res.text)
        self.assertIn("member of this community", res.json()["detail"])

    def test_lifecycle_api_missing_community_returns_404(self):
        """3. Missing community returns 404 for lifecycle endpoint."""
        creator = self._create_user("api_lc_404_user")
        headers = self._get_headers_for_user(creator)

        res = client.get("/communities/99999999/lifecycle", headers=headers)
        self.assertEqual(res.status_code, 404, res.text)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_lifecycle_api_unauthenticated_rejected(self):
        """4. Unauthenticated request to lifecycle endpoint returns 401."""
        creator = self._create_user("api_lc_unauth")
        comm = models.Community(name=f"API_LC_Unauth_{self.ts}", description="Protected", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        res = client.get(f"/communities/{comm.community_id}/lifecycle")
        self.assertEqual(res.status_code, 401, res.text)

    def test_lifecycle_api_facts_match_deterministic_calculations(self):
        """5. API facts exactly match deterministic health/trend calculations."""
        creator = self._create_user("api_lc_match")
        comm = models.Community(name=f"API_LC_Match_{self.ts}", description="Match test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        api_res = client.get(f"/communities/{comm.community_id}/lifecycle?window_days=30", headers=headers).json()
        direct_health = _compute_community_health(comm, self.db)
        direct_trend = _compute_community_health_trend(comm, self.db, window_days=30)

        self.assertEqual(api_res["community_id"], comm.community_id)
        self.assertEqual(api_res["health_score"], direct_health["health_score"])
        self.assertEqual(api_res["health_status"], direct_health["health_status"])
        self.assertEqual(api_res["trend"], direct_trend["trend"])
        self.assertEqual(api_res["score_change"], direct_trend["score_change"])

    def test_lifecycle_api_ai_failure_fallback(self):
        """6. AI failure in API endpoint still returns the deterministic fallback."""
        creator = self._create_user("api_lc_ai_fail")
        comm = models.Community(name=f"API_LC_AIFail_{self.ts}", description="API Fallback test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        with patch("ai_service.httpx.Client.post", side_effect=Exception("OpenAI timeout")):
            res = client.get(f"/communities/{comm.community_id}/lifecycle", headers=headers)

        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["community_id"], comm.community_id)
        self.assertIn(data["lifecycle_stage"], ["NEW", "GROWING", "HEALTHY", "AT_RISK", "INACTIVE"])
        self.assertTrue(len(data["insight"]) > 0)
        self.assertTrue(len(data["recommended_focus"]) > 0)

    def test_lifecycle_api_no_database_mutation(self):
        """7. Verify the lifecycle endpoint does not mutate the database."""
        creator = self._create_user("api_lc_nomut")
        comm = models.Community(name=f"API_LC_NoMut_{self.ts}", description="No mut test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)

        c_count_before = self.db.query(models.Community).count()
        m_count_before = self.db.query(models.CommunityMember).count()
        e_count_before = self.db.query(models.Event).count()
        p_count_before = self.db.query(models.EventParticipant).count()
        f_count_before = self.db.query(models.Feedback).count()

        res = client.get(f"/communities/{comm.community_id}/lifecycle", headers=headers)
        self.assertEqual(res.status_code, 200, res.text)

        self.assertEqual(self.db.query(models.Community).count(), c_count_before)
        self.assertEqual(self.db.query(models.CommunityMember).count(), m_count_before)
        self.assertEqual(self.db.query(models.Event).count(), e_count_before)
        self.assertEqual(self.db.query(models.EventParticipant).count(), p_count_before)
        self.assertEqual(self.db.query(models.Feedback).count(), f_count_before)

    def test_action_recs_growing_improving(self):
        """1. Growing/improving community -> growth/activity recommendations (CREATE_EVENT / GROW_MEMBERSHIP)."""
        creator = self._create_user("act_grow_creator")
        comm = models.Community(name=f"Act_Grow_Comm_{self.ts}", description="Growing circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"act_grow_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        today = date.today()
        for idx in range(3):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Act Grow Event {idx}",
                event_date=today - timedelta(days=idx * 2 + 1),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        res = _generate_community_action_recommendations(comm, self.db, window_days=30)
        self.assertEqual(res["community_id"], comm.community_id)
        self.assertTrue(len(res["recommendations"]) >= 1)

        actions = [r["action"] for r in res["recommendations"]]
        self.assertTrue(any(a in ["CREATE_EVENT", "GROW_MEMBERSHIP"] for a in actions))
        for r in res["recommendations"]:
            self.assertIn(r["priority"], ["HIGH", "MEDIUM", "LOW"])
            self.assertTrue(len(r["title"]) > 0)
            self.assertTrue(len(r["reason"]) > 0)
            self.assertTrue(len(r["suggested_next_step"]) > 0)

    def test_action_recs_healthy_stable(self):
        """2. Healthy/stable community -> maintenance recommendation (MAINTAIN_ACTIVITY)."""
        creator = self._create_user("act_hs_creator")
        comm = models.Community(name=f"Act_HS_Comm_{self.ts}", description="Consistent healthy", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"act_hs_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        today = date.today()
        # Current period (2 events)
        for idx in range(2):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Act HS Curr {idx}",
                event_date=today - timedelta(days=idx * 3 + 2),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        # Previous period (2 events)
        for idx in range(2):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Act HS Prev {idx}",
                event_date=today - timedelta(days=40 + idx * 3),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        res = _generate_community_action_recommendations(comm, self.db, window_days=30)
        self.assertEqual(res["community_id"], comm.community_id)
        actions = [r["action"] for r in res["recommendations"]]
        self.assertIn("MAINTAIN_ACTIVITY", actions)

    def test_action_recs_at_risk_declining(self):
        """3. At-risk/declining community -> re-engagement recommendation (RE_ENGAGE_MEMBERS)."""
        creator = self._create_user("act_ard_creator")
        comm = models.Community(name=f"Act_ARD_Comm_{self.ts}", description="Dipping cohort", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        members = [creator]
        for i in range(4):
            u = self._create_user(f"act_ard_m_{i}")
            members.append(u)
            self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=u.user_id, role="MEMBER"))
        self.db.commit()

        # Previous period had 3 events, current period has 0 events
        today = date.today()
        for idx in range(3):
            ev = models.Event(
                activity_id=self.activity.activity_id,
                host_id=creator.user_id,
                title=f"Act ARD Prev {idx}",
                event_date=today - timedelta(days=40 + idx * 3),
                start_time=dt_time(18, 0),
                end_time=dt_time(20, 0),
                max_capacity=5,
                status="COMPLETED",
            )
            self.db.add(ev)
            self.db.commit()
            self.db.refresh(ev)
            for m in members:
                self.db.add(models.EventParticipant(event_id=ev.event_id, user_id=m.user_id, status="CONFIRMED"))
            self.db.add(models.Feedback(event_id=ev.event_id, reviewer_id=members[1].user_id, rating=5))
            self.db.commit()

        res = _generate_community_action_recommendations(comm, self.db, window_days=30)
        self.assertEqual(res["community_id"], comm.community_id)
        actions = [r["action"] for r in res["recommendations"]]
        self.assertIn("RE_ENGAGE_MEMBERS", actions)
        high_prio = [r for r in res["recommendations"] if r["priority"] == "HIGH"]
        self.assertTrue(any(r["action"] == "RE_ENGAGE_MEMBERS" for r in high_prio))

    def test_action_recs_inactive(self):
        """4. Inactive community -> reactivation recommendation (REACTIVATE_COMMUNITY)."""
        creator = self._create_user("act_inact_creator")
        comm = models.Community(name=f"Act_Inact_Comm_{self.ts}", description="Dormant circle", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        res = _generate_community_action_recommendations(comm, self.db, window_days=30)
        self.assertEqual(res["community_id"], comm.community_id)
        actions = [r["action"] for r in res["recommendations"]]
        self.assertTrue(any(a in ["REACTIVATE_COMMUNITY", "CREATE_EVENT", "GROW_MEMBERSHIP"] for a in actions))

    def test_action_recs_ai_failure_fallback(self):
        """5. AI failure -> deterministic fallback recommendations."""
        creator = self._create_user("act_fail_creator")
        comm = models.Community(name=f"Act_Fail_Comm_{self.ts}", description="Fallback test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        with patch("ai_service.httpx.Client.post", side_effect=Exception("OpenAI connection timeout")):
            res = _generate_community_action_recommendations(comm, self.db, window_days=30)

        self.assertEqual(res["community_id"], comm.community_id)
        self.assertTrue(len(res["recommendations"]) > 0)
        for r in res["recommendations"]:
            self.assertIn(r["priority"], ["HIGH", "MEDIUM", "LOW"])
            self.assertIn(r["action"], ["CREATE_EVENT", "RE_ENGAGE_MEMBERS", "COLLECT_FEEDBACK", "GROW_MEMBERSHIP", "MAINTAIN_ACTIVITY", "REACTIVATE_COMMUNITY"])

    def test_action_recs_invalid_ai_action_fallback(self):
        """6. Invalid AI action -> fallback / rejection to controlled enum."""
        creator = self._create_user("act_inv_creator")
        comm = models.Community(name=f"Act_Inv_Comm_{self.ts}", description="Invalid action test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        invalid_mock_response = unittest.mock.MagicMock()
        invalid_mock_response.status_code = 200
        invalid_mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendations": [
                            {
                                "priority": "ULTRA_HIGH",
                                "action": "DELETE_EVERYTHING_NOW",
                                "title": "Invalid title",
                                "reason": "Invalid reason",
                                "suggested_next_step": "Invalid step"
                            }
                        ]
                    })
                }
            }]
        }

        with patch("ai_service.httpx.Client.post", return_value=invalid_mock_response):
            res = _generate_community_action_recommendations(comm, self.db, window_days=30)

        self.assertEqual(res["community_id"], comm.community_id)
        actions = [r["action"] for r in res["recommendations"]]
        self.assertNotIn("DELETE_EVERYTHING_NOW", actions)
        for r in res["recommendations"]:
            self.assertIn(r["action"], ["CREATE_EVENT", "RE_ENGAGE_MEMBERS", "COLLECT_FEEDBACK", "GROW_MEMBERSHIP", "MAINTAIN_ACTIVITY", "REACTIVATE_COMMUNITY"])
            self.assertIn(r["priority"], ["HIGH", "MEDIUM", "LOW"])

    def test_action_recs_no_invented_numerical_facts(self):
        """7. Recommendations contain no unverified numerical metric overrides."""
        creator = self._create_user("act_facts_creator")
        comm = models.Community(name=f"Act_Facts_Comm_{self.ts}", description="Factual integrity", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        res = _generate_community_action_recommendations(comm, self.db, window_days=30)
        self.assertEqual(res["community_id"], comm.community_id)
        # Verify schema integrity - only structured actionable fields are returned
        for r in res["recommendations"]:
            self.assertSetEqual(set(r.keys()), {"priority", "action", "title", "reason", "suggested_next_step"})

    def test_action_recs_no_database_mutation(self):
        """8. Generating action recommendations does not mutate the database."""
        creator = self._create_user("act_nomut_creator")
        comm = models.Community(name=f"Act_NoMut_Comm_{self.ts}", description="No mutation check", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        c_count_before = self.db.query(models.Community).count()
        m_count_before = self.db.query(models.CommunityMember).count()
        e_count_before = self.db.query(models.Event).count()
        p_count_before = self.db.query(models.EventParticipant).count()
        f_count_before = self.db.query(models.Feedback).count()

        _ = _generate_community_action_recommendations(comm, self.db, window_days=30)

        self.assertEqual(self.db.query(models.Community).count(), c_count_before)
        self.assertEqual(self.db.query(models.CommunityMember).count(), m_count_before)
        self.assertEqual(self.db.query(models.Event).count(), e_count_before)
        self.assertEqual(self.db.query(models.EventParticipant).count(), p_count_before)
        self.assertEqual(self.db.query(models.Feedback).count(), f_count_before)

    def test_recs_api_member_access(self):
        """1. Member can retrieve recommendations via GET /communities/{community_id}/recommendations -> 200."""
        creator = self._create_user("api_rec_member")
        comm = models.Community(name=f"API_Rec_Mem_{self.ts}", description="Recommendations test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        res = client.get(f"/communities/{comm.community_id}/recommendations", headers=headers)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()

        self.assertEqual(data["community_id"], comm.community_id)
        self.assertIn("recommendations", data)
        self.assertTrue(len(data["recommendations"]) >= 1)
        for r in data["recommendations"]:
            self.assertIn(r["priority"], ["HIGH", "MEDIUM", "LOW"])
            self.assertIn(r["action"], ["CREATE_EVENT", "RE_ENGAGE_MEMBERS", "COLLECT_FEEDBACK", "GROW_MEMBERSHIP", "MAINTAIN_ACTIVITY", "REACTIVATE_COMMUNITY"])
            self.assertTrue(len(r["title"]) > 0)
            self.assertTrue(len(r["reason"]) > 0)
            self.assertTrue(len(r["suggested_next_step"]) > 0)

    def test_recs_api_non_member_rejected(self):
        """2. Non-member request to GET /communities/{community_id}/recommendations is rejected with 403."""
        creator = self._create_user("api_rec_owner")
        comm = models.Community(name=f"API_Rec_NonMem_{self.ts}", description="Private community", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        outsider = self._create_user("api_rec_outsider")
        outsider_headers = self._get_headers_for_user(outsider)

        res = client.get(f"/communities/{comm.community_id}/recommendations", headers=outsider_headers)
        self.assertEqual(res.status_code, 403, res.text)
        self.assertIn("member of this community", res.json()["detail"])

    def test_recs_api_missing_community_returns_404(self):
        """3. Missing community returns 404 for recommendations endpoint."""
        creator = self._create_user("api_rec_404_user")
        headers = self._get_headers_for_user(creator)

        res = client.get("/communities/99999999/recommendations", headers=headers)
        self.assertEqual(res.status_code, 404, res.text)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_recs_api_unauthenticated_rejected(self):
        """4. Unauthenticated request to recommendations endpoint returns 401."""
        creator = self._create_user("api_rec_unauth")
        comm = models.Community(name=f"API_Rec_Unauth_{self.ts}", description="Protected", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        res = client.get(f"/communities/{comm.community_id}/recommendations")
        self.assertEqual(res.status_code, 401, res.text)

    def test_recs_api_matches_recommendation_engine(self):
        """5. API output exactly matches internal _generate_community_action_recommendations calculation."""
        creator = self._create_user("api_rec_match")
        comm = models.Community(name=f"API_Rec_Match_{self.ts}", description="Match test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        api_res = client.get(f"/communities/{comm.community_id}/recommendations?window_days=30", headers=headers).json()
        direct_calc = _generate_community_action_recommendations(comm, self.db, window_days=30)

        self.assertEqual(api_res["community_id"], direct_calc["community_id"])
        self.assertEqual(len(api_res["recommendations"]), len(direct_calc["recommendations"]))
        self.assertEqual(
            [r["action"] for r in api_res["recommendations"]],
            [r["action"] for r in direct_calc["recommendations"]]
        )

    def test_recs_api_ai_failure_fallback(self):
        """6. AI failure in recommendations endpoint still produces valid fallback recommendations."""
        creator = self._create_user("api_rec_ai_fail")
        comm = models.Community(name=f"API_Rec_AIFail_{self.ts}", description="API Fallback test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)
        with patch("ai_service.httpx.Client.post", side_effect=Exception("OpenAI timeout")):
            res = client.get(f"/communities/{comm.community_id}/recommendations", headers=headers)

        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["community_id"], comm.community_id)
        self.assertTrue(len(data["recommendations"]) > 0)
        for r in data["recommendations"]:
            self.assertIn(r["priority"], ["HIGH", "MEDIUM", "LOW"])
            self.assertIn(r["action"], ["CREATE_EVENT", "RE_ENGAGE_MEMBERS", "COLLECT_FEEDBACK", "GROW_MEMBERSHIP", "MAINTAIN_ACTIVITY", "REACTIVATE_COMMUNITY"])

    def test_recs_api_invalid_ai_action_rejected(self):
        """7. Invalid AI action in recommendations endpoint remains rejected and sanitized."""
        creator = self._create_user("api_rec_invalid")
        comm = models.Community(name=f"API_Rec_Invalid_{self.ts}", description="Invalid AI test", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)

        invalid_mock_response = unittest.mock.MagicMock()
        invalid_mock_response.status_code = 200
        invalid_mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendations": [
                            {
                                "priority": "CRITICAL_OVERKILL",
                                "action": "UNAUTHORIZED_ARBITRARY_ACTION",
                                "title": "Bypass Test",
                                "reason": "Testing sanitization",
                                "suggested_next_step": "None"
                            }
                        ]
                    })
                }
            }]
        }

        with patch("ai_service.httpx.Client.post", return_value=invalid_mock_response):
            res = client.get(f"/communities/{comm.community_id}/recommendations", headers=headers)

        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        actions = [r["action"] for r in data["recommendations"]]
        self.assertNotIn("UNAUTHORIZED_ARBITRARY_ACTION", actions)
        for r in data["recommendations"]:
            self.assertIn(r["priority"], ["HIGH", "MEDIUM", "LOW"])
            self.assertIn(r["action"], ["CREATE_EVENT", "RE_ENGAGE_MEMBERS", "COLLECT_FEEDBACK", "GROW_MEMBERSHIP", "MAINTAIN_ACTIVITY", "REACTIVATE_COMMUNITY"])

    def test_recs_api_no_database_mutation(self):
        """8. Endpoint causes zero database mutations."""
        creator = self._create_user("api_rec_nomut")
        comm = models.Community(name=f"API_Rec_NoMut_{self.ts}", description="No mutation check", created_by=creator.user_id)
        self.db.add(comm)
        self.db.commit()
        self.db.refresh(comm)

        self.db.add(models.CommunityMember(community_id=comm.community_id, user_id=creator.user_id, role="ADMIN"))
        self.db.commit()

        headers = self._get_headers_for_user(creator)

        c_count_before = self.db.query(models.Community).count()
        m_count_before = self.db.query(models.CommunityMember).count()
        e_count_before = self.db.query(models.Event).count()
        p_count_before = self.db.query(models.EventParticipant).count()
        f_count_before = self.db.query(models.Feedback).count()

        res = client.get(f"/communities/{comm.community_id}/recommendations", headers=headers)
        self.assertEqual(res.status_code, 200, res.text)

        self.assertEqual(self.db.query(models.Community).count(), c_count_before)
        self.assertEqual(self.db.query(models.CommunityMember).count(), m_count_before)
        self.assertEqual(self.db.query(models.Event).count(), e_count_before)
        self.assertEqual(self.db.query(models.EventParticipant).count(), p_count_before)
        self.assertEqual(self.db.query(models.Feedback).count(), f_count_before)


if __name__ == "__main__":
    unittest.main()



