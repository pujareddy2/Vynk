from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models
from datetime import date, timedelta, time
from decimal import Decimal

client = TestClient(app)

def test_complete_event_journey():
    print("\n=======================================================")
    print("=== STARTING COMPLETE EVENT & PARTICIPATION JOURNEY ===")
    print("=======================================================\n")

    # 1. Setup Host & Venue Slot
    print("--- 1. Setting up Organizer / Host ---")
    client.post('/auth/register', json={'email': 'host.lead@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_host = client.post('/auth/login', json={'email': 'host.lead@vynk.com', 'password': 'password123'}).json()['access_token']
    h_host = {'Authorization': f'Bearer {tok_host}'}

    db = SessionLocal()
    badminton = db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
    badminton_id = badminton.interest_id if badminton else 2

    # Create Activity
    act = client.post('/activities', json={
        'interest_id': badminton_id,
        'title': 'Weekend Badminton Championship 2v2',
        'description': 'Intense intermediate 2v2 doubles match.'
    }, headers=h_host).json()
    act_id = act['activity_id']

    # Create Venue & Slot (Capacity = 4, Total Price = ₹1200)
    venue = client.post('/venues', json={
        'name': 'SmashPoint Badminton Hub',
        'description': '4 indoor synthetic courts with shower facilities',
        'address': '100ft Road, Indiranagar',
        'locality': 'Indiranagar, Bengaluru',
        'activity_ids': [act_id]
    }, headers=h_host).json()
    venue_id = venue['venue_id']

    tomorrow = date.today() + timedelta(days=1)
    slot = client.post(f'/venues/{venue_id}/slots', json={
        'slot_date': tomorrow.isoformat(),
        'start_time': '18:00:00',
        'end_time': '20:00:00',
        'price_total': 1200.0,
        'currency': 'INR'
    }, headers=h_host).json()
    slot_id = slot['slot_id']

    # 2. Host Creates Event with Slot (Max Capacity = 3)
    print("\n--- 2. Creating Event with Venue Slot (Max Capacity = 3, INR 1200) ---")
    event = client.post('/events', json={
        'activity_id': act_id,
        'title': 'Saturday Evening Badminton Doubles',
        'event_date': tomorrow.isoformat(),
        'start_time': '18:00:00',
        'end_time': '20:00:00',
        'max_capacity': 3,
        'slot_id': slot_id
    }, headers=h_host).json()
    ev_id = event['event_id']

    print(f"Created Event ID: {ev_id}")
    print(f"Status: {event['status']}")
    print(f"Host: {event['host_name']}")
    print(f"Participants: {event['participant_count']}/3 (Remaining Spots: {event['remaining_spots']})")
    print(f"Split Cost per Person (1 Host): INR {event['per_person_cost']}")
    assert event['participant_count'] == 1
    assert event['remaining_spots'] == 2
    assert event['per_person_cost'] == 1200.0

    # 3. User 2 Discovers and Joins Event
    print("\n--- 3. User 2 (Karan) Discovers Event & Joins ---")
    client.post('/auth/register', json={'email': 'karan.player@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_karan = client.post('/auth/login', json={'email': 'karan.player@vynk.com', 'password': 'password123'}).json()['access_token']
    h_karan = {'Authorization': f'Bearer {tok_karan}'}

    # Discovery by locality & availability
    discover_res = client.get(f'/events?locality=Indiranagar&available_only=true', headers=h_karan).json()
    print(f"Discovered Events in Indiranagar with available capacity: {len(discover_res)}")

    # Karan Joins
    joined_ev = client.post(f'/events/{ev_id}/join', headers=h_karan).json()
    print(f"Karan joined! Participants: {joined_ev['participant_count']}/3 (Remaining Spots: {joined_ev['remaining_spots']})")
    print(f"Recalculated Split Cost per Person (1200 / 2): INR {joined_ev['per_person_cost']}")
    assert joined_ev['participant_count'] == 2
    assert joined_ev['remaining_spots'] == 1
    assert joined_ev['per_person_cost'] == 600.0

    # 4. User 3 (Rohan) Joins -> Event Reaches Full Capacity!
    print("\n--- 4. User 3 (Rohan) Joins -> Event Becomes FULL ---")
    client.post('/auth/register', json={'email': 'rohan.player@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_rohan = client.post('/auth/login', json={'email': 'rohan.player@vynk.com', 'password': 'password123'}).json()['access_token']
    h_rohan = {'Authorization': f'Bearer {tok_rohan}'}

    full_ev = client.post(f'/events/{ev_id}/join', headers=h_rohan).json()
    print(f"Rohan joined! Status: {full_ev['status']} | Participants: {full_ev['participant_count']}/3 (Remaining: {full_ev['remaining_spots']})")
    print(f"Recalculated Split Cost per Person (1200 / 3): INR {full_ev['per_person_cost']}")
    assert full_ev['status'] == "FULL"
    assert full_ev['participant_count'] == 3
    assert full_ev['remaining_spots'] == 0
    assert full_ev['per_person_cost'] == 400.0

    # 5. User 4 Attempts to Join -> Rejection with Capacity Protection
    print("\n--- 5. User 4 Attempts to Join Full Event ---")
    client.post('/auth/register', json={'email': 'extra.player@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_extra = client.post('/auth/login', json={'email': 'extra.player@vynk.com', 'password': 'password123'}).json()['access_token']
    h_extra = {'Authorization': f'Bearer {tok_extra}'}

    err_join = client.post(f'/events/{ev_id}/join', headers=h_extra)
    print(f"Attempt to join full event result: {err_join.status_code} — {err_join.json()['detail']}")
    assert err_join.status_code == 400

    # 6. User 3 (Rohan) Leaves -> DELETE /events/{event_id}/join
    print("\n--- 6. User 3 (Rohan) Leaves -> Capacity & Cost Recalculate Safely ---")
    left_ev = client.delete(f'/events/{ev_id}/join', headers=h_rohan).json()
    print(f"Rohan left using DELETE /events/{ev_id}/join!")
    print(f"Event Status Reverted To: {left_ev['status']}")
    print(f"Participants: {left_ev['participant_count']}/3 (Remaining Spots: {left_ev['remaining_spots']})")
    print(f"Split Cost Safely Restored To (1200 / 2): INR {left_ev['per_person_cost']}")
    assert left_ev['status'] == "PUBLISHED"
    assert left_ev['participant_count'] == 2
    assert left_ev['remaining_spots'] == 1
    assert left_ev['per_person_cost'] == 600.0

    # 7. Host Completes Event -> Lifecycle State Validation
    print("\n--- 7. Host Completes Event (Lifecycle Validation) ---")
    completed_ev = client.patch(f'/events/{ev_id}', json={'status': 'COMPLETED'}, headers=h_host).json()
    print(f"Event Lifecycle Status: {completed_ev['status']}")
    assert completed_ev['status'] == "COMPLETED"

    # Verify no one can join/leave a completed event
    cant_join = client.post(f'/events/{ev_id}/join', headers=h_extra)
    print(f"Attempt to join completed event: {cant_join.status_code} — {cant_join.json()['detail']}")
    assert cant_join.status_code == 400

    print("\n=======================================================")
    print("=== ALL EVENT & PARTICIPATION JOURNEY TESTS PASSED! ===")
    print("=======================================================\n")

if __name__ == '__main__':
    test_complete_event_journey()
