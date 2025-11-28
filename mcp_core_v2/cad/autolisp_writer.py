"""
AutoLISP Writer - Base functionality for generating AutoLISP code

Generates valid AutoLISP (.lsp) files for AutoCAD 2024

Key features:
- Balanced parentheses (validated)
- UTF-8 encoding support (Thai + English)
- Standard AutoCAD commands
- Layer management
- Block insertion with attributes
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoLISPWriter:
    """
    Base class for generating AutoLISP code
    
    Provides:
    - Header/footer generation
    - Layer creation
    - Common AutoCAD commands
    - Parentheses balancing
    """
    
    def __init__(self, project_name: str = "Electrical Design"):
        """
        Initialize LISP writer
        
        Args:
            project_name: Project name for header
        """
        self.project_name = project_name
        self.code_lines: List[str] = []
    
    def write_header(self, drawing_name: str, description: str = "") -> None:
        """
        Generate LISP header with project info
        
        Args:
            drawing_name: Drawing title (e.g., "E-301 Single Line Diagram")
            description: Optional description
        """
        header = f""";;; ============================================
;;; {drawing_name}
;;; Project: {self.project_name}
;;; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
;;; Generator: MCP Core v2 - CAD Module
;;; ============================================
"""
        if description:
            header += f";;; {description}\n"
        
        header += ";;; ============================================\n\n"
        
        self.code_lines.append(header)
    
    def create_layers(self, layer_specs: Dict[str, Dict[str, Any]]) -> None:
        """
        Generate layer creation commands
        
        Args:
            layer_specs: {
                'layer_name': {
                    'color': int (1-255),
                    'linetype': str ('CONTINUOUS', 'DASHED', etc.)
                }
            }
        
        Example:
            create_layers({
                'E-ELEC-SLD': {'color': 1, 'linetype': 'CONTINUOUS'},
                'E-ELEC-SCHEDULE': {'color': 7, 'linetype': 'CONTINUOUS'},
            })
        """
        self.code_lines.append(";;; Create layers\n")
        
        for layer_name, specs in layer_specs.items():
            color = specs.get('color', 7)
            linetype = specs.get('linetype', 'CONTINUOUS')
            
            cmd = f'(command "LAYER" "N" "{layer_name}" "C" "{color}" "{layer_name}" "")\n'
            self.code_lines.append(cmd)
        
        self.code_lines.append("\n")
    
    def set_layer(self, layer_name: str) -> None:
        """Set current layer"""
        self.code_lines.append(f'(setvar "CLAYER" "{layer_name}")\n')
    
    def draw_line(self, start: Tuple[float, float], end: Tuple[float, float]) -> None:
        """
        Draw a line
        
        Args:
            start: (x, y) start point
            end: (x, y) end point
        """
        self.code_lines.append(
            f'(command "LINE" (list {start[0]} {start[1]}) (list {end[0]} {end[1]}) "")\n'
        )
    
    def draw_polyline(self, points: List[Tuple[float, float]]) -> None:
        """
        Draw a polyline through multiple points
        
        Args:
            points: List of (x, y) coordinates
        """
        if len(points) < 2:
            logger.warning("Polyline needs at least 2 points")
            return
        
        cmd = '(command "PLINE"'
        for pt in points:
            cmd += f' (list {pt[0]} {pt[1]})'
        cmd += ' "")\n'
        
        self.code_lines.append(cmd)
    
    def insert_block(self, block_name: str, position: Tuple[float, float], 
                    scale: float = 1.0, rotation: float = 0.0) -> None:
        """
        Insert a block
        
        Args:
            block_name: Block name (must exist in drawing or be defined)
            position: (x, y) insertion point
            scale: Scale factor
            rotation: Rotation angle in degrees
        """
        self.code_lines.append(
            f'(command "INSERT" "{block_name}" '
            f'(list {position[0]} {position[1]}) '
            f'{scale} {rotation})\n'
        )
    
    def add_text(self, text: str, position: Tuple[float, float], 
                height: float = 100, rotation: float = 0) -> None:
        """
        Add text
        
        Args:
            text: Text string
            position: (x, y) position
            height: Text height in drawing units (mm)
            rotation: Rotation angle in degrees
        """
        # Escape special characters
        text_escaped = text.replace('"', '\\"')
        
        self.code_lines.append(
            f'(command "TEXT" (list {position[0]} {position[1]}) '
            f'{height} {rotation} "{text_escaped}")\n'
        )
    
    def write_footer(self) -> None:
        """Generate LISP footer"""
        footer = """\n;;; ============================================
;;; End of drawing commands
;;; ============================================

(princ "\\nDrawing generation complete!")
(princ)
"""
        self.code_lines.append(footer)
    
    def wrap_in_function(self, function_name: str) -> None:
        """
        Wrap current code in a defun function
        
        Args:
            function_name: Function name (e.g., "C:ELEC-E301")
        """
        # Save current code
        current_code = "".join(self.code_lines)
        
        # Clear and rewrite with function wrapper
        self.code_lines = []
        self.code_lines.append(f"(defun {function_name} ()\n")
        self.code_lines.append('  (setq oldcmd (getvar "CMDECHO"))\n')
        self.code_lines.append('  (setvar "CMDECHO" 0)\n\n')
        
        # Indent existing code
        for line in current_code.split('\n'):
            if line.strip():
                self.code_lines.append(f"  {line}\n")
        
        self.code_lines.append('\n  (setvar "CMDECHO" oldcmd)\n')
        self.code_lines.append('  (princ)\n')
        self.code_lines.append(')\n\n')
        
        # Add command hint
        self.code_lines.append(f'(princ "\\nType {function_name[2:]} to run the drawing.")\n')
        self.code_lines.append('(princ)\n')
    
    def get_code(self) -> str:
        """Get generated LISP code as string"""
        return "".join(self.code_lines)
    
    def save_to_file(self, output_path: Path) -> None:
        """
        Save LISP code to file
        
        Args:
            output_path: Output .lsp file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        code = self.get_code()
        
        # Validate balanced parentheses
        if not self._validate_parentheses(code):
            logger.error("Generated LISP has unbalanced parentheses!")
            raise ValueError("Invalid LISP code: unbalanced parentheses")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Saved LISP file: {output_path}")
    
    @staticmethod
    def _validate_parentheses(code: str) -> bool:
        """
        Validate that parentheses are balanced
        
        Returns:
            True if balanced, False otherwise
        """
        count = 0
        for char in code:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
            
            if count < 0:  # More closing than opening
                return False
        
        return count == 0  # Should end at 0


# Testing/validation utilities

def validate_lisp_syntax(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate LISP file syntax
    
    Checks:
    - Balanced parentheses
    - Valid UTF-8 encoding
    - Basic structure
    
    Args:
        file_path: Path to .lsp file
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return (False, [f"Cannot read file: {e}"])
    
    # Check parentheses
    if not AutoLISPWriter._validate_parentheses(content):
        errors.append("Unbalanced parentheses")
    
    # Check for basic LISP structure
    if '(command' not in content and '(defun' not in content:
        errors.append("No LISP commands found")
    
    # Check for invalid characters (control characters except newline/tab)
    for i, char in enumerate(content):
        if ord(char) < 32 and char not in ['\n', '\r', '\t']:
            errors.append(f"Invalid control character at position {i}")
            break
    
    is_valid = len(errors) == 0
    return (is_valid, errors)
