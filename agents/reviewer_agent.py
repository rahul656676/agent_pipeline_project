import json
import os
from groq import Groq
from pydantic import ValidationError
from .schemas import ReviewerOutputSchema

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are the Reviewer Agent in an educational content pipeline.
Responsibility: evaluate the Generator Agent's output for age appropriateness,
conceptual correctness, clarity, and coverage.

You must respond with ONLY valid JSON matching this schema:
{
  "scores": {
    "age_appropriateness": int (1-5),
    "correctness": int (1-5),
    "clarity": int (1-5),
    "coverage": int (1-5)
  },
  "pass": boolean,
  "feedback": [
    { "field": "string (dot-separated path of the field, e.g. explanation.text or mcqs.0.question)", "issue": "string" }
  ]
}

Rules:
- Give a score from 1 (poor) to 5 (excellent) for each category.
- Define a strict threshold: 'pass' must be true IF AND ONLY IF all scores are 4 or 5.
- If any score is less than 4, 'pass' must be false.
- If 'pass' is false, you must provide specific constructive feedback items.
- Every feedback item MUST reference a specific field (using dot-separated paths like 'explanation.text', 'mcqs.0.question', 'mcqs.1.options', etc.).
"""

class ReviewerAgent:
    """Evaluates the Generator Agent's output against grading criteria."""

    def __init__(self, client: Groq = None):
        self.client = client or Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def run(self, content: dict, grade: int, topic: str) -> dict:
        """
        Args:
            content: the Generator Agent's output dict.
            grade: grade level.
            topic: topic.

        Returns:
            dict matching the Reviewer output schema.
        """
        user_prompt = (
            f"Grade: {grade}\nTopic: {topic}\n"
            f"Content JSON to review:\n{json.dumps(content)}"
        )

        response = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        text = response.choices[0].message.content.strip()

        # More robust JSON extraction
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            text = text.strip()

        parsed = json.loads(text)
        
        # Enforce Python-side threshold checking to be absolutely deterministic
        scores = parsed.get("scores", {})
        age_ok = scores.get("age_appropriateness", 0) >= 4
        corr_ok = scores.get("correctness", 0) >= 4
        clar_ok = scores.get("clarity", 0) >= 4
        cov_ok = scores.get("coverage", 0) >= 4
        
        calculated_pass = age_ok and corr_ok and clar_ok and cov_ok
        parsed["pass"] = calculated_pass
        
        # Validate schema
        validated = ReviewerOutputSchema(**parsed)
        return validated.model_dump(by_alias=True)
