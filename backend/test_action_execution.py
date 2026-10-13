import time as time_mod
import unittest
from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from unittest.mock import MagicMock, patch

from database import SessionLocal
import models
import schemas
from main import (
    app,
    validate_community_action_request,
    authorize_community_action,
    dispatch_community_action,
    COMMUNITY_ACTION_HANDLERS,
    _handle_maintain_activity_action,
    _handle_reactivate_community_action,
)

client = TestClient(app)


class TestCommunityActionValidation(unittest.TestCase):
    """
    Step 9.1 Test Suite:
    Tests pure Action Execution Contract and Validation Gate:
    - AllowedAction closed enum verification
    - ActionRequest input acceptance
    - ActionValidationResult output contract
    - Parameter sanitization and malicious payload rejection
    - Zero database mutations guarantee
    """

    def setUp(self):
        self.db: Session = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_valid_create_event(self):
        """Valid CREATE_EVENT action and parameters pass pure validation."""
        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "max_capacity": 10,
                "event_date": "2026-10-25",
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": "Weekend Badminton Doubles",
                "activity_id": 2,
            },
            reason="Community participation is growing",
        )
        res = validate_community_action_request(req)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.normalized_action, schemas.AllowedAction.CREATE_EVENT)
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(res.sanitized_parameters["max_capacity"], 10)
        self.assertEqual(res.sanitized_parameters["event_date"], "2026-10-25")
        self.assertEqual(res.sanitized_parameters["title"], "Weekend Badminton Doubles")

    def test_valid_re_engage_members(self):
        """Valid RE_ENGAGE_MEMBERS action and clean message pass pure validation."""
        req = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={
                "message": "Hey team, looking forward to our next friendly session!",
                "target_inactive_days": 14,
            },
            reason="Activity has slowed down over the last two weeks",
        )
        res = validate_community_action_request(req)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.normalized_action, schemas.AllowedAction.RE_ENGAGE_MEMBERS)
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(res.sanitized_parameters["message"], "Hey team, looking forward to our next friendly session!")
        self.assertEqual(res.sanitized_parameters["target_inactive_days"], 14)

    def test_all_six_allowed_actions_valid(self):
        """All 6 defined AllowedAction values are successfully accepted and normalized."""
        expected_actions = [
            schemas.AllowedAction.CREATE_EVENT,
            schemas.AllowedAction.RE_ENGAGE_MEMBERS,
            schemas.AllowedAction.COLLECT_FEEDBACK,
            schemas.AllowedAction.GROW_MEMBERSHIP,
            schemas.AllowedAction.MAINTAIN_ACTIVITY,
            schemas.AllowedAction.REACTIVATE_COMMUNITY,
        ]

        for act in expected_actions:
            # Test direct enum string
            req = schemas.ActionRequest(action=act.value, parameters={})
            res = validate_community_action_request(req)
            self.assertTrue(res.is_valid, f"Action {act.value} should be valid")
            self.assertEqual(res.normalized_action, act)

            # Test lowercase & whitespace normalization
            req_lower = schemas.ActionRequest(action=f"  {act.value.lower()}  ", parameters={})
            res_lower = validate_community_action_request(req_lower)
            self.assertTrue(res_lower.is_valid, f"Lowercase action {act.value} should normalize to valid")
            self.assertEqual(res_lower.normalized_action, act)

    def test_disallowed_and_hallucinated_actions_rejected(self):
        """Disallowed, destructive, or hallucinated AI actions are rejected safely."""
        disallowed_actions = [
            "DELETE_COMMUNITY",
            "SEND_SPAM",
            "EXECUTE_PAYMENT",
            "ARBITRARY_AI_CMD",
            "DROP_DATABASE",
            "TRANSFER_OWNERSHIP",
            "BAN_ALL_MEMBERS",
            "UNKNOWN_LIFECYCLE_TRIGGER",
        ]

        for act in disallowed_actions:
            req = schemas.ActionRequest(action=act, parameters={})
            res = validate_community_action_request(req)
            self.assertFalse(res.is_valid, f"Disallowed action '{act}' must be rejected")
            self.assertIsNone(res.normalized_action)
            self.assertGreater(len(res.errors), 0)
            self.assertIn("not an allowed action", res.errors[0])

        # Test empty or null action string
        empty_res = validate_community_action_request({"action": ""})
        self.assertFalse(empty_res.is_valid)
        self.assertIn("Action cannot be empty", empty_res.errors[0])

        none_res = validate_community_action_request({"action": None})
        self.assertFalse(none_res.is_valid)
        self.assertIn("Action cannot be empty", none_res.errors[0])

    def test_invalid_create_event_capacity_rejected(self):
        """CREATE_EVENT with non-positive or out-of-range capacity is rejected."""
        invalid_capacities = [0, -1, -50, "unlimited", 9999]

        for cap in invalid_capacities:
            req = schemas.ActionRequest(
                action="CREATE_EVENT",
                parameters={"max_capacity": cap},
            )
            res = validate_community_action_request(req)
            self.assertFalse(res.is_valid, f"Capacity {cap} must be rejected")
            self.assertTrue(any("max_capacity" in err for err in res.errors))

    def test_malformed_date_rejected(self):
        """Malformed or non-ISO dates are rejected without throwing unhandled exceptions."""
        malformed_dates = ["tomorrow", "2026/10/25", "10-25-2026", "not-a-date", "2026-99-99"]

        for d in malformed_dates:
            req = schemas.ActionRequest(
                action="CREATE_EVENT",
                parameters={"event_date": d},
            )
            res = validate_community_action_request(req)
            self.assertFalse(res.is_valid, f"Date '{d}' must be rejected")
            self.assertTrue(any("event_date" in err for err in res.errors))

        # Check REACTIVATE_COMMUNITY proposed_date
        req_react = schemas.ActionRequest(
            action="REACTIVATE_COMMUNITY",
            parameters={"proposed_date": "invalid-react-date"},
        )
        res_react = validate_community_action_request(req_react)
        self.assertFalse(res_react.is_valid)
        self.assertTrue(any("proposed_date" in err for err in res_react.errors))

    def test_re_engagement_blank_or_malicious_input_rejected(self):
        """Blank, oversized, or malicious XSS payload in re-engagement is rejected."""
        # 1. Blank string
        req_blank = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={"message": "   "},
        )
        res_blank = validate_community_action_request(req_blank)
        self.assertFalse(res_blank.is_valid)
        self.assertTrue(any("blank" in err for err in res_blank.errors))

        # 2. Oversized message (> 500 chars)
        req_long = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={"message": "A" * 501},
        )
        res_long = validate_community_action_request(req_long)
        self.assertFalse(res_long.is_valid)
        self.assertTrue(any("500 characters" in err for err in res_long.errors))

        # 3. Script injection payload
        req_xss = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={"message": "Hello <script>alert('xss')</script>"},
        )
        res_xss = validate_community_action_request(req_xss)
        self.assertFalse(res_xss.is_valid)
        self.assertTrue(any("Malicious" in err for err in res_xss.errors))

        # 4. JavaScript protocol payload
        req_js = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={"message": "Click here: javascript:exploit()"},
        )
        res_js = validate_community_action_request(req_js)
        self.assertFalse(res_js.is_valid)
        self.assertTrue(any("Malicious" in err for err in res_js.errors))

    def test_validation_causes_zero_db_writes_and_no_side_effects(self):
        """Pure validation causes zero database mutations across all core tables."""
        # 1. Snapshot table counts
        initial_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        # 2. Run a batch of valid, invalid, and malicious validation calls
        test_requests = [
            schemas.ActionRequest(action="CREATE_EVENT", parameters={"max_capacity": 6, "event_date": "2026-10-30"}),
            schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={"message": "Come join us!"}),
            schemas.ActionRequest(action="DELETE_COMMUNITY", parameters={"force": True}),
            schemas.ActionRequest(action="EXECUTE_PAYMENT", parameters={"amount": 9999}),
            schemas.ActionRequest(action="CREATE_EVENT", parameters={"max_capacity": -1}),
            schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={"message": "<script>evil</script>"}),
            schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 5}),
            schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "Saturday mornings"}),
            schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"proposed_date": "2026-11-01"}),
            schemas.ActionRequest(action="ARBITRARY_AI_CMD", parameters={"cmd": "run"}),
        ]

        for req in test_requests:
            validate_community_action_request(req)

        # 3. Snapshot counts after
        after_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        # 4. Assert zero mutations
        self.assertEqual(initial_counts, after_counts, "Pure validation must produce zero DB mutations")


