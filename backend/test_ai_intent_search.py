"""
Vynk (Localy) - AI Intent Search Integration Test
Tests end-to-end Natural Language -> AI Intent Extraction -> Deterministic Matching & Discovery
Endpoint: POST /ai/intent/search
"""

import sys
from datetime import date, time, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
import models
from auth import hash_password

client = TestClient(app)


def setup_test_data():
    db = SessionLocal()
    try:
        # 1. Clean previous test users and their related entities
        test_emails = [
            "ai_seeker_rahul@example.com",
            "ai_candidate_amit@example.com",
            "ai_candidate_sneha@example.com",
            "ai_host_karan@example.com",
            "rahul_test@example.com",
            "amit_test@example.com",
            "sneha_test@example.com",
            "dev_test@example.com",
            "rahul@vynk.local",
            "amit@vynk.local",
            "sneha@vynk.local",
            "dev@vynk.local",
            "puja@vynk.local",
            "rahul.seeker@vynk.com",
            "amit.cricketer@vynk.com",
            "sneha.sports@vynk.com",
            "dev.techie@vynk.com",
        ]
        u_ids = [u.user_id for u in db.query(models.User).filter(models.User.email.in_(test_emails)).all()]
        if u_ids:
            # Delete feedbacks
            db.query(models.Feedback).filter(models.Feedback.reviewer_id.in_(u_ids)).delete(synchronize_session=False)
            # Delete payments
            db.query(models.Payment).filter(models.Payment.user_id.in_(u_ids)).delete(synchronize_session=False)
            # Delete bookings
            ev_ids = [e.event_id for e in db.query(models.Event).filter(models.Event.host_id.in_(u_ids)).all()]
            if ev_ids:
                db.query(models.Feedback).filter(models.Feedback.event_id.in_(ev_ids)).delete(synchronize_session=False)
                db.query(models.Payment).filter(models.Payment.booking_id.in_(
                    [b.booking_id for b in db.query(models.VenueBooking).filter(models.VenueBooking.event_id.in_(ev_ids)).all()]
                )).delete(synchronize_session=False)
                db.query(models.VenueBooking).filter(models.VenueBooking.event_id.in_(ev_ids)).delete(synchronize_session=False)
                db.query(models.EventParticipant).filter(models.EventParticipant.event_id.in_(ev_ids)).delete(synchronize_session=False)
                db.query(models.Event).filter(models.Event.event_id.in_(ev_ids)).delete(synchronize_session=False)

            db.query(models.EventParticipant).filter(models.EventParticipant.user_id.in_(u_ids)).delete(synchronize_session=False)
            db.query(models.UserInterest).filter(models.UserInterest.user_id.in_(u_ids)).delete(synchronize_session=False)
            db.query(models.UserSkill).filter(models.UserSkill.user_id.in_(u_ids)).delete(synchronize_session=False)
            db.query(models.UserAvailability).filter(models.UserAvailability.user_id.in_(u_ids)).delete(synchronize_session=False)
            db.query(models.Profile).filter(models.Profile.user_id.in_(u_ids)).delete(synchronize_session=False)
            db.query(models.User).filter(models.User.user_id.in_(u_ids)).delete(synchronize_session=False)
            db.commit()

        # 2. Lookup Master Interests & Skills
        badminton_int = db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
        cricket_int = db.query(models.Interest).filter(models.Interest.name == "Box Cricket").first()
        badminton_skill = db.query(models.Skill).filter(models.Skill.name.ilike("%badminton%")).first()

        # 3. Create User 1: Rahul (Seeker in Indiranagar)
        rahul = models.User(email="ai_seeker_rahul@example.com", password_hash=hash_password("Pass123!"), is_active=True)
        db.add(rahul)
        db.flush()
        db.add(models.Profile(user_id=rahul.user_id, display_name="Rahul Sharma", approx_locality="Indiranagar, Bengaluru"))
        db.add(models.UserInterest(user_id=rahul.user_id, interest_id=badminton_int.interest_id))
        db.add(models.UserAvailability(user_id=rahul.user_id, day_of_week="Saturday", start_time=time(18, 0), end_time=time(21, 0)))

        # 4. Create User 2: Amit (Perfect Match for Badminton in Indiranagar on Saturday)
        amit = models.User(email="ai_candidate_amit@example.com", password_hash=hash_password("Pass123!"), is_active=True)
        db.add(amit)
        db.flush()
        db.add(models.Profile(user_id=amit.user_id, display_name="Amit Kumar", approx_locality="Indiranagar, Bengaluru"))
        db.add(models.UserInterest(user_id=amit.user_id, interest_id=badminton_int.interest_id))
        db.add(models.UserAvailability(user_id=amit.user_id, day_of_week="Saturday", start_time=time(18, 0), end_time=time(20, 0)))
        if badminton_skill:
            db.add(models.UserSkill(user_id=amit.user_id, skill_id=badminton_skill.skill_id, skill_level="Advanced", is_offering=True))

        # 5. Create User 3: Sneha (Partial Match for Badminton in Koramangala on Sunday)
        sneha = models.User(email="ai_candidate_sneha@example.com", password_hash=hash_password("Pass123!"), is_active=True)
        db.add(sneha)
        db.flush()
        db.add(models.Profile(user_id=sneha.user_id, display_name="Sneha Rao", approx_locality="Koramangala, Bengaluru"))
        db.add(models.UserInterest(user_id=sneha.user_id, interest_id=badminton_int.interest_id))
        db.add(models.UserAvailability(user_id=sneha.user_id, day_of_week="Sunday", start_time=time(7, 0), end_time=time(9, 0)))

        # 6. Create User 4: Karan (Host of an active Badminton Event in Indiranagar)
        karan = models.User(email="ai_host_karan@example.com", password_hash=hash_password("Pass123!"), is_active=True)
        db.add(karan)
        db.flush()
        db.add(models.Profile(user_id=karan.user_id, display_name="Karan Varma", approx_locality="Indiranagar, Bengaluru"))

        # 7. Create Activity Template & Venue for Badminton
        badminton_act = db.query(models.Activity).filter(models.Activity.title.ilike("%badminton%")).first()
        if not badminton_act:
            badminton_act = models.Activity(interest_id=badminton_int.interest_id, title="Badminton Doubles Match", created_by=karan.user_id)
            db.add(badminton_act)
            db.flush()

        venue = models.Venue(
            owner_user_id=karan.user_id,
            name="Indiranagar Badminton Arena",
            address="100 Feet Road, Indiranagar",
            locality="Indiranagar",
            is_verified=True,
            status="ACTIVE"
        )
        db.add(venue)
        db.flush()
        db.add(models.VenueActivity(venue_id=venue.venue_id, activity_id=badminton_act.activity_id))

        sat_date = date.today() + timedelta(days=(5 - date.today().weekday()) % 7 + 1)
        slot = models.VenueSlot(
            venue_id=venue.venue_id,
            slot_date=sat_date,
            start_time=time(18, 0),
            end_time=time(20, 0),
            price_total=Decimal("1200.00"),
            currency="INR",
            status="HELD"
        )
        db.add(slot)
        db.flush()

        # Create scheduled event with venue booking
        event = models.Event(
            activity_id=badminton_act.activity_id,
            host_id=karan.user_id,
            title="Saturday Evening Badminton Doubles Indiranagar",
            event_date=sat_date,
            start_time=time(18, 0),
            end_time=time(20, 0),
            max_capacity=4,
            status="PUBLISHED"
        )
        db.add(event)
        db.flush()
        db.add(models.EventParticipant(event_id=event.event_id, user_id=karan.user_id, status="CONFIRMED"))
        db.add(models.VenueBooking(
            event_id=event.event_id,
            slot_id=slot.slot_id,
            booked_by=karan.user_id,
            total_amount=Decimal("1200.00"),
            currency="INR",
            status="PENDING"
        ))

        db.commit()
        return rahul.user_id
    finally:
        db.close()


