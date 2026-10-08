from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)

def test_people_matching():
    print("--- 1. Setting up Rahul (Seeker) ---")
    client.post('/auth/register', json={'email': 'rahul.seeker@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_rahul = client.post('/auth/login', json={'email': 'rahul.seeker@vynk.com', 'password': 'password123'}).json()['access_token']
    h_rahul = {'Authorization': f'Bearer {tok_rahul}'}

    client.post('/profile/me/onboarding', json={
        'display_name': 'Rahul Sharma',
        'bio': 'Looking for cricket and badminton partners on weekends',
        'approx_locality': 'Indiranagar, Bengaluru',
        'budget_preference': 'flexible',
        'interest_ids': [1, 2],
        'skills': [{'skill_id': 14, 'skill_level': 'Intermediate', 'is_offering': True}],
        'availability': [{'day_of_week': 'Saturday', 'start_time': '18:00:00', 'end_time': '21:00:00'}]
    }, headers=h_rahul)

    print("--- 2. Setting up Amit (Perfect Candidate: Cricket + Badminton + Indiranagar + Saturday + Coaching) ---")
    client.post('/auth/register', json={'email': 'amit.cricketer@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_amit = client.post('/auth/login', json={'email': 'amit.cricketer@vynk.com', 'password': 'password123'}).json()['access_token']
    client.post('/profile/me/onboarding', json={
        'display_name': 'Amit Kumar',
        'bio': 'All-rounder cricket player and weekend doubles enthusiast',
        'approx_locality': 'Indiranagar, Bengaluru',
        'budget_preference': 'flexible',
        'interest_ids': [1, 2],
        'skills': [{'skill_id': 14, 'skill_level': 'Advanced', 'is_offering': True}],
        'availability': [{'day_of_week': 'Saturday', 'start_time': '18:00:00', 'end_time': '20:00:00'}]
    }, headers={'Authorization': f'Bearer {tok_amit}'})

    print("--- 3. Setting up Sneha (Partial Candidate: Cricket + Koramangala + Sunday) ---")
    client.post('/auth/register', json={'email': 'sneha.sports@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_sneha = client.post('/auth/login', json={'email': 'sneha.sports@vynk.com', 'password': 'password123'}).json()['access_token']
    client.post('/profile/me/onboarding', json={
        'display_name': 'Sneha Rao',
        'bio': 'Casual cricket enthusiast and runner',
        'approx_locality': 'Koramangala, Bengaluru',
        'budget_preference': 'low',
        'interest_ids': [2, 7],
        'skills': [],
        'availability': [{'day_of_week': 'Sunday', 'start_time': '07:00:00', 'end_time': '09:00:00'}]
    }, headers={'Authorization': f'Bearer {tok_sneha}'})

    print("--- 4. Setting up Dev (Tech Candidate: AI/ML + Whitefield + Wednesday) ---")
    client.post('/auth/register', json={'email': 'dev.techie@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_dev = client.post('/auth/login', json={'email': 'dev.techie@vynk.com', 'password': 'password123'}).json()['access_token']
    client.post('/profile/me/onboarding', json={
        'display_name': 'Dev Patel',
        'bio': 'Building AI agents and web apps',
        'approx_locality': 'Whitefield, Bengaluru',
        'budget_preference': 'free',
        'interest_ids': [17, 18],
        'skills': [{'skill_id': 5, 'skill_level': 'Advanced', 'is_offering': True}],
        'availability': [{'day_of_week': 'Wednesday', 'start_time': '19:00:00', 'end_time': '21:00:00'}]
    }, headers={'Authorization': f'Bearer {tok_dev}'})

    db = SessionLocal()
    cricket = db.query(models.Interest).filter(models.Interest.name == "Cricket").first()
    badminton = db.query(models.Interest).filter(models.Interest.name == "Badminton").first()
    cricket_id = cricket.interest_id if cricket else 2
    badminton_id = badminton.interest_id if badminton else 1

    print("\n==========================================")
    print(f"=== EXECUTING MATCH QUERY FOR BADMINTON (ID: {badminton_id}) + SATURDAY ===")
    print("==========================================")
    res_sat = client.get(f'/matches?interest_id={badminton_id}&day_of_week=Saturday', headers=h_rahul).json()
    for i, m in enumerate(res_sat.get('matches', []), 1):
        print(f"Rank #{i}: {m['display_name']} — Score: {m['match_score']}/100")
        print(f"  Score Breakdown: {m['match_breakdown']}")
        print(f"  Match Reasons: {m['match_reasons']}")
        print(f"  Shared Interests: {m['shared_interests']}")
        print(f"  Relevant Skills: {m['relevant_skills']}")
        print(f"  Availability: {m['shared_availability']}")
        print("-" * 50)

if __name__ == '__main__':
    test_people_matching()
