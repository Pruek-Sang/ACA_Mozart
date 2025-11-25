"""Baseline electrical design parameters."""

from typing import Dict, List
from pydantic import BaseModel


class NECBaseline(BaseModel):
    """NEC baseline requirements and constants."""
    
    # Voltage drop limits (percentage)
    voltage_drop_feeder: float = 0.02  # 2%
    voltage_drop_branch: float = 0.03  # 3%
    voltage_drop_total: float = 0.05   # 5%
    
    # Temperature ratings (Celsius)
    conductor_temp_ratings: Dict[str, int] = {
        "60C": 60,
        "75C": 75,
        "90C": 90
    }
    
    # Continuous load factor
    continuous_load_factor: float = 1.25
    
    # Motor load factors
    motor_starting_factor: float = 1.25
    largest_motor_factor: float = 1.25
    
    # Demand factors for receptacles (NEC 220.44)
    receptacle_demand_factors: Dict[str, float] = {
        "first_10kVA": 1.0,
        "remainder": 0.5
    }
    
    # Lighting demand factors (NEC 220.42)
    lighting_demand_factors: Dict[str, float] = {
        "dwelling_first_3000VA": 1.0,
        "dwelling_3001_to_120000VA": 0.35,
        "dwelling_over_120000VA": 0.25
    }
    
    # Standard circuit breaker ratings (Amperes)
    standard_breaker_ratings: List[int] = [
        15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100,
        110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450,
        500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000
    ]
    
    # Minimum circuit ampacities for specific loads
    minimum_ampacities: Dict[str, int] = {
        "receptacle_15A": 15,
        "receptacle_20A": 20,
        "small_appliance": 20,
        "laundry": 20,
        "bathroom": 20
    }


class WireBaseline(BaseModel):
    """Wire sizing baseline data."""
    
    # Copper conductor ampacities at 75°C (NEC Table 310.16)
    copper_ampacity_75C: Dict[str, int] = {
        "14": 20,
        "12": 25,
        "10": 35,
        "8": 50,
        "6": 65,
        "4": 85,
        "3": 100,
        "2": 115,
        "1": 130,
        "1/0": 150,
        "2/0": 175,
        "3/0": 200,
        "4/0": 230,
        "250": 255,
        "300": 285,
        "350": 310,
        "400": 335,
        "500": 380,
        "600": 420,
        "700": 460,
        "750": 475,
        "800": 490,
        "900": 520,
        "1000": 545
    }
    
    # Aluminum conductor ampacities at 75°C
    aluminum_ampacity_75C: Dict[str, int] = {
        "12": 20,
        "10": 30,
        "8": 40,
        "6": 50,
        "4": 65,
        "3": 75,
        "2": 90,
        "1": 100,
        "1/0": 120,
        "2/0": 135,
        "3/0": 155,
        "4/0": 180,
        "250": 205,
        "300": 230,
        "350": 250,
        "400": 270,
        "500": 310,
        "600": 340,
        "700": 375,
        "750": 385,
        "800": 395,
        "900": 425,
        "1000": 445
    }
    
    # Conductor resistance (ohms per 1000 feet at 75°C)
    copper_resistance: Dict[str, float] = {
        "14": 3.07,
        "12": 1.93,
        "10": 1.21,
        "8": 0.764,
        "6": 0.491,
        "4": 0.308,
        "3": 0.245,
        "2": 0.194,
        "1": 0.154,
        "1/0": 0.122,
        "2/0": 0.0967,
        "3/0": 0.0766,
        "4/0": 0.0608,
        "250": 0.0515,
        "300": 0.0429,
        "350": 0.0367,
        "400": 0.0321,
        "500": 0.0258,
        "600": 0.0214,
        "750": 0.0171,
        "1000": 0.0129
    }


class ConduitBaseline(BaseModel):
    """Conduit sizing baseline data."""
    
    # Maximum fill percentages (NEC Chapter 9, Table 1)
    max_fill_percentage: Dict[int, float] = {
        1: 0.53,  # 1 conductor
        2: 0.31,  # 2 conductors
        3: 0.40   # 3 or more conductors
    }
    
    # Conduit trade sizes and internal diameters (inches)
    conduit_sizes: Dict[str, float] = {
        "1/2": 0.622,
        "3/4": 0.824,
        "1": 1.049,
        "1-1/4": 1.380,
        "1-1/2": 1.610,
        "2": 2.067,
        "2-1/2": 2.469,
        "3": 3.068,
        "3-1/2": 3.548,
        "4": 4.026,
        "5": 5.047,
        "6": 6.065
    }
    
    # Wire cross-sectional areas (square inches)
    wire_areas: Dict[str, float] = {
        "14": 0.0097,
        "12": 0.0133,
        "10": 0.0211,
        "8": 0.0366,
        "6": 0.0507,
        "4": 0.0824,
        "3": 0.0973,
        "2": 0.1158,
        "1": 0.1562,
        "1/0": 0.1855,
        "2/0": 0.2223,
        "3/0": 0.2679,
        "4/0": 0.3237,
        "250": 0.3904,
        "300": 0.4536,
        "350": 0.5166,
        "400": 0.5796,
        "500": 0.7073,
        "600": 0.8676,
        "750": 1.0496,
        "1000": 1.3478
    }
