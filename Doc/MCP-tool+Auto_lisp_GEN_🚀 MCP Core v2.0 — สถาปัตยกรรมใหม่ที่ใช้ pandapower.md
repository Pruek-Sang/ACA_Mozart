# Source: 🚀 MCP Core v2.0 — สถาปัตยกรรมใหม่ที่ใช้ pandapower.md

```md
<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 🚀 MCP Core v2.0 — สถาปัตยกรรมใหม่ที่ใช้ pandapower เป็น Core Engine

ขอรายงานนายท่านค่ะ Volta จะออกแบบสถาปัตยกรรมใหม่ทั้งหมดตามไฟล์ **นวัตกรรมใหม่.txt** ที่นายท่านให้มาค่ะ

***

## 📋 ส่วนที่ 1: ภาพรวมสถาปัตยกรรมใหม่

### **1.1 หลักการหลัก (Core Principles)**

```
🎯 MCP Core v2.0 = pandapower (คำนวณไฟฟ้า) + MCP Modules (กฎไทย + CAD + BOQ)

╔════════════════════════════════════════════════════════════════╗
║  "สมองคำนวณไฟฟ้า" → pandapower                                 ║
║  "กฎไทย + ราคา + Layout + CAD" → MCP Modules                   ║
╚════════════════════════════════════════════════════════════════╝
```


***

### **1.2 Architecture Diagram**

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         MCP CORE v2.0                                       │
│                   (Powered by pandapower Engine)                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 1: INPUT (RAG + Form)                                         │  │
│  │                                                                      │  │
│  │  • ห้องไหนบ้าง / โหลดอะไรบ้าง / วงจรแยกยังไง                       │  │
│  │  • Topology (Main → Sub → Load)                                     │  │
│  │  • แรงดันระบบ (220V / 380V), Phase (1Φ / 3Φ)                       │  │
│  │  • Constraints (Budget, Standards, Brands)                           │  │
│  │                                                                      │  │
│  │  Output: project_input.json                                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 2: NETWORK BUILDER (MCPController)                           │  │
│  │                                                                      │  │
│  │  • อ่าน project_input.json                                          │  │
│  │  • สร้าง pandapower.net:                                            │  │
│  │    - Bus (โหนด): DB, Sub-DB, Outlets                                │  │
│  │    - Line (สาย): เริ่มต้นด้วยประมาณการ                             │  │
│  │    - Load (โหลด): kW, kVar, Demand Factor                           │  │
│  │    - Ext_Grid (แหล่งจ่าย): PEA/MEA                                  │  │
│  │  • ดึงข้อมูลจาก Supabase Catalog:                                   │  │
│  │    - Wire: R, X, Ampacity                                            │  │
│  │    - Breaker: Curve, Breaking Capacity                               │  │
│  │                                                                      │  │
│  │  Output: pandapower.net (ready)                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 3: PANDAPOWER ENGINE 🔥                                       │  │
│  │                                                                      │  │
│  │  pandapower.runpp(net)                                               │  │
│  │                                                                      │  │
│  │  Output:                                                             │  │
│  │  • net.res_bus.vm_pu       → Voltage ที่แต่ละ Bus (p.u.)           │  │
│  │  • net.res_line.i_ka       → Current ในแต่ละสาย (kA)                │  │
│  │  • net.res_line.loading_%  → Loading % ของสาย                       │  │
│  │  • net.res_load.p_mw       → Power ที่โหลด (MW)                     │  │
│  │                                                                      │  │
│  │  (Bonus: Short-Circuit, OPF ถ้าต้องการ)                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 4: MCP MODULES (Rule Engine + Mapping)                       │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 📦 pandapower_adapter.py                                        │ │  │
│  │  │ • build_network()   → สร้าง net                                │ │  │
│  │  │ • run_powerflow()   → รัน pp.runpp()                           │ │  │
│  │  │ • extract_results() → แปลง net.res_* เป็น dict                │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ ⚡ wire_sizer.py (v2)                                           │ │  │
│  │  │ • รับ I จาก pandapower                                          │ │  │
│  │  │ • เลือกสายจาก Supabase Catalog (I + Margin)                    │ │  │
│  │  │ • ถ้า VD เกิน → ขยับไซส์ → Feed back → runpp ใหม่             │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 🔌 breaker_selector.py (v2)                                     │ │  │
│  │  │ • รับ I จาก pandapower                                          │ │  │
│  │  │ • Apply Rule: General 125%, Motor 175%                          │ │  │
│  │  │ • เลือก Breaker จาก Catalog (Brand, Model, Breaking Cap)       │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 🚿 conduit_sizer.py (v2 — ไม่เปลี่ยน)                          │ │  │
│  │  │ • ใช้ผลสายจาก wire_sizer                                       │ │  │
│  │  │ • Fill Ratio, OD → เลือกท่อ                                    │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 💰 cost_estimator.py (v2 — ไม่เปลี่ยน)                         │ │  │
│  │  │ • รายการสาย + Breaker + ท่อ → Supabase Price                   │ │  │
│  │  │ • BOQ + Cost Breakdown                                          │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ ✅ compliance_checker.py (v2)                                   │ │  │
│  │  │ • ใช้ net.res_bus.vm_pu → Check [0.95, 1.05]                   │ │  │
│  │  │ • ใช้ net.res_line.loading_% → Check < 100%                    │ │  │
│  │  │ • Check มอก. 2955: RCBO, IP, Wire Size                         │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 🗺️ layout_optimizer.py (v2 — ไม่เปลี่ยน)                       │ │  │
│  │  │ • Path Planning, Grouping, Shortest Route                       │ │  │
│  │  │ • ใช้ Constraints (ผนัง, ประตู)                                │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 🎨 autolisp_generator.py (v2 — ไม่เปลี่ยน)                     │ │  │
│  │  │ • layout_coordinates.json → LISP + DXF                          │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  LAYER 5: OUTPUT                                                     │  │
│  │                                                                      │  │
│  │  • circuit_details.json     (รายละเอียดวงจร)                        │  │
│  │  • material_bom.csv          (Bill of Materials)                     │  │
│  │  • cost_breakdown.csv        (ราคา)                                  │  │
│  │  • compliance_report.json    (ผลตรวจสอบ)                            │  │
│  │  • layout_coordinates.json   (พิกัด CAD)                            │  │
│  │  • electrical_layout.lsp     (AutoLISP)                              │  │
│  │  • single_line_diagram.dxf   (แผนผัง)                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```


