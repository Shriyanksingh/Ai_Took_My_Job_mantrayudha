# NovaMart Guardian - Handoff

## What is ready

The package is a self-contained runnable build using the supplied NovaMart public data and policy Markdown. The default path requires no external AI key.

## Run

Windows: use `start_windows.bat` or the commands in `README.md`.

Linux/macOS: use `start.sh` or the commands in `README.md`.

Docker: `docker build -t novamart-guardian .` then `docker run --rm -p 8000:8000 novamart-guardian`.

## Judge-facing URL

After launch, open `http://127.0.0.1:8000`.

## Core files to inspect first

1. `app/agent/orchestrator.py` - end-to-end decision loop.
2. `app/policy/compiler.py` and `app/policy/engine.py` - policy versioning and calculations.
3. `app/tools/action_guard.py` and `app/tools/registry.py` - proof-carrying writes and postconditions.
4. `app/security/input_firewall.py` - adversarial input isolation.
5. `app/agent/intents.py` - intent extraction and dependency graph.
6. `frontend/index.html` - handbook-inspired demo UI.
7. `prompts/system.md` - competition prompt strategy.

## Before organizer integration

The handbook names the logical tool capabilities but the uploaded public package does not contain a separate runnable organizer tool/API schema. The tool registry is therefore implemented behind an adapter boundary so organizer APIs can be wired without rewriting the policy/decision engine.

Run the validation suite after that integration and compare tool parameter names and postconditions against the organizer's exact specification.
