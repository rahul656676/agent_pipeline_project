from pydantic import BaseModel, Field
from typing import List, Optional

class ExplanationSchema(BaseModel):
    text: str
    grade: int

class MCQSchema(BaseModel):
    question: str
    options: List[str]
    correct_index: int = Field(..., ge=0, le=3)

class TeacherNotesSchema(BaseModel):
    learning_objective: str
    common_misconceptions: List[str]

class GeneratorOutputSchema(BaseModel):
    explanation: ExplanationSchema
    mcqs: List[MCQSchema]
    teacher_notes: TeacherNotesSchema

class ScoresSchema(BaseModel):
    age_appropriateness: int = Field(..., ge=1, le=5)
    correctness: int = Field(..., ge=1, le=5)
    clarity: int = Field(..., ge=1, le=5)
    coverage: int = Field(..., ge=1, le=5)

class FeedbackItem(BaseModel):
    field: str
    issue: str

class ReviewerOutputSchema(BaseModel):
    scores: ScoresSchema
    pass_: bool = Field(..., alias="pass")
    feedback: List[FeedbackItem]

    class Config:
        populate_by_name = True

class TaggerOutputSchema(BaseModel):
    subject: str
    topic: str
    grade: int
    difficulty: str
    content_type: List[str]
    blooms_level: str