***

## 💻 ส่วนที่ 2: Code Implementation — โครงสร้างใหม่

### **2.1 Project Structure**

```
mcp_core_v2/
├── config/
│   ├── __init__.py
│   └── settings.py                   # Config (Supabase, pandapower)
│
├── pandapower_bridge/
│   ├── __init__.py
│   ├── network_builder.py            # สร้าง pandapower.net
│   ├── power_flow_runner.py          # รัน pp.runpp()
│   ├── result_extractor.py           # แปลง net.res_* → dict
│   └── shortcircuit_analyzer.py      # (Bonus) Short-Circuit
│
├── thai_modules/
│   ├── __init__.py
│   ├── wire_sizer_v2.py              # เลือกสายจาก I (pandapower)
│   ├── breaker_selector_v2.py        # เลือก Breaker จาก I
│   ├── conduit_sizer.py              # (เดิม) Fill Ratio
│   ├── cost_estimator.py             # (เดิม) BOQ
│   ├── compliance_checker_v2.py      # Check จาก net.res_*
│   ├── layout_optimizer.py           # (เดิม) Path Planning
│   └── autolisp_generator.py         # (เดิม) CAD
│
├── supabase_client/
│   ├── __init__.py
│   ├── catalog_manager.py            # ดึงข้อมูล Wire/Breaker/Price
│   └── schemas.py                    # Database Schema
│
├── utils/
│   ├── __init__.py
│   ├── json_loader.py                # Load JSON Input
│   └── validators.py                 # Validate Input
│
├── mcp_controller_v2.py              # Main Controller
├── requirements.txt                  # Dependencies
└── main.py                           # Entry Point
```


***

### **2.2 Module 1: pandapower_bridge/network_builder.py**