def test_ai_intent_search_flow():
    print("=" * 70)
    print("TESTING END-TO-END AI INTENT SEARCH (POST /ai/intent/search)")
    print("=" * 70)

    rahul_id = setup_test_data()

    # Log in as Rahul to get JWT
    login_resp = client.post("/auth/login", json={"email": "ai_seeker_rahul@example.com", "password": "Pass123!"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query: Natural language query
    user_sentence = "I want to play badminton this Saturday evening with people near me."
    print(f"\nUser Query: \"{user_sentence}\"")

    resp = client.post("/ai/intent/search", json={"query": user_sentence, "limit": 5}, headers=headers)
    assert resp.status_code == 200, f"Search failed: {resp.status_code}: {resp.text}"

    data = resp.json()

    print("\n--- 1. AI Intent Extracted ---")
    intent = data["intent_understood"]
    print(f"  Activity:    {intent['activity']} ({intent['category']})")
    print(f"  Day / Time:  {intent['day_of_week']} / {intent['time_of_day']}")
    print(f"  Location:    {intent['location']}")
    print(f"  Intent:      {intent['intent']}")
    print(f"  Engine:      {intent['engine']}")

    assert intent["activity"].lower() == "badminton"
    assert intent["day_of_week"] == "Saturday"
    assert intent["time_of_day"] == "evening"

    print("\n--- 2. Summary ---")
    print(f"  {data['summary']}")
    assert "Badminton" in data["summary"]

    print("\n--- 3. People Matches Found ---")
    assert len(data["people_matches"]) > 0, "Expected at least 1 people match candidate"
    for idx, match in enumerate(data["people_matches"], start=1):
        print(f"  {idx}. {match['display_name']} - {match['match_score']}% match ({match['approx_locality']})")
        print(f"     Reasons: {', '.join(match['match_reasons'])}")

    top_candidate = data["people_matches"][0]
    assert "Amit" in top_candidate["display_name"]
    assert top_candidate["match_score"] >= 80

    print("\n--- 4. Events Discovered ---")
    print(f"  Found {len(data['events'])} events")
    for ev in data["events"]:
        print(f"  • {ev['title']} ({ev['event_date']} {ev['start_time']}) - {ev['remaining_spots']} spots available")
    assert len(data["events"]) >= 1

    print("\n--- 5. Venues Discovered ---")
    print(f"  Found {len(data['venues'])} venues")
    for v in data["venues"]:
        print(f"  • {v['name']} ({v['locality']})")
    assert len(data["venues"]) >= 1

    # Test Case B: Unauthenticated Guest Search
    print("\n" + "-" * 70)
    print("Test Case B: Unauthenticated Guest Search")
    guest_query = "Looking for people to play badminton on Saturday evening in Indiranagar"
    print(f"Guest Query: \"{guest_query}\"")
    guest_resp = client.post("/ai/intent/search", json={"query": guest_query, "limit": 5})
    assert guest_resp.status_code == 200, f"Guest search failed: {guest_resp.status_code}: {guest_resp.text}"
    guest_data = guest_resp.json()
    assert len(guest_data["people_matches"]) > 0
    assert len(guest_data["events"]) > 0
    print(f"  Guest Summary: {guest_data['summary']}")
    print(f"  Top Candidate for Guest: {guest_data['people_matches'][0]['display_name']} ({guest_data['people_matches'][0]['match_score']}%)")

    print("\n" + "=" * 70)
    print("SUCCESS: Natural language -> AI intent -> Existing Vynk Matching/Events/Venues verified!")
    print("=" * 70)


if __name__ == "__main__":
    test_ai_intent_search_flow()
