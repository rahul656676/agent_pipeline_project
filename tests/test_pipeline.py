import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from agents.pipeline import AgentPipeline
from agents.generator_agent import GeneratorAgent
from agents.reviewer_agent import ReviewerAgent
from agents.refiner_agent import RefinerAgent
from agents.tagger_agent import TaggerAgent

# Mock LLM response helper for completions
def make_mock_completion(content_dict: dict):
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(content_dict)
    mock_completion.choices = [mock_choice]
    return mock_completion

@patch("agents.generator_agent.Groq")
@patch("agents.reviewer_agent.Groq")
@patch("agents.refiner_agent.Groq")
@patch("agents.tagger_agent.Groq")
def test_schema_validation_failure_handling(
    mock_groq_tagger, mock_groq_refiner, mock_groq_reviewer, mock_groq_generator
):
    """
    Test 1: Schema validation failure handling.
    The generator returns an invalid JSON/schema on the first attempt,
    then fails again on the retry, causing it to fail gracefully with ValueError.
    """
    # Generator client mock
    mock_gen_client = MagicMock()
    # First response: invalid structure
    mock_response_1 = make_mock_completion({"invalid_key": "val"})
    # Second response: still invalid
    mock_response_2 = make_mock_completion({"mcqs": []})
    mock_gen_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
    mock_groq_generator.return_value = mock_gen_client

    agent = GeneratorAgent()
    with pytest.raises(ValueError) as excinfo:
        agent.run({"grade": 5, "topic": "Fractions"})
    
    assert "failed schema validation after 2 attempts" in str(excinfo.value)


@patch("agents.generator_agent.Groq")
@patch("agents.reviewer_agent.Groq")
@patch("agents.refiner_agent.Groq")
@patch("agents.tagger_agent.Groq")
def test_fail_refine_pass_orchestration(
    mock_groq_tagger, mock_groq_refiner, mock_groq_reviewer, mock_groq_generator
):
    """
    Test 2: Fail -> refine -> pass orchestration.
    - Gen returns draft 1.
    - Reviewer returns fail (score 3).
    - Refiner returns refined draft.
    - Reviewer returns pass (score 5).
    - Tagger returns tags.
    """
    # 1. Generator returns draft_1
    draft_1 = {
        "explanation": {"text": "Simple explanation of fractions.", "grade": 5},
        "mcqs": [{"question": "Q?", "options": ["A", "B", "C", "D"], "correct_index": 1}],
        "teacher_notes": {"learning_objective": "Learn.", "common_misconceptions": ["None"]}
    }
    mock_gen_client = MagicMock()
    mock_gen_client.chat.completions.create.return_value = make_mock_completion(draft_1)
    mock_groq_generator.return_value = mock_gen_client

    # 2. Reviewer returns fail on first call, pass on second call
    review_fail = {
        "scores": {"age_appropriateness": 3, "correctness": 5, "clarity": 5, "coverage": 5},
        "pass": False,
        "feedback": [{"field": "explanation.text", "issue": "Sentence too complex"}]
    }
    review_pass = {
        "scores": {"age_appropriateness": 5, "correctness": 5, "clarity": 5, "coverage": 5},
        "pass": True,
        "feedback": []
    }
    mock_rev_client = MagicMock()
    mock_rev_client.chat.completions.create.side_effect = [
        make_mock_completion(review_fail),
        make_mock_completion(review_pass)
    ]
    mock_groq_reviewer.return_value = mock_rev_client

    # 3. Refiner returns refined draft
    refined_draft = {
        "explanation": {"text": "Even simpler explanation of fractions.", "grade": 5},
        "mcqs": [{"question": "Q?", "options": ["A", "B", "C", "D"], "correct_index": 1}],
        "teacher_notes": {"learning_objective": "Learn.", "common_misconceptions": ["None"]}
    }
    mock_ref_client = MagicMock()
    mock_ref_client.chat.completions.create.return_value = make_mock_completion(refined_draft)
    mock_groq_refiner.return_value = mock_ref_client

    # 4. Tagger returns tags
    tags = {
        "subject": "Mathematics",
        "topic": "Fractions",
        "grade": 5,
        "difficulty": "Medium",
        "content_type": ["Explanation"],
        "blooms_level": "Understanding"
    }
    mock_tag_client = MagicMock()
    mock_tag_client.chat.completions.create.return_value = make_mock_completion(tags)
    mock_groq_tagger.return_value = mock_tag_client

    pipeline = AgentPipeline()
    artifact = pipeline.run(grade=5, topic="Fractions")

    assert artifact["final"]["status"] == "approved"
    assert len(artifact["attempts"]) == 2
    assert artifact["attempts"][0]["refined"] == refined_draft
    assert artifact["final"]["content"] == refined_draft
    assert artifact["final"]["tags"] == tags


@patch("agents.generator_agent.Groq")
@patch("agents.reviewer_agent.Groq")
@patch("agents.refiner_agent.Groq")
@patch("agents.tagger_agent.Groq")
def test_fail_refine_fail_reject_orchestration(
    mock_groq_tagger, mock_groq_refiner, mock_groq_reviewer, mock_groq_generator
):
    """
    Test 3: Fail -> refine -> fail -> reject orchestration.
    - Gen returns draft 1.
    - Reviewer returns fail (score 3).
    - Refiner returns refined draft 1.
    - Reviewer returns fail (score 3).
    - Refiner returns refined draft 2.
    - Reviewer returns fail (score 3).
    - Max refinements (2) reached, status becomes rejected, no tagger run.
    """
    draft_1 = {
        "explanation": {"text": "Simple explanation.", "grade": 5},
        "mcqs": [],
        "teacher_notes": {"learning_objective": "Learn.", "common_misconceptions": []}
    }
    mock_gen_client = MagicMock()
    mock_gen_client.chat.completions.create.return_value = make_mock_completion(draft_1)
    mock_groq_generator.return_value = mock_gen_client

    review_fail = {
        "scores": {"age_appropriateness": 3, "correctness": 5, "clarity": 5, "coverage": 5},
        "pass": False,
        "feedback": [{"field": "explanation.text", "issue": "Complexity"}]
    }
    mock_rev_client = MagicMock()
    mock_rev_client.chat.completions.create.side_effect = [
        make_mock_completion(review_fail),
        make_mock_completion(review_fail),
        make_mock_completion(review_fail)
    ]
    mock_groq_reviewer.return_value = mock_rev_client

    mock_ref_client = MagicMock()
    mock_ref_client.chat.completions.create.return_value = make_mock_completion(draft_1)
    mock_groq_refiner.return_value = mock_ref_client

    pipeline = AgentPipeline()
    artifact = pipeline.run(grade=5, topic="Fractions")

    assert artifact["final"]["status"] == "rejected"
    assert len(artifact["attempts"]) == 3
    assert artifact["attempts"][0]["refined"] is not None
    assert artifact["attempts"][1]["refined"] is not None
    assert artifact["attempts"][2]["refined"] is None
    assert artifact["final"]["tags"] is None