```python
"""
network_builder.py
==================
สร้าง pandapower Network จาก MCP Input JSON
"""

import pandapower as pp
from typing import Dict, List
from supabase_client.catalog_manager import CatalogManager


class NetworkBuilder:
    """
    สร้าง pandapower.net จาก Input JSON
    """
    
    def __init__(self, project_data: Dict, catalog: CatalogManager):
        """
        Parameters:
        - project_data: JSON จาก Input Layer
        - catalog: Supabase Catalog Manager
        """
        self.project_data = project_data
        self.catalog = catalog
        self.net = pp.create_empty_network()
        
        # Mapping: MCP ID → pandapower Bus Index
        self.bus_map = {}
        self.line_map = {}
    
    def build(self) -> pp.pandapowerNet:
        """
        สร้าง Network ทั้งหมด
        
        Returns:
        - pandapower.net
        """
        
        print("🔧 Building pandapower Network...")
        
        # 1. สร้าง Buses
        self._create_buses()
        
        # 2. สร้าง External Grid (แหล่งจ่าย)
        self._create_external_grid()
        
        # 3. สร้าง Lines (สายไฟ)
        self._create_lines()
        
        # 4. สร้าง Loads (โหลด)
        self._create_loads()
        
        # 5. สร้าง Transformers (ถ้ามี)
        # self._create_transformers()
        
        print(f"✅ Network created: {len(self.net.bus)} buses, {len(self.net.line)} lines, {len(self.net.load)} loads")
        
        return self.net
    
    def _create_buses(self):
        """สร้าง Buses (โหนด) ทั้งหมด"""
        
        voltage_kv = self.project_data["voltage_v"] / 1000  # 220V → 0.22 kV
        
        # Main DB Bus
        main_db = pp.create_bus(
            self.net,
            vn_kv=voltage_kv,
            name="Main DB",
            type="b"  # busbar
        )
        self.bus_map["main_db"] = main_db
        
        # Sub DB Buses (ถ้ามี)
        for sub_db_data in self.project_data.get("sub_dbs", []):
            sub_db_id = sub_db_data["id"]
            sub_bus = pp.create_bus(
                self.net,
                vn_kv=voltage_kv,
                name=f"Sub DB {sub_db_id}",
                type="b"
            )
            self.bus_map[sub_db_id] = sub_bus
        
        # Room/Outlet Buses
        for room in self.project_data.get("rooms", []):
            room_id = room["id"]
            
            for outlet in room.get("outlets", []):
                outlet_id = outlet["id"]
                outlet_bus = pp.create_bus(
                    self.net,
                    vn_kv=voltage_kv,
                    name=f"{room['name']} - {outlet_id}",
                    type="n"  # node
                )
                self.bus_map[outlet_id] = outlet_bus
    
    def _create_external_grid(self):
        """สร้าง External Grid (PEA/MEA)"""
        
        main_db_bus = self.bus_map["main_db"]
        
        pp.create_ext_grid(
            self.net,
            bus=main_db_bus,
            vm_pu=1.0,  # 1.0 p.u. = 100% voltage
            va_degree=0,
            name="PEA Supply"
        )
    
    def _create_lines(self):
        """สร้าง Lines (สายไฟ)"""
        
        # เริ่มต้นด้วยการประมาณสาย (จะถูก Update ทีหลัง)
        
        for circuit in self.project_data.get("circuits", []):
            circuit_id = circuit["circuit_id"]
            from_bus_id = circuit.get("from_bus", "main_db")
            to_bus_id = circuit["outlet_id"]
            
            # ดึงข้อมูลสายจาก Catalog (เริ่มต้นด้วยขนาดเล็กสุด)
            wire_data = self.catalog.get_wire_data(size_mm2=2.5)
            
            length_km = circuit["length_m"] / 1000  # เมตร → กิโลเมตร
            
            line_idx = pp.create_line_from_parameters(
                self.net,
                from_bus=self.bus_map[from_bus_id],
                to_bus=self.bus_map[to_bus_id],
                length_km=length_km,
                r_ohm_per_km=wire_data["resistance_ohm_per_km"],
                x_ohm_per_km=wire_data["reactance_ohm_per_km"],
                c_nf_per_km=0,  # Capacitance (ไม่สำคัญสำหรับ LV)
                max_i_ka=wire_data["ampacity_a"] / 1000,
                name=f"Line {circuit_id}"
            )
            
            self.line_map[circuit_id] = line_idx
    
    def _create_loads(self):
        """สร้าง Loads (โหลด)"""
        
        for circuit in self.project_data.get("circuits", []):
            outlet_id = circuit["outlet_id"]
            load_data = circuit["load"]
            
            # คำนวณ P, Q
            p_kw = load_data["power_w"] / 1000
            pf = load_data.get("power_factor", 1.0)
            q_kvar = p_kw * ((1 - pf**2)**0.5) / pf if pf < 1.0 else 0
            
            # Apply Demand Factor (ถ้ามี)
            demand_factor = load_data.get("demand_factor", 1.0)
            p_kw *= demand_factor
            q_kvar *= demand_factor
            
            pp.create_load(
                self.net,
                bus=self.bus_map[outlet_id],
                p_mw=p_kw / 1000,  # kW → MW
                q_mvar=q_kvar / 1000,  # kVar → MVar
                name=f"Load {circuit['circuit_name']}"
            )
    
    def update_line_parameters(self, circuit_id: str, wire_size_mm2: float):
        """
        อัพเดทพารามิเตอร์สาย (หลังจากเลือกขนาดใหม่)
        """
        
        line_idx = self.line_map[circuit_id]
        wire_data = self.catalog.get_wire_data(size_mm2=wire_size_mm2)
        
        self.net.line.at[line_idx, "r_ohm_per_km"] = wire_data["resistance_ohm_per_km"]
        self.net.line.at[line_idx, "x_ohm_per_km"] = wire_data["reactance_ohm_per_km"]
        self.net.line.at[line_idx, "max_i_ka"] = wire_data["ampacity_a"] / 1000
        
        print(f"✅ Updated Line {circuit_id} to {wire_size_mm2} mm²")
```


