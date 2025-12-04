"""
RAG Service - The Engine of Divine Wisdom
Core business logic for RAG operations

Philosophy: The Divine Service Layer
- Single Responsibility: Each method does ONE thing perfectly
- Vita ex Codice: Living, breathing logic with proper error handling
- Pulchritudo in Simplicitate: Beautiful in its clarity
"""

import json
import logging
import os
import warnings
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING

# =============================================================================
# LLM Provider Abstraction
# =============================================================================
# Supports both Google AI (API Key) and Vertex AI (GCP Credentials)
# Auto-detects based on available credentials
# =============================================================================

# Google AI SDK (simpler, uses API key)
try:
    import google.generativeai as genai  # type: ignore[import]
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]
    GOOGLE_AI_AVAILABLE = False

# Vertex AI SDK (enterprise, uses GCP credentials)
# Suppress deprecation warning - will migrate before June 2026
try:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*deprecated.*", category=UserWarning)
        import vertexai  # type: ignore[import]
        from vertexai.generative_models import GenerativeModel as VertexGenerativeModel  # type: ignore[import]
        from vertexai.generative_models import GenerationConfig as VertexGenerationConfig  # type: ignore[import]
    VERTEX_AI_AVAILABLE = True
except ImportError:
    vertexai = None  # type: ignore[assignment]
    VertexGenerativeModel = None  # type: ignore[assignment,misc]
    VertexGenerationConfig = None  # type: ignore[assignment,misc]
    VERTEX_AI_AVAILABLE = False

from pydantic import ValidationError

from app.models import (
    QueryRequest, StandardResponse, SourceRef, AnswerMetadata,
    ProjectRequirements, McpSpecResponse, ProjectInputSpec,
    RawRetrieveRequest, RoomInput, LoadInput,
    InsufficientDataError,  # Phase 3: Error model
    RoomSpec, LoadSpec, ProjectInfo, ElectricalSystem, Constraints  # For direct conversion
)
from app.config import settings
from app.knowledge_service import KnowledgeService
from app.trust_log import trust_logger
from core.database import VectorDatabase
from core.privacy import PrivacyGuard

logger = logging.getLogger("Aura.Service")


