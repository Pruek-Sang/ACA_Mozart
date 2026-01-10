"""
SLD Renderer - Single Line Diagram Generator

This module generates SLD (Single Line Diagram) data from DisplayData.
Output is structured JSON that frontend can render as SVG or use with React Flow.

[CP-SLD] Checkpoint prefix for all SLD-related logs.

Design Philosophy:
- อ่านจาก compute.py (DisplayData) - Source of Truth
- Output เป็น JSON structure ที่ Frontend render เป็น SVG ได้
- รองรับทั้ง 1-phase และ 3-phase systems

SLD Structure:
```
        ┌──────────────────────────┐
        │   Meter: 30(100)A        │
        └───────────┬──────────────┘
                    │
        ┌───────────┴──────────────┐
        │  Main Breaker: 100A/2P   │
        │  Main Wire: 25mm²        │
        └───────────┬──────────────┘
                    │
     ┌──────────────┼──────────────────┐
     │              │                  │
   ┌─┴─┐          ┌─┴─┐              ┌─┴─┐
   │C1 │          │C2 │              │C3 │
   │20A│          │32A│              │16A│
   └───┘          └───┘              └───┘
```
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict

logger = logging.getLogger("Aura.Display.SLD")


# =============================================================================
# Type Definitions
# =============================================================================

class SLDNode(TypedDict):
    """Single node in the SLD diagram."""
    id: str
    type: str  # 'meter' | 'main_breaker' | 'branch_breaker' | 'load'
    label: str
    x: float
    y: float
    width: float
    height: float
    data: Dict[str, Any]


class SLDEdge(TypedDict):
    """Connection between nodes."""
    id: str
    source: str
    target: str
    style: str  # 'solid' | 'dashed'


class SLDData(TypedDict):
    """Complete SLD data for frontend rendering."""
    nodes: List[SLDNode]
    edges: List[SLDEdge]
    metadata: Dict[str, Any]


# =============================================================================
# Constants
# =============================================================================

# Layout constants (SVG coordinates)
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
NODE_WIDTH = 120
NODE_HEIGHT = 60
VERTICAL_GAP = 80
HORIZONTAL_GAP = 30


# =============================================================================
# Main Render Function
# =============================================================================

def render_sld(display_data: Dict[str, Any]) -> SLDData:
    """
    [CP-SLD] Render SLD data from DisplayData.
    
    Layout: แนวตั้ง (Vertical)
    Power → kWh Meter → Main MCB → RCD → Branch MCBs → Loads
    
    Features:
    - Switch สำหรับ Lighting circuits
    - Cable Label (ขนาดสาย+ท่อ)
    
    Args:
        display_data: DisplayData from compute.py
    
    Returns:
        SLDData: Structured data for frontend SVG rendering
    """
    logger.info("[CP-SLD] Generating SLD diagram data (Vertical Layout)...")
    
    nodes: List[SLDNode] = []
    edges: List[SLDEdge] = []
    
    # Calculate center X
    center_x = CANVAS_WIDTH / 2
    current_y = 40
    
    # 1. Power Source Node (Top)
    power_node: SLDNode = {
        'id': 'power',
        'type': 'power_source',
        'label': 'Power from MEA',
        'x': center_x - NODE_WIDTH / 2,
        'y': current_y,
        'width': NODE_WIDTH,
        'height': 40,
        'data': {'icon': '⚡', 'cable_label': f"2 × {display_data.get('main_wire', '25')}mm² Cu"}
    }
    nodes.append(power_node)
    current_y += 60
    
    # 2. kWh Meter Node
    meter_node = _create_meter_node(display_data, center_x, current_y)
    nodes.append(meter_node)
    edges.append({
        'id': 'edge-power-meter',
        'source': 'power',
        'target': 'meter',
        'style': 'solid'
    })
    current_y += VERTICAL_GAP
    
    # 3. Main Breaker Node (MCCB/MCB)
    main_breaker_node = _create_main_breaker_node(display_data, center_x, current_y)
    nodes.append(main_breaker_node)
    edges.append({
        'id': 'edge-meter-main',
        'source': 'meter',
        'target': 'main_breaker',
        'style': 'solid'
    })
    current_y += VERTICAL_GAP
    
    # 4. RCD Node (optional - for circuits requiring ground fault protection)
    rcd_node: SLDNode = {
        'id': 'rcd',
        'type': 'rcd',
        'label': 'RCD 63A-30mA',
        'x': center_x - NODE_WIDTH / 2,
        'y': current_y,
        'width': NODE_WIDTH,
        'height': 50,
        'data': {'icon': '🛡️', 'rating': '63A-30mA DP RCD'}
    }
    nodes.append(rcd_node)
    edges.append({
        'id': 'edge-main-rcd',
        'source': 'main_breaker',
        'target': 'rcd',
        'style': 'solid'
    })
    current_y += VERTICAL_GAP
    
    # 5. Branch Circuits (arranged vertically)
    circuits = display_data.get('circuits', [])
    num_circuits = len(circuits)
    
    if num_circuits > 0:
        # Calculate circuit positions (distribute horizontally)
        branch_y = current_y
        total_width = min(num_circuits, 8) * NODE_WIDTH + (min(num_circuits, 8) - 1) * HORIZONTAL_GAP
        start_x = center_x - total_width / 2 + NODE_WIDTH / 2
        
        for i, circuit in enumerate(circuits[:8]):  # Limit to 8 circuits per row
            circuit_x = start_x + i * (NODE_WIDTH + HORIZONTAL_GAP)
            circuit_node = _create_circuit_node_vertical(circuit, i, circuit_x, branch_y)
            nodes.append(circuit_node)
            
            # Edge: RCD -> Circuit
            edges.append({
                'id': f'edge-rcd-c{i}',
                'source': 'rcd',
                'target': f'circuit_{i}',
                'style': 'solid'
            })
            
            # 🆕 Add Switch for Lighting circuits (ABOVE the circuit, not below)
            is_lighting = _is_lighting_circuit(circuit)
            if is_lighting:
                # 🔧 FIX: Switch should be ABOVE the circuit breaker (between RCD and circuit)
                switch_y = branch_y - 50  # Position above the circuit
                switch_node: SLDNode = {
                    'id': f'switch_{i}',
                    'type': 'switch',
                    'label': 'Switch',
                    'x': circuit_x - 30,
                    'y': switch_y,
                    'width': 60,
                    'height': 30,
                    'data': {'icon': '⊕', 'circuit_id': f'circuit_{i}'}
                }
                nodes.append(switch_node)
                
                # Edge: RCD -> Switch -> Circuit (Switch is between RCD and circuit)
                # Remove direct RCD->Circuit edge and add RCD->Switch, Switch->Circuit
                edges = [e for e in edges if e['id'] != f'edge-rcd-c{i}']  # Remove direct edge
                edges.append({
                    'id': f'edge-rcd-switch{i}',
                    'source': 'rcd',
                    'target': f'switch_{i}',
                    'style': 'solid'
                })
                edges.append({
                    'id': f'edge-switch{i}-c{i}',
                    'source': f'switch_{i}',
                    'target': f'circuit_{i}',
                    'style': 'solid'
                })
    
    # Calculate canvas height based on content
    canvas_height = max(CANVAS_HEIGHT, current_y + NODE_HEIGHT + 100)
    if num_circuits > 0:
        canvas_height = max(canvas_height, branch_y + NODE_HEIGHT + 80)
    
    # Metadata
    metadata = {
        'project_name': display_data.get('project_name', 'Unknown'),
        'total_kw': display_data.get('total_kw', 0),
        'demand_current': display_data.get('demand_current', 0),
        'circuit_count': num_circuits,
        'canvas_width': CANVAS_WIDTH,
        'canvas_height': canvas_height,
        'layout': 'vertical',  # 🆕 Indicate layout type
        'has_switches': any(_is_lighting_circuit(c) for c in circuits),  # 🆕
    }
    
    sld_data: SLDData = {
        'nodes': nodes,
        'edges': edges,
        'metadata': metadata,
    }
    
    logger.info(f"[CP-SLD] Generated: {len(nodes)} nodes, {len(edges)} edges (vertical layout)")
    return sld_data


def _is_lighting_circuit(circuit: Dict[str, Any]) -> bool:
    """Check if circuit is a lighting circuit (for Switch display)."""
    name = circuit.get('circuit_name', '').lower()
    return any(k in name for k in ['lighting', 'light', 'ไฟ', 'โคม', 'หลอด', 'แสงสว่าง'])


def _create_circuit_node_vertical(circuit: Dict[str, Any], index: int, x: float, y: float) -> SLDNode:
    """Create branch circuit node with Cable Label."""
    name = circuit.get('circuit_name', f'Circuit {index + 1}')
    # 🆕 Allow 2-line wrap instead of truncation
    if len(name) > 18:
        # Split into 2 lines
        mid = len(name) // 2
        # Find space near middle
        space_pos = name.rfind(' ', 0, mid + 5)
        if space_pos > 4:
            name = name[:space_pos] + '\n' + name[space_pos+1:]
        else:
            name = name[:16] + '...'
    
    breaker = circuit.get('breaker_rating', 15)
    poles = circuit.get('breaker_poles', 1)
    wire = circuit.get('wire_size', '2.5')
    conduit = circuit.get('conduit_size', '1/2"')
    rcbo = circuit.get('requires_rcbo', False)
    is_lighting = _is_lighting_circuit(circuit)
    
    # 🆕 Cable Label (สาย + ท่อ)
    cable_label = f"{wire}mm²/{conduit}"
    
    return {
        'id': f'circuit_{index}',
        'type': 'rcbo' if rcbo else 'branch_breaker',
        'label': f"{name}\n{breaker}A/{poles}P",
        'x': x - NODE_WIDTH / 2,
        'y': y,
        'width': NODE_WIDTH,
        'height': NODE_HEIGHT,
        'data': {
            'name': circuit.get('circuit_name', '-'),
            'breaker': f"{breaker}A/{poles}P",
            'wire': f"{wire}mm²",
            'conduit': conduit,
            'cable_label': cable_label,  # 🆕
            'kw': circuit.get('total_kw', 0),
            'current': circuit.get('total_current', 0),
            'rcbo': rcbo,
            'is_lighting': is_lighting,  # 🆕
            'vd_percent': circuit.get('vd_percent', 0),
            'icon': '💡' if is_lighting else ('🛡️' if rcbo else '⚡'),
        }
    }


# =============================================================================
# Node Creation Functions
# =============================================================================

def _create_meter_node(data: Dict[str, Any], x: float, y: float) -> SLDNode:
    """Create meter node."""
    return {
        'id': 'meter',
        'type': 'meter',
        'label': f"มิเตอร์ {data.get('meter_size', '-')}",
        'x': x - NODE_WIDTH / 2,
        'y': y,
        'width': NODE_WIDTH,
        'height': NODE_HEIGHT,
        'data': {
            'meter_size': data.get('meter_size', '-'),
            'icon': '📊',
        }
    }


def _create_main_breaker_node(data: Dict[str, Any], x: float, y: float) -> SLDNode:
    """Create main breaker node."""
    return {
        'id': 'main_breaker',
        'type': 'main_breaker',
        'label': f"Main CB {data.get('main_breaker', '-')}",
        'x': x - NODE_WIDTH / 2,
        'y': y,
        'width': NODE_WIDTH,
        'height': NODE_HEIGHT,
        'data': {
            'breaker': data.get('main_breaker', '-'),
            'wire': data.get('main_wire', '-'),
            'current': f"{data.get('design_current', 0):.1f}A",
            'icon': '🔌',
        }
    }


def _create_circuit_node(circuit: Dict[str, Any], index: int, x: float, y: float) -> SLDNode:
    """Create branch circuit node."""
    name = circuit.get('circuit_name', f'Circuit {index + 1}')
    if len(name) > 12:
        name = name[:10] + '...'
    
    breaker = circuit.get('breaker_rating', 15)
    poles = circuit.get('breaker_poles', 1)
    wire = circuit.get('wire_size', '2.5')
    rcbo = circuit.get('requires_rcbo', False)
    
    return {
        'id': f'circuit_{index}',
        'type': 'rcbo' if rcbo else 'branch_breaker',
        'label': f"{name}\n{breaker}A/{poles}P",
        'x': x - NODE_WIDTH / 2,
        'y': y,
        'width': NODE_WIDTH,
        'height': NODE_HEIGHT,
        'data': {
            'name': circuit.get('circuit_name', '-'),
            'breaker': f"{breaker}A/{poles}P",
            'wire': f"{wire}mm²",
            'kw': circuit.get('total_kw', 0),
            'current': circuit.get('total_current', 0),
            'rcbo': rcbo,
            'vd_percent': circuit.get('vd_percent', 0),
            'icon': '⚡' if not rcbo else '🛡️',
        }
    }


# =============================================================================
# SVG Generator (Optional - for server-side rendering)
# =============================================================================

def render_sld_svg(sld_data: SLDData) -> str:
    """
    [CP-SLD-SVG] Generate SVG string from SLD data.
    
    This can be used for:
    - Server-side rendering
    - PDF export
    - Email attachments
    """
    logger.info("[CP-SLD-SVG] Generating SVG...")
    
    width = sld_data['metadata'].get('canvas_width', CANVAS_WIDTH)
    height = sld_data['metadata'].get('canvas_height', CANVAS_HEIGHT)
    
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <defs>',
        '    <style>',
        '      .node { fill: #1e293b; stroke: #0ea5e9; stroke-width: 2; rx: 8; }',
        '      .node-meter { fill: #0f172a; stroke: #22c55e; }',
        '      .node-main { fill: #0f172a; stroke: #f59e0b; }',
        '      .node-rcbo { fill: #1e293b; stroke: #8b5cf6; }',
        '      .label { font-family: sans-serif; font-size: 12px; fill: white; text-anchor: middle; }',
        '      .label-sub { font-size: 10px; fill: #94a3b8; }',
        '      .edge { stroke: #0ea5e9; stroke-width: 2; fill: none; }',
        '    </style>',
        '  </defs>',
        '  <rect width="100%" height="100%" fill="#0f172a"/>',
    ]
    
    # Draw edges first (behind nodes)
    for edge in sld_data['edges']:
        source = next((n for n in sld_data['nodes'] if n['id'] == edge['source']), None)
        target = next((n for n in sld_data['nodes'] if n['id'] == edge['target']), None)
        
        if source and target:
            x1 = source['x'] + source['width'] / 2
            y1 = source['y'] + source['height']
            x2 = target['x'] + target['width'] / 2
            y2 = target['y']
            
            svg_lines.append(f'  <path class="edge" d="M{x1},{y1} L{x1},{(y1+y2)/2} L{x2},{(y1+y2)/2} L{x2},{y2}"/>')
    
    # Draw nodes
    for node in sld_data['nodes']:
        x, y, w, h = node['x'], node['y'], node['width'], node['height']
        
        node_class = 'node'
        if node['type'] == 'meter':
            node_class = 'node node-meter'
        elif node['type'] == 'main_breaker':
            node_class = 'node node-main'
        elif node['type'] == 'rcbo':
            node_class = 'node node-rcbo'
        
        svg_lines.append(f'  <rect class="{node_class}" x="{x}" y="{y}" width="{w}" height="{h}"/>')
        svg_lines.append(f'  <text class="label" x="{x + w/2}" y="{y + h/2 - 5}">{node["label"].split(chr(10))[0]}</text>')
        
        if '\n' in node['label']:
            svg_lines.append(f'  <text class="label label-sub" x="{x + w/2}" y="{y + h/2 + 15}">{node["label"].split(chr(10))[1]}</text>')
    
    # Title
    project = sld_data['metadata'].get('project_name', 'SLD')
    svg_lines.append(f'  <text class="label" x="{width/2}" y="25" style="font-size:16px">Single Line Diagram - {project}</text>')
    
    svg_lines.append('</svg>')
    
    result = '\n'.join(svg_lines)
    logger.info(f"[CP-SLD-SVG] Generated {len(result)} bytes SVG")
    
    return result
