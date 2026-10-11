from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ai_service import (
    generate_ai_experience_plan,
    generate_community_action_recommendations_ai,
    generate_community_lifecycle_ai,
    understand_user_intent,
)
from auth import create_access_token, get_current_user, get_optional_current_user, hash_password, verify_password
from database import SessionLocal, check_db_connection, get_db
from embedding_service import (
    backfill_all_embeddings,
    build_activity_semantic_text,
    compute_cosine_similarity,
    generate_embedding,
    update_activity_embedding,
    update_user_embedding,
)
import models
import schemas
from seed import seed_master_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed master taxonomy and embeddings on startup
    db = SessionLocal()
    try:
        seed_master_data(db)
        backfill_all_embeddings(db)
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
    update_user_embedding(current_user.user_id, db)
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
    update_user_embedding(current_user.user_id, db)
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
    update_user_embedding(current_user.user_id, db)
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
    update_user_embedding(current_user.user_id, db)
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
    update_user_embedding(current_user.user_id, db)
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
    update_activity_embedding(new_activity.activity_id, db)
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


@app.post(
    "/events/{event_id}/venue-book",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Reserve and attach a compatible venue slot to an active event (Host only)",
)
@app.post(
    "/events/{event_id}/book-venue",
    response_model=schemas.EventResponse,
    tags=["Events"],
    summary="Alias: Reserve and attach a compatible venue slot to an active event (Host only)",
)
def book_event_venue(
    event_id: int,
    req: schemas.EventVenueBookRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot book a venue for an event that is {event.status}",
        )

    if event.host_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event host can book a venue for this event",
        )

    existing_booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event_id).first()
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event already has a venue booking attached",
        )

    slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == req.slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue slot not found")

    if slot.status != "AVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Venue slot is already {slot.status}",
        )

    venue = db.query(models.Venue).filter(models.Venue.venue_id == slot.venue_id).first()
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    if venue.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Venue is not active (status: {venue.status})",
        )

    supported = db.query(models.VenueActivity).filter(
        models.VenueActivity.venue_id == venue.venue_id,
        models.VenueActivity.activity_id == event.activity_id,
    ).first()
    if not supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue does not support the activity required for this event",
        )

    if event.event_date != slot.slot_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event date ({event.event_date}) does not match venue slot date ({slot.slot_date})",
        )

    # Sync event schedule with reserved venue slot
    event.start_time = slot.start_time
    event.end_time = slot.end_time

    booking = models.VenueBooking(
        event_id=event.event_id,
        slot_id=slot.slot_id,
        booked_by=current_user.user_id,
        total_amount=slot.price_total,
        currency=slot.currency,
        status="CONFIRMED",
    )
    db.add(booking)
    slot.status = "BOOKED"

    db.commit()
    db.refresh(event)
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

    if event.status in ["CANCELLED", "COMPLETED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot make payment for an event that is {event.status}",
        )

    booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event_id).first()
    if not booking or booking.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This event does not have an active venue booking",
        )

    part = (
        db.query(models.EventParticipant)
        .filter(models.EventParticipant.event_id == event_id, models.EventParticipant.user_id == current_user.user_id)
        .first()
    )
    if not part or part.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a confirmed event participant before paying split share",
        )

    confirmed_count = db.query(models.EventParticipant).filter(
        models.EventParticipant.event_id == event_id,
        models.EventParticipant.status == "CONFIRMED",
    ).count()

    active_count = max(confirmed_count, 1)
    total_amount = float(booking.total_amount)
    equal_share = round(total_amount / active_count, 2)

    paid_so_far = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(
            models.Payment.booking_id == booking.booking_id,
            models.Payment.user_id == current_user.user_id,
            models.Payment.status == "SUCCESS",
        )
        .scalar()
    )
    paid_so_far = float(paid_so_far)
    remaining_user_share = max(0.0, round(equal_share - paid_so_far, 2))

    if remaining_user_share <= 0.001:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant has already fully paid their split share",
        )

    total_collected = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.booking_id == booking.booking_id, models.Payment.status == "SUCCESS")
        .scalar()
    )
    total_collected = float(total_collected)
    remaining_booking_total = max(0.0, round(total_amount - total_collected, 2))

    if req.amount is None:
        pay_amount = min(remaining_user_share, remaining_booking_total)
    else:
        req_amt = float(req.amount)
        if req_amt <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than 0",
            )
        if req_amt > remaining_user_share + 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount exceeds your remaining share of INR {remaining_user_share:.2f}",
            )
        if req_amt > remaining_booking_total + 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount exceeds remaining booking total of INR {remaining_booking_total:.2f}",
            )
        pay_amount = req_amt

    payment = models.Payment(
        booking_id=booking.booking_id,
        user_id=current_user.user_id,
        amount=Decimal(str(round(pay_amount, 2))),
        currency=booking.currency,
        status="SUCCESS",
        provider_payment_id=f"PAY_SIM_{booking.booking_id}_{current_user.user_id}_{int(datetime.now().timestamp() * 1000)}",
    )
    db.add(payment)
    db.flush()

    new_total_collected = round(total_collected + pay_amount, 2)
    if new_total_collected >= total_amount - 0.01:
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


def _process_payout_for_booking(event: models.Event, booking: models.VenueBooking, current_user: models.User, db: Session) -> models.Payout:
    if event.status in ["CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payout for an event that is {event.status}",
        )

    slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == booking.slot_id).first()
    venue = db.query(models.Venue).filter(models.Venue.venue_id == slot.venue_id).first() if slot else None
    if not venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    is_host = (event.host_id == current_user.user_id)
    is_owner = (venue.owner_user_id and venue.owner_user_id == current_user.user_id)
    if not is_host and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event host or venue owner can trigger payout settlement",
        )

    total_collected = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.booking_id == booking.booking_id, models.Payment.status == "SUCCESS")
        .scalar()
    )
    total_collected = float(total_collected)
    total_amount = float(booking.total_amount)

    if total_collected < total_amount - 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payout: venue booking is not fully paid (Collected: INR {total_collected:.2f} / Total: INR {total_amount:.2f})",
        )

    owner_user_id = venue.owner_user_id
    if not owner_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue does not have a registered owner for payout settlement",
        )

    owner_account = db.query(models.PaymentAccount).filter(models.PaymentAccount.user_id == owner_user_id).first()
    if not owner_account or owner_account.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue owner does not have an active payment account registered",
        )

    existing_payout = db.query(models.Payout).filter(models.Payout.booking_id == booking.booking_id).first()
    if existing_payout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payout has already been processed for this booking",
        )

    payout = models.Payout(
        booking_id=booking.booking_id,
        payment_account_id=owner_account.payment_account_id,
        amount=booking.total_amount,
        currency=booking.currency,
        status="COMPLETED",
        provider_transfer_id=f"TRF_SIM_{booking.booking_id}_{owner_user_id}_{int(datetime.now().timestamp() * 1000)}",
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


@app.post(
    "/events/{event_id}/payout",
    response_model=schemas.PayoutResponse,
    tags=["Payments"],
    summary="Trigger payout settlement to venue owner for a fully-paid event booking",
)
def trigger_event_payout(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == event_id).first()
    if not booking or booking.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This event does not have an active venue booking",
        )

    return _process_payout_for_booking(event, booking, current_user, db)


@app.post(
    "/bookings/{booking_id}/payout",
    response_model=schemas.PayoutResponse,
    tags=["Payments"],
    summary="Alias: Trigger payout settlement by booking ID",
)
def trigger_venue_payout(
    booking_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(models.VenueBooking).filter(models.VenueBooking.booking_id == booking_id).first()
    if not booking or booking.status == "CANCELLED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue booking not found")

    event = db.query(models.Event).filter(models.Event.event_id == booking.event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    return _process_payout_for_booking(event, booking, current_user, db)


# ============================================================================
# 9. DETERMINISTIC & TRUST-AWARE PEOPLE MATCHING ENGINE
# ============================================================================

def _get_user_reputation_summary(user_id: int, db: Session) -> schemas.MatchReputationSummary:
    event_ids = [
        row[0]
        for row in db.query(models.EventParticipant.event_id)
        .filter(
            models.EventParticipant.user_id == user_id,
            models.EventParticipant.status == "CONFIRMED",
        )
        .all()
    ]

    feedbacks = (
        db.query(models.Feedback)
        .filter(
            models.Feedback.event_id.in_(event_ids),
            models.Feedback.reviewer_id != user_id,
        )
        .all()
        if event_ids
        else []
    )

    completed_events = (
        db.query(models.EventParticipant)
        .join(models.Event, models.EventParticipant.event_id == models.Event.event_id)
        .filter(
            models.EventParticipant.user_id == user_id,
            models.EventParticipant.status == "CONFIRMED",
            models.Event.status == "COMPLETED",
        )
        .count()
    )

    total_reviews = len(feedbacks)
    average_rating = round(sum(f.rating for f in feedbacks) / total_reviews, 2) if total_reviews > 0 else 0.0

    return schemas.MatchReputationSummary(
        average_rating=average_rating,
        total_reviews=total_reviews,
        completed_events=completed_events,
    )


@app.get(
    "/matches",
    response_model=schemas.PeopleMatchResponse,
    tags=["Matching"],
    summary="Deterministic & Trust-Aware People Matching Engine (Discover compatible peers)",
)
@app.get(
    "/matches/people",
    response_model=schemas.PeopleMatchResponse,
    tags=["Matching"],
    summary="Deterministic & Trust-Aware People Matching Engine alias",
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

    # Query Vector Resolution for Semantic Scoring
    query_embedding = None
    if target_activity:
        if target_activity.embedding is not None:
            query_embedding = target_activity.embedding
        else:
            query_embedding = update_activity_embedding(target_activity.activity_id, db)
    elif target_interest:
        query_embedding = generate_embedding(f"Interest: {target_interest.name}. Category: {target_interest.category}.")
    else:
        if my_profile and my_profile.embedding is not None:
            query_embedding = my_profile.embedding
        else:
            query_embedding = update_user_embedding(current_user.user_id, db)

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

        deterministic_score = min(100, interest_pts + avail_pts + loc_pts + skill_pts)

        # E. AI SEMANTIC EMBEDDING SIMILARITY (30% weight)
        c_embedding = c_profile.embedding if (c_profile and c_profile.embedding is not None) else update_user_embedding(candidate.user_id, db)
        semantic_sim = compute_cosine_similarity(query_embedding, c_embedding)
        semantic_pts = round(semantic_sim * 30.0, 1)

        hybrid_score = min(100, max(0, round((deterministic_score * 0.70) + ((semantic_sim * 100.0) * 0.30))))

        if semantic_sim >= 0.40:
            reasons.append(f"AI semantic profile affinity: {int(round(semantic_sim * 100))}% (+{semantic_pts} pts)")

        # F. REPUTATION & TRUST SIGNAL
        rep_summary = _get_user_reputation_summary(candidate.user_id, db)
        if rep_summary.total_reviews > 0:
            trust_score = min(100, max(0, int(round((rep_summary.average_rating / 5.0) * 100))))
            if rep_summary.average_rating >= 4.5:
                reasons.append(f"Highly-rated peer ({rep_summary.average_rating}★ from {rep_summary.total_reviews} reviews)")
            elif rep_summary.average_rating >= 4.0:
                reasons.append(f"Well-rated participant ({rep_summary.average_rating}★)")
        else:
            trust_score = 75

        if hybrid_score >= min_score or deterministic_score >= min_score:
            matched_candidates.append(
                schemas.PeopleMatchCandidate(
                    user_id=candidate.user_id,
                    display_name=c_profile.display_name if c_profile else candidate.email.split("@")[0].capitalize(),
                    avatar_url=c_profile.avatar_url if c_profile else None,
                    approx_locality=c_profile.approx_locality if c_profile else None,
                    match_score=hybrid_score,
                    deterministic_score=deterministic_score,
                    semantic_similarity=round(float(semantic_sim), 4),
                    trust_score=trust_score,
                    reputation=rep_summary,
                    match_breakdown={
                        "interest": interest_pts,
                        "availability": avail_pts,
                        "location": loc_pts,
                        "skill": skill_pts,
                        "semantic": semantic_pts,
                        "deterministic_total": deterministic_score,
                        "total": hybrid_score,
                    },
                    match_reasons=reasons,
                    shared_interests=shared_int_names if shared_int_names else ([target_interest.name] if (target_interest and target_interest.interest_id in c_interest_ids) else []),
                    relevant_skills=relevant_skills_display,
                    shared_availability=shared_avail_display,
                )
            )

    matched_candidates.sort(key=lambda x: (x.match_score, x.trust_score or 0), reverse=True)
    matched_candidates = matched_candidates[:limit]

    return schemas.PeopleMatchResponse(
        total_candidates=len(matched_candidates),
        activity_id=activity_id,
        activity_title=target_activity.title if target_activity else None,
        target_interest=target_interest.name if target_interest else None,
        matches=matched_candidates,
    )


# ============================================================================
# 9.5 AI RECOMMENDATION ENGINE (Ranked Personalized Entities)
# ============================================================================

@app.get(
    "/recommendations",
    response_model=schemas.RecommendationResponse,
    tags=["Recommendations"],
    summary="AI Recommendation Engine: Personalized events, activities, and compatible peers",
)
def get_recommendations(
    type: Optional[str] = Query(None, description="Filter by entity type: 'EVENT', 'ACTIVITY', 'PEOPLE', or 'ALL' (default 'ALL')"),
    locality: Optional[str] = Query(None, description="Filter / boost by specific locality override"),
    min_score: int = Query(default=10, ge=0, le=100, description="Minimum recommendation threshold (0-100)"),
    limit: int = Query(default=20, ge=1, le=500, description="Max recommendations to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_type = (type or "ALL").upper().strip()

    # 1. Fetch User Profile, Preferences & Embedding
    user_profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).all()
    user_interest_ids = {ui.interest_id for ui in user_interests}

    interest_objs = db.query(models.Interest).filter(models.Interest.interest_id.in_(user_interest_ids)).all() if user_interest_ids else []
    user_interest_names = [i.name.lower() for i in interest_objs]
    user_interest_categories = [i.category.lower() for i in interest_objs]

    user_skills = (
        db.query(models.Skill.name, models.Skill.category, models.UserSkill.skill_level, models.UserSkill.is_offering)
        .join(models.UserSkill, models.Skill.skill_id == models.UserSkill.skill_id)
        .filter(models.UserSkill.user_id == current_user.user_id)
        .all()
    )
    user_skill_names = [s.name.lower() for s in user_skills]
    user_skill_categories = [s.category.lower() for s in user_skills]

    user_avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id == current_user.user_id).all()
    user_avail_days = {a.day_of_week.lower().strip() for a in user_avails}

    effective_locality = locality.strip() if locality else (user_profile.approx_locality.strip() if user_profile and user_profile.approx_locality else "")

    user_embedding = user_profile.embedding if (user_profile and user_profile.embedding is not None) else update_user_embedding(current_user.user_id, db)

    recommendations: List[schemas.RecommendationItem] = []

    # ------------------------------------------------------------------------
    # 2. EVENT RECOMMENDATIONS
    # ------------------------------------------------------------------------
    if target_type in ["ALL", "EVENT", "EVENTS"]:
        # Find active future events excluding ones user hosts or is already confirmed in
        user_confirmed_event_ids = {
            ep.event_id
            for ep in db.query(models.EventParticipant.event_id)
            .filter(models.EventParticipant.user_id == current_user.user_id, models.EventParticipant.status == "CONFIRMED")
            .all()
        }

        events = (
            db.query(models.Event)
            .filter(
                models.Event.host_id != current_user.user_id,
                models.Event.status.in_(["PUBLISHED", "FULL"]),
                models.Event.event_date >= date.today(),
            )
            .all()
        )

        for ev in events:
            if ev.event_id in user_confirmed_event_ids:
                continue

            activity = db.query(models.Activity).filter(models.Activity.activity_id == ev.activity_id).first()
            act_interest = db.query(models.Interest).filter(models.Interest.interest_id == activity.interest_id).first() if activity else None

            interest_pts = 0
            avail_pts = 0
            loc_pts = 0
            skill_pts = 0
            reasons = []

            # Interest factor (up to 40 pts)
            if activity and activity.interest_id in user_interest_ids:
                interest_pts = 40
                int_name = act_interest.name if act_interest else "interest"
                reasons.append(f"Matches your {int_name} interest (+40 pts)")
            elif act_interest and act_interest.category.lower() in user_interest_categories:
                interest_pts = 20
                reasons.append(f"Matches your {act_interest.category} category preference (+20 pts)")
            elif user_interest_names and activity and any(un in activity.title.lower() for un in user_interest_names):
                interest_pts = 25
                reasons.append(f"Activity matches your interest (+25 pts)")

            # Availability factor (up to 30 pts)
            ev_day = ev.event_date.strftime("%A")
            ev_day_lower = ev_day.lower()
            if ev_day_lower in user_avail_days or ("weekend" in user_avail_days and ev_day_lower in ["saturday", "sunday"]):
                avail_pts = 30
                reasons.append(f"Fits your {ev_day} availability (+30 pts)")

            # Locality factor (up to 20 pts)
            ev_booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == ev.event_id).first()
            ev_slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == ev_booking.slot_id).first() if ev_booking else None
            ev_venue = db.query(models.Venue).filter(models.Venue.venue_id == ev_slot.venue_id).first() if ev_slot else None

            host_prof = db.query(models.Profile).filter(models.Profile.user_id == ev.host_id).first()
            ev_locality = ev_venue.locality if ev_venue else (host_prof.approx_locality if host_prof and host_prof.approx_locality else "")

            if effective_locality and ev_locality:
                eff_loc_lower = effective_locality.lower()
                ev_loc_lower = ev_locality.lower()
                if eff_loc_lower in ev_loc_lower or ev_loc_lower in eff_loc_lower:
                    loc_pts = 20
                    reasons.append(f"Near your preferred locality: {ev_locality} (+20 pts)")
                else:
                    eff_tokens = set(eff_loc_lower.replace(",", " ").split())
                    ev_tokens = set(ev_loc_lower.replace(",", " ").split())
                    if eff_tokens.intersection(ev_tokens):
                        loc_pts = 10
                        reasons.append(f"Nearby area: {ev_locality} (+10 pts)")

            # Skill factor (up to 10 pts)
            if act_interest and (act_interest.category.lower() in user_skill_categories or any(s in act_interest.name.lower() for s in user_skill_names)):
                skill_pts = 10
                reasons.append("Aligns with your skills (+10 pts)")

            deterministic_score = min(100, interest_pts + avail_pts + loc_pts + skill_pts)

            # AI Semantic Embedding Similarity (30% weight)
            act_embedding = activity.embedding if (activity and activity.embedding is not None) else (update_activity_embedding(activity.activity_id, db) if activity else None)
            semantic_sim = compute_cosine_similarity(user_embedding, act_embedding)
            semantic_pts = round(semantic_sim * 30.0, 1)

            hybrid_score = min(100, max(0, round((deterministic_score * 0.70) + ((semantic_sim * 100.0) * 0.30))))
            if semantic_sim >= 0.40:
                reasons.append(f"AI semantic interest affinity ({int(round(semantic_sim * 100))}%)")

            # Host Reputation Trust Signal
            host_rep = _get_user_reputation_summary(ev.host_id, db)
            host_trust_score = min(100, max(0, int(round((host_rep.average_rating / 5.0) * 100)))) if host_rep.total_reviews > 0 else 75
            if host_rep.average_rating >= 4.5 and host_rep.total_reviews > 0:
                reasons.append(f"Organized by top-rated host ({host_rep.average_rating}★)")

            if hybrid_score >= min_score or deterministic_score >= min_score:
                part_count = db.query(models.EventParticipant).filter(models.EventParticipant.event_id == ev.event_id, models.EventParticipant.status == "CONFIRMED").count()
                rem_spots = max(0, ev.max_capacity - part_count)
                cost_per_person = float(ev_booking.total_amount) / max(part_count, 1) if ev_booking else 0.0

                recommendations.append(
                    schemas.RecommendationItem(
                        type="EVENT",
                        id=ev.event_id,
                        event_id=ev.event_id,
                        activity_id=ev.activity_id,
                        title=ev.title,
                        score=hybrid_score,
                        reasons=reasons,
                        locality=ev_locality if ev_locality else None,
                        event_date=ev.event_date,
                        start_time=ev.start_time,
                        end_time=ev.end_time,
                        remaining_spots=rem_spots,
                        per_person_cost=cost_per_person if cost_per_person > 0 else None,
                        trust_score=host_trust_score,
                        reputation=host_rep,
                    )
                )

    # ------------------------------------------------------------------------
    # 3. ACTIVITY RECOMMENDATIONS
    # ------------------------------------------------------------------------
    if target_type in ["ALL", "ACTIVITY", "ACTIVITIES"]:
        activities = db.query(models.Activity).all()
        for act in activities:
            act_interest = db.query(models.Interest).filter(models.Interest.interest_id == act.interest_id).first()

            interest_pts = 0
            skill_pts = 0
            reasons = []

            if act.interest_id in user_interest_ids:
                interest_pts = 50
                int_name = act_interest.name if act_interest else "interest"
                reasons.append(f"Direct match for your {int_name} interest (+50 pts)")
            elif act_interest and act_interest.category.lower() in user_interest_categories:
                interest_pts = 25
                reasons.append(f"Matches your {act_interest.category} category (+25 pts)")

            if act_interest and (act_interest.category.lower() in user_skill_categories or any(s in act.title.lower() for s in user_skill_names)):
                skill_pts = 20
                reasons.append("Aligns with your skills (+20 pts)")

            det_score = min(100, interest_pts + skill_pts)

            act_embedding = act.embedding if act.embedding is not None else update_activity_embedding(act.activity_id, db)
            semantic_sim = compute_cosine_similarity(user_embedding, act_embedding)
            hybrid_score = min(100, max(0, round((det_score * 0.70) + ((semantic_sim * 100.0) * 0.30))))

            if semantic_sim >= 0.40:
                reasons.append(f"Semantic activity match ({int(round(semantic_sim * 100))}%)")

            if hybrid_score >= min_score or det_score >= min_score:
                recommendations.append(
                    schemas.RecommendationItem(
                        type="ACTIVITY",
                        id=act.activity_id,
                        activity_id=act.activity_id,
                        title=act.title,
                        score=hybrid_score,
                        reasons=reasons,
                        locality=None,
                        trust_score=None,
                    )
                )

    # ------------------------------------------------------------------------
    # 4. PEOPLE RECOMMENDATIONS (Compatible Peers)
    # ------------------------------------------------------------------------
    if target_type in ["ALL", "PEOPLE", "USERS"]:
        people_res = match_people(
            activity_id=None,
            interest_id=None,
            locality=effective_locality if effective_locality else None,
            day_of_week=None,
            min_score=min_score,
            limit=limit,
            current_user=current_user,
            db=db,
        )
        for cand in people_res.matches:
            recommendations.append(
                schemas.RecommendationItem(
                    type="PEOPLE",
                    id=cand.user_id,
                    user_id=cand.user_id,
                    title=cand.display_name,
                    score=cand.match_score,
                    reasons=cand.match_reasons,
                    locality=cand.approx_locality,
                    trust_score=cand.trust_score,
                    reputation=cand.reputation,
                )
            )

    # Sort globally by (score DESC, trust_score DESC)
    recommendations.sort(key=lambda r: (r.score, r.trust_score or 0), reverse=True)
    recommendations = recommendations[:limit]

    return schemas.RecommendationResponse(
        total_recommendations=len(recommendations),
        user_locality=effective_locality if effective_locality else None,
        recommendations=recommendations,
    )


