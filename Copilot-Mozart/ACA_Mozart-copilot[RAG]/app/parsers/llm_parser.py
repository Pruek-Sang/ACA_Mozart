"""
LLM Parser - AI-Based Edit Command Parsing (Fallback)

Uses LLM to parse complex or ambiguous edit commands.
This is the fallback when regex parsing fails.

Created: 2025-12-28
"""

import json
import logging
from typing import Optional

from app.parsers.edit_command import EditCommand, EditAction

logger = logging.getLogger("Aura.Parsers.LLM")


# LLM Prompt template for edit parsing - FULL FLEXIBILITY VERSION
EDIT_PARSE_PROMPT = '''คุณเป็น Parser สำหรับแปลงคำสั่งแก้ไขระบบไฟฟ้าเป็น JSON

🌍 **รับทุกภาษา + พิมพ์ผิดได้:**
ผู้ใช้อาจพิมพ์ภาษาไทย, English, ผสม, หรือพิมพ์ผิด/ไม่ครบ
คุณต้องเข้าใจ intent และแปลงเป็น JSON ให้ได้

จากคำสั่ง: "{text}"

ให้วิเคราะห์และตอบเป็น JSON เท่านั้น:
{{
  "action": "CHANGE" | "ADD" | "REMOVE",
  "target_type": "DEVICE" | "ROOM",
  "device_type": "รหัสอุปกรณ์" หรือ null,
  "device_code": "รหัสเต็ม เช่น AC-18000BTU" หรือ null,
  "room_name": "ชื่อห้อง" หรือ null,
  "room_type": "living|bedroom|kitchen|bathroom|storage|exterior|garage" หรือ null,
  "target_floor": ตัวเลขชั้น หรือ null,
  "new_value": ตัวเลขค่าใหม่ หรือ null,
  "unit": "BTU" | "W" | "m" หรือ null,
  "quantity": จำนวน หรือ null,
  "branch_distance_m": ระยะสายย่อย (เมตร) หรือ null,
  "confidence": 0.0-1.0
}}

📋 **รหัสอุปกรณ์ที่รองรับ:**
- แอร์: AC-9000BTU, AC-12000BTU, AC-18000BTU, AC-24000BTU
- น้ำอุ่น: HEATER-3500W, HEATER-4500W, HEATER-6000W
- ปั๊มน้ำ: PUMP-750W, PUMP-1500W
- เตา: INDUCTION-3000W, INDUCTION-2000W
- ไฟ: LIGHT-LED-10W, LIGHT-LED-20W
- เต้ารับ: SOCKET-16A
- ตู้เย็น: REFRIG-300W, REFRIG-500W
- ไมโครเวฟ: MICROWAVE-1500W
- กาต้มน้ำ: KETTLE-2200W
- หม้อหุงข้าว: RICECOOK-800W
- พัดลมเพดาน: FAN-CEILING-60W
- ดูดอากาศ: FAN-EXHAUST-25W
- EV Charger: EV-CHARGER-7KW, EV-CHARGER-22KW

📋 **ตัวอย่างคำสั่ง:**
- "เปลี่ยนแอร์เป็น 18000" → {{"action":"CHANGE","target_type":"DEVICE","device_type":"AC","new_value":18000,"unit":"BTU"}}
- "ลบน้ำอุ่นห้องน้ำ 1" → {{"action":"REMOVE","target_type":"DEVICE","device_type":"HEATER","room_name":"ห้องน้ำ 1"}}
- "เพิ่มตู้เย็นห้องครัว" → {{"action":"ADD","target_type":"DEVICE","device_code":"REFRIG-300W","room_name":"ห้องครัว"}}
- "สายแอร์ยาว 25 เมตร" → {{"action":"CHANGE","target_type":"DEVICE","device_type":"AC","branch_distance_m":25}}
- "เพิ่มห้องนอน 1 ห้อง" → {{"action":"ADD","target_type":"ROOM","room_type":"bedroom","quantity":1}}
- "ลบห้องเก็บของ" → {{"action":"REMOVE","target_type":"ROOM","room_name":"ห้องเก็บของ"}}
- "ไฟห้องครัวเพิ่ม 2 ดวง" → {{"action":"ADD","target_type":"DEVICE","device_code":"LIGHT-LED-20W","room_name":"ห้องครัว","quantity":2}}
- "เต้ารับเหลือ 4 จุด" → {{"action":"CHANGE","target_type":"DEVICE","device_type":"SOCKET","quantity":4}}

⚠️ **กฎพิเศษ:**
- ถ้าไม่ระบุ BTU → default AC-12000BTU
- ถ้าไม่ระบุ W น้ำอุ่น → default HEATER-4500W
- ถ้ามีคำว่า "ระยะ/ยาว/เมตร" + ตัวเลข → ใส่ใน branch_distance_m (สำหรับ VD)
- ถ้าผู้ใช้พิมพ์ผิด ให้พยายามเดา intent (เช่น "แอ" = "แอร์", "น้ำร้อน" = "น้ำอุ่น")

ตอบ JSON เท่านั้น:'''


