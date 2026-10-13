from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, EmailStr, Field, model_validator


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    confirm_password: str = Field(..., min_length=6, description="Confirmation password")
    approx_locality: Optional[str] = Field(None, description="Optional live locality detected upon profile registration")

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


class EventVenueBookRequest(BaseModel):
    slot_id: int = Field(..., description="Target VenueSlot ID to reserve for this event")


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


class UserReputationResponse(BaseModel):
    user_id: int
    display_name: str
    average_rating: float = 0.0
    total_reviews: int = 0
    feedback_count: int = 0
    five_star_count: int = 0
    four_star_count: int = 0
    three_star_count: int = 0
    two_star_count: int = 0
    one_star_count: int = 0
    completed_events: int = 0

    class Config:
        from_attributes = True


class CommunityCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    initial_member_ids: Optional[List[int]] = Field(None, description="Optional user IDs to seed as initial members upon creation")


class CommunityResponse(BaseModel):
    community_id: int
    name: str
    description: Optional[str] = None
    created_by: Optional[int] = None
    member_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CommunityHealthResponse(BaseModel):
    community_id: int
    member_count: int
    active_member_count: int
    events_created: int
    completed_events: int
    recent_event_count: int
    average_event_participation: int
    average_feedback_rating: float
    health_score: int
    health_status: str

    class Config:
        from_attributes = True


class MetricTrendItem(BaseModel):
    current: Union[int, float]
    previous: Union[int, float]
    change: Union[int, float]


class MetricsComparison(BaseModel):
    active_members: MetricTrendItem
    events_created: MetricTrendItem
    completed_events: MetricTrendItem
    average_participation: MetricTrendItem
    average_feedback: MetricTrendItem


class CommunityHealthTrendResponse(BaseModel):
    community_id: int
    current_health_score: int
    previous_health_score: int
    score_change: int
    trend: str
    current_status: str
    previous_status: str
    metrics_comparison: MetricsComparison

    class Config:
        from_attributes = True


class CommunityLifecycleInsightResponse(BaseModel):
    community_id: int
    health_score: int
    health_status: str
    trend: str
    score_change: int
    lifecycle_stage: str
    insight: str
    recommended_focus: str

    class Config:
        from_attributes = True


class CommunityActionRecommendationItem(BaseModel):
    priority: str = Field(..., description="HIGH, MEDIUM, or LOW")
    action: str = Field(..., description="Controlled action enum")
    title: str = Field(..., description="Short recommendation headline")
    reason: str = Field(..., description="Grounded factual rationale")
    suggested_next_step: str = Field(..., description="Tactical next step")

    class Config:
        from_attributes = True


class CommunityActionRecommendationsResponse(BaseModel):
    community_id: int
    recommendations: List[CommunityActionRecommendationItem]

    class Config:
        from_attributes = True


# ============================================================================
# COMMUNITY ACTION EXECUTION CONTRACT SCHEMAS (Step 9)
# ============================================================================

class AllowedAction(str, Enum):
    CREATE_EVENT = "CREATE_EVENT"
    RE_ENGAGE_MEMBERS = "RE_ENGAGE_MEMBERS"
    COLLECT_FEEDBACK = "COLLECT_FEEDBACK"
    GROW_MEMBERSHIP = "GROW_MEMBERSHIP"
    MAINTAIN_ACTIVITY = "MAINTAIN_ACTIVITY"
    REACTIVATE_COMMUNITY = "REACTIVATE_COMMUNITY"


class ActionRequest(BaseModel):
    action: str = Field(..., description="Action to execute (must map to AllowedAction)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional action payload")
    reason: Optional[str] = Field(None, description="Optional trigger rationale")

    class Config:
        from_attributes = True


