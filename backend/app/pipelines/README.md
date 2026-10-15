Pipeline boundaries reserved for implementation:

1. `document_ingestion`: validate PDF/DOCX and extract source text with provenance.
2. `resume_extraction`: produce structured candidate facts only from source text.
3. `jd_extraction`: produce normalized job requirements from the job description.
4. `deterministic_analysis`: exact/normalized keyword, skills, structure, and readability checks.
5. `semantic_matching`: optional embeddings for candidate evidence to requirement similarity.
6. `llm_analysis`: schema-constrained recommendations, never candidate facts.
7. `scoring`: configurable weighted score components with evidence references.