class RagService:
    """
    Core RAG service with all divine improvements
    
    Fixes from rag_real.py:
    1. ✅ Uses strict Pydantic models (no Dict)
    2. ✅ Uses KnowledgeService for group-based retrieval
    3. ✅ Includes few-shot examples in prompts
    4. ✅ Implements retry logic with self-correction
    5. ✅ Logs all operations to trust_log
    6. ✅ Pre-validates requirements before LLM call
    7. ✅ Returns proper error codes (400/422/502/504)
    """
    
    def __init__(self):
        """Initialize RAG service with all components"""
        # Use vector adapter (FAISS by default, ChromaDB if VECTOR_DB_BACKEND=chroma)
        from core.vector_adapter import get_vector_db
        self.db = get_vector_db()
        self.privacy = PrivacyGuard()
        self.knowledge = KnowledgeService()
        self.use_google_ai: bool = False
        self.model: Any = None  # Will be set below
        
        # Force load .env to ensure GOOGLE_API_KEY is available
        from dotenv import load_dotenv
        load_dotenv()

        # Auto-detect which LLM API to use
        api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        
        if api_key and GOOGLE_AI_AVAILABLE and genai is not None:
            # Use Google AI (simpler, just needs API key)
            genai.configure(api_key=api_key)  # type: ignore[union-attr]
            self.model = genai.GenerativeModel(settings.MODEL_NAME_ANSWER)  # type: ignore[union-attr]
            self.use_google_ai = True
            logger.info("RagService initialized with Google AI (API Key)")
        # elif VERTEX_AI_AVAILABLE and vertexai is not None and VertexGenerativeModel is not None:
        #     # Use Vertex AI (requires GCP credentials)
        #     vertexai.init(project=settings.PROJECT_ID, location=settings.LOCATION)  # type: ignore[union-attr]
        #     self.model = VertexGenerativeModel(settings.MODEL_NAME_ANSWER)  # type: ignore[misc]
        #     self.use_google_ai = False
        #     logger.info("RagService initialized with Vertex AI")
        else:
            raise RuntimeError("GOOGLE_API_KEY not found in .env or environment. Vertex AI fallback disabled.")
        
        logger.info("RagService initialized with divine components")
    
    def _get_generation_config(
        self, 
        temperature: Optional[float] = None, 
        max_tokens: Optional[int] = None, 
        json_mode: bool = False
    ) -> dict:
        """
        Get generation config for either API
        Returns dict that works with both APIs
        """
        temp = temperature if temperature is not None else settings.GENERATION_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.MAX_OUTPUT_TOKENS
        
        config: Dict[str, Any] = {
            "temperature": temp,
            "max_output_tokens": tokens
        }
        if json_mode:
            config["response_mime_type"] = "application/json"
        
        return config
    
    def _generate_content(self, prompt: str, config: dict) -> str:
        """
        Generate content using the configured LLM
        Works with both Google AI and Vertex AI
        """
        if self.use_google_ai:
            # Google AI uses dict config directly
            response = self.model.generate_content(
                prompt,
                generation_config=config  # type: ignore[arg-type]
            )
        else:
            # Vertex AI uses GenerationConfig object
            gen_config = VertexGenerationConfig(**config)  # type: ignore[misc]
            response = self.model.generate_content(
                prompt,
                generation_config=gen_config  # type: ignore[arg-type]
            )
        return response.text
    
    # =========================================================================
    # Intent Detection & NLP Parsing (NEW - Option B)
    # =========================================================================
    
    def _detect_design_intent(self, query: str) -> bool:
        """
        Detect if query is asking for electrical design.
        
        Design keywords: ออกแบบ, คำนวณระบบ, วางแผนไฟฟ้า, design, calculate
        Returns True if query is a design request.
        """
        design_keywords_th = [
            "ออกแบบ", "ออกแบบระบบ", "ออกแบบไฟฟ้า",
            "คำนวณระบบ", "คำนวณไฟฟ้า", "วางแผนไฟฟ้า",
            "วางระบบ", "ติดตั้งระบบ", "ต้องใช้สายขนาด",
            "บ้าน.*ชั้น.*แอร์", "มีแอร์.*ตัว.*น้ำอุ่น",
        ]
        design_keywords_en = [
            "design electrical", "design system", "calculate electrical",
            "plan electrical", "wire sizing for", "breaker sizing for"
        ]
        
        query_lower = query.lower()
        
        # Check Thai keywords
        for kw in design_keywords_th:
            if kw in query_lower:
                return True
        
        # Check English keywords
        for kw in design_keywords_en:
            if kw in query_lower:
                return True
        
        # Pattern: mentions multiple appliances (likely design request)
        import re
        appliance_pattern = r"(แอร์|น้ำอุ่น|ปั๊มน้ำ|เตา|ไฟ).*\d+.*(ตัว|เครื่อง|จุด)"
        if re.search(appliance_pattern, query):
            return True
        
        return False
    
    def _auto_fill_lighting(
        self, 
        raw_rooms: List[Dict], 
        rooms: List[RoomInput]
    ) -> List[LoadInput]:
        """
        Auto-fill lighting based on room area and type.
        
        ใช้ Rule of Thumb ตามมาตรฐาน วสท. สำหรับบ้านพักอาศัย:
        - ห้องนอน (100-150 lux): LED 10W ต่อ 8-10 ตร.ม. → ห้อง 25 ตร.ม. ใช้ 2-3 ดวง
        - ห้องนั่งเล่น (150-200 lux): LED 20W ต่อ 10-12 ตร.ม. → ห้อง 50 ตร.ม. ใช้ 4-5 ดวง
        - ห้องครัว (300-500 lux): LED 20W ต่อ 6-8 ตร.ม. → ห้อง 15 ตร.ม. ใช้ 2-3 ดวง
        - ห้องน้ำ (150-200 lux): LED 10W ต่อ 4-5 ตร.ม. → ห้อง 6 ตร.ม. ใช้ 1-2 ดวง
        - ห้องเก็บของ (50-100 lux): LED 10W ต่อ 15-20 ตร.ม. → 1-2 ดวง
        - หน้าบ้าน/exterior (50-75 lux): LED 10W 1-2 ดวง
        """
        lighting_loads = []
        
        # Area per fixture (ตร.ม. ต่อ 1 หลอด) - based on วสท. residential standards
        # ค่านี้คือพื้นที่ที่หลอด 1 ดวงครอบคลุมได้อย่างเหมาะสม
        AREA_PER_FIXTURE = {
            "bedroom": 10,      # ห้องนอน: 1 หลอด LED 10W ต่อ 10 ตร.ม.
            "living": 12,       # ห้องนั่งเล่น: 1 หลอด LED 20W ต่อ 12 ตร.ม.
            "kitchen": 6,       # ห้องครัว: 1 หลอด LED 20W ต่อ 6 ตร.ม. (ต้องการความสว่างมาก)
            "bathroom": 5,      # ห้องน้ำ: 1 หลอด LED 10W ต่อ 5 ตร.ม.
            "storage": 15,      # ห้องเก็บของ: 1 หลอด LED 10W ต่อ 15 ตร.ม.
            "exterior": 20,     # หน้าบ้าน: 1 หลอด LED 10W ต่อ 20 ตร.ม.
            "balcony": 10,      # ระเบียง: 1 หลอด LED 10W ต่อ 10 ตร.ม.
            "garage": 12,       # โรงรถ: 1 หลอด LED 10W ต่อ 12 ตร.ม.
        }
        
        # LED specs
        LED_LUMENS = {"LIGHT-LED-10W": 810, "LIGHT-LED-20W": 1600}
        
        for i, room in enumerate(rooms):
            room_name = room.name
            room_type = room.type if hasattr(room, 'type') else "bedroom"
            
            # Try to get area from raw_rooms
            area = 25.0  # default 5x5
            if i < len(raw_rooms):
                raw = raw_rooms[i]
                if raw.get("area_sqm"):
                    area = float(raw.get("area_sqm", 25))
                elif raw.get("width") and raw.get("length"):
                    area = float(raw.get("width", 5)) * float(raw.get("length", 5))
            
            # Select fixture based on room type
            if room_type in ["kitchen", "living"]:
                device = "LIGHT-LED-20W"
            else:
                device = "LIGHT-LED-10W"
            
            # Calculate number of fixtures using simple rule of thumb
            area_per_fixture = AREA_PER_FIXTURE.get(room_type, 10)
            import math
            
            # ห้องน้ำ และ ห้องนอน: lock เป็น 1 ดวงเสมอ
            if room_type in ["bathroom", "bedroom"]:
                num_fixtures = 1
            else:
                num_fixtures = max(1, math.ceil(area / area_per_fixture))
            
            # Cap at reasonable max (8 for large rooms, 4 for small rooms)
            max_fixtures = 8 if area > 50 else 6 if area > 30 else 4
            num_fixtures = min(num_fixtures, max_fixtures)
            
            # Get floor from room
            floor = room.floor if hasattr(room, 'floor') else 1
            
            lighting_loads.append(LoadInput(
                room_name=room_name,
                device=device,
                quantity=num_fixtures,
                floor=floor
            ))
            
            logger.info(f"💡 Auto-fill lighting: {room_name} (floor={floor}, {area}m²) → {num_fixtures}x {device}")
        
        return lighting_loads
    
    def _auto_fill_outlets(self, rooms: List[RoomInput]) -> List[LoadInput]:
        """
        Auto-fill outlets based on room type.
        
        มาตรฐาน วสท.:
        - ห้องนอน: 2-3 จุด
        - ห้องนั่งเล่น: 4-6 จุด
        - ห้องครัว: 3-4 จุด (สำหรับเครื่องใช้ไฟฟ้า)
        - ห้องน้ำ: 1 จุด
        - ห้องเก็บของ: 1 จุด
        """
        outlet_loads = []
        
        OUTLET_COUNT = {
            "bedroom": 2,
            "living": 4,
            "kitchen": 3,
            "bathroom": 1,
            "storage": 1,
            "exterior": 1,
            "balcony": 1,
            "garage": 2,
        }
        
        for room in rooms:
            room_name = room.name
            room_type = room.type if hasattr(room, 'type') else "bedroom"
            floor = room.floor if hasattr(room, 'floor') else 1
            
            count = OUTLET_COUNT.get(room_type, 2)
            
            outlet_loads.append(LoadInput(
                room_name=room_name,
                device="SOCKET-16A",  # Use correct device code from DEVICE_CODES.md
                quantity=count,
                floor=floor
            ))
            
            logger.info(f"🔌 Auto-fill outlets: {room_name} (floor={floor}) → {count}x SOCKET-16A")
        
        return outlet_loads
    
    def _normalize_typos(self, text: str) -> str:
        """
        Normalize common typos and similar words in Thai electrical terms.
        
        This ensures fuzzy matching for user input with typos.
        """
        # คำผิด/คำคล้ายที่พบบ่อย
        typo_map = {
            # แอร์
            'แอ ': 'แอร์ ',
            'แอ์': 'แอร์',
            'เเอร์': 'แอร์',
            'แอร': 'แอร์',
            'เครื่องปรับอากาศ': 'แอร์',
            'แอร์คอน': 'แอร์',
            'aircon': 'แอร์',
            'ac': 'แอร์',
            
            # น้ำอุ่น
            'น้ำร้อน': 'น้ำอุ่น',
            'เครื่องทำน้ำร้อน': 'เครื่องทำน้ำอุ่น',
            'เครื่องน้ำอุ่น': 'เครื่องทำน้ำอุ่น',
            'วอเตอร์ฮีทเตอร์': 'เครื่องทำน้ำอุ่น',
            'water heater': 'เครื่องทำน้ำอุ่น',
            'ฮีทเตอร์': 'เครื่องทำน้ำอุ่น',
            
            # ปั๊มน้ำ
            'ปั้มน้ำ': 'ปั๊มน้ำ',
            'ปั้ม': 'ปั๊มน้ำ',
            'pump': 'ปั๊มน้ำ',
            
            # เตา
            'เตาไฟฟ้า': 'เตาแม่เหล็กไฟฟ้า',
            'เตาแม่เหล็ก': 'เตาแม่เหล็กไฟฟ้า',
            'induction': 'เตาแม่เหล็กไฟฟ้า',
            
            # หน่วย
            'วัตต์': 'W',
            'วัตท์': 'W',
            'watt': 'W',
            'บีทียู': 'BTU',
            'btu': 'BTU',
        }
        
        result = text.lower()
        for typo, correct in typo_map.items():
            result = result.replace(typo.lower(), correct)
        
        return result

    async def _extract_loads_from_text(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to extract structured loads from natural language query.
        
        Returns dict with: project_name, rooms, loads, missing_info
        """
        # Pre-process: แก้คำผิด/คำคล้าย
        normalized_query = self._normalize_typos(query)
        logger.info(f"📝 Normalized query: {normalized_query[:100]}...")
        
        extraction_prompt = f'''คุณเป็น parser สำหรับแปลงคำขอออกแบบไฟฟ้าเป็น JSON

จากข้อความ: "{normalized_query}"

⚠️ คำที่ต้องระวัง (Fuzzy Matching):
- "แอ", "แอ์", "เเอร์", "แอร", "ac", "เครื่องปรับอากาศ" → หมายถึง "แอร์"
- "น้ำร้อน", "เครื่องทำน้ำร้อน", "ฮีทเตอร์", "water heater" → หมายถึง "น้ำอุ่น"
- "ปั้มน้ำ", "ปั้ม", "pump" → หมายถึง "ปั๊มน้ำ"
- "เตาไฟฟ้า", "เตาแม่เหล็ก", "induction" → หมายถึง "เตาแม่เหล็กไฟฟ้า"

ให้ตอบเป็น JSON เท่านั้น (ไม่มีคำอธิบาย):
{{
  "project_name": "ชื่อโครงการ (ถ้าไม่ระบุให้ใส่ 'บ้านพักอาศัย')",
  "building_type": "residential",
  "voltage_system": "TH_1PH_230V",
  "num_floors": จำนวนชั้น (ถ้าไม่ระบุให้ใส่ 1),
  "rooms": [
    {{"name": "ชื่อห้อง", "type": "ประเภท (living/bedroom/kitchen/bathroom/storage/exterior)", "floor": ชั้นที่อยู่ (1 หรือ 2)}}
  ],
  "loads": [
    {{"room_name": "ชื่อห้อง (ต้องตรงกับ name ใน rooms)", "device": "รหัสอุปกรณ์", "quantity": จำนวน}}
  ],
  "missing_info": ["รายการข้อมูลที่ยังขาด"]
}}

⚠️ กฎสำคัญ:
1. ทุก room_name ใน loads ต้องตรงกับ name ใน rooms (ตัวอักษรเหมือนกันทุกประการ)
2. ถ้ามี "หน้าบ้าน", "ข้างนอก", "สวน" ให้สร้างห้อง type="exterior"
3. ถ้ามีปั๊มน้ำ ให้ใส่ใน room_name="พื้นที่ส่วนกลาง" หรือ "exterior"
4. 🔴 แอร์ติดได้เฉพาะ "ห้องนอน" เท่านั้น! ห้องอื่น (ห้องนั่งเล่น/ห้องครัว/ห้องเก็บของ/ห้องน้ำ) ไม่มีแอร์
5. ถ้าผู้ใช้บอก "แอร์ทุกห้อง" → หมายถึงแอร์เฉพาะห้องนอนทุกห้อง (ไม่รวมห้องอื่น)
6. 🏠 บ้าน 2 ชั้น: ชั้น 1 = ห้องนั่งเล่น+ห้องครัว+ห้องน้ำ 1+ห้องเก็บของ, ชั้น 2 = ห้องนอน+ห้องน้ำ 2
7. 🚗 พื้นที่ภายนอก (ใช้ type="exterior" หรือ "garage"):
   - โรงรถ/garage/carport → name="โรงรถ", type="garage"
   - หน้าบ้าน/front yard/ไฟหน้าบ้าน → name="หน้าบ้าน", type="exterior"
   - ข้างบ้าน/side yard/ไฟข้างบ้าน → name="ข้างบ้าน", type="exterior"
   - หลังบ้าน/backyard/ไฟหลังบ้าน → name="หลังบ้าน", type="exterior"
   - สวน/garden → name="สวน", type="exterior"

รหัสอุปกรณ์ที่ใช้ได้:
- แอร์: AC-9000BTU, AC-12000BTU, AC-18000BTU, AC-24000BTU
- น้ำอุ่น: HEATER-3500W, HEATER-4500W
- ไฟ LED: LIGHT-LED-10W, LIGHT-LED-20W
- เต้ารับ: SOCKET-16A
- ปั๊มน้ำ: PUMP-750W, PUMP-1500W
- เตา: INDUCTION-3000W

ถ้าไม่ระบุห้อง ให้สร้างห้องมาตรฐาน (ห้องนั่งเล่น, ห้องนอน, ห้องครัว, ห้องน้ำ)
ถ้าไม่ระบุ BTU ของแอร์ ให้ใช้ 12000BTU
ถ้าไม่ระบุวัตต์น้ำอุ่น ให้ใช้ 4500W

ตอบ JSON เท่านั้น:'''

        try:
            config = self._get_generation_config(temperature=0.1)
            response = self._generate_content(extraction_prompt, config)
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                extracted = json.loads(json_match.group())
                logger.info(f"Extracted loads: {len(extracted.get('loads', []))} items")
                return extracted
            else:
                logger.warning("No JSON found in LLM response")
                return {"error": "ไม่สามารถแปลงข้อมูลได้", "missing_info": ["รายละเอียดอุปกรณ์"]}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {"error": "รูปแบบข้อมูลไม่ถูกต้อง", "missing_info": ["รายละเอียดอุปกรณ์"]}
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"error": str(e), "missing_info": ["ข้อมูลทั้งหมด"]}
    
    async def _call_mcp_with_extracted_loads(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP Core with extracted loads and return design result.
        """
        from app.mcp_adapter import McpAdapter
        from app.mcp_client import McpClient
        
        # Convert extracted data to ProjectRequirements format
        rooms = [
            RoomInput(name=r["name"], type=r["type"])
            for r in extracted.get("rooms", [])
        ]
        
        loads = [
            LoadInput(
                room_name=l["room_name"],
                device=l["device"],
                quantity=l.get("quantity", 1)
            )
            for l in extracted.get("loads", [])
        ]
        
        # Create ProjectRequirements
        req = ProjectRequirements(
            project_name=extracted.get("project_name", "บ้านพักอาศัย"),
            building_type=extracted.get("building_type", "residential"),
            voltage_system=extracted.get("voltage_system", "TH_1PH_230V"),
            rooms=rooms,
            loads=loads
        )
        
        # Generate MCP spec
        try:
            spec_response = await self.generate_mcp_spec(req)
        except Exception as e:
            logger.error(f"MCP spec generation failed: {e}")
            return {"error": f"ไม่สามารถสร้าง spec ได้: {e}"}
        
        # Convert to MCP format and call MCP Core
        adapter = McpAdapter()
        mcp_request = adapter.convert(spec_response.project_input)
        
        mcp_client = McpClient()
        
        if not await mcp_client.health_check():
            logger.warning("MCP Core not available")
            return {
                "status": "partial",
                "message": "MCP Core ไม่พร้อมใช้งาน",
                "spec": spec_response.model_dump()
            }
        
        mcp_response = await mcp_client.design(mcp_request)
        
        if mcp_response.success:
            return {
                "status": "complete",
                "design_result": mcp_response.to_dict(),
                "spec": spec_response.model_dump()
            }
        else:
            return {
                "status": "partial",
                "message": f"MCP calculation failed: {mcp_response.error_message}",
                "spec": spec_response.model_dump()
            }
    
    def _format_design_result_as_text(
        self, 
        result: Dict[str, Any], 
        language: str = "th",
        project_req: 'ProjectRequirements' = None
    ) -> str:
        """
        Format MCP design result as human-readable text.
        
        Args:
            result: MCP calculation result
            language: Output language (th/en)
            project_req: Original project requirements (for load details)
        """
        if result.get("error"):
            return result["error"]
        
        if result.get("status") == "partial":
            return result.get("message", "ไม่สามารถคำนวณได้")
        
        design = result.get("design_result", {})
        breakers = design.get("breaker_selections", {})
        
        # Group loads by floor and type for details
        lighting_by_floor = {}  # floor -> [(room, device, qty)]
        outlets_by_floor = {}   # floor -> [(room, qty)]
        
        if project_req:
            for load in project_req.loads:
                floor = load.floor
                room = load.room_name
                device = load.device
                qty = load.quantity
                
                if "LED" in device or "LIGHT" in device:
                    if floor not in lighting_by_floor:
                        lighting_by_floor[floor] = []
                    lighting_by_floor[floor].append((room, device, qty))
                elif "SOCKET" in device or "OUTLET" in device:
                    if floor not in outlets_by_floor:
                        outlets_by_floor[floor] = []
                    outlets_by_floor[floor].append((room, qty))
        
        lines = []
        if language == "th":
            lines.append("🏠 ผลการออกแบบระบบไฟฟ้า:")
            lines.append("")
            lines.append("📋 สรุป Breaker ที่ต้องใช้:")
            
            for cid, b in breakers.items():
                if isinstance(b, dict) and b.get("circuit_info"):
                    name = b["circuit_info"].get("circuit_name", cid)
                    rating = b.get("breaker_rating", "?")
                    poles = b.get("poles", 1)
                    btype = b.get("breaker_type", "standard")
                    
                    icon = "❄️" if "แอร์" in name or "AC" in name else "🚿" if "น้ำอุ่น" in name or "HEATER" in name else "💡" if "ไฟ" in name else "🔌"
                    rcbo = " (RCBO)" if btype == "rcbo" else ""
                    lines.append(f"  {icon} {name}: {rating}A/{poles}P{rcbo}")
                    
                    # Add details for lighting circuits
                    if "ไฟแสงสว่าง" in name:
                        # Extract floor number from circuit name
                        import re
                        floor_match = re.search(r'ชั้น\s*(\d+)', name)
                        if floor_match:
                            floor = int(floor_match.group(1))
                            if floor in lighting_by_floor:
                                for room, device, qty in lighting_by_floor[floor]:
                                    watt = "20W" if "20W" in device else "10W"
                                    lines.append(f"      • {room}: LED {watt} x {qty} ดวง")
                    
                    # Add details for outlet circuits
                    if "เต้ารับ" in name:
                        import re
                        floor_match = re.search(r'ชั้น\s*(\d+)', name)
                        if floor_match:
                            floor = int(floor_match.group(1))
                            if floor in outlets_by_floor:
                                for room, qty in outlets_by_floor[floor]:
                                    outlet_type = "เต้าคู่" if qty >= 2 else "เต้าเดี่ยว"
                                    lines.append(f"      • {room}: {outlet_type} x {qty} จุด")
            
            # Summary
            total_circuits = len([b for b in breakers.values() if isinstance(b, dict) and b.get("circuit_info")])
            lines.append("")
            lines.append(f"✅ รวม {total_circuits} วงจร ตามมาตรฐาน วสท.")
        else:
            lines.append("🏠 Electrical Design Result:")
            lines.append("")
            lines.append("📋 Breaker Summary:")
            
            for cid, b in breakers.items():
                if isinstance(b, dict) and b.get("circuit_info"):
                    name = b["circuit_info"].get("circuit_name", cid)
                    rating = b.get("breaker_rating", "?")
                    poles = b.get("poles", 1)
                    lines.append(f"  • {name}: {rating}A/{poles}P")
        
        return "\n".join(lines)

    def _convert_to_project_requirements(self, extracted: Dict[str, Any]) -> ProjectRequirements:
        """
        Convert extracted JSON data to ProjectRequirements model.
        
        Args:
            extracted: Dict with rooms and loads from LLM extraction
        
        Returns:
            ProjectRequirements ready for MCP chain
        """
        # Get number of floors
        num_floors = extracted.get("num_floors", 1)
        
        # Build rooms with floor info
        rooms = []
        room_names = set()
        room_floor_map = {}  # Track which floor each room is on
        
        for r in extracted.get("rooms", []):
            name = r.get("name", "ห้อง")
            floor = r.get("floor", 1)
            rooms.append(RoomInput(
                name=name,
                type=r.get("type", "bedroom"),
                floor=floor
            ))
            room_names.add(name)
            room_floor_map[name] = floor
        
        # Default rooms if none specified (2-story layout)
        if not rooms:
            if num_floors >= 2:
                # ชั้น 1
                rooms.append(RoomInput(name="ห้องนั่งเล่น", type="living", floor=1))
                rooms.append(RoomInput(name="ห้องครัว", type="kitchen", floor=1))
                rooms.append(RoomInput(name="ห้องน้ำ 1", type="bathroom", floor=1))
                # ชั้น 2
                rooms.append(RoomInput(name="ห้องนอน", type="bedroom", floor=2))
                rooms.append(RoomInput(name="ห้องน้ำ 2", type="bathroom", floor=2))
                room_floor_map = {"ห้องนั่งเล่น": 1, "ห้องครัว": 1, "ห้องน้ำ 1": 1, "ห้องนอน": 2, "ห้องน้ำ 2": 2}
            else:
                rooms = [
                    RoomInput(name="ห้องนั่งเล่น", type="living", floor=1),
                    RoomInput(name="ห้องนอน", type="bedroom", floor=1),
                    RoomInput(name="ห้องครัว", type="kitchen", floor=1),
                    RoomInput(name="ห้องน้ำ", type="bathroom", floor=1)
                ]
                room_floor_map = {"ห้องนั่งเล่น": 1, "ห้องนอน": 1, "ห้องครัว": 1, "ห้องน้ำ": 1}
            room_names = set(room_floor_map.keys())
        
        # Build loads and auto-add missing rooms
        loads = []
        room_type_map = {
            # Exterior - Thai
            "หน้าบ้าน": "exterior",
            "ไฟหน้าบ้าน": "exterior",
            "ข้างบ้าน": "exterior",
            "ไฟข้างบ้าน": "exterior",
            "หลังบ้าน": "exterior",
            "ไฟหลังบ้าน": "exterior",
            "สวน": "exterior", 
            "นอกบ้าน": "exterior",
            "ข้างนอก": "exterior",
            "พื้นที่ส่วนกลาง": "exterior",
            # Exterior - English
            "front": "exterior",
            "front yard": "exterior",
            "side": "exterior",
            "side yard": "exterior",
            "back": "exterior",
            "backyard": "exterior",
            "garden": "exterior",
            "outdoor": "exterior",
            # Balcony
            "ระเบียง": "balcony",
            "balcony": "balcony",
            # Garage - Thai + English
            "โรงรถ": "garage",
            "garage": "garage",
            "carport": "garage",
            "ที่จอดรถ": "garage",
        }
        for l in extracted.get("loads", []):
            room_name = l.get("room_name", "ห้องนั่งเล่น")
            
            # Auto-add room if load references non-existent room
            if room_name not in room_names:
                # Guess room type from name
                room_type = "bedroom"  # default
                floor = 1  # default floor
                for keyword, rtype in room_type_map.items():
                    if keyword in room_name:
                        room_type = rtype
                        break
                rooms.append(RoomInput(name=room_name, type=room_type, floor=floor))
                room_names.add(room_name)
                room_floor_map[room_name] = floor
                logger.info(f"Auto-added room: {room_name} (type={room_type}, floor={floor})")
            
            # Get floor from room
            floor = room_floor_map.get(room_name, 1)
            
            loads.append(LoadInput(
                room_name=room_name,
                device=l.get("device", "OUTLET_16A"),
                quantity=l.get("quantity", 1),
                floor=floor
            ))
        
        # ============================================
        # AUTO-FILL: Lighting, Outlets, Pump
        # ตามมาตรฐาน วสท. สำหรับบ้านพักอาศัย
        # ============================================
        
        # 1. Auto-fill Lighting per room (เฉพาะห้องที่ยังไม่มี LED)
        # หาว่าห้องไหนมี lighting แล้ว
        rooms_with_lighting = set()
        for l in extracted.get("loads", []):
            if "LED" in l.get("device", "") or "LIGHT" in l.get("device", ""):
                rooms_with_lighting.add(l.get("room_name", ""))
        
        # Auto-fill เฉพาะห้องที่ยังไม่มี
        rooms_needing_lighting = [r for r in rooms if r.name not in rooms_with_lighting]
        raw_rooms_filtered = [
            raw for raw in extracted.get("rooms", []) 
            if raw.get("name") not in rooms_with_lighting
        ]
        if rooms_needing_lighting:
            loads.extend(self._auto_fill_lighting(raw_rooms_filtered, rooms_needing_lighting))
        
        # 2. Auto-fill Outlets per room (เฉพาะห้องที่ยังไม่มี)
        rooms_with_outlets = set()
        for l in extracted.get("loads", []):
            if "OUTLET" in l.get("device", "") or "SOCKET" in l.get("device", ""):
                rooms_with_outlets.add(l.get("room_name", ""))
        
        rooms_needing_outlets = [r for r in rooms if r.name not in rooms_with_outlets]
        if rooms_needing_outlets:
            loads.extend(self._auto_fill_outlets(rooms_needing_outlets))
        
        # 3. Auto-fill Pump (บ้านมาตรฐานควรมีปั๊มน้ำ)
        has_pump = any(
            "PUMP" in l.get("device", "") 
            for l in extracted.get("loads", [])
        )
        if not has_pump:
            loads.append(LoadInput(
                room_name="พื้นที่ส่วนกลาง",
                device="PUMP-750W",  # Use correct device code from DEVICE_CODES.md
                quantity=1,
                floor=1
            ))
            # เพิ่มห้องถ้ายังไม่มี
            if "พื้นที่ส่วนกลาง" not in room_names:
                rooms.append(RoomInput(name="พื้นที่ส่วนกลาง", type="exterior"))
                room_names.add("พื้นที่ส่วนกลาง")
            logger.info("🔧 Auto-added: ปั๊มน้ำ 750W")
        
        return ProjectRequirements(
            project_name=extracted.get("project_name", "บ้านพักอาศัย"),
            building_type=extracted.get("building_type", "residential"),
            voltage_system=extracted.get("voltage_system", "TH_1PH_230V"),
            rooms=rooms,
            loads=loads
        )

    def _convert_req_to_spec(self, req: ProjectRequirements) -> ProjectInputSpec:
        """
        Convert ProjectRequirements to ProjectInputSpec directly (no LLM).
        
        This is used for one-shot design requests where we already have
        complete room/load data with floor information.
        """
        from datetime import datetime, timezone
        
        # Build RoomSpec list
        room_specs = []
        room_id_map = {}  # name → room_id
        for i, room in enumerate(req.rooms):
            room_id = f"R{i+1}"
            room_id_map[room.name] = room_id
            
            # Map room type to template code
            template_map = {
                "living": "ROOMT-LIVING-STD",
                "bedroom": "ROOMT-BEDROOM-STD",
                "kitchen": "ROOMT-KITCHEN-STD",
                "bathroom": "ROOMT-BATHROOM-STD",
                "storage": "ROOMT-STORAGE-STD",
                "exterior": "ROOMT-EXTERIOR-STD",
                "balcony": "ROOMT-BALCONY-STD",
                "garage": "ROOMT-GARAGE-STD",
            }
            template_code = template_map.get(room.type, "ROOMT-BEDROOM-STD")
            
            room_specs.append(RoomSpec(
                room_id=room_id,
                name=room.name,
                room_type=room.type.upper(),
                template_code=template_code,
                area_sqm=room.area_sqm
            ))
        
        # Build LoadSpec list with floor
        load_specs = []
        for i, load in enumerate(req.loads):
            load_id = f"L{i+1}"
            room_id = room_id_map.get(load.room_name, "R1")
            
            # Map device names to standard codes
            device_code = load.device
            if device_code.startswith("LIGHT-LED"):
                device_code = device_code  # Already correct
            elif device_code == "SOCKET-16A":
                device_code = "SOCKET-16A"
            elif device_code == "PUMP-750W":
                device_code = "PUMP-750W"
            
            load_specs.append(LoadSpec(
                load_id=load_id,
                room_id=room_id,
                device_code=device_code,
                qty=load.quantity,
                floor=load.floor
            ))
        
        # Build ProjectInputSpec
        spec = ProjectInputSpec(
            project_info=ProjectInfo(
                project_name=req.project_name,
                building_type=req.building_type.upper(),
                spec_version="2.0"
            ),
            electrical_system=ElectricalSystem(
                voltage_system=req.voltage_system,
                earthing="TT"
            ),
            rooms=room_specs,
            loads=load_specs,
            constraints=Constraints(
                rule_profile_id="TH_RESIDENTIAL_LV",
                user_constraints=req.user_constraints
            )
        )
        
        return spec

    async def _build_design_response(self, req: ProjectRequirements, language: str = "th") -> StandardResponse:
        """
        Build design response by chaining to MCP Core.
        
        Uses direct conversion (no LLM) to preserve floor information.
        
        Args:
            req: ProjectRequirements with rooms and loads (including floor)
            language: Response language (th/en)
        
        Returns:
            StandardResponse with design result in answer field
        """
        from app.mcp_adapter import McpAdapter
        from app.mcp_client import McpClient
        
        try:
            # Direct conversion to ProjectInputSpec (no LLM, preserves floor)
            project_input = self._convert_req_to_spec(req)
            logger.info(f"📦 Direct conversion: {len(project_input.rooms)} rooms, {len(project_input.loads)} loads")
            
            # Log floor info
            floor_counts = {}
            for load in project_input.loads:
                f = load.floor
                floor_counts[f] = floor_counts.get(f, 0) + 1
            logger.info(f"📊 Loads by floor: {floor_counts}")
            
            # Convert to MCP format
            adapter = McpAdapter()
            mcp_request = adapter.convert(project_input)
            
            # Call MCP Core
            mcp_client = McpClient()
            
            if not await mcp_client.health_check():
                logger.warning("MCP Core not available")
                return StandardResponse(
                    answer="⚠️ MCP Core ไม่พร้อมใช้งาน กรุณาเปิด MCP Core ที่ port 5001",
                    sources=[],
                    confidence="Low",
                    grounding_status="MCP_UNAVAILABLE",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=[],
                        retrieval_group="mcp"
                    )
                )
            
            mcp_response = await mcp_client.design(mcp_request)
            
            if mcp_response.success:
                # Format as human-readable text with load details
                result = mcp_response.to_dict()
                formatted_text = self._format_design_result_as_text(
                    {"status": "complete", "design_result": result},
                    language,
                    project_req=req  # Pass project requirements for details
                )
                
                return StandardResponse(
                    answer=formatted_text,
                    sources=[SourceRef(
                        file="MCP Core Calculation",
                        section="design_result",
                        score=1.0,
                        content=f"Session: {result.get('session_id', 'N/A')}"
                    )],
                    confidence="High",
                    grounding_status="CALCULATED",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=["mcp_calculation"],
                        retrieval_group="mcp"
                    )
                )
            else:
                return StandardResponse(
                    answer=f"❌ การคำนวณล้มเหลว: {mcp_response.error_message}",
                    sources=[],
                    confidence="Low",
                    grounding_status="MCP_ERROR",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=[],
                        retrieval_group="mcp"
                    )
                )
                
        except Exception as e:
            logger.error(f"Design response build failed: {e}")
            return StandardResponse(
                answer=f"❌ ไม่สามารถคำนวณได้: {str(e)}",
                sources=[],
                confidence="Low",
                grounding_status="ERROR",
                metadata=AnswerMetadata(
                    llm_model=settings.MODEL_NAME_ANSWER,
                    retrieved_docs=[],
                    retrieval_group="mcp"
                )
            )

    async def process_ask(self, req: QueryRequest) -> StandardResponse:
        """
        Process a general QA question - now with smart intent detection!
        
        If query looks like a design request (e.g., "ออกแบบบ้าน 2 ชั้น มีแอร์ 3 ตัว"),
        automatically extracts loads and chains to MCP Core for calculations.
        
        Args:
            req: Query request with context_hint and language
        
        Returns:
            Standard response with answer, sources, and metadata
            OR MCP design result if design intent detected
        
        Raises:
            HTTPException: 503 if retrieval fails, 504 if LLM times out
        """
        from fastapi import HTTPException
        
        # =====================================================================
        # PHASE 0: DESIGN INTENT DETECTION (NEW FEATURE!)
        # =====================================================================
        # Check if user is asking for electrical design calculation
        # e.g., "ออกแบบบ้าน 2 ชั้น มีแอร์ 3 ตัว น้ำอุ่น 1 ตัว"
        # =====================================================================
        if self._detect_design_intent(req.query):
            logger.info(f"🎯 Design intent detected: {req.query[:50]}...")
            
            try:
                # Extract loads from natural language
                loads = await self._extract_loads_from_text(req.query)
                
                if loads:
                    logger.info(f"📦 Extracted: {json.dumps(loads.get('rooms', []), ensure_ascii=False)[:200]}")
                    
                    # Convert to structured ProjectRequirements
                    project_req = self._convert_to_project_requirements(loads)
                    
                    # Debug: log floors
                    floor_info = {r.name: r.floor for r in project_req.rooms}
                    logger.info(f"🏠 Room floors: {floor_info}")
                    
                    # Chain to MCP Core for calculations
                    result = await self._build_design_response(project_req, req.language)
                    
                    logger.info("✅ Design response built successfully via NLP→MCP chain")
                    return result
                else:
                    # Could not extract loads, fall back to Q&A
                    logger.warning("⚠️ Design intent detected but no loads extracted, falling back to Q&A")
                    
            except Exception as e:
                logger.error(f"❌ Design chain failed: {e}, falling back to Q&A")
                # Continue to regular Q&A flow
        
        # =====================================================================
        # PHASE 1: REGULAR Q&A FLOW (Original logic)
        # =====================================================================
        
        # 1. Anonymize Query
        safe_query = self.privacy.anonymize(req.query)
        logger.debug(f"Processing ask: {safe_query[:50]}... (lang={req.language}, hints={req.context_hint})")
        
        # 2. SEMANTIC SEARCH using ChromaDB (ใช้ vector search จริงๆ)
        filters = None
        if req.context_hint:
            # Map context_hint to folder filter
            if len(req.context_hint) == 1 and req.context_hint[0] in ["db", "mcp", "standard", "example"]:
                filters = {"folder": req.context_hint[0]}
        
        # Try ChromaDB first (semantic search)
        vector_results = self.db.search(safe_query, filters=filters, top_k=settings.DEFAULT_TOP_K)
        
        if vector_results:
            logger.info(f"ChromaDB returned {len(vector_results)} results for: {safe_query[:30]}...")
            results = vector_results
        else:
            # Fallback to folder-based if ChromaDB empty
            logger.warning("ChromaDB empty, falling back to folder-based retrieval")
            docs = self.knowledge.get_docs_for_ask(req.context_hint)
            print(f"DEBUG: Found {len(docs)} docs for hints {req.context_hint}")
            for d in docs:
                print(f"DEBUG: Doc: {d.path} (Priority: {d.priority})")
            logger.info(f"Retrieved {len(docs)} docs from knowledge (hints: {req.context_hint or 'all'})")
            
            results = []
            for doc in docs[:10]:
                content = self.knowledge.load_doc_content(doc)
                if content:
                    results.append({
                        "content": content[:settings.MAX_CONTEXT_CHARS],
                        "source": doc.id or doc.rel_path,
                        "section": doc.folder.value,
                        "score": doc.priority / 100.0
                    })

        # Add sanitized snippets for downstream auditing/judge
        for r in results:
            if "content" in r:
                r["content_snippet"] = self.privacy.anonymize(r["content"])[:500]

        if not results:
            metadata = AnswerMetadata(
                llm_model="N/A",
                retrieved_docs=[],
                retrieval_group=",".join(req.context_hint) if req.context_hint else "all"
            )
            return StandardResponse(
                answer="ไม่พบข้อมูลในเอกสาร" if req.language == "th" else "No information found in documents",
                sources=[],
                confidence="Low",
                grounding_status="NOT_FOUND",
                metadata=metadata
            )
        
        # 3. Anonymize Context
        context_str = ""
        for r in results:
            safe_content = self.privacy.anonymize(r['content'])
            part = f"Src: {r['source']} (Sec: {r.get('section')})\\nTxt: {safe_content}\\n\\n"
            
            if len(context_str) + len(part) <= settings.MAX_CONTEXT_CHARS:
                context_str += part
            else:
                # Truncate to fit remaining space
                remaining = settings.MAX_CONTEXT_CHARS - len(context_str)
                if remaining > 100:
                    context_str += part[:remaining]
                break
        
        # 4. Generate Answer with language instruction
        # 4. Generate Answer with language instruction
        if req.language == "th":
            lang_instruction = """คุณเป็นผู้เชี่ยวชาญไฟฟ้า ตอบสั้นกระชับ 1-2 ประโยค
กฎ:
- ตอบเป็นภาษาไทย ตรงประเด็น ไม่อธิบายยืดยาว
- ตอบตัวเลข/ค่าที่ต้องการก่อน แล้วค่อยอธิบายเหตุผลสั้นๆ
- สำหรับการเลือกเบรกเกอร์:
  * ขั้นตอน: Load × 1.25 → เลือก standard size ที่ใหญ่กว่า
  * Standard sizes: 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125 A
  * ❗ ห้ามตอบขนาดที่ไม่อยู่ใน standard sizes (เช่น 22, 28, 35)
- ถ้าข้อมูลไม่ครบ บอกว่า "กรุณาระบุ [ข้อมูลที่ขาด]"
- ถ้าไม่เกี่ยวกับไฟฟ้า ตอบว่า "ไม่มีข้อมูลในระบบ"
- ❗ จำกัดคำตอบไม่เกิน 3 ประโยค
"""
        else:
            lang_instruction = """You are an electrical expert. Answer in 1-2 sentences max.
Rules:
- Answer directly with numbers first, then brief explanation
- For breaker: Load × 1.25 → next standard size (6,10,16,20,25,32,40,50,63,80,100,125A)
- If missing data, say "Please specify [missing data]"
- If not electrical, say "No data in system"
- ❗ Limit to 3 sentences max"""
        
        prompt = f"{lang_instruction}\n\nContext:\n{context_str}\n\nQuestion: {safe_query}\n\nAnswer:"
        
        try:
            config = self._get_generation_config(temperature=settings.GENERATION_TEMPERATURE)
            answer = self._generate_content(prompt, config)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise HTTPException(504, "LLM provider timeout")
        
        # 5. Grounding Check
        is_grounded, status = self.privacy.validate_grounding(answer, context_str)
        
        # 6. Confidence Logic (Score + Grounding)
        top_score = results[0]['score'] if results else 0.0
        if not is_grounded:
            confidence = "Low"
        elif top_score > 0.7:
            confidence = "High"
        else:
            confidence = "Medium"
        
        sources = [
            SourceRef(
                file=r['source'],
                section=r.get('section', 'N/A'),
                score=r['score'],
                content=r.get('content_snippet')
            )
            for r in results
        ]
        
        # 7. Create metadata
        metadata = AnswerMetadata(
            llm_model=settings.MODEL_NAME_ANSWER,
            retrieved_docs=[r['source'] for r in results[:5]],  # Top 5 docs
            retrieval_group=",".join(req.context_hint) if req.context_hint else "all"
        )
        
        return StandardResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            grounding_status=status,
            metadata=metadata
        )
    
    def _validate_requirements(self, req: ProjectRequirements) -> List[str]:
        """
        Pre-validate requirements before calling LLM
        
        Args:
            req: Project requirements
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check rooms
        room_names = set()
        for i, room in enumerate(req.rooms):
            if not room.type:
                errors.append(f"Room '{room.name}' missing field: type")
            room_names.add(room.name)
        
        # Check loads
        for i, load in enumerate(req.loads):
            if not load.room_name:
                errors.append(f"Load (index {i}) missing field: room_name")
            elif load.room_name not in room_names:
                errors.append(f"Load references non-existent room: '{load.room_name}'")
            
            if not load.device:
                errors.append(f"Load (index {i}) missing field: device")
        
        return errors
    
    def _load_few_shot_examples(self) -> str:
        """
        Load few-shot examples from knowledge base
        
        Returns:
            Formatted example string for prompt
        """
        example_ids = [
            "example_req_inputspec_house_1floor_basic",
            "example_req_inputspec_house_2floor_kitchen_heavy"
        ]
        
        examples_text = "\\n\\n=== FEW-SHOT EXAMPLES ===\\n\\n"
        
        for doc_id in example_ids:
            # Try to load from knowledge - get DocumentMeta first, then load content
            doc_meta = self.knowledge.get_doc_by_id(f"DOC_EX_{doc_id.upper()}")
            if doc_meta:
                content = self.knowledge.load_doc_content(doc_meta)
            else:
                content = ""
            if content:
                # Extract just the JSON parts for brevity
                examples_text += f"--- Example: {doc_id} ---\\n{content[:2000]}\\n\\n"
        
        return examples_text
    
    def _check_critical_missing(self, req: ProjectRequirements) -> List[str]:
        """
        Check for critical missing information
        
        Args:
            req: Project requirements
        
        Returns:
            List of critical missing fields
        """
        missing = []
        
        if not req.rooms or len(req.rooms) == 0:
            missing.append("rooms")
        
        if not req.loads or len(req.loads) == 0:
            missing.append("loads")
        
        if not req.voltage_system:
            missing.append("voltage_system")
        
        # Check room details
        for i, room in enumerate(req.rooms):
            if not room.type:
                missing.append(f"room[{i}].type")
        
        return missing
    
    async def _generate_clarifying_questions(
        self,
        req: ProjectRequirements,
        missing_fields: List[str]
    ) -> List[str]:
        """
        Generate clarifying questions using LLM
        
        Args:
            req: Partial requirements
            missing_fields: List of missing fields
        
        Returns:
            List of questions in Thai
        """
        prompt = f"""คุณคือ AI ผู้ช่วยออกแบบระบบไฟฟ้า

