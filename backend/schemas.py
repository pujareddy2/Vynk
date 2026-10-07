from datetime import datetime, time
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
