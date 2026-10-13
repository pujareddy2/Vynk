"""
Step 10.1 — Notification Domain Contract & Model Unit Tests
Tests:
1. Notification creation with valid data
2. Invalid recipient rejected (non-existent user)
3. Invalid notification type rejected
4. Required title/message validation
5. Optional JSON payload accepted
6. Notification linked to community/event correctly
7. Default UNREAD state
8. Default is_read=False
9. Mark unread -> read
10. read_at populated
11. Read notification cannot become unread
12. Dismiss transition works
13. Accept transition works for actionable types
14. Invalid status transition rejected (informational cannot be accepted; terminal cannot transition)
15. User can only access their own notifications (scoping)
16. Cascade behavior when recipient user is deleted
17. Community/event SET NULL behavior when related entity is deleted
"""

from datetime import date, datetime, time, timedelta
import time as time_mod
import unittest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from database import SessionLocal
from main import app
import models
import schemas
from notification_service import (
    create_notification,
    batch_create_notifications,
    mark_notification_as_read,
    accept_notification,
    dismiss_notification,
    execute_notification_action,
    is_notification_stale,
    compute_notification_idempotency_key,
    find_existing_duplicate_notification,
    NotificationServiceError,
)


class TestNotificationDomainContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)

        # 1. Create primary recipient user
        cls.user1 = models.User(
            email=f"notif_user1_{cls.ts}@test.com",
            password_hash="mock_hash_123",
            is_active=True,
            is_verified=True,
        )
        # 2. Create peer recipient user
        cls.user2 = models.User(
            email=f"notif_user2_{cls.ts}@test.com",
            password_hash="mock_hash_123",
            is_active=True,
            is_verified=True,
        )
        cls.db.add_all([cls.user1, cls.user2])
        cls.db.commit()
        cls.db.refresh(cls.user1)
        cls.db.refresh(cls.user2)

        # 3. Create sample community
        cls.community = models.Community(
            name=f"Notification Club {cls.ts}",
            description="Testing notification linkages",
            created_by=cls.user1.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        # 4. Activity & Event
        interest = cls.db.query(models.Interest).first()
        activity = cls.db.query(models.Activity).first()
        if not activity:
            activity = models.Activity(
                title=f"Notif Activity {cls.ts}",
                interest_id=interest.interest_id if interest else 1,
            )
            cls.db.add(activity)
            cls.db.commit()
            cls.db.refresh(activity)

        cls.event = models.Event(
            activity_id=activity.activity_id,
            host_id=cls.user1.user_id,
            title=f"Notif Event {cls.ts}",
            event_date=date.today() + timedelta(days=5),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=10,
            status="PUBLISHED",
        )
        cls.db.add(cls.event)
        cls.db.commit()
        cls.db.refresh(cls.event)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_notification_creation_with_valid_data(self):
        """Notification entity persists cleanly with valid fields."""
        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="Welcome to Vynk",
            message="Your account setup is complete.",
            payload={"source": "onboarding", "step": 1},
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertIsNotNone(notif.notification_id)
        self.assertEqual(notif.recipient_user_id, self.user1.user_id)
        self.assertEqual(notif.notification_type, "SYSTEM_ALERT")
        self.assertEqual(notif.title, "Welcome to Vynk")
        self.assertEqual(notif.message, "Your account setup is complete.")
        self.assertEqual(notif.payload, {"source": "onboarding", "step": 1})
        self.assertIsNotNone(notif.created_at)

    def test_02_invalid_recipient_rejected_by_fk(self):
        """Non-existent recipient_user_id violates foreign key constraint in database."""
        notif = models.Notification(
            recipient_user_id=99999999,  # Non-existent user
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="Ghost Notification",
            message="Nobody should receive this.",
        )
        self.db.add(notif)
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()

    def test_03_invalid_notification_type_rejected_by_schema(self):
        """NotificationCreate rejects invalid enum notification_type."""
        with self.assertRaises(ValidationError):
            schemas.NotificationCreate(
                recipient_user_id=self.user1.user_id,
                notification_type="INVALID_NON_EXISTENT_TYPE",  # Invalid type
                title="Invalid type test",
                message="Testing schema validation",
            )

    def test_04_required_title_and_message_validated(self):
        """Empty title or message is rejected by Pydantic contract."""
        with self.assertRaises(ValidationError):
            schemas.NotificationCreate(
                recipient_user_id=self.user1.user_id,
                notification_type=schemas.NotificationType.SYSTEM_ALERT,
                title="",  # Empty title
                message="Valid message",
            )

        with self.assertRaises(ValidationError):
            schemas.NotificationCreate(
                recipient_user_id=self.user1.user_id,
                notification_type=schemas.NotificationType.SYSTEM_ALERT,
                title="Valid Title",
                message="",  # Empty message
            )

    def test_05_optional_json_payload_accepted(self):
        """Complex JSON payload dictionaries are preserved faithfully."""
        complex_payload = {
            "action_id": "RE_ENGAGE_MEMBERS",
            "target_days": 14,
            "metadata": {"nested": True, "count": 42},
            "tags": ["social", "sports"],
        }
        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.RE_ENGAGEMENT.value,
            title="We miss you",
            message="Come back to the community!",
            payload=complex_payload,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertEqual(notif.payload, complex_payload)
        self.assertEqual(notif.payload["metadata"]["count"], 42)

    def test_06_notification_linked_to_community_and_event(self):
        """Notifications associate with related community and event records."""
        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.FEEDBACK_REQUEST.value,
            title="How was the match?",
            message="Share your review for Badminton.",
            related_community_id=self.community.community_id,
            related_event_id=self.event.event_id,
            source_action="COLLECT_FEEDBACK",
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertEqual(notif.related_community_id, self.community.community_id)
        self.assertEqual(notif.related_event_id, self.event.event_id)
        self.assertEqual(notif.source_action, "COLLECT_FEEDBACK")
        self.assertEqual(notif.community.name, self.community.name)
        self.assertEqual(notif.event.title, self.event.title)

    def test_07_default_unread_status(self):
        """Newly created notification defaults to status='UNREAD'."""
        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="Default Status Check",
            message="Checking default status value.",
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertEqual(notif.status, "UNREAD")

    def test_08_default_is_read_is_false(self):
        """Newly created notification defaults to is_read=False and read_at=None."""
        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="Default is_read Check",
            message="Checking default read flags.",
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

    def test_09_mark_unread_to_read(self):
        """Transitioning from UNREAD to READ validates and updates status and is_read."""
        valid, err = schemas.validate_notification_status_transition("UNREAD", "READ", "SYSTEM_ALERT")
        self.assertTrue(valid)
        self.assertIsNone(err)

        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="Read Transition Check",
            message="Marking this as read.",
        )
        self.db.add(notif)
        self.db.commit()

        # Apply transition
        notif.status = "READ"
        notif.is_read = True
        notif.read_at = datetime.now()
        self.db.commit()
        self.db.refresh(notif)

        self.assertEqual(notif.status, "READ")
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)

    def test_10_read_at_populated_on_read(self):
        """read_at timestamp is populated when notification becomes READ."""
        before = datetime.now()
        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="Timestamp Check",
            message="Verifying read_at timestamp.",
            is_read=True,
            status="READ",
            read_at=datetime.now(),
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        self.assertIsNotNone(notif.read_at)
        self.assertGreaterEqual(notif.read_at.replace(tzinfo=None), before - timedelta(seconds=1))

    def test_11_read_notification_cannot_become_unread(self):
        """Contract strictly rejects transitioning a READ notification back to UNREAD."""
        valid, err = schemas.validate_notification_status_transition("READ", "UNREAD", "SYSTEM_ALERT")
        self.assertFalse(valid)
        self.assertIn("Cannot transition read or resolved notification back to UNREAD", err)

    def test_12_dismiss_transition_works_from_unread_and_read(self):
        """DISMISSED transition succeeds from both UNREAD and READ states."""
        # From UNREAD
        valid, err = schemas.validate_notification_status_transition("UNREAD", "DISMISSED", "SYSTEM_ALERT")
        self.assertTrue(valid)
        self.assertIsNone(err)

        # From READ
        valid, err = schemas.validate_notification_status_transition("READ", "DISMISSED", "SYSTEM_ALERT")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_13_accept_transition_works_for_actionable_types(self):
        """Actionable notifications (COMMUNITY_INVITATION, ACTIVITY_MAINTENANCE, COMMUNITY_REACTIVATION) can be ACCEPTED."""
        for act_type in schemas.ACTIONABLE_NOTIFICATION_TYPES:
            valid, err = schemas.validate_notification_status_transition("UNREAD", "ACCEPTED", act_type)
            self.assertTrue(valid, f"Expected {act_type} to allow ACCEPT transition from UNREAD")
            self.assertIsNone(err)

            valid, err = schemas.validate_notification_status_transition("READ", "ACCEPTED", act_type)
            self.assertTrue(valid, f"Expected {act_type} to allow ACCEPT transition from READ")
            self.assertIsNone(err)

    def test_14_invalid_status_transition_rejected(self):
        """
        Rejects:
        1. Accepting informational notifications (RE_ENGAGEMENT, FEEDBACK_REQUEST, SYSTEM_ALERT)
        2. Transitioning out of terminal state DISMISSED
        3. Transitioning out of terminal state ACCEPTED
        """
        # 1. Informational types cannot be accepted
        for info_type in schemas.INFORMATIONAL_NOTIFICATION_TYPES:
            valid, err = schemas.validate_notification_status_transition("UNREAD", "ACCEPTED", info_type)
            self.assertFalse(valid)
            self.assertIn("informational and cannot be accepted", err)

        # 2. Terminal DISMISSED cannot change
        valid, err = schemas.validate_notification_status_transition("DISMISSED", "READ", "COMMUNITY_INVITATION")
        self.assertFalse(valid)
        self.assertIn("terminal state", err)

        # 3. Terminal ACCEPTED cannot change
        valid, err = schemas.validate_notification_status_transition("ACCEPTED", "DISMISSED", "COMMUNITY_INVITATION")
        self.assertFalse(valid)
        self.assertIn("terminal state", err)

    def test_15_user_can_only_access_their_own_notifications(self):
        """Scoped query ensures User 1 cannot see User 2's notifications."""
        # Notification for User 1
        n1 = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="User 1 Note",
            message="Private to user 1",
        )
        # Notification for User 2
        n2 = models.Notification(
            recipient_user_id=self.user2.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="User 2 Note",
            message="Private to user 2",
        )
        self.db.add_all([n1, n2])
        self.db.commit()

        user1_inbox = self.db.query(models.Notification).filter(models.Notification.recipient_user_id == self.user1.user_id).all()
        user1_ids = {n.notification_id for n in user1_inbox}

        self.assertIn(n1.notification_id, user1_ids)
        self.assertNotIn(n2.notification_id, user1_ids)

    def test_16_cascade_behavior_when_recipient_user_deleted(self):
        """Deleting a user cascades and removes all their notifications."""
        temp_user = models.User(
            email=f"cascade_user_{int(time_mod.time() * 1000)}@test.com",
            password_hash="mock_hash_123",
            is_active=True,
            is_verified=True,
        )
        self.db.add(temp_user)
        self.db.commit()
        self.db.refresh(temp_user)

        notif = models.Notification(
            recipient_user_id=temp_user.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT.value,
            title="To be cascaded",
            message="This should delete with user.",
        )
        self.db.add(notif)
        self.db.commit()
        notif_id = notif.notification_id

        # Delete user
        self.db.delete(temp_user)
        self.db.commit()

        # Verify notification was deleted via CASCADE
        found = self.db.query(models.Notification).filter(models.Notification.notification_id == notif_id).first()
        self.assertIsNone(found, "Notification must be cascaded on user deletion")

    def test_17_community_and_event_set_null_behavior(self):
        """Deleting a related community or event sets related_community_id or related_event_id to NULL without deleting notification."""
        temp_comm = models.Community(
            name=f"SetNull Comm {int(time_mod.time() * 1000)}",
            description="Testing SET NULL behavior",
            created_by=self.user1.user_id,
        )
        self.db.add(temp_comm)
        self.db.commit()
        self.db.refresh(temp_comm)

        notif = models.Notification(
            recipient_user_id=self.user1.user_id,
            notification_type=schemas.NotificationType.COMMUNITY_INVITATION.value,
            title="Invitation to temp club",
            message="Join this temp club",
            related_community_id=temp_comm.community_id,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        notif_id = notif.notification_id

        self.assertEqual(notif.related_community_id, temp_comm.community_id)

        # Delete community
        self.db.delete(temp_comm)
        self.db.commit()

        # Notification still exists, but related_community_id is NULL
        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif_id).first()
        self.assertIsNotNone(persisted, "Notification should not be deleted when related community is deleted")
        self.assertIsNone(persisted.related_community_id, "related_community_id must be set to NULL")


