# Known Limitations and Failure Modes

1. The local intent parser is deterministic. It is intentionally conservative but can miss unusual natural-language phrasing that an external LLM could understand.
2. The product-spec retrieval is lexical/basic rather than a production-grade vector database. This is sufficient for the supplied 300 product sheets and keeps the demo dependency-light.
3. The runtime action state is a local JSON transaction journal, not a real payments/logistics backend.
4. The optional LLM adapter connects to Google Gemini (free tier via Google AI Studio), and falls back gracefully when unconfigured.
5. The organizer's hidden evaluator and tool API are not part of the provided public archive; adapters therefore isolate tool signatures from the decision engine.

The project is explicit about these limits rather than claiming hidden-test performance that cannot be verified locally.
