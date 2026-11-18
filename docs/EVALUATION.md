# Evaluation notes

## Supplied regression tests

`test_guardrails_v2.py` contains **18 hand-authored examples**: 13 input cases and 5 output cases. These cover ALLOW, BLOCK and HUMAN_REVIEW decisions. The suite checks whether the observed classification matches the expected decision.

**Interpretation:** Passing this suite means only that the specified rules classify these particular examples as expected. It does not establish real-world precision/recall, robustness, or safe model outputs.

## Additional unit tests

`tests/test_review_workflow.py` tests isolated JSON queue handling and reviewer status updates. `tests/test_edge_cases.py` tests selected invalid, oversized and secret-containing inputs/outputs.

## Recommended next evaluation

1. Build a balanced dataset of independently written benign, ambiguous and malicious prompts.
2. Report confusion matrices and per-class precision/recall for ALLOW/BLOCK/HUMAN_REVIEW.
3. Test paraphrases, Unicode variants, obfuscation, false positives, and adversarial prompt injection.
4. Test the end-to-end TinyLlama path separately with a pinned GGUF model version.
5. Record failure examples and mitigations rather than claiming full protection.

Do not use genuine customer records or secrets in the evaluation set.
