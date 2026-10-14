# Localy (Vynk) — Setup & API Architecture Guide

A clean, reproducible guide to run the FastAPI backend, PostgreSQL database, Next.js frontend, and the Deterministic Matchmaking Engine.

---

## 🏛️ 1. 22-Table Database Architecture

| No. | Table | Purpose | Key Relationships |
| :--- | :--- | :--- | :--- |
| 1 | `users` | Single auth source of truth | Email, password hash, account status |
| 2 | `profiles` | User-facing public identity & AI vector | 1:1 `users.user_id`, locality, bio, 1536-dim embedding |
| 3 | `interests` | Master taxonomy catalog | Sports, Music, Tech, Creative, Learning |
| 4 | `user_interests` | User selected interests | N:M `(user_id, interest_id)` composite PK |
| 5 | `skills` | Master skills catalog | Standardized skill taxonomy |
| 6 | `user_skills` | User skills + proficiency | N:M `(user_id, skill_id)` composite PK + level |
| 7 | `user_availability` | Weekly schedule windows | 1:N `users.user_id`, day of week, times |
| 8 | `activities` | Activity concept/template | FK `interest_id`, FK `created_by`, 1536-dim embedding |
| 9 | `venues` | Physical spaces & courts | Nullable `owner_user_id` FK to `users` |
| 10 | `venue_activities` | Supported venue activities | N:M `(venue_id, activity_id)` composite PK |
| 11 | `venue_slots` | Bookable time windows | `UNIQUE(venue_id, slot_date, start_time, end_time)`, total price |
| 12 | `events` | Scheduled gatherings | FK `activity_id`, FK `host_id`, capacity, date |
| 13 | `venue_bookings` | Event ↔ VenueSlot Bridge | `UNIQUE(event_id)`, `UNIQUE(slot_id)`, total amount, status |
| 14 | `event_participants` | Event attendance roster | N:M `(event_id, user_id)` composite PK |
| 15 | `payment_accounts` | Venue/Host payout accounts | 1:1 `users.user_id`, provider ID |
| 16 | `payments` | Participant split share payments | FK `booking_id`, FK `user_id`, amount, status |
| 17 | `payouts` | Venue owner settlement transfers | 1:1 `venue_bookings.booking_id`, FK `payment_account_id` |
| 18 | `communities` | Permanent recurring circles | Name UNIQUE, description, FK `created_by` |
| 19 | `community_members` | Community circle roster | N:M `(community_id, user_id)` composite PK |
| 20 | `feedback` | Post-event peer reviews & trust | `UNIQUE(event_id, reviewer_id)`, rating (1-5) |
| 21 | `group_proposals` | Temporary AI-suggested cohorts | FK `initiator_user_id`, target/min size, date, times, status |
| 22 | `group_proposal_members` | Proposal invitations & responses | N:M `(proposal_id, user_id)` composite PK, status, score |


---

## 🚀 2. Running Locally

### Backend Setup (FastAPI + PostgreSQL)

Follow these simple steps to set up the backend and database:

#### Step 1: Install Python Dependencies
```bash
cd backend
python -m pip install -r requirements.txt
```

#### Step 2: Configure Environment Variables
Copy the template file to create your `.env`:
- **Windows (CMD / PowerShell):** `copy .env.example .env`
- **Mac / Linux:** `cp .env.example .env`

