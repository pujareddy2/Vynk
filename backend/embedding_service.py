"""
Vynk (Localy) - AI Semantic Embedding Service
Generates and manages 1536-dimensional embeddings for Users (Profiles) and Activities.
Supports OpenAI text-embedding-3-small with a resilient normalized semantic hash fallback.
"""

import hashlib
import json
import math
import os
from typing import List, Optional
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

import models

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = 1536


def _l2_normalize(vector: List[float]) -> List[float]:
    """Normalizes a float vector to unit length (L2 norm = 1.0)."""
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


def compute_cosine_similarity(vec_a: Optional[List[float]], vec_b: Optional[List[float]]) -> float:
    """Calculates cosine similarity between two unit-normalized embedding vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(0.0, min(1.0, float(dot)))


def _deterministic_pseudo_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Deterministic semantic hash embedding fallback when OpenAI API key is not configured.
    Distributes token hashes and bigrams across the 1536-dimensional space with L2 normalization.
    """
    vec = [0.0] * dim
    clean_text = text.lower().strip()
    words = clean_text.replace(".", " ").replace(",", " ").replace(":", " ").split()

    # Unigram distribution
    for word in words:
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
        vec[idx] += sign * 1.5

    # Bigram distribution for phrase semantics (e.g. 'badminton coaching', 'table tennis')
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        h_bi = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
        idx_bi = h_bi % dim
        sign_bi = 1.0 if ((h_bi >> 8) % 2 == 0) else -1.0
        vec[idx_bi] += sign_bi * 2.0

    return _l2_normalize(vec)


def generate_embedding(text_input: str) -> List[float]:
    """
    Calls OpenAI Embeddings API (text-embedding-3-small, 1536 dim)
    or falls back to deterministic normalized semantic embedding generator.
    """
    raw_text = text_input.strip()
    if not raw_text:
        return [0.0] * EMBEDDING_DIM

    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("mock"):
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": EMBEDDING_MODEL,
                "input": raw_text,
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    embedding = data["data"][0]["embedding"]
                    return embedding
        except Exception:
            # Fallback gracefully
            pass

    return _deterministic_pseudo_embedding(raw_text, dim=EMBEDDING_DIM)


def build_user_semantic_text(user: models.User, db: Session) -> str:
    """
    Constructs a dense, structured text profile of a user for vector embedding generation.
    Aggregates display name, locality, bio, interests, offered skills, and schedule availability.
    """
    profile = user.profile
    interests = [ui.interest.name for ui in user.interests if ui.interest]
    skills = [f"{us.skill.name} ({us.skill_level})" for us in user.skills if us.skill and us.is_offering]
    avails = [
        f"{a.day_of_week}" + (f" ({a.start_time.strftime('%H:%M')}-{a.end_time.strftime('%H:%M')})" if a.start_time and a.end_time else "")
        for a in user.availability
    ]

    parts = [
        f"User Profile: {profile.display_name if profile else user.email}.",
        f"Locality: {profile.approx_locality}." if profile and profile.approx_locality else "",
        f"Bio: {profile.bio}." if profile and profile.bio else "",
        f"Interests: {', '.join(interests)}." if interests else "",
        f"Offered Skills: {', '.join(skills)}." if skills else "",
        f"Availability: {', '.join(avails)}." if avails else "",
        f"Budget Preference: {profile.budget_preference}." if profile and profile.budget_preference else "",
    ]
    return " ".join(p for p in parts if p)


def build_activity_semantic_text(activity: models.Activity) -> str:
    """
    Constructs a dense, structured text representation of an activity template for vector embedding generation.
    """
    category = activity.interest.category if activity.interest else "General"
    interest_name = activity.interest.name if activity.interest else ""
    parts = [
        f"Activity: {activity.title}.",
        f"Category: {category}.",
        f"Interest: {interest_name}." if interest_name else "",
        f"Description: {activity.description}." if activity.description else "",
    ]
    return " ".join(p for p in parts if p)


def update_user_embedding(user_id: int, db: Session) -> Optional[List[float]]:
    """Generates and persists the vector embedding for a specific user profile."""
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        return None

    profile = user.profile
    if not profile:
        profile = models.Profile(user_id=user.user_id, display_name=user.email.split("@")[0].capitalize())
        db.add(profile)
        db.flush()

    semantic_text = build_user_semantic_text(user, db)
    embedding = generate_embedding(semantic_text)
    profile.embedding = embedding
    db.commit()
    db.refresh(profile)
    return embedding


def update_activity_embedding(activity_id: int, db: Session) -> Optional[List[float]]:
    """Generates and persists the vector embedding for a specific activity template."""
    activity = db.query(models.Activity).filter(models.Activity.activity_id == activity_id).first()
    if not activity:
        return None

    semantic_text = build_activity_semantic_text(activity)
    embedding = generate_embedding(semantic_text)
    activity.embedding = embedding
    db.commit()
    db.refresh(activity)
    return embedding


def backfill_all_embeddings(db: Session) -> dict:
    """Batch-generates embeddings for all active users and activity templates."""
    users = db.query(models.User).filter(models.User.is_active.is_(True)).all()
    user_count = 0
    for u in users:
        update_user_embedding(u.user_id, db)
        user_count += 1

    activities = db.query(models.Activity).all()
    activity_count = 0
    for a in activities:
        update_activity_embedding(a.activity_id, db)
        activity_count += 1

    return {
        "users_embedded": user_count,
        "activities_embedded": activity_count,
    }