# ============================================================================
# Step 10.2: Notification Creation / Delivery Service Tests
# ============================================================================

class TestNotificationService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)

        # Recipient user
        cls.user = models.User(
            email=f"service_notif_user_{cls.ts}@test.com",
            password_hash="mock_hash_123",
            is_active=True,
            is_verified=True,
        )
        cls.db.add(cls.user)
        cls.db.commit()
        cls.db.refresh(cls.user)

        # Community
        cls.community = models.Community(
            name=f"Service Community {cls.ts}",
            description="Testing service linkages",
            created_by=cls.user.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        # Activity & Event
        interest = cls.db.query(models.Interest).first()
        activity = cls.db.query(models.Activity).first()
        if not activity:
            activity = models.Activity(
                title=f"Service Activity {cls.ts}",
                interest_id=interest.interest_id if interest else 1,
            )
            cls.db.add(activity)
            cls.db.commit()
            cls.db.refresh(activity)

        cls.event = models.Event(
            activity_id=activity.activity_id,
            host_id=cls.user.user_id,
            title=f"Service Event {cls.ts}",
            event_date=date.today() + timedelta(days=7),
            start_time=time(19, 0),
            end_time=time(21, 0),
            max_capacity=8,
            status="PUBLISHED",
        )
        cls.db.add(cls.event)
        cls.db.commit()
        cls.db.refresh(cls.event)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_create_valid_notification(self):
        """Service creates and persists a valid notification entity."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT,
            title="Service Alert",
            message="Created via Notification Service.",
        )
        notif = create_notification(self.db, req)

        self.assertIsNotNone(notif.notification_id)
        self.assertEqual(notif.title, "Service Alert")
        self.assertEqual(notif.message, "Created via Notification Service.")
        self.assertEqual(notif.status, "UNREAD")
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

    def test_02_correct_recipient_persisted(self):
        """Service persists notification associated with the designated recipient."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.RE_ENGAGEMENT,
            title="Re-engagement Alert",
            message="We miss you in the badminton circle!",
        )
        notif = create_notification(self.db, req)
        self.assertEqual(notif.recipient_user_id, self.user.user_id)

    def test_03_correct_notification_type_persisted(self):
        """Service correctly serializes and stores the notification_type string."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.COMMUNITY_INVITATION,
            title="Join the club",
            message="You have been invited to join.",
        )
        notif = create_notification(self.db, req)
        self.assertEqual(notif.notification_type, "COMMUNITY_INVITATION")

    def test_04_payload_preserved(self):
        """Service preserves arbitrary nested payload dictionary faithfully."""
        custom_payload = {
            "source": "GROW_MEMBERSHIP",
            "score": 92,
            "reasons": ["Nearby locality", "Shared interest in Badminton"],
            "inviter_id": self.user.user_id,
        }
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.COMMUNITY_INVITATION,
            title="Payload Preservation Test",
            message="Checking payload preservation.",
            payload=custom_payload,
        )
        notif = create_notification(self.db, req)
        self.assertEqual(notif.payload, custom_payload)
        self.assertEqual(notif.payload["score"], 92)

    def test_05_community_and_event_relationships_preserved(self):
        """Service correctly links related community and event foreign keys."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.FEEDBACK_REQUEST,
            title="Rate your event",
            message="How was your session?",
            related_community_id=self.community.community_id,
            related_event_id=self.event.event_id,
            source_action="COLLECT_FEEDBACK",
        )
        notif = create_notification(self.db, req)
        self.assertEqual(notif.related_community_id, self.community.community_id)
        self.assertEqual(notif.related_event_id, self.event.event_id)
        self.assertEqual(notif.source_action, "COLLECT_FEEDBACK")

    def test_06_default_unread_state_preserved(self):
        """Service defaults status to UNREAD and is_read to False."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.ACTIVITY_MAINTENANCE,
            title="Cadence Reminder",
            message="Time to maintain activity.",
        )
        notif = create_notification(self.db, req)
        self.assertEqual(notif.status, "UNREAD")
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

    def test_07_invalid_recipient_rejected(self):
        """Service raises NotificationServiceError when recipient user does not exist in DB."""
        req = schemas.NotificationCreate(
            recipient_user_id=99999999,  # Non-existent
            notification_type=schemas.NotificationType.SYSTEM_ALERT,
            title="Invalid Recipient",
            message="Should fail validation.",
        )
        with self.assertRaises(NotificationServiceError) as ctx:
            create_notification(self.db, req)
        self.assertIn("does not exist", str(ctx.exception))

    def test_08_invalid_notification_type_rejected(self):
        """Service rejects invalid notification types when passing raw payload dict."""
        raw_dict = {
            "recipient_user_id": self.user.user_id,
            "notification_type": "UNKNOWN_BOGUS_TYPE",
            "title": "Bogus Type",
            "message": "Should be rejected.",
        }
        with self.assertRaises(NotificationServiceError):
            create_notification(self.db, raw_dict)

    def test_09_informational_notification_cannot_be_created_in_accepted_state(self):
        """Service rejects initializing an informational notification with actionable state ACCEPTED."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.FEEDBACK_REQUEST,
            title="Feedback cannot be accepted",
            message="Testing state gate.",
        )
        with self.assertRaises(NotificationServiceError) as ctx:
            create_notification(self.db, req, initial_status="ACCEPTED")
        self.assertIn("cannot be accepted", str(ctx.exception))

    def test_10_database_failure_rolls_back_cleanly(self):
        """Batch creation rolls back completely if any single notification is invalid."""
        count_before = self.db.query(models.Notification).count()

        valid_notif = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.SYSTEM_ALERT,
            title="Batch Valid Record",
            message="Valid message",
        )
        invalid_notif = {
            "recipient_user_id": 99999999,  # Non-existent user triggers rollback
            "notification_type": "SYSTEM_ALERT",
            "title": "Batch Bad Record",
            "message": "Bad message",
        }

        with self.assertRaises(NotificationServiceError):
            batch_create_notifications(self.db, [valid_notif, invalid_notif])

        count_after = self.db.query(models.Notification).count()
        self.assertEqual(count_before, count_after, "Batch failure must roll back all inserts atomically")

    def test_11_returned_object_matches_persisted_record(self):
        """Attributes on returned entity match fresh database record query."""
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.COMMUNITY_REACTIVATION,
            title="Comeback Session",
            message="Reactivate your community with a badminton session.",
            payload={"action": "CREATE_EVENT", "date": "2026-10-26"},
            related_community_id=self.community.community_id,
        )
        created = create_notification(self.db, req)

        # Fresh DB query
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == created.notification_id).first()
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.notification_id, created.notification_id)
        self.assertEqual(persisted.recipient_user_id, created.recipient_user_id)
        self.assertEqual(persisted.title, created.title)
        self.assertEqual(persisted.message, created.message)
        self.assertEqual(persisted.notification_type, created.notification_type)
        self.assertEqual(persisted.payload, created.payload)
        self.assertEqual(persisted.related_community_id, created.related_community_id)
        self.assertEqual(persisted.status, created.status)
        self.assertEqual(persisted.is_read, created.is_read)

    def test_12_dict_payload_normalized_and_persisted(self):
        """Service transparently normalizes raw dictionary inputs through schema validation."""
        raw_input = {
            "recipient_user_id": self.user.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Dict Input Test",
            "message": "Created from plain dictionary.",
            "payload": {"key": "value"},
        }
        notif = create_notification(self.db, raw_input)
        self.assertIsNotNone(notif.notification_id)
        self.assertEqual(notif.title, "Dict Input Test")
        self.assertEqual(notif.payload, {"key": "value"})


