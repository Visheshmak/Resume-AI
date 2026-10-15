# Database Design

PostgreSQL is the source of truth. JSONB stores versioned extraction/report payloads while relational keys enforce ownership and lifecycle integrity.

```mermaid
erDiagram
  USERS ||--o{ RESUMES : owns
  RESUMES ||--o{ RESUME_VERSIONS : has
  USERS ||--o{ JOB_DESCRIPTIONS : owns
  USERS ||--o{ ANALYSES : owns
  RESUMES ||--o{ ANALYSES : compares
  JOB_DESCRIPTIONS ||--o{ ANALYSES : compares
  ANALYSES ||--o| ANALYSIS_JOBS : runs_as
  ANALYSES ||--o{ ANALYSIS_EVIDENCE : explains
  USERS ||--o{ ANALYSIS_JOBS : submits
```

## Analysis jobs

`analysis_jobs` contains `id`, `user_id`, `analysis_id`, `idempotency_key`, `status`, `progress`, `current_step`, `attempts`, `error_message`, retry/start/completion timestamps, and `created_at`. `(user_id, idempotency_key)` is unique, preventing duplicate provider work.

Important indexes cover user ownership, analysis lookup, and job status. New schema changes are Alembic migrations; deployment runs `alembic upgrade head` before serving traffic.

## Transaction boundaries

Analysis creation commits the analysis and job together. Worker completion commits the report, evidence, and terminal job state together. A failed transaction leaves the job retryable rather than a partial report.
