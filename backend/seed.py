from sqlalchemy.orm import Session
import models

DEFAULT_INTERESTS = [
    # Sports
    {"name": "Badminton", "category": "Sports"},
    {"name": "Cricket", "category": "Sports"},
    {"name": "Football", "category": "Sports"},
    {"name": "Tennis", "category": "Sports"},
    {"name": "Swimming", "category": "Sports"},
    {"name": "Cycling", "category": "Sports"},
    {"name": "Running & Marathon", "category": "Sports"},
    {"name": "Volleyball", "category": "Sports"},
    {"name": "Basketball", "category": "Sports"},
    {"name": "Table Tennis", "category": "Sports"},
    # Music
    {"name": "Acoustic Guitar", "category": "Music"},
    {"name": "Vocals & Singing", "category": "Music"},
    {"name": "Keyboard & Piano", "category": "Music"},
    {"name": "Drums & Percussion", "category": "Music"},
    {"name": "Jamming Sessions", "category": "Music"},
    {"name": "Music Production", "category": "Music"},
    # Technology
    {"name": "Python & AI / ML", "category": "Technology"},
    {"name": "Web Development", "category": "Technology"},
    {"name": "Mobile App Development", "category": "Technology"},
    {"name": "Cloud & DevOps", "category": "Technology"},
    {"name": "UI / UX Design", "category": "Technology"},
    {"name": "Open Source Contribution", "category": "Technology"},
    # Creative & Arts
    {"name": "Street & Travel Photography", "category": "Creative"},
    {"name": "Digital & Canvas Painting", "category": "Creative"},
    {"name": "Creative Writing & Poetry", "category": "Creative"},
    {"name": "Stand-up Comedy & Storytelling", "category": "Creative"},
    {"name": "Filmmaking & Video Editing", "category": "Creative"},
    # Learning & Social
    {"name": "Startup & Entrepreneurship", "category": "Learning"},
    {"name": "Book Club & Discussions", "category": "Learning"},
    {"name": "Career Mentorship", "category": "Learning"},
    {"name": "Board Games & Chess", "category": "Social"},
    {"name": "Coffee & Casual Meetups", "category": "Social"},
]

DEFAULT_SKILLS = [
    # Music
    {"name": "Guitar Playing", "category": "Music"},
    {"name": "Vocal Singing", "category": "Music"},
    {"name": "Piano & Keyboard", "category": "Music"},
    {"name": "Drums Playing", "category": "Music"},
    # Technology
    {"name": "Python Programming", "category": "Technology"},
    {"name": "React / Frontend Dev", "category": "Technology"},
    {"name": "Mobile Development (Flutter/React Native)", "category": "Technology"},
    {"name": "Machine Learning & Data Science", "category": "Technology"},
    {"name": "UI/UX & Figma", "category": "Technology"},
    # Creative
    {"name": "Photography & Lighting", "category": "Creative"},
    {"name": "Video Editing & Color Grading", "category": "Creative"},
    {"name": "Public Speaking & Hosting", "category": "Creative"},
    {"name": "Creative Writing", "category": "Creative"},
    # Sports & Fitness
    {"name": "Badminton Coaching", "category": "Sports"},
    {"name": "Football Training", "category": "Sports"},
    {"name": "Yoga & Mindfulness", "category": "Sports"},
    {"name": "Strength & Fitness Training", "category": "Sports"},
]


def seed_master_data(db: Session):
    """Populates master interests and skills if tables are empty."""
    # Seed interests if empty
    if db.query(models.Interest).count() == 0:
        for item in DEFAULT_INTERESTS:
            db.add(models.Interest(name=item["name"], category=item["category"]))
        db.commit()

    # Seed skills if empty
    if db.query(models.Skill).count() == 0:
        for item in DEFAULT_SKILLS:
            db.add(models.Skill(name=item["name"], category=item["category"]))
        db.commit()
