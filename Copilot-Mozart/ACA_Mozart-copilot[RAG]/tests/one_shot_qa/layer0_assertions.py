"""
Layer 0: Hard Assertions
========================
ชั้นแรกสุด - fail แล้ว HARD-FAIL ทันที

เจ้าค่ะนายท่าน Layer นี้ตรวจสอบ "ความถูกต้องทางเทคนิค" ของ response
ไม่สนใจว่า LLM จะ "ตอบ" ว่าอะไร แต่ดูว่า:
1. HTTP Status = 200
2. Response เป็น valid JSON
3. JSON parse ได้เป็น StandardResponse (Pydantic)
4. มี sources >= min_sources
5. metadata.llm_model ตรงกับ config
"""

import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, ValidationError
import httpx


class Layer0Verdict(str, Enum):
    """Verdict for Layer 0 assertions"""
    PASS = "PASS"
    HARD_FAIL = "HARD-FAIL"


@dataclass
class Layer0Result:
    """Result from Layer 0 assertion checks"""
    verdict: Layer0Verdict
    checks: Dict[str, bool]
    errors: List[str]
    response_data: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    http_status: Optional[int] = None


# --- Pydantic Models for Response Validation ---
# These mirror the actual models from app/models.py

class SourceRef(BaseModel):
    """Source reference from retrieval"""
    content: str
    metadata: Dict[str, Any] = {}


class AnswerMetadata(BaseModel):
    """Metadata about the answer generation"""
    llm_model: str
    retrieved_docs: int
    retrieval_group: Optional[str] = None


class StandardResponse(BaseModel):
    """Expected response schema from /api/v1/ask"""
    answer: str
    sources: List[SourceRef]
    confidence: str  # "High", "Medium", "Low"
    grounding_status: str
    metadata: AnswerMetadata


# --- Assertion Functions ---

def check_http_status(response: httpx.Response) -> tuple[bool, str]:
    """Check if HTTP status is 200 OK"""
    if response.status_code == 200:
        return True, "HTTP 200 OK"
    else:
        return False, f"HTTP {response.status_code}: {response.text[:200]}"


def check_json_parse(response: httpx.Response) -> tuple[bool, str, Optional[Dict]]:
    """Check if response is valid JSON"""
    try:
        data = response.json()
        return True, "Valid JSON", data
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}", None


def check_pydantic_schema(data: Dict[str, Any]) -> tuple[bool, str, Optional[StandardResponse]]:
    """Check if JSON matches StandardResponse schema"""
    try:
        parsed = StandardResponse.model_validate(data)
        return True, "Valid StandardResponse schema", parsed
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            error_messages.append(f"{loc}: {error['msg']}")
        return False, f"Schema validation failed: {'; '.join(error_messages)}", None


def check_min_sources(data: Dict[str, Any], min_sources: int = 1) -> tuple[bool, str]:
    """Check if response has minimum number of sources"""
    sources = data.get("sources", [])
    num_sources = len(sources)
    if num_sources >= min_sources:
        return True, f"Has {num_sources} sources (min: {min_sources})"
    else:
        return False, f"Only {num_sources} sources, need at least {min_sources}"


def check_llm_model_match(
    data: Dict[str, Any], 
    expected_model: Optional[str] = None
) -> tuple[bool, str]:
    """
    Check if LLM model in response matches expected model.
    If expected_model is None, just check that a model is specified.
    """
    metadata = data.get("metadata", {})
    llm_model = metadata.get("llm_model", "")
    
    if not llm_model:
        return False, "No llm_model in metadata"
    
    if expected_model is None:
        return True, f"LLM model: {llm_model}"
    
    if llm_model == expected_model:
        return True, f"LLM model matches: {llm_model}"
    else:
        return False, f"LLM model mismatch: got {llm_model}, expected {expected_model}"


def check_confidence_valid(data: Dict[str, Any]) -> tuple[bool, str]:
    """Check if confidence is one of valid values"""
    valid_values = {"High", "Medium", "Low"}
    confidence = data.get("confidence", "")
    
    if confidence in valid_values:
        return True, f"Valid confidence: {confidence}"
    else:
        return False, f"Invalid confidence: {confidence}, must be one of {valid_values}"


def check_no_empty_answer(data: Dict[str, Any]) -> tuple[bool, str]:
    """Check that answer is not empty"""
    answer = data.get("answer", "")
    
    if answer and len(answer.strip()) > 0:
        return True, f"Answer has {len(answer)} characters"
    else:
        return False, "Empty or whitespace-only answer"


# --- Main Layer 0 Runner ---

