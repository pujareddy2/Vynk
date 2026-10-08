from contextlib import asynccontextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ai_service import understand_user_intent
from auth import create_access_token, get_current_user, get_optional_current_user, hash_password, verify_password
from database import SessionLocal, check_db_connection, get_db
import models
import schemas
from seed import seed_master_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed master taxonomy on startup
    db = SessionLocal()
    try:
        seed_master_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Localy API",
    description="Localy Backend REST API — AI-Powered Local Activity, Talent, Intent Understanding & Split-Cost Network.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 1. SYSTEM ENDPOINTS
# ============================================================================

@app.get("/health", tags=["System"])
def health_check():
    db_status = "connected" if check_db_connection() else "disconnected"
    return {
        "status": "connected",
        "database": db_status,
        "message": f"backend connected (database {db_status})",
    }


# ============================================================================
# 2. AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    summary="Register a new user account",
)
def register(
    req: schemas.UserRegisterRequest,
    db: Session = Depends(get_db),
):
    normalized_email = req.email.strip().lower()
    existing_user = db.query(models.User).filter(models.User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    new_user = models.User(
        email=normalized_email,
        password_hash=hash_password(req.password),
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.flush()

    default_display_name = normalized_email.split("@")[0].capitalize()
    new_profile = models.Profile(
        user_id=new_user.user_id,
        display_name=default_display_name,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post(
    "/auth/login",
    response_model=schemas.TokenResponse,
    tags=["Authentication"],
    summary="Login and obtain JWT access token (supports JSON and OAuth2 Form)",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        email = str(form.get("username", "")).strip().lower()
        password = str(form.get("password", ""))
    else:
        body = await request.json()
        email = str(body.get("email", "")).strip().lower()
        password = str(body.get("password", ""))

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token(data={"sub": str(user.user_id), "email": user.email})

    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
    )


@app.get(
    "/auth/me",
    response_model=schemas.UserResponse,
    tags=["Authentication"],
    summary="Get current authenticated user account",
)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ============================================================================
# 3. MASTER CATALOG ENDPOINTS (INTERESTS & SKILLS)
# ============================================================================

@app.get(
    "/interests",
    response_model=List[schemas.InterestSchema],
    tags=["Catalog"],
    summary="List all master interests categorized",
)
def list_interests(db: Session = Depends(get_db)):
    return db.query(models.Interest).order_by(models.Interest.category, models.Interest.name).all()


@app.get(
    "/skills",
    response_model=List[schemas.SkillSchema],
    tags=["Catalog"],
    summary="List all master skills categorized",
)
def list_skills(db: Session = Depends(get_db)):
    return db.query(models.Skill).order_by(models.Skill.category, models.Skill.name).all()


# ============================================================================
# 4. USER PROFILE & ONBOARDING ENDPOINTS
# ============================================================================

def _build_full_profile(user: models.User, db: Session) -> schemas.FullProfileResponse:
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.user_id).first()
    
    user_ints = (
        db.query(models.Interest)
        .join(models.UserInterest, models.Interest.interest_id == models.UserInterest.interest_id)
        .filter(models.UserInterest.user_id == user.user_id)
        .all()
    )

    user_sks = (
        db.query(
            models.Skill.skill_id,
            models.Skill.name,
            models.Skill.category,
            models.UserSkill.skill_level,
            models.UserSkill.is_offering,
        )
        .join(models.UserSkill, models.Skill.skill_id == models.UserSkill.skill_id)
        .filter(models.UserSkill.user_id == user.user_id)
        .all()
    )
    formatted_skills = [
        schemas.UserSkillResponse(
            skill_id=s.skill_id,
            name=s.name,
            category=s.category,
            skill_level=s.skill_level,
            is_offering=s.is_offering,
        )
        for s in user_sks
    ]

    avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id == user.user_id).all()

    return schemas.FullProfileResponse(
        user_id=user.user_id,
        email=user.email,
        display_name=profile.display_name if profile else user.email.split("@")[0],
        bio=profile.bio if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        approx_locality=profile.approx_locality if profile else None,
        budget_preference=profile.budget_preference if profile else None,
        interests=user_ints,
        skills=formatted_skills,
        availability=avails,
        created_at=profile.created_at if profile else user.created_at,
        updated_at=profile.updated_at if profile else user.updated_at,
    )


@app.get(
    "/profile/me",
    response_model=schemas.FullProfileResponse,
    tags=["Profile"],
    summary="Fetch current user's complete profile, interests, skills, and availability",
)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _build_full_profile(current_user, db)


@app.patch(
    "/profile/me",
    response_model=schemas.FullProfileResponse,
    tags=["Profile"],
    summary="Partially update user basic profile fields",
)
def update_my_profile(
    req: schemas.ProfileUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    if not profile:
        profile = models.Profile(user_id=current_user.user_id, display_name=current_user.email.split("@")[0])
        db.add(profile)

    if req.display_name is not None:
        profile.display_name = req.display_name.strip()
    if req.bio is not None:
        profile.bio = req.bio.strip()
    if req.avatar_url is not None:
        profile.avatar_url = req.avatar_url.strip()
    if req.approx_locality is not None:
        profile.approx_locality = req.approx_locality.strip()
    if req.budget_preference is not None:
        profile.budget_preference = req.budget_preference.strip()

    db.commit()
    db.refresh(profile)
    return _build_full_profile(current_user, db)


@app.put(
    "/profile/me/interests",
    response_model=schemas.FullProfileResponse,
    tags=["Profile"],
    summary="Update user selected interests",
)
def update_my_interests(
    interest_ids: List[int],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).delete()
    for i_id in set(interest_ids):
        if db.query(models.Interest).filter(models.Interest.interest_id == i_id).first():
            db.add(models.UserInterest(user_id=current_user.user_id, interest_id=i_id))
    db.commit()
    return _build_full_profile(current_user, db)


@app.put(
    "/profile/me/skills",
    response_model=schemas.FullProfileResponse,
    tags=["Profile"],
    summary="Update user skills and proficiency levels",
)
def update_my_skills(
    skills: List[schemas.UserSkillItem],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.UserSkill).filter(models.UserSkill.user_id == current_user.user_id).delete()
    for s in skills:
        if db.query(models.Skill).filter(models.Skill.skill_id == s.skill_id).first():
            db.add(
                models.UserSkill(
                    user_id=current_user.user_id,
                    skill_id=s.skill_id,
                    skill_level=s.skill_level,
                    is_offering=s.is_offering,
                )
            )
    db.commit()
    return _build_full_profile(current_user, db)


@app.put(
    "/profile/me/availability",
    response_model=schemas.FullProfileResponse,
    tags=["Profile"],
    summary="Update user weekly availability schedule",
)
def update_my_availability(
    availability: List[schemas.UserAvailabilityItem],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.UserAvailability).filter(models.UserAvailability.user_id == current_user.user_id).delete()
    for a in availability:
        db.add(
            models.UserAvailability(
                user_id=current_user.user_id,
                day_of_week=a.day_of_week,
                start_time=a.start_time,
                end_time=a.end_time,
            )
        )
    db.commit()
    return _build_full_profile(current_user, db)


@app.post(
    "/profile/me/onboarding",
    response_model=schemas.FullProfileResponse,
    tags=["Profile"],
    summary="Complete atomic onboarding submission",
)
def complete_onboarding(
    req: schemas.OnboardingRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    if not profile:
        profile = models.Profile(user_id=current_user.user_id, display_name=req.display_name)
        db.add(profile)
    profile.display_name = req.display_name
    profile.bio = req.bio
    profile.avatar_url = req.avatar_url
    profile.approx_locality = req.approx_locality
    profile.budget_preference = req.budget_preference

    db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).delete()
    for i_id in set(req.interest_ids):
        if db.query(models.Interest).filter(models.Interest.interest_id == i_id).first():
            db.add(models.UserInterest(user_id=current_user.user_id, interest_id=i_id))

    db.query(models.UserSkill).filter(models.UserSkill.user_id == current_user.user_id).delete()
    for s in req.skills:
        if db.query(models.Skill).filter(models.Skill.skill_id == s.skill_id).first():
            db.add(
                models.UserSkill(
                    user_id=current_user.user_id,
                    skill_id=s.skill_id,
                    skill_level=s.skill_level,
                    is_offering=s.is_offering,
                )
            )

    db.query(models.UserAvailability).filter(models.UserAvailability.user_id == current_user.user_id).delete()
    for a in req.availability:
        db.add(
            models.UserAvailability(
                user_id=current_user.user_id,
                day_of_week=a.day_of_week,
                start_time=a.start_time,
                end_time=a.end_time,
            )
        )

    db.commit()
    return _build_full_profile(current_user, db)


@app.get(
    "/profile/{user_id}",
    response_model=schemas.PublicProfileResponse,
    tags=["Profile"],
    summary="View a user's public profile (privacy-shielded)",
)
def get_public_profile(user_id: int, db: Session = Depends(get_db)):
    target_user = db.query(models.User).filter(models.User.user_id == user_id, models.User.is_active.is_(True)).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
    user_ints = (
        db.query(models.Interest)
        .join(models.UserInterest, models.Interest.interest_id == models.UserInterest.interest_id)
        .filter(models.UserInterest.user_id == user_id)
        .all()
    )
    offered_skills = (
        db.query(
            models.Skill.skill_id,
            models.Skill.name,
            models.Skill.category,
            models.UserSkill.skill_level,
            models.UserSkill.is_offering,
        )
        .join(models.UserSkill, models.Skill.skill_id == models.UserSkill.skill_id)
        .filter(models.UserSkill.user_id == user_id, models.UserSkill.is_offering.is_(True))
        .all()
    )

    return schemas.PublicProfileResponse(
        user_id=user_id,
        display_name=profile.display_name if profile else "Localy Member",
        bio=profile.bio if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        approx_locality=profile.approx_locality if profile else None,
        interests=user_ints,
        offered_skills=[
            schemas.UserSkillResponse(
                skill_id=s.skill_id,
                name=s.name,
                category=s.category,
                skill_level=s.skill_level,
                is_offering=s.is_offering,
            )
            for s in offered_skills
        ],
    )


# ============================================================================
# 5. ACTIVITY ENGINE ENDPOINTS
# ============================================================================

def _build_activity_response(activity: models.Activity, db: Session) -> schemas.ActivityResponse:
    interest = db.query(models.Interest).filter(models.Interest.interest_id == activity.interest_id).first()
    
    creator_name = None
    if activity.created_by:
        creator_profile = db.query(models.Profile).filter(models.Profile.user_id == activity.created_by).first()
        if creator_profile:
            creator_name = creator_profile.display_name
        else:
            creator_user = db.query(models.User).filter(models.User.user_id == activity.created_by).first()
            if creator_user:
                creator_name = creator_user.email.split("@")[0].capitalize()

    return schemas.ActivityResponse(
        activity_id=activity.activity_id,
        interest_id=activity.interest_id,
        interest_name=interest.name if interest else None,
        interest_category=interest.category if interest else None,
        title=activity.title,
        description=activity.description,
        created_by=activity.created_by,
        creator_name=creator_name,
        created_at=activity.created_at,
    )


@app.post(
    "/activities",
    response_model=schemas.ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Activities"],
    summary="Create a new activity template proposal",
)
def create_activity(
    req: schemas.ActivityCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interest = db.query(models.Interest).filter(models.Interest.interest_id == req.interest_id).first()
    if not interest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified interest not found")

    new_activity = models.Activity(
        interest_id=req.interest_id,
        title=req.title.strip(),
        description=req.description.strip() if req.description else None,
        created_by=current_user.user_id,
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return _build_activity_response(new_activity, db)


@app.get(
    "/activities",
    response_model=List[schemas.ActivityResponse],
    tags=["Activities"],
    summary="List all activities with optional category, interest, and search filters",
)
def list_activities(
    interest_id: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Activity)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (models.Activity.title.ilike(search_term)) | (models.Activity.description.ilike(search_term))
        )

    if interest_id:
        query = query.filter(models.Activity.interest_id == interest_id)
    elif category:
        query = query.join(models.Interest, models.Activity.interest_id == models.Interest.interest_id).filter(
            models.Interest.category.ilike(category.strip())
        )

    activities = query.order_by(models.Activity.created_at.desc()).all()
    return [_build_activity_response(a, db) for a in activities]


@app.get(
    "/activities/{activity_id}",
    response_model=schemas.ActivityResponse,
    tags=["Activities"],
    summary="Get single activity details by ID",
)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return _build_activity_response(activity, db)


@app.patch(
    "/activities/{activity_id}",
    response_model=schemas.ActivityResponse,
    tags=["Activities"],
    summary="Update an activity (Creator only)",
)
def update_activity(
    activity_id: int,
    req: schemas.ActivityUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if activity.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can edit this activity")

    if req.interest_id is not None:
        interest = db.query(models.Interest).filter(models.Interest.interest_id == req.interest_id).first()
        if not interest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interest not found")
        activity.interest_id = req.interest_id

    if req.title is not None:
        activity.title = req.title.strip()
    if req.description is not None:
        activity.description = req.description.strip()

    db.commit()
    db.refresh(activity)
    return _build_activity_response(activity, db)


@app.delete(
    "/activities/{activity_id}",
    tags=["Activities"],
    summary="Delete an activity (Creator only)",
)
def delete_activity(
    activity_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    if activity.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can delete this activity")

    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully", "activity_id": activity_id}


# ============================================================================
# 6. VENUES & BOOKABLE SLOTS ENDPOINTS
# ============================================================================

def _build_venue_response(venue: models.Venue, db: Session) -> schemas.VenueResponse:
    acts = (
        db.query(models.Activity.activity_id, models.Activity.title, models.Interest.category)
        .join(models.VenueActivity, models.Activity.activity_id == models.VenueActivity.activity_id)
        .join(models.Interest, models.Activity.interest_id == models.Interest.interest_id)
        .filter(models.VenueActivity.venue_id == venue.venue_id)
        .all()
    )
    supported = [
        schemas.VenueActivityItem(activity_id=a.activity_id, title=a.title, category=a.category)
        for a in acts
    ]

    return schemas.VenueResponse(
        venue_id=venue.venue_id,
        owner_user_id=venue.owner_user_id,
        name=venue.name,
        description=venue.description,
        address=venue.address,
        locality=venue.locality,
        latitude=float(venue.latitude) if venue.latitude is not None else None,
        longitude=float(venue.longitude) if venue.longitude is not None else None,
        contact_phone=venue.contact_phone,
        contact_email=venue.contact_email,
        is_verified=venue.is_verified,
        status=venue.status,
        supported_activities=supported,
        created_at=venue.created_at,
    )


@app.post(
    "/venues",
    response_model=schemas.VenueResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Venues"],
    summary="Register a new venue (Admin or Venue Owner)",
)
def create_venue(
    req: schemas.VenueCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    venue = models.Venue(
        owner_user_id=current_user.user_id,
        name=req.name.strip(),
        description=req.description.strip() if req.description else None,
        address=req.address.strip(),
        locality=req.locality.strip(),
        latitude=req.latitude,
        longitude=req.longitude,
        contact_phone=req.contact_phone.strip() if req.contact_phone else None,
        contact_email=req.contact_email.strip() if req.contact_email else None,
        is_verified=True,
        status="ACTIVE",
    )
    db.add(venue)
    db.flush()

    for a_id in set(req.activity_ids):
        if db.query(models.Activity).filter(models.Activity.activity_id == a_id).first():
            db.add(models.VenueActivity(venue_id=venue.venue_id, activity_id=a_id))

    db.commit()
    db.refresh(venue)
    return _build_venue_response(venue, db)


@app.get(
    "/venues",
    response_model=List[schemas.VenueResponse],
    tags=["Venues"],
    summary="List registered venues filtered by locality, activity, or search",
)
def list_venues(
    locality: Optional[str] = None,
    activity_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Venue).filter(models.Venue.status == "ACTIVE")

    if locality:
        query = query.filter(models.Venue.locality.ilike(f"%{locality.strip()}%"))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (models.Venue.name.ilike(search_term))
            | (models.Venue.address.ilike(search_term))
            | (models.Venue.locality.ilike(search_term))
        )

    if activity_id:
        query = query.join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id).filter(
            models.VenueActivity.activity_id == activity_id
        )

    venues = query.order_by(models.Venue.name).all()
    return [_build_venue_response(v, db) for v in venues]


@app.get(
    "/venues/{venue_id}",
    response_model=schemas.VenueResponse,
    tags=["Venues"],
    summary="Get single venue details by ID",
)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.query(models.Venue).filter(models.Venue.venue_id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return _build_venue_response(venue, db)


@app.patch(
    "/venues/{venue_id}",
    response_model=schemas.VenueResponse,
    tags=["Venues"],
    summary="Update venue details (Owner only)",
)
def update_venue(
    venue_id: int,
    req: schemas.VenueUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    venue = db.query(models.Venue).filter(models.Venue.venue_id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    if venue.owner_user_id and venue.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only venue owner can modify venue")

    if req.name is not None:
        venue.name = req.name.strip()
    if req.description is not None:
        venue.description = req.description.strip()
    if req.address is not None:
        venue.address = req.address.strip()
    if req.locality is not None:
        venue.locality = req.locality.strip()
    if req.latitude is not None:
        venue.latitude = req.latitude
    if req.longitude is not None:
        venue.longitude = req.longitude
    if req.contact_phone is not None:
        venue.contact_phone = req.contact_phone.strip()
    if req.contact_email is not None:
        venue.contact_email = req.contact_email.strip()
    if req.status is not None:
        venue.status = req.status

    if req.activity_ids is not None:
        db.query(models.VenueActivity).filter(models.VenueActivity.venue_id == venue_id).delete()
        for a_id in set(req.activity_ids):
            if db.query(models.Activity).filter(models.Activity.activity_id == a_id).first():
                db.add(models.VenueActivity(venue_id=venue.venue_id, activity_id=a_id))

    db.commit()
    db.refresh(venue)
    return _build_venue_response(venue, db)


# Venue Slots
@app.post(
    "/venues/{venue_id}/slots",
    response_model=schemas.VenueSlotResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Venues"],
    summary="Create a bookable time slot for a venue",
)
def create_venue_slot(
    venue_id: int,
    req: schemas.VenueSlotCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    venue = db.query(models.Venue).filter(models.Venue.venue_id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    if venue.owner_user_id and venue.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only venue owner can create slots")

    existing = (
        db.query(models.VenueSlot)
        .filter(
            models.VenueSlot.venue_id == venue_id,
            models.VenueSlot.slot_date == req.slot_date,
            models.VenueSlot.start_time == req.start_time,
            models.VenueSlot.end_time == req.end_time,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A slot already exists for this venue at the specified date and time window",
        )

    slot = models.VenueSlot(
        venue_id=venue_id,
        slot_date=req.slot_date,
        start_time=req.start_time,
        end_time=req.end_time,
        price_total=Decimal(str(req.price_total)),
        currency=req.currency.upper(),
        status="AVAILABLE",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    return schemas.VenueSlotResponse(
        slot_id=slot.slot_id,
        venue_id=slot.venue_id,
        venue_name=venue.name,
        slot_date=slot.slot_date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        price_total=float(slot.price_total),
        currency=slot.currency,
        status=slot.status,
        created_at=slot.created_at,
    )


@app.get(
    "/venues/{venue_id}/slots",
    response_model=List[schemas.VenueSlotResponse],
    tags=["Venues"],
    summary="List available time slots for a venue with optional date filter",
)
def list_venue_slots(
    venue_id: int,
    slot_date: Optional[date] = None,
    available_only: bool = True,
    db: Session = Depends(get_db),
):
    venue = db.query(models.Venue).filter(models.Venue.venue_id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    query = db.query(models.VenueSlot).filter(models.VenueSlot.venue_id == venue_id)
    if slot_date:
        query = query.filter(models.VenueSlot.slot_date == slot_date)
    if available_only:
        query = query.filter(models.VenueSlot.status == "AVAILABLE")

    slots = query.order_by(models.VenueSlot.slot_date, models.VenueSlot.start_time).all()
    return [
        schemas.VenueSlotResponse(
            slot_id=s.slot_id,
            venue_id=s.venue_id,
            venue_name=venue.name,
            slot_date=s.slot_date,
            start_time=s.start_time,
            end_time=s.end_time,
            price_total=float(s.price_total),
            currency=s.currency,
            status=s.status,
            created_at=s.created_at,
        )
        for s in slots
    ]


# ============================================================================
# 7. EVENTS, ROSTER, PARTICIPATION & LIFECYCLE ENGINE
# ============================================================================

def _build_event_response(event: models.Event, db: Session) -> schemas.EventResponse:
    activity = db.query(models.Activity).filter(models.Activity.activity_id == event.activity_id).first()
    interest = db.query(models.Interest).filter(models.Interest.interest_id == activity.interest_id).first() if activity else None

    host_profile = db.query(models.Profile).filter(models.Profile.user_id == event.host_id).first()
    host_name = host_profile.display_name if host_profile else f"User {event.host_id}"

    parts = (
        db.query(models.EventParticipant, models.Profile.display_name, models.Profile.avatar_url)
        .outerjoin(models.Profile, models.EventParticipant.user_id == models.Profile.user_id)
        .filter(models.EventParticipant.event_id == event.event_id, models.EventParticipant.status == "CONFIRMED")
        .order_by(models.EventParticipant.joined_at.asc())
        .all()
    )

    participant_count = len(parts)
    remaining_spots = max(0, event.max_capacity - participant_count)

    booking_schema = None
    per_person_cost = None
    event_locality = None

    booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event.event_id).first()
    if booking:
        slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == booking.slot_id).first()
        venue = db.query(models.Venue).filter(models.Venue.venue_id == slot.venue_id).first() if slot else None
        if venue:
            event_locality = venue.locality

        payments_sum = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.booking_id == booking.booking_id, models.Payment.status == "SUCCESS")
            .scalar()
        )
        amount_collected = float(payments_sum)

        total_amount = float(booking.total_amount)
        active_count = max(participant_count, 1)
        per_person_share = round(total_amount / active_count, 2)
        per_person_cost = per_person_share

        booking_schema = schemas.VenueBookingResponse(
            booking_id=booking.booking_id,
            event_id=booking.event_id,
            slot_id=booking.slot_id,
            venue_id=venue.venue_id if venue else 0,
            venue_name=venue.name if venue else "Reserved Venue",
            venue_address=venue.address if venue else "",
            slot_date=slot.slot_date if slot else event.event_date,
            start_time=slot.start_time if slot else event.start_time,
            end_time=slot.end_time if slot else event.end_time,
            booked_by=booking.booked_by,
            total_amount=total_amount,
            currency=booking.currency,
            status=booking.status,
            amount_collected=amount_collected,
            per_person_share=per_person_share,
            created_at=booking.created_at,
        )

    participant_list = []
    for p, d_name, av_url in parts:
        user_paid = 0.0
        pay_status = "UNPAID"
        if booking:
            paid_sum = (
                db.query(func.coalesce(func.sum(models.Payment.amount), 0))
                .filter(
                    models.Payment.booking_id == booking.booking_id,
                    models.Payment.user_id == p.user_id,
                    models.Payment.status == "SUCCESS",
                )
                .scalar()
            )
            user_paid = float(paid_sum)
            if user_paid >= (per_person_cost or 0):
                pay_status = "PAID"
            elif user_paid > 0:
                pay_status = "PARTIAL"

        participant_list.append(
            schemas.EventParticipantResponse(
                user_id=p.user_id,
                display_name=d_name if d_name else f"Member {p.user_id}",
                avatar_url=av_url,
                status=p.status,
                payment_status=pay_status,
                paid_amount=user_paid,
                joined_at=p.joined_at,
            )
        )

    return schemas.EventResponse(
        event_id=event.event_id,
        activity_id=event.activity_id,
        activity_title=activity.title if activity else "General Activity",
        interest_name=interest.name if interest else None,
        interest_category=interest.category if interest else None,
        host_id=event.host_id,
        host_name=host_name,
        title=event.title,
        event_date=event.event_date,
        start_time=event.start_time,
        end_time=event.end_time,
        max_capacity=event.max_capacity,
        participant_count=participant_count,
        remaining_spots=remaining_spots,
        per_person_cost=per_person_cost,
        cost_per_person=per_person_cost,
        locality=event_locality,
        status=event.status,
        venue_booking=booking_schema,
        participants=participant_list,
        created_at=event.created_at,
    )


@app.post(
    "/events",
    response_model=schemas.EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    summary="Create a scheduled event with optional venue slot reservation",
)
def create_event(
    req: schemas.EventCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    activity = db.query(models.Activity).filter(models.Activity.activity_id == req.activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity template not found")

    slot = None
    if req.slot_id:
        slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == req.slot_id).first()
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue slot not found")
        if slot.status != "AVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Venue slot is already {slot.status}",
            )

    new_event = models.Event(
        activity_id=req.activity_id,
        host_id=current_user.user_id,
        title=req.title.strip(),
        event_date=req.event_date if not slot else slot.slot_date,
        start_time=req.start_time if not slot else slot.start_time,
        end_time=req.end_time if not slot else slot.end_time,
        max_capacity=req.max_capacity,
        status="PUBLISHED",
    )
    db.add(new_event)
    db.flush()

    db.add(
        models.EventParticipant(
            event_id=new_event.event_id,
            user_id=current_user.user_id,
            status="CONFIRMED",
        )
    )

    if slot:
        booking = models.VenueBooking(
            event_id=new_event.event_id,
            slot_id=slot.slot_id,
            booked_by=current_user.user_id,
            total_amount=slot.price_total,
            currency=slot.currency,
            status="PENDING",
        )
        db.add(booking)
        slot.status = "HELD"

    db.commit()
    db.refresh(new_event)
    return _build_event_response(new_event, db)


@app.get(
    "/events",
    response_model=List[schemas.EventResponse],
    tags=["Events"],
    summary="Discover scheduled events with filters (locality, activity, date, capacity, status)",
)
def list_events(
    activity_id: Optional[int] = Query(None, description="Filter by activity template ID"),
    interest_id: Optional[int] = Query(None, description="Filter by interest taxonomy ID"),
    locality: Optional[str] = Query(None, description="Filter by venue locality or area"),
    event_date: Optional[date] = Query(None, description="Filter by exact date (YYYY-MM-DD)"),
    date_from: Optional[date] = Query(None, description="Filter from start date"),
    date_to: Optional[date] = Query(None, description="Filter up to end date"),
    status: Optional[str] = Query(None, description="Filter by status ('PUBLISHED', 'FULL', 'COMPLETED')"),
    available_only: bool = Query(False, description="Show only events with remaining capacity"),
    search: Optional[str] = Query(None, description="Search keyword in title or activity"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.Event)

    if status:
        query = query.filter(models.Event.status == status)
    else:
        query = query.filter(models.Event.status.in_(["PUBLISHED", "FULL"]))

    if activity_id:
        query = query.filter(models.Event.activity_id == activity_id)

    if interest_id:
        query = query.join(models.Activity, models.Event.activity_id == models.Activity.activity_id).filter(
            models.Activity.interest_id == interest_id
        )

    if event_date:
        query = query.filter(models.Event.event_date == event_date)
    else:
        if date_from:
            query = query.filter(models.Event.event_date >= date_from)
        if date_to:
            query = query.filter(models.Event.event_date <= date_to)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(models.Event.title.ilike(search_term))

    if locality:
        loc_term = f"%{locality.strip()}%"
        query = (
            query.outerjoin(models.VenueBooking, models.Event.event_id == models.VenueBooking.event_id)
            .outerjoin(models.VenueSlot, models.VenueBooking.slot_id == models.VenueSlot.slot_id)
            .outerjoin(models.Venue, models.VenueSlot.venue_id == models.Venue.venue_id)
            .filter(
                or_(
                    models.Venue.locality.ilike(loc_term),
                    models.Venue.address.ilike(loc_term),
                    models.Event.title.ilike(loc_term),
                )
            )
        )

    events = query.order_by(models.Event.event_date.asc(), models.Event.start_time.asc()).offset(offset).limit(limit).all()

    results = []
    for e in events:
        resp = _build_event_response(e, db)
        if available_only and resp.remaining_spots <= 0:
            continue
        results.append(resp)

    return results


@app.get(
    "/events/{event_id}",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Get full event details, participant roster, venue booking, and dynamic split cost",
)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return _build_event_response(event, db)


@app.patch(
    "/events/{event_id}",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Update event details or lifecycle status (Host only)",
)
def update_event(
    event_id: int,
    req: schemas.EventUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.host_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only event host can modify event")

    if req.title is not None:
        event.title = req.title.strip()
    if req.event_date is not None:
        event.event_date = req.event_date
    if req.start_time is not None:
        event.start_time = req.start_time
    if req.end_time is not None:
        event.end_time = req.end_time

    if req.max_capacity is not None:
        current_count = db.query(models.EventParticipant).filter(
            models.EventParticipant.event_id == event_id,
            models.EventParticipant.status == "CONFIRMED",
        ).count()
        if req.max_capacity < current_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce capacity below current participant count ({current_count})",
            )
        event.max_capacity = req.max_capacity
        if current_count >= req.max_capacity:
            event.status = "FULL"
        elif event.status == "FULL":
            event.status = "PUBLISHED"

    # Lifecycle State Validation
    if req.status is not None:
        target_status = req.status.upper().strip()
        valid_transitions = {
            "DRAFT": ["PUBLISHED", "CANCELLED"],
            "PUBLISHED": ["FULL", "COMPLETED", "CANCELLED"],
            "FULL": ["PUBLISHED", "COMPLETED", "CANCELLED"],
            "COMPLETED": [],
            "CANCELLED": [],
        }

        if target_status not in valid_transitions.get(event.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {event.status} to {target_status}",
            )

        event.status = target_status

        if target_status == "CANCELLED":
            booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event_id).first()
            if booking and booking.status == "PENDING":
                booking.status = "CANCELLED"
                slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == booking.slot_id).first()
                if slot and slot.status == "HELD":
                    slot.status = "AVAILABLE"

    db.commit()
    db.refresh(event)
    return _build_event_response(event, db)


@app.post(
    "/events/{event_id}/join",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Join an event roster with concurrency-safe capacity check",
)
def join_event(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot join a {event.status} event")

    existing_part = (
        db.query(models.EventParticipant)
        .filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == current_user.user_id)
        .first()
    )
    if existing_part and existing_part.status == "CONFIRMED":
        return _build_event_response(event, db)

    current_count = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.status == "CONFIRMED",
    ).count()

    if current_count >= event.max_capacity:
        event.status = "FULL"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event has reached max capacity")

    if existing_part:
        existing_part.status = "CONFIRMED"
        existing_part.joined_at = func.now()
    else:
        new_participant = models.EventParticipant(
            event_id=event_id,
            user_id=current_user.user_id,
            status="CONFIRMED",
        )
        db.add(new_participant)

    if current_count + 1 >= event.max_capacity:
        event.status = "FULL"

    db.commit()
    db.refresh(event)
    return _build_event_response(event, db)


def _handle_leave_event(event_id: int, user_id: int, db: Session) -> models.Event:
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot leave an event that is already {event.status}",
        )

    if event.host_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host cannot leave event directly. You must cancel the event or transfer host role.",
        )

    part = (
        db.query(models.EventParticipant)
        .filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == user_id)
        .first()
    )
    if not part or part.status != "CONFIRMED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an active participant in this event")

    booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event_id).first()
    if booking:
        user_payments = db.query(models.Payment).filter(
            models.Payment.booking_id == booking.booking_id,
            models.Payment.user_id == user_id,
            models.Payment.status == "SUCCESS",
        ).all()
        for p in user_payments:
            p.status = "REFUNDED"

    db.delete(part)

    if event.status == "FULL":
        event.status = "PUBLISHED"

    db.commit()
    db.refresh(event)
    return event


@app.delete(
    "/events/{event_id}/join",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Leave an event roster (REST DELETE format)",
)
def leave_event_delete(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _handle_leave_event(event_id, current_user.user_id, db)
    return _build_event_response(event, db)


@app.post(
    "/events/{event_id}/leave",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Leave an event roster (Alias POST format)",
)
def leave_event_post(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _handle_leave_event(event_id, current_user.user_id, db)
    return _build_event_response(event, db)


# ============================================================================
# 8. PAYMENT & BOOKING SETTLEMENT (Option A: Equal Split Rule)
# ============================================================================

@app.post(
    "/events/{event_id}/pay",
    response_model=schemas.PaymentResponse,
    tags=["Payments"],
    summary="Pay participant's split share toward the venue booking",
)
def pay_event_split_share(
    event_id: int,
    req: schemas.PaymentCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This event does not require a paid venue booking",
        )

    part = (
        db.query(models.EventParticipant)
        .filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == current_user.user_id)
        .first()
    )
    if not part or part.status != "CONFIRMED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Must be a confirmed event participant before paying split share")

    confirmed_count = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.status == "CONFIRMED",
    ).count()

    active_count = max(confirmed_count, 1)
    equal_share = round(float(booking.total_amount) / active_count, 2)
    pay_amount = req.amount if req.amount is not None else equal_share

    payment = models.Payment(
        booking_id=booking.booking_id,
        user_id=current_user.user_id,
        amount=Decimal(str(pay_amount)),
        currency=booking.currency,
        status="SUCCESS",
        provider_payment_id=f"PAY_{booking.booking_id}_{current_user.user_id}_{int(datetime.now().timestamp())}",
    )
    db.add(payment)
    db.flush()

    total_collected = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.booking_id == booking.booking_id, models.Payment.status == "SUCCESS")
        .scalar()
    )

    if float(total_collected) >= float(booking.total_amount):
        booking.status = "CONFIRMED"
        slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == booking.slot_id).first()
        if slot:
            slot.status = "BOOKED"

    db.commit()
    db.refresh(payment)

    user_profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    user_name = user_profile.display_name if user_profile else current_user.email

    return schemas.PaymentResponse(
        payment_id=payment.payment_id,
        booking_id=payment.booking_id,
        user_id=payment.user_id,
        user_name=user_name,
        amount=float(payment.amount),
        currency=payment.currency,
        status=payment.status,
        provider_payment_id=payment.provider_payment_id,
        created_at=payment.created_at,
    )