ผู้ใช้ต้องการออกแบบ: {req.project_name or 'โครงการ'}
ประเภทอาคาร: {req.building_type}

ข้อมูลที่ยังขาด: {', '.join(missing_fields)}

กรุณาสร้างคำถาม 3-5 ข้อเป็นภาษาไทย เพื่อเก็บข้อมูลที่ขาดหายไป
คำถามต้องเฉพาะเจาะจงและช่วยให้ได้ข้อมูลครบ

ตอบเป็น JSON: {{"questions": ["คำถาม 1", "คำถาม 2", ...]}}
"""
        
        try:
            config = self._get_generation_config(temperature=0.3, max_tokens=500, json_mode=True)
            response_text = self._generate_content(prompt, config)
            
            result = json.loads(response_text)
            return result.get('questions', [])
            
        except Exception as e:
            logger.warning(f"Failed to generate questions: {e}")
            # Fallback to generic questions
            return [
                "มีห้องอะไรบ้างในโครงการ?",
                "แต่ละห้องมีอุปกรณ์ไฟฟ้าอะไรบ้าง?",
                "ระบบไฟฟ้าที่ต้องการคือแบบไหน (1 เฟส 230V หรือ 3 เฟส)?"
            ]
    
    async def generate_mcp_spec(self, req: ProjectRequirements) -> McpSpecResponse:
        """
        Generate MCP ProjectInputSpec from human requirements
        
        This is the CORE transformation: Human Language → Semantic Spec
        
        All 9 improvements applied here:
        1. Pre-validation
        2. Knowledge-based retrieval
        3. Few-shot learning
        4. Retry with self-correction
        5. Trust logging
        6. Proper error handling
        7. Structured models (no Dict)
        8. LLM metadata
        9. Canonical records
        
        Args:
            req: Project requirements (human-readable)
        
        Returns:
            MCP spec response ready for MCP Core v2
        
        Raises:
            HTTPException: 400 (incomplete), 422 (parse fail), 503 (DB), 504 (LLM timeout)
        """
        import uuid
        from fastapi import HTTPException
        
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] Starting MCP spec generation")
        
        # IMPROVEMENT 1: Pre-validate requirements
        validation_errors = self._validate_requirements(req)
        
        # Check for critical missing fields (Phase 3)
        missing_critical = self._check_critical_missing(req)
        
        if missing_critical:
            logger.warning(f"[{request_id}] Critical fields missing: {missing_critical}")
            
            # Generate clarifying questions
            questions = await self._generate_clarifying_questions(req, missing_critical)
            
            # Throw HTTP 422 with questions (NOT a response type)
            raise HTTPException(
                status_code=422,
                detail=InsufficientDataError(
                    missing_fields=missing_critical,
                    questions=questions,
                    suggestions=[
                        "Please provide complete room information",
                        "Specify all electrical loads with room assignments",
                        "Confirm voltage system (TH_1PH_230V or TH_3PH_400V)"
                    ]
                ).model_dump()
            )
        
        if validation_errors:
            logger.warning(f"[{request_id}] Validation failed: {validation_errors}")
            
            # Log failed validation
            trust_record = trust_logger.create_record(
                project_requirements=req.model_dump(),
                retrieved_doc_ids=[],
                llm_model="N/A",
                raw_llm_output="",
                parse_success=False,
                validation_errors=validation_errors,
                project_input=None
            )
            trust_logger.log_mcp_spec(trust_record)
            
            raise HTTPException(400, detail={
                "error": "Invalid project requirements structure",
                "validation_errors": validation_errors,
                "suggestion": "Please provide complete room types and ensure all loads reference existing rooms"
            })
        
        # IMPROVEMENT 2: Use Knowledge Service - folder-based (Phase 3)
        docs = self.knowledge.get_docs_for_mcp_spec()
        logger.info(f"[{request_id}] Retrieved {len(docs)} docs from 4 folders (db, mcp, standard, example)")
        
        # Build context from top priority docs
        context_parts = []
        retrieved_doc_ids = []
        for doc in docs[:15]:  # Top 15 by priority
            content = self.knowledge.load_doc_content(doc)
            if content:
                # Anonymize and truncate
                safe_content = self.privacy.anonymize(content[:3000])
                context_parts.append(
                    f"[{doc.folder.value}/{doc.rel_path}]\n{safe_content}"
                )
                retrieved_doc_ids.append(f"{doc.folder.value}/{doc.rel_path}")
        
        context_str = "\n\n".join(context_parts)
        
        # IMPROVEMENT 3: Load few-shot examples from example folder
        example_docs = self.knowledge.list_docs(folder="example")
        examples_str = "\n\n=== FEW-SHOT EXAMPLES ===\n\n"
        for ex_doc in example_docs[:2]:  # Top 2 examples
            ex_content = self.knowledge.load_doc_content(ex_doc)
            if ex_content:
                examples_str += f"--- {ex_doc.rel_path} ---\n{ex_content[:2000]}\n\n"
        
        # PHASE 4: STAGE 1 - Generate Human-Readable Plan
        logger.info(f"[{request_id}] STAGE 1: Generating plan...")
        plan_text = await self._generate_spec_plan(req, context_str, examples_str)
        logger.info(f"[{request_id}] Plan generated ({len(plan_text)} chars)")

        
        # IMPROVEMENT 4 & 7: Retry logic with proper schema
        max_attempts = settings.RETRY_MAX_ATTEMPTS
        raw_llm_output = ""
        parse_success = False
        validation_errors_list = []
        project_input_dict = None
        spec_response: Optional[McpSpecResponse] = None  # Initialize to avoid unbound error
        
        for attempt in range(max_attempts):
            logger.info(f"[{request_id}] LLM attempt {attempt + 1}/{max_attempts}")
            
            # Build prompt
            if attempt == 0:
                # Stage 2: Generate spec following plan
                prompt = self._build_initial_prompt(req, plan_text, context_str, examples_str)
            else:
                # Self-correction prompt
                prompt = self._build_correction_prompt(req, raw_llm_output, validation_errors_list)
            
            try:
                config = self._get_generation_config(
                    temperature=settings.GENERATION_TEMPERATURE,
                    max_tokens=settings.MAX_OUTPUT_TOKENS,
                    json_mode=True
                )
                raw_llm_output = self._generate_content(prompt, config)
                
                # Parse LLM output - may be partial (missing standards_profile, llm_metadata)
                # We'll fill in defaults for missing fields
                try:
                    spec_response = McpSpecResponse.model_validate_json(raw_llm_output)
                except ValidationError:
                    # Try to parse partial JSON and fill in missing fields
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', raw_llm_output)
                    if json_match:
                        partial_data = json.loads(json_match.group())
                        
                        # Check if project_input exists (minimum requirement)
                        if 'project_input' in partial_data:
                            logger.info(f"[{request_id}] Partial JSON found, adding defaults...")
                            
                            # Ensure project_input.constraints exists with correct schema
                            if 'constraints' not in partial_data['project_input']:
                                partial_data['project_input']['constraints'] = {
                                    "rule_profile_id": "TH_RESIDENTIAL_LV",
                                    "user_constraints": []
                                }
                            elif isinstance(partial_data['project_input']['constraints'], list):
                                # If LLM returned empty list, convert to proper object
                                partial_data['project_input']['constraints'] = {
                                    "rule_profile_id": "TH_RESIDENTIAL_LV",
                                    "user_constraints": partial_data['project_input']['constraints']
                                }
                            
                            # Add default standards_profile if missing (correct schema)
                            if 'standards_profile' not in partial_data:
                                partial_data['standards_profile'] = {
                                    "rule_profile_id": "EIT_2021_RESIDENTIAL",
                                    "notes": "มาตรฐาน วสท. 2021 สำหรับบ้านพักอาศัย"
                                }
                            
                            # Add default llm_metadata if missing
                            if 'llm_metadata' not in partial_data:
                                from datetime import datetime, timezone
                                partial_data['llm_metadata'] = {
                                    "model": settings.MODEL_NAME_ANSWER,
                                    "retrieved_docs": retrieved_doc_ids[:5],
                                    "temperature": settings.GENERATION_TEMPERATURE,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                            
                            # Fix common LLM field name variations
                            if 'loads' in partial_data['project_input']:
                                for load in partial_data['project_input']['loads']:
                                    # LLM may use 'quantity' instead of 'qty'
                                    if 'quantity' in load and 'qty' not in load:
                                        load['qty'] = load.pop('quantity')
                                    # LLM may use 'power_kw' instead of 'notes'
                                    if 'power_kw' in load:
                                        load.pop('power_kw', None)  # Remove, not needed
                            
                            # Try to validate with filled-in data
                            spec_response = McpSpecResponse.model_validate(partial_data)
                        else:
                            raise ValidationError.from_exception_data("Missing project_input", [])
                
                # Success!
                parse_success = True
                project_input_dict = spec_response.project_input.model_dump()
                logger.info(f"[{request_id}] Successfully parsed spec on attempt {attempt + 1}")
                break
                
            except ValidationError as e:
                validation_errors_list = [str(err) for err in e.errors()]
                logger.warning(f"[{request_id}] Parse failed (attempt {attempt + 1}): {validation_errors_list}")
                
                if attempt == max_attempts - 1:
                    # Final attempt failed
                    logger.error(f"[{request_id}] All retry attempts exhausted")
                    
            except Exception as e:
                logger.error(f"[{request_id}] LLM generation error: {e}")
                if "timeout" in str(e).lower():
                    raise HTTPException(504, "LLM provider timeout")
                raise HTTPException(502, "LLM provider error")
        
        # PHASE 5: Quality Check (if parse successful)
        qc_status = "N/A"
        qc_issues = []
        if parse_success and spec_response is not None:
            logger.info(f"[{request_id}] Running quality check...")
            qc_status, qc_issues = await self._quality_check_spec(spec_response, req)
            logger.info(f"[{request_id}] QC Status: {qc_status}, Issues: {len(qc_issues)}")
            
            # Add warnings to metadata if WARN
            if qc_status == "WARN":
                # Log warnings (can't modify frozen model)
                logger.warning(f"[{request_id}] QC Warnings: {qc_issues}")
            
            # Fail if critical issues
            elif qc_status == "FAIL":
                logger.error(f"[{request_id}] QC Failed: {qc_issues}")
                # Log failure and re-throw as 422
                parse_success = False
                validation_errors_list.extend(qc_issues)
        
        
        # IMPROVEMENT 5 & 9: Trust logging (with plan from Phase 4)
        trust_record = trust_logger.create_record(
            project_requirements=req.model_dump(),
            retrieved_doc_ids=retrieved_doc_ids,  # From folder-based retrieval
            llm_model=settings.MODEL_NAME_ANSWER,
            llm_plan_text=plan_text,  # Phase 4: Store plan
            raw_llm_output=raw_llm_output,
            parse_success=parse_success,
            validation_errors=validation_errors_list if not parse_success else [],
            project_input=project_input_dict,
            forwarded_to_mcp=False  # Will be updated by gateway
        )
        trust_logger.log_mcp_spec(trust_record)
        
        # If all attempts failed
        if not parse_success:
            raise HTTPException(422, detail={
                "error": "Failed to generate valid McpSpecResponse",
                "validation_errors": validation_errors_list,
                "llm_output_preview": raw_llm_output[:500]
            })
        
        # IMPROVEMENT 6 & 8: Proper response with metadata
        assert spec_response is not None  # Guaranteed by parse_success check above
        return spec_response
    
    def _build_initial_prompt(self, req: ProjectRequirements, plan: str, context: str, examples: str) -> str:
        """Build initial generation prompt following plan (Stage 2)"""
        return f"""You are 'Aura', the Goddess of Code Creation. Generate a JSON spec for MCP Core v2.