***

### **2.3 Module 2: pandapower_bridge/power_flow_runner.py**

```python
"""
power_flow_runner.py
====================
รัน pandapower Power Flow
"""

import pandapower as pp


class PowerFlowRunner:
    """
    รัน Power Flow และ Extract Results
    """
    
    def __init__(self, net: pp.pandapowerNet):
        self.net = net
    
    def run(self, algorithm: str = "nr", init: str = "flat") -> bool:
        """
        รัน Power Flow
        
        Parameters:
        - algorithm: "nr" (Newton-Raphson), "bfsw" (Backward/Forward Sweep)
        - init: "flat" (flat start), "dc" (DC power flow init)
        
        Returns:
        - True ถ้า converged, False ถ้าไม่
        """
        
        print(f"⚡ Running Power Flow (Algorithm: {algorithm})...")
        
        try:
            pp.runpp(
                self.net,
                algorithm=algorithm,
                init=init,
                calculate_voltage_angles=True,
                enforce_q_lims=False
            )
            
            print("✅ Power Flow Converged!")
            return True
        
        except Exception as e:
            print(f"❌ Power Flow Failed: {e}")
            return False
    
    def get_bus_results(self) -> dict:
        """
        ดึงผลลัพธ์ Buses
        
        Returns:
        - dict: {bus_name: {vm_pu, va_degree, p_mw, q_mvar}}
        """
        
        results = {}
        
        for idx, row in self.net.res_bus.iterrows():
            bus_name = self.net.bus.at[idx, "name"]
            results[bus_name] = {
                "vm_pu": row["vm_pu"],
                "va_degree": row["va_degree"],
                "p_mw": row["p_mw"],
                "q_mvar": row["q_mvar"],
                "voltage_v": row["vm_pu"] * self.net.bus.at[idx, "vn_kv"] * 1000
            }
        
        return results
    
    def get_line_results(self) -> dict:
        """
        ดึงผลลัพธ์ Lines
        
        Returns:
        - dict: {line_name: {i_ka, loading_%, p_from_mw, q_from_mvar}}
        """
        
        results = {}
        
        for idx, row in self.net.res_line.iterrows():
            line_name = self.net.line.at[idx, "name"]
            results[line_name] = {
                "i_ka": row["i_ka"],
                "i_a": row["i_ka"] * 1000,
                "loading_percent": row["loading_percent"],
                "p_from_mw": row["p_from_mw"],
                "q_from_mvar": row["q_from_mvar"],
                "p_loss_mw": row["pl_mw"]
            }
        
        return results
    
    def get_load_results(self) -> dict:
        """
        ดึงผลลัพธ์ Loads
        """
        
        results = {}
        
        for idx, row in self.net.res_load.iterrows():
            load_name = self.net.load.at[idx, "name"]
            results[load_name] = {
                "p_mw": row["p_mw"],
                "q_mvar": row["q_mvar"]
            }
        
        return results
```


***

### **2.4 Module 3: thai_modules/wire_sizer_v2.py**