# ============================================================================
# 9.6 DO SOMETHING NOW ENGINE (Real-Time Feasibility & Viable Actions)
# ============================================================================

@app.get(
    "/do-something-now",
    response_model=schemas.DoSomethingNowResponse,
    tags=["Recommendations"],
    summary="Do Something Now: Real-time viable experiences (Join active events vs Create group/activity)",
)
def do_something_now(
    target_date: Optional[date] = Query(None, description="Target evaluation date (defaults to today)"),
    target_time: Optional[time] = Query(None, description="Target evaluation time (defaults to current time)"),
    locality: Optional[str] = Query(None, description="Locality override for real-time feasibility"),
    interest_id: Optional[int] = Query(None, description="Focus on a specific interest"),
    limit: int = Query(default=10, ge=1, le=100, description="Max viable options to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    eval_date = target_date or date.today()
    eval_time = target_time or datetime.now().time()
    day_name = eval_date.strftime("%A")
    day_name_lower = day_name.lower().strip()

    # 1. Fetch User Profile & Availability Schedule
    user_profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    effective_locality = locality.strip() if locality else (user_profile.approx_locality.strip() if user_profile and user_profile.approx_locality else "")

    user_avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id == current_user.user_id).all()
    user_avail_days = {a.day_of_week.lower().strip() for a in user_avails}

    # Evaluate whether user is available right now
    if not user_avails:
        user_available_now = True  # Flexible by default if no constraints configured
    else:
        is_day_match = (day_name_lower in user_avail_days) or ("weekend" in user_avail_days and day_name_lower in ["saturday", "sunday"])
        if not is_day_match:
            user_available_now = False
        else:
            # Check if any matching day has time window enclosing or close to eval_time
            matched_avail = [a for a in user_avails if a.day_of_week.lower().strip() == day_name_lower or ("weekend" in a.day_of_week.lower().strip() and day_name_lower in ["saturday", "sunday"])]
            has_time_restriction = any(a.start_time and a.end_time for a in matched_avail)
            if not has_time_restriction:
                user_available_now = True
            else:
                user_available_now = any(
                    (a.start_time is None or a.start_time <= eval_time) and (a.end_time is None or a.end_time >= eval_time)
                    for a in matched_avail
                )

    # 2. Target Interests Resolution
    if interest_id:
        target_interest_ids = [interest_id]
    else:
        user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).all()
        target_interest_ids = [ui.interest_id for ui in user_interests]

    # If no specific user interests, fallback to all catalog interests
    if not target_interest_ids:
        all_ints = db.query(models.Interest.interest_id).all()
        target_interest_ids = [i[0] for i in all_ints]

    options: List[schemas.DoSomethingNowOption] = []
    seen_activity_ids = set()

    # ------------------------------------------------------------------------
    # 3. SCAN REAL-TIME EVENTS (Action: JOIN)
    # ------------------------------------------------------------------------
    user_confirmed_event_ids = {
        ep.event_id
        for ep in db.query(models.EventParticipant.event_id)
        .filter(models.EventParticipant.user_id == current_user.user_id, models.EventParticipant.status == "CONFIRMED")
        .all()
    }

    events = (
        db.query(models.Event)
        .filter(
            models.Event.host_id != current_user.user_id,
            models.Event.status.in_(["PUBLISHED", "FULL"]),
            models.Event.event_date == eval_date,
            models.Event.end_time >= eval_time,
        )
        .all()
    )

    for ev in events:
        if ev.event_id in user_confirmed_event_ids:
            continue

        activity = db.query(models.Activity).filter(models.Activity.activity_id == ev.activity_id).first()
        if not activity:
            continue

        act_interest = db.query(models.Interest).filter(models.Interest.interest_id == activity.interest_id).first()
        interest_match = (activity.interest_id in target_interest_ids)
        if interest_id is not None and not interest_match:
            continue

        # Capacity & Spots
        part_count = db.query(models.EventParticipant).filter(
            models.EventParticipant.event_id == ev.event_id,
            models.EventParticipant.status == "CONFIRMED",
        ).count()
        remaining_spots = max(0, ev.max_capacity - part_count)
        is_feasible = (remaining_spots > 0)

        # Locality Resolution
        ev_booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == ev.event_id).first()
        ev_slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == ev_booking.slot_id).first() if ev_booking else None
        ev_venue = db.query(models.Venue).filter(models.Venue.venue_id == ev_slot.venue_id).first() if ev_slot else None

        host_prof = db.query(models.Profile).filter(models.Profile.user_id == ev.host_id).first()
        ev_locality = ev_venue.locality if ev_venue else (host_prof.approx_locality if host_prof and host_prof.approx_locality else "")

        loc_pts = 0
        if effective_locality and ev_locality:
            eff_lower = effective_locality.lower()
            ev_lower = ev_locality.lower()
            if eff_lower in ev_lower or ev_lower in eff_lower:
                loc_pts = 25
            else:
                eff_toks = set(eff_lower.replace(",", " ").split())
                ev_toks = set(ev_lower.replace(",", " ").split())
                if eff_toks.intersection(ev_toks):
                    loc_pts = 15

        # Timing Score
        time_pts = 30 if ev.start_time <= eval_time <= ev.end_time else (25 if ev.start_time >= eval_time else 10)
        interest_pts = 35 if interest_match else 15
        avail_pts = 10 if user_available_now else -15

        total_score = min(100, max(10, interest_pts + time_pts + loc_pts + avail_pts - (30 if not is_feasible else 0)))

        reasons = []
        int_name = act_interest.name if act_interest else "activity"
        if is_feasible:
            action_text = "JOIN"
            reason_text = f"Matches your {int_name} interest and is starting today with {remaining_spots} open spot(s)"
            reasons.append(f"Direct match for {int_name}")
            reasons.append(f"Happening today ({ev.start_time.strftime('%H:%M')} - {ev.end_time.strftime('%H:%M')})")
            if loc_pts >= 15:
                reasons.append(f"Nearby at {ev_locality}")
            if not user_available_now:
                reasons.append("Outside your saved availability schedule")
        else:
            action_text = "FULL"
            reason_text = f"Event is at full capacity ({ev.max_capacity}/{ev.max_capacity} spots taken)"
            reasons.append("Event is currently full")

        cost_per_person = (float(ev_booking.total_amount) / max(part_count, 1)) if ev_booking else 0.0

        options.append(
            schemas.DoSomethingNowOption(
                type="EVENT",
                action=action_text,
                title=ev.title,
                score=total_score,
                feasible=is_feasible,
                reason=reason_text,
                reasons=reasons,
                event_id=ev.event_id,
                activity_id=ev.activity_id,
                interest_id=activity.interest_id,
                interest_name=int_name,
                locality=ev_locality if ev_locality else None,
                event_date=ev.event_date,
                start_time=ev.start_time,
                end_time=ev.end_time,
                remaining_spots=remaining_spots,
                cost_per_person=cost_per_person if cost_per_person > 0 else None,
                available_peers_count=part_count,
                available_venues_count=1 if ev_venue else 0,
            )
        )
        seen_activity_ids.add(ev.activity_id)

    # ------------------------------------------------------------------------
    # 4. SCAN FEASIBLE ACTIVITY CREATION (Action: CREATE)
    # ------------------------------------------------------------------------
    activities = db.query(models.Activity).filter(models.Activity.interest_id.in_(target_interest_ids)).all()
    if not activities:
        activities = db.query(models.Activity).limit(10).all()

    for act in activities:
        act_interest = db.query(models.Interest).filter(models.Interest.interest_id == act.interest_id).first()
        int_name = act_interest.name if act_interest else "activity"

        # Check Available Peers Right Now (Users with interest + availability today)
        peer_query = (
            db.query(models.User.user_id)
            .join(models.UserInterest, models.User.user_id == models.UserInterest.user_id)
            .join(models.UserAvailability, models.User.user_id == models.UserAvailability.user_id)
            .filter(
                models.User.user_id != current_user.user_id,
                models.User.is_active.is_(True),
                models.UserInterest.interest_id == act.interest_id,
                or_(
                    func.lower(models.UserAvailability.day_of_week) == day_name_lower,
                    func.lower(models.UserAvailability.day_of_week) == "weekend" if day_name_lower in ["saturday", "sunday"] else False,
                ),
            )
        )
        available_peers_count = peer_query.distinct().count()

        # Check Available Venue Slots Right Now
        slot_query = (
            db.query(models.VenueSlot)
            .join(models.Venue, models.VenueSlot.venue_id == models.Venue.venue_id)
            .join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id)
            .filter(
                models.VenueActivity.activity_id == act.activity_id,
                models.VenueSlot.slot_date == eval_date,
                models.VenueSlot.status == "AVAILABLE",
                models.VenueSlot.end_time >= eval_time,
            )
        )
        if effective_locality:
            # Boost locality match
            local_slot_query = slot_query.filter(func.lower(models.Venue.locality).contains(effective_locality.lower()))
            local_slots = local_slot_query.all()
            if local_slots:
                venue_slots = local_slots
            else:
                venue_slots = slot_query.all()
        else:
            venue_slots = slot_query.all()

        available_venues_count = len(venue_slots)
        top_slot = venue_slots[0] if venue_slots else None
        top_venue = db.query(models.Venue).filter(models.Venue.venue_id == top_slot.venue_id).first() if top_slot else None

        is_create_feasible = (available_peers_count >= 1 or available_venues_count >= 1)

        # Score calculation for Creation
        score_interest = 40
        score_peers = min(25, available_peers_count * 10)
        score_venues = min(25, available_venues_count * 12)
        score_avail = 10 if user_available_now else -15

        if is_create_feasible:
            act_score = min(95, max(20, score_interest + score_peers + score_venues + score_avail))
            action_text = "CREATE"
            reason_text = f"No active event today, but {available_peers_count} compatible player(s) and {available_venues_count} venue slot(s) are available now"
            reasons = [
                f"Matches your {int_name} interest",
                f"{available_peers_count} compatible player(s) available today",
                f"{available_venues_count} bookable venue slot(s) available today",
            ]
            if not user_available_now:
                reasons.append("Outside your saved availability schedule")
        else:
            act_score = max(10, score_interest + score_avail - 25)
            action_text = "NOT_FEASIBLE"
            reason_text = f"No active event, and no available venue slots or peers found nearby right now"
            reasons = [
                f"Matches interest '{int_name}'",
                "No compatible peers available today",
                "No bookable venue slots available today",
            ]

        options.append(
            schemas.DoSomethingNowOption(
                type="ACTIVITY",
                action=action_text,
                title=act.title,
                score=act_score,
                feasible=is_create_feasible,
                reason=reason_text,
                reasons=reasons,
                activity_id=act.activity_id,
                interest_id=act.interest_id,
                interest_name=int_name,
                locality=top_venue.locality if top_venue else (effective_locality if effective_locality else None),
                event_date=eval_date,
                start_time=top_slot.start_time if top_slot else None,
                end_time=top_slot.end_time if top_slot else None,
                cost_per_person=float(top_slot.price_total) if top_slot else None,
                available_peers_count=available_peers_count,
                available_venues_count=available_venues_count,
                suggested_slot_id=top_slot.slot_id if top_slot else None,
                suggested_venue_name=top_venue.name if top_venue else None,
            )
        )

    # ------------------------------------------------------------------------
    # 5. RANK & SORT
    # ------------------------------------------------------------------------
    # Priority order: Feasible first -> Score DESC -> Existing JOINABLE events tie-breaker
    options.sort(key=lambda x: (1 if x.feasible else 0, x.score, 1 if x.action == "JOIN" else 0), reverse=True)
    options = options[:limit]

    return schemas.DoSomethingNowResponse(
        target_date=eval_date,
        target_time=eval_time,
        day_of_week=day_name,
        user_locality=effective_locality if effective_locality else None,
        user_available_now=user_available_now,
        total_options=len(options),
        options=options,
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

    initial_count = 1
    if req.initial_member_ids:
        for uid in set(req.initial_member_ids):
            if uid != current_user.user_id:
                u_exists = db.query(models.User).filter(models.User.user_id == uid, models.User.is_active.is_(True)).first()
                if u_exists:
                    db.add(
                        models.CommunityMember(
                            community_id=community.community_id,
                            user_id=uid,
                            role="MEMBER",
                        )
                    )
                    initial_count += 1

    db.commit()
    db.refresh(community)

    return schemas.CommunityResponse(
        community_id=community.community_id,
        name=community.name,
        description=community.description,
        created_by=community.created_by,
        member_count=initial_count,
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


@app.get(
    "/communities/{community_id}/health",
    response_model=schemas.CommunityHealthResponse,
    tags=["Communities"],
    summary="Get deterministic community health metrics and score",
)
def get_community_health(
    community_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Read-only community health inspection:
    - Authenticates the requester
    - Verifies community exists
    - Ensures requester is an enrolled community member
    - Computes and returns deterministic health metrics
    """
    comm = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    is_member = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == current_user.user_id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this community to access its health metrics",
        )

    return _compute_community_health(comm, db)


@app.get(
    "/communities/{community_id}/health/trend",
    response_model=schemas.CommunityHealthTrendResponse,
    tags=["Communities"],
    summary="Get deterministic community health trend and period comparison",
)
def get_community_health_trend(
    community_id: int,
    window_days: int = Query(default=30, ge=7, le=90, description="Evaluation window size in days"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Read-only community health trend comparison:
    - Authenticates the requester
    - Verifies community exists (404)
    - Ensures requester is an enrolled community member (403)
    - Computes and returns deterministic health trend across consecutive time windows
    """
    comm = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    is_member = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == current_user.user_id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this community to access its health trend",
        )

    return _compute_community_health_trend(comm, db, window_days=window_days)


@app.get(
    "/communities/{community_id}/lifecycle",
    response_model=schemas.CommunityLifecycleInsightResponse,
    tags=["Communities"],
    summary="Get AI Community Lifecycle Intelligence and strategic engagement insight",
)
def get_community_lifecycle(
    community_id: int,
    window_days: int = Query(default=30, ge=7, le=90, description="Evaluation window size in days"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Read-only community lifecycle intelligence:
    - Authenticates the requester
    - Verifies community exists (404)
    - Ensures requester is an enrolled community member (403)
    - Calls _generate_community_lifecycle_insight(...)
    - Validates with Pydantic response schema
    - Zero database modifications
    """
    comm = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    is_member = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == current_user.user_id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this community to access its lifecycle insights",
        )

    return _generate_community_lifecycle_insight(comm, db, window_days=window_days)


@app.get(
    "/communities/{community_id}/recommendations",
    response_model=schemas.CommunityActionRecommendationsResponse,
    tags=["Communities"],
    summary="Get tactical AI action recommendations grounded in community lifecycle state",
)
def get_community_recommendations(
    community_id: int,
    window_days: int = Query(default=30, ge=7, le=90, description="Evaluation window size in days"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Read-only community action recommendations:
    - Authenticates the requester
    - Verifies community exists (404)
    - Ensures requester is an enrolled community member (403)
    - Calls _generate_community_action_recommendations(...)
    - Validates with Pydantic response schema
    - Zero database modifications
    """
    comm = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not comm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")

    is_member = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == current_user.user_id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this community to access its recommendations",
        )

    return _generate_community_action_recommendations(comm, db, window_days=window_days)





@app.post(
    "/events/{event_id}/feedback",
    response_model=schemas.FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
    summary="Submit peer rating and review for a completed event",
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

    if event.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feedback can only be submitted for COMPLETED events (current status: {event.status})",
        )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted feedback for this event",
        )

    fb = models.Feedback(
        event_id=event_id,
        reviewer_id=current_user.user_id,
        rating=req.rating,
        comment=req.comment.strip() if req.comment else None,
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


def _calculate_user_reputation(user_id: int, db: Session) -> schemas.UserReputationResponse:
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    profile = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
    display_name = profile.display_name if (profile and profile.display_name) else user.email.split("@")[0]

    # Completed events where the user was a confirmed participant or host
    completed_events = (
        db.query(models.EventParticipant)
        .join(models.Event, models.EventParticipant.event_id == models.Event.event_id)
        .filter(
            models.EventParticipant.user_id == user_id,
            models.EventParticipant.status == "CONFIRMED",
            models.Event.status == "COMPLETED",
        )
        .count()
    )

    # Events user participated in
    event_ids = [
        row[0]
        for row in db.query(models.EventParticipant.event_id)
        .filter(
            models.EventParticipant.user_id == user_id,
            models.EventParticipant.status == "CONFIRMED",
        )
        .all()
    ]

    # Feedback on those events from peer participants
    feedbacks = (
        db.query(models.Feedback)
        .filter(
            models.Feedback.event_id.in_(event_ids),
            models.Feedback.reviewer_id != user_id,
        )
        .all()
        if event_ids
        else []
    )

    total_reviews = len(feedbacks)
    average_rating = round(sum(f.rating for f in feedbacks) / total_reviews, 2) if total_reviews > 0 else 0.0

    five_star = sum(1 for f in feedbacks if f.rating == 5)
    four_star = sum(1 for f in feedbacks if f.rating == 4)
    three_star = sum(1 for f in feedbacks if f.rating == 3)
    two_star = sum(1 for f in feedbacks if f.rating == 2)
    one_star = sum(1 for f in feedbacks if f.rating == 1)

    return schemas.UserReputationResponse(
        user_id=user_id,
        display_name=display_name,
        average_rating=average_rating,
        total_reviews=total_reviews,
        feedback_count=total_reviews,
        five_star_count=five_star,
        four_star_count=four_star,
        three_star_count=three_star,
        two_star_count=two_star,
        one_star_count=one_star,
        completed_events=completed_events,
    )


@app.get(
    "/users/me/reputation",
    response_model=schemas.UserReputationResponse,
    tags=["Reputation"],
    summary="Get reputation summary for authenticated user",
)
def get_my_reputation(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _calculate_user_reputation(current_user.user_id, db)


@app.get(
    "/users/{user_id}/reputation",
    response_model=schemas.UserReputationResponse,
    tags=["Reputation"],
    summary="Get reputation and trust summary for a specific user",
)
def get_user_reputation(
    user_id: int,
    db: Session = Depends(get_db),
):
    return _calculate_user_reputation(user_id, db)


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

    # 4. Hybrid Deterministic + Semantic People Matching
    my_user_id = current_user.user_id if current_user else 0
    my_interests = (
        {ui.interest_id for ui in db.query(models.UserInterest).filter(models.UserInterest.user_id == my_user_id).all()}
        if current_user else set()
    )
    my_avails = (
        {a.day_of_week.lower().strip() for a in db.query(models.UserAvailability).filter(models.UserAvailability.user_id == my_user_id).all()}
        if current_user else set()
    )

    query_embedding = generate_embedding(req.query)

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

        deterministic_score = min(100, interest_pts + avail_pts + loc_pts + skill_pts)

        # E. AI Semantic Cosine Similarity (30% weight)
        c_embedding = c_profile.embedding if (c_profile and c_profile.embedding is not None) else update_user_embedding(cand.user_id, db)
        semantic_sim = compute_cosine_similarity(query_embedding, c_embedding)
        semantic_pts = round(semantic_sim * 30.0, 1)

        hybrid_score = min(100, max(0, round((deterministic_score * 0.70) + ((semantic_sim * 100.0) * 0.30))))

        if semantic_sim >= 0.35:
            reasons.append(f"AI semantic query affinity: {int(round(semantic_sim * 100))}% (+{semantic_pts} pts)")

        # F. REPUTATION & TRUST SIGNAL
        rep_summary = _get_user_reputation_summary(cand.user_id, db)
        if rep_summary.total_reviews > 0:
            trust_score = min(100, max(0, int(round((rep_summary.average_rating / 5.0) * 100))))
            if rep_summary.average_rating >= 4.5:
                reasons.append(f"Highly-rated peer ({rep_summary.average_rating}★ from {rep_summary.total_reviews} reviews)")
            elif rep_summary.average_rating >= 4.0:
                reasons.append(f"Well-rated participant ({rep_summary.average_rating}★)")
        else:
            trust_score = 75

        if hybrid_score >= 10 or deterministic_score >= 10:
            matched_candidates.append(
                schemas.PeopleMatchCandidate(
                    user_id=cand.user_id,
                    display_name=c_profile.display_name if c_profile else cand.email.split("@")[0].capitalize(),
                    avatar_url=c_profile.avatar_url if c_profile else None,
                    approx_locality=c_profile.approx_locality if c_profile else None,
                    match_score=hybrid_score,
                    deterministic_score=deterministic_score,
                    semantic_similarity=round(float(semantic_sim), 4),
                    trust_score=trust_score,
                    reputation=rep_summary,
                    match_breakdown={
                        "interest": interest_pts,
                        "availability": avail_pts,
                        "location": loc_pts,
                        "skill": skill_pts,
                        "semantic": semantic_pts,
                        "deterministic_total": deterministic_score,
                        "total": hybrid_score,
                    },
                    match_reasons=reasons,
                    shared_interests=shared_int_names if shared_int_names else ([target_interest.name] if (target_interest and target_interest.interest_id in c_interest_ids) else []),
                    relevant_skills=relevant_skills_display,
                    shared_availability=shared_avail_display,
                )
            )


    matched_candidates.sort(key=lambda x: (x.match_score, x.trust_score or 0), reverse=True)
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


# ============================================================================
# 12. AI GROUP FORMATION ENGINE
# ============================================================================

def _resolve_target_date_and_times(day_str: Optional[str], time_str: Optional[str]):
    today = date.today()
    target_date = today + timedelta(days=2)

    if day_str:
        d_clean = day_str.lower().strip()
        days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        if d_clean == "today":
            target_date = today
        elif d_clean == "tomorrow":
            target_date = today + timedelta(days=1)
        elif d_clean in days_map:
            target_dow = days_map[d_clean]
            current_dow = today.weekday()
            days_ahead = (target_dow - current_dow) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = today + timedelta(days=days_ahead)
        elif "weekend" in d_clean:
            days_ahead = (5 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = today + timedelta(days=days_ahead)

    # Time window resolution
    start_t = time(18, 0)
    end_t = time(20, 0)
    if time_str:
        t_clean = time_str.lower().strip()
        if "morning" in t_clean:
            start_t = time(7, 0)
            end_t = time(9, 0)
        elif "afternoon" in t_clean:
            start_t = time(14, 0)
            end_t = time(16, 0)
        elif "evening" in t_clean:
            start_t = time(18, 0)
            end_t = time(20, 0)
        elif "night" in t_clean:
            start_t = time(20, 0)
            end_t = time(22, 0)

    return target_date, start_t, end_t


def _build_group_proposal_response(
    proposal: models.GroupProposal,
    db: Session,
    intent_understood: Optional[schemas.AIIntentResponse] = None
) -> schemas.GroupProposalResponse:
    initiator_profile = db.query(models.Profile).filter(models.Profile.user_id == proposal.initiator_user_id).first()
    initiator_user = db.query(models.User).filter(models.User.user_id == proposal.initiator_user_id).first()
    initiator_name = (
        initiator_profile.display_name if (initiator_profile and initiator_profile.display_name)
        else (initiator_user.email.split("@")[0].capitalize() if initiator_user else "Member")
    )

    activity = db.query(models.Activity).filter(models.Activity.activity_id == proposal.activity_id).first() if proposal.activity_id else None
    suggested_venue = db.query(models.Venue).filter(models.Venue.venue_id == proposal.suggested_venue_id).first() if proposal.suggested_venue_id else None

    members_resp = []
    for m in proposal.members:
        m_profile = db.query(models.Profile).filter(models.Profile.user_id == m.user_id).first()
        m_user = db.query(models.User).filter(models.User.user_id == m.user_id).first()
        d_name = (
            m_profile.display_name if (m_profile and m_profile.display_name)
            else (m_user.email.split("@")[0].capitalize() if m_user else f"Member #{m.user_id}")
        )
        members_resp.append(
            schemas.GroupProposalMemberResponse(
                user_id=m.user_id,
                display_name=d_name,
                avatar_url=m_profile.avatar_url if m_profile else None,
                approx_locality=m_profile.approx_locality if m_profile else None,
                status=m.status,
                compatibility_score=m.compatibility_score,
                invited_at=m.invited_at,
                responded_at=m.responded_at,
            )
        )

    # Initiator first, then sorted by compatibility score descending
    members_resp.sort(key=lambda x: (x.status != "ACCEPTED", -(x.compatibility_score or 0)))

    return schemas.GroupProposalResponse(
        proposal_id=proposal.proposal_id,
        initiator_user_id=proposal.initiator_user_id,
        initiator_name=initiator_name,
        activity_id=proposal.activity_id,
        activity_title=activity.title if activity else None,
        title=proposal.title,
        description=proposal.description,
        target_size=proposal.target_size,
        min_required_size=proposal.min_required_size,
        proposed_date=proposal.proposed_date,
        proposed_start_time=proposal.proposed_start_time,
        proposed_end_time=proposal.proposed_end_time,
        target_locality=proposal.target_locality,
        suggested_venue_id=proposal.suggested_venue_id,
        suggested_venue_name=suggested_venue.name if suggested_venue else None,
        status=proposal.status,
        converted_event_id=proposal.converted_event_id,
        expires_at=proposal.expires_at,
        created_at=proposal.created_at,
        members=members_resp,
        intent_understood=intent_understood,
    )


@app.post(
    "/ai/groups/propose",
    response_model=schemas.GroupProposalResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["AI Engine"],
    summary="Formulate and create an AI-suggested temporary Group Proposal with invited matching candidates",
)
def propose_ai_group(
    req: schemas.AIGroupProposeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. AI Intent Understanding
    intent_data = understand_user_intent(req.query)

    # 2. Resolve Target Activity & Interest
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
    else:
        my_prof = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
        if my_prof and my_prof.approx_locality:
            search_locality = my_prof.approx_locality.strip()

    # 4. Resolve Dates and Times
    prop_date, prop_start_t, prop_end_t = _resolve_target_date_and_times(intent_data.day_of_week, intent_data.time_of_day)

    # 5. Resolve Cohort Sizes
    target_sz = req.target_size or intent_data.group_size or 4
    min_sz = req.min_required_size or max(2, target_sz - 1)
    if min_sz > target_sz:
        min_sz = target_sz

    # 6. Check for duplicate active proposal by same initiator for same activity & date
    existing_active = db.query(models.GroupProposal).filter(
        models.GroupProposal.initiator_user_id == current_user.user_id,
        models.GroupProposal.activity_id == (target_activity.activity_id if target_activity else None),
        models.GroupProposal.proposed_date == prop_date,
        models.GroupProposal.status.in_(["PROPOSED", "CONFIRMED"]),
    ).first()
    if existing_active:
        return _build_group_proposal_response(existing_active, db, intent_understood=intent_data)

    # 7. Candidate Discovery & Hybrid Matching
    query_embedding = generate_embedding(req.query)
    my_interests = {ui.interest_id for ui in db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).all()}
    my_avails = {a.day_of_week.lower().strip() for a in db.query(models.UserAvailability).filter(models.UserAvailability.user_id == current_user.user_id).all()}

    candidates = (
        db.query(models.User)
        .filter(models.User.user_id != current_user.user_id, models.User.is_active.is_(True))
        .all()
    )

    scored_candidates = []
    for cand in candidates:
        c_profile = db.query(models.Profile).filter(models.Profile.user_id == cand.user_id).first()
        c_user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id == cand.user_id).all()
        c_interest_ids = {ui.interest_id for ui in c_user_interests}

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

        # Interest
        if target_interest:
            if target_interest.interest_id in c_interest_ids:
                interest_pts = 40
            elif my_interests.intersection(c_interest_ids):
                interest_pts = min(30, len(my_interests.intersection(c_interest_ids)) * 15)
        elif my_interests.intersection(c_interest_ids):
            interest_pts = min(40, len(my_interests.intersection(c_interest_ids)) * 20)

        # Availability
        if intent_data.day_of_week:
            target_day_clean = intent_data.day_of_week.lower().strip()
            if target_day_clean in c_days or any(target_day_clean in d for d in c_days):
                avail_pts = 30
        elif my_avails:
            overlap = my_avails.intersection(c_days)
            avail_pts = 30 if len(overlap) >= 2 else (20 if len(overlap) == 1 else 0)

        # Locality
        c_loc = c_profile.approx_locality.strip() if (c_profile and c_profile.approx_locality) else ""
        if search_locality and c_loc:
            s_low, c_low = search_locality.lower(), c_loc.lower()
            if s_low in c_low or c_low in s_low:
                loc_pts = 20
            elif set(s_low.replace(",", " ").split()).intersection(set(c_low.replace(",", " ").split())):
                loc_pts = 10

        # Skill
        offered_skills = [s for s in c_skills if s.is_offering]
        for s in offered_skills:
            if target_interest and (s.category.lower() == target_interest.category.lower() or s.name.lower() in target_interest.name.lower()):
                skill_pts = 10
        if skill_pts == 0 and offered_skills:
            skill_pts = 5

        deterministic_score = min(100, interest_pts + avail_pts + loc_pts + skill_pts)

        # Semantic embedding
        c_embedding = c_profile.embedding if (c_profile and c_profile.embedding is not None) else update_user_embedding(cand.user_id, db)
        semantic_sim = compute_cosine_similarity(query_embedding, c_embedding)
        hybrid_score = min(100, max(0, round((deterministic_score * 0.70) + ((semantic_sim * 100.0) * 0.30))))

        if hybrid_score >= 10 or deterministic_score >= 10:
            scored_candidates.append({
                "user_id": cand.user_id,
                "hybrid_score": hybrid_score,
                "deterministic_score": deterministic_score,
                "semantic_sim": semantic_sim,
            })

    scored_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
    num_to_invite = max(1, target_sz - 1)
    selected_candidates = scored_candidates[:num_to_invite]

    # 8. Venue Recommendation
    venues_q = db.query(models.Venue).filter(models.Venue.status == "ACTIVE")
    if search_locality:
        base_loc = search_locality.split(",")[0].strip()
        venues_q = venues_q.filter(or_(models.Venue.locality.ilike(f"%{base_loc}%"), models.Venue.address.ilike(f"%{base_loc}%")))
    if target_activity:
        venues_q = venues_q.join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id).filter(
            models.VenueActivity.activity_id == target_activity.activity_id
        )
    suggested_venue = venues_q.first()

    # 9. Create GroupProposal & Members
    title = req.custom_title or f"{intent_data.day_of_week or 'Upcoming'} {target_activity.title if target_activity else (intent_data.activity or 'Activity')} ({target_sz} Players)"
    proposal = models.GroupProposal(
        initiator_user_id=current_user.user_id,
        activity_id=target_activity.activity_id if target_activity else None,
        title=title,
        description=f"AI-suggested cohort for '{req.query}' in {search_locality or 'nearby area'}.",
        target_size=target_sz,
        min_required_size=min_sz,
        proposed_date=prop_date,
        proposed_start_time=prop_start_t,
        proposed_end_time=prop_end_t,
        target_locality=search_locality,
        suggested_venue_id=suggested_venue.venue_id if suggested_venue else None,
        status="PROPOSED",
        expires_at=datetime.now() + timedelta(hours=24),
    )
    db.add(proposal)
    db.flush()

    # Add Initiator as ACCEPTED
    db.add(
        models.GroupProposalMember(
            proposal_id=proposal.proposal_id,
            user_id=current_user.user_id,
            status="ACCEPTED",
            compatibility_score=100,
            responded_at=datetime.now(),
        )
    )

    # Add Selected Candidate Peers as INVITED
    for c in selected_candidates:
        db.add(
            models.GroupProposalMember(
                proposal_id=proposal.proposal_id,
                user_id=c["user_id"],
                status="INVITED",
                compatibility_score=c["hybrid_score"],
            )
        )

    db.commit()
    db.refresh(proposal)

    return _build_group_proposal_response(proposal, db, intent_understood=intent_data)


@app.post(
    "/groups/proposals/{proposal_id}/respond",
    response_model=schemas.GroupProposalResponse,
    tags=["AI Engine"],
    summary="Accept or decline an invitation to a temporary group proposal",
)
def respond_to_group_proposal(
    proposal_id: int,
    req: schemas.GroupProposalRespondRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.query(models.GroupProposal).filter(models.GroupProposal.proposal_id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group proposal not found")

    # Expiration check
    now_utc = datetime.now(proposal.expires_at.tzinfo) if proposal.expires_at.tzinfo else datetime.now()
    if proposal.expires_at < now_utc:
        if proposal.status == "PROPOSED":
            proposal.status = "EXPIRED"
            db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This group proposal has expired")

    # Status check
    if proposal.status not in ["PROPOSED", "CONFIRMED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot respond to proposal with status '{proposal.status}'",
        )

    # Membership check
    member = db.query(models.GroupProposalMember).filter(
        models.GroupProposalMember.proposal_id == proposal_id,
        models.GroupProposalMember.user_id == current_user.user_id,
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an invited member of this group proposal",
        )

    # Duplicate response check
    if member.status in ["ACCEPTED", "DECLINED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have already responded with status '{member.status}'",
        )

    # Input validation
    clean_resp = req.response.strip().upper()
    if clean_resp not in ["ACCEPTED", "DECLINED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Response must be either 'ACCEPTED' or 'DECLINED'",
        )

    # Update member status
    member.status = clean_resp
    member.responded_at = datetime.now()
    db.flush()

    # Recalculate accepted count & threshold state transition
    accepted_count = (
        db.query(models.GroupProposalMember)
        .filter(models.GroupProposalMember.proposal_id == proposal_id, models.GroupProposalMember.status == "ACCEPTED")
        .count()
    )

    if accepted_count >= proposal.min_required_size and proposal.status == "PROPOSED":
        proposal.status = "CONFIRMED"

    db.commit()
    db.refresh(proposal)

    return _build_group_proposal_response(proposal, db)


@app.get(
    "/groups/proposals/me",
    response_model=List[schemas.GroupProposalResponse],
    tags=["AI Engine"],
    summary="List all group proposals where current user is initiator or invited member",
)
def list_my_group_proposals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_proposal_ids = [
        r[0]
        for r in db.query(models.GroupProposalMember.proposal_id)
        .filter(models.GroupProposalMember.user_id == current_user.user_id)
        .all()
    ]

    filter_cond = models.GroupProposal.initiator_user_id == current_user.user_id
    if user_proposal_ids:
        filter_cond = or_(filter_cond, models.GroupProposal.proposal_id.in_(user_proposal_ids))

    proposals = (
        db.query(models.GroupProposal)
        .filter(filter_cond)
        .order_by(models.GroupProposal.created_at.desc())
        .all()
    )

    return [_build_group_proposal_response(p, db) for p in proposals]


@app.get(
    "/groups/proposals/{proposal_id}",
    response_model=schemas.GroupProposalResponse,
    tags=["AI Engine"],
    summary="Get details and member status roster of a group proposal",
)
def get_group_proposal(
    proposal_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.query(models.GroupProposal).filter(models.GroupProposal.proposal_id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group proposal not found")

    # Check expiration dynamically
    now_utc = datetime.now(proposal.expires_at.tzinfo) if proposal.expires_at.tzinfo else datetime.now()
    if proposal.expires_at < now_utc and proposal.status == "PROPOSED":
        proposal.status = "EXPIRED"
        db.commit()
        db.refresh(proposal)

    return _build_group_proposal_response(proposal, db)


@app.post(
    "/groups/proposals/{proposal_id}/convert",
    response_model=schemas.EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["AI Engine"],
    summary="Convert a CONFIRMED group proposal into a scheduled Event with enrolled participants",
)
def convert_group_proposal_to_event(
    proposal_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proposal = db.query(models.GroupProposal).filter(models.GroupProposal.proposal_id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group proposal not found")

    # Double conversion check
    if proposal.status == "CONVERTED_TO_EVENT" or proposal.converted_event_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This group proposal has already been converted to Event #{proposal.converted_event_id}",
        )

    # Status check: Must be CONFIRMED
    if proposal.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot convert proposal with status '{proposal.status}'. Proposal must be 'CONFIRMED'.",
        )

    # Initiator authorization check
    if proposal.initiator_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the proposal initiator can convert it to an official scheduled event.",
        )

    # Expiration check
    now_utc = datetime.now(proposal.expires_at.tzinfo) if proposal.expires_at.tzinfo else datetime.now()
    if proposal.expires_at < now_utc:
        proposal.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This group proposal has expired")

    # Accepted members count check
    accepted_members = (
        db.query(models.GroupProposalMember)
        .filter(models.GroupProposalMember.proposal_id == proposal_id, models.GroupProposalMember.status == "ACCEPTED")
        .all()
    )

    if len(accepted_members) < proposal.min_required_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot convert: accepted members ({len(accepted_members)}) is below minimum required ({proposal.min_required_size})",
        )

    # Resolve activity
    activity_id = proposal.activity_id
    if not activity_id:
        first_act = db.query(models.Activity).first()
        activity_id = first_act.activity_id if first_act else 1

    event_date = proposal.proposed_date or (date.today() + timedelta(days=2))
    start_time = proposal.proposed_start_time or time(18, 0)
    end_time = proposal.proposed_end_time or time(20, 0)

    is_full = len(accepted_members) >= proposal.target_size
    event_status = "FULL" if is_full else "PUBLISHED"

    # Create scheduled Event
    new_event = models.Event(
        activity_id=activity_id,
        host_id=proposal.initiator_user_id,
        title=proposal.title,
        event_date=event_date,
        start_time=start_time,
        end_time=end_time,
        max_capacity=proposal.target_size,
        status=event_status,
    )
    db.add(new_event)
    db.flush()

    # Automatically enroll all ACCEPTED cohort members as CONFIRMED EventParticipants
    for member in accepted_members:
        db.add(
            models.EventParticipant(
                event_id=new_event.event_id,
                user_id=member.user_id,
                status="CONFIRMED",
            )
        )

    # Update Proposal
    proposal.converted_event_id = new_event.event_id
    proposal.status = "CONVERTED_TO_EVENT"

    db.commit()
    db.refresh(new_event)
    db.refresh(proposal)

    return _build_event_response(new_event, db)


# ============================================================================
# 13. AI EXPERIENCE GENERATOR ENGINE
# ============================================================================

@app.post(
    "/ai/experiences/generate",
    response_model=schemas.ExperiencePlanResponse,
    tags=["AI Engine"],
    summary="AI Experience Generator: Synthesize verified backend facts into an actionable experience plan",
)
def generate_experience_plan(
    req: schemas.ExperienceGenerateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. AI Intent Understanding from Query
    intent = understand_user_intent(req.query)

    # 2. Activity & Interest Resolution
    target_activity = None
    if req.activity_id:
        target_activity = db.query(models.Activity).filter(models.Activity.activity_id == req.activity_id).first()

    if not target_activity and intent.activity:
        act_clean = intent.activity.strip()
        target_activity = db.query(models.Activity).filter(models.Activity.title.ilike(f"%{act_clean}%")).first()
        if not target_activity:
            target_interest = db.query(models.Interest).filter(models.Interest.name.ilike(f"%{act_clean}%")).first()
            if target_interest:
                target_activity = db.query(models.Activity).filter(models.Activity.interest_id == target_interest.interest_id).first()

    if not target_activity and intent.category:
        target_activity = (
            db.query(models.Activity)
            .join(models.Interest, models.Activity.interest_id == models.Interest.interest_id)
            .filter(models.Interest.category.ilike(f"%{intent.category}%"))
            .first()
        )

    if not target_activity:
        target_activity = db.query(models.Activity).first()
        if not target_activity:
            # Seed an activity if db is empty
            first_int = db.query(models.Interest).first()
            int_id = first_int.interest_id if first_int else 1
            target_activity = models.Activity(interest_id=int_id, title="Badminton Match")
            db.add(target_activity)
            db.commit()
            db.refresh(target_activity)

    act_interest = db.query(models.Interest).filter(models.Interest.interest_id == target_activity.interest_id).first()
    category_name = act_interest.category if act_interest else "Sports"

    # 3. Target Date & Times
    if req.target_date and req.target_time:
        target_date = req.target_date
        start_time = req.target_time
        end_time = time((start_time.hour + 2) % 24, start_time.minute)
    else:
        resolved_date, def_start, def_end = _resolve_target_date_and_times(intent.day_of_week, intent.time_of_day)
        target_date = req.target_date or resolved_date
        start_time = req.target_time or def_start
        end_time = time((start_time.hour + 2) % 24, start_time.minute)

    # 4. Target Locality
    user_prof = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    target_locality = (
        req.locality
        or (intent.location if intent.location and intent.location.lower() != "nearby" else None)
        or (user_prof.approx_locality if user_prof and user_prof.approx_locality else None)
        or "Indiranagar, Bengaluru"
    )

    # 5. Cohort Size
    target_size = req.target_size or intent.group_size or 4

    # 6. Verified Candidate Peers Discovery (Real Users via Matching Engine)
    day_name = target_date.strftime("%A")
    match_resp = match_people(
        activity_id=target_activity.activity_id,
        interest_id=target_activity.interest_id,
        locality=target_locality,
        day_of_week=day_name,
        min_score=10,
        limit=max(1, target_size - 1),
        current_user=current_user,
        db=db,
    )
    cohort_ids = [m.user_id for m in match_resp.matches]
    cohort_names = [m.display_name for m in match_resp.matches]

    # 7. Verified Venue & Slot Discovery (Real Database Facts)
    selected_venue = None
    selected_slot = None
    if req.slot_id:
        selected_slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == req.slot_id).first()
        if selected_slot:
            selected_venue = db.query(models.Venue).filter(models.Venue.venue_id == selected_slot.venue_id).first()
    elif req.venue_id:
        selected_venue = db.query(models.Venue).filter(models.Venue.venue_id == req.venue_id).first()
        if selected_venue:
            selected_slot = (
                db.query(models.VenueSlot)
                .filter(
                    models.VenueSlot.venue_id == selected_venue.venue_id,
                    models.VenueSlot.slot_date == target_date,
                    models.VenueSlot.status == "AVAILABLE",
                )
                .first()
            )

    if not selected_venue:
        base_loc = target_locality.split(",")[0].strip()
        venue_query = (
            db.query(models.Venue)
            .join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id)
            .filter(
                models.VenueActivity.activity_id == target_activity.activity_id,
                models.Venue.status == "ACTIVE",
                models.Venue.locality.ilike(f"%{base_loc}%"),
            )
        )
        selected_venue = venue_query.first()
        if not selected_venue:
            selected_venue = (
                db.query(models.Venue)
                .join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id)
                .filter(models.VenueActivity.activity_id == target_activity.activity_id, models.Venue.status == "ACTIVE")
                .first()
            )

    if selected_venue and not selected_slot:
        selected_slot = (
            db.query(models.VenueSlot)
            .filter(
                models.VenueSlot.venue_id == selected_venue.venue_id,
                models.VenueSlot.slot_date == target_date,
                models.VenueSlot.status == "AVAILABLE",
            )
            .first()
        )

    # 8. Real Pricing Calculation
    if selected_slot:
        total_cost = float(selected_slot.price_total)
        per_person_cost = round(total_cost / max(1, target_size), 2)
        slot_id = selected_slot.slot_id
        start_time = selected_slot.start_time
        end_time = selected_slot.end_time
    else:
        total_cost = None
        per_person_cost = None
        slot_id = None

    # 9. Pack Verified Facts and Call AI Experience Synthesis
    facts = {
        "query": req.query,
        "activity_name": target_activity.title,
        "category": category_name,
        "locality": target_locality,
        "venue_name": selected_venue.name if selected_venue else None,
        "target_size": target_size,
        "start_time_str": start_time.strftime("%H:%M"),
        "end_time_str": end_time.strftime("%H:%M"),
        "suggested_cohort_names": cohort_names,
        "per_person_cost": per_person_cost,
    }
    ai_synthesis = generate_ai_experience_plan(facts)

    # 10. Construct Downstream Action Payload
    action_payload = {
        "query": req.query,
        "activity_id": target_activity.activity_id,
        "target_size": target_size,
        "proposed_date": target_date.isoformat(),
        "proposed_start_time": start_time.strftime("%H:%M:%S"),
        "proposed_end_time": end_time.strftime("%H:%M:%S"),
        "target_locality": target_locality,
        "suggested_venue_id": selected_venue.venue_id if selected_venue else None,
        "custom_title": ai_synthesis["experience_title"],
    }

    agenda_items = [
        schemas.ExperienceAgendaItem(
            time_window=item.get("time_window", "Session"),
            title=item.get("title", "Phase"),
            description=item.get("description", "Activity guidance"),
        )
        for item in ai_synthesis.get("agenda", [])
    ]

    return schemas.ExperiencePlanResponse(
        experience_title=ai_synthesis["experience_title"],
        tagline=ai_synthesis["tagline"],
        activity_id=target_activity.activity_id,
        activity_name=target_activity.title,
        target_date=target_date,
        start_time=start_time,
        end_time=end_time,
        locality=target_locality,
        venue_id=selected_venue.venue_id if selected_venue else None,
        venue_name=selected_venue.name if selected_venue else None,
        venue_address=selected_venue.address if selected_venue else None,
        slot_id=slot_id,
        target_size=target_size,
        per_person_cost=per_person_cost,
        total_cost=total_cost,
        currency="INR",
        why_this_works=ai_synthesis["why_this_works"],
        agenda=agenda_items,
        preparation_checklist=ai_synthesis["preparation_checklist"],
        suggested_cohort_user_ids=cohort_ids,
        suggested_cohort_names=cohort_names,
        action_type="CREATE_PROPOSAL",
        action_payload=action_payload,
        ai_generated=ai_synthesis.get("ai_generated", True),
    )


# ============================================================================
# 14. AI DEMAND RADAR ENGINE
# ============================================================================

@app.get(
    "/ai/demand-radar",
    response_model=schemas.DemandRadarResponse,
    tags=["AI Engine"],
    summary="AI Demand Radar: Detect collective activity demand and underserved local opportunities",
)
def get_demand_radar(
    locality: Optional[str] = Query(None, description="Optional filter by locality, e.g. Indiranagar"),
    activity: Optional[str] = Query(None, description="Optional filter by activity or interest name"),
    day_of_week: Optional[str] = Query(None, description="Optional filter by day of week, e.g. Saturday"),
    min_demand_score: Optional[int] = Query(0, ge=0, le=100, description="Minimum demand score filter"),
    limit: int = Query(20, ge=1, le=100, description="Max clusters to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes aggregate user interests, weekly availability schedules, localities,
    and scheduled event capacity to detect emerging and underserved activity demand.
    """
    # 1. Fetch active users with profile localities, interests, and availability
    user_interest_rows = (
        db.query(
            models.User.user_id,
            models.Profile.approx_locality,
            models.Interest.interest_id,
            models.Interest.name.label("interest_name"),
            models.Interest.category.label("interest_category"),
            models.UserAvailability.day_of_week,
            models.UserAvailability.start_time,
            models.UserAvailability.end_time,
        )
        .join(models.Profile, models.User.user_id == models.Profile.user_id)
        .join(models.UserInterest, models.User.user_id == models.UserInterest.user_id)
        .join(models.Interest, models.UserInterest.interest_id == models.Interest.interest_id)
        .outerjoin(models.UserAvailability, models.User.user_id == models.UserAvailability.user_id)
        .filter(models.User.is_active.is_(True))
        .all()
    )

    # 2. Group into demand clusters: Key = (interest_id, clean_locality, day_of_week)
    clusters_data = {}

    for row in user_interest_rows:
        raw_loc = row.approx_locality or "General"
        # Normalize locality: "Indiranagar, Bengaluru" -> "Indiranagar"
        clean_loc = raw_loc.split(",")[0].strip()
        if not clean_loc:
            clean_loc = "General"

        # Determine day(s) of week
        raw_day = row.day_of_week
        if raw_day:
            day_lower = raw_day.strip().lower()
            if day_lower == "weekend":
                days = ["Saturday", "Sunday"]
            elif day_lower in ["weekday", "weekdays"]:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            else:
                days = [raw_day.strip().capitalize()]
        else:
            days = ["Saturday"]

        # Preferred time slot formatting
        if row.start_time and row.end_time:
            time_str = f"{row.start_time.strftime('%H:%M')}-{row.end_time.strftime('%H:%M')}"
        else:
            time_str = "18:00-20:00"

        for d in days:
            c_key = (row.interest_id, clean_loc, d)
            if c_key not in clusters_data:
                clusters_data[c_key] = {
                    "interest_id": row.interest_id,
                    "interest_name": row.interest_name,
                    "category": row.interest_category,
                    "locality": clean_loc,
                    "day": d,
                    "user_ids": set(),
                    "time_counts": Counter(),
                }
            clusters_data[c_key]["user_ids"].add(row.user_id)
            clusters_data[c_key]["time_counts"][time_str] += 1

    # 3. Cache Activity representations for each Interest
    all_activities = db.query(models.Activity).all()
    activity_by_interest = {}
    for act in all_activities:
        if act.interest_id not in activity_by_interest:
            activity_by_interest[act.interest_id] = act

    # 4. Query and index all active upcoming/current events
    active_events = (
        db.query(models.Event)
        .filter(
            models.Event.status.in_(["PUBLISHED", "DRAFT", "FULL"]),
            models.Event.event_date >= date.today(),
        )
        .all()
    )

    # Index active events by (interest_id, clean_locality_lower, day_name_lower)
    events_by_cluster = defaultdict(list)
    for ev in active_events:
        ev_act = db.query(models.Activity).filter(models.Activity.activity_id == ev.activity_id).first()
        int_id = ev_act.interest_id if ev_act else None
        if not int_id:
            continue

        ev_booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == ev.event_id).first()
        ev_slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == ev_booking.slot_id).first() if ev_booking else None
        ev_venue = db.query(models.Venue).filter(models.Venue.venue_id == ev_slot.venue_id).first() if ev_slot else None
        host_prof = db.query(models.Profile).filter(models.Profile.user_id == ev.host_id).first()
        raw_ev_loc = ev_venue.locality if ev_venue else (host_prof.approx_locality if host_prof and host_prof.approx_locality else "General")
        ev_clean_loc = raw_ev_loc.split(",")[0].strip().lower()
        ev_day = ev.event_date.strftime("%A").lower()

        p_count = (
            db.query(models.EventParticipant)
            .filter(
                models.EventParticipant.event_id == ev.event_id,
                models.EventParticipant.status.in_(["CONFIRMED", "JOINED", "ACCEPTED"]),
            )
            .count()
        )
        remaining_spots = max(0, ev.max_capacity - p_count)

        events_by_cluster[(int_id, ev_clean_loc, ev_day)].append({
            "event_id": ev.event_id,
            "remaining_spots": remaining_spots,
            "title": ev.title,
        })

    # Ensure events without registered user interest records still register on the radar
    for (e_int_id, e_loc_lower, e_day_lower), ev_list in events_by_cluster.items():
        matching_keys = [k for k in clusters_data.keys() if k[0] == e_int_id and k[1].lower() == e_loc_lower and k[2].lower() == e_day_lower]
        if not matching_keys:
            int_obj = db.query(models.Interest).filter(models.Interest.interest_id == e_int_id).first()
            if int_obj:
                display_loc = e_loc_lower.capitalize()
                display_day = e_day_lower.capitalize()
                c_key = (e_int_id, display_loc, display_day)
                clusters_data[c_key] = {
                    "interest_id": e_int_id,
                    "interest_name": int_obj.name,
                    "category": int_obj.category,
                    "locality": display_loc,
                    "day": display_day,
                    "user_ids": set(),
                    "time_counts": Counter({"18:00-20:00": 1}),
                }

    # 5. Calculate Metrics and Demand Scores for each Cluster
    items = []
    for (c_int_id, c_loc, c_day), c_info in clusters_data.items():
        interested_users = len(c_info["user_ids"])
        act = activity_by_interest.get(c_int_id)
        # Use master interest name as primary activity concept (e.g. 'Badminton', 'Football')
        act_title = c_info["interest_name"]
        act_id = act.activity_id if act else None

        # Resolve preferred time window
        preferred_time = "18:00-20:00"
        if c_info["time_counts"]:
            preferred_time = c_info["time_counts"].most_common(1)[0][0]

        # Match active events in this cluster
        matching_evs = events_by_cluster.get((c_int_id, c_loc.lower(), c_day.lower()), [])
        active_events_count = len(matching_evs)
        available_spots = sum(ev["remaining_spots"] for ev in matching_evs)

        # Estimated unmet demand
        estimated_unmet_demand = max(0, interested_users - available_spots)

        # Deterministic Demand Score Formula (0 to 100)
        # Volume Component (0-60): Scaled with interested user volume
        volume_component = min(60, int(interested_users * 5.0))

        # Unmet Demand Ratio Component (0-30): Rewards clusters with high underserved ratio
        unmet_ratio = (estimated_unmet_demand / max(1, interested_users)) if interested_users > 0 else 0.0
        unmet_component = int(unmet_ratio * 30.0)

        # Local Density Component (0-10): Peer concentration & active venue presence
        density_component = min(10, int(interested_users * 0.5) + (1 if active_events_count > 0 else 0))

        demand_score = min(100, max(0, volume_component + unmet_component + density_component))

        # Status Classification
        if demand_score >= 80:
            status_label = "HIGH_DEMAND"
        elif available_spots >= interested_users and interested_users > 0:
            status_label = "BALANCED"
        elif demand_score >= 50:
            status_label = "MODERATE_DEMAND"
        elif demand_score >= 25:
            status_label = "EMERGING_DEMAND"
        else:
            status_label = "LOW_DEMAND"

        # Context-aware Suggested Action
        if status_label == "HIGH_DEMAND":
            suggested_action = f"Host new events or partner with local venues in {c_loc} to absorb {estimated_unmet_demand} unmet players."
        elif status_label == "MODERATE_DEMAND":
            suggested_action = f"Schedule a targeted session on {c_day} ({preferred_time}) in {c_loc}."
        elif status_label == "BALANCED":
            suggested_action = f"Capacity is well-balanced with {available_spots} open spot(s) serving demand."
        elif status_label == "EMERGING_DEMAND":
            suggested_action = f"Emerging local interest detected: encourage community hosts to propose a session."
        else:
            suggested_action = f"Monitor local activity."

        item = schemas.DemandRadarItem(
            activity=act_title,
            activity_id=act_id,
            interest_id=c_int_id,
            category=c_info["category"],
            locality=c_loc,
            preferred_day=c_day,
            preferred_time=preferred_time,
            interested_users=interested_users,
            active_events=active_events_count,
            available_spots=available_spots,
            estimated_unmet_demand=estimated_unmet_demand,
            demand_score=demand_score,
            status=status_label,
            suggested_action=suggested_action,
        )
        items.append(item)

    # 6. Apply Query Filters
    filtered_items = []
    for item in items:
        if locality and locality.strip().lower() not in item.locality.lower():
            continue
        if activity and (
            activity.strip().lower() not in item.activity.lower()
            and (not item.category or activity.strip().lower() not in item.category.lower())
        ):
            continue
        if day_of_week and day_of_week.strip().lower() != item.preferred_day.lower():
            continue
        if min_demand_score is not None and item.demand_score < min_demand_score:
            continue
        filtered_items.append(item)

    # 7. Deterministic Sorting: Primary by demand_score DESC, secondary by unmet_demand DESC, tertiary by interested_users DESC
    filtered_items.sort(
        key=lambda x: (x.demand_score, x.estimated_unmet_demand, x.interested_users),
        reverse=True,
    )

    final_clusters = filtered_items[:limit]

    return schemas.DemandRadarResponse(
        total_clusters=len(filtered_items),
        locality_filter=locality,
        clusters=final_clusters,
    )


# ============================================================================
# 15. AI DEMAND PREDICTION & FEASIBILITY ENGINE
# ============================================================================

def _compute_demand_prediction(
    locality: str,
    day_of_week: str,
    activity_name: Optional[str] = None,
    activity_id: Optional[int] = None,
    interest_id: Optional[int] = None,
    preferred_time: Optional[str] = "18:00-20:00",
    target_capacity: Optional[int] = None,
    target_price: Optional[float] = None,
    db: Session = None,
) -> schemas.DemandPredictionResponse:
    target_interest = None
    target_activity = None

    if activity_id:
        target_activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
        if target_activity:
            target_interest = db.query(models.Interest).filter(models.Interest.interest_id == target_activity.interest_id).first()
    elif interest_id:
        target_interest = db.query(models.Interest).filter(models.Interest.interest_id == interest_id).first()
        if target_interest:
            target_activity = db.query(models.Activity).filter(models.Activity.interest_id == target_interest.interest_id).first()

    if not target_interest and activity_name:
        clean_act = activity_name.strip()
        target_interest = db.query(models.Interest).filter(models.Interest.name.ilike(f"%{clean_act}%")).first()
        if target_interest:
            target_activity = db.query(models.Activity).filter(models.Activity.interest_id == target_interest.interest_id).first()
        else:
            target_activity = db.query(models.Activity).filter(models.Activity.title.ilike(f"%{clean_act}%")).first()
            if target_activity:
                target_interest = db.query(models.Interest).filter(models.Interest.interest_id == target_activity.interest_id).first()

    if not target_interest:
        target_interest = db.query(models.Interest).first()
        if target_interest:
            target_activity = db.query(models.Activity).filter(models.Activity.interest_id == target_interest.interest_id).first()

    final_activity_title = activity_name or (target_activity.title if target_activity else (target_interest.name if target_interest else "Activity"))
    final_interest_id = target_interest.interest_id if target_interest else 1
    final_activity_id = target_activity.activity_id if target_activity else None

    clean_loc = locality.split(",")[0].strip()
    target_day = day_of_week.strip().capitalize()
    target_time_window = preferred_time or "18:00-20:00"

    # 1. Query pool of interested & available users in this locality
    user_query = (
        db.query(models.User.user_id)
        .join(models.Profile, models.User.user_id == models.Profile.user_id)
        .join(models.UserInterest, models.User.user_id == models.UserInterest.user_id)
        .outerjoin(models.UserAvailability, models.User.user_id == models.UserAvailability.user_id)
        .filter(
            models.User.is_active.is_(True),
            models.UserInterest.interest_id == final_interest_id,
            models.Profile.approx_locality.ilike(f"%{clean_loc}%"),
            or_(
                models.UserAvailability.day_of_week.ilike(f"%{target_day}%"),
                models.UserAvailability.day_of_week.ilike("%weekend%") if target_day in ["Saturday", "Sunday"] else False,
                models.UserAvailability.day_of_week.is_(None),
            ),
        )
    )
    interested_users = user_query.distinct().count()

    # 2. Query competing active events in this locality on this day
    active_events_query = (
        db.query(models.Event)
        .join(models.Activity, models.Event.activity_id == models.Activity.activity_id)
        .filter(
            models.Activity.interest_id == final_interest_id,
            models.Event.status.in_(["PUBLISHED", "DRAFT", "FULL"]),
            models.Event.event_date >= date.today(),
        )
        .all()
    )

    matched_events = []
    available_spots = 0
    for ev in active_events_query:
        if ev.event_date.strftime("%A").lower() == target_day.lower():
            ev_booking = db.query(models.VenueBooking).filter(models.VenueBooking.event_id == ev.event_id).first()
            ev_slot = db.query(models.VenueSlot).filter(models.VenueSlot.slot_id == ev_booking.slot_id).first() if ev_booking else None
            ev_venue = db.query(models.Venue).filter(models.Venue.venue_id == ev_slot.venue_id).first() if ev_slot else None
            host_prof = db.query(models.Profile).filter(models.Profile.user_id == ev.host_id).first()
            ev_loc = ev_venue.locality if ev_venue else (host_prof.approx_locality if host_prof and host_prof.approx_locality else "")
            if clean_loc.lower() in ev_loc.lower():
                matched_events.append(ev)
                p_count = db.query(models.EventParticipant).filter(
                    models.EventParticipant.event_id == ev.event_id,
                    models.EventParticipant.status.in_(["CONFIRMED", "JOINED", "ACCEPTED"]),
                ).count()
                available_spots += max(0, ev.max_capacity - p_count)

    active_events_count = len(matched_events)
    unmet_demand = max(0, interested_users - available_spots)

    # 3. Deterministic Demand Metrics
    vol = min(60, int(interested_users * 5.0))
    unmet_ratio = (unmet_demand / max(1, interested_users)) if interested_users > 0 else 0.0
    unmet_comp = int(unmet_ratio * 30.0)
    density_comp = min(10, int(interested_users * 0.5) + (1 if active_events_count > 0 else 0))
    demand_score = min(100, max(0, vol + unmet_comp + density_comp))

    if demand_score >= 80:
        current_demand_status = "HIGH"
    elif demand_score >= 50:
        current_demand_status = "MODERATE"
    elif available_spots >= interested_users and interested_users > 0:
        current_demand_status = "BALANCED"
    else:
        current_demand_status = "LOW"

    # 4. Venue Availability & Pricing
    venue_slots_query = []
    if final_activity_id:
        venue_slots_query = (
            db.query(models.VenueSlot)
            .join(models.Venue, models.VenueSlot.venue_id == models.Venue.venue_id)
            .join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id)
            .filter(
                models.VenueActivity.activity_id == final_activity_id,
                models.Venue.locality.ilike(f"%{clean_loc}%"),
                models.VenueSlot.status == "AVAILABLE",
            )
            .all()
        )
    venue_slots_available = len(venue_slots_query)
    if venue_slots_available > 0:
        avg_slot_price = float(sum(s.price_total for s in venue_slots_query) / len(venue_slots_query))
    else:
        avg_slot_price = 2400.0

    # 5. Recommended Capacity
    if target_capacity:
        recommended_capacity = target_capacity
    else:
        if unmet_demand >= 10:
            recommended_capacity = 8
        elif unmet_demand >= 6:
            recommended_capacity = 6
        elif unmet_demand >= 3:
            recommended_capacity = 4
        else:
            recommended_capacity = 4

    # 6. Attendance Probability & Turnout Range
    if current_demand_status == "HIGH":
        attendance_prob = 80 + min(10, int(unmet_ratio * 10))
    elif current_demand_status == "MODERATE":
        attendance_prob = 65 + min(10, int(unmet_ratio * 10))
    elif current_demand_status == "BALANCED":
        attendance_prob = 50
    else:
        attendance_prob = 35

    if venue_slots_available > 0:
        attendance_prob = min(95, attendance_prob + 2)

    attendance_probability = min(95, max(15, attendance_prob))

    # Turnout range
    if unmet_demand >= recommended_capacity:
        min_p = recommended_capacity
        max_p = min(interested_users, recommended_capacity + max(1, int(unmet_demand * 0.2)))
    else:
        min_p = max(1, round(recommended_capacity * (attendance_probability / 100.0)))
        max_p = recommended_capacity

    expected_range = f"{min_p}-{max_p}" if min_p != max_p else str(min_p)
    estimated_fill_rate = min(100, max(20, round(attendance_probability * 1.06)))

    # 7. Suggested Price per Participant
    if target_price is not None:
        suggested_price = float(target_price)
    else:
        suggested_price = round(avg_slot_price / max(1, recommended_capacity), 2)

    # 8. Composite Feasibility Score
    v_bonus = 10 if venue_slots_available > 0 else 0
    feasibility_score = min(100, max(10, int(demand_score * 0.55 + attendance_probability * 0.35 + v_bonus)))

    if feasibility_score >= 75:
        feasibility_status = "HIGH"
    elif feasibility_score >= 50:
        feasibility_status = "MODERATE"
    elif feasibility_score >= 30:
        feasibility_status = "LOW"
    else:
        feasibility_status = "CRITICAL_RISK"

    # 9. Feasibility Factors Breakdown
    factors = [
        f"{unmet_demand} unmet players seeking {final_activity_title} in {clean_loc} on {target_day}",
        f"Attendance probability: {attendance_probability}% with projected fill rate of {estimated_fill_rate}%",
        f"Recommended capacity of {recommended_capacity} participants (expected turnout: {expected_range})",
        f"{venue_slots_available} active venue slot(s) in {clean_loc} supporting ₹{suggested_price:.0f}/person split cost",
    ]

    return schemas.DemandPredictionResponse(
        activity=final_activity_title,
        activity_id=final_activity_id,
        interest_id=final_interest_id,
        locality=clean_loc,
        day_of_week=target_day,
        preferred_time=target_time_window,
        current_demand=current_demand_status,
        demand_score=demand_score,
        interested_users=interested_users,
        active_events=active_events_count,
        available_spots=available_spots,
        unmet_demand=unmet_demand,
        expected_participants_min=min_p,
        expected_participants_max=max_p,
        expected_participants_range=expected_range,
        attendance_probability=attendance_probability,
        recommended_capacity=recommended_capacity,
        estimated_fill_rate=estimated_fill_rate,
        suggested_price_per_person=suggested_price,
        feasibility=feasibility_status,
        feasibility_score=feasibility_score,
        venue_slots_available=venue_slots_available,
        factors=factors,
    )


@app.post(
    "/ai/demand-prediction",
    response_model=schemas.DemandPredictionResponse,
    tags=["AI Engine"],
    summary="AI Demand Prediction & Feasibility: Predict attendance, fill rate, and capacity for proposed activities",
)
def predict_demand_feasibility(
    req: schemas.DemandPredictionRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _compute_demand_prediction(
        locality=req.locality,
        day_of_week=req.day_of_week,
        activity_name=req.activity,
        activity_id=req.activity_id,
        interest_id=req.interest_id,
        preferred_time=req.preferred_time,
        target_capacity=req.target_capacity,
        target_price=req.target_price,
        db=db,
    )


@app.get(
    "/ai/demand-prediction",
    response_model=schemas.DemandPredictionResponse,
    tags=["AI Engine"],
    summary="AI Demand Prediction & Feasibility (GET): Predict attendance, fill rate, and capacity for proposed activities",
)
def predict_demand_feasibility_get(
    locality: str = Query(..., description="Target locality, e.g. Indiranagar"),
    day_of_week: str = Query(..., description="Target day of week, e.g. Saturday"),
    activity: Optional[str] = Query(None, description="Activity title or interest name, e.g. Badminton"),
    activity_id: Optional[int] = Query(None, description="Optional Activity ID override"),
    interest_id: Optional[int] = Query(None, description="Optional Interest ID override"),
    preferred_time: Optional[str] = Query("18:00-20:00", description="Preferred time window"),
    target_capacity: Optional[int] = Query(None, ge=2, le=50, description="Optional capacity target"),
    target_price: Optional[float] = Query(None, ge=0, description="Optional target price in INR"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _compute_demand_prediction(
        locality=locality,
        day_of_week=day_of_week,
        activity_name=activity,
        activity_id=activity_id,
        interest_id=interest_id,
        preferred_time=preferred_time,
        target_capacity=target_capacity,
        target_price=target_price,
        db=db,
    )


# ============================================================================
# 16. CROSS-DOMAIN OPPORTUNITY INTELLIGENCE ENGINE
# ============================================================================

@app.get(
    "/ai/opportunities",
    response_model=schemas.OpportunitiesResponse,
    tags=["AI Engine"],
    summary="Cross-Domain Opportunity Intelligence: Orchestrate demand, prediction, venues, and matching into actionable opportunities",
)
def get_opportunities(
    locality: Optional[str] = Query(None, description="Optional filter by locality, e.g. Indiranagar"),
    activity: Optional[str] = Query(None, description="Optional filter by activity or interest name"),
    day: Optional[str] = Query(None, description="Optional filter by day of week, e.g. Saturday"),
    min_opportunity_score: int = Query(default=30, ge=0, le=100, description="Minimum composite opportunity score"),
    limit: int = Query(default=20, ge=1, le=100, description="Max opportunities to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cross-domain orchestrator connecting Demand Radar signals, Demand Prediction & Feasibility,
    local venue slot availability, and group cohort feasibility into ranked, actionable opportunities.
    """
    # 1. Fetch live demand clusters via Demand Radar
    radar_res = get_demand_radar(
        locality=locality,
        activity=activity,
        day_of_week=day,
        min_demand_score=20,
        limit=50,
        current_user=current_user,
        db=db,
    )

    opportunities = []

    for cluster in radar_res.clusters:
        # 2. Orchestrate Demand Prediction & Feasibility for each cluster
        pred = _compute_demand_prediction(
            locality=cluster.locality,
            day_of_week=cluster.preferred_day,
            activity_name=cluster.activity,
            activity_id=cluster.activity_id,
            interest_id=cluster.interest_id,
            preferred_time=cluster.preferred_time,
            db=db,
        )

        # 3. Check Venue Grounding in Locality
        venue_match = None
        if cluster.activity_id:
            venue_match = (
                db.query(models.Venue)
                .join(models.VenueActivity, models.Venue.venue_id == models.VenueActivity.venue_id)
                .filter(
                    models.VenueActivity.activity_id == cluster.activity_id,
                    models.Venue.locality.ilike(f"%{cluster.locality}%"),
                    models.Venue.status == "ACTIVE",
                )
                .first()
            )

        venue_available = (pred.venue_slots_available > 0 or venue_match is not None)
        suggested_venue_id = venue_match.venue_id if venue_match else None
        suggested_venue_name = venue_match.name if venue_match else None

        # 4. Determine Opportunity Type and Action
        if venue_available:
            opportunity_type = "CREATE_EVENT"
            action = "CREATE_EVENT"
        else:
            opportunity_type = "VENUE_PARTNERSHIP"
            action = "PARTNER_VENUE"

        # 5. Composite Opportunity Score (0-100)
        # 50% Demand Pressure + 40% Feasibility & Turnout + 10% Venue Readiness
        v_bonus = 10 if venue_available else 0
        composite_score = min(
            100,
            max(
                0,
                int(cluster.demand_score * 0.50 + pred.feasibility_score * 0.40 + v_bonus),
            ),
        )

        if composite_score < min_opportunity_score:
            continue

        # 6. Actionable Payload
        action_payload = {
            "action": action,
            "opportunity_type": opportunity_type,
            "activity": cluster.activity,
            "activity_id": cluster.activity_id,
            "interest_id": cluster.interest_id,
            "locality": cluster.locality,
            "day": cluster.preferred_day,
            "time": cluster.preferred_time,
            "recommended_capacity": pred.recommended_capacity,
            "suggested_price": pred.suggested_price_per_person,
            "suggested_venue_id": suggested_venue_id,
            "suggested_venue_name": suggested_venue_name,
        }

        # 7. Actionable Reasons
        reasons = [
            f"{cluster.estimated_unmet_demand} unmet players seeking {cluster.activity} in {cluster.locality} on {cluster.preferred_day}",
            f"Feasibility: {pred.feasibility} (Projected fill rate: {pred.estimated_fill_rate}%, attendance prob: {pred.attendance_probability}%)",
            f"{'Verified venue ready: ' + suggested_venue_name if suggested_venue_name else ('Available venue slots in locality' if venue_available else 'No venue registered yet — high partnership opportunity')}",
            f"Recommended pricing: ₹{pred.suggested_price_per_person:.0f}/person for {pred.recommended_capacity} participants",
        ]

        opp = schemas.OpportunityItem(
            opportunity_type=opportunity_type,
            activity=cluster.activity,
            activity_id=cluster.activity_id,
            interest_id=cluster.interest_id,
            category=cluster.category,
            locality=cluster.locality,
            day=cluster.preferred_day,
            time=cluster.preferred_time,
            demand_score=cluster.demand_score,
            feasibility_score=pred.feasibility_score,
            expected_participants=pred.expected_participants_range,
            recommended_capacity=pred.recommended_capacity,
            venue_available=venue_available,
            suggested_venue_id=suggested_venue_id,
            suggested_venue_name=suggested_venue_name,
            suggested_price_per_person=pred.suggested_price_per_person,
            opportunity_score=composite_score,
            action=action,
            action_payload=action_payload,
            reasons=reasons,
        )
        opportunities.append(opp)

    # 8. Sort by composite opportunity_score DESC
    opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)

    return schemas.OpportunitiesResponse(
        total_opportunities=len(opportunities),
        locality_filter=locality,
        opportunities=opportunities[:limit],
    )


# ============================================================================
# 17. AI COMMUNITY INTELLIGENCE ENGINE
# ============================================================================

@app.get(
    "/ai/community-intelligence",
    response_model=schemas.CommunityIntelligenceResponse,
    tags=["AI Engine"],
    summary="AI Community Intelligence: Detect naturally forming patterns and propose communities",
)
@app.get(
    "/ai/community-proposals",
    response_model=schemas.CommunityIntelligenceResponse,
    tags=["AI Engine"],
    summary="AI Community Proposals alias",
)
@app.get(
    "/ai/communities",
    response_model=schemas.CommunityIntelligenceResponse,
    tags=["AI Engine"],
    summary="AI Communities intelligence endpoint alias",
)
def get_community_intelligence(
    locality: Optional[str] = Query(None, description="Optional filter by locality, e.g. Indiranagar"),
    activity: Optional[str] = Query(None, description="Optional filter by activity or interest name, e.g. Badminton"),
    day: Optional[str] = Query(None, description="Optional filter by preferred recurring day, e.g. Saturday"),
    min_opportunity_score: int = Query(default=30, ge=0, le=100, description="Minimum community viability score threshold"),
    limit: int = Query(default=20, ge=1, le=100, description="Max community proposals to return"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Detects recurring cohorts of compatible users, weekly schedule alignments,
    localities, and repeated event participation to propose community circles before creation.
    Does not write to database automatically; follows: Propose -> Validate -> User Decides.
    """
    # 1. Fetch active users, profiles, interests, and schedules
    users = db.query(models.User).filter(models.User.is_active.is_(True)).all()
    user_ids = [u.user_id for u in users]
    if not user_ids:
        return schemas.CommunityIntelligenceResponse(total_proposals=0, locality_filter=locality, proposals=[])

    profiles = db.query(models.Profile).filter(models.Profile.user_id.in_(user_ids)).all()
    profile_by_user = {p.user_id: p for p in profiles}

    user_interests = db.query(models.UserInterest).filter(models.UserInterest.user_id.in_(user_ids)).all()
    interests_by_user: Dict[int, Set[int]] = defaultdict(set)
    for ui in user_interests:
        interests_by_user[ui.user_id].add(ui.interest_id)

    user_avails = db.query(models.UserAvailability).filter(models.UserAvailability.user_id.in_(user_ids)).all()
    avails_by_user: Dict[int, List[models.UserAvailability]] = defaultdict(list)
    for ua in user_avails:
        avails_by_user[ua.user_id].append(ua)

    all_interests = db.query(models.Interest).all()
    interest_map = {i.interest_id: i for i in all_interests}

    activities = db.query(models.Activity).all()
    activity_by_interest = {a.interest_id: a for a in activities}

    # 2. Track past and active event participations for repeated cohesion signal
    part_query = (
        db.query(models.Activity.interest_id, models.EventParticipant.user_id)
        .join(models.Event, models.EventParticipant.event_id == models.Event.event_id)
        .join(models.Activity, models.Event.activity_id == models.Activity.activity_id)
        .filter(models.EventParticipant.status == "CONFIRMED")
        .all()
    )
    user_interest_events_count: Dict[Tuple[int, int], int] = Counter()
    for int_id, uid in part_query:
        user_interest_events_count[(int_id, uid)] += 1

    # 3. Detect candidate clusters by (interest_id, locality, day)
    clusters: Dict[Tuple[int, str, str], Dict[str, Any]] = {}

    for uid in user_ids:
        prof = profile_by_user.get(uid)
        raw_loc = (prof.approx_locality or "").strip() if prof else ""
        if not raw_loc:
            continue
        clean_loc = raw_loc.split(",")[0].strip().capitalize()

        u_int_ids = interests_by_user.get(uid, set())
        u_av = avails_by_user.get(uid, [])

        # If user has no explicit availability, treat as general Weekend / Saturday
        days = {ua.day_of_week.capitalize().strip() for ua in u_av} if u_av else {"Saturday"}

        for i_id in u_int_ids:
            if i_id not in interest_map:
                continue
            for d in days:
                c_key = (i_id, clean_loc, d)
                if c_key not in clusters:
                    clusters[c_key] = {
                        "interest_id": i_id,
                        "locality": clean_loc,
                        "day": d,
                        "user_ids": set(),
                        "time_windows": [],
                    }
                clusters[c_key]["user_ids"].add(uid)
                for ua in u_av:
                    if ua.day_of_week.capitalize().strip() == d and ua.start_time and ua.end_time:
                        clusters[c_key]["time_windows"].append(f"{ua.start_time.strftime('%H:%M')}-{ua.end_time.strftime('%H:%M')}")

    proposals: List[schemas.CommunityProposalItem] = []

    # 4. Formulate community proposals for viable clusters
    for (i_id, c_loc, c_day), c_info in clusters.items():
        candidate_uids = sorted(list(c_info["user_ids"]))
        member_candidates = len(candidate_uids)
        if member_candidates < 1:
            continue

        interest = interest_map[i_id]
        act = activity_by_interest.get(i_id)
        act_id = act.activity_id if act else None

        # Filter criteria checks
        if locality:
            loc_q = locality.lower().strip()
            if loc_q not in c_loc.lower() and c_loc.lower() not in loc_q:
                continue

        if activity:
            act_q = activity.lower().strip()
            if act_q not in interest.name.lower() and (not act or act_q not in act.title.lower()):
                continue

        if day:
            day_q = day.lower().strip()
            if day_q not in c_day.lower():
                continue

        # Community type & theme
        comm_type = interest.category.upper() if interest.category else "SPORTS"
        if c_day.lower() in ["saturday", "sunday"]:
            theme = f"{c_loc} Weekend {interest.name}"
        else:
            theme = f"{c_loc} {c_day} {interest.name}"

        # Schedule pattern
        time_win = c_info["time_windows"][0] if c_info["time_windows"] else "18:00-20:00"
        recurring_pattern = f"{c_day} evenings" if time_win in ["18:00-20:00", "18:00-21:00", "evening"] else f"{c_day} ({time_win})"

        # Cohesion & repeated participation
        repeated_total = sum(user_interest_events_count.get((i_id, uid), 0) for uid in candidate_uids)
        has_repeated = (repeated_total >= 2)

        # Compatibility score (0-100)
        # 40 (Interest match) + 25 (Same locality) + 22 (Recurring day availability) + bonus
        cohesion_bonus = min(13, int(repeated_total * 2.0) + (3 if member_candidates >= 4 else 0))
        compat_score = min(100, max(50, 40 + 25 + 22 + cohesion_bonus))

        # Community Opportunity Score (0-100)
        # 60% Compatibility + 30% Volume (2.5 pts per candidate up to 30) + 10% Repeated Participation
        vol_pts = min(30.0, member_candidates * 2.5)
        rep_pts = 10.0 if has_repeated else 0.0
        opp_score = min(100, max(10, int(round(compat_score * 0.60 + vol_pts + rep_pts))))

        if opp_score < min_opportunity_score:
            continue

        # Check existing communities in database
        existing_comm = (
            db.query(models.Community)
            .filter(
                (models.Community.name.ilike(f"%{theme}%")) |
                (func.lower(models.Community.name).contains(c_loc.lower()) & func.lower(models.Community.name).contains(interest.name.lower()))
            )
            .first()
        )

        if existing_comm:
            existing_comm_id = existing_comm.community_id
            suggested_action = "JOIN_COMMUNITY"
        else:
            existing_comm_id = None
            suggested_action = "CREATE_COMMUNITY"

        # Action payload for frontend or direct POST /communities execution
        action_payload = {
            "name": theme,
            "description": f"A recurring local community for {interest.name} enthusiasts in {c_loc} ({recurring_pattern}).",
            "initial_member_ids": candidate_uids,
            "activity": interest.name,
            "locality": c_loc,
            "recurring_pattern": recurring_pattern,
            "community_type": comm_type,
            "suggested_action": suggested_action,
        }

        reasons = [
            f"{member_candidates} compatible peers with active {interest.name} interest in {c_loc}",
            f"Recurring availability pattern on {recurring_pattern}",
            f"Cohort compatibility score: {compat_score}%",
        ]
        if has_repeated:
            reasons.append(f"Strong track record of repeated participation ({repeated_total} past event sessions)")

        proposals.append(
            schemas.CommunityProposalItem(
                community_type=comm_type,
                theme=theme,
                activity=interest.name,
                activity_id=act_id,
                interest_id=i_id,
                locality=c_loc,
                member_candidates=member_candidates,
                candidate_user_ids=candidate_uids,
                recurring_pattern=recurring_pattern,
                day_of_week=c_day,
                time_window=time_win,
                compatibility_score=compat_score,
                community_opportunity_score=opp_score,
                suggested_action=suggested_action,
                action_payload=action_payload,
                reasons=reasons,
                existing_community_id=existing_comm_id,
            )
        )

    # 5. Sort by community_opportunity_score DESC, then member_candidates DESC
    proposals.sort(key=lambda p: (p.community_opportunity_score, p.member_candidates), reverse=True)

    return schemas.CommunityIntelligenceResponse(
        total_proposals=len(proposals),
        locality_filter=locality,
        proposals=proposals[:limit],
    )


# ============================================================================
# 18. COMMUNITY HEALTH & LIFECYCLE INTELLIGENCE (Deterministic Foundation)
# ============================================================================

def _compute_community_health(
    community_or_id: Union[models.Community, int],
    db: Session,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
) -> dict:
    """
    Computes deterministic community health metrics and score (0-100) using existing tables:
    communities, community_members, events, event_participants, and feedback.
    Optionally evaluates activity within a specific [period_start, period_end] time window.

    Weights:
      Participation:   35%
      Event Activity:  25%
      Completion:      15%
      Feedback:        15%
      Member Activity: 10%

    Classifications:
      75–100 -> HEALTHY
      50–74  -> GROWING
      30–49  -> AT_RISK
      0–29   -> INACTIVE
    """
    if isinstance(community_or_id, int):
        comm = db.query(models.Community).filter(models.Community.community_id == community_or_id).first()
        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    else:
        comm = community_or_id

    # 1. Members
    member_records = db.query(models.CommunityMember).filter(models.CommunityMember.community_id == comm.community_id).all()
    member_user_ids = {m.user_id for m in member_records}
    member_count = len(member_user_ids)

    if member_count == 0:
        return {
            "community_id": comm.community_id,
            "member_count": 0,
            "active_member_count": 0,
            "events_created": 0,
            "completed_events": 0,
            "recent_event_count": 0,
            "average_event_participation": 0,
            "average_feedback_rating": 0.0,
            "health_score": 0,
            "health_status": "INACTIVE",
        }

    # 2. Events associated with community (hosted by members or creator)
    events_query = db.query(models.Event).filter(models.Event.host_id.in_(member_user_ids))
    if period_start is not None:
        events_query = events_query.filter(models.Event.event_date >= period_start)
    if period_end is not None:
        events_query = events_query.filter(models.Event.event_date <= period_end)
    events = events_query.all()

    events_created = len(events)
    event_ids = [e.event_id for e in events]

    completed_events = len([e for e in events if e.status == "COMPLETED"])

    # Recent events: if period specified, events in that period; otherwise in last 30 days
    if period_start is not None or period_end is not None:
        recent_event_count = events_created
    else:
        now_date = date.today()
        cutoff_recent = now_date - timedelta(days=30)
        recent_event_count = len([e for e in events if e.event_date >= cutoff_recent])

    # 3. Active Members (members who hosted an event or participated in a confirmed event in this period)
    if events:
        confirmed_participant_uids = {
            row[0]
            for row in db.query(models.EventParticipant.user_id)
            .filter(
                models.EventParticipant.user_id.in_(member_user_ids),
                models.EventParticipant.event_id.in_(event_ids),
                models.EventParticipant.status == "CONFIRMED",
            )
            .all()
        }
    elif period_start is None and period_end is None:
        confirmed_participant_uids = {
            row[0]
            for row in db.query(models.EventParticipant.user_id)
            .filter(
                models.EventParticipant.user_id.in_(member_user_ids),
                models.EventParticipant.status == "CONFIRMED",
            )
            .all()
        }
    else:
        confirmed_participant_uids = set()

    hosts_uids = {e.host_id for e in events}
    active_member_uids = member_user_ids.intersection(confirmed_participant_uids.union(hosts_uids))
    active_member_count = len(active_member_uids)

    # 4. Average Event Participation Rate (fill rate: confirmed participants / max_capacity * 100)
    fill_rates = []
    for ev in events:
        part_count = (
            db.query(models.EventParticipant)
            .filter(
                models.EventParticipant.event_id == ev.event_id,
                models.EventParticipant.status == "CONFIRMED",
            )
            .count()
        )
        rate = min(100.0, (part_count / max(1, ev.max_capacity)) * 100.0)
        fill_rates.append(rate)

    average_event_participation = round(sum(fill_rates) / len(fill_rates)) if fill_rates else 0

    # 5. Average Feedback Rating
    if event_ids:
        feedbacks = db.query(models.Feedback).filter(models.Feedback.event_id.in_(event_ids)).all()
        if feedbacks:
            average_feedback_rating = round(sum(f.rating for f in feedbacks) / len(feedbacks), 1)
        else:
            average_feedback_rating = 0.0
    else:
        average_feedback_rating = 0.0

    # 6. Deterministic Score Calculation
    # Participation (35%)
    pts_participation = (average_event_participation / 100.0) * 35.0

    # Event Activity (25%): 3+ recent events gives full 25; otherwise scaled by activity volume
    if recent_event_count >= 3:
        pts_event_activity = 25.0
    elif recent_event_count > 0:
        pts_event_activity = min(25.0, recent_event_count * 8.0 + (events_created * 1.0))
    elif events_created > 0:
        pts_event_activity = min(15.0, events_created * 3.0)
    else:
        pts_event_activity = 0.0

    # Completion (15%): completed / created ratio
    completion_ratio = (completed_events / max(1, events_created)) if events_created > 0 else 0.0
    pts_completion = completion_ratio * 15.0

    # Feedback (15%): average_feedback_rating out of 5.0
    pts_feedback = (average_feedback_rating / 5.0) * 15.0 if average_feedback_rating > 0 else 0.0

    # Member Activity (10%): active_member_count / member_count ratio
    member_ratio = (active_member_count / max(1, member_count)) if member_count > 0 else 0.0
    pts_member_activity = member_ratio * 10.0

    health_score = min(100, max(0, int(round(
        pts_participation + pts_event_activity + pts_completion + pts_feedback + pts_member_activity
    ))))

    # 7. Classification
    if health_score >= 75:
        health_status = "HEALTHY"
    elif health_score >= 50:
        health_status = "GROWING"
    elif health_score >= 30:
        health_status = "AT_RISK"
    else:
        health_status = "INACTIVE"

    return {
        "community_id": comm.community_id,
        "member_count": member_count,
        "active_member_count": active_member_count,
        "events_created": events_created,
        "completed_events": completed_events,
        "recent_event_count": recent_event_count,
        "average_event_participation": average_event_participation,
        "average_feedback_rating": average_feedback_rating,
        "health_score": health_score,
        "health_status": health_status,
    }


def _compute_community_health_trend(
    community_or_id: Union[models.Community, int],
    db: Session,
    window_days: int = 30,
) -> dict:
    """
    Compares deterministic community health metrics across two consecutive time windows:
    - Current period:  [today - window_days, today + 30 days]
    - Previous period: [today - 2 * window_days, today - window_days - 1]

    Deterministic Trend Classification:
      score_change >= 10  -> IMPROVING
      score_change <= -10 -> DECLINING
      otherwise           -> STABLE
    """
    if isinstance(community_or_id, int):
        comm = db.query(models.Community).filter(models.Community.community_id == community_or_id).first()
        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    else:
        comm = community_or_id

    today = date.today()
    curr_start = today - timedelta(days=window_days)
    curr_end = today + timedelta(days=30)
    prev_start = today - timedelta(days=window_days * 2)
    prev_end = today - timedelta(days=window_days + 1)

    curr_metrics = _compute_community_health(comm, db, period_start=curr_start, period_end=curr_end)
    prev_metrics = _compute_community_health(comm, db, period_start=prev_start, period_end=prev_end)

    curr_score = curr_metrics["health_score"]
    prev_score = prev_metrics["health_score"]
    score_change = curr_score - prev_score

    if score_change >= 10:
        trend = "IMPROVING"
    elif score_change <= -10:
        trend = "DECLINING"
    else:
        trend = "STABLE"

    metrics_comparison = {
        "active_members": {
            "current": curr_metrics["active_member_count"],
            "previous": prev_metrics["active_member_count"],
            "change": curr_metrics["active_member_count"] - prev_metrics["active_member_count"],
        },
        "events_created": {
            "current": curr_metrics["events_created"],
            "previous": prev_metrics["events_created"],
            "change": curr_metrics["events_created"] - prev_metrics["events_created"],
        },
        "completed_events": {
            "current": curr_metrics["completed_events"],
            "previous": prev_metrics["completed_events"],
            "change": curr_metrics["completed_events"] - prev_metrics["completed_events"],
        },
        "average_participation": {
            "current": curr_metrics["average_event_participation"],
            "previous": prev_metrics["average_event_participation"],
            "change": curr_metrics["average_event_participation"] - prev_metrics["average_event_participation"],
        },
        "average_feedback": {
            "current": curr_metrics["average_feedback_rating"],
            "previous": prev_metrics["average_feedback_rating"],
            "change": round(curr_metrics["average_feedback_rating"] - prev_metrics["average_feedback_rating"], 1),
        },
    }

    return {
        "community_id": comm.community_id,
        "current_health_score": curr_score,
        "previous_health_score": prev_score,
        "score_change": score_change,
        "trend": trend,
        "current_status": curr_metrics["health_status"],
        "previous_status": prev_metrics["health_status"],
        "metrics_comparison": metrics_comparison,
    }


def _generate_community_lifecycle_insight(
    community_or_id: Union[models.Community, int],
    db: Session,
    health_data: Optional[dict] = None,
    trend_data: Optional[dict] = None,
    window_days: int = 30,
) -> dict:
    """
    Synthesizes AI Community Lifecycle Intelligence from verified deterministic health & trend calculations:
    - Interprets health trajectory, metric shifts, and member momentum
    - Enforces strict factual boundaries: AI cannot alter metrics, member counts, ratings, or scores
    - Validates output with Pydantic schemas (schemas.CommunityLifecycleInsightResponse)
    - Reverts gracefully to deterministic fallback on AI failure or invalid response
    - Performs ZERO database modifications
    """
    if isinstance(community_or_id, int):
        comm = db.query(models.Community).filter(models.Community.community_id == community_or_id).first()
        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    else:
        comm = community_or_id

    # 1. Deterministic Foundation
    if health_data is None:
        health_data = _compute_community_health(comm, db)
    if trend_data is None:
        trend_data = _compute_community_health_trend(comm, db, window_days=window_days)

    # 2. Package Verified Ground Truth Facts
    facts = {
        "community_id": comm.community_id,
        "community_name": comm.name,
        "health_status": health_data["health_status"],
        "health_score": health_data["health_score"],
        "trend": trend_data["trend"],
        "score_change": trend_data["score_change"],
        "current_health_score": trend_data["current_health_score"],
        "previous_health_score": trend_data["previous_health_score"],
        "member_count": health_data.get("member_count", 0),
        "active_member_count": health_data.get("active_member_count", 0),
        "events_created": health_data.get("events_created", 0),
        "completed_events": health_data.get("completed_events", 0),
        "recent_event_count": health_data.get("recent_event_count", 0),
        "average_event_participation": health_data.get("average_event_participation", 0),
        "average_feedback_rating": health_data.get("average_feedback_rating", 0.0),
        "metrics_comparison": trend_data.get("metrics_comparison", {}),
    }

    # 3. Call AI Interpretation Layer (with automatic deterministic fallback in ai_service)
    ai_result = generate_community_lifecycle_ai(facts)

    # 4. Enforce Boundary & Fact Immunity:
    # Deterministic facts (community_id, health_status, trend) MUST match verified ground truth!
    valid_stages = {"NEW", "GROWING", "HEALTHY", "AT_RISK", "INACTIVE"}
    lifecycle_stage = ai_result.get("lifecycle_stage")
    if not isinstance(lifecycle_stage, str) or lifecycle_stage.strip().upper() not in valid_stages:
        # Fallback to deterministic stage derivation
        if health_data["health_status"] == "INACTIVE":
            lifecycle_stage = "NEW" if health_data.get("events_created", 0) == 0 and health_data.get("member_count", 0) <= 2 else "INACTIVE"
        elif health_data["health_status"] == "AT_RISK" or trend_data["trend"] == "DECLINING":
            lifecycle_stage = "AT_RISK"
        elif trend_data["trend"] == "IMPROVING":
            lifecycle_stage = "GROWING"
        elif health_data["health_status"] == "HEALTHY":
            lifecycle_stage = "HEALTHY"
        elif health_data["health_status"] == "GROWING":
            lifecycle_stage = "GROWING"
        else:
            lifecycle_stage = "NEW"
    else:
        lifecycle_stage = lifecycle_stage.strip().upper()

    insight = ai_result.get("insight")
    if not isinstance(insight, str) or not insight.strip():
        insight = "The community maintains active regular engagement."

    recommended_focus = ai_result.get("recommended_focus")
    if not isinstance(recommended_focus, str) or not recommended_focus.strip():
        recommended_focus = "Continue scheduled recurring gatherings and monitor member participation."

    validated_payload = {
        "community_id": comm.community_id,
        "health_score": health_data["health_score"],
        "health_status": health_data["health_status"],
        "trend": trend_data["trend"],
        "score_change": trend_data["score_change"],
        "lifecycle_stage": lifecycle_stage,
        "insight": insight.strip(),
        "recommended_focus": recommended_focus.strip(),
    }

    # 5. Schema Validation
    validated = schemas.CommunityLifecycleInsightResponse(**validated_payload)
    return validated.model_dump()


def _generate_community_action_recommendations(
    community_or_id: Union[models.Community, int],
    db: Session,
    lifecycle_data: Optional[dict] = None,
    window_days: int = 30,
) -> dict:
    """
    Synthesizes tactical AI action recommendations grounded strictly in verified community lifecycle facts:
    - Consumes verified health, trend, and lifecycle analysis
    - Generates 1-3 recommendations with controlled action enum and priority
    - Zero numerical fact hallucination: does not calculate or invent numbers
    - Validates output with Pydantic schemas (schemas.CommunityActionRecommendationsResponse)
    - Reverts gracefully to deterministic fallback on AI failure or invalid action enum
    - Performs ZERO database modifications
    """
    if isinstance(community_or_id, int):
        comm = db.query(models.Community).filter(models.Community.community_id == community_or_id).first()
        if not comm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    else:
        comm = community_or_id

    # 1. Obtain Lifecycle Intelligence Ground Truth
    if lifecycle_data is None:
        lifecycle_data = _generate_community_lifecycle_insight(comm, db, window_days=window_days)

    health_data = _compute_community_health(comm, db)
    trend_data = _compute_community_health_trend(comm, db, window_days=window_days)

    # 2. Package Verified Ground Truth Facts
    facts = {
        "community_id": comm.community_id,
        "community_name": comm.name,
        "lifecycle_stage": lifecycle_data["lifecycle_stage"],
        "health_score": lifecycle_data["health_score"],
        "health_status": lifecycle_data["health_status"],
        "trend": lifecycle_data["trend"],
        "score_change": lifecycle_data["score_change"],
        "insight": lifecycle_data.get("insight", ""),
        "recommended_focus": lifecycle_data.get("recommended_focus", ""),
        "member_count": health_data.get("member_count", 0),
        "active_member_count": health_data.get("active_member_count", 0),
        "events_created": health_data.get("events_created", 0),
        "completed_events": health_data.get("completed_events", 0),
        "recent_event_count": health_data.get("recent_event_count", 0),
        "average_event_participation": health_data.get("average_event_participation", 0),
        "average_feedback_rating": health_data.get("average_feedback_rating", 0.0),
    }

    # 3. Call Recommendation Engine (AI with deterministic fallback)
    raw_recommendations = generate_community_action_recommendations_ai(facts)

    # 4. Strict Validation & Controlled Action Enum Enforcement
    valid_actions = {
        "CREATE_EVENT",
        "RE_ENGAGE_MEMBERS",
        "COLLECT_FEEDBACK",
        "GROW_MEMBERSHIP",
        "MAINTAIN_ACTIVITY",
        "REACTIVATE_COMMUNITY",
    }
    valid_priorities = {"HIGH", "MEDIUM", "LOW"}

    sanitized_recs = []
    for item in raw_recommendations:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "")).strip().upper()
        priority = str(item.get("priority", "")).strip().upper()
        title = str(item.get("title", "")).strip()
        reason = str(item.get("reason", "")).strip()
        next_step = str(item.get("suggested_next_step", "")).strip()

        if action in valid_actions and priority in valid_priorities and title and reason and next_step:
            sanitized_recs.append({
                "priority": priority,
                "action": action,
                "title": title,
                "reason": reason,
                "suggested_next_step": next_step,
            })

    if not sanitized_recs:
        from ai_service import _deterministic_community_action_fallback
        sanitized_recs = _deterministic_community_action_fallback(facts)

    # 5. Validate with Pydantic Response Schema
    validated = schemas.CommunityActionRecommendationsResponse(
        community_id=comm.community_id,
        recommendations=sanitized_recs,
    )
    return validated.model_dump()


# ============================================================================
# 18.5 COMMUNITY ACTION EXECUTION CONTRACT VALIDATION (Step 9.1 - Pure)
# ============================================================================

def validate_community_action_request(
    request: Union[schemas.ActionRequest, Dict[str, Any]]
) -> schemas.ActionValidationResult:
    """
    Pure action validation function for Step 9.1.
    - Validates that action maps to the closed AllowedAction enum.
    - Rejects arbitrary / hallucinated AI actions.
    - Performs parameter-specific sanity & type checks.
    - Detects and rejects malicious / script injection payloads.
    - Causes ZERO database writes and ZERO external side-effects.
    """
    if isinstance(request, schemas.ActionRequest):
        raw_action = request.action
        raw_params = request.parameters or {}
        reason = request.reason
    elif isinstance(request, dict):
        raw_action = request.get("action")
        raw_params = request.get("parameters") or {}
        reason = request.get("reason")
    else:
        return schemas.ActionValidationResult(
            is_valid=False,
            action=None,
            normalized_action=None,
            errors=["Request must be an ActionRequest instance or dictionary."],
            sanitized_parameters={},
        )

    if raw_action is None or not isinstance(raw_action, str) or not raw_action.strip():
        return schemas.ActionValidationResult(
            is_valid=False,
            action=str(raw_action) if raw_action is not None else None,
            normalized_action=None,
            errors=["Action cannot be empty or null."],
            sanitized_parameters={},
        )

    normalized_str = raw_action.strip().upper()
    allowed_values = {a.value for a in schemas.AllowedAction}

    if normalized_str not in allowed_values:
        return schemas.ActionValidationResult(
            is_valid=False,
            action=raw_action,
            normalized_action=None,
            errors=[f"Action '{raw_action}' is not an allowed action. Permitted actions: {', '.join(sorted(allowed_values))}."],
            sanitized_parameters={},
        )

    normalized_action = schemas.AllowedAction(normalized_str)

    if not isinstance(raw_params, dict):
        return schemas.ActionValidationResult(
            is_valid=False,
            action=raw_action,
            normalized_action=normalized_action,
            errors=["Action parameters must be a dictionary/object."],
            sanitized_parameters={},
        )

    errors: List[str] = []
    sanitized: Dict[str, Any] = {}

    def _contains_dangerous_payload(val: Any) -> bool:
        if isinstance(val, str):
            low = val.lower()
            if "<script" in low or "javascript:" in low or ("<img" in low and "onerror" in low):
                return True
        elif isinstance(val, dict):
            return any(_contains_dangerous_payload(v) for v in val.values())
        elif isinstance(val, list):
            return any(_contains_dangerous_payload(v) for v in val)
        return False

    if _contains_dangerous_payload(raw_params):
        errors.append("Malicious input or script tags detected in action parameters.")

    # Action-specific parameter checks
    if normalized_action == schemas.AllowedAction.CREATE_EVENT:
        if "max_capacity" in raw_params:
            cap_val = raw_params["max_capacity"]
            if isinstance(cap_val, bool) or not isinstance(cap_val, (int, float)):
                errors.append("CREATE_EVENT requires max_capacity to be an integer.")
            else:
                cap_int = int(cap_val)
                if cap_int <= 0 or cap_int > 500:
                    errors.append("CREATE_EVENT requires max_capacity to be between 1 and 500.")
                else:
                    sanitized["max_capacity"] = cap_int

        if "event_date" in raw_params:
            date_str = str(raw_params["event_date"]).strip()
            try:
                parsed_date = date.fromisoformat(date_str)
                sanitized["event_date"] = parsed_date.isoformat()
            except (ValueError, TypeError):
                errors.append("CREATE_EVENT requires event_date to be a valid ISO format YYYY-MM-DD.")

        if "start_time" in raw_params:
            t_str = str(raw_params["start_time"]).strip()
            try:
                parsed_t = time.fromisoformat(t_str)
                sanitized["start_time"] = parsed_t.isoformat()
            except (ValueError, TypeError):
                errors.append("CREATE_EVENT start_time must be in valid time format HH:MM or HH:MM:SS.")

        if "end_time" in raw_params:
            t_str = str(raw_params["end_time"]).strip()
            try:
                parsed_t = time.fromisoformat(t_str)
                sanitized["end_time"] = parsed_t.isoformat()
            except (ValueError, TypeError):
                errors.append("CREATE_EVENT end_time must be in valid time format HH:MM or HH:MM:SS.")

        if "title" in raw_params:
            title_val = raw_params["title"]
            if not isinstance(title_val, str) or not title_val.strip():
                errors.append("CREATE_EVENT title cannot be blank if provided.")
            else:
                sanitized["title"] = title_val.strip()

        if "activity_id" in raw_params:
            act_val = raw_params["activity_id"]
            if isinstance(act_val, bool) or not isinstance(act_val, int) or act_val <= 0:
                errors.append("CREATE_EVENT activity_id must be a positive integer.")
            else:
                sanitized["activity_id"] = act_val

    elif normalized_action == schemas.AllowedAction.RE_ENGAGE_MEMBERS:
        if "message" in raw_params:
            msg_val = raw_params["message"]
            if not isinstance(msg_val, str) or not msg_val.strip():
                errors.append("RE_ENGAGE_MEMBERS message cannot be blank or whitespace-only.")
            elif len(msg_val.strip()) > 500:
                errors.append("RE_ENGAGE_MEMBERS message cannot exceed 500 characters.")
            else:
                sanitized["message"] = msg_val.strip()

        if "target_inactive_days" in raw_params:
            d_val = raw_params["target_inactive_days"]
            if isinstance(d_val, bool) or not isinstance(d_val, int) or d_val <= 0:
                errors.append("RE_ENGAGE_MEMBERS target_inactive_days must be a positive integer.")
            else:
                sanitized["target_inactive_days"] = d_val

    elif normalized_action == schemas.AllowedAction.COLLECT_FEEDBACK:
        if "event_id" in raw_params:
            eid_val = raw_params["event_id"]
            if isinstance(eid_val, bool) or not isinstance(eid_val, int) or eid_val <= 0:
                errors.append("COLLECT_FEEDBACK event_id must be a positive integer.")
            else:
                sanitized["event_id"] = eid_val

    elif normalized_action == schemas.AllowedAction.GROW_MEMBERSHIP:
        if "target_count" in raw_params:
            tc_val = raw_params["target_count"]
            if isinstance(tc_val, bool) or not isinstance(tc_val, int) or tc_val <= 0:
                errors.append("GROW_MEMBERSHIP target_count must be a positive integer.")
            else:
                sanitized["target_count"] = tc_val

    elif normalized_action == schemas.AllowedAction.MAINTAIN_ACTIVITY:
        if "recurring_pattern" in raw_params:
            rp_val = raw_params["recurring_pattern"]
            if not isinstance(rp_val, str) or not rp_val.strip():
                errors.append("MAINTAIN_ACTIVITY recurring_pattern cannot be blank if provided.")
            else:
                sanitized["recurring_pattern"] = rp_val.strip()

    elif normalized_action == schemas.AllowedAction.REACTIVATE_COMMUNITY:
        if "proposed_date" in raw_params:
            pd_str = str(raw_params["proposed_date"]).strip()
            try:
                parsed_pd = date.fromisoformat(pd_str)
                sanitized["proposed_date"] = parsed_pd.isoformat()
            except (ValueError, TypeError):
                errors.append("REACTIVATE_COMMUNITY proposed_date must be a valid ISO format YYYY-MM-DD.")

    if "notes" in raw_params and isinstance(raw_params["notes"], str) and raw_params["notes"].strip():
        sanitized["notes"] = raw_params["notes"].strip()

    if errors:
        return schemas.ActionValidationResult(
            is_valid=False,
            action=raw_action,
            normalized_action=normalized_action,
            errors=errors,
            sanitized_parameters={},
        )

    return schemas.ActionValidationResult(
        is_valid=True,
        action=raw_action,
        normalized_action=normalized_action,
        errors=[],
        sanitized_parameters=sanitized,
    )


# ============================================================================
# 18.6 COMMUNITY ACTION PERMISSION & MEMBERSHIP GATE (Step 9.2)
# ============================================================================

def authorize_community_action(
    db: Session,
    community_id: int,
    requester_id: Optional[int],
    validation_result: schemas.ActionValidationResult,
) -> schemas.ActionAuthorizationResult:
    """
    Step 9.2 Permission & Membership Gate.
    Evaluates whether an authenticated member is permitted to request an action:
    1. Action validation check: If validation_result.is_valid is False -> INVALID_ACTION (400)
    2. Authentication check: If requester_id is None or <= 0 -> UNAUTHENTICATED (401)
    3. Community existence: If community does not exist in DB -> COMMUNITY_NOT_FOUND (404)
    4. Membership verification: If requester is not an enrolled community member -> NOT_A_MEMBER (403)
    5. Authorized: If all gates pass -> AUTHORIZED (200)

    Guarantees zero database writes and zero action execution.
    """
    action_str = validation_result.action or (
        validation_result.normalized_action.value if validation_result.normalized_action else None
    )

    # 1. Action must be validated first (reject invalid/hallucinated before membership checks)
    if not validation_result.is_valid:
        error_msg = "; ".join(validation_result.errors) if validation_result.errors else "Action validation failed."
        return schemas.ActionAuthorizationResult(
            is_authorized=False,
            status="INVALID_ACTION",
            status_code=400,
            community_id=community_id,
            requester_id=requester_id,
            action=action_str,
            message=f"Action validation rejected: {error_msg}",
        )

    # 2. Authentication check
    if requester_id is None or requester_id <= 0:
        return schemas.ActionAuthorizationResult(
            is_authorized=False,
            status="UNAUTHENTICATED",
            status_code=401,
            community_id=community_id,
            requester_id=requester_id,
            action=action_str,
            message="Authentication required to request community action.",
        )

    # 3. Community existence check (read-only query)
    comm = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not comm:
        return schemas.ActionAuthorizationResult(
            is_authorized=False,
            status="COMMUNITY_NOT_FOUND",
            status_code=404,
            community_id=community_id,
            requester_id=requester_id,
            action=action_str,
            message=f"Community #{community_id} does not exist.",
        )

    # 4. Membership verification (read-only query)
    membership = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == requester_id,
        )
        .first()
    )
    if not membership:
        return schemas.ActionAuthorizationResult(
            is_authorized=False,
            status="NOT_A_MEMBER",
            status_code=403,
            community_id=community_id,
            requester_id=requester_id,
            action=action_str,
            message=f"User #{requester_id} is not a member of Community #{community_id}.",
        )

    # 5. All gates passed -> Authorized
    return schemas.ActionAuthorizationResult(
        is_authorized=True,
        status="AUTHORIZED",
        status_code=200,
        community_id=community_id,
        requester_id=requester_id,
        action=action_str,
        message=f"User #{requester_id} is authorized to request action '{action_str}' on Community #{community_id}.",
    )


# ============================================================================
# 18.7 COMMUNITY ACTION EXECUTION DISPATCHER (Step 9.3)
# ============================================================================

def _handle_create_event_action(
    community_id: int, requester_id: int, params: Dict[str, Any], db: Session
) -> schemas.ActionExecutionResult:
    """
    Step 9.4 Concrete Action Execution Handler for CREATE_EVENT.
    - Re-validates domain business rules against database (activity exists, community & member exist).
    - Validates date/time (cannot be in the past, end_time > start_time).
    - Validates capacity (positive integer within limits).
    - Checks for duplicate events and scheduling conflicts for the host.
    - Executes event creation atomically within a database transaction.
    - Automatically enrolls the requester/host as a CONFIRMED EventParticipant.
    - Guarantees strict rollback on any failure, leaving zero partial records.
    - Returns structured ActionExecutionResult.
    """
    action_str = schemas.AllowedAction.CREATE_EVENT.value

    # 1. Verify community existence
    community = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not community:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="Community does not exist.",
            details={"reason": "community_not_found"},
            executed_at=None,
        )

    # 2. Verify requester exists and is a community member
    requester = db.query(models.User).filter(models.User.user_id == requester_id).first()
    if not requester:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="Requester user does not exist.",
            details={"reason": "requester_not_found"},
            executed_at=None,
        )

    membership = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == requester_id,
        )
        .first()
    )
    if not membership:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="Requester is not an enrolled member of this community.",
            details={"reason": "not_a_member"},
            executed_at=None,
        )

    # 3. Validate activity template
    activity_id = params.get("activity_id")
    if not activity_id or not isinstance(activity_id, int) or activity_id <= 0:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="A valid positive activity_id is required to create an event.",
            details={"reason": "invalid_activity_id"},
            executed_at=None,
        )

    activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
    if not activity:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"Activity template #{activity_id} not found.",
            details={"reason": "activity_not_found", "activity_id": activity_id},
            executed_at=None,
        )

    # 4. Validate event date
    event_date_val = params.get("event_date")
    if not event_date_val:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="event_date is required for event creation.",
            details={"reason": "missing_event_date"},
            executed_at=None,
        )

    if isinstance(event_date_val, str):
        try:
            parsed_event_date = date.fromisoformat(event_date_val)
        except (ValueError, TypeError):
            return schemas.ActionExecutionResult(
                community_id=community_id,
                action=action_str,
                status="REJECTED",
                success=False,
                message=f"Invalid event_date format: '{event_date_val}'. Must be YYYY-MM-DD.",
                details={"reason": "invalid_date_format"},
                executed_at=None,
            )
    elif isinstance(event_date_val, date):
        parsed_event_date = event_date_val
    else:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="event_date must be a valid date object or ISO string.",
            details={"reason": "invalid_date_type"},
            executed_at=None,
        )

    if parsed_event_date < date.today():
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"event_date ({parsed_event_date}) cannot be in the past.",
            details={"reason": "date_in_past", "event_date": parsed_event_date.isoformat()},
            executed_at=None,
        )

    # 5. Validate start and end times
    start_time_val = params.get("start_time")
    end_time_val = params.get("end_time")

    if not start_time_val:
        parsed_start_time = time(18, 0)
    elif isinstance(start_time_val, str):
        try:
            parsed_start_time = time.fromisoformat(start_time_val)
        except (ValueError, TypeError):
            return schemas.ActionExecutionResult(
                community_id=community_id,
                action=action_str,
                status="REJECTED",
                success=False,
                message=f"Invalid start_time format: '{start_time_val}'. Must be HH:MM or HH:MM:SS.",
                details={"reason": "invalid_start_time_format"},
                executed_at=None,
            )
    elif isinstance(start_time_val, time):
        parsed_start_time = start_time_val
    else:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="start_time must be a valid time object or ISO string.",
            details={"reason": "invalid_start_time_type"},
            executed_at=None,
        )

    if not end_time_val:
        new_hour = min(23, parsed_start_time.hour + 2)
        parsed_end_time = time(new_hour, parsed_start_time.minute, parsed_start_time.second) if new_hour > parsed_start_time.hour else time(23, 59, 59)
    elif isinstance(end_time_val, str):
        try:
            parsed_end_time = time.fromisoformat(end_time_val)
        except (ValueError, TypeError):
            return schemas.ActionExecutionResult(
                community_id=community_id,
                action=action_str,
                status="REJECTED",
                success=False,
                message=f"Invalid end_time format: '{end_time_val}'. Must be HH:MM or HH:MM:SS.",
                details={"reason": "invalid_end_time_format"},
                executed_at=None,
            )
    elif isinstance(end_time_val, time):
        parsed_end_time = end_time_val
    else:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="end_time must be a valid time object or ISO string.",
            details={"reason": "invalid_end_time_type"},
            executed_at=None,
        )

    if parsed_end_time <= parsed_start_time:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="end_time must be strictly after start_time.",
            details={
                "reason": "invalid_time_range",
                "start_time": parsed_start_time.isoformat(),
                "end_time": parsed_end_time.isoformat(),
            },
            executed_at=None,
        )

    # 6. Validate capacity
    max_capacity_val = params.get("max_capacity")
    if max_capacity_val is None:
        max_capacity = 10
    elif isinstance(max_capacity_val, bool) or not isinstance(max_capacity_val, (int, float)):
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="max_capacity must be a positive integer between 1 and 500.",
            details={"reason": "invalid_capacity"},
            executed_at=None,
        )
    else:
        max_capacity = int(max_capacity_val)
        if max_capacity <= 0 or max_capacity > 500:
            return schemas.ActionExecutionResult(
                community_id=community_id,
                action=action_str,
                status="REJECTED",
                success=False,
                message="max_capacity must be between 1 and 500.",
                details={"reason": "capacity_out_of_range", "max_capacity": max_capacity},
                executed_at=None,
            )

    # 7. Title resolution
    raw_title = params.get("title")
    if raw_title and isinstance(raw_title, str) and raw_title.strip():
        event_title = raw_title.strip()[:200]
    else:
        event_title = f"{community.name} - {activity.title} Gathering"[:200]

    # 8. Duplicate event check (same host, date, and title)
    duplicate_event = (
        db.query(models.Event)
        .filter(
            models.Event.host_id == requester_id,
            models.Event.event_date == parsed_event_date,
            models.Event.title == event_title,
            models.Event.status != "CANCELLED",
        )
        .first()
    )
    if duplicate_event:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"Duplicate event: Event #{duplicate_event.event_id} with the same title already exists on {parsed_event_date}.",
            details={"reason": "duplicate_event", "existing_event_id": duplicate_event.event_id},
            executed_at=None,
        )

    # 9. Host schedule conflict check (overlapping time window on same date)
    conflict_event = (
        db.query(models.Event)
        .filter(
            models.Event.host_id == requester_id,
            models.Event.event_date == parsed_event_date,
            models.Event.status != "CANCELLED",
            models.Event.start_time < parsed_end_time,
            models.Event.end_time > parsed_start_time,
        )
        .first()
    )
    if conflict_event:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"Schedule conflict: Host already has Event #{conflict_event.event_id} ('{conflict_event.title}') scheduled during this time ({conflict_event.start_time} - {conflict_event.end_time}).",
            details={"reason": "schedule_conflict", "conflicting_event_id": conflict_event.event_id},
            executed_at=None,
        )

    # 10. Atomic Execution & Rollback Guardrail
    try:
        new_event = models.Event(
            activity_id=activity.activity_id,
            host_id=requester_id,
            title=event_title,
            event_date=parsed_event_date,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            max_capacity=max_capacity,
            status="PUBLISHED",
        )
        db.add(new_event)
        db.flush()

        # Automatically enroll host as confirmed participant
        host_participant = models.EventParticipant(
            event_id=new_event.event_id,
            user_id=requester_id,
            status="CONFIRMED",
        )
        db.add(host_participant)
        db.commit()
        db.refresh(new_event)

        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="COMPLETED",
            success=True,
            message=f"Event #{new_event.event_id} '{new_event.title}' successfully created and published.",
            details={
                "event_id": new_event.event_id,
                "title": new_event.title,
                "activity_id": new_event.activity_id,
                "host_id": new_event.host_id,
                "event_date": new_event.event_date.isoformat(),
                "start_time": new_event.start_time.isoformat(),
                "end_time": new_event.end_time.isoformat(),
                "max_capacity": new_event.max_capacity,
                "status": new_event.status,
            },
            executed_at=datetime.now(),
        )
    except Exception as ex:
        db.rollback()
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="FAILED",
            success=False,
            message=f"Database execution failed during event creation: {str(ex)}",
            details={"reason": "database_error", "error": str(ex)},
            executed_at=datetime.now(),
        )


def _handle_re_engage_members_action(
    community_id: int, requester_id: int, params: Dict[str, Any], db: Session
) -> schemas.ActionExecutionResult:
    """
    Step 9.5 Concrete Action Execution Handler for RE_ENGAGE_MEMBERS.
    - Re-validates domain business rules against database (community exists, requester exists & is member).
    - Validates parameters (target_inactive_days, message length & sanitization).
    - Identifies eligible inactive community members (excluding requester).
    - Builds controlled, personalized notification payloads ready for dispatch.
    - Enforces zero uncontrolled external messaging (prepares/records notification batch deterministically).
    - Returns structured ActionExecutionResult with full audit payload.
    """
    action_str = schemas.AllowedAction.RE_ENGAGE_MEMBERS.value

    # 1. Verify community existence
    community = db.query(models.Community).filter(models.Community.community_id == community_id).first()
    if not community:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="Community does not exist.",
            details={"reason": "community_not_found"},
            executed_at=None,
        )

    # 2. Verify requester exists and is a community member
    requester = db.query(models.User).filter(models.User.user_id == requester_id).first()
    if not requester:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="Requester user does not exist.",
            details={"reason": "requester_not_found"},
            executed_at=None,
        )

    membership = (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == requester_id,
        )
        .first()
    )
    if not membership:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="Requester is not an enrolled member of this community.",
            details={"reason": "not_a_member"},
            executed_at=None,
        )

    # 3. Validate target_inactive_days parameter
    target_inactive_days_val = params.get("target_inactive_days")
    if target_inactive_days_val is None:
        target_inactive_days = 14
    elif isinstance(target_inactive_days_val, bool) or not isinstance(target_inactive_days_val, int) or target_inactive_days_val <= 0 or target_inactive_days_val > 365:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message="target_inactive_days must be a positive integer between 1 and 365.",
            details={"reason": "invalid_target_inactive_days"},
            executed_at=None,
        )
    else:
        target_inactive_days = target_inactive_days_val

    # 4. Validate custom message parameter
    raw_message = params.get("message")
    if raw_message is not None:
        if not isinstance(raw_message, str) or not raw_message.strip():
            return schemas.ActionExecutionResult(
                community_id=community_id,
                action=action_str,
                status="REJECTED",
                success=False,
                message="message cannot be blank or whitespace-only if provided.",
                details={"reason": "invalid_message"},
                executed_at=None,
            )
        if len(raw_message.strip()) > 500:
            return schemas.ActionExecutionResult(
                community_id=community_id,
                action=action_str,
                status="REJECTED",
                success=False,
                message="message cannot exceed 500 characters.",
                details={"reason": "message_too_long"},
                executed_at=None,
            )
        notification_message = raw_message.strip()
    else:
        notification_message = f"We miss you in {community.name}! Check out our latest activities and reconnect with your fellow members."

    # 5. Identify candidate community members (excluding requester)
    all_members = (
        db.query(models.CommunityMember)
        .filter(models.CommunityMember.community_id == community_id)
        .all()
    )
    candidate_member_ids = [m.user_id for m in all_members if m.user_id != requester_id]

    if not candidate_member_ids:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"No other members found in community '{community.name}' to re-engage.",
            details={"reason": "no_other_members", "community_id": community_id},
            executed_at=None,
        )

    # 6. Identify inactive members based on target_inactive_days
    cutoff_date = date.today() - timedelta(days=target_inactive_days)

    # Active participants in confirmed events since cutoff_date
    recent_participant_uids = {
        row[0]
        for row in db.query(models.EventParticipant.user_id)
        .join(models.Event, models.EventParticipant.event_id == models.Event.event_id)
        .filter(
            models.EventParticipant.user_id.in_(candidate_member_ids),
            models.EventParticipant.status == "CONFIRMED",
            models.Event.event_date >= cutoff_date,
        )
        .all()
    }

    # Active event hosts since cutoff_date
    recent_host_uids = {
        row[0]
        for row in db.query(models.Event.host_id)
        .filter(
            models.Event.host_id.in_(candidate_member_ids),
            models.Event.event_date >= cutoff_date,
            models.Event.status != "CANCELLED",
        )
        .all()
    }

    active_uids = recent_participant_uids.union(recent_host_uids)
    eligible_inactive_uids = [uid for uid in candidate_member_ids if uid not in active_uids]

    if not eligible_inactive_uids:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="COMPLETED",
            success=True,
            message=f"All {len(candidate_member_ids)} community members are currently active (active within last {target_inactive_days} days). No re-engagement necessary.",
            details={
                "community_id": community_id,
                "community_name": community.name,
                "target_inactive_days": target_inactive_days,
                "total_candidate_members": len(candidate_member_ids),
                "eligible_member_count": 0,
                "eligible_member_ids": [],
                "prepared_notifications": [],
                "delivery_status": "NO_INACTIVE_MEMBERS",
            },
            executed_at=datetime.now(),
        )

    # 7. Build deterministic, controlled notification payloads
    users = db.query(models.User).filter(models.User.user_id.in_(eligible_inactive_uids)).all()
    user_map = {u.user_id: u for u in users}

    prepared_notifications = []
    for uid in eligible_inactive_uids:
        target_user = user_map.get(uid)
        prepared_notifications.append({
            "recipient_id": uid,
            "recipient_email": target_user.email if target_user else f"user_{uid}@vynk.local",
            "community_id": community_id,
            "community_name": community.name,
            "message": notification_message,
            "channel": "IN_APP",
            "status": "PREPARED",
            "prepared_at": datetime.now().isoformat(),
        })

    return schemas.ActionExecutionResult(
        community_id=community_id,
        action=action_str,
        status="COMPLETED",
        success=True,
        message=f"Successfully prepared re-engagement notifications for {len(prepared_notifications)} inactive member(s) in '{community.name}'.",
        details={
            "community_id": community_id,
            "community_name": community.name,
            "target_inactive_days": target_inactive_days,
            "message": notification_message,
            "total_candidate_members": len(candidate_member_ids),
            "eligible_member_count": len(eligible_inactive_uids),
            "eligible_member_ids": eligible_inactive_uids,
            "prepared_notifications": prepared_notifications,
            "delivery_status": "PREPARED_FOR_DELIVERY",
        },
        executed_at=datetime.now(),
    )


def _handle_collect_feedback_action(
    community_id: int, requester_id: int, params: Dict[str, Any], db: Session
) -> schemas.ActionExecutionResult:
    """Explicitly controlled handler stub for COLLECT_FEEDBACK."""
    return schemas.ActionExecutionResult(
        community_id=community_id,
        action=schemas.AllowedAction.COLLECT_FEEDBACK.value,
        status="READY",
        success=True,
        message="Handler for COLLECT_FEEDBACK dispatched successfully.",
        details={"dispatched_handler": "collect_feedback", "sanitized_parameters": params},
        executed_at=datetime.now(),
    )


def _handle_grow_membership_action(
    community_id: int, requester_id: int, params: Dict[str, Any], db: Session
) -> schemas.ActionExecutionResult:
    """Explicitly controlled handler stub for GROW_MEMBERSHIP."""
    return schemas.ActionExecutionResult(
        community_id=community_id,
        action=schemas.AllowedAction.GROW_MEMBERSHIP.value,
        status="READY",
        success=True,
        message="Handler for GROW_MEMBERSHIP dispatched successfully.",
        details={"dispatched_handler": "grow_membership", "sanitized_parameters": params},
        executed_at=datetime.now(),
    )


def _handle_maintain_activity_action(
    community_id: int, requester_id: int, params: Dict[str, Any], db: Session
) -> schemas.ActionExecutionResult:
    """Explicitly controlled handler stub for MAINTAIN_ACTIVITY."""
    return schemas.ActionExecutionResult(
        community_id=community_id,
        action=schemas.AllowedAction.MAINTAIN_ACTIVITY.value,
        status="READY",
        success=True,
        message="Handler for MAINTAIN_ACTIVITY dispatched successfully.",
        details={"dispatched_handler": "maintain_activity", "sanitized_parameters": params},
        executed_at=datetime.now(),
    )


def _handle_reactivate_community_action(
    community_id: int, requester_id: int, params: Dict[str, Any], db: Session
) -> schemas.ActionExecutionResult:
    """Explicitly controlled handler stub for REACTIVATE_COMMUNITY."""
    return schemas.ActionExecutionResult(
        community_id=community_id,
        action=schemas.AllowedAction.REACTIVATE_COMMUNITY.value,
        status="READY",
        success=True,
        message="Handler for REACTIVATE_COMMUNITY dispatched successfully.",
        details={"dispatched_handler": "reactivate_community", "sanitized_parameters": params},
        executed_at=datetime.now(),
    )


COMMUNITY_ACTION_HANDLERS = {
    schemas.AllowedAction.CREATE_EVENT: _handle_create_event_action,
    schemas.AllowedAction.RE_ENGAGE_MEMBERS: _handle_re_engage_members_action,
    schemas.AllowedAction.COLLECT_FEEDBACK: _handle_collect_feedback_action,
    schemas.AllowedAction.GROW_MEMBERSHIP: _handle_grow_membership_action,
    schemas.AllowedAction.MAINTAIN_ACTIVITY: _handle_maintain_activity_action,
    schemas.AllowedAction.REACTIVATE_COMMUNITY: _handle_reactivate_community_action,
}


def dispatch_community_action(
    db: Session,
    community_id: int,
    requester_id: int,
    validation_result: schemas.ActionValidationResult,
    authorization_result: schemas.ActionAuthorizationResult,
) -> schemas.ActionExecutionResult:
    """
    Step 9.3 Controlled Execution Dispatcher.
    - Accepts already validated and authorized actions.
    - Enforces that unvalidated or unauthorized requests cannot be dispatched.
    - Maps strictly by AllowedAction enum keys, preventing arbitrary function selection.
    - Encapsulates unexpected handler exceptions into structured FAILED responses.
    - Causes zero unintended database mutations.
    """
    action_str = (
        validation_result.normalized_action.value
        if validation_result.normalized_action
        else (validation_result.action or "UNKNOWN")
    )

    # 1. Validation check
    if not validation_result.is_valid or not validation_result.normalized_action:
        error_msg = "; ".join(validation_result.errors) if validation_result.errors else "Action validation failed."
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"Dispatcher blocked execution: action is invalid ({error_msg}).",
            details={"reason": "validation_failed", "errors": validation_result.errors},
            executed_at=None,
        )

    # 2. Authorization check
    if not authorization_result.is_authorized:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"Dispatcher blocked execution: authorization rejected ({authorization_result.message}).",
            details={"reason": "authorization_failed", "auth_status": authorization_result.status},
            executed_at=None,
        )

    # 3. Handler lookup (strictly using AllowedAction Enum key)
    handler = COMMUNITY_ACTION_HANDLERS.get(validation_result.normalized_action)
    if not handler:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="REJECTED",
            success=False,
            message=f"Dispatcher error: No handler registered for action '{action_str}'.",
            details={"reason": "unregistered_action"},
            executed_at=None,
        )

    # 4. Safe execution
    try:
        return handler(
            community_id=community_id,
            requester_id=requester_id,
            params=validation_result.sanitized_parameters,
            db=db,
        )
    except Exception as ex:
        return schemas.ActionExecutionResult(
            community_id=community_id,
            action=action_str,
            status="FAILED",
            success=False,
            message=f"Execution failed during dispatch of '{action_str}': {str(ex)}",
            details={"error_type": type(ex).__name__, "error": str(ex)},
            executed_at=datetime.now(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)