Open `backend/.env` and update your PostgreSQL connection URL with your password and port:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/major
```
*(Make sure an empty database named `major` exists in your PostgreSQL).*

#### Step 3: Auto-Build Database Tables & Relations (One-Time Setup)
Run the automated setup script. This automatically enables the `pgvector` extension, creates all **23 tables & foreign key relations**, and seeds all master interests and skills:
```bash
python init_db.py
```
> **Tip for Windows:** If you haven't installed pgvector yet, right-click `install_pgvector.bat` and select **Run as Administrator** once.

#### Step 4: Start the Backend Server
```bash
python main.py
```
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger UI (API Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Interactive ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
- **App:** [http://localhost:3000](http://localhost:3000)

---

## 🎯 3. Hybrid Semantic & Deterministic Matching Engine

### Scoring Formula (Deterministic 70% + Semantic 30%)
```text
Hybrid Match Score = round(Deterministic Score * 0.70 + (Semantic Cosine Similarity * 100) * 0.30)
```

| Component | Weight | Max Pts | Criteria |
| :--- | :---: | :---: | :--- |
| **Deterministic Anchor** | **70%** | **70 pts** | Rule-based compatibility across Interest (+40), Availability (+30), Location (+20), and Skill (+10) |
| **Semantic AI Embedding** | **30%** | **30 pts** | Cosine similarity between query/activity embedding and candidate 1536-dim profile vector (`profiles.embedding`) |

#### Deterministic Breakdown (Max 100 Raw Points)
| Category | Max Raw Pts | Criteria |
| :--- | :---: | :--- |
| **Interest Overlap** | **+40** | Shares the requested activity / target interest (or +20 per shared general interest) |
| **Availability Overlap** | **+30** | Free on requested day or matching recurring weekly schedule windows |
| **Location Proximity** | **+20** | Same locality (+20 pts) or neighboring area token match (+10 pts) |
| **Skill Relevance** | **+10** | Offers skill in same activity category (+10 pts) or active peer skill (+5 pts) |

### API Endpoints
- `GET /matches` or `GET /matches/people`
  - **Query Params:**
    - `activity_id` (optional `int`): Target activity to find people for
    - `interest_id` (optional `int`): Target interest catalog ID
    - `locality` (optional `str`): Location area filter/boost
    - `day_of_week` (optional `str`): E.g. `'Saturday'`, `'Sunday'`
    - `min_score` (optional `int`, default `10`): Minimum compatibility score threshold
    - `limit` (optional `int`, default `20`): Max candidates returned

### Example Matching Response
```json
{
  "total_candidates": 1,
  "activity_id": 1,
  "activity_title": "Badminton Doubles",
  "target_interest": "Badminton",
  "matches": [
    {
      "user_id": 3,
      "display_name": "Amit Kumar",
      "avatar_url": null,
      "approx_locality": "Indiranagar, Bengaluru",
      "match_score": 88,
      "deterministic_score": 100,
      "semantic_similarity": 0.6014,
      "trust_score": 94,
      "reputation": {
        "average_rating": 4.7,
        "total_reviews": 12,
        "completed_events": 15
      },
      "match_breakdown": {
        "interest": 40,
        "availability": 30,
        "location": 20,
        "skill": 10,
        "semantic": 18.0,
        "deterministic_total": 100,
        "total": 88
      },
      "match_reasons": [
        "Shares target interest 'Badminton' (+40 pts)",
        "Available on requested day: Saturday (+30 pts)",
        "Same locality match: Indiranagar, Bengaluru (+20 pts)",
        "Offers relevant skill matching activity category (+10 pts)",
        "AI semantic profile affinity: 60% (+18.0 pts)",
        "Highly-rated peer (4.7★ from 12 reviews)"
      ],
      "shared_interests": ["Badminton"],
      "relevant_skills": ["Badminton Coaching (Advanced)"],
      "shared_availability": ["Saturday (18:00-20:00)"]
    }
  ]
}
```


---

## 🔐 4. Complete REST API Reference

### 🔐 Authentication & Accounts
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/auth/register` | Register new user account | No |
| `POST` | `/auth/login` | Login (JSON or Form) & receive JWT token | No |
| `GET` | `/auth/me` | Fetch authenticated account details | **Yes** |

### 🎨 Master Catalogs & Profiles
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `GET` | `/interests` | List all standardized interests | No |
| `GET` | `/skills` | List all standardized skills | No |
| `GET` | `/profile/me` | Fetch full profile, skills, availability | **Yes** |
| `PATCH` | `/profile/me` | Update bio, display name, locality, budget | **Yes** |
| `PUT` | `/profile/me/interests` | Replace selected interests list | **Yes** |
| `PUT` | `/profile/me/skills` | Replace user skills with proficiency levels | **Yes** |
| `PUT` | `/profile/me/availability` | Replace weekly schedule windows | **Yes** |
| `POST` | `/profile/me/onboarding` | Complete atomic user onboarding | **Yes** |
| `GET` | `/profile/{user_id}` | Public privacy-shielded profile | No |

### 🎯 Matchmaking Engine
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `GET` | `/matches` | Discover compatible people with score & reasons | **Yes** |
| `GET` | `/matches/people` | Alias for people matching | **Yes** |

### 🎪 Activities Engine
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/activities` | Create activity template (FK `interest_id`) | **Yes** |
| `GET` | `/activities` | List activities (filters: `interest_id`, `category`, `search`) | No |
| `GET` | `/activities/{id}` | Get activity details | No |
| `PATCH` | `/activities/{id}` | Update activity template (Creator only) | **Yes** |
| `DELETE` | `/activities/{id}` | Delete activity template (Creator only) | **Yes** |

### 🏟️ Venues & Bookable Slots
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/venues` | Register new venue (Admin or Venue Owner) | **Yes** |
| `GET` | `/venues` | List venues (filters: `locality`, `activity_id`, `search`) | No |
| `GET` | `/venues/{id}` | Get single venue details & supported activities | No |
| `PATCH` | `/venues/{id}` | Update venue details (Owner only) | **Yes** |
| `POST` | `/venues/{id}/slots` | Create bookable time slot with total price | **Yes** |
| `GET` | `/venues/{id}/slots` | List available slots by date | No |

