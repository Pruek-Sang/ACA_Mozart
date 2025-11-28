"""
Wire Router - Orthogonal (Manhattan-style) wire routing

Routes wires between:
- Devices → Switch (lighting circuits)
- Devices → Panel (power circuits, homeruns)

Algorithm: Simple H+V routing (horizontal then vertical)
For MVP: Functional routing, not optimized for minimum path
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

Point = Tuple[float, float]


class WireRouter:
    """
    Wire router for electrical circuits
    
    Provides orthogonal (H+V) routing between devices.
    
    Usage:
        router = WireRouter()
        path = router.route_orthogonal(device_pos, panel_pos)
        lisp_code = router.generate_wire_lisp([path1, path2, ...])
    """
    
    def __init__(self):
        """Initialize wire router"""
        self.routes = []
    
    def route_lighting_circuit(self, lights: List[Dict], switch: Dict, 
                              panel: Dict) -> List[Dict[str, Any]]:
        """
        Route lighting circuit
        
        Algorithm:
        1. Connect switch → each light (simple H+V)
        2. Connect switch → panel (homerun)
        
        Args:
            lights: List of light devices
            switch: Switch device
            panel: Panel location
        
        Returns:
            List of route segments:
            [
                {
                    'from': device1,
                    'to': device2,
                    'path': [(x,y), ...],
                    'circuit_type': 'lighting'
                }
            ]
        """
        routes = []
        
        switch_pos = switch['position']
        
        # Route from switch to each light
        for light in lights:
            light_pos = light['position']
            path = self.route_orthogonal(switch_pos, light_pos)
            
            routes.append({
                'from': switch,
                'to': light,
                'path': path,
                'circuit_type': 'lighting',
                'wire_type': 'switch_leg'
            })
        
        # Homerun from switch to panel
        panel_pos = panel['position']
        homerun_path = self.route_orthogonal(switch_pos, panel_pos)
        
        routes.append({
            'from': switch,
            'to': panel,
            'path': homerun_path,
            'circuit_type': 'lighting',
            'wire_type': 'homerun'
        })
        
        return routes
    
    def route_power_circuit(self, outlets: List[Dict], panel: Dict) -> List[Dict[str, Any]]:
        """
        Route power circuit
        
        Algorithm:
        1. Chain outlets together (daisy-chain)
        2. Connect first outlet → panel (homerun)
        
        Args:
            outlets: List of outlet devices
            panel: Panel location
        
        Returns:
            List of route segments
        """
        routes = []
        
        if not outlets:
            return routes
        
        # Sort outlets by proximity (simple: by x-coordinate)
        sorted_outlets = sorted(outlets, key=lambda o: o['position'][0])
        
        # Chain outlets together
        for i in range(len(sorted_outlets) - 1):
            outlet1 = sorted_outlets[i]
            outlet2 = sorted_outlets[i + 1]
            
            path = self.route_orthogonal(outlet1['position'], outlet2['position'])
            
            routes.append({
                'from': outlet1,
                'to': outlet2,
                'path': path,
                'circuit_type': 'power',
                'wire_type': 'daisy_chain'
            })
        
        # Homerun from first outlet to panel
        first_outlet = sorted_outlets[0]
        panel_pos = panel['position']
        homerun_path = self.route_orthogonal(first_outlet['position'], panel_pos)
        
        routes.append({
            'from': first_outlet,
            'to': panel,
            'path': homerun_path,
            'circuit_type': 'power',
            'wire_type': 'homerun'
        })
        
        return routes
    
    def route_orthogonal(self, start: Point, end: Point) -> List[Point]:
        """
        Route orthogonal path from start to end
        
        Algorithm: H+V (horizontal first, then vertical)
        
        Args:
            start: (x, y) start point
            end: (x, y) end point
        
        Returns:
            Path as list of points: [start, corner, end]
        """
        start_x, start_y = start
        end_x, end_y = end
        
        # Simple H+V routing
        # Go horizontal first, then vertical
        path = [
            start,
            (end_x, start_y),  # Corner point
            end
        ]
        
        return path
    
    def generate_wire_lisp(self, routes: List[Dict[str, Any]], 
                          layer: str = 'E-WIRE') -> str:
        """
        Generate AutoLISP code for wire routes
        
        Args:
            routes: List of route dicts
            layer: Layer name for wires
        
        Returns:
            LISP code string
        """
        from ..autolisp_writer import AutoLISPWriter
        
        writer = AutoLISPWriter()
        
        # Create and set layer
        writer.create_layers({layer: {'color': 1, 'linetype': 'CONTINUOUS'}})
        writer.set_layer(layer)
        
        for route in routes:
            path = route['path']
            wire_type = route.get('wire_type', 'wire')
            
            # Draw polyline for wire
            if len(path) >= 2:
                writer.draw_polyline(path)  # Use AutoLISPWriter method
            
            # Add homerun arrow if applicable
            if wire_type == 'homerun':
                # Draw arrow at end
                end_point = path[-1]
                prev_point = path[-2] if len(path) > 1 else path[0]
                
                # Simple arrow (line with two short diagonals)
                dx = end_point[0] - prev_point[0]
                dy = end_point[1] - prev_point[1]
                
                # Normalize
                length = (dx**2 + dy**2)**0.5
                if length > 0:
                    dx /= length
                    dy /= length
                    
                    # Arrow head (30deg, 200mm length)
                    arrow_len = 200
                    arrow1 = (
                        end_point[0] - arrow_len * (dx * 0.866 + dy * 0.5),
                        end_point[1] - arrow_len * (dy * 0.866 - dx * 0.5)
                    )
                    arrow2 = (
                        end_point[0] - arrow_len * (dx * 0.866 - dy * 0.5),
                        end_point[1] - arrow_len * (dy * 0.866 + dx * 0.5)
                    )
                    
                    writer.draw_line(end_point, arrow1)
                    writer.draw_line(end_point, arrow2)
        
        return writer.get_code()
    
    def route_all_circuits(self, devices: Dict[str, List[Dict]], 
                          panel: Dict) -> List[Dict[str, Any]]:
        """
        Route all circuits for a set of devices
        
        Args:
            devices: {
                'outlets': [...],
                'lights': [...],
                'switches': [...]
            }
            panel: Panel dict with 'position'
        
        Returns:
            Combined list of all routes
        """
        all_routes = []
        
        # Power circuits (outlets)
        if devices.get('outlets'):
            power_routes = self.route_power_circuit(devices['outlets'], panel)
            all_routes.extend(power_routes)
        
        # Lighting circuits
        if devices.get('lights') and devices.get('switches'):
            for switch in devices['switches']:
                # Find lights controlled by this switch
                controlled_lights = []
                switch_controls = switch.get('controls', [])
                
                for light in devices['lights']:
                    if light['id'] in switch_controls or not switch_controls:
                        controlled_lights.append(light)
                
                if controlled_lights:
                    lighting_routes = self.route_lighting_circuit(
                        controlled_lights, switch, panel
                    )
                    all_routes.extend(lighting_routes)
        
        return all_routes


def route_wires(devices: Dict[str, List[Dict]], panel_position: Point) -> List[Dict[str, Any]]:
    """
    Convenience function to route all wires
    
    Args:
        devices: Device dict from DevicePlacer
        panel_position: (x, y) panel location
    
    Returns:
        List of route segments
    """
    router = WireRouter()
    panel = {'position': panel_position, 'id': 'PANEL'}
    
    return router.route_all_circuits(devices, panel)