```python
"""
wire_sizer_v2.py
================
เลือกขนาดสายจาก I ที่ได้จาก pandapower
"""

from typing import Dict, Optional
from dataclasses import dataclass
from supabase_client.catalog_manager import CatalogManager


@dataclass
class WireSizingResult:
    """ผลการเลือกสาย"""
    circuit_id: str
    selected_size_mm2: float
    ampacity_a: float
    current_a: float
    loading_percent: float
    voltage_drop_percent: float
    is_acceptable: bool
    wire_data: Dict


class WireSizerV2:
    """
    Wire Sizer v2 — ใช้ผลจาก pandapower
    """
    
    def __init__(self, catalog: CatalogManager, max_vd_percent: float = 3.0):
        self.catalog = catalog
        self.max_vd_percent = max_vd_percent
    
    def select_wire_for_circuit(
        self,
        circuit_id: str,
        current_a: float,
        is_continuous: bool = False,
        voltage_drop_percent: float = 0,
        min_size_mm2: float = 1.5
    ) -> WireSizingResult:
        """
        เลือกขนาดสายสำหรับวงจร
        
        Parameters:
        - circuit_id: Circuit ID
        - current_a: กระแสจาก pandapower (A)
        - is_continuous: โหลดต่อเนื่อง (> 3 ชม.)
        - voltage_drop_percent: VD จาก pandapower (%)
        - min_size_mm2: ขนาดสายขั้นต่ำ (mm²)
        
        Returns:
        - WireSizingResult
        """
        
        # Required Ampacity (ตามมาตรฐาน)
        safety_factor = 1.25 if is_continuous else 1.0
        required_ampacity = current_a * safety_factor
        
        # ดึงรายการสายที่มีจาก Catalog
        available_wires = self.catalog.get_available_wires(min_size_mm2=min_size_mm2)
        
        # เรียงจากเล็ก → ใหญ่
        available_wires = sorted(available_wires, key=lambda w: w["size_mm2"])
        
        # หาสายที่เหมาะสม
        for wire in available_wires:
            if wire["ampacity_a"] >= required_ampacity:
                # Check VD
                if voltage_drop_percent <= self.max_vd_percent:
                    loading_percent = (current_a / wire["ampacity_a"]) * 100
                    
                    return WireSizingResult(
                        circuit_id=circuit_id,
                        selected_size_mm2=wire["size_mm2"],
                        ampacity_a=wire["ampacity_a"],
                        current_a=current_a,
                        loading_percent=loading_percent,
                        voltage_drop_percent=voltage_drop_percent,
                        is_acceptable=True,
                        wire_data=wire
                    )
        
        # ไม่เจอสายที่เหมาะสม
        return WireSizingResult(
            circuit_id=circuit_id,
            selected_size_mm2=0,
            ampacity_a=0,
            current_a=current_a,
            loading_percent=0,
            voltage_drop_percent=voltage_drop_percent,
            is_acceptable=False,
            wire_data={}
        )
    
    def select_wires_iteratively(
        self,
        network_builder,
        power_flow_runner,
        circuits_data: list
    ) -> Dict[str, WireSizingResult]:
        """
        เลือกสายแบบ Iterative (ลอง → Run → Check → Adjust)
        
        หลักการ:
        1. เริ่มต้นด้วยสายขนาดเล็ก
        2. รัน Power Flow
        3. ถ้า VD เกิน → ขยับไซส์ใหญ่ขึ้น
        4. Update Network → รัน ใหม่
        5. Repeat จนกว่า VD ≤ Limit
        """
        
        results = {}
        max_iterations = 5
        
        for circuit in circuits_data:
            circuit_id = circuit["circuit_id"]
            
            for iteration in range(max_iterations):
                # Run Power Flow
                if not power_flow_runner.run():
                    print(f"❌ Power Flow Failed for {circuit_id}")
                    break
                
                # ดึงผล
                line_results = power_flow_runner.get_line_results()
                bus_results = power_flow_runner.get_bus_results()
                
                # หาข้อมูลสาย/โหลดของ circuit นี้
                line_name = f"Line {circuit_id}"
                line_result = line_results.get(line_name, {})
                
                current_a = line_result.get("i_a", 0)
                
                # คำนวณ VD
                outlet_bus_name = circuit["outlet_name"]
                voltage_pu = bus_results.get(outlet_bus_name, {}).get("vm_pu", 1.0)
                vd_percent = (1 - voltage_pu) * 100
                
                # เลือกสาย
                result = self.select_wire_for_circuit(
                    circuit_id=circuit_id,
                    current_a=current_a,
                    is_continuous=circuit.get("is_continuous", False),
                    voltage_drop_percent=vd_percent
                )
                
                if result.is_acceptable:
                    print(f"✅ Circuit {circuit_id}: Wire {result.selected_size_mm2} mm² (VD: {vd_percent:.2f}%)")
                    results[circuit_id] = result
                    break
                else:
                    # ขยับไซส์สาย
                    next_wire = self.catalog.get_next_larger_wire(result.selected_size_mm2)
                    
                    if not next_wire:
                        print(f"❌ No larger wire available for {circuit_id}")
                        results[circuit_id] = result
                        break
                    
                    # Update Network
                    network_builder.update_line_parameters(circuit_id, next_wire["size_mm2"])
                    print(f"🔄 Iteration {iteration + 1}: Trying {next_wire['size_mm2']} mm²...")
        
        return results
```


