import json
import os
from groq import Groq
from pydantic import ValidationError
from .schemas import GeneratorOutputSchema

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are the Refiner Agent in an educational content pipeline.
Responsibility: Refine the previously generated educational content based on the Reviewer's feedback.

You must output valid JSON matching this schema:
{
  "explanation": {
    "text": "string (revised explanation)",
    "grade": int
  },
  "mcqs": [
    {
      "question": "string",
      "options": ["A text", "B text", "C text", "D text"],
      "correct_index": int (0-3)
    }
  ],
  "teacher_notes": {
    "learning_objective": "string",
    "common_misconceptions": ["string", "..."]
  }
}

Rules:
- Keep the overall topic and grade level the same.
- Focus specifically on correcting the issues listed in the feedback.
- Do not introduce new issues.
"""

class RefinerAgent:
    """Refines draft content using reviewer feedback."""

    def __init__(self, client: Groq = None):
        self.client = client or Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def run(self, draft: dict, feedback: list, grade: int, topic: str) -> dict:
        """
        Args:
            draft: The original or previous draft dict.
            feedback: List of dicts, each with 'field' and 'issue'.
            grade: Grade level.
            topic: Topic.

        Returns:
            dict matching the Generator output schema.
        """
        feedback_str = "\n".join(f"- Field '{item['field']}': {item['issue']}" for item in feedback)
        
        user_prompt = (
            f"Grade: {grade}\n"
            f"Topic: {topic}\n\n"
            f"Current Draft:\n{json.dumps(draft, indent=2)}\n\n"
            f"Reviewer Feedback:\n{feedback_str}\n\n"
            "Please revise the content to address all the feedback items above."
        )

        response = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        text = response.choices[0].message.content.strip()

        # Extract and parse
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        else:
            text = text.strip()

        parsed = json.loads(text)
        validated = GeneratorOutputSchema(**parsed)
        return validated.model_dump()