**YOUR PLAN** (ทำตามนี้):
{plan}

CRITICAL RULES:
1. **FOLLOW THE PLAN ABOVE** - อ้างอิงแผนที่สร้างไว้
2. **DO NOT CALCULATE** electrical values (No Voltage Drop, No Cable Size)
3. Output STRICTLY valid JSON matching McpSpecResponse schema
4. Use provided EXAMPLES as templates
5. Map room types: living_room→LIVING, bedroom→BEDROOM, kitchen→KITCHEN, bathroom→BATHROOM
6. Generate sequential IDs: R1, R2... for rooms, L1, L2... for loads
7. Link loads to rooms via room_id
8. Use template codes from plan (ROOMT-LIVING-STD, ROOMT-KITCHEN-HEAVY, etc.)
9. Map devices according to rag_knowledge/db/DEVICE_CODES.md
10. Use rule_profile_id as planned
11. **IMPORTANT: PRESERVE FLOOR FROM INPUT** - ถ้า rooms มี floor ให้ใส่ใน output ด้วย
12. **IMPORTANT: LOADS MUST HAVE FLOOR** - ทุก load ต้องมี floor ตาม room ที่อ้างอิง

{examples}

CONTEXT FROM KNOWLEDGE BASE:
{context[:15000]}

USER REQUIREMENTS:
{req.model_dump_json(indent=2)}