async def llm_parse(text: str) -> Optional[EditCommand]:
    """
    Parse edit command using LLM.
    
    Args:
        text: Normalized text to parse
        
    Returns:
        EditCommand if successfully parsed, None otherwise
    """
    if not text:
        return None
    
    try:
        # Import LLM utilities (lazy load to avoid circular imports)
        from app.service import RagService
        
        # Get singleton or create temporary instance
        # Note: In production, this should use a shared instance
        service = RagService()
        
        prompt = EDIT_PARSE_PROMPT.format(text=text)
        
        config = {"temperature": 0.1, "max_output_tokens": 500}
        response = service._generate_content(prompt, config)
        
        # Parse JSON response
        return _parse_llm_response(response, text)
        
    except Exception as e:
        logger.error(f"[LLM] Parse failed: {e}")
        return None


def _parse_llm_response(response: str, raw_input: str) -> Optional[EditCommand]:
    """
    Parse LLM response into EditCommand.
    """
    try:
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if not json_match:
            logger.warning("[LLM] No JSON found in response")
            return None
        
        data = json.loads(json_match.group())
        
        # Map to EditCommand
        action_str = data.get("action", "UNKNOWN")
        try:
            action = EditAction(action_str)
        except ValueError:
            action = EditAction.UNKNOWN
        
        # Parse target_type
        from app.parsers.edit_command import TargetType
        target_type_str = data.get("target_type", "DEVICE")
        try:
            target_type = TargetType(target_type_str)
        except ValueError:
            target_type = TargetType.DEVICE
        
        cmd = EditCommand(
            action=action,
            target_type=target_type,
            device_type=data.get("device_type") or "",
            device_code=data.get("device_code"),
            room_name=data.get("room_name"),
            room_type=data.get("room_type"),
            target_floor=data.get("target_floor"),
            new_value=data.get("new_value"),
            unit=data.get("unit"),
            quantity=data.get("quantity"),
            branch_distance_m=data.get("branch_distance_m"),
            confidence=data.get("confidence", 0.7),
            parse_method="llm",
            raw_input=raw_input,
            normalized_input=raw_input.lower(),
        )
        
        # Log what we parsed
        if target_type == TargetType.ROOM:
            logger.info(f"[LLM] Parsed ROOM: {cmd.action.value} {cmd.room_type or cmd.room_name}")
        else:
            logger.info(f"[LLM] Parsed DEVICE: {cmd.action.value} {cmd.device_type or cmd.device_code} → {cmd.new_value} {cmd.unit}")
        
        return cmd
        
    except json.JSONDecodeError as e:
        logger.error(f"[LLM] JSON parse failed: {e}")
        return None
    except Exception as e:
        logger.error(f"[LLM] Response parsing failed: {e}")
        return None
