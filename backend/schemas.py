from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Confirmation password")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


class UserResponse(BaseModel):
    user_id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CATALOG SCHEMAS (INTERESTS & SKILLS)
# ============================================================================

class InterestSchema(BaseModel):
    interest_id: int
    name: str
    category: str

    class Config:
        from_attributes = True


class SkillSchema(BaseModel):
    skill_id: int
    name: str
    category: str

    class Config:
        from_attributes = True


# ============================================================================
# USER RELATIONAL SCHEMAS
# ============================================================================

class UserSkillItem(BaseModel):
    skill_id: int
    skill_level: str = Field(default="Beginner", description="'Beginner', 'Intermediate', 'Advanced'")
    is_offering: bool = Field(default=True)


class UserSkillResponse(BaseModel):
    skill_id: int
    name: str
    category: str
    skill_level: str
    is_offering: bool

    class Config:
        from_attributes = True


class UserAvailabilityItem(BaseModel):
    day_of_week: str = Field(..., description="e.g. 'Monday', 'Saturday', 'Weekend'")
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class UserAvailabilityResponse(BaseModel):
    availability_id: int
    day_of_week: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    class Config:
        from_attributes = True


# ============================================================================
# PROFILE & ONBOARDING SCHEMAS
# ============================================================================

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=512)
    approx_locality: Optional[str] = Field(None, max_length=150)
    budget_preference: Optional[str] = Field(None, description="'free', 'low', 'moderate', 'flexible'")


class FullProfileResponse(BaseModel):
    user_id: int
    email: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    approx_locality: Optional[str] = None
    budget_preference: Optional[str] = None
    interests: List[InterestSchema] = []
    skills: List[UserSkillResponse] = []
    availability: List[UserAvailabilityResponse] = []
    created_at: datetime
    updated_at: datetime


class PublicProfileResponse(BaseModel):
    user_id: int
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    approx_locality: Optional[str] = None
    interests: List[InterestSchema] = []
    offered_skills: List[UserSkillResponse] = []


class OnboardingRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    approx_locality: Optional[str] = Field(None, max_length=150)
    budget_preference: Optional[str] = Field(default="flexible")
    interest_ids: List[int] = []
    skills: List[UserSkillItem] = []
    availability: List[UserAvailabilityItem] = []

    class Config:
        from_attributes = True


# ============================================================================
# ACTIVITY SCHEMAS
# ============================================================================

class ActivityCreateRequest(BaseModel):
    interest_id: int = Field(..., description="Target master interest ID")
    title: str = Field(..., min_length=3, max_length=150, description="Activity title")
    description: Optional[str] = Field(None, max_length=1000, description="Activity description")


class ActivityUpdateRequest(BaseModel):
    interest_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)


class ActivityResponse(BaseModel):
    activity_id: int
    interest_id: int
    interest_name: Optional[str] = None
    interest_category: Optional[str] = None
    title: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# VENUE & VENUE SLOT SCHEMAS
# ============================================================================

