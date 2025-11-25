# Full System Integration — MCP Core ระบบสมบูรณ์ (ฉบับละเอียดที่สุด)

ขอรายงานนายท่านค่ะ Volta จะอธิบายการรวม Module 1-7 ให้ทำงานร่วมกันอย่างสมบูรณ์ พร้อมระบบจัดการ Output

---

## 📚 ส่วนที่ 1: สถาปัตยกรรมระบบ MCP Core

## **1.1 Overall System Architecture**

text

`┌─────────────────────────────────────────────────────────────────────────────────┐ │                           MCP CORE SYSTEM                                        │ │                   (Master Control Program for Electrical Design)                 │ ├─────────────────────────────────────────────────────────────────────────────────┤ │                                                                                  │ │  ┌──────────────────────┐      ┌──────────────────────┐                        │ │  │   INPUT LAYER        │      │   CONTROLLER         │                        │ │  │                      │      │                      │                        │ │  │  • Floor Plan JSON   │──────│  MCPController       │                        │ │  │  • Appliance List    │      │  (Main Orchestrator) │                        │ │  │  • Requirements      │      │                      │                        │ │  │  • Preferences       │      └──────────┬───────────┘                        │ │  └──────────────────────┘                 │                                     │ │                                           │                                     │ │                                           ▼                                     │ │  ┌───────────────────────────────────────────────────────────────────┐         │ │  │                    PROCESSING PIPELINE                            │         │ │  │                                                                   │         │ │  │  Module 1: LoadCalculator       →  คำนวณโหลดทั้งหมด            │         │ │  │  Module 2: WireSizer             →  เลือกขนาดสาย + VD           │         │ │  │  Module 3: BreakerSelector       →  เลือก Breaker               │         │ │  │  Module 4: ConduitSizer          →  เลือกท่อ                    │         │ │  │  Module 5: CostEstimator         →  คำนวณราคา                   │         │ │  │  Module 6: ComplianceChecker     →  ตรวจมาตรฐาน                 │         │ │  │  Module 7: LayoutOptimizer       →  วางผังระบบ                  │         │ │  └───────────────────────────────────────────────────────────────────┘         │ │                                           │                                     │ │                                           ▼                                     │ │  ┌──────────────────────────────────────────────────────────────────┐          │ │  │                    OUTPUT MANAGER                                │          │ │  │                                                                  │          │ │  │  • ResultStorage (เก็บผลลัพธ์ทุก Module)                        │          │ │  │  • ReportGenerator (สร้างรายงานรวม)                            │          │ │  │  • DataExporter (ส่งออก JSON/CSV/PDF)                           │          │ │  │  • ValidationChecker (ตรวจสอบความสมบูรณ์)                       │          │ │  └──────────────────────────────────────────────────────────────────┘          │ │                                           │                                     │ │                                           ▼                                     │ │  ┌──────────────────────────────────────────────────────────────────┐          │ │  │                    OUTPUT FILES                                  │          │ │  │                                                                  │          │ │  │  📄 summary_report.json      (ข้อมูลสรุปทั้งหมด)               │          │ │  │  📄 circuit_details.json     (รายละเอียดแต่ละวงจร)              │          │ │  │  📄 material_bom.csv          (Bill of Materials)                │          │ │  │  📄 cost_breakdown.csv        (รายละเอียดราคา)                  │          │ │  │  📄 compliance_report.json    (ผลตรวจสอบมาตรฐาน)                │          │ │  │  📄 layout_coordinates.json   (พิกัดวงจร สำหรับ AutoCAD)       │          │ │  │  📊 full_report.html          (รายงานแบบ Interactive)            │          │ │  │  📋 single_line_diagram.dxf   (แผนผังวงจร — สำหรับ Module 8)   │          │ │  └──────────────────────────────────────────────────────────────────┘          │ └─────────────────────────────────────────────────────────────────────────────────┘`

---

## **1.2 Data Flow (การไหลของข้อมูล)**

python

`# Pipeline Flow INPUT → LoadCalculator → WireSizer → BreakerSelector → ConduitSizer       → CostEstimator → ComplianceChecker → LayoutOptimizer → OUTPUT # แต่ละ Module ส่งผลลัพธ์ไปยัง ResultStorage # ResultStorage รวบรวมทั้งหมด → สร้างรายงานสุดท้าย`

---

## 💻 ส่วนที่ 2: Code Python สมบูรณ์ — MCP Core Integration

