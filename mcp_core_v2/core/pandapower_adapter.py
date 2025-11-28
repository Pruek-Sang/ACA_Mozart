"""Pandapower adapter for power flow analysis."""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Conditional import for pandapower
try:
    import pandapower as pp
    import pandapower.networks as pn
    PANDAPOWER_AVAILABLE = True
except ImportError:
    logger.warning("Pandapower not available. Power flow analysis will be limited.")
    PANDAPOWER_AVAILABLE = False


class PandapowerAdapter:
    """Adapter for pandapower electrical network analysis."""
    
    def __init__(self):
        """Initialize pandapower adapter."""
        if not PANDAPOWER_AVAILABLE:
            logger.warning("Pandapower not installed. Install with: pip install pandapower")
        self.network = None
    
    def create_network(
        self,
        name: str = "electrical_design",
        frequency: float = 60.0
    ) -> Any:
        """Create a new pandapower network."""
        if not PANDAPOWER_AVAILABLE:
            raise ImportError("Pandapower is not available")
        
        self.network = pp.create_empty_network(name=name, f_hz=frequency)
        return self.network
    
    def add_bus(
        self,
        name: str,
        vn_kv: float,
        bus_type: str = "b"
    ) -> int:
        """Add a bus to the network."""
        if not self.network:
            self.create_network()
        
        bus_idx = pp.create_bus(
            self.network,
            vn_kv=vn_kv,
            name=name,
            type=bus_type
        )
        return bus_idx
    
    def add_external_grid(
        self,
        bus: int,
        vm_pu: float = 1.0,
        va_degree: float = 0.0
    ) -> int:
        """Add an external grid connection (utility service)."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        ext_grid_idx = pp.create_ext_grid(
            self.network,
            bus=bus,
            vm_pu=vm_pu,
            va_degree=va_degree
        )
        return ext_grid_idx
    
    def add_load(
        self,
        bus: int,
        p_mw: float,
        q_mvar: float = 0.0,
        name: str = ""
    ) -> int:
        """Add a load to the network."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        load_idx = pp.create_load(
            self.network,
            bus=bus,
            p_mw=p_mw,
            q_mvar=q_mvar,
            name=name
        )
        return load_idx
    
    def add_line(
        self,
        from_bus: int,
        to_bus: int,
        length_km: float,
        std_type: str = "NAYY 4x50 SE",
        name: str = ""
    ) -> int:
        """Add a line between two buses."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        line_idx = pp.create_line(
            self.network,
            from_bus=from_bus,
            to_bus=to_bus,
            length_km=length_km,
            std_type=std_type,
            name=name
        )
        return line_idx
    
    def add_transformer(
        self,
        hv_bus: int,
        lv_bus: int,
        std_type: str = "0.4 MVA 20/0.4 kV",
        name: str = ""
    ) -> int:
        """Add a transformer between two buses."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        trafo_idx = pp.create_transformer(
            self.network,
            hv_bus=hv_bus,
            lv_bus=lv_bus,
            std_type=std_type,
            name=name
        )
        return trafo_idx
    
    def run_power_flow(self) -> bool:
        """Run power flow calculation."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        try:
            pp.runpp(self.network)
            return self.network.converged
        except Exception as e:
            logger.error(f"Power flow calculation failed: {e}")
            return False
    
    def get_results(self) -> Dict[str, Any]:
        """Get power flow results."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        if not hasattr(self.network, 'converged') or not self.network.converged:
            logger.warning("Power flow has not converged")
            return {}
        
        results = {
            'buses': self.network.res_bus.to_dict() if hasattr(self.network, 'res_bus') else {},
            'loads': self.network.res_load.to_dict() if hasattr(self.network, 'res_load') else {},
            'lines': self.network.res_line.to_dict() if hasattr(self.network, 'res_line') else {},
            'converged': self.network.converged
        }
        
        return results
    
    def get_bus_voltages(self) -> Dict[int, float]:
        """Get voltage at all buses."""
        if not self.network or not hasattr(self.network, 'res_bus'):
            return {}
        
        return self.network.res_bus['vm_pu'].to_dict()
    
    def get_line_loading(self) -> Dict[int, float]:
        """Get loading percentage for all lines."""
        if not self.network or not hasattr(self.network, 'res_line'):
            return {}
        
        return self.network.res_line['loading_percent'].to_dict()
    
    def analyze_network(self) -> Dict[str, Any]:
        """Perform complete network analysis."""
        if not self.network:
            raise ValueError("Network not initialized")
        
        # Run power flow
        converged = self.run_power_flow()
        
        if not converged:
            return {
                'converged': False,
                'error': 'Power flow did not converge'
            }
        
        # Get results
        results = self.get_results()
        voltages = self.get_bus_voltages()
        loading = self.get_line_loading()
        
        # Analyze for issues
        issues = []
        
        # Check for voltage violations
        for bus_id, voltage in voltages.items():
            if voltage < 0.95 or voltage > 1.05:
                issues.append(f"Bus {bus_id}: Voltage {voltage:.3f} pu is outside acceptable range")
        
        # Check for overloaded lines
        for line_id, load_pct in loading.items():
            if load_pct > 100:
                issues.append(f"Line {line_id}: Loading {load_pct:.1f}% exceeds capacity")
        
        return {
            'converged': True,
            'results': results,
            'voltages': voltages,
            'loading': loading,
            'issues': issues
        }


# Global instance
_pandapower_adapter: Optional[PandapowerAdapter] = None


def get_pandapower_adapter() -> PandapowerAdapter:
    """Get the global pandapower adapter instance."""
    global _pandapower_adapter
    if _pandapower_adapter is None:
        _pandapower_adapter = PandapowerAdapter()
    return _pandapower_adapter