OUTPUT JSON (McpSpecResponse):
{{
  "project_input": {{
    "project_info": {{"project_name": "...", "building_type": "RESIDENTIAL", "spec_version": "2.0"}},
    "electrical_system": {{"voltage_system": "...", "earthing": "TT"}},
    "rooms": [...],
    "loads": [
      {{"load_id": "L1", "room_id": "R1", "device_code": "...", "qty": 1, "floor": 1}},
      ...
    ],
    "constraints": {{"rule_profile_id": "TH_RESIDENTIAL_LV", "user_constraints": [...]}}
  }},
  "standards_profile": {{"rule_profile_id": "TH_RESIDENTIAL_LV", "notes": "..."}},
  "llm_metadata": {{"model": "{settings.MODEL_NAME_ANSWER}", "retrieved_docs": [...], "temperature": {settings.GENERATION_TEMPERATURE}, "timestamp": "..."}}
}}

Execute the plan and generate complete, valid JSON now:
"""
    
    def _build_correction_prompt(self, req: ProjectRequirements, prev_output: str, errors: List[str]) -> str:
        """Build self-correction prompt"""
        return f"""Your previous JSON output had validation errors. Please fix them.

ORIGINAL REQUIREMENTS:
{req.model_dump_json(indent=2)}

YOUR PREVIOUS OUTPUT:
{prev_output[:2000]}