class VenueActivityItem(BaseModel):
    activity_id: int
    title: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class VenueCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    address: str = Field(..., min_length=3)
    locality: str = Field(..., min_length=2, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    activity_ids: List[int] = Field(default=[], description="Supported activity IDs")


class VenueUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    activity_ids: Optional[List[int]] = None
    status: Optional[str] = None


class VenueResponse(BaseModel):
    venue_id: int
    owner_user_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    address: str
    locality: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_verified: bool
    status: str
    supported_activities: List[VenueActivityItem] = []
    created_at: datetime

    class Config:
        from_attributes = True


class VenueSlotCreateRequest(BaseModel):
    slot_date: date = Field(..., description="Date for the slot (YYYY-MM-DD)")
    start_time: time = Field(..., description="Start time (HH:MM:SS)")
    end_time: time = Field(..., description="End time (HH:MM:SS)")
    price_total: float = Field(..., gt=0, description="Total price for booking the venue slot")
    currency: str = Field(default="INR", max_length=10)


class VenueSlotResponse(BaseModel):
    slot_id: int
    venue_id: int
    venue_name: Optional[str] = None
    slot_date: date
    start_time: time
    end_time: time
    price_total: float
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# VENUE BOOKING & SPLIT PAYMENT SCHEMAS
# ============================================================================

class VenueBookingResponse(BaseModel):
    booking_id: int
    event_id: int
    slot_id: int
    venue_id: int
    venue_name: str
    venue_address: str
    slot_date: date
    start_time: time
    end_time: time
    booked_by: int
    total_amount: float
    currency: str
    status: str
    amount_collected: float = 0.0
    per_person_share: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentAccountCreateRequest(BaseModel):
    provider: str = Field(default="razorpay", description="Payment provider (e.g. 'razorpay', 'stripe')")
    provider_account_id: str = Field(..., min_length=3, description="Merchant / linked account ID")


class PaymentAccountResponse(BaseModel):
    payment_account_id: int
    user_id: int
    provider: str
    provider_account_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreateRequest(BaseModel):
    amount: Optional[float] = Field(None, gt=0, description="Payment amount (defaults to calculated share if omitted)")


class PaymentResponse(BaseModel):
    payment_id: int
    booking_id: int
    user_id: int
    user_name: Optional[str] = None
    amount: float
    currency: str
    status: str
    provider_payment_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PayoutResponse(BaseModel):
    payout_id: int
    booking_id: int
    payment_account_id: int
    amount: float
    currency: str
    status: str
    provider_transfer_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EVENT & PARTICIPATION SCHEMAS
# ============================================================================

class EventParticipantResponse(BaseModel):
    user_id: int
    display_name: str
    avatar_url: Optional[str] = None
    status: str
    payment_status: Optional[str] = None
    paid_amount: Optional[float] = 0.0
    joined_at: datetime

    class Config:
        from_attributes = True


class EventCreateRequest(BaseModel):
    activity_id: int = Field(..., description="Target Activity Template ID")
    title: str = Field(..., min_length=3, max_length=200)
    event_date: date = Field(..., description="Event Date (YYYY-MM-DD)")
    start_time: time = Field(..., description="Start Time (HH:MM:SS)")
    end_time: time = Field(..., description="End Time (HH:MM:SS)")
    max_capacity: int = Field(..., gt=0, description="Max participants allowed")
    slot_id: Optional[int] = Field(None, description="Optional venue slot ID to reserve")


class EventUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_capacity: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None


class EventResponse(BaseModel):
    event_id: int
    activity_id: int
    activity_title: str
    interest_name: Optional[str] = None
    interest_category: Optional[str] = None
    host_id: int
    host_name: str
    title: str
    event_date: date
    start_time: time
    end_time: time
    max_capacity: int
    participant_count: int = 0
    remaining_spots: int = 0
    per_person_cost: Optional[float] = None
    cost_per_person: Optional[float] = None
    locality: Optional[str] = None
    status: str
    venue_booking: Optional[VenueBookingResponse] = None
    participants: List[EventParticipantResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# FEEDBACK & COMMUNITY SCHEMAS
# ============================================================================

class FeedbackCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    feedback_id: int
    event_id: int
    reviewer_id: int
    reviewer_name: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommunityCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)


class CommunityResponse(BaseModel):
    community_id: int
    name: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DETERMINISTIC PEOPLE MATCHING SCHEMAS
# ============================================================================

class PeopleMatchCandidate(BaseModel):
    user_id: int
    display_name: str
    avatar_url: Optional[str] = None
    approx_locality: Optional[str] = None
    match_score: int = Field(..., ge=0, le=100, description="Deterministic compatibility score (0-100)")
    match_breakdown: dict = Field(..., description="Points breakdown: interest, availability, location, skill")
    match_reasons: List[str] = Field(default=[], description="Human-readable reasons for match")
    shared_interests: List[str] = []
    relevant_skills: List[str] = []
    shared_availability: List[str] = []


class PeopleMatchResponse(BaseModel):
    total_candidates: int
    activity_id: Optional[int] = None
    activity_title: Optional[str] = None
    target_interest: Optional[str] = None
    matches: List[PeopleMatchCandidate] = []


# ============================================================================
# AI INTENT UNDERSTANDING SCHEMAS
# ============================================================================

class AIIntentRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Natural language user sentence")


class AIIntentResponse(BaseModel):
    raw_query: str
    intent: str = Field(..., description="E.g. 'find_activity_and_people', 'find_people', 'find_event', 'find_venue', 'create_event', 'general_inquiry'")
    activity: Optional[str] = Field(None, description="Extracted activity or interest name (e.g. 'Badminton', 'Cricket', 'Guitar')")
    category: Optional[str] = Field(None, description="Broad category (e.g. 'Sports', 'Music', 'Technology', 'Creative', 'Learning')")
    day_of_week: Optional[str] = Field(None, description="E.g. 'Saturday', 'Sunday', 'Weekend', 'Today', 'Tomorrow'")
    time_of_day: Optional[str] = Field(None, description="E.g. 'morning', 'afternoon', 'evening', 'night'")
    location: Optional[str] = Field(None, description="E.g. 'nearby', 'Indiranagar', 'Sarjapur Road'")
    skill_level: Optional[str] = Field(None, description="E.g. 'beginner', 'intermediate', 'advanced'")
    budget_preference: Optional[str] = Field(None, description="E.g. 'free', 'low', 'moderate', 'flexible'")
    group_size: Optional[int] = Field(None, description="Mentioned target group size or capacity")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    engine: str = Field(default="openai-gpt-4o-mini", description="Processing engine")


class AIIntentSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Natural language user query")
    limit: int = Field(default=10, ge=1, le=50, description="Max results per section")


class AIIntentSearchResponse(BaseModel):
    query: str
    intent_understood: AIIntentResponse
    summary: str
    people_matches: List[PeopleMatchCandidate] = []
    events: List[EventResponse] = []
    venues: List[VenueResponse] = []