### 📅 Events, Roster & Participation Lifecycle
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/events` | Create scheduled event with optional venue slot reservation | **Yes** |
| `GET` | `/events` | Discover events (filters: `locality`, `activity_id`, `date`, `available_only`, `status`) | No |
| `GET` | `/events/{id}` | Full event details, remaining spots, dynamic split cost & roster | No |
| `PATCH` | `/events/{id}` | Update event details or lifecycle status (Host only) | **Yes** |
| `POST` | `/events/{id}/join` | Join event roster (concurrency-safe capacity enforcement) | **Yes** |
| `DELETE` | `/events/{id}/join` | Leave event roster (restores capacity spot & recalculates split cost) | **Yes** |
| `POST` | `/events/{id}/leave` | Alias to leave event roster | **Yes** |

### 💳 Split Payments & Payouts (Option A Rule)
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/events/{id}/pay` | Pay participant split share (`Venue Price ÷ Confirmed Count`) | **Yes** |
| `POST` | `/payment-accounts` | Register venue owner payout account | **Yes** |
| `GET` | `/payment-accounts/me` | Fetch registered payout account | **Yes** |
| `POST` | `/bookings/{id}/payout` | Trigger settlement transfer to venue owner | **Yes** |

### 👥 Communities & Feedback
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/communities` | Create permanent community circle | **Yes** |
| `GET` | `/communities` | List all community circles | No |
| `POST` | `/communities/{id}/join` | Join a community circle | **Yes** |
| `GET` | `/communities/{id}/health` | Retrieve member-only deterministic community health metrics and score | **Yes** |
| `POST` | `/events/{id}/feedback` | Submit post-event peer rating (1-5) & review | **Yes** |
| `GET` | `/events/{id}/feedback` | Get all peer reviews for an event | No |

### 🧠 AI Intent, Group Formation & Recommendation Engine
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/ai/intent` | Understand and extract structured parameters from natural language input | No |
| `POST` | `/ai/intent/search` | Natural Language → AI Intent → People Matching, Events & Venues Discovery | Optional |
| `POST` | `/ai/groups/propose` | Formulate and create AI-suggested temporary Group Proposal with invited candidates | **Yes** |
| `POST` | `/groups/proposals/{id}/respond` | Accept or Decline an invitation (`status: 'ACCEPTED' \| 'DECLINED'`) | **Yes** |
| `POST` | `/groups/proposals/{id}/convert` | Convert a CONFIRMED group proposal into an official scheduled Event | **Yes** |
| `GET` | `/groups/proposals/me` | List all active group proposals where user is initiator or invited member | **Yes** |
| `GET` | `/groups/proposals/{id}` | Get detailed group proposal status and member responses roster | **Yes** |
| `GET` | `/recommendations` | Ranked AI Recommendations (Events, Activities, People) based on interests, availability & locality | **Yes** |
| `GET` | `/do-something-now` | Real-time immediate viable experiences (Join active events vs Create group/activity) | **Yes** |
| `POST` | `/ai/experiences/generate` | Synthesize verified backend facts into actionable experience plan & agenda | **Yes** |
| `GET` | `/ai/demand-radar` | Detect collective activity demand, underserved capacity & opportunity scores | **Yes** |
| `POST` | `/ai/demand-prediction` | Predict attendance, fill rate, capacity & feasibility for proposed activities | **Yes** |
| `GET` | `/ai/opportunities` | Cross-domain actionable opportunity intelligence combining demand, prediction, venues & matching | **Yes** |
| `GET` | `/ai/community-intelligence` | Detect recurring cohorts, shared schedule patterns & propose community circles | **Yes** |






#### 1. Example AI Intent Parsing (`POST /ai/intent`)
```bash
curl -X POST "http://127.0.0.1:8000/ai/intent" \
  -H "Content-Type: application/json" \
  -d '{"query": "I want to play badminton this Saturday evening with people near me."}'
```

#### 2. Example End-to-End AI Intent Search (`POST /ai/intent/search`)
```bash
curl -X POST "http://127.0.0.1:8000/ai/intent/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{"query": "I want to play badminton this Saturday evening with people near me.", "limit": 5}'
```

#### Example AI Intent Search Response
```json
{
  "query": "I want to play badminton this Saturday evening with people near me.",
  "intent_understood": {
    "raw_query": "I want to play badminton this Saturday evening with people near me.",
    "intent": "find_activity_and_people",
    "activity": "Badminton",
    "category": "Sports",
    "day_of_week": "Saturday",
    "time_of_day": "evening",
    "location": "nearby",
    "skill_level": null,
    "budget_preference": "flexible",
    "group_size": null,
    "confidence": 0.88,
    "engine": "semantic-rules-engine"
  },
  "summary": "Intent understood: Badminton • Saturday evening • Indiranagar, Bengaluru. Found 4 matching peers, 1 events, and 1 venues.",
  "people_matches": [
    {
      "user_id": 28,
      "display_name": "Amit Kumar",
      "avatar_url": null,
      "approx_locality": "Indiranagar, Bengaluru",
      "match_score": 100,
      "match_breakdown": {
        "interest": 40,
        "availability": 30,
        "location": 20,
        "skill": 10,
        "total": 100
      },
      "match_reasons": [
        "Shares target interest 'Badminton' (+40 pts)",
        "Available on requested day: Saturday (+30 pts)",
        "Same locality match: Indiranagar, Bengaluru (+20 pts)",
        "Offers relevant skill matching activity category (+10 pts)"
      ],
      "shared_interests": ["Badminton"],
      "relevant_skills": ["Badminton Coaching (Advanced)"],
      "shared_availability": ["Saturday (18:00-20:00)"]
    }
  ],
  "events": [
    {
      "event_id": 4,
      "activity_id": 2,
      "activity_title": "Badminton Doubles Match",
      "host_name": "Karan Varma",
      "title": "Saturday Evening Badminton Doubles Indiranagar",
      "event_date": "2026-10-11",
      "start_time": "18:00:00",
      "end_time": "20:00:00",
      "max_capacity": 4,
      "participant_count": 1,
      "remaining_spots": 3,
      "status": "PUBLISHED"
    }
  ],
  "venues": [
    {
      "venue_id": 3,
      "name": "Indiranagar Badminton Arena",
      "locality": "Indiranagar",
      "address": "100 Feet Road, Indiranagar",
    }
  ]
}
```

