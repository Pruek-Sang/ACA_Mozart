from typing import List, Dict, Any, Optional
import math

class LogicValidator:
    """
    Validates logical consistency and sanity of the electrical design.
    Acts as a 'Common Sense' layer before or after heavy calculations.
    """

    # Reasonable limits for residential devices
    DEVICE_LIMITS = {
        'air_conditioner': {'max_btu': 60000, 'max_kw': 7.0, 'warning_threshold_qty': 10},
        'water_heater': {'max_watts': 12000, 'max_kw': 12.0, 'warning_threshold_qty': 8},
        'ev_charger': {'max_kw': 22.0, 'warning_threshold_qty': 3},
    }

    def validate_sanity(self, loads: List[Dict[str, Any]]) -> List[str]:
        """
        Check for 'Fat Finger' errors or unrealistic numbers.
        Returns a list of warning messages.
        """
        warnings = []

        for i, load in enumerate(loads):
            device_name = load.get('device', '').lower()
            qty = load.get('quantity', 1)
            power_kw = load.get('power_kw', 0) or 0
            
            # 1. Fat Finger Check (e.g. 180,000 BTU instead of 18,000)
            # Heuristic: If power > 50kW for a single residential item, it's suspicious
            if power_kw > 50 and 'transformer' not in device_name:
                warnings.append(f"⚠️ Load '{device_name}' seems abnormally high ({power_kw} kW). Did you mean something smaller?")

            # 2. Device Specific Checks
            if 'air' in device_name or 'แอร์' in device_name:
                # Check BTU if available in name (parsing required)
                # Fallback to kW check
                if power_kw > self.DEVICE_LIMITS['air_conditioner']['max_kw']:
                     warnings.append(f"⚠️ Aircon '{device_name}' ({power_kw} kW) exceeds typical residential unit size (max 7kW).")
                
                if qty > self.DEVICE_LIMITS['air_conditioner']['warning_threshold_qty']:
                    warnings.append(f"ℹ️ Large number of Aircons ({qty} units). Ensure main service size is sufficient.")

            if 'water' in device_name or 'heater' in device_name or 'น้ำอุ่น' in device_name:
                 if power_kw > self.DEVICE_LIMITS['water_heater']['max_kw']:
                     warnings.append(f"⚠️ Water Heater '{device_name}' ({power_kw} kW) is unusually large.")

        return warnings

    def validate_transformer_capacity(self, total_kw: float, transformer_kva: Optional[float] = None) -> List[str]:
        """
        Check if total load fits within transformer or typical service entrance.
        """
        warnings = []
        
        # Power Factor assumption
        pf = 0.85 
        total_kva = total_kw / pf

        if transformer_kva:
            if total_kva > transformer_kva:
                percent = (total_kva / transformer_kva) * 100
                warnings.append(f"❌ **Overload Warning**: Total Load ({total_kva:.1f} kVA) exceeds Transformer Capacity ({transformer_kva} kVA) by {percent-100:.1f}%")
        else:
            # No transformer specified, check residential single phase limits
            # Typical max for 1-phase 30(100)A is ~22kVA
            if total_kva > 30 and total_kva < 100:
                 warnings.append(f"ℹ️ Load ({total_kva:.1f} kVA) is high for typical 1-phase service. Consider 3-phase or Transformer.")
            elif total_kva >= 100:
                 warnings.append(f"⚠️ Total Load ({total_kva:.1f} kVA) likely requires a dedicated Transformer.")

        return warnings

    def calculate_phase_balance(self, loads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Simulate phase balancing for 3-phase systems (A, B, C).
        Strategies:
        1. Sort largest to smallest
        2. Distribute via 'Snake' method or least-loaded phase
        """
        phases = {'A': 0.0, 'B': 0.0, 'C': 0.0}
        phase_assignments = [] 

        # Sort loads desc
        sorted_loads = sorted(loads, key=lambda x: x.get('power_kw', 0), reverse=True)

        for load in sorted_loads:
            kw = load.get('power_kw', 0)
            qty = load.get('quantity', 1)
            total_load_kw = kw * qty
            
            # Find phase with min load
            target_phase = min(phases, key=phases.get)
            phases[target_phase] += total_load_kw
            
            phase_assignments.append({
                'load': load.get('device'),
                'phase': target_phase,
                'kw': total_load_kw
            })

        # Calculate imbalance
        max_load = max(phases.values())
        min_load = min(phases.values())
        avg_load = sum(phases.values()) / 3
        
        if avg_load > 0:
            imbalance_percent = ((max_load - min_load) / avg_load) * 100
        else:
            imbalance_percent = 0

        warnings = []
        if imbalance_percent > 20:
            warnings.append(f"⚠️ **Phase Imbalance**: {imbalance_percent:.1f}% (Recommended < 20%). Check splitting large loads.")

        return {
            'phases': phases,
            'imbalance_percent': imbalance_percent,
            'assignments': phase_assignments,
            'warnings': warnings
        }
