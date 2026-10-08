"""
Vynk (Localy) - AI Intent Understanding Test Suite
Tests natural language understanding with 10 diverse sentences.
Validates structured JSON output, extracted parameters, and schema compliance.
"""

import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

TEST_SENTENCES = [
    {
        "query": "I want to play badminton this Saturday evening with people near me.",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Badminton",
        "expected_day": "Saturday",
        "expected_time": "evening",
        "expected_location": "nearby",
    },
    {
        "query": "Looking for 4 people for casual box cricket tomorrow morning in Sarjapur Road.",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Cricket",
        "expected_day": "Tomorrow",
        "expected_time": "morning",
        "expected_location": "Sarjapur",
    },
    {
        "query": "Anyone up for an acoustic guitar jamming session on Sunday afternoon?",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Guitar",
        "expected_day": "Sunday",
        "expected_time": "afternoon",
    },
    {
        "query": "Need a beginner-friendly Python and AI study group this weekend.",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Python",
        "expected_day": "Weekend",
        "expected_skill": "beginner",
    },
    {
        "query": "Want to find an available badminton court in Indiranagar for Friday night.",
        "expected_intent": "find_venue",
        "expected_activity": "Badminton",
        "expected_day": "Friday",
        "expected_time": "night",
        "expected_location": "Indiranagar",
    },
    {
        "query": "Organize a 6v6 turf football match this Saturday evening.",
        "expected_intent": "create_event",
        "expected_activity": "Football",
        "expected_day": "Saturday",
        "expected_time": "evening",
    },
    {
        "query": "Looking for an advanced tennis partner nearby.",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Tennis",
        "expected_skill": "advanced",
        "expected_location": "nearby",
    },
    {
        "query": "Are there any book club meetups or storytelling circles happening today?",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Storytelling",
        "expected_day": "Today",
    },
    {
        "query": "Want to play chess casually in Koramangala this Sunday evening.",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Chess",
        "expected_day": "Sunday",
        "expected_time": "evening",
        "expected_location": "Koramangala",
    },
    {
        "query": "Need 2 players for table tennis doubles tomorrow afternoon near me.",
        "expected_intent": "find_activity_and_people",
        "expected_activity": "Table tennis",
        "expected_day": "Tomorrow",
        "expected_time": "afternoon",
        "expected_location": "nearby",
    }
]


def run_ai_intent_tests():
    print("=" * 70)
    print("VYNK AI INTENT UNDERSTANDING - TEST SUITE")
    print("=" * 70)

    passed_count = 0

    for idx, test_case in enumerate(TEST_SENTENCES, start=1):
        query = test_case["query"]
        print(f"\n[Test Case {idx}/10]")
        print(f"Sentence: \"{query}\"")

        resp = client.post("/ai/intent", json={"query": query})
        assert resp.status_code == 200, f"Failed with status {resp.status_code}: {resp.text}"

        data = resp.json()

        # Validate required structured fields exist
        assert "raw_query" in data
        assert "intent" in data
        assert "activity" in data
        assert "category" in data
        assert "day_of_week" in data
        assert "time_of_day" in data
        assert "location" in data
        assert "skill_level" in data
        assert "confidence" in data
        assert "engine" in data

        print(f"  --> Extracted Intent:    {data['intent']}")
        print(f"  --> Extracted Activity:  {data['activity']} ({data['category']})")
        print(f"  --> Day / Time:          {data['day_of_week']} / {data['time_of_day']}")
        print(f"  --> Location / Skill:    {data['location']} / {data['skill_level']}")
        print(f"  --> Group Size / Conf:   {data['group_size']} / {data['confidence']:.2f}")
        print(f"  --> Engine:              {data['engine']}")

        # Verify key extracted fields match expectation
        if "expected_activity" in test_case:
            assert data["activity"] is not None and test_case["expected_activity"].lower() in data["activity"].lower(), (
                f"Activity mismatch: got '{data['activity']}', expected '{test_case['expected_activity']}'"
            )

        if "expected_day" in test_case:
            assert data["day_of_week"] == test_case["expected_day"], (
                f"Day mismatch: got '{data['day_of_week']}', expected '{test_case['expected_day']}'"
            )

        if "expected_time" in test_case:
            assert data["time_of_day"] == test_case["expected_time"], (
                f"Time mismatch: got '{data['time_of_day']}', expected '{test_case['expected_time']}'"
            )

        if "expected_location" in test_case:
            assert data["location"] == test_case["expected_location"], (
                f"Location mismatch: got '{data['location']}', expected '{test_case['expected_location']}'"
            )

        passed_count += 1
        print("  [PASSED] Structured JSON validated successfully!")

    print("\n" + "=" * 70)
    print(f"ALL {passed_count}/{len(TEST_SENTENCES)} AI INTENT UNDERSTANDING TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_ai_intent_tests()
