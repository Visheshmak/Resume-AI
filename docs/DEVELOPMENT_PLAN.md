# ResumeIQ Development Plan

## Product guardrails

1. Resume facts, job requirements, matched evidence, missing information, and generated recommendations remain separate data types.
2. Scores are computed by a configurable scoring engine and always include evidence references.
3. LLM output is schema-validated, provenance-labelled, and never treated as candidate fact.
4. All user-uploaded files are validated, isolated, and processed asynchronously.
5. Every user-facing metric comes from persisted analysis data or an explicit empty state.

## Phases

### Phase 0: Foundation

- Monorepo structure and local infrastructure
- FastAPI configuration, health checks, persistence boundaries, and API versioning
- React application shell with truthful empty states
- Shared contract documentation and environment configuration

### Phase 1: Identity and document intake

- User, session, and refresh-token persistence
- JWT authentication with Argon2 password hashing
- PDF/DOCX validation, object storage abstraction, upload lifecycle
- Background job status model

### Phase 2: Deterministic extraction

- PDF and DOCX text extraction with page/section provenance
- Resume section and entity schemas
- Job description requirement extraction
- Skill and keyword normalization taxonomy

### Phase 3: Evidence-based analysis

- Exact and normalized keyword matching
- Skill evidence mapping
- Semantic matching behind a provider interface
- Configurable scoring engine with persisted score breakdowns
- Formatting and readability diagnostics

### Phase 4: Explainable recommendations

- Weak bullet detection
- Recommendation schemas with source evidence and confidence
- LLM provider adapter with structured output validation
- Job-specific bullet suggestions clearly labelled as generated
- Interview question generation

### Phase 5: Product workflows

- Analysis history and version comparison
- Dashboard analytics sourced from persisted analyses
- Export/share controls and deletion lifecycle
- Audit logging, rate limiting, and observability

### Phase 6: Production hardening

- CI checks, migrations, test fixtures, and contract tests
- Security review and dependency scanning
- Containerized deployment configuration
- Load and failure-path testing
