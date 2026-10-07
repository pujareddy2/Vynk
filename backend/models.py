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
# MODULE 1: IDENTITY & PROFILES
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
    event_participations = relationship("EventParticipant", back_populates="user", cascade="all, delete-orphan")
    community_memberships = relationship("CommunityMember", back_populates="user", cascade="all, delete-orphan")
    given_feedbacks = relationship("Feedback", back_populates="reviewer", cascade="all, delete-orphan")


class Profile(Base):
    """User-facing identity, fuzzy location context, and preferences."""
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
# MODULE 2: INTERESTS, SKILLS & AVAILABILITY
# ============================================================================

class Interest(Base):
    """Master taxonomy catalog for hobbies, sports, arts, and activities."""
    __tablename__ = "interests"

    interest_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)

    # Relationships
    user_interests = relationship("UserInterest", back_populates="interest", cascade="all, delete-orphan")
    activity_interests = relationship("ActivityInterest", back_populates="interest", cascade="all, delete-orphan")


class UserInterest(Base):
    """Many-to-Many junction linking Users to Interests."""
    __tablename__ = "user_interests"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    interest_id = Column(Integer, ForeignKey("interests.interest_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="interests")
    interest = relationship("Interest", back_populates="user_interests")


class Skill(Base):
    """Master skills catalog for talents, competencies, and tools."""
    __tablename__ = "skills"

    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)

    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    """Many-to-Many junction linking Users to Skills with proficiency level."""
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True)
    skill_level = Column(String(50), nullable=False)  # 'Beginner', 'Intermediate', 'Advanced'
    is_offering = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")


class UserAvailability(Base):
    """Recurring weekly availability windows for match scheduling."""
    __tablename__ = "user_availability"

    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(String(20), nullable=False)  # 'Monday', 'Saturday', 'Weekend', etc.
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Relationships
    user = relationship("User", back_populates="availability")


# ============================================================================
# MODULE 3: ACTIVITIES, VENUES & SCHEDULED EVENTS
# ============================================================================

class Activity(Base):
    """Activity templates and experience proposals."""
    __tablename__ = "activities"

    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    interests = relationship("ActivityInterest", back_populates="activity", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="activity", cascade="all, delete-orphan")
    creator = relationship("User")


class ActivityInterest(Base):
    """Many-to-Many junction linking Activities to multiple Interests."""
    __tablename__ = "activity_interests"

    activity_id = Column(Integer, ForeignKey("activities.activity_id", ondelete="CASCADE"), primary_key=True)
    interest_id = Column(Integer, ForeignKey("interests.interest_id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    activity = relationship("Activity", back_populates="interests")
    interest = relationship("Interest", back_populates="activity_interests")


class Venue(Base):
    """Reusable physical spaces (courts, cafes, studios, community halls, parks)."""
    __tablename__ = "venues"

    venue_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    address = Column(Text, nullable=False)
    locality = Column(String(100), nullable=False, index=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    events = relationship("Event", back_populates="venue")


class Event(Base):
    """Specific scheduled real-world occurrences with date, time, capacity, and status."""
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey("activities.activity_id", ondelete="RESTRICT"), nullable=False, index=True)
    venue_id = Column(Integer, ForeignKey("venues.venue_id", ondelete="SET NULL"), nullable=True, index=True)
    host_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    price_per_person = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)  # 'DRAFT', 'PUBLISHED', 'FULL', 'COMPLETED', 'CANCELLED'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("max_capacity > 0", name="chk_event_max_capacity"),
    )

    # Relationships
    activity = relationship("Activity", back_populates="events")
    venue = relationship("Venue", back_populates="events")
    host = relationship("User")
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="event", cascade="all, delete-orphan")


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
# MODULE 4: COMMUNITIES
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


class CommunityMember(Base):
    """Community membership junction with role definitions."""
    __tablename__ = "community_members"

    community_id = Column(Integer, ForeignKey("communities.community_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50), default="MEMBER", nullable=False)  # 'ADMIN', 'MODERATOR', 'MEMBER'
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    community = relationship("Community", back_populates="members")
    user = relationship("User", back_populates="community_memberships")


# ============================================================================
# MODULE 5: TRUST & FEEDBACK
# ============================================================================

class Feedback(Base):
    """Post-event peer & experience reviews feeding trust scores and matching."""
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