class ActionValidationResult(BaseModel):
    is_valid: bool
    action: Optional[str] = None
    normalized_action: Optional[AllowedAction] = None
    errors: List[str] = Field(default_factory=list)
    sanitized_parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ActionExecutionResult(BaseModel):
    community_id: int
    action: str
    status: str = Field(..., description="'SUCCESS', 'REJECTED', 'PENDING', or 'FAILED'")
    success: bool
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActionAuthorizationResult(BaseModel):
    is_authorized: bool
    status: str = Field(..., description="'AUTHORIZED', 'UNAUTHENTICATED', 'COMMUNITY_NOT_FOUND', 'NOT_A_MEMBER', or 'INVALID_ACTION'")
    status_code: int = Field(..., description="HTTP status code (200, 401, 404, 403, 400)")
    community_id: Optional[int] = None
    requester_id: Optional[int] = None
    action: Optional[str] = None
    message: str

    class Config:
        from_attributes = True
# ============================================================================
# DETERMINISTIC PEOPLE MATCHING SCHEMAS
# ============================================================================

class MatchReputationSummary(BaseModel):
    average_rating: float = 0.0
    total_reviews: int = 0
    completed_events: int = 0


class PeopleMatchCandidate(BaseModel):
    user_id: int
    display_name: str
    avatar_url: Optional[str] = None
    approx_locality: Optional[str] = None
    match_score: int = Field(..., ge=0, le=100, description="Combined final match score (0-100)")
    deterministic_score: Optional[int] = Field(None, description="Deterministic rule-based score (0-100)")
    semantic_similarity: Optional[float] = Field(None, description="AI semantic embedding cosine similarity (0.0 to 1.0)")
    trust_score: Optional[int] = Field(None, ge=0, le=100, description="Reputation and trust score (0-100)")
    reputation: Optional[MatchReputationSummary] = None
    match_breakdown: dict = Field(..., description="Points breakdown: interest, availability, location, skill, semantic")
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


# ============================================================================
# AI GROUP PROPOSAL SCHEMAS
# ============================================================================

class AIGroupProposeRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language group request (e.g. 'Play badminton with 4 people Saturday evening in Indiranagar')")
    target_size: Optional[int] = Field(None, ge=2, le=20, description="Optional override for target cohort size")
    min_required_size: Optional[int] = Field(None, ge=2, le=20, description="Optional override for minimum required accepted members")
    custom_title: Optional[str] = Field(None, max_length=150)


class GroupProposalMemberResponse(BaseModel):
    user_id: int
    display_name: str
    avatar_url: Optional[str] = None
    approx_locality: Optional[str] = None
    status: str = Field(..., description="INVITED, ACCEPTED, DECLINED, AUTO_EXPIRED")
    compatibility_score: Optional[int] = None
    invited_at: datetime
    responded_at: Optional[datetime] = None


class GroupProposalResponse(BaseModel):
    proposal_id: int
    initiator_user_id: int
    initiator_name: str
    activity_id: Optional[int] = None
    activity_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_size: int
    min_required_size: int
    proposed_date: Optional[date] = None
    proposed_start_time: Optional[time] = None
    proposed_end_time: Optional[time] = None
    target_locality: Optional[str] = None
    suggested_venue_id: Optional[int] = None
    suggested_venue_name: Optional[str] = None
    status: str = Field(..., description="PROPOSED, CONFIRMED, EXPIRED, CONVERTED_TO_EVENT, CANCELLED")
    converted_event_id: Optional[int] = None
    expires_at: datetime
    created_at: datetime
    members: List[GroupProposalMemberResponse] = []
    intent_understood: Optional[AIIntentResponse] = None


class GroupProposalRespondRequest(BaseModel):
    response: str = Field(..., description="Response to invitation: 'ACCEPTED' or 'DECLINED'")


# ============================================================================
# AI RECOMMENDATION ENGINE SCHEMAS
# ============================================================================

class RecommendationItem(BaseModel):
    type: str = Field(..., description="'EVENT', 'ACTIVITY', or 'PEOPLE'")
    id: int
    title: str
    score: int = Field(..., ge=0, le=100, description="Recommendation match score (0-100)")
    reasons: List[str] = Field(default=[], description="Explanation of why this entity is recommended")
    locality: Optional[str] = None
    event_id: Optional[int] = None
    activity_id: Optional[int] = None
    user_id: Optional[int] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    remaining_spots: Optional[int] = None
    per_person_cost: Optional[float] = None
    trust_score: Optional[int] = None
    reputation: Optional[MatchReputationSummary] = None

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    total_recommendations: int
    user_locality: Optional[str] = None
    recommendations: List[RecommendationItem] = []