#### 3. Example AI Group Proposal (`POST /ai/groups/propose`)
```bash
curl -X POST "http://127.0.0.1:8000/ai/groups/propose" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{"query": "I want to play badminton with 4 people this Saturday evening near me."}'
```

#### Example AI Group Proposal Response
```json
{
  "proposal_id": 5,
  "initiator_user_id": 1,
  "initiator_name": "Pooja Hegde",
  "activity_id": 2,
  "activity_title": "Badminton Doubles Match",
  "title": "Saturday Evening Badminton Doubles Match (4 Players)",
  "description": "AI-suggested cohort for 'I want to play badminton with 4 people this Saturday evening near me.' in Indiranagar, Bengaluru.",
  "target_size": 4,
  "min_required_size": 3,
  "proposed_date": "2026-10-17",
  "proposed_start_time": "18:00:00",
  "proposed_end_time": "20:00:00",
  "target_locality": "Indiranagar, Bengaluru",
  "suggested_venue_id": 3,
  "suggested_venue_name": "Smash & Groove Arena",
  "status": "PROPOSED",
  "converted_event_id": null,
  "expires_at": "2026-10-11T18:00:00Z",
  "created_at": "2026-10-10T11:20:00Z",
  "members": [
    {
      "user_id": 1,
      "display_name": "Pooja Hegde",
      "avatar_url": null,
      "approx_locality": "Indiranagar, Bengaluru",
      "status": "ACCEPTED",
      "compatibility_score": 100,
      "invited_at": "2026-10-10T11:20:00Z",
      "responded_at": "2026-10-10T11:20:00Z"
    },
    {
      "user_id": 3,
      "display_name": "Rahul Sharma",
      "avatar_url": null,
      "approx_locality": "Indiranagar, Bengaluru",
      "status": "INVITED",
      "compatibility_score": 74,
      "invited_at": "2026-10-10T11:20:00Z",
      "responded_at": null
    },
    {
      "user_id": 4,
      "display_name": "Amit Kumar",
      "avatar_url": null,
      "approx_locality": "Indiranagar, Bengaluru",
      "status": "INVITED",
      "compatibility_score": 73,
      "invited_at": "2026-10-10T11:20:00Z",
      "responded_at": null
    },
    {
      "user_id": 5,
      "display_name": "Karthik Racket Coach",
      "avatar_url": null,
      "approx_locality": "Indiranagar, Bengaluru",
      "status": "INVITED",
      "compatibility_score": 73,
      "invited_at": "2026-10-10T11:20:00Z",
      "responded_at": null
    }
  ]
}
```

#### 4. Event Venue Booking Bridge (`POST /events/{event_id}/venue-book`)
Reserve and attach an available, compatible venue slot directly to a scheduled event:

```bash
curl -X POST "http://127.0.0.1:8000/events/10/venue-book" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <HOST_ACCESS_TOKEN>" \
  -d '{"slot_id": 14}'
```

#### Example Response
```json
{
  "event_id": 10,
  "activity_id": 2,
  "activity_title": "Badminton Doubles Arena",
  "interest_name": "Badminton",
  "interest_category": "Sports",
  "host_id": 1,
  "host_name": "Pooja Hegde",
  "title": "Saturday Evening Badminton Doubles Championship",
  "event_date": "2026-10-17",
  "start_time": "18:00:00",
  "end_time": "20:00:00",
  "max_capacity": 4,
  "participant_count": 3,
  "remaining_spots": 1,
  "per_person_cost": 400.0,
  "cost_per_person": 400.0,
  "locality": "Indiranagar, Bengaluru",
  "status": "PUBLISHED",
  "venue_booking": {
    "booking_id": 7,
    "event_id": 10,
    "slot_id": 14,
    "venue_id": 3,
    "venue_name": "Smash & Groove Arena",
    "venue_address": "100 Feet Road, Indiranagar",
    "slot_date": "2026-10-17",
    "start_time": "18:00:00",
    "end_time": "20:00:00",
    "booked_by": 1,
    "total_amount": 1200.0,
    "currency": "INR",
    "status": "CONFIRMED",
    "amount_collected": 0.0,
    "per_person_share": 400.0,
    "created_at": "2026-10-10T11:35:00Z"
  },
  "participants": [
    {
      "user_id": 1,
      "display_name": "Pooja Hegde",
      "avatar_url": null,
      "status": "CONFIRMED",
      "payment_status": "UNPAID",
      "paid_amount": 0.0,
      "joined_at": "2026-10-10T11:30:00Z"
    },
    {
      "user_id": 3,
      "display_name": "Rahul Sharma",
      "avatar_url": null,
      "status": "CONFIRMED",
      "payment_status": "UNPAID",
      "paid_amount": 0.0,
      "joined_at": "2026-10-10T11:30:00Z"
    },
    {
      "user_id": 4,
      "display_name": "Amit Kumar",
      "avatar_url": null,
      "status": "CONFIRMED",
      "payment_status": "UNPAID",
      "paid_amount": 0.0,
      "joined_at": "2026-10-10T11:30:00Z"
    }
  ],
  "created_at": "2026-10-10T11:30:00Z"
}
```

