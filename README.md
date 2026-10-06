# Localy (Vynk) — AI-Powered Local Activity, Talent & Community Network

> **Turning local interests and intentions into real-world participation, offline experiences, and active communities.**

---

## 🌟 1. Vision & Mission

### 🎯 Vision
To transform disconnected local individuals into thriving, self-sustaining real-world communities by converting personal interests, latent skills, and immediate intentions into offline participation, shared experiences, and authentic social bonds.

### 🚀 Mission
Provide an intelligent, intent-driven, privacy-preserving coordination platform that bridges participants, emerging creators/talents, local venues, and recurring communities—replacing mindless digital feeds with verified offline action and demand-validated micro-experiences.

---

## 📖 2. Project Description

**Localy** is an AI-powered local activity, talent, and community platform that connects people based on **what they want to do, create, learn, experience, or discuss**—rather than merely who they are.

Modern social and networking platforms are fundamentally fragmented:
- **Social Media** fosters passive scrolling rather than active real-world connection.
- **Event Platforms** cater to large commercial events, ignoring spontaneous micro-gatherings (5–25 people).
- **Sports & Interest Apps** operate in isolated silos, making discovery rigid and impersonal.

Localy introduces an **AI intelligence layer** that understands the multi-dimensional intent of users (interests, skill levels, budget, real-time availability, and approximate location) to coordinate real-world experiences seamlessly:
- **"I want to do something"** ➔ **"I found the right people"** ➔ **"We made it happen"** ➔ **"We became a community"**

---

## 🔍 3. Core Problems Solved

1. **Activity Coordination Friction:** People frequently want to participate in sports, music, discussions, or hobbies (e.g., badminton, jamming, tech meetups) but lack available peers at that precise moment, budget, or location.
2. **Emerging Talent & Creator Barriers:** Local singers, artists, comedians, and teachers struggle to host small gatherings due to upfront venue costs, lack of audience reach, and fear of low turnout.
3. **Absence of Demand Validation:** Creators risk capital before knowing if real interest exists. Localy introduces a **"Demand-Before-Investment"** model to validate participation upfront.
4. **Fragmented Community Building:** Individuals living within a few kilometers sharing identical passions (e.g., AI engineering, acoustic music, cycling) remain separated with no discovery mechanism.
5. **Privacy & Offline Safety Risks:** Strangers meeting offline requires strict safety protocols without exposing exact residential addresses, phone numbers, or private metadata.

---

## 💡 4. Key Platform Pillars & Features

```
                                    PLATFORM CORE
                                          │
    ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
    ▼                  ▼                  ▼                  ▼                  ▼
[Intent Engine] [Demand Radar]   [Semantic Matching] [Creator Studio] [Trust & Privacy]
 "Do Something   Pre-validate      Multi-attribute    Micro-events,    Approx location,
     Now"        interest first    compatibility       cost-split       trust scores
```

### 🎯 1. Intent-Driven Discovery ("What Do You Want to Do?")
- Dynamic intent processing (`Participate`, `Create`, `Learn`, `Connect`, `Relax`).
- **"Do Something Now"**: Real-time matching based on instantaneous free time (e.g., *"I have 2 hours and ₹200 free tonight"*).
- **"I Don't Know What I Want"**: Structured conversational AI discovery for open-ended queries.

### 📊 2. Demand-Before-Investment & Demand Radar
- Creators publish experience drafts without upfront financial commitment.
- Public collects **"Expressions of Interest"**; AI calculates attendance feasibility scores.
- **Unmet Demand Detection**: Alerts creators when clusters of local users request activities that don't yet exist.

### 🧠 3. Semantic Person & Group Matching
- Hybrid matching engine: Strict hard filters (distance, availability, privacy) + vector embeddings (`pgvector`) for interest & skill semantic compatibility.
- Multi-player group formation for team sports, jam sessions, and study circles.

### 🤝 4. Skill-Swap, Mentorship & Micro-Experiences
- Direct reciprocal skill exchange (e.g., *Python ↔ Guitar*).
- Low-cost, high-impact gatherings (5–30 seats) with automated cost-splitting calculators.

### 🔒 5. Privacy, Trust & Reputation
- **Approximate Location Zones**: No exact residential coordinate leakage; visual activity heatmaps and radar zones.
- **Reputation Intelligence**: Trust scores based on actual attendance, reliability, host reviews, and community contributions.
- **Safety First**: Event check-in/check-out, reporting, instant blocking, and verification tiers.

