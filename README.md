# Generator / Reviewer Agent Pipeline

Two structured AI agents plus a UI, built to the assessment spec.

## Structure

```
agent_pipeline_project/
├── agents/
│   ├── generator_agent.py   # Generator Agent (clear responsibility, structured I/O)
│   ├── reviewer_agent.py    # Reviewer Agent (clear responsibility, structured I/O)
│   ├── pipeline.py          # Orchestrates Generator -> Reviewer -> (refine once)
│   └── __init__.py
├── ui/
│   └── index.html           # UI: triggers pipeline, shows all 3 stages
├── app.py                   # Flask API + static file server
├── requirements.txt
├── standalone.html          # Same UI, but calls the Anthropic API directly
│                             from the browser (no backend needed)
└── README.md
```

## Agents

**Generator Agent** — `agents/generator_agent.py`
Responsibility: generate draft educational content for a grade/topic.
Input: `{"grade": 4, "topic": "Types of angles"}` (optionally `"feedback": [...]`)
Output: `{"explanation": "...", "mcqs": [{"question","options","answer"}, ...]}`

**Reviewer Agent** — `agents/reviewer_agent.py`
Responsibility: evaluate the Generator's output for age-appropriateness,
conceptual correctness, and clarity.
Input: content JSON from the Generator.
Output: `{"status": "pass|fail", "feedback": ["...", "..."]}`

**Refinement logic** — `agents/pipeline.py`
If the Reviewer returns `fail`, the Generator is re-run once with the
feedback embedded in its input, then re-reviewed. No separate Refiner
agent — it's the same Generator called again inline, limited to one pass.

## Option A: Run with the Flask backend (recommended)

```bash
cd agent_pipeline_project
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # Windows: set ANTHROPIC_API_KEY=...
python app.py
```

Open **http://localhost:5000** — the UI calls `POST /api/run-pipeline`
with `{"grade": 4, "topic": "Types of angles"}` and renders all three
stages (Generator output, Reviewer feedback, Refined output if applicable).

You can also run the pipeline directly from Python:

```bash
python -m agents.pipeline
```

## Option B: Standalone HTML (no server, no API key setup needed)

`standalone.html` contains the same UI but calls `api.anthropic.com`
directly from the browser — just open the file. Useful for a quick demo
without setting up Flask.

## Notes

- No agent framework is used — each agent is a plain Python class with a
  `run()` method taking structured input and returning structured output,
  per the assessment's "simple Python classes or functions are sufficient."
- Both agents call the Anthropic Messages API (`claude-sonnet-4-6`) and are
  instructed to return JSON only, which is then parsed into Python dicts.
- The UI's pipeline strip (Generator → Reviewer → Refinement) highlights
  the active/passed/failed stage as the pipeline runs, making the agent
  flow visually obvious.
