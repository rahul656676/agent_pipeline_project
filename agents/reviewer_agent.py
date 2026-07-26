"""
Reviewer Agent
--------------
Responsibility:
    Evaluate the Generator Agent's output.

Input (structured):
    Content JSON from the Generator Agent, plus grade/topic context.

Output (structured):
    {
        "status": "pass | fail",
        "feedback": [
            "Sentence 2 is too complex for Grade 4",
            "Question 3 tests a concept not introduced"
        ]
    }

Evaluation criteria:
    - Age appropriateness
    - Conceptual correctness
    - Clarity
"""

import json
import os
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are the Reviewer Agent in an educational content pipeline.
Responsibility: evaluate the Generator Agent's output for age appropriateness,
conceptual correctness, and clarity.
You must respond with ONLY valid JSON, no markdown fences, no preamble, matching
exactly this schema:
{
  "status": "pass" or "fail",
  "feedback": ["short specific critique", "..."]
}
Rules:
- Mark "fail" if any explanation sentence is too complex for the grade, any
  question tests an unintroduced concept, any answer is wrong, or clarity is poor.
- If everything is acceptable, return "status": "pass" and "feedback": [].
- Feedback items must be concrete and specific enough that a generator could act
  on them (e.g. reference which sentence or question number).
"""


class ReviewerAgent:
    """Evaluates the Generator Agent's output against grading criteria."""

    def __init__(self, client: Groq = None):
        self.client = client or Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def run(self, content: dict, grade: int, topic: str) -> dict:
        """
        Args:
            content: the Generator Agent's output dict (explanation + mcqs).
            grade: grade level the content was written for.
            topic: topic the content was written about.

        Returns:
            dict matching the Reviewer output schema: {"status", "feedback"}.
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

        return json.loads(text)
