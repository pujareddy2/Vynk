from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from auth import create_access_token, get_current_user, hash_password, verify_password
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
    description="Localy Backend REST API — AI-Powered Local Activity, Talent & Community Network.",
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
# SYSTEM ENDPOINTS
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
# AUTHENTICATION ENDPOINTS
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
    summary="Login and obtain JWT access token",
)
def login(
    req: schemas.UserLoginRequest,
    db: Session = Depends(get_db),
):
    normalized_email = req.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == normalized_email).first()

    if not user or not verify_password(req.password, user.password_hash):
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
# MASTER CATALOG ENDPOINTS (INTERESTS & SKILLS)
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
# USER PROFILE & ONBOARDING ENDPOINTS
# ============================================================================

def _build_full_profile(user: models.User, db: Session) -> schemas.FullProfileResponse:
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.user_id).first()
    
    # User interests
    user_ints = (
        db.query(models.Interest)
        .join(models.UserInterest, models.Interest.interest_id == models.UserInterest.interest_id)
        .filter(models.UserInterest.user_id == user.user_id)
        .all()
    )

    # User skills
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

    # Availability
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
    # Clear existing and replace with new selections
    db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).delete()
    for i_id in set(interest_ids):
        # Verify interest exists
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
    # 1. Update Profile fields
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.user_id).first()
    if not profile:
        profile = models.Profile(user_id=current_user.user_id, display_name=req.display_name)
        db.add(profile)
    profile.display_name = req.display_name
    profile.bio = req.bio
    profile.avatar_url = req.avatar_url
    profile.approx_locality = req.approx_locality
    profile.budget_preference = req.budget_preference

    # 2. Update Interests
    db.query(models.UserInterest).filter(models.UserInterest.user_id == current_user.user_id).delete()
    for i_id in set(req.interest_ids):
        if db.query(models.Interest).filter(models.Interest.interest_id == i_id).first():
            db.add(models.UserInterest(user_id=current_user.user_id, interest_id=i_id))

    # 3. Update Skills
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

    # 4. Update Availability
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
