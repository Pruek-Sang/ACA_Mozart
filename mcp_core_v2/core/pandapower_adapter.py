"""
MCP Core v2 Pandapower Adapter
Single-phase equivalent power flow analysis using pandapower.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    pp = None

from models.contracts import CircuitSpec, RoomDesign


class PandapowerAdapter:
    """
    Adapter for pandapower power flow analysis.
    Uses single-phase equivalent model for residential calculations.
    """
    
    def __init__(self, voltage_kv: float = 0.22):
        """
        Initialize adapter.
        
        Args:
            voltage_kv: System voltage in kV (default 220V = 0.22kV)
        """
        self.voltage_kv = voltage_kv
        self.net = None
        
        if not PANDAPOWER_AVAILABLE:
            print("Warning: pandapower not available, using simplified calculations")
    
    def create_network(self, circuits: List[CircuitSpec]) -> Optional[Any]:
        """
        Create pandapower network from circuit specifications.
        
        Args:
            circuits: List of circuit specifications
            
        Returns:
            pandapower network object or None
        """
        if not PANDAPOWER_AVAILABLE:
            return None
        
        # Create empty network
        self.net = pp.create_empty_network()
        
        # Create external grid (utility connection)
        bus_main = pp.create_bus(self.net, vn_kv=self.voltage_kv, name="main_panel")
        pp.create_ext_grid(self.net, bus=bus_main, vm_pu=1.0, name="utility")
        
        # Create bus for each circuit
        for i, circuit in enumerate(circuits):
            bus_circuit = pp.create_bus(
                self.net,
                vn_kv=self.voltage_kv,
                name=circuit.circuit_id
            )
            
            # Create line from main panel to circuit
            # Use simplified impedance based on wire size
            r_ohm_per_km, x_ohm_per_km = self._get_impedance(circuit.wire_size)
            length_km = 0.02  # Assume 20m average run
            
            pp.create_line_from_parameters(
                self.net,
                from_bus=bus_main,
                to_bus=bus_circuit,
                length_km=length_km,
                r_ohm_per_km=r_ohm_per_km,
                x_ohm_per_km=x_ohm_per_km,
                c_nf_per_km=0,
                max_i_ka=circuit.breaker_size / 1000,
                name=f"line_{circuit.circuit_id}"
            )
            
            # Create load
            load_kw = circuit.total_load / 1000
            pp.create_load(
                self.net,
                bus=bus_circuit,
                p_mw=load_kw / 1000,  # Convert to MW
                q_mvar=load_kw * 0.1 / 1000,  # Assume 0.1 reactive factor
                name=f"load_{circuit.circuit_id}"
            )
        
        return self.net
    
    def _get_impedance(self, wire_size_sqmm: float) -> Tuple[float, float]:
        """
        Get wire impedance values.
        
        Args:
            wire_size_sqmm: Wire size in mm²
            
        Returns:
            Tuple of (R ohm/km, X ohm/km)
        """
        # Approximate values for copper PVC cable
        impedance_table = {
            1.5: (12.1, 0.115),
            2.5: (7.41, 0.110),
            4.0: (4.61, 0.107),
            6.0: (3.08, 0.100),
            10.0: (1.83, 0.094),
            16.0: (1.15, 0.090),
            25.0: (0.727, 0.086),
            35.0: (0.524, 0.083),
            50.0: (0.387, 0.081),
        }
        
        # Find closest match
        closest_size = min(impedance_table.keys(), key=lambda x: abs(x - wire_size_sqmm))
        return impedance_table[closest_size]
    
    def run_power_flow(self) -> Dict[str, Any]:
        """
        Run power flow analysis.
        
        Returns:
            Dictionary with results
        """
        if not PANDAPOWER_AVAILABLE or self.net is None:
            return self._simplified_analysis()
        
        try:
            pp.runpp(self.net, algorithm='nr', calculate_voltage_angles=False)
            
            results = {
                "success": True,
                "bus_voltages": {},
                "line_loading": {},
                "total_loss_kw": 0.0,
            }
            
            # Extract bus voltages
            for idx in self.net.bus.index:
                bus_name = self.net.bus.at[idx, 'name']
                vm_pu = self.net.res_bus.at[idx, 'vm_pu']
                results["bus_voltages"][bus_name] = vm_pu * self.voltage_kv * 1000
            
            # Extract line loading
            for idx in self.net.line.index:
                line_name = self.net.line.at[idx, 'name']
                loading = self.net.res_line.at[idx, 'loading_percent']
                results["line_loading"][line_name] = loading
            
            # Total losses
            results["total_loss_kw"] = self.net.res_line['pl_mw'].sum() * 1000
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "bus_voltages": {},
                "line_loading": {},
            }
    
    def _simplified_analysis(self) -> Dict[str, Any]:
        """
        Simplified power flow when pandapower unavailable.
        
        Returns:
            Approximate results
        """
        return {
            "success": True,
            "simplified": True,
            "bus_voltages": {"main_panel": 220.0},
            "line_loading": {},
            "total_loss_kw": 0.0,
            "note": "Pandapower not available, using simplified calculation"
        }
    
    def check_voltage_drop(
        self,
        circuit: CircuitSpec,
        length_m: float = 20
    ) -> Dict[str, Any]:
        """
        Check voltage drop for a circuit.
        
        Args:
            circuit: Circuit specification
            length_m: Wire run length in meters
            
        Returns:
            Voltage drop analysis
        """
        # I = P / V
        current = circuit.total_load / (self.voltage_kv * 1000)
        
        # Get resistance
        r_per_km, _ = self._get_impedance(circuit.wire_size)
        r_total = r_per_km * (length_m / 1000) * 2  # Round trip
        
        # Voltage drop
        v_drop = current * r_total
        v_drop_percent = (v_drop / (self.voltage_kv * 1000)) * 100
        
        return {
            "current_a": current,
            "voltage_drop_v": v_drop,
            "voltage_drop_percent": v_drop_percent,
            "compliant": v_drop_percent <= 3.0,  # EIT allows 3%
            "end_voltage": (self.voltage_kv * 1000) - v_drop,
        }
    
    def analyze_circuits(
        self,
        circuits: List[CircuitSpec]
    ) -> Dict[str, Any]:
        """
        Comprehensive circuit analysis.
        
        Args:
            circuits: List of circuit specifications
            
        Returns:
            Analysis results for all circuits
        """
        self.create_network(circuits)
        power_flow = self.run_power_flow()
        
        circuit_analysis = {}
        for circuit in circuits:
            vdrop = self.check_voltage_drop(circuit)
            circuit_analysis[circuit.circuit_id] = {
                "load_watts": circuit.total_load,
                "voltage_drop": vdrop,
                "compliant": vdrop["compliant"],
            }
        
        return {
            "power_flow": power_flow,
            "circuits": circuit_analysis,
            "all_compliant": all(
                c["compliant"] for c in circuit_analysis.values()
            ),
        }
