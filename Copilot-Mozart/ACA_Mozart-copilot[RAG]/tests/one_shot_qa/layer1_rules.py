"""
Layer 1: Rule-Based Engineering Checks
======================================
ชั้นที่สอง - มี Ground Truth เทียบ ถ้าผิดแล้ว SOFT-FAIL

เจ้าค่ะนายท่าน Layer นี้ตรวจสอบ "ความถูกต้องเชิงวิศวกรรม"
เทียบคำตอบกับ Ground Truth จาก catalog_rows.csv และมาตรฐาน วสท.

ความสามารถ:
1. Parse ตัวเลขจากคำตอบ (current, VD%, wire size, breaker rating)
2. Validate ค่าที่ parse ได้กับ Ground Truth (±tolerance)
3. Check ว่า sources อ้างอิง rule ที่ถูกต้องหรือไม่
"""

import re
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .ground_truth import (
    THW_CABLES,
    XLPE_CABLES,
    CableInsulation,
    CableSpec,
    STANDARD_BREAKERS,
    get_correct_breaker,
    DERATING_FACTORS,
    get_derating_factor,
    calculate_voltage_drop_1ph,
    is_voltage_drop_acceptable,
    VALID_DEVICE_CODES,
    is_valid_device_code,
    VALID_ROOM_TEMPLATES,
    is_valid_room_template,
    STANDARD_LIMITS,
    validate_ampacity_claim,
    RCD_REQUIREMENTS,
)


class Layer1Verdict(str, Enum):
    """Verdict for Layer 1 checks"""
    PASS = "PASS"
    SOFT_FAIL = "SOFT-FAIL"  # Wrong but recoverable
    HARD_FAIL = "HARD-FAIL"  # Critical engineering error


