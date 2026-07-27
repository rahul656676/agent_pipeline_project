import json
import os
from groq import Groq
from .schemas import TaggerOutputSchema

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are the Tagger Agent in an educational content pipeline.
Responsibility: Classify the approved educational content.

You must respond with ONLY valid JSON matching this schema:
{
  "subject": "string (e.g. Mathematics, Science, English, etc.)",
  "topic": "string (the topic of the content)",
  "grade": int,
  "difficulty": "string (Easy, Medium, or Hard)",
  "content_type": ["string", "... (e.g. Explanation, Quiz, Activity, etc.)"],
  "blooms_level": "string (Remembering, Understanding, Applying, Analyzing, Evaluating, or Creating)"
}
"""

class TaggerAgent:
    """Classifies approved educational content."""

    def __init__(self, client: Groq = None):
        self.client = client or Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def run(self, content: dict, grade: int, topic: str) -> dict:
        """
        Args:
            content: The final approved Generator output content.
            grade: Grade level.
            topic: Topic.

        Returns:
            dict matching the Tagger output schema.
        """
        user_prompt = (
            f"Grade: {grade}\n"
            f"Topic: {topic}\n"
            f"Content:\n{json.dumps(content, indent=2)}"
        )

        response = self.client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
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
        validated = TaggerOutputSchema(**parsed)
        return validated.model_dump()
