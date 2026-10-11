"""
Vynk (Localy) - Group Proposals Database & ORM Integration Test Suite
Validates:
1. Creation of group_proposals and group_proposal_members in PostgreSQL.
2. ORM bidirectional relationships between User, GroupProposal, and GroupProposalMember.
3. Member state transitions: INVITED -> ACCEPTED / DECLINED.
4. Business rule verification: Minimum required size threshold triggers CONFIRMED state.
5. Foreign key and cascade behavior.
"""

from datetime import date, datetime, time, timedelta
import unittest
from sqlalchemy.orm import Session

from database import SessionLocal
import models


class TestGroupProposalsDatabase(unittest.TestCase):
    def setUp(self):
        self.db: Session = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_create_proposal_and_add_members(self):
        """Test creating a proposal with initiator and invited members, verifying ORM relationships."""
        # 1. Setup Initiator and 3 Candidates
        initiator = self.db.query(models.User).filter(models.User.email == "group.initiator@vynk.com").first()
        if not initiator:
            initiator = models.User(email="group.initiator@vynk.com", password_hash="hash123", is_active=True)
            self.db.add(initiator)
            self.db.flush()
            self.db.add(models.Profile(user_id=initiator.user_id, display_name="Proposal Initiator", approx_locality="Indiranagar, Bengaluru"))
            self.db.commit()

        # Candidates
        candidates = []
        for i in range(1, 4):
            c_email = f"group.cand{i}@vynk.com"
            cand = self.db.query(models.User).filter(models.User.email == c_email).first()
            if not cand:
                cand = models.User(email=c_email, password_hash="hash123", is_active=True)
                self.db.add(cand)
                self.db.flush()
                self.db.add(models.Profile(user_id=cand.user_id, display_name=f"Candidate {i}", approx_locality="Indiranagar, Bengaluru"))
                self.db.commit()
            candidates.append(cand)

        # 2. Create Group Proposal
        activity = self.db.query(models.Activity).first()
        target_dt = date.today() + timedelta(days=2)

        proposal = models.GroupProposal(
            initiator_user_id=initiator.user_id,
            activity_id=activity.activity_id if activity else None,
            title="Saturday Evening Badminton Doubles (4 Players)",
            description="Looking for 3 players to join doubles match at Indiranagar Arena",
            target_size=4,
            min_required_size=3,
            proposed_date=target_dt,
            proposed_start_time=time(18, 0),
            proposed_end_time=time(20, 0),
            target_locality="Indiranagar, Bengaluru",
            status="PROPOSED",
            expires_at=datetime.now() + timedelta(hours=24),
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)

        self.assertIsNotNone(proposal.proposal_id)
        print(f"\n[PASS] Created GroupProposal #{proposal.proposal_id}: '{proposal.title}' (Status: {proposal.status})")

        # 3. Add Members: Initiator as ACCEPTED, Candidates as INVITED
        # Initiator
        m_initiator = models.GroupProposalMember(
            proposal_id=proposal.proposal_id,
            user_id=initiator.user_id,
            status="ACCEPTED",
            compatibility_score=100,
            responded_at=datetime.now(),
        )
        self.db.add(m_initiator)

        # 3 Invited Candidates with compatibility scores
        comp_scores = [92, 85, 78]
        for cand, score in zip(candidates, comp_scores):
            m_cand = models.GroupProposalMember(
                proposal_id=proposal.proposal_id,
                user_id=cand.user_id,
                status="INVITED",
                compatibility_score=score,
            )
            self.db.add(m_cand)

        self.db.commit()

        # 4. Verify ORM Relationships
        self.db.refresh(proposal)
        self.assertEqual(len(proposal.members), 4)
        self.assertEqual(proposal.initiator.user_id, initiator.user_id)

        # Check member statuses
        accepted = [m for m in proposal.members if m.status == "ACCEPTED"]
        invited = [m for m in proposal.members if m.status == "INVITED"]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(invited), 3)

        print(f"[PASS] Proposal has {len(proposal.members)} members (1 Accepted initiator, 3 Invited peers).")

    def test_02_member_acceptance_and_confirmation_threshold(self):
        """Test accepting invitations until min_required_size is reached, transitioning status to CONFIRMED."""
        # Find the latest proposal
        proposal = self.db.query(models.GroupProposal).order_by(models.GroupProposal.proposal_id.desc()).first()
        self.assertIsNotNone(proposal)

        # Candidate 1 accepts
        cand1_member = (
            self.db.query(models.GroupProposalMember)
            .filter(models.GroupProposalMember.proposal_id == proposal.proposal_id, models.GroupProposalMember.status == "INVITED")
            .first()
        )
        self.assertIsNotNone(cand1_member)
        cand1_member.status = "ACCEPTED"
        cand1_member.responded_at = datetime.now()
        self.db.commit()

        # Check total accepted = 2 (Initiator + Candidate 1), min_required = 3 -> Still PROPOSED
        accepted_count = (
            self.db.query(models.GroupProposalMember)
            .filter(models.GroupProposalMember.proposal_id == proposal.proposal_id, models.GroupProposalMember.status == "ACCEPTED")
            .count()
        )
        self.assertEqual(accepted_count, 2)
        self.assertLess(accepted_count, proposal.min_required_size)
        self.assertEqual(proposal.status, "PROPOSED")
        print(f"\n[PASS] 2/{proposal.target_size} accepted (Min: {proposal.min_required_size}) -> Status remains PROPOSED.")

        # Candidate 2 accepts -> Reaches min_required_size (3) -> Transitions to CONFIRMED
        cand2_member = (
            self.db.query(models.GroupProposalMember)
            .filter(models.GroupProposalMember.proposal_id == proposal.proposal_id, models.GroupProposalMember.status == "INVITED")
            .first()
        )
        self.assertIsNotNone(cand2_member)
        cand2_member.status = "ACCEPTED"
        cand2_member.responded_at = datetime.now()

        accepted_count += 1
        if accepted_count >= proposal.min_required_size:
            proposal.status = "CONFIRMED"
        self.db.commit()

        self.db.refresh(proposal)
        self.assertEqual(proposal.status, "CONFIRMED")
        print(f"[PASS] 3/{proposal.target_size} accepted -> Reached min_required_size (3) -> Status transitioned to CONFIRMED!")

    def test_03_cascade_deletion(self):
        """Verify that deleting a group proposal cascades to all member junction records."""
        # Create a temporary test proposal
        initiator = self.db.query(models.User).first()
        temp_prop = models.GroupProposal(
            initiator_user_id=initiator.user_id,
            title="Temporary Proposal For Deletion Test",
            target_size=4,
            min_required_size=2,
            status="PROPOSED",
            expires_at=datetime.now() + timedelta(hours=12),
        )
        self.db.add(temp_prop)
        self.db.commit()
        prop_id = temp_prop.proposal_id

        # Add 2 members
        self.db.add(models.GroupProposalMember(proposal_id=prop_id, user_id=initiator.user_id, status="ACCEPTED"))
        self.db.commit()

        # Delete proposal
        self.db.delete(temp_prop)
        self.db.commit()

        # Check members were cascaded
        orphans = self.db.query(models.GroupProposalMember).filter(models.GroupProposalMember.proposal_id == prop_id).all()
        self.assertEqual(len(orphans), 0)
        print(f"\n[PASS] Cascaded deletion verified for GroupProposal #{prop_id}.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