@dataclass
class ParsedValue:
    """A value parsed from the answer text"""
    raw_text: str
    value: Union[float, int, str]
    unit: Optional[str] = None
    context: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating a single value"""
    field_name: str
    expected: Any
    actual: Any
    passed: bool
    message: str
    tolerance_used: Optional[float] = None


@dataclass
class Layer1Result:
    """Result from Layer 1 rule-based checks"""
    verdict: Layer1Verdict
    validations: List[ValidationResult]
    parsed_values: Dict[str, ParsedValue]
    errors: List[str]
    warnings: List[str]


# =============================================================================
# ANSWER PARSERS - Extract numbers from LLM answer text
# =============================================================================

def parse_ampacity_from_answer(answer: str) -> Optional[ParsedValue]:
    """
    Parse ampacity value from answer text.
    
    Patterns matched:
    - "24A", "24 A", "24 แอมป์", "24 ampere"
    - "ampacity of 24A"
    - "กระแส 24 แอมป์"
    - "current carrying capacity is 24A"
    """
    patterns = [
        r'(?:ampacity|current carrying capacity|กระแสพิกัด|พิกัดกระแส)[^\d]*(\d+(?:\.\d+)?)\s*(?:A|แอมป์|ampere)?',
        r'(\d+(?:\.\d+)?)\s*(?:A|แอมป์|ampere)(?:\s+ampacity)?',
        r'(?:กระแส|current)[^\d]*(\d+(?:\.\d+)?)\s*(?:A|แอมป์)?',
        r'(\d+(?:\.\d+)?)\s*ampere',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return ParsedValue(
                raw_text=match.group(0),
                value=value,
                unit="A",
                context=answer[max(0, match.start()-20):match.end()+20]
            )
    return None


def parse_voltage_drop_from_answer(answer: str) -> Optional[ParsedValue]:
    """
    Parse voltage drop percentage from answer text.
    
    Patterns matched:
    - "2.5%", "2.5 %"
    - "voltage drop of 2.5%"
    - "VD = 2.5%"
    - "แรงดันตก 2.5%"
    """
    patterns = [
        r'(?:voltage drop|VD|แรงดันตก|แรงดันลดลง)[^\d]*(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*%\s*(?:voltage drop|VD)?',
        r'(?:drop|ตก)[^\d]*(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return ParsedValue(
                raw_text=match.group(0),
                value=value,
                unit="%",
                context=answer[max(0, match.start()-20):match.end()+20]
            )
    return None


def parse_wire_size_from_answer(answer: str) -> Optional[ParsedValue]:
    """
    Parse wire size from answer text.
    
    Patterns matched:
    - "2.5 mm²", "2.5mm2", "2.5 ตร.มม."
    - "THW 2.5mm²"
    - "สาย 2.5 ตารางมิลลิเมตร"
    """
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:mm²|mm2|ตร\.?มม\.?|ตารางมิลลิเมตร)',
        r'(?:THW|XLPE|NYY)[^\d]*(\d+(?:\.\d+)?)\s*(?:mm²|mm2)?',
        r'(?:ขนาด|size)[^\d]*(\d+(?:\.\d+)?)\s*(?:mm²|mm2|ตร\.?มม\.?)?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return ParsedValue(
                raw_text=match.group(0),
                value=value,
                unit="mm²",
                context=answer[max(0, match.start()-20):match.end()+20]
            )
    return None


def parse_breaker_rating_from_answer(answer: str) -> Optional[ParsedValue]:
    """
    Parse breaker rating from answer text.
    
    Patterns matched:
    - "16A breaker", "เบรกเกอร์ 16A"
    - "MCB 16A", "RCBO 16A"
    - "circuit breaker rated 16A"
    """
    patterns = [
        r'(?:breaker|เบรกเกอร์|MCB|RCBO|CB)[^\d]*(\d+)\s*(?:A|แอมป์)?',
        r'(\d+)\s*(?:A|แอมป์)\s*(?:breaker|เบรกเกอร์|MCB|RCBO)?',
        r'(?:rated|พิกัด)[^\d]*(\d+)\s*(?:A|แอมป์)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            return ParsedValue(
                raw_text=match.group(0),
                value=value,
                unit="A",
                context=answer[max(0, match.start()-20):match.end()+20]
            )
    return None


def parse_derating_factor_from_answer(answer: str) -> Optional[ParsedValue]:
    """
    Parse derating factor from answer text.
    
    Patterns matched:
    - "derating factor of 0.8"
    - "ตัวคูณลดค่า 0.8"
    - "k = 0.8"
    """
    patterns = [
        r'(?:derating factor|ตัวคูณลดค่า|correction factor)[^\d]*(\d+(?:\.\d+)?)',
        r'(?:k|K)\s*=\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*(?:derating|ลดค่า)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            if 0 < value <= 1.0:  # Valid range for derating
                return ParsedValue(
                    raw_text=match.group(0),
                    value=value,
                    unit="factor",
                    context=answer[max(0, match.start()-20):match.end()+20]
                )
    return None


def parse_device_code_from_answer(answer: str) -> List[ParsedValue]:
    """
    Parse device codes from answer text.
    
    Returns list of all device codes found.
    """
    # Pattern for device codes like AC-9000BTU, SOCKET-16A, etc.
    pattern = r'[A-Z]+-[\w\d]+-?[\w\d]*'
    
    results = []
    for match in re.finditer(pattern, answer):
        code = match.group(0)
        results.append(ParsedValue(
            raw_text=code,
            value=code,
            unit=None,
            context=answer[max(0, match.start()-20):match.end()+20]
        ))
    return results


# =============================================================================
# VALIDATORS - Compare parsed values against ground truth
# =============================================================================

def validate_ampacity(
    parsed: ParsedValue,
    wire_size_mm2: float,
    insulation: CableInsulation = CableInsulation.THW,
    in_conduit: bool = True,
    tolerance_percent: float = 5.0
) -> ValidationResult:
    """
    Validate parsed ampacity against ground truth.
    
    Args:
        parsed: ParsedValue containing the ampacity
        wire_size_mm2: Wire size to look up
        insulation: Cable insulation type
        in_conduit: True if in conduit, False for free air
        tolerance_percent: Acceptable tolerance
        
    Returns:
        ValidationResult
    """
    cables = THW_CABLES if insulation == CableInsulation.THW else XLPE_CABLES
    
    if wire_size_mm2 not in cables:
        return ValidationResult(
            field_name="ampacity",
            expected=f"Unknown for {wire_size_mm2}mm²",
            actual=parsed.value,
            passed=False,
            message=f"Wire size {wire_size_mm2}mm² not in catalog"
        )
    
    spec = cables[wire_size_mm2]
    expected = spec.ampacity_in_conduit_a if in_conduit else spec.ampacity_free_air_a
    actual = float(parsed.value)
    
    lower = expected * (1 - tolerance_percent / 100)
    upper = expected * (1 + tolerance_percent / 100)
    
    passed = lower <= actual <= upper
    
    return ValidationResult(
        field_name="ampacity",
        expected=expected,
        actual=actual,
        passed=passed,
        message=f"THW {wire_size_mm2}mm² ampacity: expected {expected}A ±{tolerance_percent}%, got {actual}A",
        tolerance_used=tolerance_percent
    )


def validate_voltage_drop(
    parsed: ParsedValue,
    expected_vd_percent: Optional[float] = None,
    max_allowed_percent: float = 3.0,
    tolerance_percent: float = 0.2
) -> ValidationResult:
    """
    Validate parsed voltage drop.
    
    Args:
        parsed: ParsedValue containing the VD percentage
        expected_vd_percent: Expected VD if known (for exact check)
        max_allowed_percent: Maximum allowed VD (default 3% per วสท.)
        tolerance_percent: Acceptable tolerance for exact match
        
    Returns:
        ValidationResult
    """
    actual = float(parsed.value)
    
    # If we have expected value, do exact check
    if expected_vd_percent is not None:
        lower = expected_vd_percent - tolerance_percent
        upper = expected_vd_percent + tolerance_percent
        passed = lower <= actual <= upper
        
        return ValidationResult(
            field_name="voltage_drop",
            expected=expected_vd_percent,
            actual=actual,
            passed=passed,
            message=f"VD: expected {expected_vd_percent}% ±{tolerance_percent}%, got {actual}%",
            tolerance_used=tolerance_percent
        )
    
    # Otherwise just check against limit
    passed = actual <= max_allowed_percent
    return ValidationResult(
        field_name="voltage_drop_limit",
        expected=f"≤{max_allowed_percent}%",
        actual=actual,
        passed=passed,
        message=f"VD limit: {actual}% vs max {max_allowed_percent}%"
    )


def validate_breaker_selection(
    parsed: ParsedValue,
    load_current_a: float
) -> ValidationResult:
    """
    Validate breaker selection for given load.
    
    Rules:
    - Breaker rating >= load current
    - Load should be <= 80% of breaker (continuous load rule)
    
    Args:
        parsed: ParsedValue containing the breaker rating
        load_current_a: Load current that breaker must handle
        
    Returns:
        ValidationResult
    """
    actual_rating = int(parsed.value)
    expected_rating = get_correct_breaker(load_current_a)
    
    # Check 80% rule
    max_load_for_rating = actual_rating * 0.8
    
    if actual_rating < load_current_a:
        passed = False
        message = f"Breaker {actual_rating}A undersized for {load_current_a}A load"
    elif load_current_a > max_load_for_rating:
        passed = False
        message = f"Load {load_current_a}A exceeds 80% of {actual_rating}A breaker ({max_load_for_rating}A)"
    elif actual_rating == expected_rating:
        passed = True
        message = f"Correct breaker: {actual_rating}A for {load_current_a}A load"
    else:
        # Oversized but acceptable
        passed = True
        message = f"Acceptable: {actual_rating}A for {load_current_a}A (optimal: {expected_rating}A)"
    
    return ValidationResult(
        field_name="breaker_rating",
        expected=expected_rating,
        actual=actual_rating,
        passed=passed,
        message=message
    )


def validate_derating_factor(
    parsed: ParsedValue,
    factor_type: str,
    condition_value: int,
    tolerance: float = 0.05
) -> ValidationResult:
    """
    Validate derating factor against ground truth.
    
    Args:
        parsed: ParsedValue containing the factor
        factor_type: Type of derating (conductor_grouping, ambient_temperature, thermal_insulation)
        condition_value: The condition value (num conductors, temp, insulation thickness)
        tolerance: Acceptable tolerance
        
    Returns:
        ValidationResult
    """
    actual = float(parsed.value)
    
    if factor_type == "conductor_grouping":
        expected = get_derating_factor("conductor_grouping", num_conductors=condition_value)
    elif factor_type == "ambient_temperature":
        expected = get_derating_factor("ambient_temperature", ambient_temp_c=condition_value)
    elif factor_type == "thermal_insulation":
        expected = get_derating_factor("thermal_insulation", insulation_thickness_mm=condition_value)
    else:
        return ValidationResult(
            field_name="derating_factor",
            expected="Unknown",
            actual=actual,
            passed=False,
            message=f"Unknown derating type: {factor_type}"
        )
    
    lower = expected - tolerance
    upper = expected + tolerance
    passed = lower <= actual <= upper
    
    return ValidationResult(
        field_name="derating_factor",
        expected=expected,
        actual=actual,
        passed=passed,
        message=f"Derating for {factor_type}={condition_value}: expected {expected} ±{tolerance}, got {actual}",
        tolerance_used=tolerance
    )


def validate_device_codes(device_codes: List[ParsedValue]) -> List[ValidationResult]:
    """
    Validate that all device codes exist in catalog.
    
    Args:
        device_codes: List of ParsedValue containing device codes
        
    Returns:
        List of ValidationResult, one per device code
    """
    results = []
    for parsed in device_codes:
        code = str(parsed.value)
        valid = is_valid_device_code(code)
        results.append(ValidationResult(
            field_name="device_code",
            expected="in DEVICE_CODES.md",
            actual=code,
            passed=valid,
            message=f"Device code {code}: {'valid' if valid else 'NOT FOUND in catalog'}"
        ))
    return results


# =============================================================================
# RULE CHECKERS - Check for specific standards compliance
# =============================================================================

def check_vd_limit_mentioned(answer: str) -> Tuple[bool, str]:
    """Check if answer mentions the 3% VD limit."""
    patterns = [
        r'3\s*%',
        r'สาม\s*เปอร์เซ็นต์',
        r'three\s*percent',
        r'≤\s*3',
    ]
    
    for pattern in patterns:
        if re.search(pattern, answer, re.IGNORECASE):
            return True, "VD limit 3% mentioned"
    return False, "VD limit 3% NOT mentioned"


def check_80_percent_rule_mentioned(answer: str) -> Tuple[bool, str]:
    """Check if answer mentions the 80% continuous load rule."""
    patterns = [
        r'80\s*%',
        r'แปดสิบ\s*เปอร์เซ็นต์',
        r'eighty\s*percent',
        r'continuous load',
        r'โหลดต่อเนื่อง',
    ]
    
    for pattern in patterns:
        if re.search(pattern, answer, re.IGNORECASE):
            return True, "80% rule mentioned"
    return False, "80% rule NOT mentioned"


def check_rcd_requirement_mentioned(answer: str, location_type: str) -> Tuple[bool, str]:
    """Check if answer correctly mentions RCD requirement for location."""
    rcd_req = RCD_REQUIREMENTS.get(location_type, {})
    
    if not rcd_req.get("required", False):
        return True, f"RCD not required for {location_type}"
    
    sensitivity = rcd_req.get("sensitivity_ma", 30)
    patterns = [
        rf'{sensitivity}\s*mA',
        r'RCD|RCBO|เครื่องตัดไฟรั่ว',
    ]
    
    for pattern in patterns:
        if re.search(pattern, answer, re.IGNORECASE):
            return True, f"RCD {sensitivity}mA mentioned for {location_type}"
    return False, f"RCD requirement for {location_type} NOT mentioned"


def check_standard_reference(answer: str, sources: List[Dict]) -> Tuple[bool, str]:
    """Check if answer references appropriate standards."""
    standard_refs = ["วสท", "EIT", "IEC", "60364", "2564"]
    
    answer_has_ref = any(ref in answer for ref in standard_refs)
    source_has_ref = any(
        any(ref in str(src) for ref in standard_refs)
        for src in sources
    )
    
    if answer_has_ref or source_has_ref:
        return True, "Standard reference found"
    return False, "No standard reference (วสท/IEC) found"


# =============================================================================
# MAIN LAYER 1 RUNNER
# =============================================================================

def run_layer1(
    answer: str,
    sources: List[Dict[str, Any]],
    test_case_type: str,
    ground_truth_params: Dict[str, Any]
) -> Layer1Result:
    """
    Run Layer 1 rule-based checks.
    
    Args:
        answer: The answer text from LLM
        sources: List of source documents
        test_case_type: Type of test case (ampacity, voltage_drop, breaker, derating, device_code)
        ground_truth_params: Parameters for ground truth lookup
            For ampacity: {"wire_size_mm2": 2.5, "insulation": "THW", "in_conduit": True}
            For voltage_drop: {"expected_vd_percent": 2.5} or {"max_allowed": 3.0}
            For breaker: {"load_current_a": 18}
            For derating: {"factor_type": "conductor_grouping", "condition_value": 6}
            For device_code: {} (codes extracted from answer)
    
    Returns:
        Layer1Result
    """
    validations: List[ValidationResult] = []
    parsed_values: Dict[str, ParsedValue] = {}
    errors: List[str] = []
    warnings: List[str] = []
    
    # --- AMPACITY CHECK ---
    if test_case_type == "ampacity":
        parsed = parse_ampacity_from_answer(answer)
        if parsed:
            parsed_values["ampacity"] = parsed
            wire_size = ground_truth_params.get("wire_size_mm2", 2.5)
            insulation = CableInsulation(ground_truth_params.get("insulation", "THW"))
            in_conduit = ground_truth_params.get("in_conduit", True)
            tolerance = ground_truth_params.get("tolerance_percent", 5.0)
            
            result = validate_ampacity(parsed, wire_size, insulation, in_conduit, tolerance)
            validations.append(result)
        else:
            errors.append("Could not parse ampacity value from answer")
    
    # --- VOLTAGE DROP CHECK ---
    elif test_case_type == "voltage_drop":
        parsed = parse_voltage_drop_from_answer(answer)
        if parsed:
            parsed_values["voltage_drop"] = parsed
            expected_vd = ground_truth_params.get("expected_vd_percent")
            max_allowed = ground_truth_params.get("max_allowed", 3.0)
            tolerance = ground_truth_params.get("tolerance_percent", 0.2)
            
            result = validate_voltage_drop(parsed, expected_vd, max_allowed, tolerance)
            validations.append(result)
            
            # Also check if limit is mentioned
            mentioned, msg = check_vd_limit_mentioned(answer)
            if not mentioned:
                warnings.append(msg)
        else:
            errors.append("Could not parse voltage drop from answer")
    
    # --- BREAKER SELECTION CHECK ---
    elif test_case_type == "breaker":
        parsed = parse_breaker_rating_from_answer(answer)
        if parsed:
            parsed_values["breaker"] = parsed
            load_current = ground_truth_params.get("load_current_a", 16)
            
            result = validate_breaker_selection(parsed, load_current)
            validations.append(result)
            
            # Check 80% rule mentioned
            mentioned, msg = check_80_percent_rule_mentioned(answer)
            if not mentioned:
                warnings.append(msg)
        else:
            errors.append("Could not parse breaker rating from answer")
    
    # --- DERATING FACTOR CHECK ---
    elif test_case_type == "derating":
        parsed = parse_derating_factor_from_answer(answer)
        if parsed:
            parsed_values["derating"] = parsed
            factor_type = ground_truth_params.get("factor_type", "conductor_grouping")
            condition_value = ground_truth_params.get("condition_value", 6)
            tolerance = ground_truth_params.get("tolerance", 0.05)
            
            result = validate_derating_factor(parsed, factor_type, condition_value, tolerance)
            validations.append(result)
        else:
            errors.append("Could not parse derating factor from answer")
    
    # --- DEVICE CODE CHECK ---
    elif test_case_type == "device_code":
        codes = parse_device_code_from_answer(answer)
        if codes:
            for code in codes:
                parsed_values[f"device_{code.value}"] = code
            code_results = validate_device_codes(codes)
            validations.extend(code_results)
        else:
            warnings.append("No device codes found in answer (may be expected)")
    
    # --- RCD CHECK ---
    elif test_case_type == "rcd":
        location_type = ground_truth_params.get("location_type", "bathroom")
        mentioned, msg = check_rcd_requirement_mentioned(answer, location_type)
        validations.append(ValidationResult(
            field_name="rcd_requirement",
            expected=f"RCD for {location_type}",
            actual="mentioned" if mentioned else "not mentioned",
            passed=mentioned,
            message=msg
        ))
    
    # --- Standard Reference Check (always run) ---
    ref_found, ref_msg = check_standard_reference(answer, sources)
    if not ref_found:
        warnings.append(ref_msg)
    
    # --- Determine Verdict ---
    failed_validations = [v for v in validations if not v.passed]
    
    if errors:
        verdict = Layer1Verdict.SOFT_FAIL
    elif failed_validations:
        # Check severity - wrong ampacity/VD calc is worse than missing device code
        critical_fails = [v for v in failed_validations if v.field_name in ["ampacity", "voltage_drop", "breaker_rating"]]
        if critical_fails:
            verdict = Layer1Verdict.HARD_FAIL
        else:
            verdict = Layer1Verdict.SOFT_FAIL
    else:
        verdict = Layer1Verdict.PASS
    
    return Layer1Result(
        verdict=verdict,
        validations=validations,
        parsed_values=parsed_values,
        errors=errors,
        warnings=warnings
    )