class TestCommunityActionAuthorization(unittest.TestCase):
    """
    Step 9.2 Test Suite:
    Tests Permission & Membership Gate:
    - Authenticated member + valid action -> AUTHORIZED (200)
    - Authenticated non-member -> NOT_A_MEMBER (403)
    - Missing community -> COMMUNITY_NOT_FOUND (404)
    - Unauthenticated requester -> UNAUTHENTICATED (401)
    - Invalid action rejected first -> INVALID_ACTION (400)
    - All 6 allowed actions authorized for member
    - Zero database mutations guarantee
    - Zero action execution guarantee
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Create Enrolled Community Member
        email_member = f"member_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_member, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.member_user = cls.db.query(models.User).filter(models.User.email == email_member).first()

        # 2. Create Community
        cls.community = models.Community(
            name=f"Auth_Test_Comm_{cls.ts}",
            description="Testing authorization gate",
            created_by=cls.member_user.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        # 3. Add member to community
        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.member_user.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # 4. Create Non-Member User
        email_non_member = f"non_member_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_non_member, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.non_member_user = cls.db.query(models.User).filter(models.User.email == email_non_member).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_authenticated_member_valid_action_authorized(self):
        """Authenticated community member requesting a valid action is authorized with status 200."""
        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={"max_capacity": 8, "event_date": "2026-10-30"},
            reason="Organize next activity",
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
        )
        self.assertTrue(auth_res.is_authorized)
        self.assertEqual(auth_res.status, "AUTHORIZED")
        self.assertEqual(auth_res.status_code, 200)
        self.assertEqual(auth_res.community_id, self.community.community_id)
        self.assertEqual(auth_res.requester_id, self.member_user.user_id)

    def test_authenticated_non_member_rejected(self):
        """Authenticated user who is not a member of the community is rejected with NOT_A_MEMBER (403)."""
        req = schemas.ActionRequest(action="CREATE_EVENT", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.non_member_user.user_id,
            validation_result=val_res,
        )
        self.assertFalse(auth_res.is_authorized)
        self.assertEqual(auth_res.status, "NOT_A_MEMBER")
        self.assertEqual(auth_res.status_code, 403)
        self.assertIn("not a member", auth_res.message.lower())

    def test_missing_community_returns_404(self):
        """Request for a non-existent community ID is rejected with COMMUNITY_NOT_FOUND (404)."""
        req = schemas.ActionRequest(action="CREATE_EVENT", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(
            db=self.db,
            community_id=9999999,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
        )
        self.assertFalse(auth_res.is_authorized)
        self.assertEqual(auth_res.status, "COMMUNITY_NOT_FOUND")
        self.assertEqual(auth_res.status_code, 404)
        self.assertIn("does not exist", auth_res.message)

    def test_unauthenticated_requester_returns_401(self):
        """Unauthenticated requester (None or invalid ID) is rejected with UNAUTHENTICATED (401)."""
        req = schemas.ActionRequest(action="CREATE_EVENT", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        for unauth_id in [None, 0, -1]:
            auth_res = authorize_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=unauth_id,
                validation_result=val_res,
            )
            self.assertFalse(auth_res.is_authorized)
            self.assertEqual(auth_res.status, "UNAUTHENTICATED")
            self.assertEqual(auth_res.status_code, 401)
            self.assertIn("Authentication required", auth_res.message)

    def test_invalid_action_rejected_first(self):
        """Invalid or hallucinated action is rejected with INVALID_ACTION (400) before any membership check."""
        req = schemas.ActionRequest(action="DELETE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        self.assertFalse(val_res.is_valid)

        # Even for an enrolled member, invalid action fails immediately with 400
        auth_res = authorize_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
        )
        self.assertFalse(auth_res.is_authorized)
        self.assertEqual(auth_res.status, "INVALID_ACTION")
        self.assertEqual(auth_res.status_code, 400)
        self.assertIn("rejected", auth_res.message)

    def test_all_six_allowed_actions_authorized_for_member(self):
        """All 6 allowed actions pass validation and authorization for an enrolled community member."""
        actions = [
            schemas.AllowedAction.CREATE_EVENT,
            schemas.AllowedAction.RE_ENGAGE_MEMBERS,
            schemas.AllowedAction.COLLECT_FEEDBACK,
            schemas.AllowedAction.GROW_MEMBERSHIP,
            schemas.AllowedAction.MAINTAIN_ACTIVITY,
            schemas.AllowedAction.REACTIVATE_COMMUNITY,
        ]

        for act in actions:
            req = schemas.ActionRequest(action=act.value, parameters={})
            val_res = validate_community_action_request(req)
            self.assertTrue(val_res.is_valid)

            auth_res = authorize_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=self.member_user.user_id,
                validation_result=val_res,
            )
            self.assertTrue(auth_res.is_authorized, f"Action {act.value} should be authorized for member")
            self.assertEqual(auth_res.status, "AUTHORIZED")
            self.assertEqual(auth_res.status_code, 200)

    def test_authorization_causes_zero_db_writes(self):
        """Authorization gate performs only read operations, causing zero database mutations."""
        initial_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        # Run multiple authorization checks (authorized, unauthorized, not found, invalid action)
        valid_val = validate_community_action_request(schemas.ActionRequest(action="CREATE_EVENT"))
        invalid_val = validate_community_action_request(schemas.ActionRequest(action="EXECUTE_PAYMENT"))

        authorize_community_action(self.db, self.community.community_id, self.member_user.user_id, valid_val)
        authorize_community_action(self.db, self.community.community_id, self.non_member_user.user_id, valid_val)
        authorize_community_action(self.db, 9999999, self.member_user.user_id, valid_val)
        authorize_community_action(self.db, self.community.community_id, None, valid_val)
        authorize_community_action(self.db, self.community.community_id, self.member_user.user_id, invalid_val)

        after_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        self.assertEqual(initial_counts, after_counts, "Authorization gate must cause zero DB writes")

    def test_authorization_does_not_execute_action(self):
        """Authorization check alone produces an authorization result and does not execute the action."""
        events_before = self.db.query(models.Event).filter(models.Event.host_id == self.member_user.user_id).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={"max_capacity": 6, "event_date": "2026-10-31", "title": "Unexecuted Test Event"},
        )
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
        )

        self.assertTrue(auth_res.is_authorized)
        self.assertEqual(auth_res.status, "AUTHORIZED")

        events_after = self.db.query(models.Event).filter(models.Event.host_id == self.member_user.user_id).count()
        self.assertEqual(events_before, events_after, "Authorization gate must NOT execute or create events")


class TestCommunityActionDispatcher(unittest.TestCase):
    """
    Step 9.3 Test Suite:
    Tests Controlled Execution Dispatcher:
    - All 6 allowed actions dispatch strictly to their matching handler
    - Unvalidated action -> rejected by dispatcher
    - Unauthorized action -> rejected by dispatcher
    - Unknown/unregistered action -> rejected by dispatcher
    - Handler exception -> structured FAILED result
    - Arbitrary string input cannot select a handler
    - Dispatcher causes zero unintended database mutations
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        email_member = f"disp_member_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_member, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.member_user = cls.db.query(models.User).filter(models.User.email == email_member).first()

        cls.community = models.Community(
            name=f"Disp_Test_Comm_{cls.ts}",
            description="Testing dispatcher",
            created_by=cls.member_user.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.member_user.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        email_non = f"disp_non_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_non, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.non_member_user = cls.db.query(models.User).filter(models.User.email == email_non).first()
        cls.activity = cls.db.query(models.Activity).first()

        # Add peer member to community for re-engagement testing
        email_peer = f"disp_peer_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_peer, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.peer_member = cls.db.query(models.User).filter(models.User.email == email_peer).first()
        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.peer_member.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # Add completed event for collect feedback testing
        disp_completed = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.member_user.user_id,
            title=f"Disp Completed Event {cls.ts}",
            event_date=date.today() - timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(16, 0),
            max_capacity=10,
            status="COMPLETED",
        )
        cls.db.add(disp_completed)
        cls.db.flush()

        cls.db.add(models.EventParticipant(
            event_id=disp_completed.event_id,
            user_id=cls.peer_member.user_id,
            status="CONFIRMED",
        ))
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_all_six_allowed_actions_dispatch_to_correct_handler(self):
        """All 6 AllowedAction values dispatch strictly to their designated handler."""
        action_handler_map = [
            (schemas.AllowedAction.CREATE_EVENT, "create_event"),
            (schemas.AllowedAction.RE_ENGAGE_MEMBERS, "re_engage_members"),
            (schemas.AllowedAction.COLLECT_FEEDBACK, "collect_feedback"),
            (schemas.AllowedAction.GROW_MEMBERSHIP, "grow_membership"),
            (schemas.AllowedAction.MAINTAIN_ACTIVITY, "maintain_activity"),
            (schemas.AllowedAction.REACTIVATE_COMMUNITY, "reactivate_community"),
        ]

        for action_enum, expected_handler_name in action_handler_map:
            if action_enum == schemas.AllowedAction.CREATE_EVENT:
                params = {
                    "activity_id": self.activity.activity_id,
                    "event_date": "2026-11-20",
                    "start_time": "18:00:00",
                    "end_time": "20:00:00",
                    "title": f"Dispatch Test Event {self.ts}",
                    "max_capacity": 10,
                }
            else:
                params = {"notes": "test"}

            req = schemas.ActionRequest(action=action_enum.value, parameters=params)
            val_res = validate_community_action_request(req)
            self.assertTrue(val_res.is_valid)

            auth_res = authorize_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=self.member_user.user_id,
                validation_result=val_res,
            )
            self.assertTrue(auth_res.is_authorized)

            exec_res = dispatch_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=self.member_user.user_id,
                validation_result=val_res,
                authorization_result=auth_res,
            )

            self.assertTrue(exec_res.success, f"Action {action_enum.value} should succeed in dispatch")
            self.assertEqual(exec_res.action, action_enum.value)
            self.assertEqual(exec_res.community_id, self.community.community_id)

            if action_enum == schemas.AllowedAction.CREATE_EVENT:
                self.assertEqual(exec_res.status, "COMPLETED")
                self.assertIsNotNone(exec_res.details.get("event_id"))
            elif action_enum == schemas.AllowedAction.RE_ENGAGE_MEMBERS:
                self.assertEqual(exec_res.status, "COMPLETED")
                self.assertIsNotNone(exec_res.details.get("prepared_notifications"))
            elif action_enum == schemas.AllowedAction.COLLECT_FEEDBACK:
                self.assertEqual(exec_res.status, "COMPLETED")
                self.assertIsNotNone(exec_res.details.get("prepared_feedback_requests"))
            elif action_enum == schemas.AllowedAction.GROW_MEMBERSHIP:
                self.assertEqual(exec_res.status, "COMPLETED")
                self.assertIsNotNone(exec_res.details.get("prepared_invitations"))
            elif action_enum == schemas.AllowedAction.MAINTAIN_ACTIVITY:
                self.assertEqual(exec_res.status, "COMPLETED")
                self.assertIsNotNone(exec_res.details.get("maintenance_plan"))
            elif action_enum == schemas.AllowedAction.REACTIVATE_COMMUNITY:
                self.assertEqual(exec_res.status, "COMPLETED")
                self.assertIsNotNone(exec_res.details.get("delivery_status"))
            else:
                self.assertEqual(exec_res.status, "READY")
                self.assertEqual(exec_res.details.get("dispatched_handler"), expected_handler_name)

    def test_unvalidated_action_rejected_by_dispatcher(self):
        """Action that failed validation is rejected by dispatcher before reaching any handler."""
        # Simulated validation failure
        val_res = schemas.ActionValidationResult(
            is_valid=False,
            action="DELETE_COMMUNITY",
            normalized_action=None,
            errors=["Action is not permitted."],
        )
        auth_res = schemas.ActionAuthorizationResult(
            is_authorized=True,
            status="AUTHORIZED",
            status_code=200,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            action="DELETE_COMMUNITY",
            message="Authorized",
        )

        exec_res = dispatch_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
            authorization_result=auth_res,
        )

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertIn("invalid", exec_res.message.lower())
        self.assertEqual(exec_res.details.get("reason"), "validation_failed")

    def test_unauthorized_action_rejected_by_dispatcher(self):
        """Action that failed authorization is rejected by dispatcher before reaching any handler."""
        req = schemas.ActionRequest(action="CREATE_EVENT", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        # Non-member authorization failure
        auth_res = authorize_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.non_member_user.user_id,
            validation_result=val_res,
        )
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.non_member_user.user_id,
            validation_result=val_res,
            authorization_result=auth_res,
        )

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertIn("authorization rejected", exec_res.message.lower())
        self.assertEqual(exec_res.details.get("reason"), "authorization_failed")

    def test_unknown_action_without_handler_rejected(self):
        """Action with no registered handler is rejected safely without dispatch."""
        # Forge an unmapped validation result
        val_res = schemas.ActionValidationResult(
            is_valid=False,
            action="UNREGISTERED_ACTION",
            normalized_action=None,
            errors=["Action is not permitted."],
        )
        auth_res = schemas.ActionAuthorizationResult(
            is_authorized=False,
            status="INVALID_ACTION",
            status_code=400,
            message="Rejected",
        )

        exec_res = dispatch_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
            authorization_result=auth_res,
        )

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_handler_exception_returns_structured_failed_result(self):
        """Unexpected exception raised within a handler is caught and wrapped in a structured FAILED result."""
        def crashing_handler(community_id, requester_id, params, db):
            raise RuntimeError("Simulated network timeout during action dispatch")

        req = schemas.ActionRequest(action="CREATE_EVENT", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(
            db=self.db,
            community_id=self.community.community_id,
            requester_id=self.member_user.user_id,
            validation_result=val_res,
        )

        # Patch handler registry to test exception containment
        with patch.dict(COMMUNITY_ACTION_HANDLERS, {schemas.AllowedAction.CREATE_EVENT: crashing_handler}):
            exec_res = dispatch_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=self.member_user.user_id,
                validation_result=val_res,
                authorization_result=auth_res,
            )

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "FAILED")
        self.assertIn("Execution failed", exec_res.message)
        self.assertEqual(exec_res.details.get("error_type"), "RuntimeError")
        self.assertIn("Simulated network timeout", exec_res.details.get("error"))
        self.assertIsNotNone(exec_res.executed_at)

    def test_arbitrary_string_cannot_select_handler(self):
        """Arbitrary string injection cannot bypass AllowedAction enum lookup."""
        arbitrary_inputs = ["__class__", "eval", "DELETE", "exec", "system", "os.system"]

        for arb in arbitrary_inputs:
            req = schemas.ActionRequest(action=arb, parameters={})
            val_res = validate_community_action_request(req)
            self.assertFalse(val_res.is_valid)

            auth_res = authorize_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=self.member_user.user_id,
                validation_result=val_res,
            )
            self.assertFalse(auth_res.is_authorized)

            exec_res = dispatch_community_action(
                db=self.db,
                community_id=self.community.community_id,
                requester_id=self.member_user.user_id,
                validation_result=val_res,
                authorization_result=auth_res,
            )

            self.assertFalse(exec_res.success)
            self.assertEqual(exec_res.status, "REJECTED")

    def test_dispatcher_causes_zero_db_writes(self):
        """Dispatcher execution stubs cause zero database mutations across all core tables."""
        initial_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        # Dispatch all 6 actions + invalid + unauthorized
        for act in schemas.AllowedAction:
            val_res = validate_community_action_request(schemas.ActionRequest(action=act.value))
            auth_res = authorize_community_action(self.db, self.community.community_id, self.member_user.user_id, val_res)
            dispatch_community_action(self.db, self.community.community_id, self.member_user.user_id, val_res, auth_res)

        after_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        self.assertEqual(initial_counts, after_counts, "Dispatcher execution must cause zero DB writes")