# ============================================================================
# DO SOMETHING NOW SCHEMAS
# ============================================================================

class DoSomethingNowOption(BaseModel):
    type: str = Field(..., description="'EVENT' or 'ACTIVITY'")
    action: str = Field(..., description="'JOIN' (existing event) or 'CREATE' (group/activity proposal) or 'EXPLORE'")
    title: str
    score: int = Field(..., ge=0, le=100, description="Real-time feasibility & match score (0-100)")
    feasible: bool = Field(..., description="Whether this option can be acted upon right now")
    reason: str = Field(..., description="Actionable human-readable explanation")
    reasons: List[str] = Field(default=[], description="Detailed factors breakdown")
    event_id: Optional[int] = None
    activity_id: Optional[int] = None
    interest_id: Optional[int] = None
    interest_name: Optional[str] = None
    locality: Optional[str] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    remaining_spots: Optional[int] = None
    cost_per_person: Optional[float] = None
    available_peers_count: int = 0
    available_venues_count: int = 0
    suggested_slot_id: Optional[int] = None
    suggested_venue_name: Optional[str] = None

    class Config:
        from_attributes = True


class DoSomethingNowResponse(BaseModel):
    target_date: date
    target_time: time
    day_of_week: str
    user_locality: Optional[str] = None
    user_available_now: bool
    total_options: int
    options: List[DoSomethingNowOption] = []


# ============================================================================
# AI EXPERIENCE GENERATOR SCHEMAS
# ============================================================================

class ExperienceAgendaItem(BaseModel):
    time_window: str = Field(..., description="e.g. '18:00 - 18:15' or '00:00 - 00:15'")
    title: str = Field(..., description="Phase title, e.g. 'Warm-up & Rally'")
    description: str = Field(..., description="Activity phase guidance")


class ExperienceGenerateRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language prompt, e.g. 'Play badminton with 4 people Saturday evening in Indiranagar'")
    activity_id: Optional[int] = Field(None, description="Optional explicit Activity ID override")
    venue_id: Optional[int] = Field(None, description="Optional explicit Venue ID override")
    slot_id: Optional[int] = Field(None, description="Optional explicit VenueSlot ID override")
    target_date: Optional[date] = Field(None, description="Optional explicit target date override")
    target_time: Optional[time] = Field(None, description="Optional explicit target start time override")
    target_size: Optional[int] = Field(None, ge=2, le=30, description="Optional cohort size override")
    locality: Optional[str] = Field(None, max_length=150, description="Optional locality override")


class ExperiencePlanResponse(BaseModel):
    experience_title: str = Field(..., description="Catchy headline title for the experience")
    tagline: str = Field(..., description="Engaging thematic tagline")
    activity_id: int
    activity_name: str
    target_date: date
    start_time: time
    end_time: time
    locality: str
    venue_id: Optional[int] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    slot_id: Optional[int] = None
    target_size: int
    per_person_cost: Optional[float] = None
    total_cost: Optional[float] = None
    currency: str = "INR"
    why_this_works: List[str] = Field(default=[], description="Bullet points explaining why this plan is feasible and tailored")
    agenda: List[ExperienceAgendaItem] = Field(default=[], description="Structured timeline/itinerary for the session")
    preparation_checklist: List[str] = Field(default=[], description="Items/gear participants should bring")
    suggested_cohort_user_ids: List[int] = Field(default=[], description="Verified compatible participant candidate IDs")
    suggested_cohort_names: List[str] = Field(default=[], description="Display names of verified candidate participants")
    action_type: str = Field(..., description="'CREATE_PROPOSAL', 'BOOK_EVENT', or 'JOIN_EVENT'")
    action_payload: dict = Field(..., description="Actionable JSON payload ready to trigger downstream Vynk lifecycle endpoints")
    ai_generated: bool = Field(default=True, description="Whether generated by LLM or deterministic fallback engine")


# ============================================================================
# AI DEMAND RADAR SCHEMAS
# ============================================================================

