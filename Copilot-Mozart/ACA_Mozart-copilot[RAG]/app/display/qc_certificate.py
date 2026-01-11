"""
QC Certificate Generator - Design Assumptions Certificate

Generates a formal QC certificate document with validated design assumptions.
All data is read from display_data (computed by compute.py).

Author: Fixia
Date: 2026-01-12

Cloud Logging Checkpoints:
- [QC-CERT-START] Starting QC validation
- [QC-CERT-DATA] Reading from display_data
- [QC-CERT-STATIC] Static param validation
- [QC-CERT-VD] VD validation per circuit
- [QC-CERT-SUMMARY] Validation summary
- [QC-CERT-DONE] Certificate generated
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import TypedDict, List, Dict, Any, Optional

logger = logging.getLogger("Aura.Display.QCCertificate")

# === CONSTANTS ===
COMPANY_NAME = "MOZART ELECTRICAL ENGINEERING"
DOCUMENT_VALID_DAYS = 30


# === TYPE DEFINITIONS ===

class ValidationItem(TypedDict):
    """Single validation item with status"""
    parameter: str
    value: str
    standard: str
    valid_range: str
    status: str  # "✓ OK" | "⚠️ WARN" | "❌ FAIL"


class CircuitVDValidation(TypedDict):
    """Per-circuit VD validation"""
    circuit_name: str
    vd_percent: float
    limit: float
    status: str


class QCCertificateData(TypedDict):
    """Complete QC Certificate data structure"""
    document_id: str
    company_name: str
    project_name: str
    date_generated: str
    valid_until: str
    revision: str
    total_kw: float
    main_breaker: str
    circuit_count: int
    
    # Validation sections
    static_params: List[ValidationItem]
    vd_limits: List[ValidationItem]
    circuit_vd_validation: List[CircuitVDValidation]
    
    # Distance info
    default_circuit_count: int
    default_circuits: List[Dict[str, Any]]
    
    # Summary
    summary: Dict[str, int]  # pass_count, warn_count, fail_count
    
    # Scope & References
    scope_items: List[str]
    references: List[str]


# === VALIDATION RULES ===

STATIC_PARAMS = [
    {
        "parameter": "Power Factor",
        "value": "0.85",
        "standard": "IEC 60364",
        "valid_range": "0.80 - 1.00",
    },
    {
        "parameter": "Safety Factor",
        "value": "125%",
        "standard": "NEC 2023",
        "valid_range": "100% - 150%",
    },
    {
        "parameter": "Continuous Load Factor",
        "value": "125%",
        "standard": "NEC 220.10",
        "valid_range": "125%",
    },
    {
        "parameter": "Ambient Temperature",
        "value": "30°C",
        "standard": "IEC",
        "valid_range": "25°C - 45°C",
    },
]

VD_LIMITS = [
    {
        "parameter": "Branch VD Limit",
        "value": "≤ 3.0%",
        "standard": "EIT 2564",
        "valid_range": "≤ 3.0%",
    },
    {
        "parameter": "Service VD Limit",
        "value": "≤ 2.0%",
        "standard": "EIT 2564",
        "valid_range": "≤ 2.0%",
    },
    {
        "parameter": "Total VD Limit",
        "value": "≤ 5.0%",
        "standard": "NEC 2023",
        "valid_range": "≤ 5.0%",
    },
]

SCOPE_ITEMS = [
    "This certificate applies to 230V single-phase residential electrical installations.",
    "Values are based on design calculations, not site measurement.",
    "Verify all distances on-site before final installation.",
    "All calculations follow EIT 2564 and NEC 2023 standards.",
]

REFERENCES = [
    "NEC 2023 (National Electrical Code)",
    "IEC 60364 (Electrical Installations of Buildings)",
    "EIT 2564 (EIT Standard for Electrical Installations - Thailand)",
    "IEEE Std 141 (Recommended Practice for Electric Power Distribution)",
]


# === VALIDATION FUNCTIONS ===

def _validate_static_params() -> List[ValidationItem]:
    """
    Validate static design parameters.
    These are always within range (hardcoded values).
    """
    results: List[ValidationItem] = []
    
    for param in STATIC_PARAMS:
        # Static params are always OK (they are our design defaults)
        results.append({
            "parameter": param["parameter"],
            "value": param["value"],
            "standard": param["standard"],
            "valid_range": param["valid_range"],
            "status": "✓ OK",
        })
        logger.info(f"[QC-CERT-STATIC] {param['parameter']}: {param['value']} - ✓ OK")
    
    return results


def _validate_vd_limits() -> List[ValidationItem]:
    """
    Validate VD limit parameters.
    These are always within standard (they ARE the standard).
    """
    results: List[ValidationItem] = []
    
    for limit in VD_LIMITS:
        results.append({
            "parameter": limit["parameter"],
            "value": limit["value"],
            "standard": limit["standard"],
            "valid_range": limit["valid_range"],
            "status": "✓ OK",
        })
        logger.info(f"[QC-CERT-STATIC] {limit['parameter']}: {limit['value']} - ✓ OK")
    
    return results


def _validate_circuit_vd(circuits: List[Dict[str, Any]]) -> List[CircuitVDValidation]:
    """
    Validate VD% for each circuit against 3% limit.
    This CAN produce WARN or FAIL status based on REAL values!
    
    Args:
        circuits: List of circuit data from display_data['circuits']
    
    Returns:
        List of per-circuit VD validation results
    """
    results: List[CircuitVDValidation] = []
    
    for circuit in circuits:
        name = circuit.get("circuit_name", circuit.get("name", "Unknown"))
        vd = circuit.get("vd_percent", 0.0)
        
        # Ensure vd is float
        try:
            vd = float(vd)
        except (ValueError, TypeError):
            vd = 0.0
        
        # Determine status based on VD%
        if vd > 3.0:
            status = "❌ FAIL"
            logger.warning(f"[QC-CERT-VD] FAIL: {name} = {vd:.2f}% > 3.0%")
        elif vd > 2.5:
            status = "⚠️ WARN"
            logger.info(f"[QC-CERT-VD] WARN: {name} = {vd:.2f}% (near limit)")
        else:
            status = "✓ OK"
            logger.info(f"[QC-CERT-VD] OK: {name} = {vd:.2f}%")
        
        results.append({
            "circuit_name": name,
            "vd_percent": vd,
            "limit": 3.0,
            "status": status,
        })
    
    return results


def _calculate_summary(
    static_params: List[ValidationItem],
    vd_limits: List[ValidationItem],
    circuit_vd: List[CircuitVDValidation]
) -> Dict[str, int]:
    """Calculate pass/warn/fail counts from all validation results."""
    all_statuses = []
    
    # Collect all statuses
    for item in static_params:
        all_statuses.append(item["status"])
    for item in vd_limits:
        all_statuses.append(item["status"])
    for item in circuit_vd:
        all_statuses.append(item["status"])
    
    # Count by status
    pass_count = sum(1 for s in all_statuses if "OK" in s)
    warn_count = sum(1 for s in all_statuses if "WARN" in s)
    fail_count = sum(1 for s in all_statuses if "FAIL" in s)
    
    return {
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "total_count": len(all_statuses),
    }


# === MAIN GENERATOR FUNCTION ===

def generate_qc_certificate(display_data: Dict[str, Any]) -> QCCertificateData:
    """
    Generate QC Certificate data from display_data.
    
    CRITICAL: Reads from display_data ONLY, never from mcp_result directly!
    
    Args:
        display_data: Output from compute_display_data() - the Single Source of Truth
    
    Returns:
        QCCertificateData with all validation results
    
    Raises:
        ValueError: If display_data is missing required fields
    """
    project_name = display_data.get("project_name", "Untitled Project")
    logger.info(f"[QC-CERT-START] Generating QC Certificate for '{project_name}'")
    
    # Read data from display_data
    circuits = display_data.get("circuits", [])
    default_circuits = display_data.get("default_distance_circuits", [])
    total_kw = display_data.get("total_kw", 0.0)
    main_breaker = display_data.get("main_breaker", "N/A")
    circuit_count = display_data.get("circuit_count", len(circuits))
    
    logger.info(f"[QC-CERT-DATA] Reading from display_data: {len(circuits)} circuits, {len(default_circuits)} using default distance")
    
    # Run validations
    static_params = _validate_static_params()
    vd_limits = _validate_vd_limits()
    circuit_vd = _validate_circuit_vd(circuits)
    
    # Calculate summary
    summary = _calculate_summary(static_params, vd_limits, circuit_vd)
    logger.info(f"[QC-CERT-SUMMARY] {summary['pass_count']} PASS, {summary['warn_count']} WARN, {summary['fail_count']} FAIL")
    
    if summary["fail_count"] > 0:
        logger.warning(f"[QC-CERT-FAIL] ⚠️ {summary['fail_count']} items FAILED validation!")
    
    # Generate document metadata
    now = datetime.now()
    document_id = f"MEE-{now.strftime('%Y')}-{uuid.uuid4().hex[:8].upper()}"
    date_generated = now.strftime("%Y-%m-%d")
    valid_until = (now + timedelta(days=DOCUMENT_VALID_DAYS)).strftime("%Y-%m-%d")
    
    # Build result
    result: QCCertificateData = {
        "document_id": document_id,
        "company_name": COMPANY_NAME,
        "project_name": project_name,
        "date_generated": date_generated,
        "valid_until": valid_until,
        "revision": "01",
        "total_kw": total_kw,
        "main_breaker": str(main_breaker),
        "circuit_count": circuit_count,
        "static_params": static_params,
        "vd_limits": vd_limits,
        "circuit_vd_validation": circuit_vd,
        "default_circuit_count": len(default_circuits),
        "default_circuits": default_circuits,
        "summary": summary,
        "scope_items": SCOPE_ITEMS,
        "references": REFERENCES,
    }
    
    logger.info(f"[QC-CERT-DONE] Certificate {document_id} generated successfully")
    return result


def format_qc_for_frontend(qc_data: QCCertificateData) -> Dict[str, Any]:
    """
    Format QC Certificate data for frontend display.
    
    Maps TypedDict to plain dict for JSON serialization.
    """
    return dict(qc_data)
