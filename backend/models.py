from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


# ============================================================================
# 1. USERS (Authentication & Security)
# ============================================================================

class User(Base):
    """Single source of truth for user authentication and account credentials."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    availability = relationship("UserAvailability", back_populates="user", cascade="all, delete-orphan")
    owned_venues = relationship("Venue", back_populates="owner")
    created_activities = relationship("Activity", back_populates="creator")
    hosted_events = relationship("Event", back_populates="host")
    event_participations = relationship("EventParticipant", back_populates="user", cascade="all, delete-orphan")
    payment_account = relationship("PaymentAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user")
    community_memberships = relationship("CommunityMember", back_populates="user", cascade="all, delete-orphan")
    given_feedbacks = relationship("Feedback", back_populates="reviewer", cascade="all, delete-orphan")


# ============================================================================
# 2. PROFILES (User-Facing Public Details)
# ============================================================================

class Profile(Base):
    """Public identity, bio, and approximate locality."""
    __tablename__ = "profiles"

    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(512), nullable=True)
    approx_locality = Column(String(150), nullable=True)
    budget_preference = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="profile")


# ============================================================================
# 3. INTERESTS (Master Taxonomy Catalog)
# ============================================================================

class Interest(Base):
    """Standardized master interests catalog."""
    __tablename__ = "interests"

    interest_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)

    # Relationships
    user_interests = relationship("UserInterest", back_populates="interest", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="interest")


# ============================================================================
# 4. USER_INTERESTS (User ↔ Interests Junction)
# ============================================================================

class UserInterest(Base):
    """Many-to-Many junction linking Users to Interests."""
    __tablename__ = "user_interests"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    interest_id = Column(Integer, ForeignKey("interests.interest_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="interests")
    interest = relationship("Interest", back_populates="user_interests")


# ============================================================================
# 5. SKILLS (Master Skills Catalog)
# ============================================================================

class Skill(Base):
    """Standardized master skills catalog."""
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)

    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


# ============================================================================
# 6. USER_SKILLS (User ↔ Skills with Proficiency)
# ============================================================================

class UserSkill(Base):
    """Many-to-Many junction linking Users to Skills with level and offering flag."""
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True)
    skill_level = Column(String(50), nullable=False)  # 'Beginner', 'Intermediate', 'Advanced'
    is_offering = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")


# ============================================================================
# 7. USER_AVAILABILITY (Weekly Schedule Windows)
# ============================================================================

class UserAvailability(Base):
    """Recurring weekly schedule slots for matchmaking."""
    __tablename__ = "user_availability"

    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(String(20), nullable=False)  # 'Monday', 'Saturday', 'Weekend', etc.
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Relationships
    user = relationship("User", back_populates="availability")


# ============================================================================
# 8. ACTIVITIES (Activity Templates & Concepts)
# ============================================================================

class Activity(Base):
    """Activity concept/template linked to primary interest."""
    __tablename__ = "activities"

    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    interest_id = Column(Integer, ForeignKey("interests.interest_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interest = relationship("Interest", back_populates="activities")
    creator = relationship("User", back_populates="created_activities")
    events = relationship("Event", back_populates="activity", cascade="all, delete-orphan")
    venue_activities = relationship("VenueActivity", back_populates="activity", cascade="all, delete-orphan")


# ============================================================================
# 9. VENUES (Physical Locations & Spaces)
# ============================================================================

class Venue(Base):
    """Physical spaces (courts, cafes, studios, grounds) registered by admin or owners."""
    __tablename__ = "venues"

    venue_id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=False)
    locality = Column(String(100), nullable=False, index=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)  # 'ACTIVE', 'INACTIVE', 'PENDING_VERIFICATION'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="owned_venues")
    supported_activities = relationship("VenueActivity", back_populates="venue", cascade="all, delete-orphan")
    slots = relationship("VenueSlot", back_populates="venue", cascade="all, delete-orphan")


# ============================================================================
# 10. VENUE_ACTIVITIES (Venue ↔ Activities Junction)
# ============================================================================

class VenueActivity(Base):
    """Supported activities at a specific venue."""
    __tablename__ = "venue_activities"

    venue_id = Column(Integer, ForeignKey("venues.venue_id", ondelete="CASCADE"), primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.activity_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    venue = relationship("Venue", back_populates="supported_activities")
    activity = relationship("Activity", back_populates="venue_activities")


# ============================================================================
# 11. VENUE_SLOTS (Bookable Time Windows & Ground Pricing)
# ============================================================================

class VenueSlot(Base):
    """Specific bookable time slots for a venue with total price."""
    __tablename__ = "venue_slots"

    slot_id = Column(Integer, primary_key=True, autoincrement=True)
    venue_id = Column(Integer, ForeignKey("venues.venue_id", ondelete="CASCADE"), nullable=False, index=True)
    slot_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    price_total = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="AVAILABLE", nullable=False, index=True)  # 'AVAILABLE', 'HELD', 'BOOKED'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("venue_id", "slot_date", "start_time", "end_time", name="uq_venue_slot_time"),
    )

    # Relationships
    venue = relationship("Venue", back_populates="slots")
    booking = relationship("VenueBooking", back_populates="slot", uselist=False)


# ============================================================================
# 12. EVENTS (Scheduled Gatherings)
# ============================================================================

class Event(Base):
    """Scheduled real-world activity instance with date, time, capacity, and host."""
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey("activities.activity_id", ondelete="RESTRICT"), nullable=False, index=True)
    host_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)  # 'DRAFT', 'PUBLISHED', 'FULL', 'COMPLETED', 'CANCELLED'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("max_capacity > 0", name="chk_event_max_capacity"),
    )

    # Relationships
    activity = relationship("Activity", back_populates="events")
    host = relationship("User", back_populates="hosted_events")
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")
    venue_booking = relationship("VenueBooking", back_populates="event", uselist=False, cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="event", cascade="all, delete-orphan")


# ============================================================================
# 13. VENUE_BOOKINGS (Event ↔ VenueSlot Bridge)
# ============================================================================

class VenueBooking(Base):
    """Bridge linking an Event to a reserved VenueSlot with payment state."""
    __tablename__ = "venue_bookings"

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("venue_slots.slot_id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    booked_by = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # 'PENDING', 'CONFIRMED', 'CANCELLED', 'REFUNDED'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    event = relationship("Event", back_populates="venue_booking")
    slot = relationship("VenueSlot", back_populates="booking")
    booker = relationship("User")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    payout = relationship("Payout", back_populates="booking", uselist=False, cascade="all, delete-orphan")


# ============================================================================
# 14. EVENT_PARTICIPANTS (Attendance & Reservation Roster)
# ============================================================================

class EventParticipant(Base):
    """Event attendance and reservation roster."""
    __tablename__ = "event_participants"

    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    status = Column(String(50), default="CONFIRMED", nullable=False, index=True)  # 'INTERESTED', 'CONFIRMED', 'CHECKED_IN', 'CANCELLED'
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="participants")
    user = relationship("User", back_populates="event_participations")


# ============================================================================
# 15. PAYMENT_ACCOUNTS (Merchant & Payout Accounts)
# ============================================================================

class PaymentAccount(Base):
    """External payment/payout accounts for venue owners & organizers."""
    __tablename__ = "payment_accounts"

    payment_account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # 'razorpay', 'stripe'
    provider_account_id = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)  # 'ACTIVE', 'PENDING', 'SUSPENDED'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="payment_account")
    payouts = relationship("Payout", back_populates="payment_account")


# ============================================================================
# 16. PAYMENTS (Individual Participant Split Payments)
# ============================================================================

class Payment(Base):
    """Individual participant split share paid toward a VenueBooking."""
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("venue_bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # 'PENDING', 'SUCCESS', 'FAILED', 'REFUNDED'
    provider_payment_id = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    booking = relationship("VenueBooking", back_populates="payments")
    user = relationship("User", back_populates="payments")


# ============================================================================
# 17. PAYOUTS (Settlements Transferred to Venue Owner)
# ============================================================================

class Payout(Base):
    """Settlement transferred from Localy to the Venue Owner's PaymentAccount."""
    __tablename__ = "payouts"

    payout_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey("venue_bookings.booking_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    payment_account_id = Column(Integer, ForeignKey("payment_accounts.payment_account_id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    provider_transfer_id = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    booking = relationship("VenueBooking", back_populates="payout")
    payment_account = relationship("PaymentAccount", back_populates="payouts")


# ============================================================================
# 18. COMMUNITIES (Permanent Recurring Circles)
# ============================================================================

class Community(Base):
    """Permanent recurring circles, clubs, and interest hubs."""
    __tablename__ = "communities"

    community_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    members = relationship("CommunityMember", back_populates="community", cascade="all, delete-orphan")
    creator = relationship("User")


# ============================================================================
# 19. COMMUNITY_MEMBERS (Community Membership Junction)
# ============================================================================

class CommunityMember(Base):
    """Community membership with role definitions."""
    __tablename__ = "community_members"

    community_id = Column(Integer, ForeignKey("communities.community_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50), default="MEMBER", nullable=False)  # 'ADMIN', 'MODERATOR', 'MEMBER'
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    community = relationship("Community", back_populates="members")
    user = relationship("User", back_populates="community_memberships")


# ============================================================================
# 20. FEEDBACK (Post-Event Reviews & Ratings)
# ============================================================================

class Feedback(Base):
    """Post-event peer reviews and ratings feeding trust scores and matching."""
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "reviewer_id", name="uq_feedback_event_reviewer"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_feedback_rating_range"),
    )

    # Relationships
    event = relationship("Event", back_populates="feedbacks")
    reviewer = relationship("User", back_populates="given_feedbacks")
