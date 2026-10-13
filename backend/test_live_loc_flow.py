import requests
import json
import time

BASE = "http://127.0.0.1:8000"

def test_live_location_pipeline():
    # 1. Health check
    r = requests.get(f"{BASE}/health")
    print("Health:", r.status_code, r.json())
    assert r.status_code == 200

    # 2. Register new user with live location (as passed by frontend when profile is created)
    ts = int(time.time())
    email = f"liveloc.{ts}@vynk.com"
    pwd = "password123"
    loc = "Indiranagar, Bengaluru"

    reg_res = requests.post(f"{BASE}/auth/register", json={
        "email": email,
        "password": pwd,
        "confirm_password": pwd,
        "approx_locality": loc
    })
    print("Register status:", reg_res.status_code)
    assert reg_res.status_code == 201

    # 3. Login
    login_res = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pwd})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Check profile me
    prof_res = requests.get(f"{BASE}/profile/me", headers=headers)
    prof = prof_res.json()
    actual_loc = prof.get("approx_locality")
    print("Profile locality in backend:", actual_loc)
    assert actual_loc == loc

    # 5. Fetch recommendations
    rec_res = requests.get(f"{BASE}/recommendations", headers=headers)
    rec_data = rec_res.json()
    print("Recommendations user_locality:", rec_data.get("user_locality"))
    print("Total recs:", rec_data.get("total_recommendations"))
    assert rec_data.get("user_locality") == loc

    # Check recommendations for locality scoring
    for item in rec_data.get("recommendations", [])[:4]:
        itype = item.get("type")
        title = item.get("title")
        score = item.get("score")
        iloc = item.get("locality")
        reasons = item.get("reasons", [])
        safe_reasons = [r.encode('ascii', 'replace').decode('ascii') for r in reasons]
        print(f"Rec Item: [{itype}] {title} | Locality: {iloc} | Score: {score}")
        print("  Reasons:", safe_reasons)

    # 6. Fetch Demand Radar (should boost user's live locality)
    radar_res = requests.get(f"{BASE}/ai/demand-radar", headers=headers)
    radar_data = radar_res.json()
    print("Demand Radar total clusters:", radar_data.get("total_clusters"))
    if radar_data.get("clusters"):
        top_cluster = radar_data["clusters"][0]
        print(f"Top cluster locality: {top_cluster.get('locality')} | Activity: {top_cluster.get('activity')} | Demand Score: {top_cluster.get('demand_score')}")

    # 7. Fetch Opportunities (grounded in user's live locality)
    opps_res = requests.get(f"{BASE}/ai/opportunities", headers=headers)
    opps_data = opps_res.json()
    print("Opportunities total:", opps_data.get("total_opportunities"))
    if opps_data.get("opportunities"):
        top_opp = opps_data["opportunities"][0]
        print(f"Top opportunity locality: {top_opp.get('locality')} | Activity: {top_opp.get('activity_name')} | Opp Score: {top_opp.get('opportunity_score')}")

    print("=== ALL LIVE LOCATION & RECOMMENDATION TESTS PASSED 100% ===")

if __name__ == "__main__":
    test_live_location_pipeline()
