"""
Vynk (Localy) - Database Migration for Group Proposals (Tables 21 & 22)
Creates:
- group_proposals
- group_proposal_members
"""

import sys
from sqlalchemy import text
from database import engine, Base
import models


def run_migration():
    print("Migrating Group Proposals schema in PostgreSQL...")
    with engine.connect() as conn:
        # Create group_proposals table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS group_proposals (
                proposal_id SERIAL PRIMARY KEY,
                initiator_user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                activity_id INTEGER REFERENCES activities(activity_id) ON DELETE SET NULL,
                title VARCHAR(150) NOT NULL,
                description TEXT,
                target_size INTEGER NOT NULL DEFAULT 4,
                min_required_size INTEGER NOT NULL DEFAULT 2,
                proposed_date DATE,
                proposed_start_time TIME,
                proposed_end_time TIME,
                target_locality VARCHAR(120),
                suggested_venue_id INTEGER REFERENCES venues(venue_id) ON DELETE SET NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'PROPOSED',
                converted_event_id INTEGER REFERENCES events(event_id) ON DELETE SET NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT chk_proposal_min_size CHECK (min_required_size >= 2),
                CONSTRAINT chk_proposal_target_gte_min CHECK (target_size >= min_required_size)
            );
            """
            )
        )

        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_group_proposals_initiator ON group_proposals(initiator_user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_group_proposals_status ON group_proposals(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_group_proposals_date ON group_proposals(proposed_date);"))

        # Create group_proposal_members table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS group_proposal_members (
                proposal_id INTEGER NOT NULL REFERENCES group_proposals(proposal_id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                status VARCHAR(20) NOT NULL DEFAULT 'INVITED',
                compatibility_score INTEGER,
                invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                responded_at TIMESTAMP WITH TIME ZONE,
                PRIMARY KEY (proposal_id, user_id)
            );
            """
            )
        )

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_group_proposal_members_user ON group_proposal_members(user_id);"))
        conn.commit()

    print("Successfully created 'group_proposals' and 'group_proposal_members' tables.")


if __name__ == "__main__":
    run_migration()
