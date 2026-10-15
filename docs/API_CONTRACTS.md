# API Contracts

API base path: `/api/v1`

FastAPI generates the authoritative OpenAPI document at `/openapi.json` and interactive documentation at `/docs`.

## Current endpoints

### `GET /health`

Returns service liveness without requiring a database connection.

```json
{
  "status": "ok",
  "service": "ResumeIQ API",
  "environment": "development"
}
```

### `GET /api/v1/health/ready`

Reserved for readiness checks. It will verify database and dependency availability when those connections are enabled.

## Planned resource boundaries

- `/auth`: registration, login, token refresh, logout
- `/resumes`: upload, versions, parsed facts, document status
- `/job-descriptions`: create, upload, extracted requirements
- `/analyses`: start, status, evidence-backed score breakdown, recommendations
- `/comparisons`: compare resume versions against a job description
- `/interviews`: generated interview question sets

Contracts will use Pydantic response models and versioned schema changes. File uploads and analysis execution will be asynchronous; clients will receive a job identifier and poll or subscribe to status updates.