VALIDATION ERRORS:
{json.dumps(errors, indent=2)}

Please generate CORRECTED JSON addressing all errors above. Follow the McpSpecResponse schema exactly:
"""
    
    async def retrieve_raw(self, req: RawRetrieveRequest) -> List[Dict[str, Any]]:
        """
        Raw retrieval for debugging
        
        Args:
            req: Raw retrieve request
        
        Returns:
            List of raw search results
        """
        logger.debug(f"Raw retrieval: {req.query}")
        return self.db.search(req.query, filters=req.filters, top_k=req.top_k)
    
    # === Phase 4: Plan Generation ===
    
    async def _generate_spec_plan(
        self,
        req: ProjectRequirements,
        context: str,
        examples: str
    ) -> str:
        """
        Generate human-readable plan before creating spec (Phase 4)
        
        Args:
            req: Project requirements
            context: Knowledge context
            examples: Few-shot examples
        
        Returns:
            Plan text in Thai
        """
        # Get valid templates for prompt
        valid_templates = self._get_valid_room_templates()
        templates_list = ", ".join(sorted(valid_templates)) if valid_templates else "ROOMT-LIVING-STD, ROOMT-KITCHEN-STD, ROOMT-BEDROOM-STD, ROOMT-BATHROOM-STD"
        
        prompt = f"""คุณคือ Aura ผู้ช่วยวางแผนการออกแบบระบบไฟฟ้า

