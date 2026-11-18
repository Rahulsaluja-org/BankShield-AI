import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from guardrails import human_review, reviewer

class ReviewWorkflowTests(unittest.TestCase):
    def test_submission_and_reviewer_decision(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'queue.json'
            with patch.object(human_review, 'REVIEW_FILE', path), patch.object(reviewer, 'REVIEW_FILE', path):
                case = human_review.submit_for_review('synthetic test prompt', 'test reason')
                self.assertEqual(case['status'], 'PENDING')
                self.assertEqual(len(json.loads(path.read_text())), 1)
                with patch('builtins.input', return_value='approve'):
                    reviewer.review_cases()
                saved = json.loads(path.read_text())
                self.assertEqual(saved[0]['status'], 'REVIEWED')
                self.assertEqual(saved[0]['reviewer_decision'], 'APPROVE')

    def test_missing_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(reviewer, 'REVIEW_FILE', Path(folder) / 'missing.json'):
                self.assertEqual(reviewer.load_cases(), [])

if __name__ == '__main__':
    unittest.main()
