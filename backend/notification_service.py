"""
Vynk (Localy) - Notification Creation & In-App Delivery Service
Step 10.2: Reliable in-app notification persistence primitive.

Responsibilities:
- Validate notification inputs, recipient existence, and entity context against live database.
- Enforce Step 10.1 state rules (initial status='UNREAD', is_read=False, read_at=None).
- Persist notification rows atomically with rollback guarantees.
- Return persisted Notification entities matching Step 10.1 contracts.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session

import models
import schemas


class NotificationServiceError(ValueError):
    """Domain exception raised when notification creation validation fails."""
    pass


def is_notification_stale(notification: Any) -> bool:
    """
    Step 10.8.3 Stale Action Detection:
    Inspects actionable notification payload to determine if the target action date has passed.
    Historical record remains untouched; does not mutate database or alter status.
    """
    if isinstance(notification, dict):
        notif_type = notification.get("notification_type")
        payload = notification.get("payload") or {}
    else:
        notif_type = getattr(notification, "notification_type", None)
        payload = getattr(notification, "payload", None) or {}

    if hasattr(notif_type, "value"):
        notif_type = notif_type.value

    if str(notif_type).strip().upper() not in schemas.ACTIONABLE_NOTIFICATION_TYPES:
        return False

    action_plan = payload.get("action_plan") or {}
    params = action_plan.get("parameters") or payload.get("parameters") or {}

    raw_date = (
        params.get("event_date")
        or payload.get("reactivation_date")
        or payload.get("date")
    )
    if raw_date:
        try:
            target_date = date.fromisoformat(str(raw_date)[:10])
            if target_date < date.today():
                return True
        except Exception:
            pass

    return False


def compute_notification_idempotency_key(req: schemas.NotificationCreate) -> str:
    """
    Step 10.8.1 Type-Aware Idempotency Identity Fingerprint:
    Computes a deterministic string key based on notification type and domain context.
    """
    notif_type = req.notification_type.value if hasattr(req.notification_type, "value") else str(req.notification_type)
    uid = req.recipient_user_id
    payload = req.payload or {}
    comm_id = req.related_community_id or payload.get("community_id") or 0
    event_id = req.related_event_id or payload.get("event_id") or 0

    if notif_type == schemas.NotificationType.FEEDBACK_REQUEST.value:
        return f"{uid}:{notif_type}:{event_id}"
    elif notif_type == schemas.NotificationType.COMMUNITY_INVITATION.value:
        return f"{uid}:{notif_type}:{comm_id}"
    elif notif_type == schemas.NotificationType.ACTIVITY_MAINTENANCE.value:
        cadence = payload.get("cadence", "")
        plan_date = (payload.get("action_plan") or {}).get("parameters", {}).get("event_date", "")
        return f"{uid}:{notif_type}:{comm_id}:{cadence}:{plan_date}"
    elif notif_type == schemas.NotificationType.COMMUNITY_REACTIVATION.value:
        react_date = payload.get("reactivation_date") or (payload.get("action_plan") or {}).get("parameters", {}).get("event_date", "")
        return f"{uid}:{notif_type}:{comm_id}:{react_date}"
    elif notif_type == schemas.NotificationType.RE_ENGAGEMENT.value:
        return f"{uid}:{notif_type}:{comm_id}"
    elif notif_type == schemas.NotificationType.SYSTEM_ALERT.value:
        alert_code = payload.get("alert_code", req.title.strip())
        return f"{uid}:{notif_type}:{alert_code}"
    return f"{uid}:{notif_type}:{comm_id}:{event_id}"


def find_existing_duplicate_notification(
    db: Session,
    req: schemas.NotificationCreate,
) -> Optional[models.Notification]:
    """
    Step 10.8.2 Type-Aware Duplicate Lookup:
    Enforces Vynk's deduplication invariants:
    - FEEDBACK_REQUEST: permanent single-shot per (user, event) across all statuses.
    - COMMUNITY_INVITATION: duplicate while pending (UNREAD, READ) for same (user, community).
    - ACTIVITY_MAINTENANCE: duplicate while pending for same (user, community, cadence/date). Once resolved, repeatable.
    - COMMUNITY_REACTIVATION: duplicate while pending for same (user, community, reactivation_date). Different dates allowed.
    - RE_ENGAGEMENT: duplicate while pending for same (user, community). Repeatable once resolved.
    - SYSTEM_ALERT: duplicate while UNREAD for same (user, alert_code).
    """
    notif_type = req.notification_type.value if hasattr(req.notification_type, "value") else str(req.notification_type)
    uid = req.recipient_user_id
    payload = req.payload or {}
    comm_id = req.related_community_id or payload.get("community_id")
    event_id = req.related_event_id or payload.get("event_id")

    query = db.query(models.Notification).filter(
        models.Notification.recipient_user_id == uid,
        models.Notification.notification_type == notif_type,
    )

    if notif_type == schemas.NotificationType.FEEDBACK_REQUEST.value:
        if event_id:
            return query.filter(models.Notification.related_event_id == event_id).first()
        return None

    elif notif_type == schemas.NotificationType.COMMUNITY_INVITATION.value:
        if comm_id:
            return query.filter(
                models.Notification.related_community_id == comm_id,
                models.Notification.status.in_(["UNREAD", "READ"]),
            ).first()
        return None

    elif notif_type == schemas.NotificationType.ACTIVITY_MAINTENANCE.value:
        if comm_id:
            active_list = query.filter(
                models.Notification.related_community_id == comm_id,
                models.Notification.status.in_(["UNREAD", "READ"]),
            ).all()
            target_cadence = payload.get("cadence")
            target_date = (payload.get("action_plan") or {}).get("parameters", {}).get("event_date")
            for notif in active_list:
                p = notif.payload or {}
                c = p.get("cadence")
                d = (p.get("action_plan") or {}).get("parameters", {}).get("event_date")
                if (target_date and d == target_date) or (target_cadence and c == target_cadence):
                    return notif
                if not target_date and not target_cadence:
                    return notif
        return None

    elif notif_type == schemas.NotificationType.COMMUNITY_REACTIVATION.value:
        if comm_id:
            active_list = query.filter(
                models.Notification.related_community_id == comm_id,
                models.Notification.status.in_(["UNREAD", "READ"]),
            ).all()
            target_date = payload.get("reactivation_date") or (payload.get("action_plan") or {}).get("parameters", {}).get("event_date")
            for notif in active_list:
                p = notif.payload or {}
                d = p.get("reactivation_date") or (p.get("action_plan") or {}).get("parameters", {}).get("event_date")
                if target_date and d == target_date:
                    return notif
                if not target_date and not d:
                    return notif
        return None

    elif notif_type == schemas.NotificationType.RE_ENGAGEMENT.value:
        if comm_id:
            return query.filter(
                models.Notification.related_community_id == comm_id,
                models.Notification.status.in_(["UNREAD", "READ"]),
            ).first()
        return None

    elif notif_type == schemas.NotificationType.SYSTEM_ALERT.value:
        alert_code = payload.get("alert_code")
        if alert_code:
            active_list = query.filter(models.Notification.status == "UNREAD").all()
            for notif in active_list:
                if (notif.payload or {}).get("alert_code") == alert_code:
                    return notif
        else:
            return query.filter(
                models.Notification.status == "UNREAD",
                models.Notification.title == req.title.strip(),
            ).first()

    return None


def create_notification(
    db: Session,
    notification_in: Union[schemas.NotificationCreate, Dict[str, Any]],
    initial_status: Optional[str] = None,
) -> models.Notification:
    """
    Creates and persists a single in-app notification record.
    Enforces type-specific idempotency: returns existing notification if matching duplicate exists.
    """
    # 1. Parse / normalize input through Pydantic contract
    if isinstance(notification_in, dict):
        try:
            req = schemas.NotificationCreate(**notification_in)
        except Exception as e:
            raise NotificationServiceError(f"Invalid notification payload: {e}") from e
    elif isinstance(notification_in, schemas.NotificationCreate):
        req = notification_in
    else:
        raise NotificationServiceError("notification_in must be a NotificationCreate instance or dict.")

    # 2. Extract notification type string
    notif_type_str = req.notification_type.value if hasattr(req.notification_type, "value") else str(req.notification_type)
    valid_types = {t.value for t in schemas.NotificationType}
    if notif_type_str not in valid_types:
        raise NotificationServiceError(f"Invalid notification_type '{notif_type_str}'. Must be one of {valid_types}.")

    # 3. Validate recipient existence in database
    recipient = db.query(models.User).filter(models.User.user_id == req.recipient_user_id).first()
    if not recipient:
        raise NotificationServiceError(f"Recipient user #{req.recipient_user_id} does not exist.")

    # 4. Validate related community if provided
    if req.related_community_id is not None:
        comm = db.query(models.Community).filter(models.Community.community_id == req.related_community_id).first()
        if not comm:
            raise NotificationServiceError(f"Related community #{req.related_community_id} does not exist.")

    # 5. Validate related event if provided
    if req.related_event_id is not None:
        ev = db.query(models.Event).filter(models.Event.event_id == req.related_event_id).first()
        if not ev:
            raise NotificationServiceError(f"Related event #{req.related_event_id} does not exist.")

    # 6. Idempotency & Duplicate Check
    existing = find_existing_duplicate_notification(db, req)
    if existing:
        return existing

    # 7. Validate initial state
    target_status = "UNREAD"
    if initial_status is not None:
        norm_status = str(initial_status).strip().upper()
        if norm_status != "UNREAD":
            valid, err = schemas.validate_notification_status_transition("UNREAD", norm_status, notif_type_str)
            if not valid:
                raise NotificationServiceError(f"Cannot initialize notification in state '{norm_status}': {err}")
            target_status = norm_status

    is_read = target_status in ["READ", "DISMISSED", "ACCEPTED"]
    read_at = datetime.now() if is_read else None

    # 8. Construct entity
    notification_entity = models.Notification(
        recipient_user_id=req.recipient_user_id,
        notification_type=notif_type_str,
        title=req.title.strip(),
        message=req.message.strip(),
        payload=req.payload,
        source_action=req.source_action,
        related_community_id=req.related_community_id,
        related_event_id=req.related_event_id,
        is_read=is_read,
        read_at=read_at,
        status=target_status,
    )

    # 9. Atomic persistence with rollback safety
    try:
        db.add(notification_entity)
        db.commit()
        db.refresh(notification_entity)
        return notification_entity
    except Exception as e:
        db.rollback()
        raise e


def batch_create_notifications(
    db: Session,
    notifications_in: List[Union[schemas.NotificationCreate, Dict[str, Any]]],
) -> List[models.Notification]:
    """
    Atomically creates and persists multiple notifications.
    Enforces in-batch de-duplication and database duplicate avoidance.
    If any single record fails validation, the entire batch rolls back.
    """
    if not notifications_in:
        return []

    created_entities = []
    seen_batch_keys: Dict[str, models.Notification] = {}

    try:
        for notif_in in notifications_in:
            if isinstance(notif_in, dict):
                req = schemas.NotificationCreate(**notif_in)
            else:
                req = notif_in

            batch_key = compute_notification_idempotency_key(req)
            if batch_key in seen_batch_keys:
                created_entities.append(seen_batch_keys[batch_key])
                continue

            # Check DB duplicate
            db_duplicate = find_existing_duplicate_notification(db, req)
            if db_duplicate:
                seen_batch_keys[batch_key] = db_duplicate
                created_entities.append(db_duplicate)
                continue

            notif_type_str = req.notification_type.value if hasattr(req.notification_type, "value") else str(req.notification_type)

            # Validate recipient
            recipient = db.query(models.User).filter(models.User.user_id == req.recipient_user_id).first()
            if not recipient:
                raise NotificationServiceError(f"Recipient user #{req.recipient_user_id} does not exist.")

            # Validate related community
            if req.related_community_id is not None:
                comm = db.query(models.Community).filter(models.Community.community_id == req.related_community_id).first()
                if not comm:
                    raise NotificationServiceError(f"Related community #{req.related_community_id} does not exist.")

            # Validate related event
            if req.related_event_id is not None:
                ev = db.query(models.Event).filter(models.Event.event_id == req.related_event_id).first()
                if not ev:
                    raise NotificationServiceError(f"Related event #{req.related_event_id} does not exist.")

            entity = models.Notification(
                recipient_user_id=req.recipient_user_id,
                notification_type=notif_type_str,
                title=req.title.strip(),
                message=req.message.strip(),
                payload=req.payload,
                source_action=req.source_action,
                related_community_id=req.related_community_id,
                related_event_id=req.related_event_id,
                is_read=False,
                read_at=None,
                status="UNREAD",
            )
            db.add(entity)
            seen_batch_keys[batch_key] = entity
            created_entities.append(entity)

        db.commit()
        for e in created_entities:
            db.refresh(e)
        return created_entities
    except Exception as e:
        db.rollback()
        if isinstance(e, NotificationServiceError):
            raise e
        raise NotificationServiceError(f"Batch notification creation failed: {e}") from e


class NotificationNotFoundError(NotificationServiceError):
    """Raised when notification does not exist."""
    pass


class NotificationPermissionError(NotificationServiceError):
    """Raised when user attempts to access or modify another user's notification."""
    pass