#### 5. Participant Split Payment Collection (`POST /events/{event_id}/pay`)
Pay participant's exact split share toward the venue booking:

```bash
curl -X POST "http://127.0.0.1:8000/events/10/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <PARTICIPANT_ACCESS_TOKEN>" \
  -d '{"amount": 400.0}'
```

#### Example Response
```json
{
  "payment_id": 1,
  "booking_id": 7,
  "user_id": 3,
  "user_name": "Rahul Sharma",
  "amount": 400.0,
  "currency": "INR",
  "status": "SUCCESS",
  "provider_payment_id": "PAY_SIM_7_3_1760077800000",
  "created_at": "2026-10-10T11:38:00Z"
}
```

#### 6. Venue Settlement & Payout (`POST /events/{event_id}/payout`)
Trigger direct settlement transfer to the venue owner once booking is fully collected:

```bash
curl -X POST "http://127.0.0.1:8000/events/10/payout" \
  -H "Authorization: Bearer <HOST_OR_VENUE_OWNER_ACCESS_TOKEN>"
```

#### Example Response
```json
{
  "payout_id": 1,
  "booking_id": 7,
  "payment_account_id": 2,
  "amount": 1200.0,
  "currency": "INR",
  "status": "COMPLETED",
  "provider_transfer_id": "TRF_SIM_7_2_1760078000000",
  "created_at": "2026-10-10T11:41:00Z"
}
```

#### 7. Post-Event Feedback & Rating (`POST /events/{event_id}/feedback`)
Submit rating and review once the event is marked `COMPLETED`:

```bash
curl -X POST "http://127.0.0.1:8000/events/10/feedback" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <PARTICIPANT_ACCESS_TOKEN>" \
  -d '{"rating": 5, "comment": "Amazing game! Great court and competitive doubles."}'
```

#### Example Response
```json
{
  "feedback_id": 1,
  "event_id": 10,
  "reviewer_id": 3,
  "reviewer_name": "Rahul Sharma",
  "rating": 5,
  "comment": "Amazing game! Great court and competitive doubles.",
  "created_at": "2026-10-10T11:45:00Z"
}
```

#### 8. User Reputation & Trust Summary (`GET /users/{user_id}/reputation`)
Retrieve calculated peer ratings, star distribution, and completed events:

```bash
curl -X GET "http://127.0.0.1:8000/users/3/reputation"
```

#### Example Response
```json
{
  "user_id": 3,
  "display_name": "Rahul Sharma",
  "average_rating": 4.75,
  "total_reviews": 12,
  "feedback_count": 12,
  "five_star_count": 9,
  "four_star_count": 3,
  "three_star_count": 0,
  "two_star_count": 0,
  "one_star_count": 0,
  "completed_events": 15
}
```

#### 9. AI Recommendation Engine (`GET /recommendations`)
Retrieve ranked personalized recommendations (`EVENT`, `ACTIVITY`, `PEOPLE`):

```bash
curl -X GET "http://127.0.0.1:8000/recommendations?type=EVENT&limit=10" \
  -H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

#### Example Response
```json
{
  "total_recommendations": 1,
  "user_locality": "Indiranagar, Bengaluru",
  "recommendations": [
    {
      "type": "EVENT",
      "id": 13,
      "event_id": 13,
      "activity_id": 2,
      "title": "Saturday Badminton Doubles at Indiranagar",
      "score": 92,
      "reasons": [
        "Matches your Badminton interest (+40 pts)",
        "Fits your Saturday availability (+30 pts)",
        "Near your preferred locality: Indiranagar, Bengaluru (+20 pts)",
        "AI semantic interest affinity (68%)",
        "Organized by top-rated host (5.0★)"
      ],
      "locality": "Indiranagar, Bengaluru",
      "event_date": "2026-10-17",
      "start_time": "18:00:00",
      "end_time": "20:00:00",
      "remaining_spots": 3,
      "per_person_cost": 400.0,
      "trust_score": 100,
      "reputation": {
        "average_rating": 5.0,
        "total_reviews": 4,
        "completed_events": 3
      }
    }
  ]
}
```

#### 10. “Do Something Now” Real-Time Feasibility Engine (`GET /do-something-now`)
Evaluate what can realistically happen *right now* (Join live active events vs Create group/activity with available peers & venue slots):

```bash
curl -X GET "http://127.0.0.1:8000/do-something-now?target_time=18:00:00" \
  -H "Authorization: Bearer <USER_ACCESS_TOKEN>"