async def run_layer0(
    api_url: str,
    query: str,
    min_sources: int = 1,
    expected_model: Optional[str] = None,
    timeout: float = 30.0
) -> Layer0Result:
    """
    Run all Layer 0 assertions against the API.
    
    Args:
        api_url: Full URL to the /api/v1/ask endpoint
        query: Query string to send
        min_sources: Minimum number of sources expected
        expected_model: Expected LLM model name (None to skip check)
        timeout: Request timeout in seconds
        
    Returns:
        Layer0Result with verdict and detailed check results
    """
    checks: Dict[str, bool] = {}
    errors: List[str] = []
    response_data: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    http_status: Optional[int] = None
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                api_url,
                json={"question": query}
            )
            http_status = response.status_code
            raw_response = response.text
            
            # Check 1: HTTP Status
            passed, msg = check_http_status(response)
            checks["http_status_200"] = passed
            if not passed:
                errors.append(msg)
                return Layer0Result(
                    verdict=Layer0Verdict.HARD_FAIL,
                    checks=checks,
                    errors=errors,
                    http_status=http_status,
                    raw_response=raw_response
                )
            
            # Check 2: JSON Parse
            passed, msg, data = check_json_parse(response)
            checks["json_valid"] = passed
            if not passed:
                errors.append(msg)
                return Layer0Result(
                    verdict=Layer0Verdict.HARD_FAIL,
                    checks=checks,
                    errors=errors,
                    http_status=http_status,
                    raw_response=raw_response
                )
            response_data = data
            
            # Check 3: Pydantic Schema
            passed, msg, _ = check_pydantic_schema(data)
            checks["pydantic_schema"] = passed
            if not passed:
                errors.append(msg)
                return Layer0Result(
                    verdict=Layer0Verdict.HARD_FAIL,
                    checks=checks,
                    errors=errors,
                    http_status=http_status,
                    raw_response=raw_response,
                    response_data=response_data
                )
            
            # Check 4: Minimum Sources
            passed, msg = check_min_sources(data, min_sources)
            checks["min_sources"] = passed
            if not passed:
                errors.append(msg)
                # This is a SOFT-FAIL candidate, but in Layer 0 we're strict
                return Layer0Result(
                    verdict=Layer0Verdict.HARD_FAIL,
                    checks=checks,
                    errors=errors,
                    http_status=http_status,
                    raw_response=raw_response,
                    response_data=response_data
                )
            
            # Check 5: LLM Model (optional)
            passed, msg = check_llm_model_match(data, expected_model)
            checks["llm_model"] = passed
            if not passed and expected_model is not None:
                errors.append(msg)
                # Non-fatal but logged
            
            # Check 6: Valid Confidence
            passed, msg = check_confidence_valid(data)
            checks["confidence_valid"] = passed
            if not passed:
                errors.append(msg)
                return Layer0Result(
                    verdict=Layer0Verdict.HARD_FAIL,
                    checks=checks,
                    errors=errors,
                    http_status=http_status,
                    raw_response=raw_response,
                    response_data=response_data
                )
            
            # Check 7: Non-empty Answer
            passed, msg = check_no_empty_answer(data)
            checks["non_empty_answer"] = passed
            if not passed:
                errors.append(msg)
                return Layer0Result(
                    verdict=Layer0Verdict.HARD_FAIL,
                    checks=checks,
                    errors=errors,
                    http_status=http_status,
                    raw_response=raw_response,
                    response_data=response_data
                )
            
            # All checks passed!
            return Layer0Result(
                verdict=Layer0Verdict.PASS,
                checks=checks,
                errors=errors,
                http_status=http_status,
                raw_response=raw_response,
                response_data=response_data
            )
            
        except httpx.TimeoutException:
            errors.append(f"Request timeout after {timeout}s")
            return Layer0Result(
                verdict=Layer0Verdict.HARD_FAIL,
                checks={"timeout": False},
                errors=errors
            )
        except httpx.ConnectError as e:
            errors.append(f"Connection error: {e}")
            return Layer0Result(
                verdict=Layer0Verdict.HARD_FAIL,
                checks={"connection": False},
                errors=errors
            )
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            return Layer0Result(
                verdict=Layer0Verdict.HARD_FAIL,
                checks={"unexpected": False},
                errors=errors
            )


def run_layer0_sync(
    api_url: str,
    query: str,
    min_sources: int = 1,
    expected_model: Optional[str] = None,
    timeout: float = 30.0
) -> Layer0Result:
    """Synchronous wrapper for run_layer0"""
    import asyncio
    return asyncio.run(run_layer0(
        api_url=api_url,
        query=query,
        min_sources=min_sources,
        expected_model=expected_model,
        timeout=timeout
    ))


# --- Direct Response Validation (for testing without HTTP) ---

def validate_response_dict(
    data: Dict[str, Any],
    min_sources: int = 1,
    expected_model: Optional[str] = None
) -> Layer0Result:
    """
    Validate a response dictionary directly (for unit testing).
    
    Args:
        data: Response dictionary to validate
        min_sources: Minimum number of sources expected
        expected_model: Expected LLM model name
        
    Returns:
        Layer0Result
    """
    checks: Dict[str, bool] = {}
    errors: List[str] = []
    
    # JSON is already parsed
    checks["json_valid"] = True
    
    # Check Pydantic Schema
    passed, msg, _ = check_pydantic_schema(data)
    checks["pydantic_schema"] = passed
    if not passed:
        errors.append(msg)
        return Layer0Result(
            verdict=Layer0Verdict.HARD_FAIL,
            checks=checks,
            errors=errors,
            response_data=data
        )
    
    # Check Minimum Sources
    passed, msg = check_min_sources(data, min_sources)
    checks["min_sources"] = passed
    if not passed:
        errors.append(msg)
        return Layer0Result(
            verdict=Layer0Verdict.HARD_FAIL,
            checks=checks,
            errors=errors,
            response_data=data
        )
    
    # Check LLM Model
    passed, msg = check_llm_model_match(data, expected_model)
    checks["llm_model"] = passed
    if not passed and expected_model is not None:
        errors.append(msg)
    
    # Check Valid Confidence
    passed, msg = check_confidence_valid(data)
    checks["confidence_valid"] = passed
    if not passed:
        errors.append(msg)
        return Layer0Result(
            verdict=Layer0Verdict.HARD_FAIL,
            checks=checks,
            errors=errors,
            response_data=data
        )
    
    # Check Non-empty Answer
    passed, msg = check_no_empty_answer(data)
    checks["non_empty_answer"] = passed
    if not passed:
        errors.append(msg)
        return Layer0Result(
            verdict=Layer0Verdict.HARD_FAIL,
            checks=checks,
            errors=errors,
            response_data=data
        )
    
    return Layer0Result(
        verdict=Layer0Verdict.PASS,
        checks=checks,
        errors=errors,
        response_data=data
    )