สร้างแผนการออกแบบเป็นภาษาไทยโดยละเอียด

แหล่งความรู้ที่มี:
- rag_knowledge/db/ → catalog อุปกรณ์, template, กฎการออกแบบ
- rag_knowledge/standard/ → มาตรฐานไฟฟ้าไทย
- rag_knowledge/example/ → โครงการตัวอย่าง

**⚠️ VALID ROOM TEMPLATES (ใช้ได้เท่านี้เท่านั้น):**
{templates_list}

ข้อกำหนดโครงการ:
{req.model_dump_json(indent=2, exclude_none=True)}

บริบทจากความรู้:
{context[:8000]}

สร้างแผนครอบคลุม:
1. **วิเคราะห์ห้อง**: ระบุห้องทั้งหมดพร้อมชนิดและพื้นที่
2. **จัดกลุ่มโหลด**: แยกตามประเภท (แอร์/ไฟ/เต้ารับ/อุปกรณ์พิเศษ)
3. **ตรวจสอบโหลดหนัก**: ห้องไหนมีโหลด >3kW
4. **เลือก Template**: ใช้ ROOMT-* จากรายการด้านบนเท่านั้น! เช่น:
   - ห้องนั่งเล่น → ROOMT-LIVING-STD (ขนาดปกติ) หรือ ROOMT-LIVING-LARGE (≥25 ตร.ม.)
   - ครัว → ROOMT-KITCHEN-STD หรือ ROOMT-KITCHEN-HEAVY (มีเตาแม่เหล็ก/โหลดหนัก)
   - ห้องนอน → ROOMT-BEDROOM-STD หรือ ROOMT-BEDROOM-MASTER
   - ห้องน้ำ → ROOMT-BATHROOM-STD หรือ ROOMT-BATHROOM-MASTER