```

#### Example Response
```json
{
  "target_date": "2026-10-10",
  "target_time": "18:00:00",
  "day_of_week": "Saturday",
  "user_locality": "Indiranagar, Bengaluru",
  "user_available_now": true,
  "total_options": 2,
  "options": [
    {
      "type": "EVENT",
      "action": "JOIN",
      "title": "Saturday Badminton Doubles Live Match",
      "score": 95,
      "feasible": true,
      "reason": "Matches your Badminton interest and is starting today with 2 open spot(s)",
      "reasons": [
        "Direct match for Badminton",
        "Happening today (18:00 - 20:00)",
        "Nearby at Indiranagar, Bengaluru"
      ],
      "event_id": 13,
      "activity_id": 2,
      "interest_id": 1,
      "interest_name": "Badminton",
      "locality": "Indiranagar, Bengaluru",
      "event_date": "2026-10-10",
      "start_time": "18:00:00",
      "end_time": "20:00:00",
      "remaining_spots": 2,
      "cost_per_person": 300.0,
      "available_peers_count": 2,
      "available_venues_count": 1
    },
    {
      "type": "ACTIVITY",
      "action": "CREATE",
      "title": "5v5 Turf Football",
      "score": 85,
      "feasible": true,
      "reason": "No active event today, but 4 compatible player(s) and 2 venue slot(s) are available now",
      "reasons": [
        "Matches your Football interest",
        "4 compatible player(s) available today",
        "2 bookable venue slot(s) available today"
      ],
      "activity_id": 5,
      "interest_id": 4,
      "interest_name": "Football",
      "locality": "Indiranagar, Bengaluru",
      "event_date": "2026-10-10",
      "start_time": "18:00:00",
      "end_time": "20:00:00",
      "available_peers_count": 4,
      "available_venues_count": 2,
      "suggested_slot_id": 15,
      "suggested_venue_name": "Indiranagar Turf Arena"
    }
  ]
}
```

#### 11. AI Experience Generator (`POST /ai/experiences/generate`)
Transform user natural language intent + strictly verified backend facts into a rich, structured experience plan:

```bash
curl -X POST "http://127.0.0.1:8000/ai/experiences/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
  -d '{"query": "Play badminton with 4 people Saturday evening in Indiranagar"}'
```

#### Example Response
```json
{
  "experience_title": "Saturday Badminton Doubles Championship at Indiranagar Smash Arena",
  "tagline": "Competitive and friendly doubles games with verified peers in Indiranagar",
  "activity_id": 2,
  "activity_name": "Badminton Doubles League",
  "target_date": "2026-10-17",
  "start_time": "18:00:00",
  "end_time": "20:00:00",
  "locality": "Indiranagar, Bengaluru",
  "venue_id": 3,
  "venue_name": "Indiranagar Smash Arena",
  "venue_address": "12th Main Road, Indiranagar",
  "slot_id": 7,
  "target_size": 4,
  "per_person_cost": 300.0,
  "total_cost": 1200.0,
  "currency": "INR",
  "why_this_works": [
    "Matches your target Badminton interest in Indiranagar",
    "Fits participant schedules (18:00 - 20:00)",
    "Dedicated bookable slot at Indiranagar Smash Arena",
    "Fair split cost of INR 300.00 per participant",
    "Includes verified high-compatibility peers: Rahul Sharma, Amit Kumar"
  ],
  "agenda": [
    {
      "time_window": "18:00 - 15m",
      "title": "Arrival & Court Warm-up",
      "description": "Meet team at court, stretch, and quick rally warm-up"
    },
    {
      "time_window": "+15m - 60m",
      "title": "Doubles Match Rotation",
      "description": "Round-robin sets to 21 points with partner rotations"
    },
    {
      "time_window": "+60m - 20:00",
      "title": "Cool-down & Debrief",
      "description": "Hydration break, post-game scores, and wrap-up"
    }
  ],
  "preparation_checklist": [
    "Non-marking indoor court shoes",
    "Badminton racquet (or rental at venue)",
    "Sweat towel & hydration bottle",
    "Mavis 350 / feather shuttlecocks"
  ],
  "suggested_cohort_user_ids": [3, 4, 7],
  "suggested_cohort_names": ["Rahul Sharma", "Amit Kumar", "Pooja Hegde"],
  "action_type": "CREATE_PROPOSAL",
  "action_payload": {
    "query": "Play badminton with 4 people Saturday evening in Indiranagar",
    "activity_id": 2,
    "target_size": 4,
    "proposed_date": "2026-10-17",
    "proposed_start_time": "18:00:00",
    "proposed_end_time": "20:00:00",
    "target_locality": "Indiranagar, Bengaluru",
    "suggested_venue_id": 3,
    "custom_title": "Saturday Badminton Doubles Championship at Indiranagar Smash Arena"
  },
  "ai_generated": true
}
```

#### 9. Example AI Demand Radar (`GET /ai/demand-radar`)
```bash
curl -X GET "http://127.0.0.1:8000/ai/demand-radar?locality=Indiranagar&activity=Badminton&day_of_week=Saturday" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