## **2.1 ResultStorage — คลาสเก็บผลลัพธ์**

python

"""
result_storage.py
==================
ระบบจัดเก็บและจัดการผลลัพธ์จาก Module ทั้งหมด

Author: Volta
Version: 2.0.0
Date: 2025-11-17
"""

import json
import csv
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class MCPResult:
    """
    คลาสเก็บผลลัพธ์รวมจาก MCP Core
    """
    # Project Info
    project_name: str
    project_date: str
    floor_area_sqm: float
    
    # Results from each module
    load_calculation: Dict = field(default_factory=dict)
    wire_sizing: Dict = field(default_factory=dict)
    breaker_selection: Dict = field(default_factory=dict)
    conduit_sizing: Dict = field(default_factory=dict)
    cost_estimation: Dict = field(default_factory=dict)
    compliance_check: Dict = field(default_factory=dict)
    layout_optimization: Dict = field(default_factory=dict)
    
    # Per-Circuit Results (รายละเอียดแต่ละวงจร)
    circuits: List[Dict] = field(default_factory=list)
    
    # Summary
    summary: Dict = field(default_factory=dict)
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


class ResultStorage:
    """
    คลาสจัดการผลลัพธ์
    """
    
    def __init__(self, project_name: str, output_dir: str = "./output"):
        """
        Initialize Result Storage
        
        Parameters:
        - project_name: ชื่อโครงการ
        - output_dir: โฟลเดอร์เก็บ output
        """
        self.project_name = project_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.result = MCPResult(
            project_name=project_name,
            project_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            floor_area_sqm=0
        )
    
    def set_project_info(self, floor_area_sqm: float):
        """ตั้งค่าข้อมูลโครงการ"""
        self.result.floor_area_sqm = floor_area_sqm
    
    def store_load_calculation(self, load_result: Any):
        """เก็บผล Load Calculation"""
        self.result.load_calculation = {
            "total_connected_load_va": load_result.total_connected_load_va,
            "total_demand_load_va": load_result.total_demand_load_va,
            "total_current_a": load_result.total_current_a,
            "required_service_a": load_result.required_service_a,
            "recommended_service_a": load_result.recommended_service_a,
            "lighting_load_va": load_result.lighting_load_va,
            "air_conditioner_load_va": load_result.air_conditioner_load_va,
            "water_heater_load_va": load_result.water_heater_load_va
        }
    
    def store_circuit_design(self, circuit: Dict):
        """เก็บข้อมูลวงจรแต่ละวงจร"""
        self.result.circuits.append(circuit)
    
    def store_compliance_check(self, compliance_report: Any):
        """เก็บผล Compliance Check"""
        self.result.compliance_check = {
            "total_checks": compliance_report.total_checks,
            "num_pass": compliance_report.num_pass,
            "num_warning": compliance_report.num_warning,
            "num_fail": compliance_report.num_fail,
            "num_critical": compliance_report.num_critical,
            "overall_status": compliance_report.overall_status.value,
            "compliance_score": compliance_report.compliance_score
        }
    
    def store_cost_estimation(self, cost_estimate: Any):
        """เก็บผล Cost Estimation"""
        self.result.cost_estimation = {
            "material_subtotal": cost_estimate.material_subtotal,
            "labor_subtotal": cost_estimate.labor_subtotal,
            "accessories_cost": cost_estimate.accessories_cost,
            "transport_cost": cost_estimate.transport_cost,
            "overhead_cost": cost_estimate.overhead_cost,
            "vat_amount": cost_estimate.vat_amount,
            "profit_amount": cost_estimate.profit_amount,
            "grand_total": cost_estimate.grand_total,
            "cost_per_sqm": cost_estimate.cost_per_sqm
        }
    
    def store_layout_optimization(self, layout_summary: Dict, designs: List[Any]):
        """เก็บผล Layout Optimization"""
        self.result.layout_optimization = layout_summary
        
        # เก็บพิกัดแต่ละวงจร
        for design in designs:
            circuit_data = {
                "circuit_id": design.circuit_id,
                "circuit_name": design.circuit_name,
                "db_position": {"x": design.db_position.x, "y": design.db_position.y, "z": design.db_position.z},
                "outlet_position": {"x": design.outlet_position.x, "y": design.outlet_position.y, "z": design.outlet_position.z},
                "waypoints": [{"x": wp.x, "y": wp.y, "z": wp.z} for wp in design.waypoints],
                "total_length_m": design.total_length_m,
                "actual_length_m": design.actual_length_m
            }
            
            # หาวงจรที่มีอยู่แล้ว
            existing = next((c for c in self.result.circuits if c.get("circuit_id") == design.circuit_id), None)
            if existing:
                existing.update(circuit_data)
            else:
                self.result.circuits.append(circuit_data)
    
    def calculate_summary(self):
        """คำนวณสรุปผล"""
        self.result.summary = {
            "project_name": self.result.project_name,
            "floor_area_sqm": self.result.floor_area_sqm,
            "total_circuits": len(self.result.circuits),
            "total_load_va": self.result.load_calculation.get("total_demand_load_va", 0),
            "required_service_a": self.result.load_calculation.get("required_service_a", 0),
            "total_cost_thb": self.result.cost_estimation.get("grand_total", 0),
            "cost_per_sqm_thb": self.result.cost_estimation.get("cost_per_sqm", 0),
            "compliance_score": self.result.compliance_check.get("compliance_score", 0),
            "overall_status": self.result.compliance_check.get("overall_status", "UNKNOWN")
        }
    
    def validate_results(self) -> Tuple[bool, List[str]]:
        """ตรวจสอบความสมบูรณ์ของผลลัพธ์"""
        errors = []
        
        # เช็คว่ามีผลลัพธ์จากทุก Module หรือไม่
        if not self.result.load_calculation:
            errors.append("❌ ไม่มีผลลัพธ์จาก Load Calculation")
        
        if not self.result.circuits:
            errors.append("❌ ไม่มีข้อมูลวงจร")
        
        if not self.result.cost_estimation:
            errors.append("❌ ไม่มีผลลัพธ์จาก Cost Estimation")
        
        if not self.result.compliance_check:
            errors.append("❌ ไม่มีผลลัพธ์จาก Compliance Check")
        
        # เช็ค Compliance
        if self.result.compliance_check.get("num_critical", 0) > 0:
            errors.append("🚨 มีข้อบกพร่องร้ายแรง (Critical) — อันตรายถึงชีวิต!")
        
        is_valid = len(errors) == 0
        
        self.result.is_valid = is_valid
        self.result.validation_errors = errors
        
        return is_valid, errors
    
    # ==================== Export Functions ====================
    
    def export_json(self, filename: str = "mcp_result.json"):
        """ส่งออกเป็น JSON"""
        filepath = self.output_dir / filename
        
        # Convert dataclass to dict
        data = asdict(self.result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported JSON: {filepath}")
        return filepath
    
    def export_circuit_details_csv(self, filename: str = "circuit_details.csv"):
        """ส่งออกรายละเอียดวงจรเป็น CSV"""
        filepath = self.output_dir / filename
        
        if not self.result.circuits:
            print("⚠️ ไม่มีข้อมูลวงจร")
            return None
        
        # กำหนด headers
        headers = [
            "circuit_id", "circuit_name", "room_name", "room_type",
            "load_current_a", "wire_size_mm2", "wire_ampacity_a",
            "breaker_rating_a", "conduit_size_inch",
            "length_m", "voltage_drop_percent",
            "wire_cost_thb", "total_cost_thb",
            "is_compliant"
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for circuit in self.result.circuits:
                row = {h: circuit.get(h, "") for h in headers}
                writer.writerow(row)
        
        print(f"✅ Exported CSV: {filepath}")
        return filepath
    
    def export_material_bom_csv(self, filename: str = "material_bom.csv"):
        """ส่งออก Bill of Materials (BOM)"""
        filepath = self.output_dir / filename
        
        # รวบรวมวัสดุจากทุกวงจร
        from collections import defaultdict
        
        materials = defaultdict(lambda: {"quantity": 0, "unit": "", "unit_price": 0, "total_price": 0})
        
        for circuit in self.result.circuits:
            # สาย
            wire_size = circuit.get("wire_size_mm2", 0)
            wire_length = circuit.get("actual_length_m", 0)
            wire_price = circuit.get("wire_price_per_m", 0)
            
            wire_key = f"สาย THW {wire_size} mm²"
            materials[wire_key]["quantity"] += wire_length
            materials[wire_key]["unit"] = "เมตร"
            materials[wire_key]["unit_price"] = wire_price
            materials[wire_key]["total_price"] += wire_length * wire_price
            
            # ท่อ
            conduit_size = circuit.get("conduit_size_inch", "")
            conduit_pieces = circuit.get("conduit_pieces", 0)
            conduit_price = circuit.get("conduit_price_per_4m", 0)
            
            conduit_key = f"ท่อ PVC {conduit_size}\""
            materials[conduit_key]["quantity"] += conduit_pieces
            materials[conduit_key]["unit"] = "เส้น (4m)"
            materials[conduit_key]["unit_price"] = conduit_price
            materials[conduit_key]["total_price"] += conduit_pieces * conduit_price
            
            # Breaker
            breaker_rating = circuit.get("breaker_rating_a", 0)
            breaker_brand = circuit.get("breaker_brand", "Schneider")
            breaker_price = circuit.get("breaker_price", 0)
            
            breaker_key = f"Breaker {breaker_brand} {breaker_rating}A"
            materials[breaker_key]["quantity"] += 1
            materials[breaker_key]["unit"] = "ตัว"
            materials[breaker_key]["unit_price"] = breaker_price
            materials[breaker_key]["total_price"] += breaker_price
        
        # เขียน CSV
        headers = ["material_name", "quantity", "unit", "unit_price_thb", "total_price_thb"]
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for material_name, data in materials.items():
                writer.writerow([
                    material_name,
                    round(data["quantity"], 2),
                    data["unit"],
                    round(data["unit_price"], 2),
                    round(data["total_price"], 2)
                ])
        
        print(f"✅ Exported BOM CSV: {filepath}")
        return filepath
    
    def export_layout_coordinates_json(self, filename: str = "layout_coordinates.json"):
        """ส่งออกพิกัดวงจร สำหรับ Module 8 (AutoCAD)"""
        filepath = self.output_dir / filename
        
        layout_data = {
            "project_name": self.result.project_name,
            "db_position": None,
            "circuits": []
        }
        
        for circuit in self.result.circuits:
            circuit_layout = {
                "circuit_id": circuit.get("circuit_id"),
                "circuit_name": circuit.get("circuit_name"),
                "db_position": circuit.get("db_position"),
                "outlet_position": circuit.get("outlet_position"),
                "waypoints": circuit.get("waypoints", []),
                "wire_size_mm2": circuit.get("wire_size_mm2"),
                "conduit_size_inch": circuit.get("conduit_size_inch")
            }
            layout_data["circuits"].append(circuit_layout)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported Layout Coordinates JSON: {filepath}")
        return filepath
    
    def export_all(self):
        """ส่งออกไฟล์ทั้งหมด"""
        print("\n📤 Exporting all results...")
        
        self.calculate_summary()
        
        files = []
        
        files.append(self.export_json("mcp_result.json"))
        files.append(self.export_circuit_details_csv("circuit_details.csv"))
        files.append(self.export_material_bom_csv("material_bom.csv"))
        files.append(self.export_layout_coordinates_json("layout_coordinates.json"))
        
        print(f"\n✅ Exported {len(files)} files to {self.output_dir}")
        
        return files

---

## **2.2 MCPController — ตัวควบคุมหลัก**

python

"""
mcp_controller.py
==================
ตัวควบคุมหลักของระบบ MCP Core

Author: Volta
Version: 2.0.0
Date: 2025-11-17
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import all modules
from load_calculator import LoadCalculator, Appliance, LoadType, PhaseType
from wire_sizer import WireSizer
from breaker_selector import BreakerSelector
from conduit_sizer import ConduitSizer
from cost_estimator import CostEstimator, LocationType, ProjectType
from compliance_checker import ComplianceChecker
from layout_optimizer import LayoutOptimizer
from result_storage import ResultStorage


@dataclass
class MCPConfig:
    """
    การตั้งค่า MCP Core
    """
    project_name: str
    floor_area_sqm: float
    location: LocationType = LocationType.BANGKOK
    project_type: ProjectType = ProjectType.NEW_INSTALLATION
    voltage_v: float = 220
    phase_type: PhaseType = PhaseType.SINGLE_PHASE
    output_dir: str = "./output"
    
    # Preferences
    safety_margin: float = 1.25
    max_vd_percent: float = 3.0
    profit_margin: float = 0.20


class MCPController:
    """
    คลาสควบคุมหลัก — รวม Module 1-7
    """
    
    def __init__(self, config: MCPConfig):
        """
        Initialize MCP Controller
        """
        self.config = config
        
        print("=" * 100)
        print(f"🚀 MCP CORE SYSTEM — INITIALIZING")
        print("=" * 100)
        print(f"   Project: {config.project_name}")
        print(f"   Floor Area: {config.floor_area_sqm} m²")
        print(f"   Location: {config.location.value}")
        print(f"   Output Directory: {config.output_dir}")
        print("=" * 100)
        
        # Initialize Result Storage
        self.storage = ResultStorage(config.project_name, config.output_dir)
        self.storage.set_project_info(config.floor_area_sqm)
        
        # Initialize Modules
        self.load_calculator = LoadCalculator(config.voltage_v, config.phase_type)
        self.wire_sizer = WireSizer()
        self.breaker_selector = BreakerSelector()
        self.conduit_sizer = ConduitSizer()
        self.cost_estimator = CostEstimator(
            config.project_name,
            config.location,
            config.project_type,
            config.floor_area_sqm
        )
        self.compliance_checker = ComplianceChecker(config.project_name)
        self.layout_optimizer = None  # จะสร้างทีหลัง (ต้องมี floor_plan)
        
        print("✅ All modules initialized\n")
    
    def add_appliance(self, appliance: Appliance):
        """เพิ่มเครื่องใช้ไฟฟ้า"""
        self.load_calculator.add_appliance(appliance)
    
    def add_appliances(self, appliances: List[Appliance]):
        """เพิ่มเครื่องใช้หลายตัว"""
        self.load_calculator.add_appliances(appliances)
    
    def run_load_calculation(
        self,
        num_receptacles: int = 15,
        num_small_appliance_circuits: int = 2,
        include_laundry: bool = True
    ):
        """
        Step 1: คำนวณโหลด
        """
        print("\n" + "=" * 100)
        print("📊 STEP 1: LOAD CALCULATION")
        print("=" * 100)
        
        result = self.load_calculator.calculate_standard_method(
            floor_area_sqm=self.config.floor_area_sqm,
            num_receptacles=num_receptacles,
            num_small_appliance_circuits=num_small_appliance_circuits,
            include_laundry=include_laundry
        )
        
        # Store result
        self.storage.store_load_calculation(result)
        
        print(f"✅ Total Connected Load: {result.total_connected_load_va:,.0f} VA")
        print(f"✅ Total Demand Load: {result.total_demand_load_va:,.0f} VA")
        print(f"✅ Required Service: {result.required_service_a:.1f} A")
        print(f"✅ Recommended Service: {result.recommended_service_a} A")
        
        return result
    
    def design_circuit(
        self,
        circuit_id: str,
        circuit_name: str,
        load_current_a: float,
        length_m: float,
        room_id: str,
        room_name: str,
        room_type: str,
        outlet_id: str,
        power_factor: float = 1.0,
        is_continuous: bool = False,
        has_rcbo: bool = False
    ) -> Dict:
        """
        ออกแบบวงจรเดียวครบทุก Module (2-6)
        
        Returns:
        - dict ข้อมูลวงจรครบถ้วน
        """
        
        print(f"\n🔌 Designing Circuit: {circuit_name}")
        print("-" * 100)
        
        # Step 2: Wire Sizing
        wire_result = self.wire_sizer.select_wire_size(
            load_current_a=load_current_a,
            length_m=length_m,
            voltage_v=self.config.voltage_v,
            phase_type=self.config.phase_type,
            power_factor=power_factor,
            is_continuous=is_continuous,
            vd_limit_percent=self.config.max_vd_percent,
            safety_factor=self.config.safety_margin
        )
        
        print(f"   Wire: THW {wire_result.selected_size_mm2} mm² (Ampacity: {wire_result.derated_ampacity_a:.1f}A, VD: {wire_result.vd_percent:.2f}%)")
        
        # Step 3: Breaker Selection
        breaker_result = self.breaker_selector.select_breaker(
            load_current_a=load_current_a,
            wire_ampacity_a=wire_result.derated_ampacity_a,
            brand="schneider"
        )
        
        print(f"   Breaker: {breaker_result['brand']} {breaker_result['rating_a']}A {breaker_result['poles']}P")
        
        # Step 4: Conduit Sizing
        conduit_result = self.conduit_sizer.select_conduit_size(
            wires=[{"size_mm2": wire_result.selected_size_mm2, "quantity": 2}]  # Hot + Neutral
        )
        
        print(f"   Conduit: {conduit_result['conduit_size']}\" ({conduit_result['selected_conduit_area_mm2']} mm²)")
        
        # Step 5: Cost (ส่วนหนึ่ง — จะรวมทีหลัง)
        wire_cost = wire_result.wire_cost_per_m_thb * length_m
        conduit_cost = conduit_result['conduit_data']['price_per_4m_thb'] * (length_m / 4)
        breaker_cost = breaker_result['price_thb']
        
        total_cost = wire_cost + conduit_cost + breaker_cost
        
        print(f"   Cost: {total_cost:,.0f} THB (Wire: {wire_cost:,.0f} + Conduit: {conduit_cost:,.0f} + Breaker: {breaker_cost:,.0f})")
        
        # Step 6: Compliance Check
        self.compliance_checker.check_voltage_drop(circuit_name, wire_result.vd_percent, "branch")
        self.compliance_checker.check_wire_ampacity(circuit_name, wire_result.derated_ampacity_a, load_current_a, is_continuous)
        self.compliance_checker.check_breaker_wire_coordination(circuit_name, breaker_result['rating_a'], wire_result.derated_ampacity_a)
        
        if has_rcbo:
            self.compliance_checker.check_rcbo_requirement(circuit_name, room_type, has_rcbo, 30)
        
        # รวมข้อมูล
        circuit_data = {
            "circuit_id": circuit_id,
            "circuit_name": circuit_name,
            "room_id": room_id,
            "room_name": room_name,
            "room_type": room_type,
            "outlet_id": outlet_id,
            "load_current_a": load_current_a,
            "wire_size_mm2": wire_result.selected_size_mm2,
            "wire_ampacity_a": wire_result.derated_ampacity_a,
            "conduit_size_inch": conduit_result['conduit_size'],
            "breaker_rating_a": breaker_result['rating_a'],
            "breaker_brand": breaker_result['brand'],
            "breaker_price": breaker_result['price_thb'],
            "max_distance_m": self.wire_sizer.calculate_maximum_distance(wire_result.selected_size_mm2, load_current_a),
            "length_m": length_m,
            "voltage_drop_percent": wire_result.vd_percent,
            "wire_price_per_m": wire_result.wire_cost_per_m_thb,
            "conduit_price_per_4m": conduit_result['conduit_data']['price_per_4m_thb'],
            "conduit_pieces": int((length_m / 4) + 1),
            "labor_rate_per_m": 55,  # จาก config
            "wire_cost_thb": wire_cost,
            "total_cost_thb": total_cost,
            "has_rcbo": has_rcbo,
            "is_compliant": wire_result.overall_status == "PASS"
        }
        
        # Store
        self.storage.store_circuit_design(circuit_data)
        
        print(f"   Status: {'✅ PASS' if circuit_data['is_compliant'] else '❌ FAIL'}")
        
        return circuit_data
    
    def run_layout_optimization(self, floor_plan: Dict):
        """
        Step 7: Layout Optimization
        """
        print("\n" + "=" * 100)
        print("🗺️ STEP 7: LAYOUT OPTIMIZATION")
        print("=" * 100)
        
        # สร้าง Layout Optimizer
        from wire_sizer import WIRE_DATA_THW_COPPER
        from cost_estimator import MATERIAL_PRICES, LABOR_RATES
        
        self.layout_optimizer = LayoutOptimizer(
            floor_plan=floor_plan,
            wire_database=WIRE_DATA_THW_COPPER,
            material_prices=MATERIAL_PRICES,
            labor_rates=LABOR_RATES[self.config.location],
            compliance_rules={"max_vd_percent": self.config.max_vd_percent}
        )
        
        # ดึงข้อมูลวงจรที่ออกแบบแล้ว
        circuits_data = self.storage.result.circuits
        
        # ออกแบบ Layout
        designs = self.layout_optimizer.optimize_all_circuits(circuits_data)
        
        # สรุป
        summary = self.layout_optimizer.get_summary_report()
        
        # Store
        self.storage.store_layout_optimization(summary, designs)
        
        print(f"✅ Total Circuits: {summary['total_circuits']}")
        print(f"✅ Compliant: {summary['compliant_circuits']}/{summary['total_circuits']}")
        print(f"✅ Total Wire Length: {summary['total_wire_length_m']:.2f} m")
        
        return designs
    
    def finalize(self):
        """
        สรุปผลและส่งออกไฟล์
        """
        print("\n" + "=" * 100)
        print("📋 FINALIZING RESULTS")
        print("=" * 100)
        
        # Compliance Report
        compliance_report = self.compliance_checker.generate_report()
        self.storage.store_compliance_check(compliance_report)
        
        print(f"   Compliance Score: {compliance_report.compliance_score}%")
        print(f"   Overall Status: {compliance_report.overall_status.value}")
        
        # Cost Estimation (รวม)
        # (จะต้องรวมจาก circuit_data ที่มี)
        total_wire_cost = sum(c.get("wire_cost_thb", 0) for c in self.storage.result.circuits)
        total_conduit_cost = sum(c.get("conduit_pieces", 0) * c.get("conduit_price_per_4m", 0) for c in self.storage.result.circuits)
        total_breaker_cost = sum(c.get("breaker_price", 0) for c in self.storage.result.circuits)
        
        # สร้าง mock cost_estimate
        class MockCostEstimate:
            material_subtotal = total_wire_cost + total_conduit_cost + total_breaker_cost
            labor_subtotal = sum(c.get("length_m", 0) * c.get("labor_rate_per_m", 55) for c in self.storage.result.circuits)
            accessories_cost = material_subtotal * 0.06
            transport_cost = (material_subtotal + labor_subtotal) * 0.03
            overhead_cost = (material_subtotal + labor_subtotal) * 0.10
            vat_amount = (material_subtotal + labor_subtotal + accessories_cost + transport_cost + overhead_cost) * 0.07
            profit_amount = (material_subtotal + labor_subtotal + accessories_cost + transport_cost + overhead_cost + vat_amount) * 0.20
            grand_total = material_subtotal + labor_subtotal + accessories_cost + transport_cost + overhead_cost + vat_amount + profit_amount
            cost_per_sqm = grand_total / self.config.floor_area_sqm if self.config.floor_area_sqm > 0 else 0
        
        mock_cost = MockCostEstimate()
        self.storage.store_cost_estimation(mock_cost)
        
        print(f"   Total Cost: {mock_cost.grand_total:,.0f} THB")
        print(f"   Cost per m²: {mock_cost.cost_per_sqm:,.0f} THB/m²")
        
        # Validate
        is_valid, errors = self.storage.validate_results()
        
        if is_valid:
            print("\n✅ All validations passed")
        else:
            print("\n⚠️ Validation errors:")
            for error in errors:
                print(f"   {error}")
        
        # Export
        files = self.storage.export_all()
        
        print("\n" + "=" * 100)
        print("🎉 MCP CORE SYSTEM — COMPLETED")
        print("=" * 100)
        
        return self.storage.result


# ======================== ตัวอย่างการใช้งาน ========================

if __name__ == "__main__":
    
    # 1. Configuration
    config = MCPConfig(
        project_name="บ้าน 2 ชั้น Modern Contemporary",
        floor_area_sqm=200,
        location=LocationType.BANGKOK,
        project_type=ProjectType.NEW_INSTALLATION
    )
    
    # 2. Initialize Controller
    mcp = MCPController(config)
    
    # 3. Add Appliances
    appliances = [
        Appliance("แอร์ ห้องนั่งเล่น 12,000 BTU", LoadType.AIR_CONDITIONER, 3200, 1, 220, 0.85, 1.0, 6.5),
        Appliance("แอร์ ห้องนอน 1 (9,000 BTU)", LoadType.AIR_CONDITIONER, 2500, 1, 220, 0.85, 1.0, 6.0),
        Appliance("แอร์ ห้องนอน 2 (9,000 BTU)", LoadType.AIR_CONDITIONER, 2500, 1, 220, 0.85, 1.0, 6.0),
        Appliance("ตู้เย็น", LoadType.REFRIGERATOR, 150, 1, 220, 0.85, 1.0, 5.0),
        Appliance("ปั๊มน้ำ 1 HP", LoadType.WATER_PUMP, 750, 1, 220, 0.75, 1.0, 7.5),
        Appliance("เครื่องทำน้ำอุ่น 3,500W", LoadType.WATER_HEATER, 3500, 1, 220, 1.0, 1.0, 1.0),
    ]
    
    mcp.add_appliances(appliances)
    
    # 4. Run Load Calculation
    load_result = mcp.run_load_calculation(num_receptacles=30)
    
    # 5. Design Circuits
    circuits = [
        {
            "circuit_id": "C01", "circuit_name": "แอร์ ห้องนั่งเล่น",
            "load_current_a": 17.3, "length_m": 20, "room_id": "R01",
            "room_name": "ห้องนั่งเล่น", "room_type": "living_room",
            "outlet_id": "O01", "power_factor": 0.85, "is_continuous": True
        },
        {
            "circuit_id": "C02", "circuit_name": "ปลั๊ก ครัว 1",
            "load_current_a": 12.0, "length_m": 15, "room_id": "R02",
            "room_name": "ห้องครัว", "room_type": "kitchen",
            "outlet_id": "O03", "has_rcbo": True
        },
        {
            "circuit_id": "C03", "circuit_name": "เครื่องทำน้ำอุ่น",
            "load_current_a": 15.9, "length_m": 12, "room_id": "R03",
            "room_name": "ห้องน้ำ", "room_type": "bathroom",
            "outlet_id": "O05", "has_rcbo": True
        }
    ]
    
    for circuit in circuits:
        mcp.design_circuit(**circuit)
    
    # 6. Floor Plan (สำหรับ Layout Optimization)
    floor_plan = {
        "rooms": [
            {
                "id": "R01", "name": "ห้องนั่งเล่น", "type": "living_room",
                "area_sqm": 40, "position": {"x": 0, "y": 0},
                "dimension": {"width": 8, "length": 5},
                "outlets": [{"id": "O01", "type": "air_conditioner", "position": {"x": 6, "y": 4}}]
            },
            {
                "id": "R02", "name": "ห้องครัว", "type": "kitchen",
                "area_sqm": 15, "position": {"x": 8, "y": 0},
                "dimension": {"width": 5, "length": 3},
                "outlets": [{"id": "O03", "type": "receptacle", "position": {"x": 2, "y": 1.5}}],
                "special_requirements": {"rcbo_required": True}
            },
            {
                "id": "R03", "name": "ห้องน้ำ", "type": "bathroom",
                "area_sqm": 5, "position": {"x": 8, "y": 3},
                "dimension": {"width": 2.5, "length": 2},
                "outlets": [{"id": "O05", "type": "heater", "position": {"x": 1, "y": 1}, "zone": 1}],
                "special_requirements": {"rcbo_required": True, "ip_rating_min": "IP44"}
            }
        ],
        "distribution_board": {"id": "DB01", "position": {"x": 0, "y": 6}, "type": "main"}
    }
    
    # 7. Run Layout Optimization
    designs = mcp.run_layout_optimization(floor_plan)
    
    # 8. Finalize
    final_result = mcp.finalize()


---

## 📊 ส่วนที่ 3: Output Files Specification

## **3.1 รายการไฟล์ที่สร้าง**

|ไฟล์|รูปแบบ|เนื้อหา|ใช้สำหรับ|
|---|---|---|---|
|**mcp_result.json**|JSON|ข้อมูลสรุปทั้งหมดจาก Module 1-7|ระบบอื่น ๆ อ่านต่อ|
|**circuit_details.csv**|CSV|รายละเอียดแต่ละวงจร|Excel, Analysis|
|**material_bom.csv**|CSV|Bill of Materials (รายการวัสดุรวม)|จัดซื้อ, สต็อก|
|**layout_coordinates.json**|JSON|พิกัดวงจร (DB → Outlet)|**Module 8 (AutoCAD)**|
|**compliance_report.json**|JSON|ผลตรวจสอบมาตรฐาน|ตรวจสอบความปลอดภัย|

---

## **3.2 โครงสร้าง layout_coordinates.json (สำหรับ Module 8)**

json

{
  "project_name": "บ้าน 2 ชั้น Modern Contemporary",
  "db_position": null,
  "circuits": [
    {
      "circuit_id": "C01",
      "circuit_name": "แอร์ ห้องนั่งเล่น",
      "db_position": {"x": 0, "y": 6, "z": 0},
      "outlet_position": {"x": 6, "y": 4, "z": 2.5},
      "waypoints": [
        {"x": 0, "y": 6, "z": 0},
        {"x": 6, "y": 6, "z": 0},
        {"x": 6, "y": 4, "z": 2.5}
      ],
      "wire_size_mm2": 2.5,
      "conduit_size_inch": "1/2"
    }
  ]
}


**Module 8 จะอ่านไฟล์นี้แล้วสร้าง:**

- เส้นสาย (Polyline) จาก waypoints
    
- สัญลักษณ์ DB, Outlet, Switch
    
- ข้อความบอกขนาดสาย/ท่อ
    

---
