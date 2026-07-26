"""
Pipeline orchestration
-----------------------
Wires the Generator Agent and Reviewer Agent together with lightweight,
inline refinement logic:

    1. Run Generator(grade, topic)          -> draft
    2. Run Reviewer(draft)                  -> review
    3. If review.status == "fail":
           Re-run Generator with feedback embedded (ONE refinement pass only)
           Re-run Reviewer on the refined draft
    4. Return everything the UI needs to render each stage.

No separate "Refiner" agent is used -- refinement is just calling the
Generator again with the Reviewer's feedback folded into its input.
"""

from .generator_agent import GeneratorAgent
from .reviewer_agent import ReviewerAgent


class AgentPipeline:
    def __init__(self, generator: GeneratorAgent = None, reviewer: ReviewerAgent = None):
        self.generator = generator or GeneratorAgent()
        self.reviewer = reviewer or ReviewerAgent()

    def run(self, grade: int, topic: str) -> dict:
        """
        Runs the full pipeline and returns a result dict describing every
        stage, suitable for direct display in a UI:

        {
            "generator_output": {...},
            "reviewer_output": {"status": ..., "feedback": [...]},
            "refined": bool,
            "refined_output": {...} | None,
            "refined_review": {...} | None
        }
        """
        result = {
            "generator_output": None,
            "reviewer_output": None,
            "refined": False,
            "refined_output": None,
            "refined_review": None,
        }

        # Stage 1: Generator
        draft = self.generator.run({"grade": grade, "topic": topic})
        result["generator_output"] = draft

        # Stage 2: Reviewer
        review = self.reviewer.run(draft, grade, topic)
        result["reviewer_output"] = review

        # Stage 3: Refinement (single bounded pass, inline)
        if review.get("status") == "fail":
            result["refined"] = True
            refined_draft = self.generator.run(
                {"grade": grade, "topic": topic, "feedback": review.get("feedback", [])}
            )
            refined_review = self.reviewer.run(refined_draft, grade, topic)

            result["refined_output"] = refined_draft
            result["refined_review"] = refined_review

        return result


if __name__ == "__main__":
    import json

    pipeline = AgentPipeline()
    output = pipeline.run(grade=4, topic="Types of angles")
    print(json.dumps(output, indent=2))