#### Example AI Demand Radar Response
```json
{
  "total_clusters": 1,
  "locality_filter": "Indiranagar",
  "clusters": [
    {
      "activity": "Badminton",
      "activity_id": 2,
      "interest_id": 1,
      "category": "Sports",
      "locality": "Indiranagar",
      "preferred_day": "Saturday",
      "preferred_time": "18:00-20:00",
      "interested_users": 12,
      "active_events": 1,
      "available_spots": 2,
      "estimated_unmet_demand": 10,
      "demand_score": 91,
      "status": "HIGH_DEMAND",
      "suggested_action": "Host new events or partner with local venues in Indiranagar to absorb 10 unmet players."
    }
  ]
}
```

#### 10. Example AI Demand Prediction & Feasibility (`POST /ai/demand-prediction`)
```bash
curl -X POST "http://127.0.0.1:8000/ai/demand-prediction" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{
    "activity": "Badminton",
    "locality": "Indiranagar",
    "day_of_week": "Saturday",
    "preferred_time": "18:00-20:00"
  }'
```

#### Example AI Demand Prediction Response
```json
{
  "activity": "Badminton",
  "activity_id": 2,
  "interest_id": 1,
  "locality": "Indiranagar",
  "day_of_week": "Saturday",
  "preferred_time": "18:00-20:00",
  "current_demand": "HIGH",
  "demand_score": 91,
  "interested_users": 12,
  "active_events": 1,
  "available_spots": 2,
  "unmet_demand": 10,
  "expected_participants_min": 8,
  "expected_participants_max": 10,
  "expected_participants_range": "8-10",
  "attendance_probability": 82,
  "recommended_capacity": 8,
  "estimated_fill_rate": 87,
  "suggested_price_per_person": 300.0,
  "feasibility": "HIGH",
  "feasibility_score": 88,
  "venue_slots_available": 1,
  "factors": [
    "10 unmet players seeking Badminton in Indiranagar on Saturday",
    "Attendance probability: 82% with projected fill rate of 87%",
    "Recommended capacity of 8 participants (expected turnout: 8-10)",
    "1 active venue slot(s) in Indiranagar supporting ₹300/person split cost"
  ]
}
```

#### 14. Cross-Domain Opportunity Intelligence (`GET /ai/opportunities`)
Combines multi-domain signals across Demand Radar, Feasibility Prediction, Matching & Venue Availability to surface ranked, actionable opportunities:

```bash
curl -X GET "http://127.0.0.1:8000/ai/opportunities?locality=Indiranagar&activity=Badminton&min_opportunity_score=50" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

#### Example Opportunity Intelligence Response
```json
{
  "total_opportunities": 1,
  "locality_filter": "Indiranagar",
  "opportunities": [
    {
      "opportunity_type": "CREATE_EVENT",
      "activity": "Badminton",
      "activity_id": 2,
      "interest_id": 1,
      "locality": "Indiranagar",
      "day": "Saturday",
      "time": "18:00-20:00",
      "demand_score": 91,
      "feasibility_score": 88,
      "opportunity_score": 90,
      "expected_participants": "8-10",
      "recommended_capacity": 8,
      "venue_available": true,
      "venue_slots_count": 1,
      "suggested_price_per_person": 300.0,
      "action": "CREATE_EVENT",
      "reasons": [
        "High unmet demand: 10 players seeking Badminton in Indiranagar on Saturday",
        "Deterministic feasibility: 88% with projected fill rate of 87%",
        "1 bookable venue slot(s) verified in Indiranagar"
      ]
    }
  ]
}
```

#### 15. AI Community Intelligence (`GET /ai/community-intelligence`)
Detects naturally recurring groups, weekly schedules, shared localities, and repeated event participation to propose community circles before creation:

```bash
curl -X GET "http://127.0.0.1:8000/ai/community-intelligence?locality=Indiranagar&activity=Badminton&day=Saturday" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

