# ResumeIQ AI Layer

The AI layer is an optional language-understanding layer above deterministic extraction and matching.

## Boundaries

- `app/ai/context.py`: immutable structured resume/JD/matching context and evidence map.
- `app/ai/providers.py`: provider adapters for OpenAI, Gemini, mock tests, and the unconfigured stub.
- `app/ai/schemas.py`: strict Pydantic output contracts.
- `app/ai/service.py`: retries, schema validation, evidence validation, and hallucination guards.
- `app/ai/tasks.py`: typed feature entry points.

## Grounding contract

Every generated claim must reference one or more evidence IDs supplied in the context. The orchestration service rejects unknown evidence, empty evidence, extracted skills incorrectly labelled as missing, and bullet rewrites with no matching source text.

The provider receives structured JSON and an explicit instruction to make only claims supported by supplied resume evidence. Hidden reasoning is never stored or returned; only concise explanations and confidence values are accepted.

## Failure behavior

Provider timeouts and transient schema failures retry a bounded number of times. Provider-specific details are not exposed by the service; callers receive a typed `AIServiceError` code such as `provider_timeout`, `invalid_grounded_output`, or `provider_response_error`.

The default `stub` provider fails closed. It never invents AI output.

## Asynchronous analysis

The expensive analysis workflow is represented by a durable `AnalysisJob`. The API creates the analysis and job in one transaction, publishes the job to Redis, and returns `202` with a job identifier. Stateless workers perform extraction/matching/scoring and persist progress and results. The frontend polls the job endpoint; SSE/WebSockets can be added later without changing the worker contract.

Deterministic matching and scoring remain separate from AI interpretation. The matcher owns the final reproducible score; AI providers are used only for typed, grounded explanations and recommendations.