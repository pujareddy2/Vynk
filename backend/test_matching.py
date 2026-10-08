import requests

BASE = 'http://127.0.0.1:8000'

def test_people_matching():
    # 1. Register and setup Seeker (Rahul)
    print("--- 1. Setting up Rahul (Seeker) ---")
    requests.post(f'{BASE}/auth/register', json={'email': 'rahul.seeker@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_rahul = requests.post(f'{BASE}/auth/login', json={'email': 'rahul.seeker@vynk.com', 'password': 'password123'}).json()['access_token']
    h_rahul = {'Authorization': f'Bearer {tok_rahul}'}

    requests.post(f'{BASE}/profile/me/onboarding', json={
        'display_name': 'Rahul Sharma',
        'bio': 'Looking for cricket and badminton partners on weekends',
        'approx_locality': 'Indiranagar, Bengaluru',
        'budget_preference': 'flexible',
        'interest_ids': [1, 2],
        'skills': [{'skill_id': 14, 'skill_level': 'Intermediate', 'is_offering': True}],
        'availability': [{'day_of_week': 'Saturday', 'start_time': '18:00:00', 'end_time': '21:00:00'}]
    }, headers=h_rahul)

    # 2. Register Candidate 1: Amit (Perfect Match: Cricket + Badminton + Indiranagar + Saturday + Coaching skill)
    print("--- 2. Setting up Amit (Perfect Candidate) ---")
    requests.post(f'{BASE}/auth/register', json={'email': 'amit.cricketer@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_amit = requests.post(f'{BASE}/auth/login', json={'email': 'amit.cricketer@vynk.com', 'password': 'password123'}).json()['access_token']
    requests.post(f'{BASE}/profile/me/onboarding', json={
        'display_name': 'Amit Kumar',
        'bio': 'All-rounder cricket player and weekend doubles enthusiast',
        'approx_locality': 'Indiranagar, Bengaluru',
        'budget_preference': 'flexible',
        'interest_ids': [1, 2],
        'skills': [{'skill_id': 14, 'skill_level': 'Advanced', 'is_offering': True}],
        'availability': [{'day_of_week': 'Saturday', 'start_time': '18:00:00', 'end_time': '20:00:00'}]
    }, headers={'Authorization': f'Bearer {tok_amit}'})

    # 3. Register Candidate 2: Sneha (Partial Match: Cricket + Koramangala + Sunday)
    print("--- 3. Setting up Sneha (Partial Candidate) ---")
    requests.post(f'{BASE}/auth/register', json={'email': 'sneha.sports@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_sneha = requests.post(f'{BASE}/auth/login', json={'email': 'sneha.sports@vynk.com', 'password': 'password123'}).json()['access_token']
    requests.post(f'{BASE}/profile/me/onboarding', json={
        'display_name': 'Sneha Rao',
        'bio': 'Casual cricket enthusiast and runner',
        'approx_locality': 'Koramangala, Bengaluru',
        'budget_preference': 'low',
        'interest_ids': [2, 7],
        'skills': [],
        'availability': [{'day_of_week': 'Sunday', 'start_time': '07:00:00', 'end_time': '09:00:00'}]
    }, headers={'Authorization': f'Bearer {tok_sneha}'})

    # 4. Register Candidate 3: Dev (Different Domain: AI/ML + Whitefield + Wednesday)
    print("--- 4. Setting up Dev (Tech Candidate) ---")
    requests.post(f'{BASE}/auth/register', json={'email': 'dev.techie@vynk.com', 'password': 'password123', 'confirm_password': 'password123'})
    tok_dev = requests.post(f'{BASE}/auth/login', json={'email': 'dev.techie@vynk.com', 'password': 'password123'}).json()['access_token']
    requests.post(f'{BASE}/profile/me/onboarding', json={
        'display_name': 'Dev Patel',
        'bio': 'Building AI agents and web apps',
        'approx_locality': 'Whitefield, Bengaluru',
        'budget_preference': 'free',
        'interest_ids': [17, 18],
        'skills': [{'skill_id': 5, 'skill_level': 'Advanced', 'is_offering': True}],
        'availability': [{'day_of_week': 'Wednesday', 'start_time': '19:00:00', 'end_time': '21:00:00'}]
    }, headers={'Authorization': f'Bearer {tok_dev}'})

    # 5. Query Deterministic Matches for Cricket (interest_id=2)
    print("\n==========================================")
    print("=== EXECUTING DETERMINISTIC MATCH QUERY ===")
    print("==========================================")
    res = requests.get(f'{BASE}/matches?interest_id=2', headers=h_rahul).json()
    print(f"Target Interest: {res.get('target_interest')}")
    print(f"Total Matches Found: {res.get('total_candidates')}\n")

    for i, m in enumerate(res.get('matches', []), 1):
        print(f"Rank #{i}: {m['display_name']} — Score: {m['match_score']}/100")
        print(f"  Locality: {m['approx_locality']}")
        print(f"  Breakdown: {m['match_breakdown']}")
        print(f"  Reasons: {m['match_reasons']}")
        print(f"  Shared Interests: {m['shared_interests']}")
        print(f"  Skills: {m['relevant_skills']}")
        print(f"  Availability: {m['shared_availability']}")
        print("-" * 50)

if __name__ == '__main__':
    test_people_matching()