class DemandRadarItem(BaseModel):
    activity: str = Field(..., description="Activity title or master interest name")
    activity_id: Optional[int] = Field(None, description="Matched Activity Template ID if available")
    interest_id: Optional[int] = Field(None, description="Master Interest ID")
    category: Optional[str] = Field(None, description="Interest category, e.g. 'Sports', 'Music', 'Tech'")
    locality: str = Field(..., description="Geographic cluster locality, e.g. 'Indiranagar'")
    preferred_day: str = Field(..., description="Peak day of week for demand, e.g. 'Saturday'")
    preferred_time: str = Field(..., description="Peak time window, e.g. '18:00-20:00'")
    interested_users: int = Field(..., description="Number of local active users with this interest & availability")
    active_events: int = Field(..., description="Number of currently scheduled/open events serving this cluster")
    available_spots: int = Field(..., description="Remaining open spots across active events")
    estimated_unmet_demand: int = Field(..., description="Estimated unmet user demand: max(0, interested_users - available_spots)")
    demand_score: int = Field(..., ge=0, le=100, description="Deterministic demand pressure score (0-100)")
    status: str = Field(..., description="'HIGH_DEMAND', 'MODERATE_DEMAND', 'BALANCED', 'EMERGING_DEMAND', or 'LOW_DEMAND'")
    suggested_action: Optional[str] = Field(None, description="Actionable recommendation for community hosts or venue owners")

    class Config:
        from_attributes = True


class DemandRadarResponse(BaseModel):
    total_clusters: int = Field(..., description="Total demand clusters detected")
    locality_filter: Optional[str] = None
    clusters: List[DemandRadarItem] = Field(default=[], description="Ranked list of detected demand clusters")

    class Config:
        from_attributes = True


# ============================================================================
# AI DEMAND PREDICTION & FEASIBILITY SCHEMAS
# ============================================================================

class DemandPredictionRequest(BaseModel):
    activity: Optional[str] = Field(None, description="Activity title or interest name, e.g. 'Badminton'")
    activity_id: Optional[int] = Field(None, description="Optional Activity ID override")
    interest_id: Optional[int] = Field(None, description="Optional Interest ID override")
    locality: str = Field(..., description="Target locality, e.g. 'Indiranagar'")
    day_of_week: str = Field(..., description="Target day of week, e.g. 'Saturday'")
    preferred_time: Optional[str] = Field("18:00-20:00", description="Time window, e.g. '18:00-20:00'")
    target_capacity: Optional[int] = Field(None, ge=2, le=50, description="Proposed event capacity")
    target_price: Optional[float] = Field(None, ge=0, description="Proposed price per participant in INR")


class DemandPredictionResponse(BaseModel):
    activity: str
    activity_id: Optional[int] = None
    interest_id: Optional[int] = None
    locality: str
    day_of_week: str
    preferred_time: str
    current_demand: str = Field(..., description="'HIGH', 'MODERATE', 'BALANCED', or 'LOW'")
    demand_score: int = Field(..., ge=0, le=100, description="Deterministic demand pressure score")
    interested_users: int = Field(..., description="Local pool of interested & available users")
    active_events: int = Field(..., description="Existing competing events in this locality/window")
    available_spots: int = Field(..., description="Currently open spots in existing events")
    unmet_demand: int = Field(..., description="Unserved local user count")
    expected_participants_min: int = Field(..., description="Conservative lower bound expected attendance")
    expected_participants_max: int = Field(..., description="Optimistic upper bound expected attendance")
    expected_participants_range: str = Field(..., description="Human-readable expected range, e.g. '8-10'")
    attendance_probability: int = Field(..., ge=0, le=100, description="Percentage likelihood of target turnout (e.g. 82)")
    recommended_capacity: int = Field(..., description="AI recommended max participants for optimal fill rate")
    estimated_fill_rate: int = Field(..., ge=0, le=100, description="Projected event fill percentage (e.g. 87)")
    suggested_price_per_person: float = Field(..., description="Fair recommended split cost per participant in INR")
    feasibility: str = Field(..., description="'HIGH', 'MODERATE', 'LOW', or 'CRITICAL_RISK'")
    feasibility_score: int = Field(..., ge=0, le=100, description="Composite feasibility score (0-100)")
    venue_slots_available: int = Field(default=0, description="Bookable venue slots found in this locality")
    factors: List[str] = Field(default=[], description="Bullet-point feasibility rationale")

    class Config:
        from_attributes = True


