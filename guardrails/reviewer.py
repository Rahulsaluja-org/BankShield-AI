import json
from pathlib import Path

REVIEW_FILE = Path(__file__).resolve().parent.parent / "review_queue.json"


def load_cases():
    if not REVIEW_FILE.exists():
        return []

    try:
        return json.loads(REVIEW_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("Could not read the review queue.")
        return []


def save_cases(cases):
    REVIEW_FILE.write_text(
        json.dumps(cases, indent=2),
        encoding="utf-8",
    )


def review_cases():
    cases = load_cases()
    pending = [case for case in cases if case["status"] == "PENDING"]

    if not pending:
        print("No pending review cases.")
        return

    for case in pending:
        print("\n" + "-" * 45)
        print("Case ID:", case["case_id"])
        print("Created:", case["created_at"])
        print("Prompt:", case["prompt"])
        print("Reason:", case["reason"])
        print("Status:", case["status"])

        decision = input("Decision (approve/reject/skip): ").strip().lower()

        if decision == "skip":
            continue

        if decision not in ("approve", "reject"):
            print("Invalid decision. Case remains pending.")
            continue

        case["status"] = "REVIEWED"
        case["reviewer_decision"] = decision.upper()

        print("Case updated:", case["case_id"])
        print("Reviewer decision:", decision.upper())

    save_cases(cases)


if __name__ == "__main__":
    review_cases()