class NotificationTerminalStateError(NotificationServiceError):
    """Raised when notification is in a terminal state (DISMISSED/ACCEPTED) and cannot be reopened."""
    pass


class NotificationInvalidStateError(NotificationServiceError):
    """Raised when notification transition is invalid or rejected by domain rules."""
    pass


def mark_notification_as_read(
    db: Session,
    notification_id: int,
    user_id: int,
) -> models.Notification:
    """
    Step 10.4: Marks an unread notification as READ for the authenticated user.
    Enforces:
    - Notification existence (404 if missing)
    - Ownership verification: recipient_user_id == user_id (403 if mismatch)
    - Idempotency: if already READ, preserves original read_at timestamp and returns entity
    - Terminal immutability: if DISMISSED or ACCEPTED, cannot transition or reopen
    - Atomic database commit
    """
    notif = db.query(models.Notification).filter(models.Notification.notification_id == notification_id).first()
    if not notif:
        raise NotificationNotFoundError(f"Notification #{notification_id} not found.")

    if notif.recipient_user_id != user_id:
        raise NotificationPermissionError(f"User #{user_id} does not have permission to modify notification #{notification_id}.")

    # Terminal state check
    if notif.status in ["DISMISSED", "ACCEPTED"]:
        raise NotificationTerminalStateError(f"Cannot mark notification #{notification_id} as read: Notification is in terminal state '{notif.status}'.")

    # If already READ, idempotent no-op (preserves original read_at)
    if notif.status == "READ" and notif.is_read:
        return notif

    # Apply transition
    notif.status = "READ"
    notif.is_read = True
    notif.read_at = datetime.now()

    try:
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as e:
        db.rollback()
        raise e


