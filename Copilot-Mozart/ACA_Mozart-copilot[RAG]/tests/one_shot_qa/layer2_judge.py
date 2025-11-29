"""
Layer 2: Semantic Judge (LLM Evaluator)
=======================================
ชั้นที่สาม - ใช้ LLM ตัดสินคุณภาพเชิง semantic

เจ้าค่ะนายท่าน Layer นี้ใช้ LLM ประเมินคุณภาพคำตอบในมิติที่ regex จับไม่ได้:
1. answer_quality: คำตอบดีหรือไม่ (GOOD/OK/BROKEN)
2. uses_docs: ใช้เอกสารอ้างอิงหรือไม่ (YES/PARTIAL/NO)
3. logic_correct: เหตุผลถูกต้องหรือไม่ (YES/NO)
4. math_correct: คำนวณถูกต้องหรือไม่ (YES/NO/N_A)
5. language_ok: ภาษาถูกต้อง (YES/NO)
6. violations: รายการปัญหาที่พบ
"""

import json
from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
from enum import Enum

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class Layer2Verdict(str, Enum):
    """Verdict from Layer 2 semantic evaluation"""
    PASS = "PASS"
    SOFT_FAIL = "SOFT-FAIL"
    HARD_FAIL = "HARD-FAIL"
    SKIPPED = "SKIPPED"  # When LLM not available


@dataclass
class SemanticEvaluation:
    """Structured evaluation from LLM judge"""
    answer_quality: Literal["GOOD", "OK", "BROKEN"]
    uses_docs: Literal["YES", "PARTIAL", "NO"]
    logic_correct: Literal["YES", "NO"]
    math_correct: Literal["YES", "NO", "N_A"]
    language_ok: Literal["YES", "NO"]
    violations: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class Layer2Result:
    """Result from Layer 2 semantic evaluation"""
    verdict: Layer2Verdict
    evaluation: Optional[SemanticEvaluation]
    raw_llm_output: Optional[str]
    error: Optional[str] = None


# =============================================================================
# JUDGE PROMPT TEMPLATES
# =============================================================================

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for electrical engineering QA systems.
You will be given:
1. A USER QUESTION about electrical engineering
2. An AI ANSWER to evaluate
3. SOURCE DOCUMENTS that the AI used

Your task is to evaluate the answer quality. Return a JSON object with these fields:
{
    "answer_quality": "GOOD" | "OK" | "BROKEN",
    "uses_docs": "YES" | "PARTIAL" | "NO",
    "logic_correct": "YES" | "NO",
    "math_correct": "YES" | "NO" | "N_A",
    "language_ok": "YES" | "NO",
    "violations": ["list of specific problems"],
    "reasoning": "brief explanation"
}

Evaluation criteria:
- answer_quality: 
  - GOOD = Correct, complete, well-structured answer
  - OK = Mostly correct but minor issues
  - BROKEN = Wrong answer, hallucinations, or missing key info
  
- uses_docs:
  - YES = Answer clearly uses information from sources
  - PARTIAL = Some info from sources, some from elsewhere
  - NO = Answer ignores sources or contradicts them
  
- logic_correct:
  - YES = Reasoning chain is valid
  - NO = Logical fallacies or incorrect reasoning
  
- math_correct:
  - YES = All calculations are correct
  - NO = Calculation errors
  - N_A = No calculations in answer
  
- language_ok:
  - YES = Language matches expected (Thai if Thai question, English if English)
  - NO = Language mismatch or broken text

- violations: List specific problems like:
  - "Hallucinated value: 30A is wrong for THW 2.5mm²"
  - "Missing: Did not mention 3% voltage drop limit"
  - "Contradicts source: Source says X but answer says Y"