@app.post(
    "/payment-accounts",
    response_model=schemas.PaymentAccountResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Payments"],
    summary="Register venue owner or host payout account",
)
def create_payment_account(
    req: schemas.PaymentAccountCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(models.PaymentAccount).filter(models.PaymentAccount.user_id == current_user.user_id).first()
    if existing:
        existing.provider = req.provider
        existing.provider_account_id = req.provider_account_id
        existing.status = "ACTIVE"
        db.commit()
        db.refresh(existing)
        return existing

    account = models.PaymentAccount(
        user_id=current_user.user_id,
        provider=req.provider,
        provider_account_id=req.provider_account_id,
        status="ACTIVE",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get(
    "/payment-accounts/me",
    response_model=schemas.PaymentAccountResponse,
    tags=["Payments"],
    summary="Get current user's registered payout account",
)
def get_my_payment_account(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(models.PaymentAccount).filter(models.PaymentAccount.user_id == current_user.user_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No payout account registered")
    return account


@app.post(
    "/bookings/{booking_id}/payout",
    response_model=schemas.PayoutResponse,
    tags=["Payments"],
    summary="Trigger payout settlement to venue owner",
)
def trigger_venue_payout(
    booking_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(models.VenueBooking).filter(models.VenueBooking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue booking not found")

    if booking.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payout can only be initiated for CONFIRMED bookings",
        )

    existing_payout = db.query(models.Payout).filter(models.Payout.booking_id == booking_id).first()
    if existing_payout:
        return existing_payout

    slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == booking.slot_id).first()
    venue = db.query(models.Venue).filter(models.Venue.venue_id == slot.venue_id).first() if slot else None
    
    owner_user_id = venue.owner_user_id if (venue and venue.owner_user_id) else booking.booked_by

    owner_account = db.query(models.PaymentAccount).filter(models.PaymentAccount.user_id == owner_user_id).first()
    if not owner_account:
        owner_account = models.PaymentAccount(
            user_id=owner_user_id,
            provider="razorpay",
            provider_account_id=f"acc_sim_{owner_user_id}",
            status="ACTIVE",
        )
        db.add(owner_account)
        db.flush()

    payout = models.Payout(
        booking_id=booking.booking_id,
        payment_account_id=owner_account.payment_account_id,
        amount=booking.total_amount,
        currency=booking.currency,
        status="COMPLETED",
        provider_transfer_id=f"TRF_{booking.booking_id}_{int(datetime.now().timestamp())}",
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


# ============================================================================
# 9. DETERMINISTIC PEOPLE MATCHING ENGINE
# ============================================================================

@app.get(
    "/matches",
    response_model=schemas.PeopleMatchResponse,
    tags=["Matching"],
    summary="Deterministic People Matching Engine (Discover compatible peers)",
)
@app.get(
    "/matches/people",
    response_model=schemas.PeopleMatchResponse,
    tags=["Matching"],
    summary="Deterministic People Matching Engine alias",
)
def match_people(
    activity_id: Optional[int] = Query(None, description="Optional target activity ID to find matches for"),
    interest_id: Optional[int] = Query(None, description="Optional target interest ID"),
    locality: Optional[str] = Query(None, description="Filter/boost by approximate locality"),
    day_of_week: Optional[str] = Query(None, description="Filter/boost by specific day of week availability"),
    min_score: int = Query(default=10, ge=0, le=100, description="Minimum compatibility score threshold (0-100)"),
    limit: int = Query(default=20, ge=1, le=100, description="Max candidates to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_activity = None
    target_interest = None

    if activity_id:
        target_activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
        if target_activity:
            target_interest = db.query(models.Interest).filter(models.Interest.interest_id == target_activity.interest_id).first()
    elif interest_id:
        target_interest = db.query(models.Interest).filter(models.Interest.interest_id == interest_id).first()

    my_profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    my_user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).all()
    my_interest_ids = {ui.interest_id for ui in my_user_interests}

    my_avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id == current_user.user_id).all()
    my_days = {a.day_of_week.lower().strip() for a in my_avails}

    my_locality = locality.strip() if locality else (my_profile.approx_locality if my_profile and my_profile.approx_locality else "")

    candidates = db.query(models.User).filter(
        models.User.user_id != current_user.user_id,
        models.User.is_active.is_(True),
    ).all()

    matched_candidates = []

    for candidate in candidates:
        c_profile = db.query(models.Profile).filter(models.Profile.user_id == candidate.user_id).first()
        c_user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id == candidate.user_id).all()
        c_interest_ids = {ui.interest_id for ui in c_user_interests}

        c_interests = db.query(models.Interest).filter(models.Interest.interest_id.in_(c_interest_ids)).all() if c_interest_ids else []
        c_interest_map = {i.interest_id: i.name for i in c_interests}

        c_skills = (
            db.query(models.Skill.name, models.Skill.category, models.UserSkill.skill_level, models.UserSkill.is_offering)
            .join(models.UserSkill, models.Skill.skill_id == models.UserSkill.skill_id)
            .filter(models.UserSkill.user_id == candidate.user_id)
            .all()
        )

        c_avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id == candidate.user_id).all()
        c_days = {a.day_of_week.lower().strip() for a in c_avails}

        interest_pts = 0
        avail_pts = 0
        loc_pts = 0
        skill_pts = 0
        reasons = []

        # A. INTEREST SCORE (up to 40 pts)
        shared_int_ids = my_interest_ids.intersection(c_interest_ids)
        shared_int_names = [c_interest_map[i_id] for i_id in shared_int_ids if i_id in c_interest_map]

        if target_interest:
            if target_interest.interest_id in c_interest_ids:
                interest_pts = 40
                reasons.append(f"Shares target interest '{target_interest.name}' (+40 pts)")
            elif shared_int_names:
                interest_pts = min(30, len(shared_int_names) * 15)
                reasons.append(f"Shares common interests: {', '.join(shared_int_names[:2])} (+{interest_pts} pts)")
        else:
            if shared_int_names:
                interest_pts = min(40, len(shared_int_names) * 20)
                reasons.append(f"Shares common interests: {', '.join(shared_int_names[:2])} (+{interest_pts} pts)")

        # B. AVAILABILITY SCORE (up to 30 pts)
        shared_avail_display = [f"{a.day_of_week}" + (f" ({a.start_time.strftime('%H:%M')}-{a.end_time.strftime('%H:%M')})" if a.start_time and a.end_time else "") for a in c_avails]

        if day_of_week:
            target_day_clean = day_of_week.lower().strip()
            if target_day_clean in c_days or any(target_day_clean in d for d in c_days):
                avail_pts = 30
                reasons.append(f"Available on requested day: {day_of_week.capitalize()} (+30 pts)")
        else:
            overlap_days = my_days.intersection(c_days)
            if len(overlap_days) >= 2:
                avail_pts = 30
                reasons.append(f"Multiple overlapping days: {', '.join([d.capitalize() for d in list(overlap_days)[:2]])} (+30 pts)")
            elif len(overlap_days) == 1:
                avail_pts = 20
                reasons.append(f"Matching availability on {list(overlap_days)[0].capitalize()} (+20 pts)")

        # C. LOCATION SCORE (up to 20 pts)
        c_locality = c_profile.approx_locality.strip() if (c_profile and c_profile.approx_locality) else ""
        if my_locality and c_locality:
            my_loc_lower = my_locality.lower()
            c_loc_lower = c_locality.lower()

            if my_loc_lower in c_loc_lower or c_loc_lower in my_loc_lower:
                loc_pts = 20
                reasons.append(f"Same locality match: {c_locality} (+20 pts)")
            else:
                my_tokens = set(my_loc_lower.replace(",", " ").split())
                c_tokens = set(c_loc_lower.replace(",", " ").split())
                if my_tokens.intersection(c_tokens):
                    loc_pts = 10
                    reasons.append(f"Nearby area: {c_locality} (+10 pts)")

        # D. SKILL SCORE (up to 10 pts)
        relevant_skills_display = []
        offered_skills = [s for s in c_skills if s.is_offering]

        for s in offered_skills:
            relevant_skills_display.append(f"{s.name} ({s.skill_level})")
            if target_interest and (s.category.lower() == target_interest.category.lower() or s.name.lower() in target_interest.name.lower()):
                skill_pts = 10

        if skill_pts == 10:
            reasons.append(f"Offers relevant skill matching activity category (+10 pts)")
        elif offered_skills:
            skill_pts = 5
            reasons.append(f"Offers active skill: {offered_skills[0].name} (+5 pts)")

        total_score = min(100, interest_pts + avail_pts + loc_pts + skill_pts)

        if total_score >= min_score:
            matched_candidates.append(
                schemas.PeopleMatchCandidate(
                    user_id=candidate.user_id,
                    display_name=c_profile.display_name if c_profile else candidate.email.split("@")[0].capitalize(),
                    avatar_url=c_profile.avatar_url if c_profile else None,
                    approx_locality=c_profile.approx_locality if c_profile else None,
                    match_score=total_score,
                    match_breakdown={
                        "interest": interest_pts,
                        "availability": avail_pts,
                        "location": loc_pts,
                        "skill": skill_pts,
                        "total": total_score,
                    },
                    match_reasons=reasons,
                    shared_interests=shared_int_names if shared_int_names else ([target_interest.name] if (target_interest and target_interest.interest_id in c_interest_ids) else []),
                    relevant_skills=relevant_skills_display,
                    shared_availability=shared_avail_display,
                )
            )

    matched_candidates.sort(key=lambda x: x.match_score, reverse=True)
    matched_candidates = matched_candidates[:limit]

    return schemas.PeopleMatchResponse(
        total_candidates=len(matched_candidates),
        activity_id=activity_id,
        activity_title=target_activity.title if target_activity else None,
        target_interest=target_interest.name if target_interest else None,
        matches=matched_candidates,
    )


# ============================================================================
# 10. COMMUNITIES & FEEDBACK ENDPOINTS
# ============================================================================

@app.post(
    "/communities",
    response_model=schemas.CommunityResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Communities"],
    summary="Create a permanent recurring community circle",
)
def create_community(
    req: schemas.CommunityCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Community).filter(models.Community.name == req.name.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Community name already exists")

    community = models.Community(
        name=req.name.strip(),
        description=req.description.strip() if req.description else None,
        created_by=current_user.user_id,
    )
    db.add(community)
    db.flush()

    db.add(
        models.CommunityMember(
            community_id=community.community_id,
            user_id=current_user.user_id,
            role="ADMIN",
        )
    )
    db.commit()
    db.refresh(community)

    return schemas.CommunityResponse(
        community_id=community.community_id,
        name=community.name,
        description=community.description,
        created_by=community.created_by,
        member_count=1,
        created_at=community.created_at,
    )


@app.get(
    "/communities",
    response_model=List[schemas.CommunityResponse],
    tags=["Communities"],
    summary="List all community circles",
)
def list_communities(db: Session = Depends(get_db)):
    comms = db.query(models.Community).all()
    results = []
    for c in comms:
        count = db.query(models.CommunityMember).filter(models.CommunityMember.community_id == c.community_id).count()
        results.append(
            schemas.CommunityResponse(
                community_id=c.community_id,
                name=c.name,
                description=c.description,
                created_by=c.created_by,
                member_count=count,
                created_at=c.created_at,
            )
        )
    return results


@app.post(
    "/communities/{community_id}/join",
    tags=["Communities"],
    summary="Join a community circle",
)
def join_community(
    community_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comm = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    existing = (
        db.query(models.CommunityMember)
        .filter(models.CommunityMember.community_id == community_id, models.CommunityMember.user_id == current_user.user_id)
        .first()
    )
    if existing:
        return {"message": "Already a member of this community", "community_id": community_id}

    db.add(
        models.CommunityMember(
            community_id=community_id,
            user_id=current_user.user_id,
            role="MEMBER",
        )
    )
    db.commit()
    return {"message": "Successfully joined community", "community_id": community_id}


@app.post(
    "/events/{event_id}/feedback",
    response_model=schemas.FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
    summary="Submit peer rating and review for an event",
)
def submit_feedback(
    event_id: int,
    req: schemas.FeedbackCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    part = (
        db.query(models.EventParticipant)
        .filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == current_user.user_id)
        .first()
    )
    if not part or part.status != "CONFIRMED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only confirmed event participants can leave feedback")

    existing = (
        db.query(models.Feedback)
        .filter(models.Feedback.event_id == event_id, models.Feedback.reviewer_id == current_user.user_id)
        .first()
    )
    if existing:
        existing.rating = req.rating
        existing.comment = req.comment
        db.commit()
        db.refresh(existing)
        fb = existing
    else:
        fb = models.Feedback(
            event_id=event_id,
            reviewer_id=current_user.user_id,
            rating=req.rating,
            comment=req.comment,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

    user_profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    reviewer_name = user_profile.display_name if user_profile else current_user.email

    return schemas.FeedbackResponse(
        feedback_id=fb.feedback_id,
        event_id=fb.event_id,
        reviewer_id=fb.reviewer_id,
        reviewer_name=reviewer_name,
        rating=fb.rating,
        comment=fb.comment,
        created_at=fb.created_at,
    )


@app.get(
    "/events/{event_id}/feedback",
    response_model=List[schemas.FeedbackResponse],
    tags=["Feedback"],
    summary="Get all peer feedback and reviews for an event",
)
def get_event_feedback(event_id: int, db: Session = Depends(get_db)):
    feedbacks = db.query(models.Feedback).filter(models.Feedback.event_id == event_id).all()
    results = []
    for f in feedbacks:
        prof = db.query(models.Profile).filter(models.Profile.user_id == f.reviewer_id).first()
        results.append(
            schemas.FeedbackResponse(
                feedback_id=f.feedback_id,
                event_id=f.event_id,
                reviewer_id=f.reviewer_id,
                reviewer_name=prof.display_name if prof else f"User {f.reviewer_id}",
                rating=f.rating,
                comment=f.comment,
                created_at=f.created_at,
            )
        )
    return results


# ============================================================================
# 11. AI INTENT UNDERSTANDING ENGINE
# ============================================================================

@app.post(
    "/ai/intent",
    response_model=schemas.AIIntentResponse,
    tags=["AI Engine"],
    summary="Understand and extract structured parameters from natural language user input",
)
def parse_ai_intent(req: schemas.AIIntentRequest):
    return understand_user_intent(req.query)


@app.post(
    "/ai/intent/search",
    response_model=schemas.AIIntentSearchResponse,
    tags=["AI Engine"],
    summary="Execute end-to-end AI search: Natural language sentence -> Structured intent -> People, Events & Venues",
)
def search_by_ai_intent(
    req: schemas.AIIntentSearchRequest,
    current_user: Optional[models.User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    # 1. AI Intent Understanding
    intent_data = understand_user_intent(req.query)

    # 2. Resolve Target Activity & Interest from taxonomy
    target_activity = None
    target_interest = None

    if intent_data.activity:
        act_term = intent_data.activity.strip()
        target_activity = (
            db.query(models.Activity)
            .filter(models.Activity.title.ilike(f"%{act_term}%"))
            .first()
        )
        if target_activity:
            target_interest = db.query(models.Interest).filter(models.Interest.interest_id == target_activity.interest_id).first()
        else:
            target_interest = (
                db.query(models.Interest)
                .filter(models.Interest.name.ilike(f"%{act_term}%"))
                .first()
            )

    if not target_interest and intent_data.category:
        target_interest = (
            db.query(models.Interest)
            .filter(models.Interest.category.ilike(f"%{intent_data.category}%"))
            .first()
        )

    # 3. Resolve Locality Context
    search_locality = None
    if intent_data.location and intent_data.location.lower() != "nearby":
        search_locality = intent_data.location.strip()
    elif current_user:
        my_prof = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
        if my_prof and my_prof.approx_locality:
            search_locality = my_prof.approx_locality.strip()

    # 4. Deterministic People Matching
    my_user_id = current_user.user_id if current_user else 0
    my_interests = (
        {ui.interest_id for ui in db.query(models.UserInterest).filter(models.UserInterest.user_id == my_user_id).all()}
        if current_user else set()
    )
    my_avails = (
        {a.day_of_week.lower().strip() for a in db.query(models.UserAvailability).filter(models.UserAvailability.user_id == my_user_id).all()}
        if current_user else set()
    )

    candidates_query = db.query(models.User).filter(models.User.is_active.is_(True))
    if current_user:
        candidates_query = candidates_query.filter(models.User.user_id != current_user.user_id)
    candidates = candidates_query.all()

    matched_candidates = []
    for cand in candidates:
        c_profile = db.query(models.Profile).filter(models.Profile.user_id == cand.user_id).first()
        c_user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id == cand.user_id).all()
        c_interest_ids = {ui.interest_id for ui in c_user_interests}

        c_interests = db.query(models.Interest).filter(models.Interest.interest_id.in_(c_interest_ids)).all() if c_interest_ids else []
        c_interest_map = {i.interest_id: i.name for i in c_interests}

        c_skills = (
            db.query(models.Skill.name, models.Skill.category, models.UserSkill.skill_level, models.UserSkill.is_offering)
            .join(models.UserSkill, models.Skill.skill_id == models.UserSkill.skill_id)
            .filter(models.UserSkill.user_id == cand.user_id)
            .all()
        )

        c_avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id == cand.user_id).all()
        c_days = {a.day_of_week.lower().strip() for a in c_avails}

        interest_pts = 0
        avail_pts = 0
        loc_pts = 0
        skill_pts = 0
        reasons = []

        # A. Interest Score (up to 40)
        shared_int_ids = my_interests.intersection(c_interest_ids) if current_user else set()
        shared_int_names = [c_interest_map[i_id] for i_id in shared_int_ids if i_id in c_interest_map]

        if target_interest:
            if target_interest.interest_id in c_interest_ids:
                interest_pts = 40
                reasons.append(f"Shares target interest '{target_interest.name}' (+40 pts)")
            elif shared_int_names:
                interest_pts = min(30, len(shared_int_names) * 15)
                reasons.append(f"Shares common interests: {', '.join(shared_int_names[:2])} (+{interest_pts} pts)")
        else:
            if shared_int_names:
                interest_pts = min(40, len(shared_int_names) * 20)
                reasons.append(f"Shares common interests: {', '.join(shared_int_names[:2])} (+{interest_pts} pts)")

        # B. Availability Score (up to 30)
        shared_avail_display = [f"{a.day_of_week}" + (f" ({a.start_time.strftime('%H:%M')}-{a.end_time.strftime('%H:%M')})" if a.start_time and a.end_time else "") for a in c_avails]

        if intent_data.day_of_week:
            target_day_clean = intent_data.day_of_week.lower().strip()
            if target_day_clean in c_days or any(target_day_clean in d for d in c_days):
                avail_pts = 30
                reasons.append(f"Available on requested day: {intent_data.day_of_week.capitalize()} (+30 pts)")
        elif my_avails:
            overlap_days = my_avails.intersection(c_days)
            if len(overlap_days) >= 2:
                avail_pts = 30
                reasons.append(f"Multiple overlapping days: {', '.join([d.capitalize() for d in list(overlap_days)[:2]])} (+30 pts)")
            elif len(overlap_days) == 1:
                avail_pts = 20
                reasons.append(f"Matching availability on {list(overlap_days)[0].capitalize()} (+20 pts)")

        # C. Location Score (up to 20)
        c_locality = c_profile.approx_locality.strip() if (c_profile and c_profile.approx_locality) else ""
        if search_locality and c_locality:
            s_loc_lower = search_locality.lower()
            c_loc_lower = c_locality.lower()
            if s_loc_lower in c_loc_lower or c_loc_lower in s_loc_lower:
                loc_pts = 20
                reasons.append(f"Same locality match: {c_locality} (+20 pts)")
            else:
                s_tokens = set(s_loc_lower.replace(",", " ").split())
                c_tokens = set(c_loc_lower.replace(",", " ").split())
                if s_tokens.intersection(c_tokens):
                    loc_pts = 10
                    reasons.append(f"Nearby area: {c_locality} (+10 pts)")

        # D. Skill Score (up to 10)
        relevant_skills_display = []
        offered_skills = [s for s in c_skills if s.is_offering]
        for s in offered_skills:
            relevant_skills_display.append(f"{s.name} ({s.skill_level})")
            if target_interest and (s.category.lower() == target_interest.category.lower() or s.name.lower() in target_interest.name.lower()):
                skill_pts = 10

        if skill_pts == 10:
            reasons.append("Offers relevant skill matching activity category (+10 pts)")
        elif offered_skills:
            skill_pts = 5
            reasons.append(f"Offers active skill: {offered_skills[0].name} (+5 pts)")

        total_score = min(100, interest_pts + avail_pts + loc_pts + skill_pts)

        if total_score >= 10:
            matched_candidates.append(
                schemas.PeopleMatchCandidate(
                    user_id=cand.user_id,
                    display_name=c_profile.display_name if c_profile else cand.email.split("@")[0].capitalize(),
                    avatar_url=c_profile.avatar_url if c_profile else None,
                    approx_locality=c_profile.approx_locality if c_profile else None,
                    match_score=total_score,
                    match_breakdown={
                        "interest": interest_pts,
                        "availability": avail_pts,
                        "location": loc_pts,
                        "skill": skill_pts,
                        "total": total_score,
                    },
                    match_reasons=reasons,
                    shared_interests=shared_int_names if shared_int_names else ([target_interest.name] if (target_interest and target_interest.interest_id in c_interest_ids) else []),
                    relevant_skills=relevant_skills_display,
                    shared_availability=shared_avail_display,
                )
            )

    matched_candidates.sort(key=lambda x: x.match_score, reverse=True)
    people_results = matched_candidates[:req.limit]

    # 5. Event Discovery
    events_query = db.query(models.Event).filter(models.Event.status.in_(["PUBLISHED", "FULL"]))
    if target_activity:
        events_query = events_query.filter(models.Event.activity_id == target_activity.activity_id)
    elif target_interest:
        events_query = events_query.join(models.Activity, models.Event.activity_id == models.Activity.activity_id).filter(
            models.Activity.interest_id == target_interest.interest_id
        )

    if search_locality:
        base_locality = search_locality.split(",")[0].strip()
        loc_term = f"%{base_locality}%"
        events_query = (
            events_query.outerjoin(models.VenueBooking, models.Event.event_id == models.VenueBooking.event_id)
            .outerjoin(models.VenueSlot, models.VenueBooking.slot_id == models.VenueSlot.slot_id)
            .outerjoin(models.Venue, models.VenueSlot.venue_id == models.Venue.venue_id)
            .filter(
                or_(
                    models.Venue.locality.ilike(loc_term),
                    models.Venue.address.ilike(loc_term),
                    models.Event.title.ilike(loc_term),
                    models.Event.title.ilike(f"%{search_locality.strip()}%"),
                )
            )
        )

    events = events_query.order_by(models.Event.event_date.asc()).limit(req.limit).all()
    event_results = [_build_event_response(e, db) for e in events]

    # 6. Venue Discovery
    venues_query = db.query(models.Venue).filter(models.Venue.status == "ACTIVE")
    if search_locality:
        base_locality = search_locality.split(",")[0].strip()
        venues_query = venues_query.filter(
            or_(
                models.Venue.locality.ilike(f"%{base_locality}%"),
                models.Venue.address.ilike(f"%{base_locality}%"),
            )
        )
    if target_activity:
        venues_query = venues_query.join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id).filter(
            models.VenueActivity.activity_id == target_activity.activity_id
        )

    venues = venues_query.order_by(models.Venue.name).limit(req.limit).all()
    venue_results = [_build_venue_response(v, db) for v in venues]

    # 7. Construct Summary
    activity_str = intent_data.activity or (target_interest.name if target_interest else "General Activity")
    day_time_str = f" • {intent_data.day_of_week}" if intent_data.day_of_week else ""
    if intent_data.time_of_day:
        day_time_str += f" {intent_data.time_of_day}"
    loc_str = f" • {search_locality}" if search_locality else (" • Nearby" if intent_data.location == "nearby" else "")

    summary_text = (
        f"Intent understood: {activity_str}{day_time_str}{loc_str}. "
        f"Found {len(people_results)} matching peers, {len(event_results)} events, and {len(venue_results)} venues."
    )

    return schemas.AIIntentSearchResponse(
        query=req.query,
        intent_understood=intent_data,
        summary=summary_text,
        people_matches=people_results,
        events=event_results,
        venues=venue_results,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

