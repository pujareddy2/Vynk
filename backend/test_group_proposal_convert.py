"""
Vynk (Localy) - Confirmed Group Proposal to Event Conversion Test Suite
Validates:
1. End-to-end proposal creation (Target=4, Min=3).
2. Acceptance by required members transitioning proposal to CONFIRMED.
3. POST /groups/proposals/{id}/convert by initiator creates scheduled Event in PostgreSQL.
4. Accepted cohort members automatically enrolled as CONFIRMED EventParticipants.
5. Proposal status transitions to CONVERTED_TO_EVENT with converted_event_id.
6. Guardrails: Second conversion blocked (400) and non-initiator conversion blocked (403).
"""

from datetime import date, datetime, time, timedelta
import unittest
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from auth import create_access_token
import models

client = TestClient(app)


class TestGroupProposalConvert(unittest.TestCase):
    def test_01_confirmed_group_to_event_conversion_flow(self):
        """Test full conversion journey from CONFIRMED proposal to scheduled Event."""
        # 1. Setup Initiator (Priyanka)
        email_init = "priyanka.conv@vynk.com"
        client.post("/auth/register", json={"email": email_init, "password": "password123", "confirm_password": "password123"})
        tok_init = client.post("/auth/login", json={"email": email_init, "password": "password123"}).json()["access_token"]
        h_init = {"Authorization": f"Bearer {tok_init}"}

        client.post("/profile/me/onboarding", json={
            "display_name": "Priyanka Captain",
            "bio": "Organizing weekend badminton doubles squad.",
            "approx_locality": "Indiranagar, Bengaluru",
            "budget_preference": "flexible",
            "interest_ids": [1],
            "skills": [{"skill_id": 14, "skill_level": "Intermediate", "is_offering": True}],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "21:00:00"}],
        }, headers=h_init)

        # 2. Setup Candidates
        cand_tokens = []
        for i in range(1, 4):
            c_email = f"conv.cand{i}@vynk.com"
            client.post("/auth/register", json={"email": c_email, "password": "password123", "confirm_password": "password123"})
            c_tok = client.post("/auth/login", json={"email": c_email, "password": "password123"}).json()["access_token"]
            c_h = {"Authorization": f"Bearer {c_tok}"}
            client.post("/profile/me/onboarding", json={
                "display_name": f"Squad Player {i}",
                "bio": f"Squad player {i} ready for doubles.",
                "approx_locality": "Indiranagar, Bengaluru",
                "budget_preference": "flexible",
                "interest_ids": [1],
                "skills": [{"skill_id": 14, "skill_level": "Intermediate", "is_offering": True}],
                "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "21:00:00"}],
            }, headers=c_h)
            cand_tokens.append(c_h)

        # 3. Create Group Proposal (Target=4, Min=3)
        prop_resp = client.post(
            "/ai/groups/propose",
            json={
                "query": "I want to play badminton with 4 people this Saturday evening in Indiranagar",
                "target_size": 4,
                "min_required_size": 3,
                "custom_title": "Saturday Indiranagar Badminton Doubles Championship",
            },
            headers=h_init,
        )
        self.assertEqual(prop_resp.status_code, 201)
        prop_data = prop_resp.json()
        prop_id = prop_data["proposal_id"]

        print(f"\n=======================================================")
        print(f"Step 1: Created Group Proposal #{prop_id}: '{prop_data['title']}'")
        print(f"Status: {prop_data['status']} | Target: {prop_data['target_size']} (Min Required: {prop_data['min_required_size']})")
        print(f"=======================================================")

        self.assertEqual(prop_data["status"], "PROPOSED")

        # 4. Attempt conversion before reaching minimum threshold -> Should fail (400)
        print("\n--- Step 2: Attempt conversion while status is still PROPOSED ---")
        early_conv_resp = client.post(f"/groups/proposals/{prop_id}/convert", headers=h_init)
        self.assertEqual(early_conv_resp.status_code, 400)
        print(f"  Early conversion blocked: {early_conv_resp.status_code} - {early_conv_resp.json()['detail']}")

        # 5. Members accept invitations until threshold (3/4 accepted) is met
        print("\n--- Step 3: Members Accept Invitations ---")
        invited_members = [m for m in prop_data["members"] if m["status"] == "INVITED"]
        self.assertGreaterEqual(len(invited_members), 2)

        # Candidate 1 accepts
        h_cand1 = {"Authorization": f"Bearer {create_access_token({'sub': str(invited_members[0]['user_id'])})}"}
        r1 = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "ACCEPTED"}, headers=h_cand1)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], "PROPOSED")
        print(f"  Member 1 ({invited_members[0]['display_name']}) accepted -> 2/4 accepted (Status: PROPOSED)")

        # Candidate 2 accepts -> Reaches min_required_size (3) -> CONFIRMED
        h_cand2 = {"Authorization": f"Bearer {create_access_token({'sub': str(invited_members[1]['user_id'])})}"}
        r2 = client.post(f"/groups/proposals/{prop_id}/respond", json={"response": "ACCEPTED"}, headers=h_cand2)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], "CONFIRMED")
        print(f"  Member 2 ({invited_members[1]['display_name']}) accepted -> 3/4 accepted (Status: CONFIRMED!)")

        # 6. Non-initiator attempts conversion -> Should fail (403 Forbidden)
        print("\n--- Step 4: Non-initiator attempts conversion ---")
        unauth_conv = client.post(f"/groups/proposals/{prop_id}/convert", headers=h_cand1)
        self.assertEqual(unauth_conv.status_code, 403)
        print(f"  Non-initiator conversion blocked: {unauth_conv.status_code} - {unauth_conv.json()['detail']}")

        # 7. Initiator converts confirmed proposal to official scheduled event
        print("\n--- Step 5: Initiator converts CONFIRMED Proposal to Event ---")
        conv_resp = client.post(f"/groups/proposals/{prop_id}/convert", headers=h_init)
        self.assertEqual(conv_resp.status_code, 201)
        event_data = conv_resp.json()
        event_id = event_data["event_id"]

        print(f"\n[EVENT CREATED FROM GROUP PROPOSAL]")
        print(f"  Event ID:           #{event_id}")
        print(f"  Title:              {event_data['title']}")
        print(f"  Host:               {event_data['host_name']} (User #{event_data['host_id']})")
        print(f"  Date & Time:        {event_data['event_date']} ({event_data['start_time']} - {event_data['end_time']})")
        print(f"  Capacity:           {event_data['participant_count']}/{event_data['max_capacity']} spots")
        print(f"  Status:             {event_data['status']}")
        print(f"  Enrolled Roster:    {[p['display_name'] for p in event_data['participants']]}")

        # Validate Event fields
        self.assertIsNotNone(event_id)
        self.assertEqual(event_data["title"], prop_data["title"])
        self.assertEqual(event_data["max_capacity"], 4)
        self.assertEqual(event_data["participant_count"], 3)
        self.assertEqual(len(event_data["participants"]), 3)

        # 8. Verify proposal status updated to CONVERTED_TO_EVENT
        print("\n--- Step 6: Verify Group Proposal Status Update ---")
        updated_prop = client.get(f"/groups/proposals/{prop_id}", headers=h_init).json()
        self.assertEqual(updated_prop["status"], "CONVERTED_TO_EVENT")
        self.assertEqual(updated_prop["converted_event_id"], event_id)
        print(f"  Proposal #{prop_id} status is now CONVERTED_TO_EVENT (converted_event_id: #{updated_prop['converted_event_id']})")

        # 9. Second conversion attempt -> Should fail (400 Bad Request)
        print("\n--- Step 7: Second Conversion Attempt Blocked ---")
        dup_conv = client.post(f"/groups/proposals/{prop_id}/convert", headers=h_init)
        self.assertEqual(dup_conv.status_code, 400)
        print(f"  Duplicate conversion blocked: {dup_conv.status_code} - {dup_conv.json()['detail']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
