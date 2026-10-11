"""
Vynk (Localy) - Group Proposal Acceptance & State Machine Test Suite
Validates:
1. Initiator creates Group Proposal (Target=4, Min=3).
2. Invited member accepts -> Recalculates accepted count.
3. Second member accepts -> Threshold (3/4) met -> Automatically transitions PROPOSED -> CONFIRMED.
4. Third member declines -> Member status updated to DECLINED.
5. Unauthorized response attempts return 403 Forbidden.
6. Duplicate response attempts return 400 Bad Request.
7. Verification of GET /groups/proposals/{id} and GET /groups/proposals/me.
"""

from datetime import datetime, timedelta
import unittest
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from embedding_service import backfill_all_embeddings
import models

client = TestClient(app)


class TestGroupProposalResponse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = SessionLocal()
        try:
            backfill_all_embeddings(db)
        finally:
            db.close()

    def _get_auth_header(self, email: str, name: str, locality: str = "Indiranagar, Bengaluru"):
        client.post("/auth/register", json={"email": email, "password": "password123", "confirm_password": "password123"})
        tok = client.post("/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {tok}"}
        client.post("/profile/me/onboarding", json={
            "display_name": name,
            "bio": f"{name} profile bio for testing group response.",
            "approx_locality": locality,
            "budget_preference": "flexible",
            "interest_ids": [1],
            "skills": [{"skill_id": 14, "skill_level": "Intermediate", "is_offering": True}],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "21:00:00"}],
        }, headers=headers)
        return headers

    def test_01_proposal_acceptance_and_confirmation_lifecycle(self):
        """Test full acceptance lifecycle from PROPOSED to CONFIRMED and member responses."""
        # Clean up prior proposals for test user
        db = SessionLocal()
        try:
            u = db.query(models.User).filter(models.User.email == "ananya.host@vynk.com").first()
            if u:
                db.query(models.GroupProposal).filter(models.GroupProposal.initiator_user_id == u.user_id).delete()
                db.commit()
        finally:
            db.close()

        # 1. Setup Initiator (Ananya)
        h_initiator = self._get_auth_header("ananya.host@vynk.com", "Ananya Host")

        # 2. Setup Candidates
        h_cand1 = self._get_auth_header("rohit.player1@vynk.com", "Rohit Player 1")
        h_cand2 = self._get_auth_header("vikram.player2@vynk.com", "Vikram Player 2")
        h_cand3 = self._get_auth_header("deepa.player3@vynk.com", "Deepa Player 3")
        h_outsider = self._get_auth_header("outsider.user@vynk.com", "Outsider User", locality="Whitefield, Bengaluru")

        # 3. Create Group Proposal
        prop_resp = client.post(
            "/ai/groups/propose",
            json={"query": "I want to play badminton with 4 people this Saturday evening in Indiranagar", "target_size": 4, "min_required_size": 3},
            headers=h_initiator,
        )
        self.assertEqual(prop_resp.status_code, 201)
        prop_data = prop_resp.json()
        prop_id = prop_data["proposal_id"]

        print(f"\n=======================================================")
        print(f"Created Group Proposal #{prop_id}: '{prop_data['title']}'")
        print(f"Initial Status: {prop_data['status']} | Target: {prop_data['target_size']} (Min: {prop_data['min_required_size']})")
        print(f"=======================================================")

        self.assertEqual(prop_data["status"], "PROPOSED")
        self.assertEqual(prop_data["min_required_size"], 3)

        # Get invited members
        from auth import create_access_token
        invited_members = [m for m in prop_data["members"] if m["status"] == "INVITED"]
        self.assertGreaterEqual(len(invited_members), 3)

        cand1 = invited_members[0]
        cand2 = invited_members[1]
        cand3 = invited_members[2]

        h_cand1 = {"Authorization": f"Bearer {create_access_token({'sub': str(cand1['user_id'])})}"}
        h_cand2 = {"Authorization": f"Bearer {create_access_token({'sub': str(cand2['user_id'])})}"}
        h_cand3 = {"Authorization": f"Bearer {create_access_token({'sub': str(cand3['user_id'])})}"}

        # 4. Outsider attempts to respond -> Should fail with 403 Forbidden
        print("\n--- 1. Testing unauthorized response by non-member ---")
        unauth_resp = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "ACCEPTED"}, headers=h_outsider)
        self.assertEqual(unauth_resp.status_code, 403)
        print(f"  Outsider blocked successfully: {unauth_resp.status_code} - {unauth_resp.json()['detail']}")

        # 5. Candidate 1 accepts -> Status remains PROPOSED (2/4 accepted, Min is 3)
        print(f"\n--- 2. Candidate 1 ({cand1['display_name']}) responds: ACCEPTED ---")
        c1_resp = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "ACCEPTED"}, headers=h_cand1)
        self.assertEqual(c1_resp.status_code, 200)
        c1_data = c1_resp.json()
        print(f"  Proposal Status: {c1_data['status']}")
        accepted_members = [m for m in c1_data["members"] if m["status"] == "ACCEPTED"]
        print(f"  Accepted Members Count: {len(accepted_members)}/4 (Min Required: {c1_data['min_required_size']})")
        self.assertEqual(len(accepted_members), 2)
        self.assertEqual(c1_data["status"], "PROPOSED")

        # 6. Candidate 1 attempts duplicate response -> Should fail with 400 Bad Request
        print(f"\n--- 3. Candidate 1 ({cand1['display_name']}) attempts duplicate response ---")
        dup_resp = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "ACCEPTED"}, headers=h_cand1)
        self.assertEqual(dup_resp.status_code, 400)
        print(f"  Duplicate response blocked: {dup_resp.status_code} - {dup_resp.json()['detail']}")

        # 7. Candidate 2 accepts -> Reaches threshold (3/4 accepted, Min is 3) -> Status becomes CONFIRMED
        print(f"\n--- 4. Candidate 2 ({cand2['display_name']}) responds: ACCEPTED (Threshold Hit) ---")
        c2_resp = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "ACCEPTED"}, headers=h_cand2)
        self.assertEqual(c2_resp.status_code, 200)
        c2_data = c2_resp.json()
        print(f"  Proposal Status: {c2_data['status']}")
        accepted_members = [m for m in c2_data["members"] if m["status"] == "ACCEPTED"]
        print(f"  Accepted Members Count: {len(accepted_members)}/4 (Min Required: {c2_data['min_required_size']})")
        self.assertEqual(len(accepted_members), 3)
        self.assertEqual(c2_data["status"], "CONFIRMED")
        print(f"  SUCCESS: Minimum threshold reached -> State transitioned to CONFIRMED!")

        # 8. Candidate 3 responds: DECLINED
        print(f"\n--- 5. Candidate 3 ({cand3['display_name']}) responds: DECLINED ---")
        c3_resp = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "DECLINED"}, headers=h_cand3)
        self.assertEqual(c3_resp.status_code, 200)
        c3_data = c3_resp.json()
        c3_member = [m for m in c3_data["members"] if m["user_id"] == cand3["user_id"]][0]
        self.assertEqual(c3_member["status"], "DECLINED")
        self.assertEqual(c3_data["status"], "CONFIRMED")
        print(f"  Candidate 3 recorded as DECLINED. Proposal remains CONFIRMED.")

        # 9. Verify GET /groups/proposals/{id}
        print("\n--- 6. Verify GET /groups/proposals/{id} ---")
        get_resp = client.get(f"/groups/proposals/{prop_id}", headers=h_initiator)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["status"], "CONFIRMED")
        print(f"  GET /groups/proposals/{prop_id} returned confirmed proposal with {len(get_resp.json()['members'])} members.")

        # 10. Verify GET /groups/proposals/me
        print("\n--- 7. Verify GET /groups/proposals/me ---")
        my_props = client.get("/groups/proposals/me", headers=h_cand1).json()
        self.assertGreaterEqual(len(my_props), 1)
        self.assertEqual(my_props[0]["proposal_id"], prop_id)
        print(f"  Candidate 1 sees {len(my_props)} proposal(s) in their active dashboard list.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