# ============================================================================
# CROSS-DOMAIN OPPORTUNITY INTELLIGENCE SCHEMAS
# ============================================================================

class OpportunityItem(BaseModel):
    opportunity_type: str = Field(..., description="'CREATE_EVENT', 'VENUE_PARTNERSHIP', or 'COMMUNITY_PROPOSAL'")
    activity: str = Field(..., description="Activity title or master interest name")
    activity_id: Optional[int] = None
    interest_id: Optional[int] = None
    category: Optional[str] = None
    locality: str
    day: str
    time: str
    demand_score: int
    feasibility_score: int
    expected_participants: str
    recommended_capacity: int
    venue_available: bool
    suggested_venue_id: Optional[int] = None
    suggested_venue_name: Optional[str] = None
    suggested_price_per_person: float
    opportunity_score: int
    action: str
    action_payload: Optional[dict] = None
    reasons: List[str] = []

    class Config:
        from_attributes = True


class OpportunitiesResponse(BaseModel):
    total_opportunities: int
    locality_filter: Optional[str] = None
    opportunities: List[OpportunityItem] = []

    class Config:
        from_attributes = True


# ============================================================================
# 17. AI COMMUNITY INTELLIGENCE SCHEMAS
# ============================================================================

class CommunityProposalItem(BaseModel):
    community_type: str = Field(..., description="Theme category, e.g. 'SPORTS', 'OUTDOORS', 'ARTS'")
    theme: str = Field(..., description="Proposed community title, e.g. 'Indiranagar Weekend Badminton'")
    activity: str = Field(..., description="Core activity name, e.g. 'Badminton'")
    activity_id: Optional[int] = None
    interest_id: Optional[int] = None
    locality: str = Field(..., description="Geographical focal point, e.g. 'Indiranagar'")
    member_candidates: int = Field(..., description="Number of compatible peers detected in pattern")
    candidate_user_ids: List[int] = Field(default=[], description="User IDs of matched cohort peers")
    recurring_pattern: str = Field(..., description="Weekly schedule alignment, e.g. 'Saturday evenings'")
    day_of_week: Optional[str] = None
    time_window: Optional[str] = None
    compatibility_score: int = Field(..., description="Average cohort compatibility score (0-100)")
    community_opportunity_score: int = Field(..., description="Composite community viability score (0-100)")
    suggested_action: str = Field(default="CREATE_COMMUNITY", description="'CREATE_COMMUNITY' or 'JOIN_COMMUNITY'")
    action_payload: Optional[dict] = Field(None, description="Pre-filled payload to pass to POST /communities")
    reasons: List[str] = []
    existing_community_id: Optional[int] = None

    class Config:
        from_attributes = True


class CommunityIntelligenceResponse(BaseModel):
    total_proposals: int
    locality_filter: Optional[str] = None
    proposals: List[CommunityProposalItem] = []

    class Config:
        from_attributes = True


# ============================================================================
# 18. NOTIFICATION INBOX SCHEMAS (Step 10.1 Domain Contracts)
# ============================================================================

class NotificationType(str, Enum):
    RE_ENGAGEMENT = "RE_ENGAGEMENT"
    FEEDBACK_REQUEST = "FEEDBACK_REQUEST"
    COMMUNITY_INVITATION = "COMMUNITY_INVITATION"
    ACTIVITY_MAINTENANCE = "ACTIVITY_MAINTENANCE"
    COMMUNITY_REACTIVATION = "COMMUNITY_REACTIVATION"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    DISMISSED = "DISMISSED"
    ACCEPTED = "ACCEPTED"


ACTIONABLE_NOTIFICATION_TYPES = {
    NotificationType.COMMUNITY_INVITATION.value,
    NotificationType.ACTIVITY_MAINTENANCE.value,
    NotificationType.COMMUNITY_REACTIVATION.value,
}