def accept_notification(
    db: Session,
    notification_id: int,
    user_id: int,
) -> models.Notification:
    """
    Step 10.6: Transitions an actionable notification to ACCEPTED for the authenticated user.
    Enforces:
    - Notification existence (404 if missing)
    - Ownership verification: recipient_user_id == user_id (403 if mismatch)
    - Actionable gate: Only actionable notification types (COMMUNITY_INVITATION, ACTIVITY_MAINTENANCE, COMMUNITY_REACTIVATION) can be accepted
    - State transition validity: UNREAD -> ACCEPTED, READ -> ACCEPTED
    - Terminal immutability: DISMISSED or ACCEPTED cannot transition again
    - Read state: is_read=True, read_at preserved or set to current timestamp
    - Zero execution: Strictly does NOT execute the target action (CREATE_EVENT, etc.)
    """
    notif = db.query(models.Notification).filter(models.Notification.notification_id == notification_id).first()
    if not notif:
        raise NotificationNotFoundError(f"Notification #{notification_id} not found.")

    if notif.recipient_user_id != user_id:
        raise NotificationPermissionError(f"User #{user_id} does not have permission to accept notification #{notification_id}.")

    valid, err = schemas.validate_notification_status_transition(notif.status, "ACCEPTED", notif.notification_type)
    if not valid:
        if notif.status in ["DISMISSED", "ACCEPTED"]:
            raise NotificationTerminalStateError(err)
        raise NotificationInvalidStateError(err)

    # Transition to ACCEPTED
    notif.status = "ACCEPTED"
    notif.is_read = True
    if not notif.read_at:
        notif.read_at = datetime.now()

    try:
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as e:
        db.rollback()
        raise e


