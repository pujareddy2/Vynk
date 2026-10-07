# Localy (Vynk) — Setup & API Guide

A clean, reproducible guide to run the FastAPI backend, PostgreSQL database, and Next.js frontend.

---

## 1. Database & Backend (FastAPI + PostgreSQL)

### Database Configuration
PostgreSQL connection string configured in `backend/.env` under `DATABASE_URL`:
- **Connection:** `postgresql://postgres:puja%40555@localhost:5555/major`

### Run Backend
```bash
cd backend
python -m pip install -r requirements.txt
python main.py
```
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Interactive ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 🔐 2. Authentication API

| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `POST` | `/auth/register` | Register new user with email & password | No |
| `POST` | `/auth/login` | Authenticate credentials and receive JWT | No |
| `GET` | `/auth/me` | Fetch currently logged-in account | **Yes (Bearer JWT)** |

---

## 🎨 3. Catalog API (Interests & Skills Taxonomy)

| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `GET` | `/interests` | List all standardized master interests | No |
| `GET` | `/skills` | List all standardized master skills | No |

---

## 👤 4. Profile & Onboarding API

| Method | Endpoint | Description | Protected? |
| :--- | :--- | :--- | :---: |
| `GET` | `/profile/me` | Fetch full profile, interests, skills & availability | **Yes (Bearer JWT)** |
| `PATCH` | `/profile/me` | Partially update display name, bio, locality, budget | **Yes (Bearer JWT)** |
| `PUT` | `/profile/me/interests` | Replace selected interests list | **Yes (Bearer JWT)** |
| `PUT` | `/profile/me/skills` | Replace user skills with proficiency levels | **Yes (Bearer JWT)** |
| `PUT` | `/profile/me/availability` | Replace weekly availability schedule | **Yes (Bearer JWT)** |
| `POST` | `/profile/me/onboarding` | Complete atomic onboarding submission | **Yes (Bearer JWT)** |
| `GET` | `/profile/{user_id}` | View privacy-shielded public profile | No |

### Example Onboarding Submission:
```bash
curl -X POST "http://127.0.0.1:8000/profile/me/onboarding" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Puja Reddy",
    "bio": "Passionate about AI, Badminton & Acoustic Music",
    "approx_locality": "Banjara Hills, Hyderabad",
    "budget_preference": "low",
    "interest_ids": [1, 2, 11],
    "skills": [
      {
        "skill_id": 5,
        "skill_level": "Intermediate",
        "is_offering": true
      }
    ],
    "availability": [
      {
        "day_of_week": "Saturday",
        "start_time": "18:00:00",
        "end_time": "21:00:00"
      }
    ]
  }'
```

---

## 5. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```
- **App:** [http://localhost:3000](http://localhost:3000)
- **Display:** `backend connected (database connected)`
