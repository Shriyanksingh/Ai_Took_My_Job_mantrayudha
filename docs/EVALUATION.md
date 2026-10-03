# Evaluation Strategy

The local evaluator is designed around the handbook's published capability categories, while keeping hidden cases unknown.

## Test families

- policy version cutover
- approval thresholds
- calendar-day boundaries
- refund caps
- delivery/OTP contradictions
- suspicious/refund patterns
- ambiguity
- contradictory records
- warranty vs refund
- prompt injection
- multi-intent dependencies
- payment states
- safety escalation
- policy mutation

## Metamorphic tests

The same legitimate request is transformed by adding adversarial instructions. The legitimate outcome must remain unchanged.

Policy values are mutated at runtime and the agent must adapt without source-code edits.

## Local evidence

Run `pytest -q` for the deterministic unit/integration suite, `python scripts/validate_dataset.py` for source-data integrity, and `python scripts/run_evals.py` for the 10-case end-to-end smoke set.

The hidden organizer evaluation cannot be reproduced locally because the handbook says the hidden records and exact thresholds are not disclosed.


## Current local evidence

At packaging time, `pytest -q` reports 24 passed tests. The end-to-end evaluator reports 10/10 passed cases across verified delivery, prompt injection, cancellation, high-value escalation, safety, human hand-off, ambiguity, OTP contradiction, alternate refund destination, and product-ID lookup. These are local tests, not the organizer's hidden evaluation.
