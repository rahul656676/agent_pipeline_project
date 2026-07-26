"""
Generator Agent
---------------
Responsibility:
    Generate draft educational content for a given grade and topic.

Input (structured):
    {
        "grade": 4,
        "topic": "Types of angles",
        "feedback": ["optional reviewer feedback to address"]   # optional
    }

Output (structured):
    {
        "explanation": "...",
        "mcqs": [
            {
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": "B"
            },
            ...
        ]
    }
"""

import json
import os
from groq import Groq

MODEL = "llama3-70b-8192"

SYSTEM_PROMPT = """You are the Generator Agent in an educational content pipeline.
Responsibility: generate draft educational content for a given grade and topic.
You must respond with ONLY valid JSON, no markdown fences, no preamble, matching exactly this schema:
{
  "explanation": "string, 3-6 sentences, written at the reading level of the given grade",
  "mcqs": [
    {"question": "string", "options": ["A text","B text","C text","D text"], "answer": "A"}
  ]
}
Rules:
- Produce exactly 3 multiple choice questions.
- "answer" must be one of "A","B","C","D" and correspond to the correct option's position.
- Language complexity, vocabulary and sentence length must match the grade level.
- Concepts must be factually and pedagogically correct.
- Do not introduce any concept not appropriate for the stated grade.
"""


class GeneratorAgent:
    """Generates draft educational content for a given grade and topic."""

    def __init__(self, client: Groq = None):
        self.client = client or Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
