import json
import os
import re
from typing import Any, Dict, List, Optional, Set, Union
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


# ============================================================================
# AI EXPERIENCE GENERATOR SYNTHESIS
# ============================================================================

SYSTEM_EXPERIENCE_PROMPT = """You are the AI Experience Generator for Localy (Vynk).
Your job is to transform verified backend facts into a rich, structured, and engaging real-world experience plan.

CRITICAL RULES:
1. You MUST NOT invent or change any facts:
   - Do NOT change the activity name, venue name, address, price, date, times, or participant names.
   - All factual data must strictly reflect the provided facts.
2. Generate:
   - experience_title: An exciting headline (e.g. 'Saturday Badminton Doubles Championship')
   - tagline: A compelling 1-sentence description
   - why_this_works: 3-4 bullet points explaining why this plan works based on participant availability, venue slot, and locality
   - agenda: An array of 3-4 structured timeline items (time_window, title, description)
   - preparation_checklist: An array of 3-4 items or gear to bring

Respond ONLY with valid JSON with keys:
{
  "experience_title": "...",
  "tagline": "...",
  "why_this_works": ["...", "..."],
  "agenda": [
    {"time_window": "...", "title": "...", "description": "..."},
    ...
  ],
  "preparation_checklist": ["...", "..."]
}
Do not include markdown code fences or explanatory text.
"""

