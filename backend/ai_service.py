import json
import os
import re
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

import schemas

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_INTENT_PROMPT = """You are the AI Intent Understanding Engine for Localy (Vynk), a local real-world activity, talent, venue booking, and community platform.
Analyze the user's input sentence and extract structured intent parameters for downstream database matching and event discovery.

Extract the following JSON structure:
{
  "intent": "find_activity_and_people" | "find_people" | "find_event" | "find_venue" | "create_event" | "general_inquiry",
  "activity": "<activity name, e.g. Badminton, Cricket, Acoustic Guitar, Python, Photography, Chess, or null>",
  "category": "Sports" | "Music" | "Technology" | "Creative" | "Learning" | "Social" | null,
  "day_of_week": "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday" | "Sunday" | "Weekend" | "Today" | "Tomorrow" | null,
  "time_of_day": "morning" | "afternoon" | "evening" | "night" | null,
  "location": "<extracted locality or area, e.g. Indiranagar, Sarjapur Road, Whitefield, nearby, or null>",
  "skill_level": "beginner" | "intermediate" | "advanced" | null,
  "budget_preference": "free" | "low" | "moderate" | "flexible" | null,
  "group_size": <integer count if mentioned, or null>,
  "confidence": <float between 0.0 and 1.0>
}

Respond ONLY with valid JSON. Do not include markdown fences or explanation.
"""

# Categorical taxonomy mappings for heuristic fallback
CATEGORY_KEYWORDS = {
    "Sports": ["table tennis", "box cricket", "badminton", "cricket", "football", "tennis", "swimming", "cycling", "running", "volleyball", "basketball", "turf", "ground", "doubles"],
    "Music": ["acoustic guitar", "music production", "guitar", "vocals", "singing", "keyboard", "piano", "drums", "jamming"],
    "Technology": ["machine learning", "web development", "python", "artificial intelligence", "flutter", "react", "coding", "hackathon", "devops", "ai", "ml"],
    "Creative": ["video editing", "photography", "painting", "writing", "poetry", "comedy", "stand-up", "filmmaking"],
    "Learning": ["book club", "storytelling", "startup", "entrepreneurship", "mentorship", "reading"],
    "Social": ["board games", "chess", "coffee meetup", "hangout"]
}


def _heuristic_intent_parser(query: str) -> Dict[str, Any]:
    """Deterministic fallback NLP heuristic parser when OpenAI API key is unavailable or offline."""
    q_lower = query.lower().strip()

    # 1. Determine Day
    day = None
    days_map = {
        "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
        "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday",
        "sunday": "Sunday", "weekend": "Weekend", "today": "Today", "tomorrow": "Tomorrow"
    }
    for k, v in days_map.items():
        if k in q_lower:
            day = v
            break

    # 2. Determine Time of Day
    time_of_day = None
    times = ["morning", "afternoon", "evening", "night"]
    for t in times:
        if t in q_lower:
            time_of_day = t
            break

    # 3. Determine Category & Activity
    detected_cat = None
    detected_act = None

    for cat, keywords in CATEGORY_KEYWORDS.items():
        # Match longest keywords first so multi-word terms (e.g. "table tennis") take precedence over "tennis"
        sorted_kws = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kws:
            if kw in q_lower:
                detected_cat = cat
                detected_act = kw.capitalize()
                break
        if detected_act:
            break

    # 4. Location extraction
    location = None
    if "near me" in q_lower or "nearby" in q_lower or "around me" in q_lower:
        location = "nearby"
    else:
        known_localities = ["indiranagar", "sarjapur", "koramangala", "whitefield", "hsr", "jayanagar", "banjara hills", "jubilee hills"]
        for loc in known_localities:
            if loc in q_lower:
                location = loc.capitalize()
                break

    # 5. Skill Level
    skill_level = None
    if "beginner" in q_lower or "starter" in q_lower or "newbie" in q_lower:
        skill_level = "beginner"
    elif "intermediate" in q_lower or "casual" in q_lower or "medium" in q_lower or "my level" in q_lower:
        skill_level = "intermediate"
    elif "advanced" in q_lower or "pro" in q_lower or "competitive" in q_lower or "expert" in q_lower:
        skill_level = "advanced"

    # 6. Intent classification
    intent = "find_activity_and_people"
    if "host" in q_lower or "create" in q_lower or "organize" in q_lower:
        intent = "create_event"
    elif "venue" in q_lower or "court" in q_lower or "ground" in q_lower or "turf" in q_lower:
        intent = "find_venue" if "find" in q_lower else "find_activity_and_people"
    elif "people" in q_lower or "partner" in q_lower or "players" in q_lower or "someone" in q_lower:
        intent = "find_people" if not detected_act else "find_activity_and_people"

    # 7. Group size
    group_size = None
    num_match = re.search(r'\b(\d+)\s*(people|players|members|vs|v)\b', q_lower)
    if num_match:
        try:
            group_size = int(num_match.group(1))
        except ValueError:
            pass

    return {
        "intent": intent,
        "activity": detected_act,
        "category": detected_cat,
        "day_of_week": day,
        "time_of_day": time_of_day,
        "location": location,
        "skill_level": skill_level,
        "budget_preference": "flexible",
        "group_size": group_size,
        "confidence": 0.88,
        "engine": "semantic-rules-engine"
    }


def understand_user_intent(query: str) -> schemas.AIIntentResponse:
    """
    Core AI Intent Understanding Service:
    Sends natural language prompt to OpenAI and parses structured intent,
    with an intelligent fallback if no API key is provided.
    """
    raw_query = query.strip()

    # If OpenAI API Key is provided, call OpenAI with JSON Schema mode
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("mock"):
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_INTENT_PROMPT},
                    {"role": "user", "content": raw_query},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return schemas.AIIntentResponse(
                        raw_query=raw_query,
                        intent=parsed.get("intent", "find_activity_and_people"),
                        activity=parsed.get("activity"),
                        category=parsed.get("category"),
                        day_of_week=parsed.get("day_of_week"),
                        time_of_day=parsed.get("time_of_day"),
                        location=parsed.get("location"),
                        skill_level=parsed.get("skill_level"),
                        budget_preference=parsed.get("budget_preference"),
                        group_size=parsed.get("group_size"),
                        confidence=float(parsed.get("confidence", 0.95)),
                        engine=f"openai-{OPENAI_MODEL}",
                    )
        except Exception as e:
            # Fallback gracefully on network/auth error
            pass

    # Fallback to local semantic heuristic parser
    parsed = _heuristic_intent_parser(raw_query)
    return schemas.AIIntentResponse(
        raw_query=raw_query,
        intent=parsed["intent"],
        activity=parsed["activity"],
        category=parsed["category"],
        day_of_week=parsed["day_of_week"],
        time_of_day=parsed["time_of_day"],
        location=parsed["location"],
        skill_level=parsed["skill_level"],
        budget_preference=parsed["budget_preference"],
        group_size=parsed["group_size"],
        confidence=parsed["confidence"],
        engine=parsed["engine"],
    )