5. **ข้อกำหนดพิเศษ**: user_constraints มีผลยังไง
6. **Rule Profile**: เลือก rule_profile_id ตามประเภทอาคาร

เขียนเป็นรายการเลขลำดับ อ้างอิงไฟล์ความรู้ที่เกี่ยวข้อง:
"""
        
        try:
            config = self._get_generation_config(temperature=0.2, max_tokens=2000)
            return self._generate_content(prompt, config)
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return f"[Plan generation failed: {e}]"
    
    # === Validation Functions (Phase 2: NO DB ACCESS) ===
    
    def _normalize_device_code(self, code: str) -> str:
        """
        Normalize device code for comparison
        
        Handles variations like:
        - AC-12000BTU vs AC_12000BTU
        - HEATER-3500W vs WATER_HEATER_3500W
        - SOCKET-16A vs OUTLET_16A
        
        Returns:
            Normalized code (uppercase, underscores replaced with dashes)
        """
        if not code:
            return ""
        
        # Basic normalization: uppercase and replace underscore with dash
        normalized = code.upper().replace("_", "-")
        
        # Common synonyms mapping
        synonyms = {
            "WATER-HEATER": "HEATER",
            "OUTLET": "SOCKET",
            "INDUCTION-COOKER": "INDUCTION",
        }
        
        for old, new in synonyms.items():
            if old in normalized:
                normalized = normalized.replace(old, new)
        
        return normalized
    
    def _get_valid_device_codes(self) -> set[str]:
        """
        Load valid device codes from rag_knowledge/db/DEVICE_CODES.md
        
        CRITICAL RULES:
        - ห้าม import DB client (psycopg2, supabase, etc.)
        - ห้าม query amadeus.catalog
        - อ่านจาก DEVICE_CODES.md เท่านั้น
        
        To refresh snapshot:
        - Run scripts/build_device_codes_snapshot.py manually
        
        Returns:
            Set of normalized valid device codes
        """
        db_docs = self.knowledge.list_docs(folder="db")
        
        device_codes_doc = next(
            (d for d in db_docs if "DEVICE_CODES" in d.rel_path),
            None
        )
        
        if not device_codes_doc:
            logger.warning("DEVICE_CODES.md not found in rag_knowledge/db/")
            return set()
        
        content = self.knowledge.load_doc_content(device_codes_doc)
        codes = self._parse_device_codes(content)
        
        # Normalize all codes for flexible matching
        normalized_codes = {self._normalize_device_code(c) for c in codes}
        
        logger.debug(f"Loaded {len(normalized_codes)} valid device codes from snapshot")
        return normalized_codes
    
    def _parse_device_codes(self, content: str) -> List[str]:
        """
        Parse DEVICE_CODES.md format
        
        Expected format: - `CODE` - Description
        
        Args:
            content: Markdown file content
        
        Returns:
            List of device codes
        """
        import re
        codes = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('-') and '`' in line:
                # Extract code between backticks
                match = re.search(r'`([^`]+)`', line)
                if match:
                    codes.append(match.group(1))
        
        return codes
    
    def _get_valid_room_templates(self) -> set[str]:
        """
        Load valid room templates from rag_knowledge/db/ROOM_TEMPLATES.md
        
        Returns:
            Set of valid template codes
        """
        db_docs = self.knowledge.list_docs(folder="db")
        
        templates_doc = next(
            (d for d in db_docs if "ROOM_TEMPLATES" in d.rel_path),
            None
        )
        
        if not templates_doc:
            logger.warning("ROOM_TEMPLATES.md not found in rag_knowledge/db/")
            return set()
        
        content = self.knowledge.load_doc_content(templates_doc)
        templates = self._parse_device_codes(content)  # Same parser works
        
        logger.debug(f"Loaded {len(templates)} valid room templates from snapshot")
        return set(templates)
    
    # === Phase 5: Quality Check ===
    
    async def _quality_check_spec(
        self,
        spec: McpSpecResponse,
        original_req: ProjectRequirements
    ) -> tuple[str, List[str]]:
        """
        Quality check generated spec (Phase 5)
        
        Checks:
        - Rule-based: device codes, room templates validity
        - LLM judge: semantic correctness
        
        Args:
            spec: Generated spec
            original_req: Original requirements
        
        Returns:
            Tuple of (status, issues)
            status: "PASS" | "WARN" | "FAIL"
            issues: List of issue descriptions
        """
        issues = []
        
        # Rule 1: Check device codes against rag_knowledge/db/DEVICE_CODES.md
        # Use normalized comparison to handle variations (AC-12000BTU vs AC_12000BTU)
        valid_codes = self._get_valid_device_codes()
        for load in spec.project_input.loads:
            if load.device_code:
                normalized_load_code = self._normalize_device_code(load.device_code)
                if normalized_load_code not in valid_codes:
                    issues.append(
                        f"Invalid device_code '{load.device_code}' "
                        f"(not in rag_knowledge/db/DEVICE_CODES.md)"
                    )
        
        # Rule 2: Check room templates against rag_knowledge/db/ROOM_TEMPLATES.md
        valid_templates = self._get_valid_room_templates()
        for room in spec.project_input.rooms:
            if room.template_code and room.template_code not in valid_templates:
                issues.append(
                    f"Invalid template '{room.template_code}' "
                    f"(not in rag_knowledge/db/ROOM_TEMPLATES.md)"
                )
        
        # Rule 3: Check rooms/loads completeness
        if len(spec.project_input.rooms) == 0:
            issues.append("No rooms in spec")
        
        if len(spec.project_input.loads) == 0:
            issues.append("No loads in spec")
        
        # Rule 4: LLM semantic judge
        llm_issues = await self._llm_semantic_check(spec, original_req)
        issues.extend(llm_issues)
        
        # Classify severity
        if not issues:
            return "PASS", []
        elif len(issues) <= 2 and not any("Invalid" in i for i in issues):
            return "WARN", issues
        else:
            return "FAIL", issues
    
    async def _llm_semantic_check(
        self,
        spec: McpSpecResponse,
        req: ProjectRequirements
    ) -> List[str]:
        """
        LLM-based semantic validation
        
        Args:
            spec: Generated spec
            req: Original requirements
        
        Returns:
            List of semantic issues
        """
        prompt = f"""คุณคือ QC judge สำหรับ electrical spec

**Requirements ต้นฉบับ**:
{req.model_dump_json(indent=2, exclude_none=True)}

**Spec ที่สร้าง**:
- Rooms: {len(spec.project_input.rooms)} ห้อง
- Loads: {len(spec.project_input.loads)} loads
- Voltage: {spec.project_input.electrical_system.voltage_system}

**Room Details**:
{json.dumps([{'room_type': r.room_type, 'template': r.template_code} for r in spec.project_input.rooms], indent=2, ensure_ascii=False)}

**Load Summary**:
{json.dumps([{'device_code': l.device_code, 'room_id': l.room_id} for l in spec.project_input.loads[:10]], indent=2, ensure_ascii=False)}

ตรวจสอบ:
1. จำนวนห้องถูกต้องหรือไม่?
2. device mapping สมเหตุสมผลหรือไม่?
3. template เลือกเหมาะสมหรือไม่?
4. loads ครบตาม requirements หรือไม่?

ถ้าพบปัญหา ให้ตอบ JSON: {{"issues": ["ปัญหา 1", "ปัญหา 2"]}}
ถ้าไม่มีปัญหา ตอบ: {{"issues": []}}
"""
        
        try:
            config = self._get_generation_config(temperature=0.1, max_tokens=500, json_mode=True)
            response_text = self._generate_content(prompt, config)
            
            result = json.loads(response_text)
            return result.get('issues', [])
            
        except Exception as e:
            logger.warning(f"LLM semantic check failed: {e}")
            return []  # Don't fail QC if judge fails