INFORMATIONAL_NOTIFICATION_TYPES = {
    NotificationType.RE_ENGAGEMENT.value,
    NotificationType.FEEDBACK_REQUEST.value,
    NotificationType.SYSTEM_ALERT.value,
}


def validate_notification_status_transition(
    current_status: str,
    new_status: str,
    notification_type: str,
) -> Tuple[bool, Optional[str]]:
    """
    Step 10.1 Domain validation for notification lifecycle state transitions.
    Rules:
    1. READ, DISMISSED, ACCEPTED cannot transition back to UNREAD (READ -> UNREAD is prohibited).
    2. Terminal states (DISMISSED, ACCEPTED) cannot transition to any other status.
    3. ACCEPTED is strictly reserved for ACTIONABLE_NOTIFICATION_TYPES
       (COMMUNITY_INVITATION, ACTIVITY_MAINTENANCE, COMMUNITY_REACTIVATION).
       INFORMATIONAL types (RE_ENGAGEMENT, FEEDBACK_REQUEST, SYSTEM_ALERT) cannot be ACCEPTED.
    4. UNREAD can transition to READ, DISMISSED, or ACCEPTED (if actionable).
    5. READ can transition to DISMISSED or ACCEPTED (if actionable).
    """
    current_s = str(current_status.value if hasattr(current_status, "value") else current_status).strip().upper()
    if "." in current_s:
        current_s = current_s.split(".")[-1]

    new_s = str(new_status.value if hasattr(new_status, "value") else new_status).strip().upper()
    if "." in new_s:
        new_s = new_s.split(".")[-1]

    notif_type = str(notification_type.value if hasattr(notification_type, "value") else notification_type).strip().upper()
    if "." in notif_type:
        notif_type = notif_type.split(".")[-1]

    if current_s in ["DISMISSED", "ACCEPTED"]:
        return False, f"Notification is already in terminal state '{current_s}'."

    if new_s == current_s:
        return True, None

    if new_s == "UNREAD":
        return False, "Cannot transition read or resolved notification back to UNREAD."

    if new_s == "ACCEPTED" and notif_type not in ACTIONABLE_NOTIFICATION_TYPES:
        return False, f"Notification type '{notif_type}' is informational and cannot be accepted."

    if current_s == "UNREAD" and new_s in ["READ", "DISMISSED", "ACCEPTED"]:
        return True, None

    if current_s == "READ" and new_s in ["DISMISSED", "ACCEPTED"]:
        return True, None

    return False, f"Invalid transition from '{current_s}' to '{new_s}'."


class NotificationCreate(BaseModel):
    recipient_user_id: int
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    payload: Optional[Dict[str, Any]] = None
    source_action: Optional[str] = None
    related_community_id: Optional[int] = None
    related_event_id: Optional[int] = None


class NotificationResponse(BaseModel):
    notification_id: int
    recipient_user_id: int
    notification_type: str
    title: str
    message: str
    payload: Optional[Dict[str, Any]] = None
    source_action: Optional[str] = None
    related_community_id: Optional[int] = None
    related_event_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime
    is_stale: bool = False

    class Config:
        from_attributes = True


class NotificationSummary(BaseModel):
    total_count: int
    unread_count: int


class NotificationStatusUpdate(BaseModel):
    status: NotificationStatus


class NotificationInboxResponse(BaseModel):
    notifications: List[NotificationResponse] = []
    total: int
    unread_count: int
    limit: int
    offset: int

    class Config:
        from_attributes = True


# ============================================================================
# 19. ACTION-AWARE NOTIFICATION PAYLOAD CONTRACTS (Step 10.5)
# ============================================================================

class BaseNotificationPayload(BaseModel):
    actionable: bool = False
    context: Optional[str] = None
    target_action: Optional[str] = None
    target_endpoint: Optional[str] = None