Return ONLY valid JSON. No markdown formatting."""


def build_judge_prompt(
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    expected_language: str = "thai"
) -> str:
    """Build the evaluation prompt for the judge LLM."""
    source_text = ""
    for i, src in enumerate(sources, 1):
        content = src.get("content", "")[:500]  # Limit source length
        source_text += f"\n--- Source {i} ---\n{content}\n"
    
    return f"""EVALUATE THIS QA PAIR:

USER QUESTION:
{question}

AI ANSWER:
{answer}

SOURCE DOCUMENTS:
{source_text}

EXPECTED LANGUAGE: {expected_language}

Return your evaluation as JSON only."""


# =============================================================================
# LLM JUDGE IMPLEMENTATION
# =============================================================================

async def evaluate_with_gemini(
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    expected_language: str = "thai",
    model_name: str = "gemini-2.0-flash-exp",
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> Layer2Result:
    """
    Evaluate answer using Gemini as judge.
    
    Args:
        question: The original question
        answer: The answer to evaluate
        sources: Source documents used
        expected_language: Expected response language
        model_name: Gemini model to use
        project_id: GCP project ID
        location: GCP location
        
    Returns:
        Layer2Result
    """
    if not GENAI_AVAILABLE:
        return Layer2Result(
            verdict=Layer2Verdict.SKIPPED,
            evaluation=None,
            raw_llm_output=None,
            error="google-genai package not installed"
        )
    
    try:
        # Initialize client
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        # Build prompt
        user_prompt = build_judge_prompt(question, answer, sources, expected_language)
        
        # Generate response
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_SYSTEM_PROMPT,
                temperature=0.1,  # Low temp for consistent judgment
                max_output_tokens=1024,
            )
        )
        
        raw_output = response.text
        
        # Parse JSON response
        evaluation = parse_judge_response(raw_output)
        
        if evaluation is None:
            return Layer2Result(
                verdict=Layer2Verdict.SOFT_FAIL,
                evaluation=None,
                raw_llm_output=raw_output,
                error="Failed to parse judge response as JSON"
            )
        
        # Determine verdict from evaluation
        verdict = determine_verdict(evaluation)
        
        return Layer2Result(
            verdict=verdict,
            evaluation=evaluation,
            raw_llm_output=raw_output
        )
        
    except Exception as e:
        return Layer2Result(
            verdict=Layer2Verdict.SKIPPED,
            evaluation=None,
            raw_llm_output=None,
            error=f"LLM error: {str(e)}"
        )


def evaluate_with_gemini_sync(
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    expected_language: str = "thai",
    model_name: str = "gemini-2.0-flash-exp",
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> Layer2Result:
    """Synchronous wrapper for evaluate_with_gemini."""
    import asyncio
    return asyncio.run(evaluate_with_gemini(
        question=question,
        answer=answer,
        sources=sources,
        expected_language=expected_language,
        model_name=model_name,
        project_id=project_id,
        location=location
    ))


def parse_judge_response(raw_output: str) -> Optional[SemanticEvaluation]:
    """Parse JSON response from judge LLM."""
    try:
        # Clean up potential markdown formatting
        text = raw_output.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        
        return SemanticEvaluation(
            answer_quality=data.get("answer_quality", "BROKEN"),
            uses_docs=data.get("uses_docs", "NO"),
            logic_correct=data.get("logic_correct", "NO"),
            math_correct=data.get("math_correct", "N_A"),
            language_ok=data.get("language_ok", "NO"),
            violations=data.get("violations", []),
            reasoning=data.get("reasoning", "")
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def determine_verdict(evaluation: SemanticEvaluation) -> Layer2Verdict:
    """Determine verdict from semantic evaluation."""
    # HARD-FAIL conditions
    if evaluation.answer_quality == "BROKEN":
        return Layer2Verdict.HARD_FAIL
    
    if evaluation.logic_correct == "NO" and evaluation.math_correct == "NO":
        return Layer2Verdict.HARD_FAIL
    
    if evaluation.uses_docs == "NO":
        return Layer2Verdict.HARD_FAIL  # RAG should use docs
    
    # SOFT-FAIL conditions
    if evaluation.answer_quality == "OK":
        return Layer2Verdict.SOFT_FAIL
    
    if evaluation.uses_docs == "PARTIAL":
        return Layer2Verdict.SOFT_FAIL
    
    if evaluation.language_ok == "NO":
        return Layer2Verdict.SOFT_FAIL
    
    if len(evaluation.violations) > 0:
        return Layer2Verdict.SOFT_FAIL
    
    # All checks passed
    return Layer2Verdict.PASS


# =============================================================================
# MOCK JUDGE (for testing without LLM)
# =============================================================================

def mock_evaluate(
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    expected_language: str = "thai"
) -> Layer2Result:
    """
    Mock evaluation for testing without LLM.
    Uses simple heuristics to provide a baseline evaluation.
    """
    violations = []
    
    # Check answer length
    if len(answer) < 50:
        violations.append("Answer too short")
        answer_quality = "BROKEN"
    elif len(answer) < 200:
        answer_quality = "OK"
    else:
        answer_quality = "GOOD"
    
    # Check if sources referenced
    source_content = " ".join(s.get("content", "") for s in sources)
    common_words = set(answer.lower().split()) & set(source_content.lower().split())
    if len(common_words) > 20:
        uses_docs = "YES"
    elif len(common_words) > 5:
        uses_docs = "PARTIAL"
    else:
        uses_docs = "NO"
        violations.append("Answer doesn't seem to use source documents")
    
    # Language check
    thai_chars = sum(1 for c in answer if '\u0e00' <= c <= '\u0e7f')
    if expected_language == "thai":
        if thai_chars > len(answer) * 0.3:
            language_ok = "YES"
        else:
            language_ok = "NO"
            violations.append(f"Expected Thai but answer is {thai_chars/len(answer)*100:.0f}% Thai")
    else:
        if thai_chars < len(answer) * 0.1:
            language_ok = "YES"
        else:
            language_ok = "NO"
            violations.append("Expected English but answer contains Thai")
    
    evaluation = SemanticEvaluation(
        answer_quality=answer_quality,
        uses_docs=uses_docs,
        logic_correct="YES",  # Can't evaluate without LLM
        math_correct="N_A",   # Can't evaluate without LLM
        language_ok=language_ok,
        violations=violations,
        reasoning="Mock evaluation using heuristics"
    )
    
    verdict = determine_verdict(evaluation)
    
    return Layer2Result(
        verdict=verdict,
        evaluation=evaluation,
        raw_llm_output="[MOCK EVALUATION]"
    )


# =============================================================================
# MAIN LAYER 2 RUNNER
# =============================================================================

async def run_layer2(
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    expected_language: str = "thai",
    use_mock: bool = False,
    model_name: str = "gemini-2.0-flash-exp",
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> Layer2Result:
    """
    Run Layer 2 semantic evaluation.
    
    Args:
        question: The original question
        answer: The answer to evaluate
        sources: Source documents
        expected_language: Expected response language
        use_mock: Use mock evaluation instead of LLM
        model_name: Gemini model to use
        project_id: GCP project ID
        location: GCP location
        
    Returns:
        Layer2Result
    """
    if use_mock:
        return mock_evaluate(question, answer, sources, expected_language)
    
    return await evaluate_with_gemini(
        question=question,
        answer=answer,
        sources=sources,
        expected_language=expected_language,
        model_name=model_name,
        project_id=project_id,
        location=location
    )


def run_layer2_sync(
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    expected_language: str = "thai",
    use_mock: bool = False,
    model_name: str = "gemini-2.0-flash-exp",
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> Layer2Result:
    """Synchronous wrapper for run_layer2."""
    import asyncio
    return asyncio.run(run_layer2(
        question=question,
        answer=answer,
        sources=sources,
        expected_language=expected_language,
        use_mock=use_mock,
        model_name=model_name,
        project_id=project_id,
        location=location
    ))
