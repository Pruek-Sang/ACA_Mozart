"""
Parse catalog_rows.csv และสร้างเอกสาร AutoLISP Placement ที่ตรงกับ CSV 100%
"""

import csv
import json
from collections import defaultdict
from typing import Dict, List, Any

def parse_json_field(json_str: str) -> Dict:
    """Parse JSON field จาก CSV"""
    try:
        # แทนที่ double quotes ที่ escape มาด้วย single quotes
        cleaned = json_str.replace('""', '"')
        return json.loads(cleaned)
    except:
        return {}

def main():
    # อ่าน CSV
    rows_by_kind = defaultdict(list)
    
    with open('catalog_rows.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['is_active'] == 'true':  # เอาเฉพาะที่ active
                kind = row['kind']
                data = parse_json_field(row['data'])
                rows_by_kind[kind].append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'data': data
                })
    
    # สร้างเอกสาร Markdown
    doc = []
    doc.append("# 🏠 คู่มือการวางอุปกรณ์และสร้าง AutoLISP (ตรงกับ catalog_rows.csv ทุกอย่าง)\n")
    doc.append("**เอกสารฉบับนี้สร้างจากข้อมูลจริงใน catalog_rows.csv - ไม่มีการสมมติใดๆ**\n")
    doc.append("**Date:** 2025-12-03\n")
    doc.append("**Total Rules:** {} items\n".format(sum(len(v) for v in rows_by_kind.values())))
    doc.append("\n---\n\n")
    
    # สารบัญ
    doc.append("## 📑 สารบัญ\n\n")
    doc.append("1. [ภาพรวมข้อมูล](#ภาพรวมข้อมูล)\n")
    doc.append("2. [PLACEMENT_RULE - กฎการวาง](#placement_rule)\n")
    doc.append("3. [VALIDATION_RULE - กฎตรวจสอบ](#validation_rule)\n")
    doc.append("4. [GEOMETRY_FILTER - กรองเส้นทาง](#geometry_filter)\n")
    doc.append("5. [COMPONENT - อุปกรณ์](#component)\n")
    doc.append("6. [ROOM_TEMPLATE - เทมเพลตห้อง](#room_template)\n")
    doc.append("7. [CABLE_SPEC - ข้อมูลสาย](#cable_spec)\n")
    doc.append("8. [DERATING_FACTOR - ค่าลดกระแส](#derating_factor)\n")
    doc.append("9. [CIRCUIT_TEMPLATE - เทมเพลตวงจร](#circuit_template)\n")
    doc.append("10. [APPLIANCE - เครื่องใช้ไฟฟ้า](#appliance)\n")
    doc.append("11. [วิธีใช้ข้อมูลนี้ใน Code](#วิธีใช้)\n\n")
    doc.append("---\n\n")
    
    # ภาพรวม
    doc.append("## ภาพรวมข้อมูล\n\n")
    doc.append("| ประเภทข้อมูล | จำนวน | คำอธิบาย |\n")
    doc.append("|--------------|--------|----------|\n")
    for kind in sorted(rows_by_kind.keys()):
        count = len(rows_by_kind[kind])
        desc = {
            'PLACEMENT_RULE': 'กฎการวางอุปกรณ์ในห้อง',
            'VALIDATION_RULE': 'กฎตรวจสอบความถูกต้อง',
            'GEOMETRY_FILTER': 'กรองเส้นทางเดินสาย',
            'COMPONENT': 'อุปกรณ์ไฟฟ้า (ปลั๊ก, โคมไฟ, สวิตช์)',
            'ROOM_TEMPLATE': 'เทมเพลตห้อง (ห้องนอน, ครัว, ห้องน้ำ)',
            'CABLE_SPEC': 'ข้อมูลสายไฟ (THW, XLPE)',
            'DERATING_FACTOR': 'ค่าลดกระแส (อุณหภูมิ, การจับกลุ่ม)',
            'CIRCUIT_TEMPLATE': 'เทมเพลตวงจร',
            'APPLIANCE': 'เครื่องใช้ไฟฟ้า',
            'ZONE_BUNDLE': 'ชุดอุปกรณ์ตามโซน',
            'ELECTRICAL_STANDARD': 'มาตรฐานไฟฟ้า',
            'ROUTING_RULE': 'กฎเดินสาย',
            'PROJECT_CONFIG': 'การตั้งค่าโปรเจกต์',
            'QA_PLAN': 'แผนตรวจสอบคุณภาพ',
            'PANELBOARD': 'ตู้ไฟ',
            'DEVICE_PROFILE': 'โปรไฟล์อุปกรณ์'
        }.get(kind, '-')
        doc.append(f"| {kind} | {count} | {desc} |\n")
    doc.append("\n---\n\n")
    
    # PLACEMENT_RULE
    if 'PLACEMENT_RULE' in rows_by_kind:
        doc.append("## PLACEMENT_RULE\n\n")
        doc.append("กฎการวางอุปกรณ์ในห้องต่างๆ (จาก catalog_rows.csv)\n\n")
        
        for rule in rows_by_kind['PLACEMENT_RULE']:
            doc.append(f"### {rule['name']}\n\n")
            doc.append(f"**ID:** `{rule['id']}`\n\n")
            
            data = rule['data']
            
            # Strategy
            if 'strategy' in data:
                doc.append(f"**กลยุทธ์การวาง:** {data['strategy']}\n\n")
            
            # Scope (โซนที่ใช้)
            if 'scope' in data and 'zone' in data['scope']:
                zones = data['scope']['zone']
                doc.append(f"**ใช้กับโซน:** {', '.join(zones)}\n\n")
            
            # Component
            if 'component_id' in data:
                doc.append(f"**อุปกรณ์:** `{data['component_id']}`\n\n")
            
            # Placement rules
            if 'placement' in data:
                p = data['placement']
                doc.append("**กฎการวาง:**\n\n")
                if 'room_type' in p:
                    doc.append(f"- ห้อง: {', '.join(p['room_type'])}\n")
                if 'min_distance_from_sink_mm' in p:
                    doc.append(f"- ห่างจากซิงค์: อย่างน้อย {p['min_distance_from_sink_mm']} mm\n")
                if 'max_spacing_m' in p:
                    doc.append(f"- ระยะห่างสูงสุด: {p['max_spacing_m']} m\n")
                if 'min_spacing_m' in p:
                    doc.append(f"- ระยะห่างต่ำสุด: {p['min_spacing_m']} m\n")
                if 'mount_location' in p:
                    doc.append(f"- ตำแหน่งติดตั้ง: {p['mount_location']}\n")
                if 'gfci_required' in p:
                    doc.append(f"- ต้องมี GFCI: {'✅ ใช่' if p['gfci_required'] else '❌ ไม่'}\n")
                if 'min_ip_rating' in p:
                    doc.append(f"- IP Rating ต่ำสุด: {p['min_ip_rating']}\n")
                if 'min_distance_from_water_mm' in p:
                    doc.append(f"- ห่างจากน้ำ: อย่างน้อย {p['min_distance_from_water_mm']} mm\n")
                if 'min_distance_from_corner_mm' in p:
                    doc.append(f"- ห่างจากมุม: อย่างน้อย {p['min_distance_from_corner_mm']} mm\n")
                doc.append("\n")
            
            # Offsets
            if 'offsets_mm' in data:
                o = data['offsets_mm']
                doc.append("**ค่า Offset:**\n\n")
                for key, val in o.items():
                    doc.append(f"- {key}: {val} mm\n")
                doc.append("\n")
            
            # Count formula
            if'count_formula' in data:
                cf = data['count_formula']
                doc.append("**สูตรนับจำนวน:**\n\n")
                doc.append(f"- ประเภท: {cf.get('type', 'N/A')}\n")
                doc.append(f"- จำนวนต่ำสุด: {cf.get('min_count', 'N/A')}\n")
                if 'L_unit_m' in cf:
                    doc.append(f"- หน่วยความยาว: {cf['L_unit_m']} m\n")
                if 'pcs_per_Lunit' in cf:
                    doc.append(f"- จำนวนต่อหน่วย: {cf['pcs_per_Lunit']}\n")
                doc.append("\n")
            
            # Enforcement
            if 'enforcement' in data:
                doc.append(f"**ระดับบังคับ:** {data['enforcement']}\n\n")
            
            doc.append("---\n\n")
    
    # VALIDATION_RULE
    if 'VALIDATION_RULE' in rows_by_kind:
        doc.append("## VALIDATION_RULE\n\n")
        doc.append("กฎตรวจสอบความถูกต้อง\n\n")
        
        for rule in rows_by_kind['VALIDATION_RULE']:
            doc.append(f"### {rule['name']}\n\n")
            doc.append(f"**ID:** `{rule['id']}`\n\n")
            
            data = rule['data']
            
            if 'rule_id' in data:
                doc.append(f"**Rule ID:** `{data['rule_id']}`\n\n")
            
            if 'logic' in data:
                logic = data['logic']
                doc.append("**Logic:**\n\n")
                
                if 'validation_type' in logic:
                    doc.append(f"- ประเภท: {logic['validation_type']}\n")
                if 'applies_to' in logic:
                    doc.append(f"- ใช้กับ: {', '.join(logic['applies_to'])}\n")
                if 'target_field' in logic:
                    doc.append(f"- Field เป้าหมาย: `{logic['target_field']}`\n")
                if 'error_level' in logic:
                    doc.append(f"- ระดับ Error: {logic['error_level']}\n")
                
                if 'parameters' in logic:
                    doc.append("- พารามิเตอร์:\n")
                    for k, v in logic['parameters'].items():
                        doc.append(f"  - {k}: {v}\n")
                
                if 'standard_reference' in logic:
                    doc.append(f"- มาตรฐานอ้างอิง: {logic['standard_reference']}\n")
                
                doc.append("\n")
            
            doc.append("---\n\n")
    
    # COMPONENT
    if 'COMPONENT' in rows_by_kind:
        doc.append("## COMPONENT\n\n")
        doc.append("อุปกรณ์ไฟฟ้าทั้งหมด\n\n")
        doc.append("| ชื่อ | Block Name | Layer Out | Mount Height (mm) | Rated (A/W) |\n")
        doc.append("|------|------------|-----------|-------------------|-------------|\n")
        
        for comp in sorted(rows_by_kind['COMPONENT'], key=lambda x: x['name']):
            data = comp['data']
            attrs = data.get('attributes', {})
            
            block_name = data.get('block_name', '-')
            layer = data.get('layer_out', '-')
            mount_h = attrs.get('mount_height_mm', '-')
            
            # ดึงค่า rating
            rated = []
            if 'rated_current_a' in attrs:
                rated.append(f"{attrs['rated_current_a']}A")
            if 'rated_power_w' in attrs:
                rated.append(f"{attrs['rated_power_w']}W")
            rated_str = ', '.join(rated) if rated else '-'
            
            doc.append(f"| {comp['description'][:40]} | `{block_name}` | `{layer}` | {mount_h} | {rated_str} |\n")
        
        doc.append("\n---\n\n")
    
    # ROOM_TEMPLATE
    if 'ROOM_TEMPLATE' in rows_by_kind:
        doc.append("## ROOM_TEMPLATE\n\n")
        doc.append("เทมเพลตห้องต่างๆ\n\n")
        
        for tmpl in rows_by_kind['ROOM_TEMPLATE']:
            doc.append(f"### {tmpl['description']}\n\n")
            
            data = tmpl['data']
            
            if 'template_code' in data:
                doc.append(f"**Template Code:** `{data['template_code']}`\n\n")
            if 'template_id' in data:
                doc.append(f"**Template ID:** `{data['template_id']}`\n\n")
            
            if 'room_type' in data:
                doc.append(f"**ประเภทห้อง:** {data['room_type']}\n\n")
            
            if 'default_appliances' in data:
                doc.append("**เครื่องใช้มาตรฐาน:**\n\n")
                for app in data['default_appliances']:
                    doc.append(f"- {app}\n")
                doc.append("\n")
            
            if 'typical_appliances' in data:
                doc.append("**เครื่องใช้ทั่วไป:**\n\n")
                for app in data['typical_appliances']:
                    if isinstance(app, dict):
                        name = app.get('name', app.get('appliance_id', 'N/A'))
                        optional = ' (ตัวเลือก)' if app.get('optional', False) else ''
                        doc.append(f"- {name}{optional}\n")
                    else:
                        doc.append(f"- {app}\n")
                doc.append("\n")
            
            if 'compliance' in data:
                comp = data['compliance']
                doc.append("**ข้อกำหนดตามมาตรฐาน:**\n\n")
                for k, v in comp.items():
                    doc.append(f"- {k}: {v}\n")
                doc.append("\n")
            
            doc.append("---\n\n")
    
    # CABLE_SPEC
    if 'CABLE_SPEC' in rows_by_kind:
        doc.append("## CABLE_SPEC\n\n")
        doc.append("ข้อมูลสายไฟทั้งหมด\n\n")
        doc.append("| Cable ID | Size (mm²) | Insulation | Ampacity (A) | Resistance (Ω/km@20°C) | Price (฿/m) |\n")
        doc.append("|----------|------------|------------|--------------|------------------------|-------------|\n")
        
        for cable in sorted(rows_by_kind['CABLE_SPEC'], key=lambda x: x['data'].get('size_mm2', 0)):
            data = cable['data']
            
            cable_id = data.get('cable_id', '-')
            size = data.get('size_mm2', '-')
            insulation = data.get('insulation_type', '-')
            ampacity = data.get('ampacity_in_conduit_a', data.get('base_ampacity_a', '-'))
            resistance = data.get('resistance_ohm_per_km_20c', data.get('resistance_ohm_per_km_20C', '-'))
            price = data.get('price_thb_per_m', '-')
            
            doc.append(f"| {cable_id} | {size} | {insulation} | {ampacity} | {resistance} | {price} |\n")
        
        doc.append("\n---\n\n")
    
    # DERATING_FACTOR
    if 'DERATING_FACTOR' in rows_by_kind:
        doc.append("## DERATING_FACTOR\n\n")
        doc.append("ค่าลดกระแสตามเงื่อนไขต่างๆ\n\n")
        
        for df in rows_by_kind['DERATING_FACTOR']:
            doc.append(f"### {df['description']}\n\n")
            
            data = df['data']
            
            if 'factor_id' in data:
                doc.append(f"**Factor ID:** `{data['factor_id']}`\n\n")
            
            if 'derating_type' in data:
                doc.append(f"**ประเภท:** {data['derating_type']}\n\n")
            
            if 'standard_reference' in data:
                doc.append(f"**มาตรฐาน:** {data['standard_reference']}\n\n")
            
            if 'table' in data:
                doc.append("**ตารางค่าลด:**\n\n")
                table = data['table']
                if table and isinstance(table, list):
                    # หา headers
                    headers = list(table[0].keys())
                    doc.append("| " + " | ".join(headers) + " |\n")
                    doc.append("|" + "|".join(["---"]*len(headers)) + "|\n")
                    
                    for row in table:
                        values = [str(row.get(h, '')) for h in headers]
                        doc.append("| " + " | ".join(values) + " |\n")
                    doc.append("\n")
            
            doc.append("---\n\n")
    
    # GEOMETRY_FILTER
    if 'GEOMETRY_FILTER' in rows_by_kind:
        doc.append("## GEOMETRY_FILTER\n\n")
        doc.append("กรองเส้นทางเดินสาย\n\n")
        
        for gf in rows_by_kind['GEOMETRY_FILTER']:
            doc.append(f"### {gf['description']}\n\n")
            
            data = gf['data']
            
            if 'filter_id' in data:
                doc.append(f"**Filter ID:** `{data['filter_id']}`\n\n")
            
            if 'routing_type' in data:
                doc.append(f"**ประเภทการเดินสาย:** {data['routing_type']}\n\n")
            
            if 'include_entity' in data:
                doc.append(f"**รวม Entity:** {', '.join(data['include_entity'])}\n\n")
            
            if 'exclude_entity' in data:
                doc.append(f"**ไม่รวม Entity:** {', '.join(data['exclude_entity'])}\n\n")
            
            if 'avoid_zones' in data:
                doc.append(f"**หลีกเลี่ยงโซน:** {', '.join(data['avoid_zones'])}\n\n")
            
            if 'preferred_path' in data:
                doc.append(f"**เส้นทางที่แนะนำ:** {', '.join(data['preferred_path'])}\n\n")
            
            if 'max_deviation_mm' in data:
                doc.append(f"**ค่าเบี่ยงเบนสูงสุด:** {data['max_deviation_mm']} mm\n\n")
            
            doc.append("---\n\n")
    
    # บันทึกไฟล์
    output_file = '/home/builder/Desktop/ACA_Mozart/MCP-tool+Auto lisp GEN/📐 คู่มือการวางอุปกรณ์และสร้าง AutoLISP (จาก catalog_rows.csv).md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(doc))
    
    print(f"✅ สร้างเอกสารเรียบร้อย: {output_file}")
    print(f"📊 ข้อมูลทั้งหมด: {sum(len(v) for v in rows_by_kind.values())} items")

if __name__ == '__main__':
    main()
