# NovaMart Guardian

A competition-grade, policy-grounded AI customer-support agent built for the Mantra Yudha "AI Customer Support Agent from Hell" challenge.

## Core idea

**LLM proposes -> backend verifies -> policy engine decides -> guarded tools act -> postconditions verify -> response composer speaks.**

The application is intentionally usable without any external AI API key. A deterministic intent parser and decision engine provide the complete submitted evaluation path. An optional Google Gemini adapter (free tier via Google AI Studio) is included for fluent customer response enrichment, but it never becomes the authority for policy, identity, financial calculations, or writes.

## Features

- Four explicit terminal decisions: `ANSWER`, `ASK`, `ACT`, `ESCALATE`.
- Customer/order ownership verification.
- Version-aware policy compiler from the supplied Markdown policy files.
- Calendar-day window arithmetic.
- v1/v2 refund thresholds and rules.
- Loyalty extensions.
- v2 restocking fee for laptops/tablets/cameras/monitors.
- Delivery and OTP contradiction handling.
- Suspicious refund and repeated-claim risk signals.
- Conversation memory retrieval and open-ticket context.
- Multi-intent decomposition with dependency-aware execution.
- Prompt-injection defense with customer text treated as untrusted data.
- Proof-carrying actions / action contracts.
- Post-action verification and idempotency.
- Mutation mode for policy-change demonstrations.
- Local adversarial, boundary and metamorphic test harness.
- Handbook-inspired dark red / black / cream interface.

## Repository layout

```text
novamart-guardian/
├── app/
│   ├── agent/                 # orchestration, intents, decisions, responses
│   ├── memory/                # conversation/ticket context
│   ├── policy/                # Markdown policy compiler + policy logic
│   ├── retrieval/             # product/review retrieval
│   ├── security/              # injection/safety/legal detectors
│   ├── tools/                 # verified data + guarded write actions
│   ├── config.py
│   ├── data_store.py
│   ├── llm.py
│   ├── main.py
│   └── models.py
├── data/                      # supplied public dataset + compiled artifacts
├── frontend/                  # handbook-inspired UI
├── docs/                      # architecture, prompts, tool contracts, failure modes
├── prompts/                   # full system prompt + decision schema
├── tests/                     # unit, adversarial, boundary, mutation
├── scripts/                   # evals and dataset/policy utilities
├── runtime/                   # generated action state (safe to reset)
├── reference/                 # supplied handbook + public source archive
├── Dockerfile
├── start.sh
├── FINAL_VALIDATION.md        # delivered-build validation record
├── REPORT.md
├── REPORT.docx
├── REPORT.pdf
├── requirements.txt
├── .env.example
├── .gitignore
├── .dockerignore
└── start_windows.bat
```

## Quick start - Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

For a PowerShell environment that blocks activation scripts, simply run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Quick start - Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Validation

```bash
python scripts/validate_dataset.py
pytest -q
python scripts/run_evals.py
```

Latest delivered-build result: dataset validation passed, **24 automated tests passed**, and the **10-case end-to-end smoke suite passed 10/10**. See `FINAL_VALIDATION.md` for the exact scope and limitations.

## Docker

```bash
docker build -t novamart-guardian .
docker run --rm -p 8000:8000 novamart-guardian
```

Open `http://127.0.0.1:8000`.

## Free Google Gemini API adapter

The system integrates with Google's free Gemini API (e.g. `gemini-1.5-flash` or `gemini-2.0-flash` via [Google AI Studio](https://aistudio.google.com/)).

Set these environment variables or paste your key directly in the web UI:

```powershell
$env:GEMINI_API_KEY="your-free-gemini-api-key"
$env:GEMINI_MODEL="gemini-1.5-flash"
```

Or add to `.env`:

```text
GEMINI_API_KEY=your-free-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash
```

The Gemini adapter is non-authoritative: it enriches customer-facing response phrasing and fluency, while verified database state, compiled policy and action guards remain the absolute safety authority.

## Submission checklist

See `docs/SUBMISSION_CHECKLIST.md` for the handbook-aligned deliverables and final GitHub/demo steps.

## Demo flow

1. Select a customer in the left panel.
2. Choose a prebuilt adversarial case or type your own message.
3. Run the agent.
4. Inspect the four-move decision, evidence, policy version, intent graph and execution trace.
5. Use the Mutation panel to change a policy value without changing code, then rerun a window test.

## Data integrity

The supplied public dataset remains under `data/public` and is not modified by the agent. Writes go to `runtime/state.json`, allowing repeatable demos and a clean reset.

## Competition positioning

The project is designed around the handbook's main constraints: verification-first reasoning, explicit terminal actions, versioned policy application, conversation continuity, adversarial input handling, multi-intent processing, and end-to-end result verification.