def dismiss_notification(
    db: Session,
    notification_id: int,
    user_id: int,
) -> models.Notification:
    """
    Step 10.6: Transitions a notification to DISMISSED for the authenticated user.
    Enforces:
    - Notification existence (404 if missing)
    - Ownership verification: recipient_user_id == user_id (403 if mismatch)
    - State transition validity: UNREAD -> DISMISSED, READ -> DISMISSED
    - Terminal immutability: DISMISSED or ACCEPTED cannot transition again
    - Read state: is_read=True, read_at preserved or set to current timestamp
    """
    notif = db.query(models.Notification).filter(models.Notification.notification_id == notification_id).first()
    if not notif:
        raise NotificationNotFoundError(f"Notification #{notification_id} not found.")

    if notif.recipient_user_id != user_id:
        raise NotificationPermissionError(f"User #{user_id} does not have permission to dismiss notification #{notification_id}.")

    valid, err = schemas.validate_notification_status_transition(notif.status, "DISMISSED", notif.notification_type)
    if not valid:
        if notif.status in ["DISMISSED", "ACCEPTED"]:
            raise NotificationTerminalStateError(err)
        raise NotificationInvalidStateError(err)

    # Transition to DISMISSED
    notif.status = "DISMISSED"
    notif.is_read = True
    if not notif.read_at:
        notif.read_at = datetime.now()

    try:
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as e:
        db.rollback()
        raise e


def execute_notification_action(
    db: Session,
    notification_id: int,
    user_id: int,
):
    """
    Step 10.7: Bridge function delegating actionable notification execution to Step 9 dispatcher.
    """
    import main
    return main.execute_notification_action(db, notification_id, user_id)



