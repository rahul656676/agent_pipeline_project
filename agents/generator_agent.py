import json
import os
from groq import Groq
from pydantic import ValidationError
from .schemas import GeneratorOutputSchema

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are the Generator Agent in an educational content pipeline.
Responsibility: generate draft educational content for a given grade and topic.
You must respond with ONLY valid JSON matching this schema:
{
  "explanation": {
    "text": "string (3-6 sentences, written at the reading level of the given grade)",
    "grade": int
  },
  "mcqs": [
    {
      "question": "string",
      "options": ["A text", "B text", "C text", "D text"],
      "correct_index": int (0-3 representing the index of the correct option)
    }
  ],
  "teacher_notes": {
    "learning_objective": "string",
    "common_misconceptions": ["string", "..."]
  }
}

Rules:
- Produce exactly 3 multiple choice questions.
- "correct_index" must be an integer between 0 and 3.
- Language complexity, vocabulary and sentence length must match the grade level.
- Concepts must be factually and pedagogically correct.
- Do not introduce any concept not appropriate for the stated grade.
"""

class GeneratorAgent:
    """Generates draft educational content for a given grade and topic."""

    def __init__(self, client: Groq = None):
        self.client = client or Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def run_raw(self, grade: int, topic: str, feedback: list = None) -> str:
        feedback_clause = ""
        if feedback:
            feedback_lines = "\n".join(f"- {item}" for item in feedback)
            feedback_clause = (
                "\n\nThe previous draft was reviewed and marked as FAIL for these "
                f"reasons:\n{feedback_lines}\nRevise the content so every one of "
                "these issues is fixed."
            )

        user_prompt = (
            f"Input:\n{json.dumps({'grade': grade, 'topic': topic})}{feedback_clause}"
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

        return response.choices[0].message.content.strip()

    def run(self, input_data: dict) -> dict:
        """
        Args:
            input_data: {"grade": int, "topic": str, "feedback": Optional[List[str]]}

        Returns:
            dict matching the Generator output schema.
        """
        grade = input_data["grade"]
        topic = input_data["topic"]
        feedback = input_data.get("feedback")

        attempts = 2
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                text = self.run_raw(grade, topic, feedback)
                
                # More robust JSON extraction
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                else:
                    text = text.strip()

                parsed = json.loads(text)
                validated = GeneratorOutputSchema(**parsed)
                return validated.model_dump()
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                if attempt == 1:
                    feedback = [f"JSON/Schema Validation Error on attempt 1: {str(e)}"]
                else:
                    raise ValueError(f"Generator output failed schema validation after {attempts} attempts. Error: {str(last_error)}")
