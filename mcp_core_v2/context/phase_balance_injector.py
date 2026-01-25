"""
Phase Balance Injector
======================
PRE-pipeline injector for 3-phase load balancing.

📋 PURPOSE:
-----------
แบ่งโหลดให้สมดุลระหว่าง 3 phases (L1, L2, L3) ตาม วสท. 2564

📊 WHEN TO USE:
--------------
- service_voltage = THREE_PHASE_380V หรือ THREE_PHASE_400V
- total_power_kw > 12 kW (เกิน 1 phase limit)
- user ระบุ phase_balance = True

📐 ALGORITHM:
-------------
1. Sort loads by power (descending) - Largest First Decreasing (LFD)
2. Assign each load to phase with lowest current total
3. Check imbalance: max_phase - min_phase ≤ 15% of average
4. If imbalance > 15%: redistribute หรือ warn user

Author: Mozart AI - Sprint 2 Implementation
Date: 2026-01-25
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class PhaseBalanceResult:
    """Result of phase balance operation."""
    is_balanced: bool
    imbalance_percent: float
    phase_assignments: Dict[str, List[str]]  # {"L1": [load_ids...], "L2": [...], "L3": [...]}
    phase_totals: Dict[str, float]  # {"L1": watts, "L2": watts, "L3": watts}
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'is_balanced': self.is_balanced,
            'imbalance_percent': round(self.imbalance_percent, 2),
            'phase_assignments': self.phase_assignments,
            'phase_totals': {k: round(v, 2) for k, v in self.phase_totals.items()},
            'warnings': self.warnings
        }


class PhaseBalanceInjector:
    """
    PRE-pipeline injector for 3-phase load balancing.
    
    [CP-3PH-BALANCE] Cloud logging checkpoint prefix.
    
    Usage:
        injector = PhaseBalanceInjector(max_imbalance_percent=15.0)
        result = injector.inject(request)
    """
    
    # ════════════════════════════════════════════════════════════════════════
    # CONFIGURABLE CONSTANTS
    # ════════════════════════════════════════════════════════════════════════
    
    DEFAULT_MAX_IMBALANCE = 15.0  # วสท. 2564 recommends ≤15%
    SINGLE_PHASE_MAX_KW = 12.0   # Max load per single phase
    VOLTAGE_3PH_LINE = 400.0     # Thai standard line-to-line voltage
    VOLTAGE_3PH_PHASE = 230.0    # Thai standard line-to-neutral voltage
    
    # ════════════════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ════════════════════════════════════════════════════════════════════════
    
    def __init__(self, max_imbalance_percent: float = DEFAULT_MAX_IMBALANCE):
        """
        Initialize the Phase Balance Injector.
        
        Args:
            max_imbalance_percent: Maximum allowed imbalance between phases (default: 15%)
        """
        self.max_imbalance = max_imbalance_percent
        logger.info(f"[CP-3PH-BALANCE] PhaseBalanceInjector initialized with max_imbalance={max_imbalance_percent}%")
    
    # ════════════════════════════════════════════════════════════════════════
    # MAIN INJECT METHOD
    # ════════════════════════════════════════════════════════════════════════
    
    def inject(self, request: Any) -> PhaseBalanceResult:
        """
        Main injection point - balance loads across 3 phases.
        
        [CP-3PH-BALANCE] Cloud logging checkpoint.
        
        Algorithm (Largest First Decreasing - LFD):
        1. Check if request requires 3-phase balancing
        2. Sort loads by power (Largest First Decreasing)
        3. Assign loads to phases using greedy algorithm
        4. Check imbalance and rebalance if needed
        5. Add assigned_phase to each load
        6. Return PhaseBalanceResult
        
        Args:
            request: DesignRequest with loads
            
        Returns:
            PhaseBalanceResult with phase assignments and balance info
        """
        logger.info("[CP-3PH-BALANCE] Starting phase balance injection...")
        
        # Step 1: Check if 3-phase balancing is needed
        if not self._is_three_phase(request):
            logger.info("[CP-3PH-BALANCE] Not a 3-phase system, skipping balance")
            return PhaseBalanceResult(
                is_balanced=True,
                imbalance_percent=0.0,
                phase_assignments={"L1": [], "L2": [], "L3": []},
                phase_totals={"L1": 0.0, "L2": 0.0, "L3": 0.0},
                warnings=[]
            )
        
        loads = request.loads if hasattr(request, 'loads') else []
        if not loads:
            logger.warning("[CP-3PH-BALANCE] No loads to balance")
            return PhaseBalanceResult(
                is_balanced=True,
                imbalance_percent=0.0,
                phase_assignments={"L1": [], "L2": [], "L3": []},
                phase_totals={"L1": 0.0, "L2": 0.0, "L3": 0.0},
                warnings=["No loads provided for balancing"]
            )
        
        # Step 2: Sort loads by power (descending)
        sorted_loads = self._sort_loads_by_power(loads)
        logger.info(f"[CP-3PH-BALANCE] Sorted {len(sorted_loads)} loads for balancing")
        
        # Step 3: Assign to phases using greedy LFD
        phase_assignments, phase_totals = self._assign_to_phases(sorted_loads)
        
        # Step 4: Calculate imbalance
        imbalance = self._calculate_imbalance(phase_totals)
        logger.info(f"[CP-3PH-BALANCE] Initial imbalance: {imbalance:.2f}%")
        
        # Step 5: Check if rebalancing needed
        warnings = []
        is_balanced = imbalance <= self.max_imbalance
        
        if not is_balanced:
            logger.warning(f"[CP-3PH-BALANCE] Imbalance {imbalance:.2f}% exceeds threshold {self.max_imbalance}%")
            
            # Try to rebalance
            phase_assignments, phase_totals = self._rebalance_if_needed(
                phase_assignments, phase_totals, loads
            )
            imbalance = self._calculate_imbalance(phase_totals)
            is_balanced = imbalance <= self.max_imbalance
            
            if not is_balanced:
                warning_msg = (
                    f"⚠️ [3PH-002] Phase imbalance {imbalance:.1f}% เกินค่าที่แนะนำ {self.max_imbalance}% "
                    f"(วสท. 2564 แนะนำไม่เกิน 15%)"
                )
                warnings.append(warning_msg)
                logger.warning(f"[CP-3PH-BALANCE] {warning_msg}")
        
        # Step 6: Assign phase to each load object
        self._apply_phase_assignments(loads, phase_assignments)
        
        # Log phase totals
        for phase, total in phase_totals.items():
            logger.info(f"[CP-3PH-BALANCE] {phase}: {total:.2f}W ({len(phase_assignments[phase])} loads)")
        
        result = PhaseBalanceResult(
            is_balanced=is_balanced,
            imbalance_percent=imbalance,
            phase_assignments=phase_assignments,
            phase_totals=phase_totals,
            warnings=warnings
        )
        
        logger.info(
            f"[CP-3PH-BALANCE] Complete: balanced={is_balanced}, imbalance={imbalance:.2f}%, "
            f"L1={phase_totals['L1']:.0f}W, L2={phase_totals['L2']:.0f}W, L3={phase_totals['L3']:.0f}W"
        )
        
        return result
    
    # ════════════════════════════════════════════════════════════════════════
    # PRIVATE HELPER METHODS
    # ════════════════════════════════════════════════════════════════════════
    
    def _is_three_phase(self, request: Any) -> bool:
        """
        Check if request requires 3-phase balancing.
        
        Args:
            request: DesignRequest object
            
        Returns:
            True if 3-phase system
        """
        if not hasattr(request, 'service_voltage'):
            return False
        
        voltage = request.service_voltage
        voltage_str = voltage.value if hasattr(voltage, 'value') else str(voltage)
        
        is_3phase = '3PH' in voltage_str.upper() or 'THREE' in voltage_str.upper()
        logger.info(f"[CP-3PH-BALANCE] Voltage check: {voltage_str} -> is_3phase={is_3phase}")
        
        return is_3phase
    
    def _sort_loads_by_power(self, loads: List[Any]) -> List[Any]:
        """
        Sort loads by power in descending order (Largest First Decreasing).
        
        Args:
            loads: List of ElectricalLoad objects
            
        Returns:
            Sorted list of loads (largest power first)
        """
        def get_total_power(load) -> float:
            power = getattr(load, 'power_watts', 0) or 0
            qty = getattr(load, 'quantity', 1) or 1
            return power * qty
        
        return sorted(loads, key=get_total_power, reverse=True)
    
    def _assign_to_phases(self, loads: List[Any]) -> Tuple[Dict[str, List[str]], Dict[str, float]]:
        """
        Assign each load to the phase with lowest total power.
        
        Algorithm (Greedy LFD - Largest First Decreasing):
        1. Initialize L1, L2, L3 = 0
        2. For each load (sorted by power, descending):
           - Find phase with minimum current total
           - Assign load to that phase
           - Add load power to phase total
        
        Args:
            loads: Sorted list of loads (largest first)
            
        Returns:
            Tuple of (phase_assignments dict, phase_totals dict)
        """
        phase_assignments: Dict[str, List[str]] = {"L1": [], "L2": [], "L3": []}
        phase_totals: Dict[str, float] = {"L1": 0.0, "L2": 0.0, "L3": 0.0}
        
        for load in loads:
            load_id = getattr(load, 'id', str(id(load)))
            power = getattr(load, 'power_watts', 0) or 0
            qty = getattr(load, 'quantity', 1) or 1
            total_power = power * qty
            
            # Find phase with minimum total (use default param to capture current value)
            min_phase = min(phase_totals.keys(), key=lambda k, pt=phase_totals: pt[k])
            
            # Assign load to that phase
            phase_assignments[min_phase].append(load_id)
            phase_totals[min_phase] += total_power
            
            logger.debug(
                f"[CP-3PH-BALANCE] Assigned load {load_id} ({total_power:.0f}W) to {min_phase} "
                f"(total now: {phase_totals[min_phase]:.0f}W)"
            )
        
        return phase_assignments, phase_totals
    
    def _calculate_imbalance(self, phase_totals: Dict[str, float]) -> float:
        """
        Calculate imbalance percentage.
        
        Formula: (max_phase - min_phase) / average * 100
        
        Args:
            phase_totals: Dict with L1, L2, L3 totals in watts
            
        Returns:
            Imbalance percentage (0-100)
        """
        values = list(phase_totals.values())
        
        if not values or all(v == 0 for v in values):
            return 0.0
        
        max_val = max(values)
        min_val = min(values)
        avg_val = sum(values) / len(values)
        
        if avg_val == 0:
            return 0.0
        
        imbalance = ((max_val - min_val) / avg_val) * 100
        return imbalance
    
    def _rebalance_if_needed(
        self, 
        phase_assignments: Dict[str, List[str]], 
        phase_totals: Dict[str, float],
        loads: List[Any]
    ) -> Tuple[Dict[str, List[str]], Dict[str, float]]:
        """
        Try to rebalance if imbalance > threshold.
        
        Strategy: Move smallest loads from heaviest phase to lightest phase.
        
        Args:
            phase_assignments: Current phase assignments
            phase_totals: Current phase totals
            loads: Original load list
            
        Returns:
            Updated (phase_assignments, phase_totals)
        """
        logger.info("[CP-3PH-BALANCE] Attempting rebalance...")
        
        # Create load lookup by ID
        load_lookup = {}
        for load in loads:
            load_id = getattr(load, 'id', str(id(load)))
            power = getattr(load, 'power_watts', 0) or 0
            qty = getattr(load, 'quantity', 1) or 1
            load_lookup[load_id] = power * qty
        
        # Try up to 10 iterations
        for iteration in range(10):
            current_imbalance = self._calculate_imbalance(phase_totals)
            if current_imbalance <= self.max_imbalance:
                logger.info(f"[CP-3PH-BALANCE] Rebalance successful after {iteration} iterations")
                break
            
            # Find heaviest and lightest phases (use default param to capture current value)
            heaviest = max(phase_totals.keys(), key=lambda k, pt=phase_totals: pt[k])
            lightest = min(phase_totals.keys(), key=lambda k, pt=phase_totals: pt[k])
            
            # Find smallest load in heaviest phase that helps balance
            candidate_load_id = None
            candidate_power = float('inf')
            
            for load_id in phase_assignments[heaviest]:
                power = load_lookup.get(load_id, 0)
                if power < candidate_power and power > 0:
                    # Check if moving this load improves balance
                    new_light = phase_totals[lightest] + power
                    
                    # Only move if it doesn't make lightest become heaviest
                    if new_light < phase_totals[heaviest]:
                        candidate_load_id = load_id
                        candidate_power = power
            
            if candidate_load_id is None:
                logger.warning("[CP-3PH-BALANCE] No suitable load found for rebalance")
                break
            
            # Move the load
            phase_assignments[heaviest].remove(candidate_load_id)
            phase_assignments[lightest].append(candidate_load_id)
            phase_totals[heaviest] -= candidate_power
            phase_totals[lightest] += candidate_power
            
            logger.info(
                f"[CP-3PH-BALANCE] Moved load {candidate_load_id} ({candidate_power:.0f}W) "
                f"from {heaviest} to {lightest}"
            )
        
        return phase_assignments, phase_totals
    
    def _apply_phase_assignments(
        self, 
        loads: List[Any], 
        phase_assignments: Dict[str, List[str]]
    ) -> None:
        """
        Apply phase assignments to load objects.
        
        Modifies load objects in place by setting assigned_phase attribute.
        
        Args:
            loads: List of load objects
            phase_assignments: Dict mapping phase to load IDs
        """
        # Create reverse lookup: load_id -> phase
        load_to_phase = {}
        for phase, load_ids in phase_assignments.items():
            for load_id in load_ids:
                load_to_phase[load_id] = phase
        
        # Apply to load objects
        for load in loads:
            load_id = getattr(load, 'id', str(id(load)))
            assigned_phase = load_to_phase.get(load_id)
            
            if assigned_phase:
                try:
                    # Try direct assignment first
                    load.assigned_phase = assigned_phase
                except AttributeError:
                    # For Pydantic models, use object.__setattr__
                    try:
                        object.__setattr__(load, 'assigned_phase', assigned_phase)
                    except Exception as e:
                        logger.warning(f"[CP-3PH-BALANCE] Could not set assigned_phase for {load_id}: {e}")


# ════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ════════════════════════════════════════════════════════════════════════════

def get_phase_balance_injector(max_imbalance: float = 15.0) -> PhaseBalanceInjector:
    """
    Factory function to get PhaseBalanceInjector instance.
    
    Usage in pipeline.py:
        from context.phase_balance_injector import get_phase_balance_injector
        
        injector = get_phase_balance_injector()
        result = injector.inject(request)
    """
    return PhaseBalanceInjector(max_imbalance_percent=max_imbalance)