---

## 🛠️ 5. Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend Framework** | **Next.js 14+ (React, TypeScript, App Router)** |
| **UI & Styling** | **Tailwind CSS + shadcn/ui + Lucide React** |
| **State Management** | **Zustand** (Client State) + **TanStack Query v5** (Server State) |
| **Forms & Validation** | **React Hook Form + Zod** |
| **Mapping & Spatial UI** | **Mapbox GL JS / react-map-gl** |
| **Backend Framework** | **FastAPI (Python 3.11+)** |
| **ORM & Migrations** | **SQLAlchemy 2.0 + Alembic** |
| **Database & Vector Search** | **PostgreSQL 16+ (Supabase) + pgvector** |
| **Authentication & Storage**| **Supabase Auth (JWT / RBAC) + Supabase Storage** |
| **AI / LLM Layer** | **OpenAI API (Structured JSON / GPT-4o) + Text Embeddings** |
| **Caching & Background** | **Redis + Celery** (as needed) |
| **Testing & Quality** | **Pytest** (Backend), **Vitest + Playwright** (Frontend), **Ruff + ESLint** |
| **Deployment & Ops** | **Vercel** (Frontend), **Render** (Backend), **Sentry + PostHog** |

---

## 🏗️ 6. System Architecture

```
                    ┌────────────────────────────────────────┐
                    │          Next.js App Router            │
                    │   (Desktop & Mobile-First Web App)     │
                    └───────────────────┬────────────────────┘
                                        │
                                        ▼ REST API (HTTPS / JSON)
                    ┌────────────────────────────────────────┐
                    │           FastAPI Application          │
                    │   Routers ──► Services ──► Repos       │
                    └─────────┬───────────────────┬──────────┘
                              │                   │
               ┌──────────────┴──────────┐        └──────────────┐
               ▼                         ▼                       ▼
┌─────────────────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│ PostgreSQL 16+ (Supabase)   │ │  pgvector Search │ │ OpenAI Intelligence  │
│ - Relational Entities       │ │  - User Vectors  │ │ - Intent Parser      │
│ - Capacity & Concurrency    │ │  - Activity Sim  │ │ - Feasibility Scorer │
│ - Audit Logs & Safety       │ │  - Skill Graphs  │ │ - Experience Builder │
└─────────────────────────────┘ └──────────────────┘ └──────────────────────┘
               │                                                 │
               └───────────────────────┬─────────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   Real-World Participation    │
                       │ Attendance, Reviews, Feedback │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Continuous AI Learning Loop  │
                       └───────────────────────────────┘
```

---

## 👥 7. Team Alignment & Ownership

- **Member 1 (Frontend Lead):** User interface design system, responsive screen implementation, client state management, form validations, API service abstraction layer, and frontend testing.
- **Member 2 (Backend & AI Lead):** Database architecture, Alembic migrations, FastAPI endpoints, Pydantic schemas, concurrency controls, Supabase auth/storage integration, pgvector vector matching, and AI orchestrations.
- **Member 3 (Product, QA & Documentation Lead):** Product requirements verification, user journey test plans, manual scenario validation, edge-case and safety audits, AI output evaluation, and system documentation.

---

## 🗺️ 8. Phased Development Roadmap

- [x] **Phase 0:** Strategic Planning, Architectural Blueprint & Repository Setup
- [ ] **Phase 1 – 2:** Database Master Architecture, Schema Definition & Alembic Migrations
- [ ] **Phase 3 – 4:** Backend Foundation, API Architecture & Supabase Auth Integration
- [ ] **Phase 5 – 7:** User Profiles, Interest & Skill Taxonomy, and Structured Intent System
- [ ] **Phase 8 – 10:** Activity Engine, Concurrency-Safe Events & People/Group Matching
- [ ] **Phase 11 – 13:** Creator Studio, Demand-Before-Investment & Cost Planning
- [ ] **Phase 14 – 16:** Recurring Communities, Skill-Swap, Privacy Shields & Safety Check-ins
- [ ] **Phase 17 – 28:** Applied AI (Intent Extraction, Semantic Embeddings, Demand Radar & Learning Loop)
- [ ] **Phase 29 – 34:** End-to-End System Integration, Security Audits, CI/CD & Cloud Deployment

---

## 📄 License
This project is developed as an academic Major Project. All rights reserved.