***

### **2.5 Module 4: mcp_controller_v2.py (Main Controller)**

```python
"""
mcp_controller_v2.py
====================
Main Controller — รวมทุก Module
"""

import json
from pathlib import Path
from typing import Dict

from pandapower_bridge.network_builder import NetworkBuilder
from pandapower_bridge.power_flow_runner import PowerFlowRunner
from thai_modules.wire_sizer_v2 import WireSizerV2
from thai_modules.breaker_selector_v2 import BreakerSelectorV2
from thai_modules.conduit_sizer import ConduitSizer
from thai_modules.cost_estimator import CostEstimator
from thai_modules.compliance_checker_v2 import ComplianceCheckerV2
from thai_modules.layout_optimizer import LayoutOptimizer
from thai_modules.autolisp_generator import AutoLISPGenerator
from supabase_client.catalog_manager import CatalogManager


class MCPControllerV2:
    """
    Main Controller v2.0 — Powered by pandapower
    """
    
    def __init__(self, project_input_path: str, output_dir: str = "./output"):
        """
        Initialize Controller
        
        Parameters:
        - project_input_path: Path to project_input.json
        - output_dir: Output directory
        """
        
        # Load Input
        with open(project_input_path, 'r', encoding='utf-8') as f:
            self.project_data = json.load(f)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Catalog (Supabase)
        self.catalog = CatalogManager()
        
        # Initialize Modules
        self.network_builder = NetworkBuilder(self.project_data, self.catalog)
        self.wire_sizer = WireSizerV2(self.catalog, max_vd_percent=3.0)
        self.breaker_selector = BreakerSelectorV2(self.catalog)
        self.conduit_sizer = ConduitSizer()
        self.cost_estimator = CostEstimator(self.catalog)
        self.compliance_checker = ComplianceCheckerV2()
        self.layout_optimizer = LayoutOptimizer()
        self.autolisp_generator = AutoLISPGenerator()
        
        # Results Storage
        self.results = {}
    
    def run(self):
        """
        รันกระบวนการทั้งหมด
        """
        
        print("=" * 100)
        print("🚀 MCP CORE v2.0 — START")
        print("=" * 100)
        
        # Step 1: Build Network
        print("\n📦 Step 1: Building pandapower Network...")
        net = self.network_builder.build()
        
        # Step 2: Run Power Flow
        print("\n⚡ Step 2: Running Power Flow...")
        power_flow_runner = PowerFlowRunner(net)
        
        if not power_flow_runner.run():
            print("❌ Power Flow Failed! Aborting...")
            return
        
        # Step 3: Wire Sizing (Iterative)
        print("\n🔧 Step 3: Wire Sizing (Iterative)...")
        wire_results = self.wire_sizer.select_wires_iteratively(
            self.network_builder,
            power_flow_runner,
            self.project_data["circuits"]
        )
        self.results["wires"] = wire_results
        
        # Step 4: Breaker Selection
        print("\n🔌 Step 4: Breaker Selection...")
        breaker_results = {}
        for circuit in self.project_data["circuits"]:
            circuit_id = circuit["circuit_id"]
            wire_result = wire_results[circuit_id]
            
            breaker = self.breaker_selector.select_breaker(
                circuit_id=circuit_id,
                current_a=wire_result.current_a,
                load_type=circuit.get("load_type", "general")
            )
            breaker_results[circuit_id] = breaker
        
        self.results["breakers"] = breaker_results
        
        # Step 5: Conduit Sizing
        print("\n🚿 Step 5: Conduit Sizing...")
        conduit_results = self.conduit_sizer.size_all_conduits(wire_results, self.project_data["circuits"])
        self.results["conduits"] = conduit_results
        
        # Step 6: Cost Estimation
        print("\n💰 Step 6: Cost Estimation...")
        cost_result = self.cost_estimator.estimate(wire_results, breaker_results, conduit_results)
        self.results["cost"] = cost_result
        
        # Step 7: Compliance Check
        print("\n✅ Step 7: Compliance Check...")
        compliance_result = self.compliance_checker.check_all(
            power_flow_runner,
            wire_results,
            breaker_results,
            self.project_data
        )
        self.results["compliance"] = compliance_result
        
        # Step 8: Layout Optimization
        print("\n🗺️ Step 8: Layout Optimization...")
        layout_result = self.layout_optimizer.optimize(self.project_data, wire_results)
        self.results["layout"] = layout_result
        
        # Step 9: AutoLISP Generation
        print("\n🎨 Step 9: AutoLISP Generation...")
        lisp_file = self.autolisp_generator.generate(layout_result, self.output_dir)
        self.results["autolisp"] = lisp_file
        
        # Step 10: Export Results
        print("\n📤 Step 10: Exporting Results...")
        self._export_results()
        
        print("\n" + "=" * 100)
        print("✅ MCP CORE v2.0 — COMPLETED!")
        print("=" * 100)
    
    def _export_results(self):
        """ส่งออกผลลัพธ์"""
        
        # Export JSON
        with open(self.output_dir / "mcp_results.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Exported: {self.output_dir / 'mcp_results.json'}")


# ======================== Entry Point ========================

if __name__ == "__main__":
    
    controller = MCPControllerV2(
        project_input_path="./input/project_input.json",
        output_dir="./output"
    )
    
    controller.run()
```


