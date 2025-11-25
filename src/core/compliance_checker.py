"""Compliance checker for verifying electrical design standards."""

from src.models.baseline import BaselineContext


class ComplianceChecker:
    """Verifies electrical design compliance with NEC/EIT standards."""

    # Voltage drop limits per NEC 210.19(A) Informational Note 4
    MAX_BRANCH_VD_PCT = 3.0  # 3% for branch circuits
    MAX_FEEDER_VD_PCT = 3.0  # 3% for feeders
    MAX_TOTAL_VD_PCT = 5.0  # 5% total (branch + feeder)

    def check_circuit_compliance(
        self,
        voltage_drop_pct: float,
        breaker_rating_a: float,
        design_current_a: float,
        wire_size_sqmm: float,
    ) -> tuple[bool, list[str]]:
        """Check compliance for a single circuit.
        
        Args:
            voltage_drop_pct: Calculated voltage drop percentage.
            breaker_rating_a: Selected breaker rating.
            design_current_a: Design current (Ib).
            wire_size_sqmm: Selected wire size.
            
        Returns:
            Tuple of (is_compliant, list_of_notes).
        """
        compliant = True
        notes: list[str] = []

        # Check voltage drop
        if voltage_drop_pct > self.MAX_BRANCH_VD_PCT:
            compliant = False
            notes.append(
                f"Voltage drop {voltage_drop_pct:.2f}% exceeds {self.MAX_BRANCH_VD_PCT}% limit"
            )
        elif voltage_drop_pct > self.MAX_BRANCH_VD_PCT * 0.9:
            notes.append(
                f"Warning: Voltage drop {voltage_drop_pct:.2f}% approaching limit"
            )

        # Check breaker vs current (In >= Ib)
        if breaker_rating_a < design_current_a:
            compliant = False
            notes.append(
                f"Breaker rating {breaker_rating_a}A < design current {design_current_a:.2f}A"
            )

        # Check minimum wire size for breaker rating
        min_wire_for_breaker = self._get_min_wire_for_breaker(breaker_rating_a)
        if wire_size_sqmm < min_wire_for_breaker:
            notes.append(
                f"Warning: Wire {wire_size_sqmm}mm² may be undersized for "
                f"{breaker_rating_a}A breaker (recommend >= {min_wire_for_breaker}mm²)"
            )

        return compliant, notes

    def _get_min_wire_for_breaker(self, breaker_rating_a: float) -> float:
        """Get minimum recommended wire size for breaker rating.
        
        Args:
            breaker_rating_a: Breaker rating in amperes.
            
        Returns:
            Minimum wire size in sq mm.
        """
        # Based on NEC/EIT ampacity tables for THW copper
        wire_breaker_map = [
            (1.5, 10),
            (2.5, 16),
            (4.0, 20),
            (6.0, 32),
            (10.0, 40),
            (16.0, 63),
            (25.0, 80),
            (35.0, 100),
        ]

        for wire_size, max_breaker in wire_breaker_map:
            if breaker_rating_a <= max_breaker:
                return wire_size

        return 35.0  # Default to largest common size

    def check(self, context: BaselineContext) -> BaselineContext:
        """Check compliance for all circuits and update context.
        
        Args:
            context: BaselineContext with calculated values.
            
        Returns:
            Updated BaselineContext with compliance status.
        """
        overall_compliant = True
        project_notes: list[str] = []

        # Check each circuit
        for room in context.rooms:
            for circuit in room.circuits:
                compliant, notes = self.check_circuit_compliance(
                    voltage_drop_pct=circuit.voltage_drop_pct,
                    breaker_rating_a=circuit.breaker_rating_a,
                    design_current_a=circuit.design_current_a,
                    wire_size_sqmm=circuit.wire_size_sqmm,
                )

                circuit.compliant = compliant
                circuit.compliance_notes = notes

                if not compliant:
                    overall_compliant = False
                    project_notes.append(
                        f"Circuit {circuit.circuit_id}: Non-compliant"
                    )

        # Check total voltage drop (simplified - assumes series path)
        max_vd = 0.0
        for room in context.rooms:
            for circuit in room.circuits:
                max_vd = max(max_vd, circuit.voltage_drop_pct)

        if max_vd > self.MAX_TOTAL_VD_PCT:
            overall_compliant = False
            project_notes.append(
                f"Maximum voltage drop {max_vd:.2f}% exceeds {self.MAX_TOTAL_VD_PCT}% total limit"
            )

        # Update context
        context.overall_compliant = overall_compliant
        context.compliance_notes = project_notes

        return context
