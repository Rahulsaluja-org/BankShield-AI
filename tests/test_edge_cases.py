import unittest
from guardrails.input_guardrail import check_input
from guardrails.output_guardrail import check_output

class GuardrailEdgeCases(unittest.TestCase):
    def test_empty_input_blocked(self):
        self.assertEqual(check_input('')['decision'], 'BLOCK')

    def test_non_string_input_blocked(self):
        self.assertEqual(check_input(None)['decision'], 'BLOCK')

    def test_long_input_reviewed(self):
        self.assertEqual(check_input('x' * 4001)['decision'], 'HUMAN_REVIEW')

    def test_empty_output_blocked(self):
        self.assertEqual(check_output('')['decision'], 'BLOCK')

    def test_long_output_reviewed(self):
        self.assertEqual(check_output('x' * 10001)['decision'], 'HUMAN_REVIEW')

    def test_api_secret_blocked(self):
        self.assertEqual(check_output('API key: abcdefghijklmnop123456')['decision'], 'BLOCK')

if __name__ == '__main__':
    unittest.main()