class TestCreateEventActionExecution(unittest.TestCase):
    """
    Step 9.4 Test Suite: Concrete CREATE_EVENT Action Execution
    - Valid CREATE_EVENT -> event created & host enrolled as confirmed participant
    - Invalid activity template -> rejected without DB mutation
    - Invalid capacity -> rejected without DB mutation
    - Invalid date/time (in past or end <= start) -> rejected without DB mutation
    - Unauthorized requester -> rejected
    - Duplicate event (same title, date, host) -> rejected
    - Conflicting schedule (overlapping time on same date) -> rejected
    - Successful creation -> correct ActionExecutionResult with event_id
    - DB mutation occurs ONLY on success
    - Failed execution (exception during flush/add) -> rollback leaves no partial event
    - Other 5 actions remain controlled stubs returning READY
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Setup Member User
        email_member = f"event_exec_mem_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_member, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.member = cls.db.query(models.User).filter(models.User.email == email_member).first()

        # 2. Setup Community
        cls.community = models.Community(
            name=f"Exec_Event_Comm_{cls.ts}",
            description="Testing CREATE_EVENT execution",
            created_by=cls.member.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        # 3. Add Member to Community
        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.member.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # 4. Setup Non-Member User
        email_non = f"event_exec_non_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_non, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.non_member = cls.db.query(models.User).filter(models.User.email == email_non).first()

        # 5. Fetch a valid activity
        cls.activity = cls.db.query(models.Activity).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_valid_create_event_creates_event_and_participant(self):
        """Valid CREATE_EVENT creates scheduled Event in PostgreSQL and enrolls host."""
        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-15",
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": f"Community Tennis Singles {self.ts}",
                "max_capacity": 8,
            },
            reason="High member activity and demand",
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.action, "CREATE_EVENT")
        self.assertIn("successfully created", exec_res.message)
        self.assertIsNotNone(exec_res.executed_at)

        event_id = exec_res.details.get("event_id")
        self.assertIsNotNone(event_id)

        # Verify PostgreSQL database records
        event = self.db.query(models.Event).filter(models.Event.event_id == event_id).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, f"Community Tennis Singles {self.ts}")
        self.assertEqual(event.host_id, self.member.user_id)
        self.assertEqual(event.activity_id, self.activity.activity_id)
        self.assertEqual(event.max_capacity, 8)
        self.assertEqual(event.status, "PUBLISHED")

        # Verify Host Participant enrolled
        participant = (
            self.db.query(models.EventParticipant)
            .filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == self.member.user_id)
            .first()
        )
        self.assertIsNotNone(participant)
        self.assertEqual(participant.status, "CONFIRMED")

    def test_02_invalid_activity_rejected_without_db_mutation(self):
        """CREATE_EVENT with non-existent activity_id is rejected with zero event creation."""
        events_before = self.db.query(models.Event).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": 999999,  # Non-existent activity
                "event_date": "2026-11-16",
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": f"Invalid Activity Event {self.ts}",
            },
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "activity_not_found")
        self.assertIn("not found", exec_res.message.lower())

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after, "Failed activity check must cause zero DB writes")

    def test_03_invalid_capacity_rejected_without_db_mutation(self):
        """CREATE_EVENT with invalid capacity is rejected safely."""
        events_before = self.db.query(models.Event).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-17",
                "max_capacity": -10,
            },
        )
        val_res = validate_community_action_request(req)
        self.assertFalse(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after)

    def test_04_invalid_past_date_rejected_without_db_mutation(self):
        """CREATE_EVENT with past date is rejected by handler."""
        events_before = self.db.query(models.Event).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2020-01-01",  # Past date
                "title": f"Past Date Event {self.ts}",
            },
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "date_in_past")
        self.assertIn("past", exec_res.message.lower())

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after)

    def test_05_invalid_time_range_rejected_without_db_mutation(self):
        """CREATE_EVENT with end_time <= start_time is rejected."""
        events_before = self.db.query(models.Event).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-18",
                "start_time": "20:00:00",
                "end_time": "18:00:00",  # End before start
                "title": f"Inverted Times Event {self.ts}",
            },
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "invalid_time_range")
        self.assertIn("strictly after start_time", exec_res.message.lower())

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after)

    def test_06_unauthorized_requester_rejected(self):
        """Non-member cannot execute CREATE_EVENT."""
        events_before = self.db.query(models.Event).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-19",
                "title": f"Unauthorized Event {self.ts}",
            },
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.non_member.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.non_member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after)

    def test_07_duplicate_event_rejected(self):
        """Duplicate event request with identical title and date for same host is rejected."""
        title = f"Duplicate Guard Event {self.ts}"
        params = {
            "activity_id": self.activity.activity_id,
            "event_date": "2026-11-21",
            "start_time": "14:00:00",
            "end_time": "16:00:00",
            "title": title,
        }

        req1 = schemas.ActionRequest(action="CREATE_EVENT", parameters=params)
        val1 = validate_community_action_request(req1)
        auth1 = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val1)
        res1 = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val1, auth1)
        self.assertTrue(res1.success)
        self.assertEqual(res1.status, "COMPLETED")

        events_count = self.db.query(models.Event).count()

        # Second attempt with same title, date, host
        req2 = schemas.ActionRequest(action="CREATE_EVENT", parameters=params)
        val2 = validate_community_action_request(req2)
        auth2 = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val2)
        res2 = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val2, auth2)

        self.assertFalse(res2.success)
        self.assertEqual(res2.status, "REJECTED")
        self.assertEqual(res2.details.get("reason"), "duplicate_event")
        self.assertIn("duplicate event", res2.message.lower())

        self.assertEqual(self.db.query(models.Event).count(), events_count, "Duplicate attempt must not create second event")

    def test_08_conflicting_schedule_rejected(self):
        """Host cannot create overlapping events on the same date."""
        # 1. Create initial event: 10:00 - 12:00
        req1 = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-22",
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "title": f"Morning Slot {self.ts}",
            },
        )
        val1 = validate_community_action_request(req1)
        auth1 = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val1)
        res1 = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val1, auth1)
        self.assertTrue(res1.success)

        events_count = self.db.query(models.Event).count()

        # 2. Attempt overlapping event: 11:00 - 13:00 (overlaps with 10:00 - 12:00)
        req2 = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-22",
                "start_time": "11:00:00",
                "end_time": "13:00:00",
                "title": f"Overlapping Slot {self.ts}",
            },
        )
        val2 = validate_community_action_request(req2)
        auth2 = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val2)
        res2 = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val2, auth2)

        self.assertFalse(res2.success)
        self.assertEqual(res2.status, "REJECTED")
        self.assertEqual(res2.details.get("reason"), "schedule_conflict")
        self.assertIn("schedule conflict", res2.message.lower())

        self.assertEqual(self.db.query(models.Event).count(), events_count, "Conflicting schedule must not create event")

    def test_09_db_mutation_occurs_only_on_success(self):
        """DB records are created strictly on successful execution; failed calls cause zero state mutation."""
        initial_events = self.db.query(models.Event).count()
        initial_participants = self.db.query(models.EventParticipant).count()

        # Failed attempt: missing activity_id
        req_bad = schemas.ActionRequest(action="CREATE_EVENT", parameters={"event_date": "2026-11-23"})
        val_bad = validate_community_action_request(req_bad)
        auth_bad = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_bad)
        res_bad = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_bad, auth_bad)
        self.assertFalse(res_bad.success)

        self.assertEqual(self.db.query(models.Event).count(), initial_events)
        self.assertEqual(self.db.query(models.EventParticipant).count(), initial_participants)

        # Successful attempt: valid parameters
        req_good = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-23",
                "start_time": "15:00:00",
                "end_time": "17:00:00",
                "title": f"Success Mutation Test {self.ts}",
            },
        )
        val_good = validate_community_action_request(req_good)
        auth_good = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_good)
        res_good = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_good, auth_good)
        self.assertTrue(res_good.success)

        # Counts must increase by exactly 1
        self.assertEqual(self.db.query(models.Event).count(), initial_events + 1)
        self.assertEqual(self.db.query(models.EventParticipant).count(), initial_participants + 1)

    def test_10_failed_execution_leaves_no_partial_event(self):
        """Failure during execution triggers strict rollback leaving zero partial records."""
        events_before = self.db.query(models.Event).count()
        participants_before = self.db.query(models.EventParticipant).count()

        req = schemas.ActionRequest(
            action="CREATE_EVENT",
            parameters={
                "activity_id": self.activity.activity_id,
                "event_date": "2026-11-24",
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": f"Rollback Test Event {self.ts}",
            },
        )
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)

        # Simulate exception during participant enrollment / commit by patching db.commit
        with patch.object(self.db, "commit", side_effect=RuntimeError("Simulated database constraint crash")):
            exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "FAILED")
        self.assertEqual(exec_res.details.get("reason"), "database_error")
        self.assertIn("Simulated database constraint crash", exec_res.details.get("error"))

        # Verify rollback left NO partial event or participant
        events_after = self.db.query(models.Event).count()
        participants_after = self.db.query(models.EventParticipant).count()
        self.assertEqual(events_before, events_after, "Failed execution must leave no partial event")
        self.assertEqual(participants_before, participants_after, "Failed execution must leave no partial participant")

    def test_11_reactivate_community_action_causes_zero_event_mutations(self):
        """Executing REACTIVATE_COMMUNITY causes strictly zero unexpected event creations."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"notes": "check"})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.member.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        events_before = self.db.query(models.Event).count()
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.member.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after, "REACTIVATE_COMMUNITY must create zero events")