class CommunityInvitationPayload(BaseNotificationPayload):
    actionable: bool = True
    community_id: int
    community_name: str
    inviter_user_id: Optional[int] = None
    affinity_reasons: List[str] = []
    target_action: str = "JOIN_COMMUNITY"
    target_endpoint: str = ""

    @model_validator(mode="after")
    def set_endpoint(self):
        if not self.target_endpoint:
            self.target_endpoint = f"/communities/{self.community_id}/join"
        return self


class ActivityMaintenancePayload(BaseNotificationPayload):
    actionable: bool = True
    community_id: int
    community_name: str
    cadence: str = "WEEKLY"
    suggested_activity_id: Optional[int] = None
    suggested_activity_title: Optional[str] = None
    target_action: str = "CREATE_EVENT"
    target_endpoint: str = ""
    action_plan: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def set_endpoint(self):
        if not self.target_endpoint:
            self.target_endpoint = f"/communities/{self.community_id}/actions/execute"
        return self


class CommunityReactivationPayload(BaseNotificationPayload):
    actionable: bool = True
    community_id: int
    community_name: str
    reactivation_date: str
    suggested_activity_id: Optional[int] = None
    suggested_activity_title: Optional[str] = None
    target_action: str = "CREATE_EVENT"
    target_endpoint: str = ""
    action_plan: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def set_endpoint(self):
        if not self.target_endpoint:
            self.target_endpoint = f"/communities/{self.community_id}/actions/execute"
        return self


class FeedbackRequestPayload(BaseNotificationPayload):
    actionable: bool = False
    event_id: int
    event_title: str
    community_id: Optional[int] = None
    target_endpoint: str = "/feedback"


class ReEngagementPayload(BaseNotificationPayload):
    actionable: bool = False
    community_id: int
    community_name: str
    target_inactive_days: int = 14
    target_endpoint: str = ""

    @model_validator(mode="after")
    def set_endpoint(self):
        if not self.target_endpoint:
            self.target_endpoint = f"/communities/{self.community_id}"
        return self


class SystemAlertPayload(BaseNotificationPayload):
    actionable: bool = False
    alert_code: Optional[str] = None


def normalize_action_aware_payload(
    notification_type: str,
    raw_payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Step 10.5: Normalizes and validates action-aware notification payloads.
    Guarantees:
    - Actionable notifications (COMMUNITY_INVITATION, ACTIVITY_MAINTENANCE, COMMUNITY_REACTIVATION)
      are tagged with actionable=True, verified required metadata, and target_action/endpoint.
    - Informational notifications (FEEDBACK_REQUEST, RE_ENGAGEMENT, SYSTEM_ALERT)
      are tagged with actionable=False.
    """
    notif_type = str(notification_type.value if hasattr(notification_type, "value") else notification_type).strip().upper()
    if "." in notif_type:
        notif_type = notif_type.split(".")[-1]
    data = dict(raw_payload) if raw_payload else {}

    if notif_type == NotificationType.COMMUNITY_INVITATION.value:
        data["actionable"] = True
        data.setdefault("target_action", "JOIN_COMMUNITY")
        comm_id = data.get("community_id")
        if comm_id is not None:
            data.setdefault("target_endpoint", f"/communities/{comm_id}/join")
        else:
            data.setdefault("target_endpoint", "/communities")

    elif notif_type in [NotificationType.ACTIVITY_MAINTENANCE.value, NotificationType.COMMUNITY_REACTIVATION.value]:
        data["actionable"] = True
        data.setdefault("target_action", "CREATE_EVENT")
        comm_id = data.get("community_id")
        if comm_id is not None:
            data.setdefault("target_endpoint", f"/communities/{comm_id}/actions/execute")
        else:
            data.setdefault("target_endpoint", "/events")

    elif notif_type == NotificationType.FEEDBACK_REQUEST.value:
        data["actionable"] = False
        data.setdefault("target_endpoint", "/feedback")

    elif notif_type == NotificationType.RE_ENGAGEMENT.value:
        data["actionable"] = False
        comm_id = data.get("community_id")
        if comm_id is not None:
            data.setdefault("target_endpoint", f"/communities/{comm_id}")

    else:
        # Default SYSTEM_ALERT or generic
        data["actionable"] = False

    return data


