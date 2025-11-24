"""Pandapower adapter for MCP Core v2.

Builds a single-phase equivalent network and runs power flow analysis
using the pandapower library.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pandapower as pp
from pandapower.auxiliary import pandapowerNet

from models.baseline import BaselineContext, BaselineCircuit
from dal.catalog_dal import CatalogDAL

logger = logging.getLogger(__name__)


@dataclass
class PowerFlowResults:
    """Results from power flow analysis."""
    
    total_load_kw: float
    total_current_a: float
    power_factor: float
    voltage_at_furthest_point_v: float
    max_voltage_drop_percent: float
    convergence_achieved: bool
    bus_voltages: Dict[str, float]  # bus_name -> voltage p.u.
    line_currents: Dict[str, float]  # line_name -> current in A
    line_loading_percent: Dict[str, float]  # line_name -> loading %


class PandapowerAdapter:
    """Adapter for pandapower power flow analysis.
    
    Creates a single-phase equivalent model of the electrical system
    and performs power flow calculations.
    """

    def __init__(self, catalog_dal: CatalogDAL, voltage: float = 220.0):
        """Initialize pandapower adapter.
        
        Args:
            catalog_dal: Catalog data access object
            voltage: Nominal system voltage
        """
        self._catalog = catalog_dal
        self._voltage = voltage
        self._net: Optional[pandapowerNet] = None
        self._bus_mapping: Dict[str, int] = {}
        self._line_mapping: Dict[str, int] = {}

    def build_network(self, context: BaselineContext) -> pandapowerNet:
        """Build pandapower network from baseline context.
        
        Creates a single-phase equivalent network with:
        - External grid at the main panel
        - Buses for each circuit
        - Lines representing wire runs
        - Loads at each circuit bus
        
        Args:
            context: Baseline context with circuits
            
        Returns:
            pandapower network object
        """
        logger.info("Building pandapower network")
        
        # Create empty network
        net = pp.create_empty_network(name=context.project_name)
        
        # Create main bus (panel)
        main_bus = pp.create_bus(
            net,
            vn_kv=self._voltage / 1000,  # Convert to kV
            name="main_panel"
        )
        self._bus_mapping["main_panel"] = main_bus
        
        # Create external grid connection at main bus
        pp.create_ext_grid(
            net,
            bus=main_bus,
            vm_pu=1.0,  # 1.0 per unit voltage
            name="utility_supply"
        )
        
        # Create buses and loads for each circuit
        for room in context.rooms:
            for circuit in room.circuits:
                self._add_circuit_to_network(net, circuit, main_bus)
        
        self._net = net
        
        logger.info(
            f"Network created with {len(net.bus)} buses, "
            f"{len(net.line)} lines, "
            f"{len(net.load)} loads"
        )
        
        return net

    def _add_circuit_to_network(
        self,
        net: pandapowerNet,
        circuit: BaselineCircuit,
        main_bus: int
    ) -> None:
        """Add a circuit to the pandapower network.
        
        Args:
            net: pandapower network
            circuit: Circuit to add
            main_bus: Index of main panel bus
        """
        # Create bus for this circuit
        circuit_bus = pp.create_bus(
            net,
            vn_kv=self._voltage / 1000,
            name=f"bus_{circuit.circuit_id}"
        )
        self._bus_mapping[circuit.circuit_id] = circuit_bus
        
        # Get wire parameters
        wire_spec = self._get_wire_spec_for_circuit(circuit)
        
        # Create line from main bus to circuit bus
        # Using simplified impedance model
        r_ohm_per_km = wire_spec.get("r_ohm_per_km", 12.1)  # Default 1.5mm²
        x_ohm_per_km = wire_spec.get("x_ohm_per_km", 0.08)
        
        # Length in km
        length_km = circuit.distance_from_panel_m / 1000
        
        # Create line using standard type or direct parameters
        # For single-phase, we model as a line with R and X
        line_idx = pp.create_line_from_parameters(
            net,
            from_bus=main_bus,
            to_bus=circuit_bus,
            length_km=length_km,
            r_ohm_per_km=r_ohm_per_km,
            x_ohm_per_km=x_ohm_per_km,
            c_nf_per_km=0,  # Negligible for short runs
            max_i_ka=wire_spec.get("max_i_ka", 0.019),  # Default 19A
            name=f"line_{circuit.circuit_id}"
        )
        self._line_mapping[circuit.circuit_id] = line_idx
        
        # Create load at circuit bus
        # Convert demand load to MW and MVAr
        p_mw = circuit.total_demand_load_w / 1_000_000
        
        # Calculate reactive power based on power factor
        pf = self._get_circuit_power_factor(circuit)
        q_mvar = p_mw * ((1 - pf**2) ** 0.5) / pf if pf < 1 else 0
        
        pp.create_load(
            net,
            bus=circuit_bus,
            p_mw=p_mw,
            q_mvar=q_mvar,
            name=f"load_{circuit.circuit_id}"
        )

    def _get_wire_spec_for_circuit(self, circuit: BaselineCircuit) -> Dict[str, float]:
        """Get wire specifications based on circuit type.
        
        Returns default values for initial network building.
        Actual wire sizing is done by WireSizer.
        """
        # Default wire specs by circuit type
        specs = {
            "lighting": {
                "r_ohm_per_km": 12.1,  # 1.5mm²
                "x_ohm_per_km": 0.08,
                "max_i_ka": 0.014,
            },
            "outlet": {
                "r_ohm_per_km": 7.41,  # 2.5mm²
                "x_ohm_per_km": 0.08,
                "max_i_ka": 0.019,
            },
            "dedicated": {
                "r_ohm_per_km": 4.61,  # 4.0mm²
                "x_ohm_per_km": 0.08,
                "max_i_ka": 0.026,
            },
        }
        
        return specs.get(circuit.circuit_type.value, specs["outlet"])

    def _get_circuit_power_factor(self, circuit: BaselineCircuit) -> float:
        """Calculate weighted average power factor for circuit."""
        if not circuit.loads or circuit.total_connected_load_w == 0:
            return 0.85
        
        weighted_pf = sum(
            load.watts * load.quantity * load.power_factor
            for load in circuit.loads
        ) / circuit.total_connected_load_w
        
        return min(max(weighted_pf, 0.5), 1.0)

    def run_power_flow(self) -> PowerFlowResults:
        """Run power flow analysis on the built network.
        
        Returns:
            PowerFlowResults with analysis results
        """
        if self._net is None:
            raise ValueError("Network not built. Call build_network first.")
        
        logger.info("Running power flow analysis")
        
        try:
            # Run Newton-Raphson power flow
            pp.runpp(self._net, algorithm="nr", init="auto")
            convergence = True
        except pp.LoadflowNotConverged:
            logger.warning("Power flow did not converge, using DC approximation")
            try:
                pp.rundcpp(self._net)
                convergence = False
            except Exception as e:
                logger.error(f"DC power flow also failed: {e}")
                return self._create_fallback_results()
        except Exception as e:
            logger.error(f"Power flow failed: {e}")
            return self._create_fallback_results()
        
        # Extract results
        return self._extract_results(convergence)

    def _extract_results(self, convergence: bool) -> PowerFlowResults:
        """Extract results from completed power flow."""
        net = self._net
        
        # Bus voltages
        bus_voltages = {}
        min_voltage_pu = 1.0
        
        for idx, row in net.res_bus.iterrows():
            bus_name = net.bus.at[idx, "name"]
            vm_pu = row["vm_pu"]
            bus_voltages[bus_name] = vm_pu
            if bus_name != "main_panel":
                min_voltage_pu = min(min_voltage_pu, vm_pu)
        
        # Line currents and loading
        line_currents = {}
        line_loading = {}
        max_loading = 0.0
        
        for idx, row in net.res_line.iterrows():
            line_name = net.line.at[idx, "name"]
            # Current in A (pandapower gives kA)
            current_a = row["i_ka"] * 1000
            loading_pct = row["loading_percent"]
            
            line_currents[line_name] = current_a
            line_loading[line_name] = loading_pct
            max_loading = max(max_loading, loading_pct)
        
        # Calculate totals
        total_load_kw = net.res_load["p_mw"].sum() * 1000
        total_current_a = sum(line_currents.values())
        
        # Average power factor
        if net.res_load["p_mw"].sum() > 0:
            total_p = net.res_load["p_mw"].sum()
            total_q = net.res_load["q_mvar"].sum()
            total_s = (total_p**2 + total_q**2) ** 0.5
            power_factor = total_p / total_s if total_s > 0 else 0.85
        else:
            power_factor = 0.85
        
        # Voltage drop calculation
        max_voltage_drop = (1.0 - min_voltage_pu) * 100
        voltage_at_furthest = min_voltage_pu * self._voltage
        
        logger.info(
            f"Power flow complete: "
            f"total_load={total_load_kw:.2f}kW, "
            f"max_vdrop={max_voltage_drop:.2f}%"
        )
        
        return PowerFlowResults(
            total_load_kw=total_load_kw,
            total_current_a=total_current_a,
            power_factor=power_factor,
            voltage_at_furthest_point_v=voltage_at_furthest,
            max_voltage_drop_percent=max_voltage_drop,
            convergence_achieved=convergence,
            bus_voltages=bus_voltages,
            line_currents=line_currents,
            line_loading_percent=line_loading,
        )

    def _create_fallback_results(self) -> PowerFlowResults:
        """Create fallback results when power flow fails."""
        return PowerFlowResults(
            total_load_kw=0.0,
            total_current_a=0.0,
            power_factor=0.85,
            voltage_at_furthest_point_v=self._voltage,
            max_voltage_drop_percent=0.0,
            convergence_achieved=False,
            bus_voltages={},
            line_currents={},
            line_loading_percent={},
        )

    def get_voltage_at_circuit(self, circuit_id: str) -> float:
        """Get voltage at a specific circuit bus.
        
        Args:
            circuit_id: Circuit identifier
            
        Returns:
            Voltage in per-unit at the circuit bus
        """
        if self._net is None:
            return 1.0
        
        bus_idx = self._bus_mapping.get(circuit_id)
        if bus_idx is not None and bus_idx in self._net.res_bus.index:
            return self._net.res_bus.at[bus_idx, "vm_pu"]
        
        return 1.0

    def get_current_in_line(self, circuit_id: str) -> float:
        """Get current flowing in line to a circuit.
        
        Args:
            circuit_id: Circuit identifier
            
        Returns:
            Current in Amps
        """
        if self._net is None:
            return 0.0
        
        line_idx = self._line_mapping.get(circuit_id)
        if line_idx is not None and line_idx in self._net.res_line.index:
            return self._net.res_line.at[line_idx, "i_ka"] * 1000
        
        return 0.0