#### Example Community Intelligence Response
```json
{
  "total_proposals": 1,
  "locality_filter": "Indiranagar",
  "proposals": [
    {
      "community_type": "SPORTS",
      "theme": "Indiranagar Weekend Badminton",
      "activity": "Badminton",
      "activity_id": 2,
      "interest_id": 1,
      "locality": "Indiranagar",
      "member_candidates": 14,
      "candidate_user_ids": [1, 3, 4, 5, 7, 8, 12, 14, 15, 18, 19, 21, 22, 25],
      "recurring_pattern": "Saturday evenings",
      "day_of_week": "Saturday",
      "time_window": "18:00-20:00",
      "compatibility_score": 87,
      "community_opportunity_score": 91,
      "suggested_action": "CREATE_COMMUNITY",
      "action_payload": {
        "name": "Indiranagar Weekend Badminton",
        "description": "A recurring local community for Badminton enthusiasts in Indiranagar (Saturday evenings).",
        "initial_member_ids": [1, 3, 4, 5, 7, 8, 12, 14, 15, 18, 19, 21, 22, 25],
        "activity": "Badminton",
        "locality": "Indiranagar",
        "recurring_pattern": "Saturday evenings",
        "community_type": "SPORTS",
        "suggested_action": "CREATE_COMMUNITY"
      },
      "reasons": [
        "14 compatible peers with active Badminton interest in Indiranagar",
        "Recurring availability pattern on Saturday evenings",
        "Cohort compatibility score: 87%",
        "Strong track record of repeated participation (5 past event sessions)"
      ],
      "existing_community_id": null
    }
  ]
}
```

#### 16. Deterministic Community Health Inspection (`GET /communities/{community_id}/health`)
Inspect verified health metrics, engagement, and lifecycle score for an enrolled community circle:

```bash
curl -X GET "http://127.0.0.1:8000/communities/12/health" \
  -H "Authorization: Bearer <MEMBER_ACCESS_TOKEN>"
```

#### Example Community Health Response
```json
{
  "community_id": 12,
  "member_count": 14,
  "active_member_count": 10,
  "events_created": 8,
  "completed_events": 6,
  "recent_event_count": 3,
  "average_event_participation": 78,
  "average_feedback_rating": 4.4,
  "health_score": 86,
  "health_status": "HEALTHY"
}
```

#### 17. Deterministic Community Health Trend & Comparison (`GET /communities/{community_id}/health/trend`)
Inspect health trajectory, period-over-period score differences, and component metric shifts for an enrolled community circle:

```bash
curl -X GET "http://127.0.0.1:8000/communities/12/health/trend?window_days=30" \
  -H "Authorization: Bearer <MEMBER_ACCESS_TOKEN>"
```

#### Example Community Health Trend Response
```json
{
  "community_id": 12,
  "current_health_score": 86,
  "previous_health_score": 72,
  "score_change": 14,
  "trend": "IMPROVING",
  "current_status": "HEALTHY",
  "previous_status": "GROWING",
  "metrics_comparison": {
    "active_members": {
      "current": 10,
      "previous": 8,
      "change": 2
    },
    "events_created": {
      "current": 8,
      "previous": 5,
      "change": 3
    },
    "completed_events": {
      "current": 6,
      "previous": 4,
      "change": 2
    },
    "average_participation": {
      "current": 78,
      "previous": 65,
      "change": 13
    },
    "average_feedback": {
      "current": 4.4,
      "previous": 4.1,
      "change": 0.3
    }
  }
}
```

#### 18. AI Community Lifecycle Intelligence (`GET /communities/{community_id}/lifecycle`)
Inspect AI-synthesized lifecycle stage analysis, growth insights, and recommended tactical focus built strictly on top of verified deterministic metrics:

```bash
curl -X GET "http://127.0.0.1:8000/communities/12/lifecycle?window_days=30" \
  -H "Authorization: Bearer <MEMBER_ACCESS_TOKEN>"
```

#### Example Community Lifecycle Response
```json
{
  "community_id": 12,
  "health_score": 86,
  "health_status": "HEALTHY",
  "trend": "IMPROVING",
  "score_change": 14,
  "lifecycle_stage": "GROWING",
  "insight": "The community is becoming more active, with participation and event frequency increasing.",
  "recommended_focus": "Continue recurring weekend activities and maintain member engagement."
}
```

#### 19. AI Community Action Recommendation API (`GET /communities/{community_id}/recommendations`)
Inspect actionable, lifecycle-grounded recommendations for community organizers, powered by AI with deterministic fallbacks and strict action validation:

```bash
curl -X GET "http://127.0.0.1:8000/communities/12/recommendations?window_days=30" \
  -H "Authorization: Bearer <MEMBER_ACCESS_TOKEN>"
```

#### Example Action Recommendations Response
```json
{
  "community_id": 12,
  "recommendations": [
    {
      "priority": "HIGH",
      "action": "MAINTAIN_ACTIVITY",
      "title": "Maintain community momentum",
      "reason": "Community health is strong and improving with consistent participation.",
      "suggested_next_step": "Schedule regular recurring activities and celebrate active contributors."
    },
    {
      "priority": "MEDIUM",
      "action": "GROW_MEMBERSHIP",
      "title": "Expand community membership",
      "reason": "Healthy core engagement provides a great foundation to welcome new members.",
      "suggested_next_step": "Invite compatible local users to upcoming sessions."
    }
  ]
}
```



