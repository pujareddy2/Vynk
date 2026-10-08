# Localy (Vynk) — Setup & API Architecture Guide

A clean, reproducible guide to run the FastAPI backend, PostgreSQL database, Next.js frontend, and the Deterministic Matchmaking Engine.

---

## 🏛️ 1. Frozen 20-Table Database Architecture

| No. | Table | Purpose | Key Relationships |
| :--- | :--- | :--- | :--- |
| 1 | `users` | Single auth source of truth | Email, password hash, account status |
| 2 | `profiles` | User-facing public identity | 1:1 `users.user_id`, locality, bio, budget |
| 3 | `interests` | Master taxonomy catalog | Sports, Music, Tech, Creative, Learning |
| 4 | `user_interests` | User selected interests | N:M `(user_id, interest_id)` composite PK |
| 5 | `skills` | Master skills catalog | Standardized skill taxonomy |
| 6 | `user_skills` | User skills + proficiency | N:M `(user_id, skill_id)` composite PK + level |
| 7 | `user_availability` | Weekly schedule windows | 1:N `users.user_id`, day of week, times |
| 8 | `activities` | Activity concept/template | FK `interest_id`, FK `created_by` |
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

---

## 🚀 2. Running Locally

### Backend (FastAPI + PostgreSQL)
PostgreSQL connection configured in `backend/.env` under `DATABASE_URL`:
- **Connection:** `postgresql://postgres:puja%40555@localhost:5555/major`

```bash
cd backend
python -m pip install -r requirements.txt
python main.py
```
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Interactive ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
- **App:** [http://localhost:3000](http://localhost:3000)

---

## 🎯 3. Deterministic People Matching Engine

### Scoring Formula (Max 100 Points)
```text
Candidate Score = Interest (max 40) + Availability (max 30) + Location (max 20) + Skill (max 10)
```

| Component | Points | Criteria |
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

### Example Matching Query
```bash
curl -X GET "http://127.0.0.1:8000/matches?interest_id=2&day_of_week=Saturday" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Example Matching Response
```json
{
  "total_candidates": 1,
  "activity_id": null,
  "activity_title": null,
  "target_interest": "Badminton",
  "matches": [
    {
      "user_id": 3,
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
| `POST` | `/events/{id}/feedback` | Submit post-event peer rating (1-5) & review | **Yes** |
| `GET` | `/events/{id}/feedback` | Get all peer reviews for an event | No |

### 🧠 AI Intent Engine (Natural Language Understanding & Connected Search)
| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/ai/intent` | Understand and extract structured parameters from natural language input | No |
| `POST` | `/ai/intent/search` | Natural Language → AI Intent → People Matching, Events & Venues Discovery | Optional |

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
      "status": "ACTIVE"
    }
  ]
}
```


