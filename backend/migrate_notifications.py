"""
Vynk (Localy) - Database Migration for Notifications (Table 23)
Creates:
- notifications table
- Indexes for recipient, type, status, and read flags
"""

import sys
from sqlalchemy import text
from database import engine, Base
import models


def run_migration():
    print("Migrating Notifications schema in PostgreSQL...")
    with engine.connect() as conn:
        # Create notifications table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id SERIAL PRIMARY KEY,
                recipient_user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                notification_type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                payload JSONB,
                source_action VARCHAR(50),
                related_community_id INTEGER REFERENCES communities(community_id) ON DELETE SET NULL,
                related_event_id INTEGER REFERENCES events(event_id) ON DELETE SET NULL,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                read_at TIMESTAMP WITH TIME ZONE,
                status VARCHAR(30) NOT NULL DEFAULT 'UNREAD',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            )
        )

        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_community ON notifications(related_community_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_event ON notifications(related_event_id);"))

        conn.commit()

    print("Checking live tables in PostgreSQL:")
    with engine.connect() as conn:
        res = conn.execute(
            text(
                """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'notifications';
            """
            )
        ).fetchall()
        print(f"Verified tables found: {res}")


if __name__ == "__main__":
    run_migration()
