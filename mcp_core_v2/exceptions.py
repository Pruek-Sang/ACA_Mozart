"""Custom exceptions for MCP Core v2."""

class MCPError(Exception):
    """Base exception for all MCP errors."""
    pass


class InvalidSpecError(MCPError):
    """Raised when project specification is invalid or incomplete."""
    pass


class UnsupportedProjectError(MCPError):
    """Raised when project type is not supported by MCP."""
    pass


class CatalogLookupError(MCPError):
    """Raised when catalog item cannot be found."""
    pass


class SimulationError(MCPError):
    """Raised when electrical simulation fails."""
    pass


class ComplianceError(MCPError):
    """Raised when design violates electrical standards."""
    pass


class ValidationError(MCPError):
    """Raised when input validation fails."""
    pass


# ============================================================================
# 3-Phase Specific Errors (Sprint 1 - Threshold Detection)
# Error Code: 3PH-001 to 3PH-005
# ============================================================================

class ThreePhaseRequiredError(MCPError):
    """
    Error Code: 3PH-001
    Raised when connected load exceeds 25kW but user specified 1-Phase system.
    
    วสท. 2564: โหลดรวมเกิน 25kW ต้องใช้ระบบ 3 เฟส
    Thai EIT Standard: Total load > 25kW requires 3-phase system
    """
    error_code = "3PH-001"
    
    def __init__(self, connected_load_kw: float, threshold_kw: float = 25.0, message: str = None):
        self.connected_load_kw = connected_load_kw
        self.threshold_kw = threshold_kw
        self.message = message or (
            f"[{self.error_code}] โหลดรวม {connected_load_kw:.2f} kW เกินขีดจำกัด {threshold_kw} kW "
            f"สำหรับระบบ 1 เฟส ต้องใช้ระบบ 3 เฟส (วสท. 2564)"
        )
        super().__init__(self.message)


class PhaseBalanceWarning(MCPError):
    """
    Error Code: 3PH-002
    Warning when phase imbalance exceeds 15%.
    
    วสท. 2564: Imbalance ระหว่าง phase ไม่ควรเกิน 15%
    """
    error_code = "3PH-002"
    
    def __init__(self, imbalance_percent: float, threshold_percent: float = 15.0, message: str = None):
        self.imbalance_percent = imbalance_percent
        self.threshold_percent = threshold_percent
        self.message = message or (
            f"[{self.error_code}] Phase imbalance {imbalance_percent:.1f}% เกินค่าที่แนะนำ {threshold_percent}% "
            f"(วสท. 2564 แนะนำไม่เกิน 15%)"
        )
        super().__init__(self.message)


class PhaseDataInconsistencyError(MCPError):
    """
    Error Code: 3PH-003
    Raised when 1-Phase system has L2/L3 data (data contamination).
    
    ป้องกันข้อมูล 1-Phase และ 3-Phase ปนกัน
    """
    error_code = "3PH-003"
    
    def __init__(self, phase_system: str, has_l2: bool, has_l3: bool, message: str = None):
        self.phase_system = phase_system
        self.has_l2 = has_l2
        self.has_l3 = has_l3
        self.message = message or (
            f"[{self.error_code}] ระบบ {phase_system} มีข้อมูล "
            f"{'L2 ' if has_l2 else ''}{'L3 ' if has_l3 else ''}ซึ่งไม่ควรมี (Data Contamination)"
        )
        super().__init__(self.message)


class IncompleteThreePhaseError(MCPError):
    """
    Error Code: 3PH-004
    Raised when 3-Phase system lacks phase balance data.
    
    ระบบ 3 เฟสต้องมีข้อมูล phase balance
    """
    error_code = "3PH-004"
    
    def __init__(self, missing_fields: list = None, message: str = None):
        self.missing_fields = missing_fields or []
        self.message = message or (
            f"[{self.error_code}] ระบบ 3 เฟสขาดข้อมูล: {', '.join(self.missing_fields) or 'phase_balance'}"
        )
        super().__init__(self.message)


class PolesMismatchError(MCPError):
    """
    Error Code: 3PH-005
    Raised when breaker poles don't match voltage system.
    
    เช่น ระบบ 3 เฟส แต่ main breaker เป็น 2P
    """
    error_code = "3PH-005"
    
    def __init__(self, expected_poles: int, actual_poles: int, voltage_system: str, message: str = None):
        self.expected_poles = expected_poles
        self.actual_poles = actual_poles
        self.voltage_system = voltage_system
        self.message = message or (
            f"[{self.error_code}] ระบบ {voltage_system} ต้องใช้ breaker {expected_poles}P "
            f"แต่กำหนดเป็น {actual_poles}P"
        )
        super().__init__(self.message)
