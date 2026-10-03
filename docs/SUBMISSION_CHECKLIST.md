# Mantra Yudha Submission Checklist

The handbook asks for a working application, full source, a public GitHub repository, README/setup instructions, dependency file, architecture, model names/versions, prompt or agent strategy documentation, limitations/failure modes, and a 3-5 minute recorded demo.

## Included in this package

- Runnable FastAPI application + handbook-inspired single-page UI
- Full source code
- Supplied public dataset under `data/public`
- Supplied handbook and original public archive under `reference/`
- `README.md` with Windows/Linux/Docker setup
- `requirements.txt`
- `docs/architecture.svg` and `docs/architecture.png`
- `prompts/system.md` and `prompts/decision_schema.json`
- `docs/PROMPT_STRATEGY.md`
- `docs/TOOL_CONTRACTS.md`
- `docs/FAILURE_MODES.md`
- `docs/EVALUATION.md`
- `REPORT.md`, `REPORT.docx`, `REPORT.pdf`
- Automated tests and end-to-end smoke evaluator
- Mutation demo and reset endpoint
- `Dockerfile` and `.dockerignore`
- `FINAL_VALIDATION.md`

## Before publishing to GitHub

1. Add the final public repository URL to the README.
2. Run the full validation commands from `FINAL_VALIDATION.md`.
3. Record a 3-5 minute demo using the sequence in `docs/DEMO_SCRIPT.md`.
4. Confirm no local API keys or secrets are committed.
5. Include the final demo link in the repository README.