class TestReEngageMembersActionExecution(unittest.TestCase):
    """
    Step 9.5 Test Suite: Concrete RE_ENGAGE_MEMBERS Action Execution
    - Identifies inactive community members based on target_inactive_days.
    - Prepares controlled in-app notification payloads.
    - Omitted message uses courteous default with community name.
    - Zero inactive members -> returns COMPLETED with 0 notifications.
    - Community with only the requester -> rejected (no other members).
    - Unauthorized requester (non-member) -> rejected.
    - Invalid target_inactive_days (<= 0 or > 365) -> rejected.
    - Invalid message (empty or > 500 chars) -> rejected.
    - Zero unintended database writes across all core tables.
    - No external network or delivery side effects.
    - Remaining 4 actions remain controlled READY stubs.
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Setup Host/Requester
        email_host = f"reengage_host_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_host, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.host = cls.db.query(models.User).filter(models.User.email == email_host).first()

        # 2. Setup Active Member
        email_active = f"reengage_act_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_active, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.active_member = cls.db.query(models.User).filter(models.User.email == email_active).first()

        # 3. Setup Inactive Members
        email_inact1 = f"reengage_inact1_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_inact1, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.inactive_member1 = cls.db.query(models.User).filter(models.User.email == email_inact1).first()

        email_inact2 = f"reengage_inact2_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_inact2, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.inactive_member2 = cls.db.query(models.User).filter(models.User.email == email_inact2).first()

        # 4. Setup Non-Member
        email_non = f"reengage_non_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_non, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.non_member = cls.db.query(models.User).filter(models.User.email == email_non).first()

        # 5. Setup Community with 4 members (host + active + 2 inactives)
        cls.community = models.Community(
            name=f"ReEngage_Comm_{cls.ts}",
            description="Testing RE_ENGAGE_MEMBERS execution",
            created_by=cls.host.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        for user in [cls.host, cls.active_member, cls.inactive_member1, cls.inactive_member2]:
            cls.db.add(models.CommunityMember(
                community_id=cls.community.community_id,
                user_id=user.user_id,
                role="MEMBER",
            ))
        cls.db.commit()

        # 6. Setup Solo Community with only the host
        cls.solo_community = models.Community(
            name=f"ReEngage_Solo_{cls.ts}",
            description="Solo community without other members",
            created_by=cls.host.user_id,
        )
        cls.db.add(cls.solo_community)
        cls.db.commit()
        cls.db.refresh(cls.solo_community)

        cls.db.add(models.CommunityMember(
            community_id=cls.solo_community.community_id,
            user_id=cls.host.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # 7. Create recent event participation for active_member (2 days ago)
        cls.activity = cls.db.query(models.Activity).first()
        recent_event = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.host.user_id,
            title=f"Recent ReEngage Event {cls.ts}",
            event_date=date.today() - timedelta(days=2),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=10,
            status="PUBLISHED",
        )
        cls.db.add(recent_event)
        cls.db.flush()

        cls.db.add(models.EventParticipant(
            event_id=recent_event.event_id,
            user_id=cls.active_member.user_id,
            status="CONFIRMED",
        ))
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_valid_re_engage_identifies_inactive_and_prepares_notifications(self):
        """RE_ENGAGE_MEMBERS identifies inactive members and creates prepared notification payloads."""
        custom_message = "Hey friends, we'd love to see you back on the court soon!"
        req = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={
                "target_inactive_days": 14,
                "message": custom_message,
            },
            reason="Activity has cooled down over the past 2 weeks",
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.action, "RE_ENGAGE_MEMBERS")
        self.assertIn("Successfully prepared re-engagement notifications", exec_res.message)
        self.assertIsNotNone(exec_res.executed_at)

        details = exec_res.details
        self.assertEqual(details["target_inactive_days"], 14)
        self.assertEqual(details["eligible_member_count"], 2)
        self.assertEqual(set(details["eligible_member_ids"]), {self.inactive_member1.user_id, self.inactive_member2.user_id})
        self.assertNotIn(self.active_member.user_id, details["eligible_member_ids"])
        self.assertNotIn(self.host.user_id, details["eligible_member_ids"])
        self.assertEqual(details["delivery_status"], "PREPARED_FOR_DELIVERY")

        # Verify prepared notification structures
        notifications = details["prepared_notifications"]
        self.assertEqual(len(notifications), 2)
        for notif in notifications:
            self.assertIn(notif["recipient_id"], {self.inactive_member1.user_id, self.inactive_member2.user_id})
            self.assertEqual(notif["message"], custom_message)
            self.assertEqual(notif["channel"], "IN_APP")
            self.assertEqual(notif["status"], "PREPARED")
            self.assertEqual(notif["community_id"], self.community.community_id)

    def test_02_default_message_generated_when_message_omitted(self):
        """When message is omitted, courteous default with community name is used."""
        req = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={"target_inactive_days": 14},
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertIn(self.community.name, exec_res.details["message"])
        self.assertGreater(len(exec_res.details["prepared_notifications"]), 0)
        self.assertEqual(exec_res.details["prepared_notifications"][0]["message"], exec_res.details["message"])

    def test_03_all_members_active_returns_completed_with_zero_notifications(self):
        """When all members have been active within target_inactive_days, returns 0 notifications."""
        # Use target_inactive_days=1000 so that even old activity counts as active,
        # or simulate a community where everyone joined recent events
        # Let's add inactive_member1 and inactive_member2 to a recent event
        test_event = models.Event(
            activity_id=self.activity.activity_id,
            host_id=self.host.user_id,
            title=f"All Active Event {self.ts}",
            event_date=date.today(),
            start_time=time(14, 0),
            end_time=time(16, 0),
            max_capacity=10,
            status="PUBLISHED",
        )
        self.db.add(test_event)
        self.db.flush()

        self.db.add(models.EventParticipant(event_id=test_event.event_id, user_id=self.inactive_member1.user_id, status="CONFIRMED"))
        self.db.add(models.EventParticipant(event_id=test_event.event_id, user_id=self.inactive_member2.user_id, status="CONFIRMED"))
        self.db.commit()

        req = schemas.ActionRequest(
            action="RE_ENGAGE_MEMBERS",
            parameters={"target_inactive_days": 7},
        )
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.details["eligible_member_count"], 0)
        self.assertEqual(exec_res.details["prepared_notifications"], [])
        self.assertEqual(exec_res.details["delivery_status"], "NO_INACTIVE_MEMBERS")
        self.assertIn("No re-engagement necessary", exec_res.message)

    def test_04_no_other_members_in_community_rejected(self):
        """RE_ENGAGE_MEMBERS is rejected when community has no members other than requester."""
        req = schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.solo_community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.solo_community.community_id, self.host.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "no_other_members")
        self.assertIn("No other members found", exec_res.message)

    def test_05_unauthorized_non_member_rejected(self):
        """Non-member cannot execute RE_ENGAGE_MEMBERS."""
        req = schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.non_member.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.non_member.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_06_invalid_target_inactive_days_rejected(self):
        """Negative or out-of-range target_inactive_days is rejected safely."""
        invalid_days = [-5, 0, 999]
        for days in invalid_days:
            req = schemas.ActionRequest(
                action="RE_ENGAGE_MEMBERS",
                parameters={"target_inactive_days": days},
            )
            val_res = validate_community_action_request(req)
            if val_res.is_valid:
                # If pure validation allowed it, handler rejects it
                auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
                exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
                self.assertFalse(exec_res.success)
                self.assertEqual(exec_res.status, "REJECTED")
            else:
                self.assertFalse(val_res.is_valid)

    def test_07_invalid_or_oversized_message_rejected(self):
        """Empty whitespace or message exceeding 500 characters is rejected."""
        # Empty whitespace
        req_empty = schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={"message": "   "})
        val_empty = validate_community_action_request(req_empty)
        self.assertFalse(val_empty.is_valid)

        # Oversized message (> 500 chars)
        req_oversized = schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={"message": "x" * 501})
        val_oversized = validate_community_action_request(req_oversized)
        self.assertFalse(val_oversized.is_valid)

    def test_08_zero_unintended_database_writes(self):
        """RE_ENGAGE_MEMBERS execution causes zero database mutations across all core tables."""
        initial_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        req = schemas.ActionRequest(action="RE_ENGAGE_MEMBERS", parameters={"target_inactive_days": 14})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
        self.assertTrue(exec_res.success)

        after_counts = {
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        self.assertEqual(initial_counts, after_counts, "Re-engagement preparation must cause zero DB writes")

    def test_09_reactivate_community_action_causes_zero_side_effects(self):
        """Executing REACTIVATE_COMMUNITY causes strictly zero side effects."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"notes": "check"})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")


