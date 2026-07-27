import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from .generator_agent import GeneratorAgent
from .reviewer_agent import ReviewerAgent
from .refiner_agent import RefinerAgent
from .tagger_agent import TaggerAgent

class AgentPipeline:
    def __init__(
        self,
        generator: GeneratorAgent = None,
        reviewer: ReviewerAgent = None,
        refiner: RefinerAgent = None,
        tagger: TaggerAgent = None
    ):
        self.generator = generator or GeneratorAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.refiner = refiner or RefinerAgent()
        self.tagger = tagger or TaggerAgent()

    def run(self, grade: int, topic: str) -> Dict[str, Any]:
        """
        Runs the governed, auditable AI content generation pipeline.
        Returns a RunArtifact matching the specifications in Part 2.
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        
        attempts = []
        final_status = "rejected"
        final_content = None
        final_tags = None

        # Step 1: Generate initial draft
        current_draft = self.generator.run({"grade": grade, "topic": topic})
        current_review = self.reviewer.run(current_draft, grade, topic)

        refinement_count = 0
        max_refinements = 2

        while True:
            if current_review.get("pass") is True:
                final_status = "approved"
                final_content = current_draft
                # Run Tagger on approved content only
                final_tags = self.tagger.run(final_content, grade, topic)
                
                # Log the successful attempt
                attempts.append({
                    "attempt": len(attempts) + 1,
                    "draft": current_draft,
                    "review": current_review,
                    "refined": None
                })
                break

            # If failed and we reached the maximum refinement calls (2), we stop
            if refinement_count >= max_refinements:
                final_status = "rejected"
                final_content = current_draft
                attempts.append({
                    "attempt": len(attempts) + 1,
                    "draft": current_draft,
                    "review": current_review,
                    "refined": None
                })
                break

            # Perform refinement
            refined_draft = self.refiner.run(
                current_draft,
                current_review.get("feedback", []),
                grade,
                topic
            )
            refinement_count += 1

            # Log the current attempt with its refinement output
            attempts.append({
                "attempt": len(attempts) + 1,
                "draft": current_draft,
                "review": current_review,
                "refined": refined_draft
            })

            # Prepare for next iteration
            current_draft = refined_draft
            current_review = self.reviewer.run(current_draft, grade, topic)

        finished_at = datetime.now(timezone.utc).isoformat()

        run_artifact = {
            "run_id": run_id,
            "input": {
                "grade": grade,
                "topic": topic
            },
            "attempts": attempts,
            "final": {
                "status": final_status,
                "content": final_content,
                "tags": final_tags
            },
            "timestamps": {
                "started_at": started_at,
                "finished_at": finished_at
            }
        }

        return run_artifact
