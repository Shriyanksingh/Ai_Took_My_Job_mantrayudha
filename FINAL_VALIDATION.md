# Final Validation

This file records the validation performed on the delivered NovaMart Guardian build.

## Dataset validation

Command:

```bash
python scripts/validate_dataset.py
```

Expected result: all supplied public dataset counts match the handbook archive and all 300 product specification IDs are covered.

## Automated unit/integration tests

Command:

```bash
pytest -q
```

Latest validation: **24 passed**.

## End-to-end evaluation smoke suite

Command:

```bash
python scripts/run_evals.py
```

Latest validation: **10/10 passed (100% pass rate)** across verified delivery, prompt injection, cancellation, high-value refund, safety, explicit human request, ambiguous return, OTP contradiction, different refund destination and product-ID lookup.

## Syntax checks

- Python modules compile successfully with `python -m compileall -q app scripts tests`.
- Frontend JavaScript passes `node --check`.

## Mutation check

The API mutation endpoint changes compiled policy values through a runtime overlay and the mutation reset endpoint restores the baseline compiled policy. No source policy file is edited.

## Scope note

The organizer's hidden test cases and exact scoring thresholds are not included in the handbook. These results are therefore local validation evidence, not a claim about an organizer-assigned score.
