import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

REVIEW_FILE = Path(__file__).resolve().parent.parent / "review_queue.json"

def submit_for_review(prompt: str, reason: str) -> dict:
    """Record a flagged prompt for a human reviewer."""

    queue = []

    if REVIEW_FILE.exists():
        try:
            queue = json.loads(
                REVIEW_FILE.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            queue = []

    case = {
        "case_id": str(uuid4())[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "reason": reason,
        "status": "PENDING",
        "reviewer_decision": None,
    }

    queue.append(case)

    REVIEW_FILE.write_text(
        json.dumps(queue, indent=2),
        encoding="utf-8",
    )

    return case

if __name__ == "__main__":
    case = submit_for_review(
        "How can I hack a bank account?",
        "Security-related content requires review.",
    )

    print("Review case created:")
    print(json.dumps(case, indent=2))
    print(f"\nSaved to: {REVIEW_FILE}")
