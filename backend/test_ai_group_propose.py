"""
Vynk (Localy) - AI Group Proposal Endpoint Test Suite
Validates:
1. POST /ai/groups/propose with natural language sentence.
2. AI Intent extraction + Hybrid Matching candidate selection.
3. Creation of GroupProposal and GroupProposalMember records.
4. Accurate member statuses: Initiator is ACCEPTED (100), Candidates are INVITED.
5. Cohort size constraints and duplicate active proposal handling.
"""

from datetime import date, datetime
import unittest
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from embedding_service import backfill_all_embeddings
import models

client = TestClient(app)


class TestAIGroupPropose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = SessionLocal()
        try:
            backfill_all_embeddings(db)
        finally:
            db.close()

    def test_01_propose_ai_group_flow(self):
        """Test full natural language group proposal flow with 4 players on Saturday evening."""
        # 1. Setup Initiator (Pooja)
        initiator_email = "pooja.groupinitiator@vynk.com"
        client.post("/auth/register", json={"email": initiator_email, "password": "password123", "confirm_password": "password123"})
        tok_resp = client.post("/auth/login", json={"email": initiator_email, "password": "password123"})
        self.assertEqual(tok_resp.status_code, 200)
        token = tok_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        client.post("/profile/me/onboarding", json={
            "display_name": "Pooja Hegde",
            "bio": "Passionate badminton player looking for a 4-person doubles squad this weekend.",
            "approx_locality": "Indiranagar, Bengaluru",
            "budget_preference": "flexible",
            "interest_ids": [1], # Badminton
            "skills": [{"skill_id": 14, "skill_level": "Intermediate", "is_offering": True}],
            "availability": [{"day_of_week": "Saturday", "start_time": "18:00:00", "end_time": "21:00:00"}],
        }, headers=headers)

        # 2. Call POST /ai/groups/propose with natural language query
        query_text = "I want to play badminton with 4 people this Saturday evening near me."
        print(f"\n=======================================================")
        print(f"Executing POST /ai/groups/propose: '{query_text}'")
        print(f"=======================================================")

        resp = client.post("/ai/groups/propose", json={"query": query_text}, headers=headers)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()

        print(f"\n[GROUP PROPOSAL CREATED]")
        print(f"  Proposal ID:       #{data['proposal_id']}")
        print(f"  Title:             {data['title']}")
        print(f"  Status:            {data['status']}")
        print(f"  Target Size:       {data['target_size']} members (Min Required: {data['min_required_size']})")
        print(f"  Proposed Date:     {data['proposed_date']} ({data['proposed_start_time']} - {data['proposed_end_time']})")
        print(f"  Locality:          {data['target_locality']}")
        print(f"  Suggested Venue:   {data['suggested_venue_name']}")
        print(f"  Expires At:        {data['expires_at']}")

        # Validate proposal fields
        self.assertIsNotNone(data["proposal_id"])
        self.assertEqual(data["status"], "PROPOSED")
        self.assertEqual(data["target_size"], 4)
        self.assertGreaterEqual(data["min_required_size"], 2)
        self.assertIsNotNone(data["proposed_date"])
        self.assertEqual(data["proposed_start_time"], "18:00:00")

        # Validate member roster
        members = data["members"]
        print(f"\n[MEMBERS ROSTER ({len(members)} Total)]")
        for idx, m in enumerate(members, start=1):
            print(f"  {idx}. {m['display_name']} — Status: {m['status']} | Match Score: {m['compatibility_score']}/100 | Locality: {m['approx_locality']}")

        self.assertEqual(len(members), 4)

        # Check initiator is first and ACCEPTED
        initiator_member = members[0]
        self.assertEqual(initiator_member["status"], "ACCEPTED")
        self.assertEqual(initiator_member["compatibility_score"], 100)
        self.assertIn("Pooja", initiator_member["display_name"])

        # Check candidate members are INVITED
        for cand_m in members[1:]:
            self.assertEqual(cand_m["status"], "INVITED")
            self.assertIsNotNone(cand_m["compatibility_score"])
            self.assertGreater(cand_m["compatibility_score"], 0)

        # 3. Test duplicate active proposal safety
        print("\n--- Testing duplicate active proposal handling ---")
        dup_resp = client.post("/ai/groups/propose", json={"query": query_text}, headers=headers)
        self.assertEqual(dup_resp.status_code, 201)
        dup_data = dup_resp.json()
        self.assertEqual(dup_data["proposal_id"], data["proposal_id"])
        print(f"  Duplicate request safely returned existing active Proposal #{dup_data['proposal_id']}.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
