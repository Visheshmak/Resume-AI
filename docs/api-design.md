# API Design

Base path: `/api/v1`. FastAPI OpenAPI is authoritative.

## Asynchronous analysis

```http
POST /api/v1/analysis
GET /api/v1/analysis/jobs/{job_id}
POST /api/v1/analysis/jobs/{job_id}/retry
GET /api/v1/analysis/{analysis_id}
GET /api/v1/analysis/{analysis_id}/evidence
```

`POST /analysis` returns `202` with the analysis identifier and `job_id`. Clients poll the job endpoint until `completed`, `failed`, or `permanently_failed`. The existing report endpoint remains compatible with the workspace UI.

## Resource rules

Every resume, job, analysis, evidence, and job lookup includes the authenticated user's ID. Unknown or foreign resources return the same not-found behavior rather than leaking existence. API keys and storage credentials remain server-side.

## Response shape

New job responses expose `job_id`, `analysis_id`, `status`, `progress`, `current_step`, `attempts`, and safe error text. Breaking contract changes require a new `/api/v2` prefix.