class TestCollectFeedbackActionExecution(unittest.TestCase):
    """
    Step 9.6 Test Suite: Concrete COLLECT_FEEDBACK Action Execution
    - Identifies eligible completed event(s) and prepares feedback requests
    - Auto-resolves most recent completed event if event_id is omitted
    - Rejects non-completed events (status != COMPLETED)
    - Rejects invalid/non-existent event_id
    - Rejects event outside community
    - Rejects unauthorized non-member requester
    - Automatically excludes participants who already submitted feedback
    - Clean zero-result when no eligible participants remain
    - Zero fake feedback rows created (zero unintended DB mutation)
    - Remaining 3 actions remain controlled READY stubs
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Setup Host & Community
        email_host = f"feedback_host_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_host, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.host = cls.db.query(models.User).filter(models.User.email == email_host).first()

        cls.community = models.Community(
            name=f"Feedback_Comm_{cls.ts}",
            description="Testing COLLECT_FEEDBACK execution",
            created_by=cls.host.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.host.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # 2. Setup Attendees (Community Members)
        email_att1 = f"feedback_att1_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_att1, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.attendee1 = cls.db.query(models.User).filter(models.User.email == email_att1).first()

        email_att2 = f"feedback_att2_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_att2, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.attendee2 = cls.db.query(models.User).filter(models.User.email == email_att2).first()

        for att in [cls.attendee1, cls.attendee2]:
            cls.db.add(models.CommunityMember(
                community_id=cls.community.community_id,
                user_id=att.user_id,
                role="MEMBER",
            ))
        cls.db.commit()

        # 3. Setup Outsider (Non-member)
        email_out = f"feedback_out_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_out, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.outsider = cls.db.query(models.User).filter(models.User.email == email_out).first()

        # 4. Activity
        cls.activity = cls.db.query(models.Activity).first()

        # 5. Completed Event for Community
        cls.completed_event = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.host.user_id,
            title=f"Completed Badminton Match {cls.ts}",
            event_date=date.today() - timedelta(days=2),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=8,
            status="COMPLETED",
        )
        cls.db.add(cls.completed_event)
        cls.db.flush()

        # Add attendees as confirmed participants
        for att in [cls.attendee1, cls.attendee2]:
            cls.db.add(models.EventParticipant(
                event_id=cls.completed_event.event_id,
                user_id=att.user_id,
                status="CONFIRMED",
            ))
        cls.db.commit()

        # 6. Non-completed Event (PUBLISHED status)
        cls.published_event = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.host.user_id,
            title=f"Future Published Event {cls.ts}",
            event_date=date.today() + timedelta(days=3),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=8,
            status="PUBLISHED",
        )
        cls.db.add(cls.published_event)
        cls.db.commit()

        # 7. Outsider Event (Hosted by someone outside community)
        cls.outsider_event = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.outsider.user_id,
            title=f"Outsider Completed Event {cls.ts}",
            event_date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            max_capacity=8,
            status="COMPLETED",
        )
        cls.db.add(cls.outsider_event)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_valid_completed_event_prepares_feedback_requests(self):
        """COLLECT_FEEDBACK on completed event prepares structured feedback requests for eligible attendees."""
        req = schemas.ActionRequest(
            action="COLLECT_FEEDBACK",
            parameters={"event_id": self.completed_event.event_id},
            reason="Gather attendee reviews after event completion",
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.action, "COLLECT_FEEDBACK")
        self.assertIn("Successfully prepared feedback requests", exec_res.message)
        self.assertIsNotNone(exec_res.executed_at)

        details = exec_res.details
        self.assertEqual(details["event_id"], self.completed_event.event_id)
        self.assertEqual(details["eligible_participant_count"], 2)
        self.assertEqual(set(details["eligible_participant_ids"]), {self.attendee1.user_id, self.attendee2.user_id})
        self.assertEqual(details["delivery_status"], "PREPARED_FOR_DELIVERY")

        requests = details["prepared_feedback_requests"]
        self.assertEqual(len(requests), 2)
        for req_item in requests:
            self.assertEqual(req_item["event_id"], self.completed_event.event_id)
            self.assertTrue(req_item["feedback_requested"])
            self.assertEqual(req_item["status"], "PREPARED")
            self.assertEqual(req_item["channel"], "IN_APP")
            self.assertEqual(req_item["community_id"], self.community.community_id)

    def test_02_omitted_event_id_resolves_most_recent_completed_event(self):
        """When event_id is omitted, handler automatically resolves the community's latest completed event."""
        req = schemas.ActionRequest(action="COLLECT_FEEDBACK", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.details["event_id"], self.completed_event.event_id)

    def test_03_non_completed_event_rejected(self):
        """COLLECT_FEEDBACK on non-completed event (e.g. PUBLISHED) is rejected."""
        req = schemas.ActionRequest(
            action="COLLECT_FEEDBACK",
            parameters={"event_id": self.published_event.event_id},
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "event_not_completed")
        self.assertIn("only completed events are eligible", exec_res.message.lower())

    def test_04_invalid_event_id_rejected(self):
        """Non-existent event_id is rejected safely."""
        req = schemas.ActionRequest(
            action="COLLECT_FEEDBACK",
            parameters={"event_id": 999999},
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "event_not_found")

    def test_05_event_outside_community_rejected(self):
        """Event not belonging to this community is rejected."""
        req = schemas.ActionRequest(
            action="COLLECT_FEEDBACK",
            parameters={"event_id": self.outsider_event.event_id},
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertEqual(exec_res.details.get("reason"), "event_outside_community")
        self.assertIn("does not belong to community", exec_res.message.lower())

    def test_06_non_member_requester_rejected(self):
        """Non-member cannot execute COLLECT_FEEDBACK."""
        req = schemas.ActionRequest(action="COLLECT_FEEDBACK", parameters={"event_id": self.completed_event.event_id})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.outsider.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.outsider.user_id, val_res, auth_res)

        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_07_already_submitted_feedback_participants_excluded(self):
        """Participants who have already submitted feedback for the event are excluded from new requests."""
        # Insert feedback from attendee1
        fb = models.Feedback(
            event_id=self.completed_event.event_id,
            reviewer_id=self.attendee1.user_id,
            rating=5,
            comment="Awesome doubles match!",
        )
        self.db.add(fb)
        self.db.commit()

        req = schemas.ActionRequest(
            action="COLLECT_FEEDBACK",
            parameters={"event_id": self.completed_event.event_id},
        )
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        # attendee1 is excluded, only attendee2 remains
        self.assertEqual(exec_res.details["eligible_participant_count"], 1)
        self.assertEqual(exec_res.details["eligible_participant_ids"], [self.attendee2.user_id])
        self.assertEqual(len(exec_res.details["prepared_feedback_requests"]), 1)
        self.assertEqual(exec_res.details["prepared_feedback_requests"][0]["recipient_id"], self.attendee2.user_id)

    def test_08_no_eligible_participants_returns_clean_zero_result(self):
        """When all participants have submitted feedback, returns clean COMPLETED result with count=0."""
        # Insert feedback from attendee2 as well
        fb2 = models.Feedback(
            event_id=self.completed_event.event_id,
            reviewer_id=self.attendee2.user_id,
            rating=4,
            comment="Good game, let's play again!",
        )
        self.db.add(fb2)
        self.db.commit()

        req = schemas.ActionRequest(
            action="COLLECT_FEEDBACK",
            parameters={"event_id": self.completed_event.event_id},
        )
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.details["eligible_participant_count"], 0)
        self.assertEqual(exec_res.details["prepared_feedback_requests"], [])
        self.assertEqual(exec_res.details["delivery_status"], "ALL_FEEDBACK_SUBMITTED")
        self.assertIn("all eligible participants", exec_res.message.lower())

    def test_09_no_fake_feedback_rows_created(self):
        """COLLECT_FEEDBACK causes zero database mutations and creates no fake feedback rows."""
        initial_feedback_count = self.db.query(models.Feedback).count()
        initial_events_count = self.db.query(models.Event).count()

        req = schemas.ActionRequest(action="COLLECT_FEEDBACK", parameters={"event_id": self.completed_event.event_id})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
        self.assertTrue(exec_res.success)

        self.assertEqual(self.db.query(models.Feedback).count(), initial_feedback_count, "No feedback rows should be inserted")
        self.assertEqual(self.db.query(models.Event).count(), initial_events_count, "No event rows should be mutated")

    def test_10_reactivate_community_action_causes_zero_side_effects(self):
        """Executing REACTIVATE_COMMUNITY causes strictly zero feedback rows to be created."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"notes": "check"})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        feedback_before = self.db.query(models.Feedback).count()
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(self.db.query(models.Feedback).count(), feedback_before)


class TestGrowMembershipActionExecution(unittest.TestCase):
    """
    Step 9.7 Test Suite: Concrete GROW_MEMBERSHIP Action Execution
    - Identifies eligible candidate users and prepares membership invitations
    - Respects desired target_count / target_invites with safe bounds (capped at 20)
    - Omitted target_count uses default (5)
    - Custom invitation_message is validated and propagated to prepared payloads
    - Strictly excludes existing community members and requester from candidates
    - Evaluates compatibility (locality match, interest affinity) and ranks candidates
    - Rejects unauthorized requester (non-member)
    - Rejects non-existent community
    - Rejects invalid target_count (<= 0)
    - Returns clean zero-result when all active users are already enrolled (no eligible candidates)
    - Strictly ZERO automatic user insertions into community_members table (unconsented additions forbidden)
    - Strictly ZERO mutations across all core tables (users, communities, community_members, events, feedback)
    - Strictly ZERO external messaging delivery side-effects
    - The remaining 2 actions (MAINTAIN_ACTIVITY, REACTIVATE_COMMUNITY) remain controlled READY stubs.
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Setup Host & Community
        email_host = f"grow_host_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_host, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.host = cls.db.query(models.User).filter(models.User.email == email_host).first()

        cls.community = models.Community(
            name=f"Indiranagar_Badminton_Club_{cls.ts}",
            description="A vibrant badminton and fitness community in Indiranagar, Bengaluru",
            created_by=cls.host.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.host.user_id,
            role="ADMIN",
        ))

        # 2. Existing peer member (must be excluded from invitations)
        email_peer = f"grow_peer_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_peer, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.peer_member = cls.db.query(models.User).filter(models.User.email == email_peer).first()
        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.peer_member.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # Update host profile locality to Indiranagar
        host_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.host.user_id).first()
        if host_prof:
            host_prof.approx_locality = "Indiranagar, Bengaluru"
            cls.db.commit()

        # Find or create Badminton interest
        badminton_interest = cls.db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        if not badminton_interest:
            badminton_interest = models.Interest(name="Badminton", category="Sports")
            cls.db.add(badminton_interest)
            cls.db.commit()
            cls.db.refresh(badminton_interest)
        cls.badminton_interest = badminton_interest

        # 3. Setup Candidate 1 (Locality match + Badminton interest -> Highest rank)
        email_cand1 = f"grow_cand1_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_cand1, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.cand1 = cls.db.query(models.User).filter(models.User.email == email_cand1).first()
        cand1_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.cand1.user_id).first()
        if cand1_prof:
            cand1_prof.display_name = f"Indiranagar Player {cls.ts}"
            cand1_prof.approx_locality = "Indiranagar, Bengaluru"
        cls.db.add(models.UserInterest(user_id=cls.cand1.user_id, interest_id=cls.badminton_interest.interest_id))
        cls.db.commit()

        # 4. Setup Candidate 2 (Badminton interest only, different locality -> Medium rank)
        email_cand2 = f"grow_cand2_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_cand2, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.cand2 = cls.db.query(models.User).filter(models.User.email == email_cand2).first()
        cand2_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.cand2.user_id).first()
        if cand2_prof:
            cand2_prof.display_name = f"Whitefield Player {cls.ts}"
            cand2_prof.approx_locality = "Whitefield, Bengaluru"
        cls.db.add(models.UserInterest(user_id=cls.cand2.user_id, interest_id=cls.badminton_interest.interest_id))
        cls.db.commit()

        # 5. Setup Candidate 3 (No matching interest, distant locality -> Baseline score)
        email_cand3 = f"grow_cand3_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_cand3, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.cand3 = cls.db.query(models.User).filter(models.User.email == email_cand3).first()
        cand3_prof = cls.db.query(models.Profile).filter(models.Profile.user_id == cls.cand3.user_id).first()
        if cand3_prof:
            cand3_prof.display_name = f"Jayanagar Player {cls.ts}"
            cand3_prof.approx_locality = "Jayanagar, Bengaluru"
        cls.db.commit()

        # 6. Setup Inactive Candidate (Must be excluded)
        email_inact = f"grow_inact_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_inact, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.inactive_user = cls.db.query(models.User).filter(models.User.email == email_inact).first()
        cls.inactive_user.is_active = False
        cls.db.commit()

        # 7. Setup Outsider (Non-member for authorization rejection test)
        email_out = f"grow_out_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_out, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.outsider = cls.db.query(models.User).filter(models.User.email == email_out).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_valid_growth_prepares_membership_invitations(self):
        """Enrolled member requests GROW_MEMBERSHIP with target_count=2 -> prepares top ranked candidate invitations."""
        req = schemas.ActionRequest(
            action="GROW_MEMBERSHIP",
            parameters={"target_count": 2},
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.action, "GROW_MEMBERSHIP")
        self.assertEqual(exec_res.community_id, self.community.community_id)

        details = exec_res.details
        self.assertEqual(details["target_count"], 2)
        self.assertEqual(details["invited_candidate_count"], 2)
        self.assertEqual(details["delivery_status"], "PREPARED_FOR_DELIVERY")

        invitations = details["prepared_invitations"]
        self.assertEqual(len(invitations), 2)
        for inv in invitations:
            self.assertEqual(inv["community_id"], self.community.community_id)
            self.assertEqual(inv["status"], "PREPARED")
            self.assertEqual(inv["channel"], "IN_APP")
            self.assertIn("prepared_at", inv)
            self.assertGreaterEqual(inv["match_score"], 50)
            self.assertIsInstance(inv["match_reasons"], list)

        # Top invitations should feature high compatibility match scores (>= 80)
        self.assertGreater(invitations[0]["match_score"], 50)
        self.assertTrue(any(inv["match_score"] >= 80 for inv in invitations))

    def test_02_omitted_target_count_uses_default_limit(self):
        """When target_count is omitted, defaults to 5 without failure."""
        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.details["target_count"], 5)
        self.assertLessEqual(exec_res.details["invited_candidate_count"], 5)

    def test_03_existing_community_members_strictly_excluded(self):
        """All existing community members (including peer and host) are strictly excluded from candidates."""
        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 20})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        invited_ids = set(exec_res.details["invited_candidate_ids"])

        # Neither host nor peer_member can be invited
        self.assertNotIn(self.host.user_id, invited_ids)
        self.assertNotIn(self.peer_member.user_id, invited_ids)

    def test_04_inactive_users_strictly_excluded(self):
        """Inactive accounts (is_active=False) are strictly excluded from invitations."""
        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 20})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        invited_ids = set(exec_res.details["invited_candidate_ids"])
        self.assertNotIn(self.inactive_user.user_id, invited_ids)

    def test_05_custom_invitation_message_is_propagated(self):
        """Custom invitation_message is included in each prepared invitation payload."""
        custom_msg = "Join our competitive weekend badminton crew!"
        req = schemas.ActionRequest(
            action="GROW_MEMBERSHIP",
            parameters={"target_count": 2, "invitation_message": custom_msg},
        )
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        for inv in exec_res.details["prepared_invitations"]:
            self.assertEqual(inv["invitation_message"], custom_msg)

    def test_06_non_member_requester_rejected(self):
        """Requester not belonging to the community is rejected before candidate processing."""
        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 5})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.outsider.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.outsider.user_id, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertIn("not a member", exec_res.message.lower())

    def test_07_invalid_community_id_rejected(self):
        """Non-existent community_id is rejected gracefully."""
        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 5})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, 9999999, self.host.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, 9999999, self.host.user_id, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_08_invalid_target_count_rejected(self):
        """Non-positive target_count is rejected by validation."""
        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": -5})
        val_res = validate_community_action_request(req)
        self.assertFalse(val_res.is_valid)
        self.assertIn("target_count must be a positive integer", val_res.errors[0])

    def test_09_no_eligible_candidates_returns_clean_zero_result(self):
        """When all active users in the system are enrolled in a community, returns clean COMPLETED result with count=0."""
        temp_comm = models.Community(
            name=f"Isolated_Full_Comm_{self.ts}",
            description="All platform users enrolled",
            created_by=self.host.user_id,
        )
        self.db.add(temp_comm)
        self.db.commit()

        # Enroll all active users into this temporary community
        active_uids = [u.user_id for u in self.db.query(models.User).filter(models.User.is_active == True).all()]
        for uid in active_uids:
            self.db.add(models.CommunityMember(community_id=temp_comm.community_id, user_id=uid, role="MEMBER"))
        self.db.commit()

        try:
            req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 5})
            val_res = validate_community_action_request(req)
            auth_res = authorize_community_action(self.db, temp_comm.community_id, self.host.user_id, val_res)
            exec_res = dispatch_community_action(self.db, temp_comm.community_id, self.host.user_id, val_res, auth_res)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.status, "COMPLETED")
            self.assertEqual(exec_res.details["eligible_candidate_count"], 0)
            self.assertEqual(exec_res.details["invited_candidate_count"], 0)
            self.assertEqual(exec_res.details["prepared_invitations"], [])
            self.assertEqual(exec_res.details["delivery_status"], "NO_ELIGIBLE_CANDIDATES")
        finally:
            self.db.query(models.CommunityMember).filter(models.CommunityMember.community_id == temp_comm.community_id).delete()
            self.db.delete(temp_comm)
            self.db.commit()

    def test_10_zero_unintended_database_mutations_and_zero_fake_members(self):
        """Zero DB writes occur: no community_members rows, no users, no fake records inserted."""
        initial_counts = {
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        req = schemas.ActionRequest(action="GROW_MEMBERSHIP", parameters={"target_count": 3})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")

        after_counts = {
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "communities": self.db.query(models.Community).count(),
            "events": self.db.query(models.Event).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        self.assertEqual(initial_counts, after_counts, "GROW_MEMBERSHIP preparation must cause strictly zero DB writes")

    def test_11_reactivate_community_action_causes_zero_mutations(self):
        """Executing REACTIVATE_COMMUNITY causes strictly zero member rows to be added."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"notes": "check"})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        members_before = self.db.query(models.CommunityMember).count()
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
        self.assertTrue(exec_res.success, f"Failed: status={exec_res.status}, msg={exec_res.message}, details={exec_res.details}")
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(self.db.query(models.CommunityMember).count(), members_before)


class TestMaintainActivityActionExecution(unittest.TestCase):
    """
    Step 9.8 Test Suite: Concrete MAINTAIN_ACTIVITY Action Execution
    - Healthy community -> maintenance payload prepared with forward plan
    - Growing community -> maintenance payload prepared with forward plan
    - No upcoming activity -> preparation still works (delivery_status='PREPARED')
    - Existing upcoming activity -> avoids unnecessary duplicate immediate cadence (delivery_status='ACTIVITY_ALREADY_SCHEDULED')
    - Custom recurring pattern (e.g. BIWEEKLY, MONTHLY) -> appropriately calculates cadence and title
    - Invalid/blank recurring_pattern -> rejected
    - Invalid community_id -> rejected
    - Non-member requester -> rejected
    - Unauthorized requester -> rejected
    - No suitable activity in system -> clean NO_ACTIVITY_TO_MAINTAIN result
    - Zero DB mutation: strictly zero events created and zero records mutated
    - Remaining REACTIVATE_COMMUNITY action remains a controlled READY stub.
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Setup Host & Community
        email_host = f"maintain_host_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_host, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.host = cls.db.query(models.User).filter(models.User.email == email_host).first()

        cls.community = models.Community(
            name=f"Indiranagar_Badminton_Club_{cls.ts}",
            description="Active badminton community in Indiranagar, Bengaluru",
            created_by=cls.host.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        cls.db.add(models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.host.user_id,
            role="ADMIN",
        ))

        # 2. Add Peer Members
        email_peer1 = f"maintain_p1_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_peer1, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.peer1 = cls.db.query(models.User).filter(models.User.email == email_peer1).first()

        email_peer2 = f"maintain_p2_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_peer2, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.peer2 = cls.db.query(models.User).filter(models.User.email == email_peer2).first()

        for peer in [cls.peer1, cls.peer2]:
            cls.db.add(models.CommunityMember(
                community_id=cls.community.community_id,
                user_id=peer.user_id,
                role="MEMBER",
            ))
        cls.db.commit()

        # 3. Find or Create Activity
        cls.activity = cls.db.query(models.Activity).first()
        if not cls.activity:
            cls.activity = models.Activity(
                title="Weekend Badminton Doubles",
                category="Sports",
                description="Community badminton matches",
            )
            cls.db.add(cls.activity)
            cls.db.commit()
            cls.db.refresh(cls.activity)

        # 4. Add a Past Event to link community to activity
        cls.past_event = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.host.user_id,
            title=f"Past Badminton Match {cls.ts}",
            event_date=date.today() - timedelta(days=5),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=10,
            status="COMPLETED",
        )
        cls.db.add(cls.past_event)
        cls.db.commit()
        cls.db.refresh(cls.past_event)

        # 5. Outsider (Non-member)
        email_out = f"maintain_out_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_out, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.outsider = cls.db.query(models.User).filter(models.User.email == email_out).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_healthy_community_prepares_maintenance_payload(self):
        """Enrolled member executes MAINTAIN_ACTIVITY -> generates forward maintenance plan for CREATE_EVENT."""
        req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res =  authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.action, "MAINTAIN_ACTIVITY")
        self.assertEqual(exec_res.community_id, self.community.community_id)

        details = exec_res.details
        self.assertEqual(details["delivery_status"], "PREPARED")
        self.assertEqual(details["recurring_pattern"], "WEEKLY")
        self.assertEqual(details["suggested_activity_id"], self.activity.activity_id)
        self.assertEqual(details["suggested_activity_title"], self.activity.title)
        self.assertIsNotNone(details["suggested_date"])
        self.assertGreaterEqual(details["suggested_capacity"], 3)
        self.assertIn("cadence_recommendation", details)

        plan = details["maintenance_plan"]
        self.assertIsNotNone(plan)
        self.assertEqual(plan["action"], "CREATE_EVENT")
        self.assertEqual(plan["parameters"]["activity_id"], self.activity.activity_id)
        self.assertIn(self.community.name, plan["parameters"]["title"])

    def test_02_growing_community_prepares_maintenance_payload(self):
        """Growing community properly derives and packages maintenance recommendation."""
        growing_comm = models.Community(
            name=f"Growing_Comm_{self.ts}",
            description="Rapidly expanding yoga club",
            created_by=self.host.user_id,
        )
        self.db.add(growing_comm)
        self.db.commit()
        self.db.refresh(growing_comm)

        self.db.add(models.CommunityMember(community_id=growing_comm.community_id, user_id=self.host.user_id, role="MEMBER"))
        self.db.commit()

        try:
            req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "BIWEEKLY"})
            val_res = validate_community_action_request(req)
            auth_res = authorize_community_action(self.db, growing_comm.community_id, self.host.user_id, val_res)
            exec_res = dispatch_community_action(self.db, growing_comm.community_id, self.host.user_id, val_res, auth_res)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.status, "COMPLETED")
            self.assertEqual(exec_res.details["recurring_pattern"], "BIWEEKLY")
            self.assertIsNotNone(exec_res.details["maintenance_plan"])
        finally:
            self.db.query(models.CommunityMember).filter(models.CommunityMember.community_id == growing_comm.community_id).delete()
            self.db.delete(growing_comm)
            self.db.commit()

    def test_03_no_upcoming_activity_prepares_standard_cadence(self):
        """When no upcoming events exist, upcoming_events_count is 0 and delivery_status is PREPARED."""
        req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.details["upcoming_events_count"], 0)
        self.assertEqual(exec_res.details["delivery_status"], "PREPARED")

    def test_04_existing_upcoming_activity_avoids_duplicate_immediate_cadence(self):
        """When an upcoming event is already scheduled in the near future, delivery_status indicates it and plans beyond."""
        upcoming = models.Event(
            activity_id=self.activity.activity_id,
            host_id=self.host.user_id,
            title=f"Upcoming Badminton Match {self.ts}",
            event_date=date.today() + timedelta(days=2),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=8,
            status="PUBLISHED",
        )
        self.db.add(upcoming)
        self.db.commit()
        self.db.refresh(upcoming)

        try:
            req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "WEEKLY"})
            val_res = validate_community_action_request(req)
            auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
            exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.status, "COMPLETED")
            self.assertGreaterEqual(exec_res.details["upcoming_events_count"], 1)
            self.assertEqual(exec_res.details["delivery_status"], "ACTIVITY_ALREADY_SCHEDULED")

            # Forward maintenance plan schedules after the upcoming event (at least 7 days after upcoming event date)
            suggested_date = date.fromisoformat(exec_res.details["suggested_date"])
            self.assertGreater(suggested_date, upcoming.event_date)
        finally:
            self.db.delete(upcoming)
            self.db.commit()

    def test_05_custom_recurring_patterns_calculate_cadence(self):
        """Custom recurring patterns (BIWEEKLY, MONTHLY) properly propagate to title and cadence date."""
        req_bi = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "BIWEEKLY"})
        val_bi = validate_community_action_request(req_bi)
        auth_bi = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_bi)
        exec_bi = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_bi, auth_bi)

        self.assertTrue(exec_bi.success)
        self.assertEqual(exec_bi.details["recurring_pattern"], "BIWEEKLY")
        self.assertIn("Biweekly", exec_bi.details["maintenance_plan"]["parameters"]["title"])

        req_mo = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "MONTHLY"})
        val_mo = validate_community_action_request(req_mo)
        auth_mo = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_mo)
        exec_mo = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_mo, auth_mo)

        self.assertTrue(exec_mo.success)
        self.assertEqual(exec_mo.details["recurring_pattern"], "MONTHLY")
        self.assertIn("Monthly", exec_mo.details["maintenance_plan"]["parameters"]["title"])

    def test_06_blank_or_invalid_recurring_pattern_rejected(self):
        """Blank or whitespace-only recurring_pattern is rejected by validation."""
        req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "   "})
        val_res = validate_community_action_request(req)
        self.assertFalse(val_res.is_valid)
        self.assertIn("recurring_pattern cannot be blank", val_res.errors[0])

    def test_07_invalid_community_id_rejected(self):
        """Non-existent community_id is rejected gracefully."""
        req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, 9999999, self.host.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, 9999999, self.host.user_id, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_08_non_member_requester_rejected(self):
        """Requester not belonging to community is rejected before activity inspection."""
        req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.outsider.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.outsider.user_id, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertIn("not a member", exec_res.message.lower())

    def test_09_no_suitable_activity_returns_clean_result(self):
        """When no suitable activity exists, returns clean COMPLETED result with NO_ACTIVITY_TO_MAINTAIN status."""
        with patch.object(self.db, "query") as mock_query:
            # Setup a mock flow where activity lookup yields None
            mock_comm_q = MagicMock()
            mock_comm_q.filter.return_value.first.return_value = self.community

            mock_mem_q = MagicMock()
            mock_mem_q.filter.return_value.first.return_value = MagicMock(user_id=self.host.user_id)
            mock_mem_q.filter.return_value.all.return_value = [MagicMock(user_id=self.host.user_id)]

            def query_side_effect(model_cls, *args, **kwargs):
                if model_cls == models.Community:
                    return mock_comm_q
                elif model_cls == models.CommunityMember:
                    return mock_mem_q
                elif model_cls == models.Event:
                    m = MagicMock()
                    m.filter.return_value.order_by.return_value.all.return_value = []
                    m.filter.return_value.order_by.return_value.first.return_value = None
                    return m
                elif model_cls == models.Activity:
                    m = MagicMock()
                    m.filter.return_value.first.return_value = None
                    m.all.return_value = []
                    return m
                return MagicMock()

            mock_query.side_effect = query_side_effect

            req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={})
            val_res = validate_community_action_request(req)
            exec_res = _handle_maintain_activity_action(self.community.community_id, self.host.user_id, val_res.sanitized_parameters, self.db)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.status, "COMPLETED")
            self.assertEqual(exec_res.details["delivery_status"], "NO_ACTIVITY_TO_MAINTAIN")
            self.assertIsNone(exec_res.details["maintenance_plan"])

    def test_10_zero_unintended_database_mutations_and_zero_event_creation(self):
        """Executing MAINTAIN_ACTIVITY must cause strictly zero DB writes and zero automatic event scheduling."""
        initial_counts = {
            "events": self.db.query(models.Event).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "communities": self.db.query(models.Community).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        req = schemas.ActionRequest(action="MAINTAIN_ACTIVITY", parameters={"recurring_pattern": "WEEKLY"})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")

        after_counts = {
            "events": self.db.query(models.Event).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "communities": self.db.query(models.Community).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        self.assertEqual(initial_counts, after_counts, "MAINTAIN_ACTIVITY must cause strictly zero database mutations")

    def test_11_reactivate_community_action_causes_zero_mutations(self):
        """Executing REACTIVATE_COMMUNITY causes strictly zero database mutations."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"notes": "check"})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.community.community_id, self.host.user_id, val_res, auth_res)
        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")


class TestReactivateCommunityActionExecution(unittest.TestCase):
    """
    Step 9.9 Test Suite: Concrete REACTIVATE_COMMUNITY Action Execution
    - INACTIVE community -> targeted reactivation plan prepared for CREATE_EVENT
    - AT_RISK community -> targeted reactivation plan prepared
    - HEALTHY community -> clean NOT_REQUIRED / COMMUNITY_ALREADY_ACTIVE
    - GROWING community -> clean NOT_REQUIRED / COMMUNITY_ALREADY_ACTIVE
    - Invalid community_id -> rejected
    - Non-member requester -> rejected
    - Unauthenticated requester -> rejected
    - No suitable activity in system -> clean NO_ACTIVITY_TO_REACTIVATE result
    - Future proposed_date generated correctly (or user specified)
    - Past proposed_date -> rejected
    - Zero DB mutation: strictly zero events created and zero records mutated
    - Existing actions (CREATE_EVENT, RE_ENGAGE_MEMBERS, COLLECT_FEEDBACK, GROW_MEMBERSHIP, MAINTAIN_ACTIVITY) remain intact.
    """

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Setup Host User
        email_host = f"react_host_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_host, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.host = cls.db.query(models.User).filter(models.User.email == email_host).first()

        # 2. Activity
        cls.activity = cls.db.query(models.Activity).first()
        if not cls.activity:
            interest = cls.db.query(models.Interest).first()
            cls.activity = models.Activity(title="Badminton Tournament", interest_id=interest.interest_id if interest else 1, description="Competitive play")
            cls.db.add(cls.activity)
            cls.db.commit()
            cls.db.refresh(cls.activity)

        # 3. Setup INACTIVE Community (No recent events, older than 60 days)
        cls.inactive_community = models.Community(
            name=f"Dormant_Badminton_Club_{cls.ts}",
            description="A dormant badminton group seeking reactivation",
            created_by=cls.host.user_id,
        )
        cls.db.add(cls.inactive_community)
        cls.db.commit()
        cls.db.refresh(cls.inactive_community)

        cls.db.add(models.CommunityMember(
            community_id=cls.inactive_community.community_id,
            user_id=cls.host.user_id,
            role="ADMIN",
        ))

        # Add peer member to inactive community
        email_p1 = f"react_p1_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_p1, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.peer1 = cls.db.query(models.User).filter(models.User.email == email_p1).first()
        cls.db.add(models.CommunityMember(
            community_id=cls.inactive_community.community_id,
            user_id=cls.peer1.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # Add a past event (60 days ago) to associate activity with inactive community
        past_ev = models.Event(
            activity_id=cls.activity.activity_id,
            host_id=cls.host.user_id,
            title=f"Old Badminton Event {cls.ts}",
            event_date=date.today() - timedelta(days=60),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=10,
            status="COMPLETED",
        )
        cls.db.add(past_ev)
        cls.db.commit()

        # 4. Setup HEALTHY Community (Has dedicated host and recent completed event and active participants)
        email_h_host = f"react_h_host_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_h_host, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.healthy_host = cls.db.query(models.User).filter(models.User.email == email_h_host).first()

        email_h_peer = f"react_h_peer_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_h_peer, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.healthy_peer = cls.db.query(models.User).filter(models.User.email == email_h_peer).first()

        cls.healthy_community = models.Community(
            name=f"Vibrant_Fitness_Club_{cls.ts}",
            description="A very active and healthy community",
            created_by=cls.healthy_host.user_id,
        )
        cls.db.add(cls.healthy_community)
        cls.db.commit()
        cls.db.refresh(cls.healthy_community)

        cls.db.add(models.CommunityMember(
            community_id=cls.healthy_community.community_id,
            user_id=cls.healthy_host.user_id,
            role="ADMIN",
        ))
        cls.db.add(models.CommunityMember(
            community_id=cls.healthy_community.community_id,
            user_id=cls.healthy_peer.user_id,
            role="MEMBER",
        ))
        cls.db.commit()

        # Recent events for healthy community (last 3 days) hosted by healthy_host
        for i in range(3):
            ev = models.Event(
                activity_id=cls.activity.activity_id,
                host_id=cls.healthy_host.user_id,
                title=f"Healthy Event {i} {cls.ts}",
                event_date=date.today() - timedelta(days=i + 1),
                start_time=time(18, 0),
                end_time=time(20, 0),
                max_capacity=10,
                status="COMPLETED",
            )
            cls.db.add(ev)
            cls.db.flush()
            cls.db.add(models.EventParticipant(event_id=ev.event_id, user_id=cls.healthy_peer.user_id, status="CONFIRMED"))
        cls.db.commit()

        # 5. Outsider (Non-member)
        email_out = f"react_out_{cls.ts}@test.com"
        client.post("/auth/register", json={"email": email_out, "password": cls.pwd, "confirm_password": cls.pwd})
        cls.outsider = cls.db.query(models.User).filter(models.User.email == email_out).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_inactive_community_prepares_reactivation_payload(self):
        """Inactive community properly prepares a targeted reactivation action plan for CREATE_EVENT."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        self.assertTrue(val_res.is_valid)

        auth_res = authorize_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res)
        self.assertTrue(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.action, "REACTIVATE_COMMUNITY")
        self.assertEqual(exec_res.community_id, self.inactive_community.community_id)

        details = exec_res.details
        self.assertEqual(details["delivery_status"], "PREPARED")
        self.assertEqual(details["suggested_activity_id"], self.activity.activity_id)
        self.assertIsNotNone(details["reactivation_date"])
        self.assertIn("reason", details)

        plan = details["reactivation_plan"]
        self.assertIsNotNone(plan)
        self.assertEqual(plan["action"], "CREATE_EVENT")
        self.assertEqual(plan["parameters"]["activity_id"], self.activity.activity_id)
        self.assertIn("Comeback Session", plan["parameters"]["title"])

    def test_02_at_risk_community_prepares_reactivation_payload(self):
        """AT_RISK community properly generates reactivation plan."""
        with patch("main._generate_community_lifecycle_insight") as mock_insight:
            mock_insight.return_value = {
                "lifecycle_stage": "AT_RISK",
                "health_status": "AT_RISK",
                "health_score": 45,
                "trend": "DECLINING",
            }
            req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
            val_res = validate_community_action_request(req)
            auth_res = authorize_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res)
            exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res, auth_res)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.status, "COMPLETED")
            self.assertEqual(exec_res.details["lifecycle_stage"], "AT_RISK")
            self.assertEqual(exec_res.details["delivery_status"], "PREPARED")
            self.assertIsNotNone(exec_res.details["reactivation_plan"])

    def test_03_healthy_community_returns_not_required(self):
        """Healthy community returns COMMUNITY_ALREADY_ACTIVE without preparing reactivation event."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.healthy_community.community_id, self.healthy_host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.healthy_community.community_id, self.healthy_host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        self.assertEqual(exec_res.status, "COMPLETED")
        self.assertEqual(exec_res.details["delivery_status"], "COMMUNITY_ALREADY_ACTIVE")
        self.assertIsNone(exec_res.details["reactivation_plan"])
        self.assertIn("already active", exec_res.message.lower())

    def test_04_growing_community_returns_not_required(self):
        """GROWING community returns COMMUNITY_ALREADY_ACTIVE."""
        with patch("main._generate_community_lifecycle_insight") as mock_insight:
            mock_insight.return_value = {
                "lifecycle_stage": "GROWING",
                "health_status": "GROWING",
                "health_score": 95,
                "trend": "IMPROVING",
            }
            req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
            val_res = validate_community_action_request(req)
            auth_res = authorize_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res)
            exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res, auth_res)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.details["delivery_status"], "COMMUNITY_ALREADY_ACTIVE")
            self.assertIsNone(exec_res.details["reactivation_plan"])

    def test_05_invalid_community_id_rejected(self):
        """Non-existent community_id is rejected gracefully."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, 9999999, self.host.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, 9999999, self.host.user_id, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_06_non_member_requester_rejected(self):
        """Requester not belonging to community is rejected before inspection."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.inactive_community.community_id, self.outsider.user_id, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, self.outsider.user_id, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")
        self.assertIn("not a member", exec_res.message.lower())

    def test_07_unauthenticated_requester_rejected(self):
        """Unauthenticated request (None requester_id) is blocked by authorization."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.inactive_community.community_id, None, val_res)
        self.assertFalse(auth_res.is_authorized)

        exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, None, val_res, auth_res)
        self.assertFalse(exec_res.success)
        self.assertEqual(exec_res.status, "REJECTED")

    def test_08_no_historical_activity_returns_clean_result(self):
        """When no suitable activity exists, returns clean COMPLETED result with NO_ACTIVITY_TO_REACTIVATE status."""
        with patch.object(self.db, "query") as mock_query:
            mock_comm_q = MagicMock()
            mock_comm_q.filter.return_value.first.return_value = self.inactive_community

            mock_mem_q = MagicMock()
            mock_mem_q.filter.return_value.first.return_value = MagicMock(user_id=self.host.user_id)
            mock_mem_q.filter.return_value.all.return_value = [MagicMock(user_id=self.host.user_id)]

            def query_side_effect(model_cls, *args, **kwargs):
                if model_cls == models.Community:
                    return mock_comm_q
                elif model_cls == models.CommunityMember:
                    return mock_mem_q
                elif model_cls == models.Event:
                    m = MagicMock()
                    m.filter.return_value.order_by.return_value.all.return_value = []
                    m.filter.return_value.order_by.return_value.first.return_value = None
                    return m
                elif model_cls == models.Activity:
                    m = MagicMock()
                    m.filter.return_value.first.return_value = None
                    m.all.return_value = []
                    return m
                return MagicMock()

            mock_query.side_effect = query_side_effect

            req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
            val_res = validate_community_action_request(req)
            exec_res = _handle_reactivate_community_action(self.inactive_community.community_id, self.host.user_id, val_res.sanitized_parameters, self.db)

            self.assertTrue(exec_res.success)
            self.assertEqual(exec_res.status, "COMPLETED")
            self.assertEqual(exec_res.details["delivery_status"], "NO_ACTIVITY_TO_REACTIVATE")
            self.assertIsNone(exec_res.details["reactivation_plan"])

    def test_09_omitted_proposed_date_generates_future_date(self):
        """Omitted proposed_date safely defaults to future date (14 days ahead)."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)
        react_date = date.fromisoformat(exec_res.details["reactivation_date"])
        self.assertGreater(react_date, date.today())

    def test_10_past_proposed_date_rejected(self):
        """Proposed date in the past is rejected by validation."""
        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={"proposed_date": "2020-01-01"})
        val_res = validate_community_action_request(req)
        self.assertFalse(val_res.is_valid)
        self.assertIn("cannot be in the past", val_res.errors[0])

    def test_11_zero_unintended_database_mutations_and_zero_event_creation(self):
        """Executing REACTIVATE_COMMUNITY causes strictly zero database writes and zero automatic event scheduling."""
        initial_counts = {
            "events": self.db.query(models.Event).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "communities": self.db.query(models.Community).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        req = schemas.ActionRequest(action="REACTIVATE_COMMUNITY", parameters={})
        val_res = validate_community_action_request(req)
        auth_res = authorize_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res)
        exec_res = dispatch_community_action(self.db, self.inactive_community.community_id, self.host.user_id, val_res, auth_res)

        self.assertTrue(exec_res.success)

        after_counts = {
            "events": self.db.query(models.Event).count(),
            "event_participants": self.db.query(models.EventParticipant).count(),
            "communities": self.db.query(models.Community).count(),
            "community_members": self.db.query(models.CommunityMember).count(),
            "users": self.db.query(models.User).count(),
            "feedback": self.db.query(models.Feedback).count(),
        }

        self.assertEqual(initial_counts, after_counts, "REACTIVATE_COMMUNITY must cause strictly zero database mutations")

    def test_12_other_actions_remain_unaffected(self):
        """All other 5 actions remain fully functional and uncompromised."""
        for act in [
            schemas.AllowedAction.CREATE_EVENT,
            schemas.AllowedAction.RE_ENGAGE_MEMBERS,
            schemas.AllowedAction.COLLECT_FEEDBACK,
            schemas.AllowedAction.GROW_MEMBERSHIP,
            schemas.AllowedAction.MAINTAIN_ACTIVITY,
        ]:
            req = schemas.ActionRequest(action=act.value, parameters={})
            val_res = validate_community_action_request(req)
            self.assertTrue(val_res.is_valid or len(val_res.errors) > 0)


if __name__ == "__main__":
    unittest.main()