def generate_ai_experience_plan(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synthesize an engaging experience plan based on strictly verified backend facts.
    Uses OpenAI GPT when available; otherwise falls back to a deterministic heuristic engine.
    """
    activity_name = facts.get("activity_name", "Activity")
    category = facts.get("category", "Sports")
    locality = facts.get("locality", "Local area")
    venue_name = facts.get("venue_name")
    target_size = facts.get("target_size", 4)
    start_time_str = facts.get("start_time_str", "18:00")
    end_time_str = facts.get("end_time_str", "20:00")
    candidate_names = facts.get("suggested_cohort_names", [])
    per_person_cost = facts.get("per_person_cost")

    if OPENAI_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            user_prompt = f"""Verified facts:
Activity: {activity_name} ({category})
Locality: {locality}
Venue: {venue_name or 'Local community ground / space'}
Start Time: {start_time_str}
End Time: {end_time_str}
Target Group Size: {target_size} players
Estimated Cost Per Person: INR {per_person_cost if per_person_cost is not None else 0.0}
Available Participants: {', '.join(candidate_names) if candidate_names else 'Open public cohort'}
"""
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_EXPERIENCE_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return {
                        "experience_title": parsed.get("experience_title", f"{activity_name} Gathering at {locality}"),
                        "tagline": parsed.get("tagline", f"Exciting {activity_name} session with local peers"),
                        "why_this_works": parsed.get("why_this_works", [
                            f"Direct match for {activity_name} enthusiasts in {locality}",
                            f"Fits verified participant availability ({start_time_str} - {end_time_str})",
                            f"Venue reservation confirmed with equal split cost"
                        ]),
                        "agenda": parsed.get("agenda", []),
                        "preparation_checklist": parsed.get("preparation_checklist", []),
                        "ai_generated": True,
                    }
        except Exception:
            pass

    # Deterministic Heuristic Synthesis Fallback
    title = f"{activity_name} Experience ({locality})"
    if "badminton" in activity_name.lower():
        title = f"{activity_name} Doubles Match at {venue_name or locality}"
        tagline = f"Competitive and friendly doubles games with verified peers in {locality}"
        checklist = [
            "Non-marking indoor court shoes",
            "Badminton racquet (or rental at venue)",
            "Sweat towel & hydration bottle",
            "Mavis 350 / feather shuttlecocks"
        ]
        agenda = [
            {"time_window": f"{start_time_str} - 15m", "title": "Arrival & Court Warm-up", "description": "Meet team at court, stretch, and quick rally warm-up"},
            {"time_window": f"+15m - 60m", "title": "Doubles Match Rotation", "description": "Round-robin sets to 21 points with partner rotations"},
            {"time_window": f"+60m - {end_time_str}", "title": "Cool-down & Debrief", "description": "Hydration break, post-game scores, and wrap-up"}
        ]
    elif "football" in activity_name.lower() or "cricket" in activity_name.lower():
        title = f"{activity_name} Turf Showdown at {venue_name or locality}"
        tagline = f"Fast-paced local match with {target_size} players"
        checklist = [
            "Turf boots / sports sneakers",
            "Breathable sportswear",
            "Water bottle & energy snacks"
        ]
        agenda = [
            {"time_window": f"{start_time_str} - 15m", "title": "Squad Meet & Warm-up", "description": "Team division and tactical warm-up"},
            {"time_window": f"+15m - 75m", "title": "Match Play", "description": "Full game with hydration break"},
            {"time_window": f"+75m - {end_time_str}", "title": "Debrief & Post-match Chat", "description": "Review key plays and connect"}
        ]
    else:
        title = f"{activity_name} Session at {venue_name or locality}"
        tagline = f"Engaging community {activity_name} meetup in {locality}"
        checklist = [
            f"Personal gear/tools for {activity_name}",
            "Comfortable attire",
            "Water bottle"
        ]
        agenda = [
            {"time_window": f"{start_time_str} - 15m", "title": "Welcome & Introductions", "description": f"Gather participants and outline {activity_name} goals"},
            {"time_window": f"+15m - 75m", "title": "Core Session", "description": f"Interactive {activity_name} practice and collaboration"},
            {"time_window": f"+75m - {end_time_str}", "title": "Wrap-up & Community Connect", "description": "Feedback, recap, and next steps"}
        ]

    why_this_works = [
        f"Matches your target {activity_name} interest in {locality}",
        f"Fits participant schedules ({start_time_str} - {end_time_str})",
    ]
    if venue_name:
        why_this_works.append(f"Dedicated bookable slot at {venue_name}")
    if per_person_cost is not None and per_person_cost > 0:
        why_this_works.append(f"Fair split cost of INR {per_person_cost:.2f} per participant")
    if candidate_names:
        why_this_works.append(f"Includes verified high-compatibility peers: {', '.join(candidate_names[:2])}")

    return {
        "experience_title": title,
        "tagline": tagline,
        "why_this_works": why_this_works,
        "agenda": agenda,
        "preparation_checklist": checklist,
        "ai_generated": False,
    }


# ============================================================================
# AI COMMUNITY LIFECYCLE INTELLIGENCE
# ============================================================================

SYSTEM_COMMUNITY_LIFECYCLE_PROMPT = """You are the AI Community Lifecycle Intelligence Engine for Localy (Vynk).
Your goal is to interpret verified community health scores, trend trajectories, and metric shifts into strategic lifecycle insights and recommended focus areas.

CRITICAL RULES:
1. You MUST NOT invent, falsify, or modify any verified ground truth numbers:
   - Do NOT alter or recalculate health scores, trend directions, member counts, event counts, or ratings.
2. Lifecycle stage MUST strictly be one of:
   - "NEW"
   - "GROWING"
   - "HEALTHY"
   - "AT_RISK"
   - "INACTIVE"
3. Produce:
   - lifecycle_stage: One of the five valid stages matching the health trajectory.
   - insight: A concise (1-2 sentences) human-readable explanation of the community's engagement health and trend.
   - recommended_focus: An actionable, tactical recommendation for organizers or community members to sustain or improve engagement.

Respond ONLY with valid JSON with keys:
{
  "lifecycle_stage": "NEW" | "GROWING" | "HEALTHY" | "AT_RISK" | "INACTIVE",
  "insight": "...",
  "recommended_focus": "..."
}
Do not include markdown code fences or explanatory text outside the JSON.
"""

def _deterministic_community_lifecycle_fallback(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic baseline synthesis when AI service is unavailable, offline, or returns invalid output.
    """
    health_status = facts.get("health_status", "INACTIVE")
    trend = facts.get("trend", "STABLE")
    events_created = facts.get("events_created", 0)
    member_count = facts.get("member_count", 0)

    # 1. Determine Lifecycle Stage
    if health_status == "INACTIVE":
        if events_created == 0 and member_count <= 2:
            stage = "NEW"
        else:
            stage = "INACTIVE"
    elif health_status == "AT_RISK" or trend == "DECLINING":
        stage = "AT_RISK"
    elif trend == "IMPROVING":
        stage = "GROWING"
    elif health_status == "HEALTHY":
        stage = "HEALTHY"
    elif health_status == "GROWING":
        stage = "GROWING"
    else:
        stage = "NEW"

    # 2. Derive Insight & Recommended Focus based on stage, health status, and trend
    if stage == "GROWING" or (health_status == "HEALTHY" and trend == "IMPROVING"):
        insight = "The community is becoming more active, with participation and event frequency increasing."
        focus = "Continue recurring weekend activities and maintain member engagement."
    elif stage == "HEALTHY" or (health_status == "HEALTHY" and trend == "STABLE"):
        insight = "The community maintains consistent health and reliable engagement across regular events."
        focus = "Sustain core event consistency, gather member feedback on new formats, and celebrate active participants."
    elif stage == "AT_RISK" or trend == "DECLINING":
        insight = "Community activity and participation are declining, showing elevated risk of member disengagement."
        focus = "Poll inactive members for schedule preferences, lower event commitment barriers, and organize a low-friction casual meetup."
    elif stage == "INACTIVE":
        insight = "The community has experienced prolonged dormancy with no recent events or active member attendance."
        focus = "Send a reactivation poll to registered members, suggest a simple reboot meetup, or invite fresh co-organizers."
    else:  # NEW
        insight = "This is a newly formed community cohort establishing its initial foundation."
        focus = "Host an introductory kickoff session to connect founding members and establish recurring availability."

    return {
        "lifecycle_stage": stage,
        "insight": insight,
        "recommended_focus": focus,
        "ai_generated": False,
    }


def generate_community_lifecycle_ai(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interprets verified community health & trend data into structured lifecycle assessment.
    Uses OpenAI GPT when available; otherwise falls back to deterministic synthesis.
    """
    valid_stages = {"NEW", "GROWING", "HEALTHY", "AT_RISK", "INACTIVE"}

    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("mock"):
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            score_change = facts.get("score_change", 0)
            score_change_str = f"+{score_change}" if score_change > 0 else str(score_change)
            user_prompt = f"""Verified Community Facts:
Community Name: {facts.get('community_name', 'Community')}
Health Score: {facts.get('health_score')}
Health Status: {facts.get('health_status')}
Score Trend: {facts.get('trend')} (Score change: {score_change_str} pts)
Member Count: {facts.get('member_count')} (Active: {facts.get('active_member_count')})
Events Created: {facts.get('events_created')} (Completed: {facts.get('completed_events')})
Average Participation: {facts.get('average_event_participation')}%
Average Feedback Rating: {facts.get('average_feedback_rating')}/5.0
"""
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_COMMUNITY_LIFECYCLE_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    stage = str(parsed.get("lifecycle_stage", "")).strip().upper()
                    insight = str(parsed.get("insight", "")).strip()
                    focus = str(parsed.get("recommended_focus", "")).strip()

                    if stage in valid_stages and insight and focus:
                        return {
                            "lifecycle_stage": stage,
                            "insight": insight,
                            "recommended_focus": focus,
                            "ai_generated": True,
                        }
        except Exception:
            pass

    return _deterministic_community_lifecycle_fallback(facts)


# ============================================================================
# AI COMMUNITY ACTION RECOMMENDATIONS
# ============================================================================

VALID_COMMUNITY_ACTIONS = {
    "CREATE_EVENT",
    "RE_ENGAGE_MEMBERS",
    "COLLECT_FEEDBACK",
    "GROW_MEMBERSHIP",
    "MAINTAIN_ACTIVITY",
    "REACTIVATE_COMMUNITY",
}

VALID_ACTION_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}

SYSTEM_COMMUNITY_ACTION_RECOMMENDATION_PROMPT = """You are the AI Community Action Recommendation Engine for Localy (Vynk).
Your goal is to suggest 1 to 3 tactical action recommendations for community organizers based on verified health, trend, and lifecycle analysis.

CRITICAL RULES:
1. You MUST NOT invent, falsify, or modify numerical facts (member counts, event counts, health scores, ratings).
2. The "action" field MUST strictly be one of:
   - "CREATE_EVENT"
   - "RE_ENGAGE_MEMBERS"
   - "COLLECT_FEEDBACK"
   - "GROW_MEMBERSHIP"
   - "MAINTAIN_ACTIVITY"
   - "REACTIVATE_COMMUNITY"
3. The "priority" field MUST strictly be one of:
   - "HIGH"
   - "MEDIUM"
   - "LOW"
4. Ground all recommendations in the community's current lifecycle stage and trajectory:
   - GROWING / IMPROVING -> CREATE_EVENT, GROW_MEMBERSHIP
   - HEALTHY / STABLE -> MAINTAIN_ACTIVITY, GROW_MEMBERSHIP
   - AT_RISK / DECLINING -> RE_ENGAGE_MEMBERS, CREATE_EVENT
   - INACTIVE -> REACTIVATE_COMMUNITY, RE_ENGAGE_MEMBERS
5. Produce JSON with the exact key "recommendations", which is an array of objects:
{
  "recommendations": [
    {
      "priority": "HIGH" | "MEDIUM" | "LOW",
      "action": "CREATE_EVENT" | "RE_ENGAGE_MEMBERS" | "COLLECT_FEEDBACK" | "GROW_MEMBERSHIP" | "MAINTAIN_ACTIVITY" | "REACTIVATE_COMMUNITY",
      "title": "Short title",
      "reason": "Grounded reason",
      "suggested_next_step": "Tactical next step"
    }
  ]
}

Respond ONLY with valid JSON. Do not include markdown code fences or conversational text.
"""

def _deterministic_community_action_fallback(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Deterministic baseline recommendations when AI is offline, fails, or produces invalid output.
    """
    health_status = facts.get("health_status", "INACTIVE")
    trend = facts.get("trend", "STABLE")
    lifecycle_stage = facts.get("lifecycle_stage", "INACTIVE")
    completed_events = facts.get("completed_events", 0)
    avg_feedback = facts.get("average_feedback_rating", 0.0)

    recs: List[Dict[str, Any]] = []

    # 1. Primary Recommendation based on Lifecycle State & Trend
    if lifecycle_stage in ["GROWING", "NEW"] or (health_status == "HEALTHY" and trend == "IMPROVING"):
        recs.append({
            "priority": "HIGH",
            "action": "CREATE_EVENT",
            "title": "Schedule recurring activities",
            "reason": "Participation and event momentum are expanding.",
            "suggested_next_step": "Publish recurring weekly session times to establish regular routine.",
        })
        recs.append({
            "priority": "MEDIUM",
            "action": "GROW_MEMBERSHIP",
            "title": "Expand cohort membership",
            "reason": "Healthy cohort activity attracts compatible local peers.",
            "suggested_next_step": "Share community link with nearby peers sharing matching interests.",
        })
    elif health_status == "HEALTHY" and trend == "STABLE":
        recs.append({
            "priority": "HIGH",
            "action": "MAINTAIN_ACTIVITY",
            "title": "Maintain event consistency",
            "reason": "Community shows consistent health and steady participation.",
            "suggested_next_step": "Keep core recurring event slots active and celebrate active contributors.",
        })
        recs.append({
            "priority": "MEDIUM",
            "action": "GROW_MEMBERSHIP",
            "title": "Encourage new member introductions",
            "reason": "Established community has capacity to welcome new local members.",
            "suggested_next_step": "Host an open mixer or casual beginner session.",
        })
    elif health_status == "AT_RISK" or trend == "DECLINING" or lifecycle_stage == "AT_RISK":
        recs.append({
            "priority": "HIGH",
            "action": "RE_ENGAGE_MEMBERS",
            "title": "Re-engage inactive members",
            "reason": "Recent participation has declined.",
            "suggested_next_step": "Organize a low-commitment weekend activity.",
        })
        recs.append({
            "priority": "MEDIUM",
            "action": "CREATE_EVENT",
            "title": "Host low-barrier session",
            "reason": "Smaller gatherings reduce commitment hurdles for disengaged members.",
            "suggested_next_step": "Create a casual meetup with flexible timings.",
        })
    else:  # INACTIVE
        recs.append({
            "priority": "HIGH",
            "action": "REACTIVATE_COMMUNITY",
            "title": "Run a reactivation activity",
            "reason": "Community has had no recent event activity or attendance.",
            "suggested_next_step": "Send a reboot poll to registered members asking for preferred dates.",
        })
        recs.append({
            "priority": "MEDIUM",
            "action": "RE_ENGAGE_MEMBERS",
            "title": "Reach out to founding members",
            "reason": "Early members can help kickstart renewed interest.",
            "suggested_next_step": "Message core founding members to co-host an introductory meetup.",
        })

    # 2. Contextual Secondary Recommendation: Feedback Gap
    if completed_events > 0 and avg_feedback < 4.0 and len(recs) < 3:
        recs.append({
            "priority": "LOW",
            "action": "COLLECT_FEEDBACK",
            "title": "Collect post-event feedback",
            "reason": "Feedback volume is low across completed events.",
            "suggested_next_step": "Prompt attendees to submit quick ratings after upcoming sessions.",
        })

    return recs


def generate_community_action_recommendations_ai(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Synthesizes tactical action recommendations using OpenAI GPT when available,
    strictly validated against controlled action enums. Falls back to deterministic heuristics.
    """
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("mock"):
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            user_prompt = f"""Verified Community Context:
Community Name: {facts.get('community_name', 'Community')}
Lifecycle Stage: {facts.get('lifecycle_stage')}
Health Status: {facts.get('health_status')} (Score: {facts.get('health_score')})
Score Trend: {facts.get('trend')} (Change: {facts.get('score_change', 0):+d} pts)
Member Count: {facts.get('member_count')} (Active: {facts.get('active_member_count')})
Events Created: {facts.get('events_created')} (Completed: {facts.get('completed_events')})
Average Participation: {facts.get('average_event_participation')}%
Average Feedback Rating: {facts.get('average_feedback_rating')}/5.0
Insight Summary: {facts.get('insight', '')}
Recommended Focus: {facts.get('recommended_focus', '')}
"""
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_COMMUNITY_ACTION_RECOMMENDATION_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    raw_recs = parsed.get("recommendations", [])

                    valid_recs = []
                    for item in raw_recs:
                        if not isinstance(item, dict):
                            continue
                        act = str(item.get("action", "")).strip().upper()
                        prio = str(item.get("priority", "")).strip().upper()
                        title = str(item.get("title", "")).strip()
                        reason = str(item.get("reason", "")).strip()
                        next_step = str(item.get("suggested_next_step", "")).strip()

                        if act in VALID_COMMUNITY_ACTIONS and prio in VALID_ACTION_PRIORITIES and title and reason and next_step:
                            valid_recs.append({
                                "priority": prio,
                                "action": act,
                                "title": title,
                                "reason": reason,
                                "suggested_next_step": next_step,
                            })

                    if valid_recs:
                        return valid_recs
        except Exception:
            pass

    return _deterministic_community_action_fallback(facts)



