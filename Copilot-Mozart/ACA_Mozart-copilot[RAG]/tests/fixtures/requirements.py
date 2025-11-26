"""
Test Fixtures for MCP Spec Generation
Fixed, deterministic ProjectRequirements (NO LLM parsing)
"""

import json
from pathlib import Path
from typing import Dict, Any
from app.models import ProjectRequirements


def load_example_requirements(name: str) -> ProjectRequirements:
    """
    Load ProjectRequirements from rag_knowledge/example/
    
    NO LLM PARSING - extracts JSON directly from markdown
    
    Args:
        name: Example name (e.g., "house_1floor_basic")
    
    Returns:
        Fixed ProjectRequirements object
    """
    base_path = Path(__file__).parent.parent.parent / "rag_knowledge" / "example"
    file_path = base_path / f"example_req_inputspec_{name}.md"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Example not found: {file_path}")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Extract first JSON block
    import re
    match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found in {file_path}")
    
    # Parse ProjectRequirements section
    data = json.loads(match.group(1))
    
    # Extract just ProjectRequirements if it's wrapped
    if "project_requirements" in data:
        req_data = data["project_requirements"]
    else:
        req_data = data
    
    return ProjectRequirements(**req_data)


def get_basic_house_requirements() -> ProjectRequirements:
    """Fixed requirements for basic 1-floor house"""
    return ProjectRequirements(
        project_name="Test House 1F",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        rooms=[
            {
                "name": "Living Room",
                "type": "LIVING",
                "area_sqm": 20.0
            },
            {
                "name": "Bedroom 1",
                "type": "BEDROOM",
                "area_sqm": 12.0
            },
            {
                "name": "Kitchen",
                "type": "KITCHEN",
                "area_sqm": 8.0
            }
        ],
        loads=[
            {
                "device": "Air Conditioner 12000 BTU",
                "room_name": "Bedroom 1",
                "quantity": 1,
                "power_rating_w": 1200.0
            },
            {
                "device": "Refrigerator",
                "room_name": "Kitchen",
                "quantity": 1,
                "power_rating_w": 300.0
            },
            {
                "device": "LED Lights",
                "room_name": "Living Room",
                "quantity": 4,
                "power_rating_w": 10.0
            }
        ],
        user_constraints=[]
    )


def get_heavy_kitchen_requirements() -> ProjectRequirements:
    """Fixed requirements for house with heavy kitchen loads"""
    return ProjectRequirements(
        project_name="Test House Heavy Kitchen",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        rooms=[
            {
                "name": "Kitchen",
                "type": "KITCHEN",
                "area_sqm": 12.0
            },
            {
                "name": "Living Room",
                "type": "LIVING",
                "area_sqm": 25.0
            }
        ],
        loads=[
            {
                "device": "Induction Cooker",
                "room_name": "Kitchen",
                "quantity": 1,
                "power_rating_w": 3000.0
            },
            {
                "device": "Microwave",
                "room_name": "Kitchen",
                "quantity": 1,
                "power_rating_w": 1500.0
            },
            {
                "device": "Refrigerator",
                "room_name": "Kitchen",
                "quantity": 1,
                "power_rating_w": 300.0
            }
        ],
        user_constraints=["Heavy load kitchen"]
    )
