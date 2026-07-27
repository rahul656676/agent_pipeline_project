# Project Brain v2 - System Rules

These are the operational directives for the governed and auditable AI Content Pipeline.

1. **Strict Schema Validation**: All agent responses must validate against Pydantic models.
2. **Quantitative Quality Gate**: Reviews must evaluate content across age appropriateness, correctness, clarity, and coverage with scores from 1-5. Pass threshold is set to all scores >= 4.
3. **Auditability**: Every content run must produce a complete `RunArtifact` that logs all generation and review attempts, including refined attempts and final tags.
4. **Testability**: The pipeline logic must be covered by unit tests verifying normal pass paths, refinement-then-pass paths, and validation failure paths.
