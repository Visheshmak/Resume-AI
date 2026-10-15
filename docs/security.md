# Security

- Argon2 password hashing and revocable JWT sessions are server-side.
- Resource queries always scope by authenticated `user_id`.
- Upload validation checks extension, MIME/integrity, size, archive safety, and generated storage paths.
- Files are not executed and binary content is not stored in PostgreSQL.
- Secrets use environment configuration; frontend bundles receive no database, JWT, AI, or storage credentials.
- CORS, trusted hosts, secure headers, request IDs, validation, and rate limiting are enabled.
- Logs contain request/job identifiers and timings, never passwords, tokens, full resumes, or provider keys.
- Production must add private object storage, malware scanning, HTTPS termination, centralized rate limiting, secret-manager integration, and audit retention.
