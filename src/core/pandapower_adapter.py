"""Pandapower adapter for power flow analysis and voltage drop calculations."""

import math
from typing import Optional

import pandapower as pp

from src.models.baseline import BaselineContext


class PandapowerAdapter:
    """Adapter for creating pandapower networks and running power flow analysis."""

    def __init__(self):
        """Initialize the pandapower adapter."""
        self._network: Optional[pp.pandapowerNet] = None

    def create_network(self, context: BaselineContext) -> pp.pandapowerNet:
        """Create a pandapower network from baseline context.
        
        Creates a simplified radial network with:
        - External grid at source
        - Main bus
        - Branch circuits as loads
        
        Args:
            context: BaselineContext with circuit data.
            
        Returns:
            pandapower network ready for analysis.
        """
        # Create empty network
        net = pp.create_empty_network(name=context.project_name)

        # Create main bus (source)
        main_bus = pp.create_bus(
            net,
            vn_kv=context.nominal_voltage / 1000,
            name="Main_Bus",
        )

        # Create external grid connection
        pp.create_ext_grid(
            net,
            bus=main_bus,
            vm_pu=1.0,
            name="Grid",
        )

        # Process each room and circuit
        circuit_idx = 0
        for room in context.rooms:
            for circuit in room.circuits:
                circuit_idx += 1

                # Create bus for this circuit
                circuit_bus = pp.create_bus(
                    net,
                    vn_kv=circuit.voltage_v / 1000,
                    name=f"Bus_{circuit.circuit_id}",
                )

                # Create line (simplified impedance model)
                # Using length and wire properties
                length_km = circuit.cable_length_m / 1000

                # Get resistance per km (use default if not set)
                r_ohm_per_km = self._get_resistance_per_km(circuit.wire_size_sqmm)
                x_ohm_per_km = 0.08  # Standard reactance

                pp.create_line_from_parameters(
                    net,
                    from_bus=main_bus,
                    to_bus=circuit_bus,
                    length_km=length_km,
                    r_ohm_per_km=r_ohm_per_km,
                    x_ohm_per_km=x_ohm_per_km,
                    c_nf_per_km=0,
                    max_i_ka=circuit.design_current_a / 1000 * 1.5,
                    name=f"Line_{circuit.circuit_id}",
                )

                # Create load at circuit bus
                # Convert W to MW and calculate reactive power from power factor
                p_mw = circuit.demand_load_w / 1e6
                # Q = P * tan(arccos(PF)) = P * sqrt(1 - PF²) / PF
                q_mvar = p_mw * math.sqrt(1 - circuit.power_factor**2) / circuit.power_factor
                
                pp.create_load(
                    net,
                    bus=circuit_bus,
                    p_mw=p_mw,
                    q_mvar=q_mvar,
                    name=f"Load_{circuit.circuit_id}",
                )

        self._network = net
        return net

    def _get_resistance_per_km(self, size_sqmm: float) -> float:
        """Get cable resistance per km based on wire size.
        
        Args:
            size_sqmm: Wire cross-sectional area in sq mm.
            
        Returns:
            Resistance in ohm per km.
        """
        # Standard copper resistance values
        resistance_map = {
            1.5: 12.1,
            2.5: 7.41,
            4.0: 4.61,
            6.0: 3.08,
            10.0: 1.83,
            16.0: 1.15,
            25.0: 0.727,
            35.0: 0.524,
            50.0: 0.387,
            70.0: 0.268,
            95.0: 0.193,
        }

        if size_sqmm <= 0:
            return 12.1  # Default to 1.5mm²

        # Find closest size
        for size, resistance in sorted(resistance_map.items()):
            if size >= size_sqmm:
                return resistance

        return list(resistance_map.values())[-1]

    def run_power_flow(self, context: BaselineContext) -> BaselineContext:
        """Run power flow analysis and update voltage drops.
        
        Args:
            context: BaselineContext with network data.
            
        Returns:
            Updated BaselineContext with voltage drop results.
        """
        # Create network if not already created
        if self._network is None:
            self.create_network(context)

        net = self._network
        if net is None:
            return context

        try:
            # Run power flow
            pp.runpp(net, algorithm="nr", calculate_voltage_angles=True)

            # Extract voltage drops for each circuit
            circuit_map = {}
            for room in context.rooms:
                for circuit in room.circuits:
                    circuit_map[f"Bus_{circuit.circuit_id}"] = circuit

            # Update voltage drops from results
            if len(net.res_bus) > 0:
                for bus_idx, bus_data in net.bus.iterrows():
                    bus_name = bus_data["name"]
                    if bus_name in circuit_map:
                        circuit = circuit_map[bus_name]
                        vm_pu = net.res_bus.at[bus_idx, "vm_pu"]
                        # Voltage drop = (1 - vm_pu) * nominal_voltage
                        vd_v = (1 - vm_pu) * circuit.voltage_v
                        vd_pct = (1 - vm_pu) * 100

                        circuit.voltage_drop_v = vd_v
                        circuit.voltage_drop_pct = vd_pct

        except Exception:
            # If power flow fails, use simplified calculation
            self._calculate_simplified_voltage_drop(context)

        return context

    def _calculate_simplified_voltage_drop(self, context: BaselineContext) -> None:
        """Calculate voltage drop using simplified formula.
        
        VD = (2 * L * I * R) / 1000 for single phase
        where:
        - L = length in meters
        - I = current in amperes
        - R = resistance in ohm/km
        
        Args:
            context: BaselineContext to update.
        """
        for room in context.rooms:
            for circuit in room.circuits:
                r_ohm_km = self._get_resistance_per_km(circuit.wire_size_sqmm)
                length_km = circuit.cable_length_m / 1000

                # Calculate voltage drop
                vd_v = 2 * circuit.design_current_a * r_ohm_km * length_km
                vd_pct = (vd_v / circuit.voltage_v) * 100 if circuit.voltage_v > 0 else 0

                circuit.voltage_drop_v = vd_v
                circuit.voltage_drop_pct = vd_pct