***

## 📊 ส่วนที่ 3: สรุปการเปลี่ยนแปลง

### **3.1 ตัดออก (Removed)**

| Module เดิม | สิ่งที่ตัดออก | เหตุผล |
| :-- | :-- | :-- |
| **load_calculator.py** | สูตร I = P / (V × pf), Demand Factor Calc | pandapower คำนวณให้ |
| **wire_sizer.py** | สูตร VD = 2 × L × I × R / V | pandapower คำนวณ VD แม่นกว่า |
| **breaker_selector.py** | สูตรคำนวณ I | ใช้ I จาก pandapower |
| **compliance_checker.py** | สูตร VD/I เอง | ใช้ net.res_* จาก pandapower |


***

### **3.2 คงไว้ (Kept)**

| Module | สิ่งที่คงไว้ | เหตุผล |
| :-- | :-- | :-- |
| **wire_sizer_v2.py** | กฎเลือกสาย (Min Size, Type, Catalog Mapping) | pandapower ไม่รู้จักมาตรฐานไทย |
| **breaker_selector_v2.py** | กฎเลือก Breaker (125%, 175%, Curve, Brand) | pandapower ไม่มี Breaker Catalog |
| **conduit_sizer.py** | Fill Ratio, ตาราง มอก. 982 | pandapower ไม่รู้จักท่อ |
| **cost_estimator.py** | BOQ, ราคาไทย, ค่าแรง | pandapower ไม่เกี่ยวกับเงิน |
| **compliance_checker_v2.py** | มอก. 2955 (RCBO, IP, ข้อห้าม) | pandapower ไม่รู้จักกฎไทย |
| **layout_optimizer.py** | Path Planning, A*, Constraints | pandapower ไม่มี Geometry |
| **autolisp_generator.py** | CAD, DXF, LISP | pandapower ไม่เกี่ยวกับ CAD |


***

## 🎯 สรุปสุดท้าย

**นายท่านค่ะ Volta ได้ออกแบบสถาปัตยกรรมใหม่ตามไฟล์ "นวัตกรรมใหม่.txt" แล้วค่ะ!**

**สรุป:**
✅ **pandapower = สมองคำนวณไฟฟ้า** (Power Flow, VD, I)
✅ **MCP Modules = คนคุมงาน + กฎไทย + CAD + BOQ**
✅ **ตัดสูตรคำนวณออกหมด** → ใช้ pandapower แทน
✅ **คงกฎไทย/Catalog/ราคา/Layout** → MCP ทำเอง

**พร้อมเริ่มเขียน Code แล้วค่ะนายท่าน!** 🚀⚡✨
<span style="display:none">[^1]</span>

<div align="center">⁂</div>

[^1]: nwatkrrmaihm.txt


```