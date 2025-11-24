"""AutoLISP code generator for AutoCAD integration."""

from typing import Dict, Any, List, Optional
from models.contracts import DesignRequest, ElectricalLoad, PanelSpecification
import logging

logger = logging.getLogger(__name__)


class AutoLispGenerator:
    """Generates AutoLISP code for AutoCAD electrical drawings."""
    
    def __init__(self):
        """Initialize AutoLISP generator."""
        pass
    
    def generate_complete_drawing(
        self,
        request: DesignRequest,
        design_results: Dict[str, Any]
    ) -> str:
        """Generate complete AutoLISP code for the electrical design."""
        lisp_code = []
        
        # Header
        lisp_code.append(self._generate_header(request))
        
        # Drawing setup
        lisp_code.append(self._generate_setup())
        
        # Generate panels
        lisp_code.append(self._generate_panels(request.panels))
        
        # Generate loads/devices
        lisp_code.append(self._generate_loads(request.loads))
        
        # Generate wire runs
        lisp_code.append(self._generate_wire_runs(request, design_results))
        
        # Generate schedules
        lisp_code.append(self._generate_panel_schedules(request.panels, design_results))
        
        # Footer
        lisp_code.append(self._generate_footer())
        
        return "\n".join(lisp_code)
    
    def _generate_header(self, request: DesignRequest) -> str:
        """Generate AutoLISP header with project information."""
        return f""";;; ========================================
;;; Electrical Design AutoLISP Code
;;; Project: {request.project_name}
;;; Project Number: {request.project_number or 'N/A'}
;;; Session ID: {request.session_id}
;;; Generated: {request.created_at}
;;; ========================================

(defun C:ELECTRICAL-DESIGN ()
  (setq oldcmd (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)
  (princ "\\nGenerating electrical design...")
"""
    
    def _generate_setup(self) -> str:
        """Generate drawing setup code."""
        return """
  ;;; Setup layers
  (if (not (tblsearch "LAYER" "ELECTRICAL"))
    (command "LAYER" "N" "ELECTRICAL" "C" "1" "ELECTRICAL" ""))
  (if (not (tblsearch "LAYER" "ELECTRICAL-PANEL"))
    (command "LAYER" "N" "ELECTRICAL-PANEL" "C" "2" "ELECTRICAL-PANEL" ""))
  (if (not (tblsearch "LAYER" "ELECTRICAL-DEVICE"))
    (command "LAYER" "N" "ELECTRICAL-DEVICE" "C" "3" "ELECTRICAL-DEVICE" ""))
  (if (not (tblsearch "LAYER" "ELECTRICAL-WIRE"))
    (command "LAYER" "N" "ELECTRICAL-WIRE" "C" "4" "ELECTRICAL-WIRE" ""))
  
  (setq scale-factor 1.0)
"""
    
    def _generate_panels(self, panels: List[PanelSpecification]) -> str:
        """Generate AutoLISP code for electrical panels."""
        code = ["\n  ;;; Generate panels"]
        
        for i, panel in enumerate(panels):
            x_pos = i * 120  # Space panels horizontally
            y_pos = 0
            
            code.append(f"""
  ;;; Panel: {panel.name}
  (setvar "CLAYER" "ELECTRICAL-PANEL")
  (command "RECTANGLE" (list {x_pos} {y_pos}) (list {x_pos + 48} {y_pos + 72}))
  (command "TEXT" "J" "MC" (list {x_pos + 24} {y_pos + 68}) "4" "0" "{panel.name}")
  (command "TEXT" "J" "MC" (list {x_pos + 24} {y_pos + 60}) "3" "0" "{panel.main_breaker_rating}A MAIN")
  (command "TEXT" "J" "MC" (list {x_pos + 24} {y_pos + 54}) "2.5" "0" "{panel.voltage.value}")
  (command "TEXT" "J" "MC" (list {x_pos + 24} {y_pos + 48}) "2.5" "0" "{panel.number_of_circuits} CKT")
  (command "TEXT" "J" "MC" (list {x_pos + 24} {y_pos + 42}) "2" "0" "{panel.location.room}")
""")
        
        return "\n".join(code)
    
    def _generate_loads(self, loads: List[ElectricalLoad]) -> str:
        """Generate AutoLISP code for electrical loads/devices."""
        code = ["\n  ;;; Generate devices/loads"]
        
        # Group loads by location
        locations = {}
        for load in loads:
            loc_key = f"{load.location.room}"
            if loc_key not in locations:
                locations[loc_key] = []
            locations[loc_key].append(load)
        
        y_offset = -100
        for loc_name, loc_loads in locations.items():
            code.append(f"\n  ;;; Location: {loc_name}")
            
            for i, load in enumerate(loc_loads):
                x_pos = i * 40
                symbol = self._get_load_symbol(load)
                
                code.append(f"""
  (setvar "CLAYER" "ELECTRICAL-DEVICE")
  {symbol.format(x=x_pos, y=y_offset)}
  (command "TEXT" "J" "MC" (list {x_pos} {y_offset - 15}) "2" "0" "{load.name}")
  (command "TEXT" "J" "MC" (list {x_pos} {y_offset - 20}) "1.5" "0" "{load.power_watts}W")
""")
            
            y_offset -= 60
        
        return "\n".join(code)
    
    def _get_load_symbol(self, load: ElectricalLoad) -> str:
        """Get AutoLISP symbol code for a load type."""
        symbols = {
            'lighting': '(command "CIRCLE" (list {x} {y}) "6")',
            'receptacle': '(command "RECTANGLE" (list {x} {y}) (list {{x}} {{y}}))',
            'hvac': '(command "POLYGON" "4" (list {x} {y}) "8")',
            'motor': '(command "CIRCLE" (list {x} {y}) "8") (command "TEXT" "J" "MC" (list {x} {y}) "2" "0" "M")',
        }
        
        return symbols.get(load.load_type.value, '(command "CIRCLE" (list {x} {y}) "5")')
    
    def _generate_wire_runs(
        self,
        request: DesignRequest,
        design_results: Dict[str, Any]
    ) -> str:
        """Generate AutoLISP code for wire runs."""
        code = ["\n  ;;; Generate wire runs"]
        code.append("  (setvar \"CLAYER\" \"ELECTRICAL-WIRE\")")
        
        # This would connect panels to loads
        # Simplified version just draws lines
        for panel in request.panels:
            panel_x = request.panels.index(panel) * 120 + 24
            panel_y = 0
            
            for load_id in panel.feeds:
                # Find the load
                load = next((l for l in request.loads if l.id == load_id), None)
                if not load:
                    continue
                
                # Get wire sizing from results
                wire_size = design_results.get('wire_sizing', {}).get(load_id, {}).get('wire_size', '12')
                
                code.append(f"""
  ;;; Wire from {panel.name} to {load.name} ({wire_size} AWG)
  ;; (command "LINE" (list {panel_x} {panel_y}) ... "")
""")
        
        return "\n".join(code)
    
    def _generate_panel_schedules(
        self,
        panels: List[PanelSpecification],
        design_results: Dict[str, Any]
    ) -> str:
        """Generate panel schedule tables."""
        code = ["\n  ;;; Generate panel schedules"]
        
        x_start = 0
        y_start = -400
        
        for i, panel in enumerate(panels):
            x_pos = x_start + (i * 200)
            
            code.append(f"""
  ;;; Panel Schedule: {panel.name}
  (command "RECTANGLE" (list {x_pos} {y_start}) (list {x_pos + 180} {y_start + 200}))
  (command "TEXT" "J" "ML" (list {x_pos + 5} {y_start + 190}) "4" "0" "PANEL SCHEDULE: {panel.name}")
  (command "LINE" (list {x_pos} {y_start + 180}) (list {x_pos + 180} {y_start + 180}) "")
  
  ;;; Schedule headers
  (command "TEXT" "J" "ML" (list {x_pos + 5} {y_start + 170}) "2.5" "0" "CKT")
  (command "TEXT" "J" "ML" (list {x_pos + 30} {y_start + 170}) "2.5" "0" "DESCRIPTION")
  (command "TEXT" "J" "ML" (list {x_pos + 110} {y_start + 170}) "2.5" "0" "LOAD")
  (command "TEXT" "J" "ML" (list {x_pos + 140} {y_start + 170}) "2.5" "0" "BREAKER")
""")
            
            # Add circuit rows
            calc_data = design_results.get('calculations', {}).get(panel.id, {})
            load_breakdown = calc_data.get('load_breakdown', {})
            
            row_y = y_start + 160
            for ckt_num, (load_id, load_data) in enumerate(load_breakdown.items(), start=1):
                breaker_data = design_results.get('breaker_selections', {}).get(load_id, {})
                breaker_rating = breaker_data.get('breaker_rating', 'N/A')
                
                code.append(f"""
  (command "TEXT" "J" "ML" (list {x_pos + 5} {row_y}) "2" "0" "{ckt_num}")
  (command "TEXT" "J" "ML" (list {x_pos + 30} {row_y}) "2" "0" "{load_data.get('name', 'N/A')}")
  (command "TEXT" "J" "ML" (list {x_pos + 110} {row_y}) "2" "0" "{load_data.get('va', 0)}VA")
  (command "TEXT" "J" "ML" (list {x_pos + 140} {row_y}) "2" "0" "{breaker_rating}A")
""")
                row_y -= 8
        
        return "\n".join(code)
    
    def _generate_footer(self) -> str:
        """Generate AutoLISP footer."""
        return """
  ;;; Complete
  (setvar "CMDECHO" oldcmd)
  (princ "\\nElectrical design generation complete.")
  (princ)
)

;;; Run the command
(princ "\\nType ELECTRICAL-DESIGN to generate the drawing.")
(princ)
"""
    
    def generate_panel_detail(self, panel: PanelSpecification) -> str:
        """Generate detailed panel drawing code."""
        return f"""
;;; Panel Detail: {panel.name}
(defun C:PANEL-{panel.id.upper()} ()
  (command "RECTANGLE" '(0 0) '(48 72))
  (command "TEXT" "J" "MC" '(24 68) "4" "0" "{panel.name}")
  (princ)
)
"""


# Global instance
_autolisp_generator: Optional[AutoLispGenerator] = None


def get_autolisp_generator() -> AutoLispGenerator:
    """Get the global AutoLISP generator instance."""
    global _autolisp_generator
    if _autolisp_generator is None:
        _autolisp_generator = AutoLispGenerator()
    return _autolisp_generator