# ============================================================================
# Step 10.3: User Inbox API Tests (GET /notifications)
# ============================================================================

class TestNotificationInboxAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. Register & login User A
        email_a = f"inbox_user_a_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email_a, "password": cls.pwd, "confirm_password": cls.pwd})
        res_a = cls.client.post("/auth/login", json={"email": email_a, "password": cls.pwd}).json()
        cls.token_a = res_a["access_token"]
        cls.headers_a = {"Authorization": f"Bearer {cls.token_a}"}
        cls.user_a = cls.db.query(models.User).filter(models.User.email == email_a).first()

        # 2. Register & login User B
        email_b = f"inbox_user_b_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email_b, "password": cls.pwd, "confirm_password": cls.pwd})
        res_b = cls.client.post("/auth/login", json={"email": email_b, "password": cls.pwd}).json()
        cls.token_b = res_b["access_token"]
        cls.headers_b = {"Authorization": f"Bearer {cls.token_b}"}
        cls.user_b = cls.db.query(models.User).filter(models.User.email == email_b).first()

        # 3. Register & login User C (Empty inbox)
        email_c = f"inbox_user_c_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email_c, "password": cls.pwd, "confirm_password": cls.pwd})
        res_c = cls.client.post("/auth/login", json={"email": email_c, "password": cls.pwd}).json()
        cls.token_c = res_c["access_token"]
        cls.headers_c = {"Authorization": f"Bearer {cls.token_c}"}
        cls.user_c = cls.db.query(models.User).filter(models.User.email == email_c).first()

        # 4. Seed User A notifications:
        # 3 unread
        cls.notif_a1 = create_notification(cls.db, {
            "recipient_user_id": cls.user_a.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Welcome Alert",
            "message": "Welcome to Vynk!",
        })
        time_mod.sleep(0.01)
        cls.notif_a2 = create_notification(cls.db, {
            "recipient_user_id": cls.user_a.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Badminton Club Invite",
            "message": "You have been invited to Badminton Club.",
            "payload": {"community_id": 10},
        })
        time_mod.sleep(0.01)
        cls.notif_a3 = create_notification(cls.db, {
            "recipient_user_id": cls.user_a.user_id,
            "notification_type": "FEEDBACK_REQUEST",
            "title": "Feedback on Weekend Match",
            "message": "Please rate your experience.",
        })
        time_mod.sleep(0.01)

        # 2 read
        cls.notif_a4 = create_notification(cls.db, {
            "recipient_user_id": cls.user_a.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Maintain Badminton Streak",
            "message": "Keep up the momentum.",
        }, initial_status="READ")
        time_mod.sleep(0.01)
        cls.notif_a5 = create_notification(cls.db, {
            "recipient_user_id": cls.user_a.user_id,
            "notification_type": "RE_ENGAGEMENT",
            "title": "We miss you",
            "message": "Come back soon.",
        }, initial_status="READ")

        # 5. Seed User B notification (1 unread)
        cls.notif_b1 = create_notification(cls.db, {
            "recipient_user_id": cls.user_b.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "User B Secret Notice",
            "message": "Only User B should see this.",
        })

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_authenticated_user_gets_own_notifications(self):
        """Authenticated user successfully retrieves their own notifications."""
        res = self.client.get("/notifications", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 5)
        self.assertEqual(len(data["notifications"]), 5)
        self.assertEqual(data["unread_count"], 3)
        for n in data["notifications"]:
            self.assertEqual(n["recipient_user_id"], self.user_a.user_id)

    def test_02_user_cannot_see_another_users_notifications(self):
        """Cross-user isolation: User A cannot see User B's notifications, and vice versa."""
        res_a = self.client.get("/notifications", headers=self.headers_a)
        res_b = self.client.get("/notifications", headers=self.headers_b)

        ids_a = {n["notification_id"] for n in res_a.json()["notifications"]}
        ids_b = {n["notification_id"] for n in res_b.json()["notifications"]}

        # Neither user should see the other's notifications
        self.assertNotIn(self.notif_b1.notification_id, ids_a)
        self.assertIn(self.notif_b1.notification_id, ids_b)
        for n_id in ids_a:
            self.assertNotIn(n_id, ids_b)

    def test_03_empty_inbox_returns_cleanly(self):
        """User with zero notifications receives a clean empty response."""
        res = self.client.get("/notifications", headers=self.headers_c)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["notifications"], [])
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["unread_count"], 0)

    def test_04_filter_by_status_works(self):
        """Filtering by status='UNREAD' and status='READ' works accurately."""
        # UNREAD filter
        res_unread = self.client.get("/notifications?status=UNREAD", headers=self.headers_a)
        self.assertEqual(res_unread.status_code, 200)
        data_unread = res_unread.json()
        self.assertEqual(data_unread["total"], 3)
        for n in data_unread["notifications"]:
            self.assertEqual(n["status"], "UNREAD")

        # READ filter
        res_read = self.client.get("/notifications?status=READ", headers=self.headers_a)
        self.assertEqual(res_read.status_code, 200)
        data_read = res_read.json()
        self.assertEqual(data_read["total"], 2)
        for n in data_read["notifications"]:
            self.assertEqual(n["status"], "READ")

    def test_05_filter_by_notification_type_works(self):
        """Filtering by notification_type returns only matching records."""
        res = self.client.get("/notifications?notification_type=COMMUNITY_INVITATION", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["notifications"][0]["notification_type"], "COMMUNITY_INVITATION")
        self.assertEqual(data["notifications"][0]["title"], "Badminton Club Invite")

    def test_06_filter_by_is_read_works(self):
        """Filtering by is_read=true and is_read=false works accurately."""
        res_false = self.client.get("/notifications?is_read=false", headers=self.headers_a)
        self.assertEqual(res_false.status_code, 200)
        self.assertEqual(res_false.json()["total"], 3)
        for n in res_false.json()["notifications"]:
            self.assertFalse(n["is_read"])

        res_true = self.client.get("/notifications?is_read=true", headers=self.headers_a)
        self.assertEqual(res_true.status_code, 200)
        self.assertEqual(res_true.json()["total"], 2)
        for n in res_true.json()["notifications"]:
            self.assertTrue(n["is_read"])

    def test_07_pagination_works(self):
        """Limit and offset paginate results accurately."""
        res_p1 = self.client.get("/notifications?limit=2&offset=0", headers=self.headers_a)
        self.assertEqual(res_p1.status_code, 200)
        data_p1 = res_p1.json()
        self.assertEqual(len(data_p1["notifications"]), 2)
        self.assertEqual(data_p1["limit"], 2)
        self.assertEqual(data_p1["offset"], 0)
        self.assertEqual(data_p1["total"], 5)

        res_p2 = self.client.get("/notifications?limit=2&offset=2", headers=self.headers_a)
        self.assertEqual(res_p2.status_code, 200)
        data_p2 = res_p2.json()
        self.assertEqual(len(data_p2["notifications"]), 2)
        self.assertEqual(data_p2["offset"], 2)

        # Page 1 and Page 2 IDs do not overlap
        p1_ids = {n["notification_id"] for n in data_p1["notifications"]}
        p2_ids = {n["notification_id"] for n in data_p2["notifications"]}
        self.assertEqual(len(p1_ids.intersection(p2_ids)), 0)

    def test_08_total_is_correct(self):
        """total field accurately reflects the count of filtered items."""
        res = self.client.get("/notifications?status=UNREAD", headers=self.headers_a)
        data = res.json()
        self.assertEqual(data["total"], 3)

        res_all = self.client.get("/notifications", headers=self.headers_a)
        self.assertEqual(res_all.json()["total"], 5)

    def test_09_unread_count_scoped_to_current_user(self):
        """unread_count represents current user's unread notifications even when query is filtered."""
        # Querying with status=READ should still report unread_count=3 for User A
        res = self.client.get("/notifications?status=READ", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 2)  # 2 read
        self.assertEqual(data["unread_count"], 3)  # still 3 unread for User A

        # User B unread_count is 1
        res_b = self.client.get("/notifications", headers=self.headers_b)
        self.assertEqual(res_b.json()["unread_count"], 1)

    def test_10_results_deterministic_newest_first(self):
        """Notifications are sorted newest first (created_at desc, notification_id desc)."""
        res = self.client.get("/notifications", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        notifs = res.json()["notifications"]

        for i in range(len(notifs) - 1):
            curr_time = notifs[i]["created_at"]
            next_time = notifs[i + 1]["created_at"]
            self.assertGreaterEqual(curr_time, next_time)
            if curr_time == next_time:
                self.assertGreater(notifs[i]["notification_id"], notifs[i + 1]["notification_id"])

    def test_11_invalid_filter_values_rejected(self):
        """Invalid status or notification_type values are rejected with 400 Bad Request."""
        res_status = self.client.get("/notifications?status=INVALID_STATUS_VALUE", headers=self.headers_a)
        self.assertEqual(res_status.status_code, 400)
        self.assertIn("Invalid status filter", res_status.json()["detail"])

        res_type = self.client.get("/notifications?notification_type=INVALID_TYPE_VALUE", headers=self.headers_a)
        self.assertEqual(res_type.status_code, 400)
        self.assertIn("Invalid notification_type filter", res_type.json()["detail"])

    def test_12_unauthenticated_access_rejected(self):
        """Unauthenticated request without Authorization header is rejected with 401."""
        res = self.client.get("/notifications")
        self.assertEqual(res.status_code, 401)


# ============================================================================
# Step 10.4: Read / Unread State Management Tests (PATCH /notifications/{id}/read)
# ============================================================================

class TestNotificationReadStateManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # 1. User 1
        email_1 = f"read_user_1_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email_1, "password": cls.pwd, "confirm_password": cls.pwd})
        res_1 = cls.client.post("/auth/login", json={"email": email_1, "password": cls.pwd}).json()
        cls.token_1 = res_1["access_token"]
        cls.headers_1 = {"Authorization": f"Bearer {cls.token_1}"}
        cls.user_1 = cls.db.query(models.User).filter(models.User.email == email_1).first()

        # 2. User 2 (Foreign user)
        email_2 = f"read_user_2_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email_2, "password": cls.pwd, "confirm_password": cls.pwd})
        res_2 = cls.client.post("/auth/login", json={"email": email_2, "password": cls.pwd}).json()
        cls.token_2 = res_2["access_token"]
        cls.headers_2 = {"Authorization": f"Bearer {cls.token_2}"}
        cls.user_2 = cls.db.query(models.User).filter(models.User.email == email_2).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_owner_marks_unread_notification_as_read(self):
        """Notification owner successfully marks unread notification as READ."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Mark Read Test",
            "message": "Testing mark read API.",
        })
        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["notification_id"], notif.notification_id)
        self.assertEqual(data["status"], "READ")
        self.assertTrue(data["is_read"])

    def test_02_is_read_becomes_true(self):
        """is_read field becomes True in response and in database."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "RE_ENGAGEMENT",
            "title": "is_read True Test",
            "message": "Verify boolean flag.",
        })
        self.assertFalse(notif.is_read)

        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["is_read"])

        # Fresh DB query
        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertTrue(persisted.is_read)

    def test_03_status_becomes_read(self):
        """status field transitions to 'READ' in database."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "FEEDBACK_REQUEST",
            "title": "Status Transition Test",
            "message": "Status must become READ.",
        })
        self.assertEqual(notif.status, "UNREAD")

        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "READ")

        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertEqual(persisted.status, "READ")

    def test_04_read_at_is_populated(self):
        """read_at timestamp is populated with current time upon marking read."""
        before = datetime.now()
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Timestamp Population Test",
            "message": "read_at must be populated.",
        })
        self.assertIsNone(notif.read_at)

        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        read_at_str = res.json()["read_at"]
        self.assertIsNotNone(read_at_str)

        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertIsNotNone(persisted.read_at)
        self.assertGreaterEqual(persisted.read_at.replace(tzinfo=None), before - timedelta(seconds=2))

    def test_05_already_read_notification_remains_safely_read(self):
        """Calling read on an already-read notification is idempotent and returns 200."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Idempotency Test",
            "message": "First read.",
        })
        res1 = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res1.status_code, 200)

        # Call again
        res2 = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["status"], "READ")
        self.assertTrue(res2.json()["is_read"])

    def test_06_read_at_does_not_get_unnecessarily_reset(self):
        """Subsequent read calls on an already-read notification preserve original read_at timestamp."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Preserve Timestamp Test",
            "message": "Check timestamp preservation.",
        })
        res1 = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        original_read_at = res1.json()["read_at"]

        time_mod.sleep(0.05)

        res2 = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        second_read_at = res2.json()["read_at"]

        self.assertEqual(original_read_at, second_read_at, "read_at timestamp must not be overwritten on repeated calls")

    def test_07_user_cannot_modify_another_users_notification(self):
        """Foreign user attempting to mark another user's notification as read receives 403 Forbidden."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,  # Belongs to User 1
            "notification_type": "SYSTEM_ALERT",
            "title": "User 1 Private Alert",
            "message": "User 2 cannot read this.",
        })
        # User 2 tries to read User 1's notification
        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_2)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

        # Verify status remains UNREAD
        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertEqual(persisted.status, "UNREAD")
        self.assertFalse(persisted.is_read)

    def test_08_unknown_notification_returns_404(self):
        """Attempting to mark non-existent notification returns 404 Not Found."""
        res = self.client.patch("/notifications/99999999/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 404)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_09_unauthenticated_request_returns_401(self):
        """Attempting to mark notification as read without token returns 401 Unauthorized."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Auth Gate Test",
            "message": "Requires token.",
        })
        res = self.client.patch(f"/notifications/{notif.notification_id}/read")
        self.assertEqual(res.status_code, 401)

    def test_10_dismissed_notification_cannot_be_reopened(self):
        """Notification in terminal DISMISSED state cannot be altered or marked as read."""
        notif = models.Notification(
            recipient_user_id=self.user_1.user_id,
            notification_type="COMMUNITY_INVITATION",
            title="Dismissed Notification",
            message="Already dismissed.",
            status="DISMISSED",
            is_read=True,
            read_at=datetime.now(),
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 400)
        self.assertIn("terminal state", res.json()["detail"])

    def test_11_accepted_notification_cannot_be_reopened(self):
        """Notification in terminal ACCEPTED state cannot be altered or marked as read."""
        notif = models.Notification(
            recipient_user_id=self.user_1.user_id,
            notification_type="COMMUNITY_INVITATION",
            title="Accepted Notification",
            message="Already accepted.",
            status="ACCEPTED",
            is_read=True,
            read_at=datetime.now(),
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        res = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res.status_code, 400)
        self.assertIn("terminal state", res.json()["detail"])

    def test_12_inbox_unread_count_decreases_correctly(self):
        """Marking an unread notification as read correctly decrements unread_count in inbox query."""
        notif = create_notification(self.db, {
            "recipient_user_id": self.user_1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Unread Count Test",
            "message": "Will decrement unread count.",
        })
        # Check initial unread_count
        res_before = self.client.get("/notifications", headers=self.headers_1)
        count_before = res_before.json()["unread_count"]
        self.assertGreater(count_before, 0)

        # Mark as read
        res_read = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res_read.status_code, 200)

        # Check updated unread_count
        res_after = self.client.get("/notifications", headers=self.headers_1)
        count_after = res_after.json()["unread_count"]
        self.assertEqual(count_after, count_before - 1, "Inbox unread_count must decrement by exactly 1")


# ============================================================================
# Step 10.5: Action-Aware Notification Payloads Tests
# ============================================================================

class TestActionAwareNotificationPayloads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # User
        email = f"payload_user_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email, "password": cls.pwd, "confirm_password": cls.pwd})
        res = cls.client.post("/auth/login", json={"email": email, "password": cls.pwd}).json()
        cls.token = res["access_token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}
        cls.user = cls.db.query(models.User).filter(models.User.email == email).first()

        # Community
        cls.community = models.Community(
            name=f"Payload Community {cls.ts}",
            description="Testing payload actions",
            created_by=cls.user.user_id,
        )
        cls.community2 = models.Community(
            name=f"Payload Community 2 {cls.ts}",
            description="Testing payload actions 2",
            created_by=cls.user.user_id,
        )
        cls.db.add_all([cls.community, cls.community2])
        cls.db.commit()
        cls.db.refresh(cls.community)
        cls.db.refresh(cls.community2)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_community_invitation_payload_contract(self):
        """CommunityInvitationPayload model contract specifies actionable=True and target_action='JOIN_COMMUNITY'."""
        payload = schemas.CommunityInvitationPayload(
            community_id=self.community.community_id,
            community_name=self.community.name,
            inviter_user_id=self.user.user_id,
            affinity_reasons=["Nearby locality", "Shared interest in Badminton"],
        )
        self.assertTrue(payload.actionable)
        self.assertEqual(payload.target_action, "JOIN_COMMUNITY")
        self.assertIn(str(self.community.community_id), payload.target_endpoint)
        self.assertEqual(len(payload.affinity_reasons), 2)

    def test_02_activity_maintenance_payload_contract(self):
        """ActivityMaintenancePayload model contract specifies actionable=True and target_action='CREATE_EVENT'."""
        action_plan = {
            "action": "CREATE_EVENT",
            "parameters": {
                "activity_id": 1,
                "title": "Weekly Practice Session",
                "max_capacity": 10,
            },
        }
        payload = schemas.ActivityMaintenancePayload(
            community_id=self.community.community_id,
            community_name=self.community.name,
            cadence="WEEKLY",
            suggested_activity_id=1,
            suggested_activity_title="Badminton",
            action_plan=action_plan,
        )
        self.assertTrue(payload.actionable)
        self.assertEqual(payload.target_action, "CREATE_EVENT")
        self.assertEqual(payload.cadence, "WEEKLY")
        self.assertEqual(payload.action_plan["action"], "CREATE_EVENT")

    def test_03_community_reactivation_payload_contract(self):
        """CommunityReactivationPayload model contract specifies actionable=True and target_action='CREATE_EVENT'."""
        payload = schemas.CommunityReactivationPayload(
            community_id=self.community.community_id,
            community_name=self.community.name,
            reactivation_date="2026-10-30",
            suggested_activity_id=1,
            suggested_activity_title="Badminton Tournament",
            action_plan={"action": "CREATE_EVENT"},
        )
        self.assertTrue(payload.actionable)
        self.assertEqual(payload.target_action, "CREATE_EVENT")
        self.assertEqual(payload.reactivation_date, "2026-10-30")

    def test_04_feedback_request_payload_contract(self):
        """FeedbackRequestPayload model contract specifies actionable=False and target_endpoint='/feedback'."""
        payload = schemas.FeedbackRequestPayload(
            event_id=42,
            event_title="Weekend Tournament",
            community_id=self.community.community_id,
        )
        self.assertFalse(payload.actionable)
        self.assertEqual(payload.target_endpoint, "/feedback")
        self.assertEqual(payload.event_id, 42)

    def test_05_re_engagement_payload_contract(self):
        """ReEngagementPayload model contract specifies actionable=False with target community endpoint."""
        payload = schemas.ReEngagementPayload(
            community_id=self.community.community_id,
            community_name=self.community.name,
            target_inactive_days=14,
        )
        self.assertFalse(payload.actionable)
        self.assertEqual(payload.community_id, self.community.community_id)
        self.assertEqual(payload.target_inactive_days, 14)

    def test_06_system_alert_payload_contract(self):
        """SystemAlertPayload model contract specifies actionable=False."""
        payload = schemas.SystemAlertPayload(
            alert_code="MAINTENANCE_SCHEDULED",
            context="System maintenance at midnight",
        )
        self.assertFalse(payload.actionable)
        self.assertEqual(payload.alert_code, "MAINTENANCE_SCHEDULED")

    def test_07_normalization_tags_actionable_correctly(self):
        """Normalizer tags actionable=True and populates target action/endpoint for actionable notification types."""
        for act_type in schemas.ACTIONABLE_NOTIFICATION_TYPES:
            norm = schemas.normalize_action_aware_payload(act_type, {"community_id": 5})
            self.assertTrue(norm["actionable"], f"Expected {act_type} to be actionable=True")
            self.assertIn("target_action", norm)
            self.assertIn("target_endpoint", norm)

    def test_08_normalization_tags_informational_correctly(self):
        """Normalizer tags actionable=False for informational notification types."""
        for info_type in schemas.INFORMATIONAL_NOTIFICATION_TYPES:
            norm = schemas.normalize_action_aware_payload(info_type, {"community_id": 5})
            self.assertFalse(norm["actionable"], f"Expected {info_type} to be actionable=False")

    def test_09_service_persists_action_aware_payload(self):
        """Service persists validated action-aware payload structure in database."""
        norm_payload = schemas.normalize_action_aware_payload(
            schemas.NotificationType.COMMUNITY_INVITATION,
            {"community_id": self.community.community_id, "source": "GROW_MEMBERSHIP"},
        )
        req = schemas.NotificationCreate(
            recipient_user_id=self.user.user_id,
            notification_type=schemas.NotificationType.COMMUNITY_INVITATION,
            title="Action-Aware Invite Test",
            message="Join the community session.",
            payload=norm_payload,
            related_community_id=self.community.community_id,
        )
        notif = create_notification(self.db, req)

        self.assertIsNotNone(notif.payload)
        self.assertTrue(notif.payload["actionable"])
        self.assertEqual(notif.payload["target_action"], "JOIN_COMMUNITY")
        self.assertEqual(notif.payload["target_endpoint"], f"/communities/{self.community.community_id}/join")
        self.assertEqual(notif.payload["source"], "GROW_MEMBERSHIP")

    def test_10_inbox_api_serves_action_aware_payload(self):
        """GET /notifications delivers fully structured action-aware payload to client."""
        norm_payload = schemas.normalize_action_aware_payload(
            "ACTIVITY_MAINTENANCE",
            {
                "community_id": self.community.community_id,
                "cadence": "WEEKLY",
                "action_plan": {"action": "CREATE_EVENT", "date": "2026-10-25"},
            },
        )
        notif = create_notification(self.db, {
            "recipient_user_id": self.user.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Action-Aware Maintenance Test",
            "message": "Maintenance plan ready.",
            "payload": norm_payload,
            "related_community_id": self.community.community_id,
        })

        res = self.client.get("/notifications", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        matching = [n for n in data["notifications"] if n["notification_id"] == notif.notification_id]
        self.assertEqual(len(matching), 1)

        payload = matching[0]["payload"]
        self.assertTrue(payload["actionable"])
        self.assertEqual(payload["target_action"], "CREATE_EVENT")
        self.assertEqual(payload["cadence"], "WEEKLY")
        self.assertEqual(payload["action_plan"]["action"], "CREATE_EVENT")

    def test_11_payload_creation_causes_zero_side_effects(self):
        """Constructing an action-aware payload containing CREATE_EVENT plan strictly does NOT create events."""
        events_before = self.db.query(models.Event).count()

        notif = create_notification(self.db, {
            "recipient_user_id": self.user.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Zero Side-Effect Test",
            "message": "Carries CREATE_EVENT plan without executing it.",
            "payload": {
                "community_id": self.community.community_id,
                "action_plan": {"action": "CREATE_EVENT", "title": "Phantom Event"},
            },
            "related_community_id": self.community.community_id,
        })
        self.assertIsNotNone(notif.notification_id)

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after, "Creating notification payload must cause strictly zero entity mutations")

    def test_12_custom_context_preserved_alongside_action_metadata(self):
        """Arbitrary caller metadata (e.g. affinity_score, reason_tokens) is preserved intact."""
        raw_custom = schemas.normalize_action_aware_payload(
            "COMMUNITY_INVITATION",
            {
                "community_id": self.community2.community_id,
                "affinity_score": 97,
                "reason_tokens": ["nearby", "same_skill"],
                "custom_flag": True,
            },
        )
        notif = create_notification(self.db, {
            "recipient_user_id": self.user.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Custom Metadata Preservation",
            "message": "Testing metadata preservation.",
            "payload": raw_custom,
            "related_community_id": self.community2.community_id,
        })
        self.assertEqual(notif.payload["affinity_score"], 97)
        self.assertEqual(notif.payload["reason_tokens"], ["nearby", "same_skill"])
        self.assertTrue(notif.payload["custom_flag"])
        self.assertTrue(notif.payload["actionable"])



# ============================================================================
# Step 10.6: Accept / Dismiss Semantics Tests
# ============================================================================

class TestNotificationAcceptDismissSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # User 1 (Owner)
        email1 = f"accept_owner_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email1, "password": cls.pwd, "confirm_password": cls.pwd})
        res1 = cls.client.post("/auth/login", json={"email": email1, "password": cls.pwd}).json()
        cls.token1 = res1["access_token"]
        cls.headers_1 = {"Authorization": f"Bearer {cls.token1}"}
        cls.user1 = cls.db.query(models.User).filter(models.User.email == email1).first()

        # User 2 (Foreign user)
        email2 = f"accept_foreign_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email2, "password": cls.pwd, "confirm_password": cls.pwd})
        res2 = cls.client.post("/auth/login", json={"email": email2, "password": cls.pwd}).json()
        cls.token2 = res2["access_token"]
        cls.headers_2 = {"Authorization": f"Bearer {cls.token2}"}
        cls.user2 = cls.db.query(models.User).filter(models.User.email == email2).first()

        # Community
        cls.community = models.Community(
            name=f"Accept Community {cls.ts}",
            description="Testing accept/dismiss semantics",
            created_by=cls.user1.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _create_test_notif(self, notif_type: str, actionable_payload: bool = True) -> models.Notification:
        if actionable_payload and notif_type in schemas.ACTIONABLE_NOTIFICATION_TYPES:
            payload = schemas.normalize_action_aware_payload(
                notif_type,
                {"community_id": self.community.community_id, "source": "TEST"},
            )
        else:
            payload = {"info": "test"}

        return create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": notif_type,
            "title": f"Test {notif_type}",
            "message": f"Message for {notif_type}",
            "payload": payload,
            "related_community_id": self.community.community_id,
        })

    def test_01_owner_accepts_actionable_notification(self):
        """Owner accepts actionable notification resulting in 200 and status=ACCEPTED."""
        notif = self._create_test_notif("COMMUNITY_INVITATION")
        res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ACCEPTED")
        self.assertEqual(data["notification_id"], notif.notification_id)

    def test_02_accept_sets_is_read_true_and_populates_read_at(self):
        """Accepting an unread notification sets is_read=True and populates read_at timestamp."""
        notif = self._create_test_notif("COMMUNITY_INVITATION")
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)

        res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_read"])
        self.assertIsNotNone(data["read_at"])

    def test_03_accept_activity_maintenance_actionable_notification(self):
        """Owner accepts ACTIVITY_MAINTENANCE notification transitioning to ACCEPTED."""
        notif = self._create_test_notif("ACTIVITY_MAINTENANCE")
        res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ACCEPTED")

    def test_04_accept_community_reactivation_actionable_notification(self):
        """Owner accepts COMMUNITY_REACTIVATION notification transitioning to ACCEPTED."""
        notif = self._create_test_notif("COMMUNITY_REACTIVATION")
        res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ACCEPTED")

    def test_05_informational_notifications_cannot_be_accepted(self):
        """Informational notifications (FEEDBACK_REQUEST, RE_ENGAGEMENT, SYSTEM_ALERT) reject acceptance with 400."""
        for info_type in schemas.INFORMATIONAL_NOTIFICATION_TYPES:
            notif = self._create_test_notif(info_type)
            res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
            self.assertEqual(res.status_code, 400, f"Expected 400 when accepting informational type {info_type}")
            self.assertIn("cannot be accepted", res.json()["detail"])

    def test_06_foreign_user_cannot_accept(self):
        """Foreign user attempting to accept another user's notification is blocked with 403."""
        notif = self._create_test_notif("COMMUNITY_INVITATION")
        res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_2)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

    def test_07_unknown_notification_accept_returns_404(self):
        """Accepting a non-existent notification ID returns 404."""
        res = self.client.patch("/notifications/99999999/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 404)

    def test_08_already_accepted_notification_cannot_be_accepted_again(self):
        """Calling accept on an already ACCEPTED notification returns 400 (terminal state error)."""
        notif = self._create_test_notif("COMMUNITY_INVITATION")
        res1 = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res1.status_code, 200)

        res2 = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("terminal state", res2.json()["detail"])

    def test_09_owner_dismisses_unread_notification(self):
        """Owner dismisses an unread notification resulting in 200 and status=DISMISSED."""
        notif = self._create_test_notif("COMMUNITY_INVITATION")
        res = self.client.patch(f"/notifications/{notif.notification_id}/dismiss", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "DISMISSED")
        self.assertEqual(data["notification_id"], notif.notification_id)

    def test_10_owner_dismisses_read_notification(self):
        """Owner dismisses a READ notification transitioning status to DISMISSED."""
        notif = self._create_test_notif("FEEDBACK_REQUEST")
        res_read = self.client.patch(f"/notifications/{notif.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res_read.status_code, 200)
        self.assertEqual(res_read.json()["status"], "READ")

        res_dismiss = self.client.patch(f"/notifications/{notif.notification_id}/dismiss", headers=self.headers_1)
        self.assertEqual(res_dismiss.status_code, 200)
        self.assertEqual(res_dismiss.json()["status"], "DISMISSED")

    def test_11_dismiss_sets_is_read_true_and_populates_read_at(self):
        """Dismissing an unread notification sets is_read=True and populates read_at."""
        notif = self._create_test_notif("SYSTEM_ALERT")
        res = self.client.patch(f"/notifications/{notif.notification_id}/dismiss", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_read"])
        self.assertIsNotNone(data["read_at"])

    def test_12_foreign_user_cannot_dismiss(self):
        """Foreign user attempting to dismiss another user's notification is blocked with 403."""
        notif = self._create_test_notif("COMMUNITY_INVITATION")
        res = self.client.patch(f"/notifications/{notif.notification_id}/dismiss", headers=self.headers_2)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

    def test_13_unknown_notification_dismiss_returns_404(self):
        """Dismissing a non-existent notification ID returns 404."""
        res = self.client.patch("/notifications/99999999/dismiss", headers=self.headers_1)
        self.assertEqual(res.status_code, 404)

    def test_14_terminal_notification_cannot_be_dismissed_again_or_reopened(self):
        """Terminal states (DISMISSED/ACCEPTED) cannot be dismissed again, accepted, or marked read."""
        # Case A: Dismissed notification
        notif1 = self._create_test_notif("COMMUNITY_INVITATION")
        res_d1 = self.client.patch(f"/notifications/{notif1.notification_id}/dismiss", headers=self.headers_1)
        self.assertEqual(res_d1.status_code, 200)

        # Cannot dismiss again
        res_d2 = self.client.patch(f"/notifications/{notif1.notification_id}/dismiss", headers=self.headers_1)
        self.assertEqual(res_d2.status_code, 400)

        # Cannot accept dismissed notification
        res_acc = self.client.patch(f"/notifications/{notif1.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res_acc.status_code, 400)

        # Cannot mark read dismissed notification
        res_rd = self.client.patch(f"/notifications/{notif1.notification_id}/read", headers=self.headers_1)
        self.assertEqual(res_rd.status_code, 400)

        # Case B: Accepted notification
        notif2 = self._create_test_notif("COMMUNITY_INVITATION")
        res_a1 = self.client.patch(f"/notifications/{notif2.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res_a1.status_code, 200)

        # Cannot dismiss accepted notification
        res_dis_acc = self.client.patch(f"/notifications/{notif2.notification_id}/dismiss", headers=self.headers_1)
        self.assertEqual(res_dis_acc.status_code, 400)

    def test_15_accept_actionable_notification_causes_zero_side_effects(self):
        """Accepting an actionable notification with CREATE_EVENT plan causes strictly zero domain mutations."""
        events_before = self.db.query(models.Event).count()
        participants_before = self.db.query(models.EventParticipant).count()
        members_before = self.db.query(models.CommunityMember).count()

        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Reactivation Actionable Test",
            "message": "Carrying event plan to accept.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": {"action": "CREATE_EVENT", "title": "Phantom Session"},
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.patch(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ACCEPTED")

        events_after = self.db.query(models.Event).count()
        participants_after = self.db.query(models.EventParticipant).count()
        members_after = self.db.query(models.CommunityMember).count()

        self.assertEqual(events_before, events_after, "Accepting notification must not create events")
        self.assertEqual(participants_before, participants_after, "Accepting notification must not create event participants")
        self.assertEqual(members_before, members_after, "Accepting notification must not change community members")


# ============================================================================
# Step 10.7: Step 9 Action Integration Tests
# ============================================================================

class TestNotificationStep9ActionIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password@123"

        # User 1: Community Organizer / Host
        email1 = f"int_organizer_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email1, "password": cls.pwd, "confirm_password": cls.pwd})
        res1 = cls.client.post("/auth/login", json={"email": email1, "password": cls.pwd}).json()
        cls.token1 = res1["access_token"]
        cls.headers_1 = {"Authorization": f"Bearer {cls.token1}"}
        cls.user1 = cls.db.query(models.User).filter(models.User.email == email1).first()

        # User 2: Invitee / Member
        email2 = f"int_invitee_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email2, "password": cls.pwd, "confirm_password": cls.pwd})
        res2 = cls.client.post("/auth/login", json={"email": email2, "password": cls.pwd}).json()
        cls.token2 = res2["access_token"]
        cls.headers_2 = {"Authorization": f"Bearer {cls.token2}"}
        cls.user2 = cls.db.query(models.User).filter(models.User.email == email2).first()

        # User 3: Outsider (non-member)
        email3 = f"int_outsider_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email3, "password": cls.pwd, "confirm_password": cls.pwd})
        res3 = cls.client.post("/auth/login", json={"email": email3, "password": cls.pwd}).json()
        cls.token3 = res3["access_token"]
        cls.headers_3 = {"Authorization": f"Bearer {cls.token3}"}
        cls.user3 = cls.db.query(models.User).filter(models.User.email == email3).first()

        # Community (User 1 is creator & organizer)
        cls.community = models.Community(
            name=f"Bridge Community {cls.ts}",
            description="Testing Step 9 & 10 integration bridge",
            created_by=cls.user1.user_id,
        )
        cls.db.add(cls.community)
        cls.db.commit()
        cls.db.refresh(cls.community)

        # Enroll User 1 as organizer member
        member1 = models.CommunityMember(
            community_id=cls.community.community_id,
            user_id=cls.user1.user_id,
            role="ORGANIZER",
        )
        cls.db.add(member1)
        cls.db.commit()

        # Activity template
        activity = cls.db.query(models.Activity).first()
        if not activity:
            activity = models.Activity(
                title=f"Bridge Activity {cls.ts}",
                interest_id=1,
            )
            cls.db.add(activity)
            cls.db.commit()
            cls.db.refresh(activity)
        cls.activity = activity

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _make_action_plan(self, days_ahead: int = 7, capacity: int = 10, title_suffix: str = ""):
        future_date = (date.today() + timedelta(days=days_ahead)).isoformat()
        return {
            "action": "CREATE_EVENT",
            "parameters": {
                "activity_id": self.activity.activity_id,
                "event_date": future_date,
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": f"Bridge Match {self.ts} {title_suffix}".strip(),
                "max_capacity": capacity,
            },
        }

    def test_01_actionable_notification_accepted_invokes_correct_step9_action(self):
        """Actionable notification accepted via POST /notifications/{id}/accept executes Step 9 action."""
        plan = self._make_action_plan(days_ahead=8, title_suffix="Test01")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Maintenance Plan Test 01",
            "message": "Ready to execute activity maintenance.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "CREATE_EVENT")
        self.assertEqual(data["status"], "COMPLETED")
        self.assertTrue(data["success"])

        # Check notification status updated to ACCEPTED
        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertEqual(persisted.status, "ACCEPTED")
        self.assertTrue(persisted.is_read)

    def test_02_create_event_created_only_after_acceptance(self):
        """CREATE_EVENT notification creates actual database Event only upon acceptance."""
        events_before = self.db.query(models.Event).count()
        plan = self._make_action_plan(days_ahead=9, title_suffix="Test02 Only After")

        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Reactivation Test 02",
            "message": "Event prepared but not yet created.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        # Event count MUST be unchanged before acceptance
        events_middle = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_middle, "Zero events must be created before acceptance")

        # Accept notification
        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_after, events_before + 1, "Exactly one event must be created after acceptance")

    def test_03_community_invitation_membership_action_occurs(self):
        """Accepting COMMUNITY_INVITATION notification enrolls invitee as CommunityMember."""
        # Ensure user 2 is not a member initially
        existing = self.db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == self.community.community_id,
            models.CommunityMember.user_id == self.user2.user_id,
        ).first()
        self.assertIsNone(existing)

        notif = create_notification(self.db, {
            "recipient_user_id": self.user2.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Join our Circle",
            "message": "You are invited to join.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "JOIN_COMMUNITY",
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_2)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "JOIN_COMMUNITY")
        self.assertTrue(data["success"])

        # Verify user 2 is now an enrolled member
        self.db.expire_all()
        new_membership = self.db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == self.community.community_id,
            models.CommunityMember.user_id == self.user2.user_id,
        ).first()
        self.assertIsNotNone(new_membership)
        self.assertEqual(new_membership.role, "MEMBER")

    def test_04_informational_notification_rejects_execution(self):
        """Informational notifications reject execution and trigger zero domain side-effects."""
        for info_type in schemas.INFORMATIONAL_NOTIFICATION_TYPES:
            notif = create_notification(self.db, {
                "recipient_user_id": self.user1.user_id,
                "notification_type": info_type,
                "title": f"Informational {info_type}",
                "message": "No actions can be run.",
            })

            res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
            self.assertEqual(res.status_code, 400)
            self.assertIn("informational and cannot execute", res.json()["detail"])

    def test_05_invalid_action_payload_rejected_by_step9_validation(self):
        """Notification containing invalid parameters is rejected by Step 9 validation."""
        bad_plan = self._make_action_plan(days_ahead=5, capacity=-10, title_suffix="Bad Params")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Bad Params Test",
            "message": "Carries negative capacity.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": bad_plan,
            },
            "related_community_id": self.community.community_id,
        })

        events_before = self.db.query(models.Event).count()
        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Validation failed", res.json()["detail"])

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after, "Invalid payload must not create event")

        # Notification must not be marked ACCEPTED
        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertEqual(persisted.status, "UNREAD")

    def test_06_unauthorized_community_action_rejected(self):
        """Notification for user who is not a community member is rejected by Step 9 authorization."""
        plan = self._make_action_plan(days_ahead=10, title_suffix="Test06 Outsider")
        # User 3 is NOT a member of self.community
        notif = create_notification(self.db, {
            "recipient_user_id": self.user3.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Outsider Action Test",
            "message": "User 3 has no permission here.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_3)
        self.assertEqual(res.status_code, 403)

        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertEqual(persisted.status, "UNREAD")

    def test_07_foreign_notification_owner_rejected(self):
        """Non-owner attempting to execute another user's notification is blocked with 403."""
        plan = self._make_action_plan(days_ahead=11, title_suffix="Test07 Foreign")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Private Notification",
            "message": "Only user 1 may execute this.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_2)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

    def test_08_missing_notification_returns_404(self):
        """Executing non-existent notification ID returns 404."""
        res = self.client.post("/notifications/99999999/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 404)

    def test_09_already_accepted_notification_cannot_execute_again(self):
        """Notification already in ACCEPTED state cannot execute again."""
        plan = self._make_action_plan(days_ahead=12, title_suffix="Test09 Already Accepted")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Once Only Test",
            "message": "Can only be run once.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        res1 = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res1.status_code, 200)

        # Second execution attempt is blocked
        res2 = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("terminal state", res2.json()["detail"])

    def test_10_failed_domain_action_does_not_falsely_report_success(self):
        """If activity template is not found in database, execution fails and status is not ACCEPTED."""
        plan = {
            "action": "CREATE_EVENT",
            "parameters": {
                "activity_id": 99999999,  # Non-existent activity
                "event_date": (date.today() + timedelta(days=14)).isoformat(),
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": "Missing Activity Session",
                "max_capacity": 8,
            },
        }
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Missing Template Test",
            "message": "Template does not exist.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 400)

        self.db.expire_all()
        persisted = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertEqual(persisted.status, "UNREAD")

    def test_11_notification_acceptance_does_not_bypass_step9_authorization(self):
        """Direct call to execute_notification_action enforces Step 9 authorization."""
        plan = self._make_action_plan(days_ahead=15, title_suffix="Test11 Auth Check")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user3.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Direct Auth Check",
            "message": "Checking service-level auth.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        result = execute_notification_action(self.db, notif.notification_id, self.user3.user_id)
        self.assertFalse(result.success)
        self.assertEqual(result.status, "REJECTED")
        self.assertEqual(result.details.get("auth_status"), "NOT_A_MEMBER")

    def test_12_no_arbitrary_client_supplied_action_overrides_stored_action(self):
        """Malicious client payload passed in request body is ignored; server stored action is used."""
        plan = self._make_action_plan(days_ahead=16, title_suffix="Test12 Tamper Proof")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Tamper Resistance Test",
            "message": "Client body must be ignored.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        malicious_body = {
            "action": "DROP_DATABASE",
            "parameters": {"force": True},
        }
        res = self.client.post(
            f"/notifications/{notif.notification_id}/accept",
            headers=self.headers_1,
            json=malicious_body,
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "CREATE_EVENT")
        self.assertTrue(data["success"])

    def test_13_successful_execution_returns_structured_result(self):
        """Response conforms to ActionExecutionResult schema with full execution metadata."""
        plan = self._make_action_plan(days_ahead=17, title_suffix="Test13 Result Structure")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Structured Result Test",
            "message": "Checking response fields.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        res = self.client.post(f"/notifications/{notif.notification_id}/accept", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("community_id", data)
        self.assertIn("action", data)
        self.assertIn("status", data)
        self.assertIn("success", data)
        self.assertIn("message", data)
        self.assertIn("details", data)
        self.assertIn("executed_at", data)
        self.assertEqual(data["action"], "CREATE_EVENT")

    def test_14_patch_accept_with_execute_true_works(self):
        """PATCH /notifications/{id}/accept?execute=true executes Step 9 action and returns NotificationResponse."""
        plan = self._make_action_plan(days_ahead=18, title_suffix="Test14 Patch Execute")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Patch Execute Test",
            "message": "Testing PATCH execute parameter.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        events_before = self.db.query(models.Event).count()
        res = self.client.patch(f"/notifications/{notif.notification_id}/accept?execute=true", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ACCEPTED")
        self.assertTrue(data["is_read"])

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_after, events_before + 1, "PATCH ?execute=true must create event")

    def test_15_idempotency_safety_repeated_execution_blocks_duplicate_domain_objects(self):
        """Repeated execution attempts are blocked, creating zero duplicate events or memberships."""
        # 1. Event creation idempotency check
        plan = self._make_action_plan(days_ahead=19, title_suffix="Test15 Idempotency")
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Duplicate Guard Test",
            "message": "Testing duplicate prevention.",
            "payload": {
                "community_id": self.community.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community.community_id,
        })

        # Run 1: Succeeded
        res1 = self.client.post(f"/notifications/{notif.notification_id}/execute", headers=self.headers_1)
        self.assertEqual(res1.status_code, 200)
        events_after_first = self.db.query(models.Event).count()

        # Run 2: Blocked by terminal state guard
        res2 = self.client.post(f"/notifications/{notif.notification_id}/execute", headers=self.headers_1)
        self.assertEqual(res2.status_code, 400)
        events_after_second = self.db.query(models.Event).count()

        self.assertEqual(events_after_first, events_after_second, "Repeated execution must not create duplicate events")


# ============================================================================
# Step 10.8: Notification Idempotency, Deduplication & Cleanup Tests
# ============================================================================

class TestNotificationIdempotencyAndCleanup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls.client = TestClient(app)
        cls.ts = int(time_mod.time() * 1000)
        cls.pwd = "Password123!"

        # User 1: Primary recipient
        email1 = f"idem_user1_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email1, "password": cls.pwd, "confirm_password": cls.pwd})
        res1 = cls.client.post("/auth/login", json={"email": email1, "password": cls.pwd}).json()
        cls.token1 = res1["access_token"]
        cls.headers_1 = {"Authorization": f"Bearer {cls.token1}"}
        cls.user1 = cls.db.query(models.User).filter(models.User.email == email1).first()

        # User 2: Second user for cross-user tests
        email2 = f"idem_user2_{cls.ts}@test.com"
        cls.client.post("/auth/register", json={"email": email2, "password": cls.pwd, "confirm_password": cls.pwd})
        res2 = cls.client.post("/auth/login", json={"email": email2, "password": cls.pwd}).json()
        cls.token2 = res2["access_token"]
        cls.headers_2 = {"Authorization": f"Bearer {cls.token2}"}
        cls.user2 = cls.db.query(models.User).filter(models.User.email == email2).first()

        # Community 1 & 2
        cls.community1 = models.Community(
            name=f"Idem Community 1 {cls.ts}",
            description="Testing idempotency 1",
            created_by=cls.user1.user_id,
        )
        cls.community2 = models.Community(
            name=f"Idem Community 2 {cls.ts}",
            description="Testing idempotency 2",
            created_by=cls.user1.user_id,
        )
        cls.db.add_all([cls.community1, cls.community2])
        cls.db.commit()
        cls.db.refresh(cls.community1)
        cls.db.refresh(cls.community2)

        # Member for community 1
        member1 = models.CommunityMember(
            community_id=cls.community1.community_id,
            user_id=cls.user1.user_id,
            role="ORGANIZER",
        )
        cls.db.add(member1)
        cls.db.commit()

        # Event
        event = models.Event(
            activity_id=1,
            host_id=cls.user1.user_id,
            title=f"Idem Event {cls.ts}",
            event_date=date.today() + timedelta(days=5),
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=10,
            status="PUBLISHED",
        )
        cls.db.add(event)
        cls.db.commit()
        cls.db.refresh(event)
        cls.event = event

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_idempotent_retry_returns_existing_notification(self):
        """Creating identical notification twice returns existing row without inserting duplicate."""
        payload = {"alert_code": f"CODE_TEST_01_{self.ts}"}
        notif1 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "System Notice 1",
            "message": "Notice details.",
            "payload": payload,
        })
        count_before = self.db.query(models.Notification).count()

        notif2 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "System Notice 1 (retry)",
            "message": "Notice details retry.",
            "payload": payload,
        })
        count_after = self.db.query(models.Notification).count()

        self.assertEqual(notif1.notification_id, notif2.notification_id)
        self.assertEqual(count_before, count_after, "Duplicate insert must be prevented")

    def test_02_different_context_creates_distinct_valid_notifications(self):
        """Notifications with different context create two distinct valid records."""
        notif_a = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "System Alert A",
            "message": "Alert A details.",
            "payload": {"alert_code": f"DIFF_CTX_A_{self.ts}"},
        })
        notif_b = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "System Alert B",
            "message": "Alert B details.",
            "payload": {"alert_code": f"DIFF_CTX_B_{self.ts}"},
        })
        self.assertNotEqual(notif_a.notification_id, notif_b.notification_id)

    def test_03_feedback_request_permanent_single_shot_per_event_and_user(self):
        """FEEDBACK_REQUEST is permanently single-shot per (user, event) even if dismissed."""
        # Create initial feedback request
        fb1 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "FEEDBACK_REQUEST",
            "title": "Rate Event Experience",
            "message": "How was the match?",
            "payload": {"event_id": self.event.event_id},
            "related_event_id": self.event.event_id,
        })
        self.assertEqual(fb1.status, "UNREAD")

        # User dismisses it
        dismissed = dismiss_notification(self.db, fb1.notification_id, self.user1.user_id)
        self.assertEqual(dismissed.status, "DISMISSED")

        # Attempt to create another FEEDBACK_REQUEST for the same event
        count_before = self.db.query(models.Notification).count()
        fb2 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "FEEDBACK_REQUEST",
            "title": "Rate Event Experience Again?",
            "message": "Another prompt.",
            "payload": {"event_id": self.event.event_id},
            "related_event_id": self.event.event_id,
        })
        count_after = self.db.query(models.Notification).count()

        self.assertEqual(fb1.notification_id, fb2.notification_id)
        self.assertEqual(fb2.status, "DISMISSED", "Existing row must be returned intact")
        self.assertEqual(count_before, count_after, "Never recreate dismissed feedback request")

    def test_04_accepted_maintenance_allows_future_cadence(self):
        """Accepted maintenance recommendation allows a future cadence or date to create a new notification."""
        # Week 1 maintenance recommendation
        notif_w1 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Maintenance Week 1",
            "message": "Schedule week 1 session.",
            "payload": {
                "community_id": self.community1.community_id,
                "cadence": "WEEK_1",
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })
        # Accept Week 1
        accepted_w1 = accept_notification(self.db, notif_w1.notification_id, self.user1.user_id)
        self.assertEqual(accepted_w1.status, "ACCEPTED")

        # Week 2 maintenance recommendation
        notif_w2 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Maintenance Week 2",
            "message": "Schedule week 2 session.",
            "payload": {
                "community_id": self.community1.community_id,
                "cadence": "WEEK_2",
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })
        self.assertNotEqual(notif_w1.notification_id, notif_w2.notification_id, "Future cadence must create a new valid notification")
        self.assertEqual(notif_w2.status, "UNREAD")

    def test_05_community_reactivation_same_date_blocked_different_date_allowed(self):
        """Reactivation duplicate blocked for same date; different reactivation date allowed."""
        date_1 = "2026-11-01"
        date_2 = "2026-11-15"

        notif_d1 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Reactivation Date 1",
            "message": "Reactivate community.",
            "payload": {
                "community_id": self.community1.community_id,
                "reactivation_date": date_1,
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })

        # Retry with same date -> duplicate blocked, returns existing
        notif_d1_retry = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Reactivation Date 1 Retry",
            "message": "Reactivate community.",
            "payload": {
                "community_id": self.community1.community_id,
                "reactivation_date": date_1,
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })
        self.assertEqual(notif_d1.notification_id, notif_d1_retry.notification_id)

        # Different date -> allowed as a new notification
        notif_d2 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Reactivation Date 2",
            "message": "Reactivate community second attempt.",
            "payload": {
                "community_id": self.community1.community_id,
                "reactivation_date": date_2,
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })
        self.assertNotEqual(notif_d1.notification_id, notif_d2.notification_id)

    def test_06_in_batch_deduplication_prevents_duplicates_within_same_batch(self):
        """batch_create_notifications prevents duplicate inserts inside the same batch."""
        alert_code = f"BATCH_INTERNAL_{self.ts}"
        batch_items = [
            {
                "recipient_user_id": self.user1.user_id,
                "notification_type": "SYSTEM_ALERT",
                "title": "Batch Notice 1",
                "message": "First in batch.",
                "payload": {"alert_code": alert_code},
            },
            {
                "recipient_user_id": self.user1.user_id,
                "notification_type": "SYSTEM_ALERT",
                "title": "Batch Notice 2 (duplicate)",
                "message": "Second in batch.",
                "payload": {"alert_code": alert_code},
            },
        ]

        count_before = self.db.query(models.Notification).count()
        results = batch_create_notifications(self.db, batch_items)
        count_after = self.db.query(models.Notification).count()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].notification_id, results[1].notification_id)
        self.assertEqual(count_after, count_before + 1, "Batch must insert only 1 physical row for duplicates")

    def test_07_batch_deduplication_against_existing_db_records(self):
        """batch_create_notifications prevents duplicates against existing DB rows."""
        alert_code = f"BATCH_DB_GUARD_{self.ts}"
        existing = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Already in DB",
            "message": "Pre-existing alert.",
            "payload": {"alert_code": alert_code},
        })

        count_before = self.db.query(models.Notification).count()
        results = batch_create_notifications(self.db, [
            {
                "recipient_user_id": self.user1.user_id,
                "notification_type": "SYSTEM_ALERT",
                "title": "Attempted Duplicate In Batch",
                "message": "Pre-existing alert retry.",
                "payload": {"alert_code": alert_code},
            }
        ])
        count_after = self.db.query(models.Notification).count()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].notification_id, existing.notification_id)
        self.assertEqual(count_before, count_after, "Batch must not insert duplicate of DB record")

    def test_08_dynamic_stale_detection_on_past_target_date(self):
        """is_stale property dynamically detects expired target dates without database mutation."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        # Expired actionable notification
        stale_notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Past Reactivation",
            "message": "Expired date.",
            "payload": {
                "community_id": self.community1.community_id,
                "reactivation_date": yesterday,
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })

        # Fresh actionable notification
        fresh_notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Future Reactivation",
            "message": "Upcoming date.",
            "payload": {
                "community_id": self.community1.community_id,
                "reactivation_date": tomorrow,
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })

        # Informational notification (never stale)
        info_notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "General System Notice",
            "message": "Information only.",
            "payload": {"date": yesterday},
        })

        self.assertTrue(stale_notif.is_stale)
        self.assertTrue(is_notification_stale(stale_notif))
        self.assertFalse(fresh_notif.is_stale)
        self.assertFalse(is_notification_stale(fresh_notif))
        self.assertFalse(info_notif.is_stale)
        self.assertFalse(is_notification_stale(info_notif))

    def test_09_stale_actionable_notification_cannot_execute(self):
        """Expired actionable notification cannot be executed and returns 400."""
        past_date = (date.today() - timedelta(days=3)).isoformat()
        plan = {
            "action": "CREATE_EVENT",
            "parameters": {
                "activity_id": 1,
                "event_date": past_date,
                "start_time": "18:00:00",
                "end_time": "20:00:00",
                "title": "Stale Action Event",
                "max_capacity": 10,
            },
        }
        stale_notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "ACTIVITY_MAINTENANCE",
            "title": "Stale Maintenance",
            "message": "Past session date.",
            "payload": {
                "community_id": self.community1.community_id,
                "actionable": True,
                "target_action": "CREATE_EVENT",
                "action_plan": plan,
            },
            "related_community_id": self.community1.community_id,
        })
        self.assertTrue(stale_notif.is_stale)

        events_before = self.db.query(models.Event).count()
        res = self.client.post(f"/notifications/{stale_notif.notification_id}/execute", headers=self.headers_1)
        self.assertEqual(res.status_code, 400)
        self.assertIn("expired", res.json()["detail"].lower())

        events_after = self.db.query(models.Event).count()
        self.assertEqual(events_before, events_after, "Stale notification must trigger zero domain mutations")

    def test_10_historical_stale_notification_remains_intact(self):
        """Historical stale notification remains in DB and inbox without mutation or deletion."""
        past_date = (date.today() - timedelta(days=5)).isoformat()
        notif = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "COMMUNITY_REACTIVATION",
            "title": "Historical Intact Reactivation",
            "message": "Audit history preserved.",
            "payload": {
                "community_id": self.community1.community_id,
                "reactivation_date": past_date,
                "actionable": True,
            },
            "related_community_id": self.community1.community_id,
        })

        # Query inbox via API
        res = self.client.get("/notifications", headers=self.headers_1)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        matching = [n for n in data["notifications"] if n["notification_id"] == notif.notification_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["status"], "UNREAD", "Status must remain UNREAD, not mutated to STALE")
        self.assertTrue(matching[0]["is_stale"], "API response must reflect is_stale=True")

        # Database row directly checked
        self.db.expire_all()
        db_row = self.db.query(models.Notification).filter(models.Notification.notification_id == notif.notification_id).first()
        self.assertIsNotNone(db_row)
        self.assertEqual(db_row.status, "UNREAD")

    def test_11_cross_user_notifications_never_collide(self):
        """Identical notification types and communities sent to different users never collide."""
        alert_code = f"CROSS_USER_{self.ts}"
        notif_u1 = create_notification(self.db, {
            "recipient_user_id": self.user1.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Cross User Alert",
            "message": "Notice for User 1.",
            "payload": {"alert_code": alert_code},
        })
        notif_u2 = create_notification(self.db, {
            "recipient_user_id": self.user2.user_id,
            "notification_type": "SYSTEM_ALERT",
            "title": "Cross User Alert",
            "message": "Notice for User 2.",
            "payload": {"alert_code": alert_code},
        })

        self.assertNotEqual(notif_u1.notification_id, notif_u2.notification_id)
        self.assertEqual(notif_u1.recipient_user_id, self.user1.user_id)
        self.assertEqual(notif_u2.recipient_user_id, self.user2.user_id)

    def test_12_pending_community_invitation_deduplicates_while_pending_allows_when_resolved(self):
        """Pending invitation deduplicates while pending, but a new one is allowed once resolved."""
        # 1. First invitation: UNREAD
        inv1 = create_notification(self.db, {
            "recipient_user_id": self.user2.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Join Community 2",
            "message": "You are invited to join.",
            "payload": {"community_id": self.community2.community_id, "actionable": True},
            "related_community_id": self.community2.community_id,
        })
        self.assertEqual(inv1.status, "UNREAD")

        # 2. Second invitation while first is pending -> returns existing
        inv2 = create_notification(self.db, {
            "recipient_user_id": self.user2.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Join Community 2 (retry)",
            "message": "You are invited to join.",
            "payload": {"community_id": self.community2.community_id, "actionable": True},
            "related_community_id": self.community2.community_id,
        })
        self.assertEqual(inv1.notification_id, inv2.notification_id)

        # 3. Dismiss first invitation
        dismiss_notification(self.db, inv1.notification_id, self.user2.user_id)

        # 4. Third invitation attempt -> allowed since first is no longer pending
        inv3 = create_notification(self.db, {
            "recipient_user_id": self.user2.user_id,
            "notification_type": "COMMUNITY_INVITATION",
            "title": "Join Community 2 (fresh)",
            "message": "You are invited to join again.",
            "payload": {"community_id": self.community2.community_id, "actionable": True},
            "related_community_id": self.community2.community_id,
        })
        self.assertNotEqual(inv1.notification_id, inv3.notification_id)
        self.assertEqual(inv3.status, "UNREAD")


if __name__ == "__main__":
    unittest.main()




