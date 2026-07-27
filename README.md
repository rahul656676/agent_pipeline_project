# Governed & Auditable AI Content Pipeline (Part 2)

This is a reliable, auditable, and schema-validated content generation pipeline with a FastAPI backend and SQLite database persistence. It extends the original system with strict Pydantic schemas, quantitative reviewer evaluation, and a bounded refiner/tagger flow.

## Structure

```
agent_pipeline_project/
├── agents/
│   ├── schemas.py           # Shared Pydantic schemas for validation
│   ├── generator_agent.py   # Generator Agent (validates schema, retries once)
│   ├── reviewer_agent.py    # Reviewer Agent (evaluates scores 1-5, pass thresholds)
│   ├── refiner_agent.py     # Refiner Agent (refines failing content up to 2 times)
│   ├── tagger_agent.py      # Tagger Agent (classifies approved content)
│   ├── pipeline.py          # Pipeline Orchestration (generates RunArtifact audit trail)
│   └── __init__.py
├── project-brain/           # Project Brain v2 Scaffolding
│   ├── system/
│   ├── memory/
│   ├── graph/
│   └── runtime/
├── ui/
│   └── index.html           # UI: Shows scores, refinements, tags, audit logs
├── app.py                   # FastAPI application serving endpoints & index
├── database.py              # SQLite database layer for persistence
├── requirements.txt         # Project requirements
├── tests/
│   └── test_pipeline.py     # 3 mandatory unit tests (mocked LLM calls)
└── README.md
```

## Agent Roles
1. **Generator Agent**: Produces the initial draft educational content (explanation, MCQs, learning objectives, and common misconceptions) for a given grade and topic. Validates output structure against a strict Pydantic schema and retries once if validation fails.
2. **Reviewer Agent (Gatekeeper)**: Evaluates the content quantitatively across four metrics (Age Appropriateness, Correctness, Clarity, and Coverage) on a 1-5 scale. Enforces the pass threshold (all scores must be >= 4) and provides field-specific critiques.
3. **Refiner Agent**: Receives a failed draft and the reviewer's critiques, producing a revised version focusing on resolving the specified issues.
4. **Tagger Agent**: Classifies final approved content into metadata parameters (subject, topic, grade, difficulty, content type, and Bloom's Taxonomy level).

## Pass/Fail Criteria
- **Pass Threshold**: All evaluation categories (Age Appropriateness, Correctness, Clarity, Coverage) must score **4 or 5**. 
- If any score is **< 4**, the run fails and enters the refinement loop.

## Orchestration Decisions
- **RunArtifact**: Every execution produces a single complete audit trail logging the inputs, timestamps, intermediate refinement attempts, scores, drafts, final decision, and tags.
- **Bounded Refinements**: Refinement is strictly capped at a **maximum of 2 attempts**. If the content does not pass the quality threshold by then, its final status is marked as `rejected`.

## Trade-offs
- **LLM-calculated vs. Python-enforced Thresholds**: The Python database/pipeline layer enforces the pass threshold mathematically (`all(score >= 4 for score in scores)`) rather than relying on the LLM to write the correct `pass` boolean. This prevents mismatch bugs.
- **JSON Mode with Pydantic vs. Free Text**: All agent invocations on Groq (`llama-3.3-70b-versatile`) use `response_format={"type": "json_object"}` alongside Pydantic models. This ensures extremely high structure determinism.

## Installation & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Create a `.env` file or export your Groq key:
   ```bash
   export GROQ_API_KEY=gsk_...
   ```

3. **Run the Application**:
   ```bash
   python app.py
   ```
   Open **http://localhost:5000** to view the UI.

4. **Run Tests**:
   ```bash
   python -m pytest tests/test_pipeline.py -v
   ```
