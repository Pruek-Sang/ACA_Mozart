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
from app.formatters import format_design_report  # Card-style Markdown formatter
from core.privacy import PrivacyGuard

logger = logging.getLogger("Aura.Service")

# =============================================================================
# Constants for duplicated string literals (SonarQube compliance)
# =============================================================================
ROOM_LIVING = "ห้องนั่งเล่น"
ROOM_KITCHEN = "ห้องครัว"
ROOM_BEDROOM = "ห้องนอน"
ROOM_BATHROOM_1 = "ห้องน้ำ 1"
ROOM_BATHROOM_2 = "ห้องน้ำ 2"
ROOM_BATHROOM = "ห้องน้ำ"
ROOM_COMMON = "พื้นที่ส่วนกลาง"
DEVICE_WATER_HEATER = "เครื่องทำน้ำอุ่น"
DEVICE_PUMP = "ปั๊มน้ำ"
DEVICE_INDUCTION = "เตาแม่เหล็กไฟฟ้า"

# =============================================================================
# Site Context Validation Constants
# =============================================================================
REQUIRED_SITE_FIELDS = ["distance_to_transformer", "installation_area", "panel_type"]
VALID_SITE_VALUES = {
    "distance_to_transformer": ["less_than_50m", "50_100m", "more_than_100m"],
    "installation_area": ["indoor", "high_temp", "outdoor", "underground"],
    "panel_type": ["main", "sub"]
}

# Prompt templates for missing fields
MISSING_FIELD_PROMPTS = {
    "distance_to_transformer": "❓ **ระยะห่างจากหม้อแปลง?**\n   • น้อยกว่า 50 เมตร\n   • 50-100 เมตร\n   • มากกว่า 100 เมตร",
    "installation_area": "❓ **พื้นที่ติดตั้ง?**\n   • ในอาคาร/ในบ้าน\n   • ใต้หลังคา/อุณหภูมิสูง\n   • กลางแจ้ง/ฝังดิน",
    "panel_type": "❓ **ประเภทตู้ไฟ?**\n   • ตู้เมน (Main Panel)\n   • ตู้ย่อย (Sub Panel)"
}


def is_site_context_complete(ctx: Optional[Dict[str, Any]]) -> tuple:
    """Check if site_context has all required fields.
    
    Returns:
        tuple: (is_complete: bool, missing_fields: list)
    """
    if not ctx:
        return False, REQUIRED_SITE_FIELDS.copy()
    missing = [f for f in REQUIRED_SITE_FIELDS if f not in ctx or not ctx[f]]
    return len(missing) == 0, missing


def build_missing_field_prompt(missing_fields: list) -> str:
    """Build a prompt asking user for specific missing fields."""
    if not missing_fields:
        return ""
    
    lines = ["⚠️ กรุณาระบุข้อมูลเพิ่มเติม:\n"]
    for field in missing_fields:
        if field in MISSING_FIELD_PROMPTS:
            lines.append(MISSING_FIELD_PROMPTS[field])
    
    lines.append("\n💡 ตัวอย่าง: \"หม้อแปลง 80 เมตร ติดตั้งในบ้าน ตู้เมน\"")
    return "\n".join(lines)


def extract_site_context_from_text(text: str) -> Dict[str, str]:
    """Extract site_context fields from Thai natural language text.
    
    Uses regex to detect values for:
    - distance_to_transformer
    - installation_area  
    - panel_type
    - conduit_grouping (optional)
    
    Returns:
        Dict with extracted fields (may be empty or partial)
    """
    import re
    
    context = {}
    text_lower = text.lower()
    
    # 1. Distance to transformer
    if re.search(r'(?:หม้อแปลง|transformer).*(?:น้อยกว่า|ใกล้|<)\s*50', text):
        context['distance_to_transformer'] = 'less_than_50m'
    elif re.search(r'(?:หม้อแปลง|transformer).*(?:50|ห้าสิบ).*(?:100|ร้อย)', text):
        context['distance_to_transformer'] = '50_100m'
    elif re.search(r'(?:หม้อแปลง|transformer).*(?:มากกว่า|ไกล|>)\s*100', text):
        context['distance_to_transformer'] = 'more_than_100m'
    elif re.search(r'\d+\s*(?:เมตร|m)', text):
        match = re.search(r'(\d+)\s*(?:เมตร|m)', text)
        if match:
            distance = int(match.group(1))
            if distance < 50:
                context['distance_to_transformer'] = 'less_than_50m'
            elif distance <= 100:
                context['distance_to_transformer'] = '50_100m'
            else:
                context['distance_to_transformer'] = 'more_than_100m'
    
    # 2. Installation area
    if re.search(r'(?:ภายใน|indoor|ในบ้าน|ในอาคาร)', text_lower):
        context['installation_area'] = 'indoor'
    elif re.search(r'(?:ใต้หลังคา|หลังคา|ร้อน|อุณหภูมิสูง|high.?temp)', text_lower):
        context['installation_area'] = 'high_temp'
    elif re.search(r'(?:กลางแจ้ง|outdoor|นอกบ้าน|นอกอาคาร)', text_lower):
        context['installation_area'] = 'outdoor'
    elif re.search(r'(?:ฝังดิน|underground|ใต้ดิน)', text_lower):
        context['installation_area'] = 'underground'
    
    # 3. Panel type
    if re.search(r'(?:ตู้เมน|main\s*panel|mdb|ตู้หลัก)', text_lower):
        context['panel_type'] = 'main'
    elif re.search(r'(?:ตู้ย่อย|sub\s*panel|db|ตู้รอง)', text_lower):
        context['panel_type'] = 'sub'
    
    # 4. Conduit grouping (optional)
    if re.search(r'(?:รวมท่อ|ท่อรวม|grouping|bundle)', text_lower):
        if re.search(r'(?:4|5|6|สี่|ห้า|หก)\s*(?:วงจร|circuit)', text_lower):
            context['conduit_grouping'] = '4-6'
        elif re.search(r'(?:2|3|สอง|สาม)\s*(?:วงจร|circuit)', text_lower):
            context['conduit_grouping'] = '2-3'
    
    return context


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
        
        # =====================================================================
        # AUTO-INGEST: Only run in Codespace environment (not Docker/Local)
        # Docker/Local should use pre-built vector_db from Git
        # =====================================================================
        is_codespace = os.getenv("CODESPACES") == "true"
        if self.db.count() == 0:
            if is_codespace:
                logger.warning("⚠️ Vector DB is empty! Auto-ingesting knowledge base...")
                self._auto_ingest_knowledge()
            else:
                logger.error("❌ Vector DB is empty! Please ensure vector_db/ is included from Git.")
                logger.error("   Run 'git pull' or check that vector_db/ was not deleted.")
                raise RuntimeError("Vector DB is empty. Pre-built vector_db/ required for Local/Docker.")
        
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
    
    def _auto_ingest_knowledge(self) -> None:
        """
        Auto-ingest knowledge base when vector_db is empty
        This is a safety net to prevent RAG from being unable to answer
        """
        from pathlib import Path
        from core.ingest import IngestionEngine
        
        try:
            engine = IngestionEngine()
            knowledge_root = Path(settings.KNOWLEDGE_ROOT)
            
            folders = ["db", "example", "mcp", "standard"]
            total_docs = 0
            
            for folder_name in folders:
                folder_path = knowledge_root / folder_name
                if not folder_path.exists():
                    logger.warning(f"Folder not found: {folder_path}")
                    continue
                
                docs = engine.process_folder(str(folder_path))
                if docs:
                    self.db.upsert(docs)
                    total_docs += len(docs)
                    logger.info(f"✅ Auto-ingested {len(docs)} chunks from {folder_name}/")
            
            logger.info(f"✨ Auto-ingest complete! Total: {total_docs} documents")
            
        except Exception as e:
            logger.error(f"❌ Auto-ingest failed: {e}")
            raise RuntimeError(f"Failed to auto-ingest knowledge base: {e}")
    
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
        
        for i, room in enumerate(rooms):
            room_name = room.name
            room_type = room.type if hasattr(room, 'type') else "bedroom"
            
            # Try to get area: first from room.area_sqm, then from raw_rooms
            area = 25.0  # default 5x5
            if hasattr(room, 'area_sqm') and room.area_sqm is not None:
                area = float(room.area_sqm)
            elif i < len(raw_rooms):
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
            
            # ห้องน้ำ: lock เป็น 1 ดวงเสมอ (พื้นที่เล็ก หลอดเดียวพอ)
            # ห้องนอน: คำนวณตามพื้นที่ปกติ (ผู้ใช้อาจติดหลอดสว่างมากได้)
            if room_type == "bathroom":
                num_fixtures = 1
            else:
                num_fixtures = max(1, math.ceil(area / area_per_fixture))
            
            # Cap at reasonable max (8 for large rooms, 4 for small rooms)
            if area > 50:
                max_fixtures = 8
            elif area > 30:
                max_fixtures = 6
            else:
                max_fixtures = 4
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
            'เครื่องทำน้ำร้อน': DEVICE_WATER_HEATER,
            'เครื่องน้ำอุ่น': DEVICE_WATER_HEATER,
            'วอเตอร์ฮีทเตอร์': DEVICE_WATER_HEATER,
            'water heater': DEVICE_WATER_HEATER,
            'ฮีทเตอร์': DEVICE_WATER_HEATER,
            
            # ปั๊มน้ำ
            'ปั้มน้ำ': DEVICE_PUMP,
            'ปั้ม': DEVICE_PUMP,
            'pump': DEVICE_PUMP,
            
            # เตา
            'เตาไฟฟ้า': DEVICE_INDUCTION,
            'เตาแม่เหล็ก': DEVICE_INDUCTION,
            'induction': DEVICE_INDUCTION,
            
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

    def _extract_loads_from_text(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to extract structured loads from natural language query.
        
        Returns dict with: project_name, rooms, loads, missing_info
        """
        # Pre-process: แก้คำผิด/คำคล้าย
        normalized_query = self._normalize_typos(query)
        logger.info(f"📝 Normalized query: {normalized_query[:100]}...")
        
        extraction_prompt = f'''คุณเป็น parser สำหรับแปลงคำขอออกแบบไฟฟ้าเป็น JSON

🌍 **รับทุกภาษา (Multilingual):**
ผู้ใช้อาจพิมพ์ภาษาไทย, English, 中文, 日本語, Deutsch, Español หรือผสมหลายภาษา
คุณต้องเข้าใจและแปลงเป็น JSON ได้ทุกกรณี

📝 ตัวอย่างที่ต้องเข้าใจ:
- "2-story house with AC" = บ้าน 2 ชั้น มีแอร์
- "บ้าน2ชึ้น มีair 3ตัว" = บ้าน 2 ชั้น แอร์ 3 ตัว
- "heater 4500w" = น้ำอุ่น 4500W
- "kitchen induction" = ห้องครัวมีเตาแม่เหล็กไฟฟ้า

จากข้อความ: "{normalized_query}"

⚠️ คำที่ต้องระวัง (Fuzzy Matching หลายภาษา):
- "แอ", "แอ์", "เเอร์", "แอร", "ac", "air", "aircon", "เครื่องปรับอากาศ", "空调", "エアコン" → หมายถึง "แอร์"
- "น้ำร้อน", "เครื่องทำน้ำร้อน", "ฮีทเตอร์", "water heater", "heater", "热水器" → หมายถึง "น้ำอุ่น"
- "ปั้มน้ำ", "ปั้ม", "pump", "water pump" → หมายถึง "ปั๊มน้ำ"
- "เตาไฟฟ้า", "เตาแม่เหล็ก", "induction", "electric stove" → หมายถึง "เตาแม่เหล็กไฟฟ้า"
- "bedroom", "ห้องนอน", "寝室" → ห้องนอน
- "bathroom", "ห้องน้ำ", "toilet" → ห้องน้ำ
- "kitchen", "ห้องครัว", "厨房" → ห้องครัว
- "living", "living room", "ห้องนั่งเล่น" → ห้องนั่งเล่น

ให้ตอบเป็น JSON เท่านั้น (ไม่มีคำอธิบาย):
{{
  "project_name": "ชื่อโครงการ (ถ้าไม่ระบุให้ใส่ 'บ้านพักอาศัย')",
  "building_type": "residential",
  "voltage_system": "TH_1PH_230V",
  "num_floors": จำนวนชั้น (ถ้าไม่ระบุให้ใส่ 1),
  "rooms": [
    {{"name": "ชื่อห้อง", "type": "ประเภท (living/bedroom/kitchen/bathroom/storage/exterior)", "floor": ชั้นที่อยู่ (1 หรือ 2), "area_sqm": พื้นที่ตร.ม. (ถ้าระบุ เช่น "5x5" ให้คำนวณ = 25, ถ้าไม่ระบุให้ใส่ null)}}
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

🔌 กฎนับเต้ารับ (สำคัญมาก! ตาม วสท. 2564):
8. "คู่" และ "เดี่ยว" หมายถึง **ประเภท** ของเต้ารับ ไม่ใช่ตัวคูณ!
   - "เต้ารับคู่ 6 จุด" หรือ "คู่×6" → quantity: 6 (ไม่ใช่ 12!)
   - "เต้ารับเดี่ยว 1 จุด" หรือ "เดี่ยว×1" → quantity: 1
   - "จุด" = outlet box = 1 unit ตาม วสท. 2564 (ไม่ใช่จำนวนช่องเสียบ)
   - ทุกเต้ารับไม่ว่าคู่หรือเดี่ยว ใช้ device="SOCKET-16A" เสมอ
9. ตัวอย่างการนับ:
   - "ห้องนอน เต้ารับคู่ 4 จุด" → {{"room_name": "ห้องนอน", "device": "SOCKET-16A", "quantity": 4}}
   - "ห้องครัว คู่×6 + คู่×2" → {{"room_name": "ห้องครัว", "device": "SOCKET-16A", "quantity": 8}}
   - "ห้องน้ำ เดี่ยว×1" → {{"room_name": "ห้องน้ำ", "device": "SOCKET-16A", "quantity": 1}}

🔧 กฎอุปกรณ์พิเศษ:
10. เครื่องทำน้ำอุ่น/เต้ารับกันน้ำ (ห้องน้ำ/ภายนอก) → ต้องใช้ RCBO (ระบบจะกำหนดให้อัตโนมัติ)
11. EV Charger → ต้องเผื่อสาย 25% (Continuous Load) - ระบุ device="EV-CHARGER-7KW" หรือ "EV-CHARGER-22KW"
12. มอเตอร์/ปั๊มน้ำ → มี Inrush Current สูง - ใช้ device="PUMP-750W" หรือ "PUMP-1500W"

รหัสอุปกรณ์ที่ใช้ได้:
- แอร์: AC-9000BTU, AC-12000BTU, AC-18000BTU, AC-24000BTU
- น้ำอุ่น: HEATER-3500W, HEATER-4500W
- ไฟ LED: LIGHT-LED-10W, LIGHT-LED-20W
- เต้ารับ: SOCKET-16A (ใช้สำหรับทั้งคู่และเดี่ยว)
- ปั๊มน้ำ: PUMP-750W, PUMP-1500W
- เตา: INDUCTION-3000W
- EV Charger: EV-CHARGER-7KW, EV-CHARGER-22KW (ถ้าระบุ)
- พัดลมเพดาน: FAN-CEILING-60W
- พัดลมดูดอากาศ: FAN-EXHAUST-25W
- ไมโครเวฟ: MICROWAVE-1500W
- ตู้เย็น: REFRIG-300W
- กาต้มน้ำ: KETTLE-2200W
- หม้อหุงข้าว: RICECOOK-800W

🔥 กฎ Auto-fill (One-Shot Mode):
- ถ้าไม่ระบุห้อง ให้สร้างห้องมาตรฐาน (ห้องนั่งเล่น, ห้องนอน, ห้องครัว, ห้องน้ำ)
- ถ้าไม่ระบุ BTU ของแอร์ ให้ใช้ 12000BTU
- ถ้าไม่ระบุวัตต์น้ำอุ่น ให้ใช้ 4500W
- ถ้าบอกว่ามี "น้ำอุ่น" หรือ "เครื่องทำน้ำอุ่น" ให้ใส่ HEATER-4500W ในห้องน้ำทุกห้อง
- ถ้าบอกว่ามี "โคมไฟหน้าบ้าน" หรือ "ไฟหน้าบ้าน" ให้สร้างห้อง type="exterior" name="หน้าบ้าน" และใส่ LIGHT-LED-10W
- ❗ ใส่ missing_info: [] (ว่าง) เสมอ - ห้ามถามกลับ ต้อง auto-fill ให้ครบ

ตอบ JSON เท่านั้น:'''

        try:
            config = self._get_generation_config(temperature=0.1)
            response = self._generate_content(extraction_prompt, config)
            
            # 🆕 DEBUG: Log LLM response for troubleshooting
            logger.info(f"📤 LLM extraction response length: {len(response)} chars")
            logger.debug(f"📤 LLM response (first 500): {response[:500]}")
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                extracted = json.loads(json_match.group())
                # เก็บ original query ไว้สำหรับ auto-fill checks
                extracted["original_query"] = normalized_query
                
                # 🆕 Validation: Check if extraction actually succeeded
                rooms_count = len(extracted.get('rooms', []))
                loads_count = len(extracted.get('loads', []))
                logger.info(f"✅ Extracted: {rooms_count} rooms, {loads_count} loads")
                
                if rooms_count == 0 and loads_count == 0:
                    logger.warning("⚠️ LLM returned empty rooms AND loads - extraction likely failed")
                
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
            RoomInput(
                name=r["name"], 
                type=r["type"],
                area_sqm=r.get("area_sqm"),  # Pass area if LLM extracted it
                floor=r.get("floor") or 1   # Use 1 if floor is None or missing
            )
            for r in extracted.get("rooms", [])
        ]
        
        loads = [
            LoadInput(
                room_name=l["room_name"],
                device=l["device"],
                quantity=l.get("quantity") or 1  # Handle None from LLM
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
        # wire_sizing removed - unused (SonarQube)
        conduit_sizing = design.get("conduit_sizing", {})
        compliance = design.get("compliance_report", {})
        calculations = design.get("calculations", {})
        
        # [NEXIA] Get injector results
        design_warnings = design.get("warnings", [])  # From injectors
        site_context = result.get("site_context", {})  # Original site context
        
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
        outlets_displayed_floors = set()  # Track which floors already displayed outlets
        if language == "th":
            # Get project name from project_req or use default
            project_name = "บ้านพักอาศัย"
            if project_req and hasattr(project_req, 'project_name') and project_req.project_name:
                project_name = project_req.project_name
            
            # ═══════════════════════════════════════════
            # HEADER - Professional Engineering Report Style
            # ═══════════════════════════════════════════
            lines.append("╔══════════════════════════════════════════════════════════════╗")
            lines.append("║        ตารางโหลดและวงจรย่อย (LOAD SCHEDULE)                  ║")
            lines.append("╚══════════════════════════════════════════════════════════════╝")
            lines.append("")
            lines.append(f"📋 โครงการ: {project_name}")
            lines.append(f"📅 วันที่: {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}")
            lines.append("👷 ออกแบบโดย: ACA Mozart - AI Electrical Design System")
            lines.append("📐 มาตรฐาน: วสท. 2001-56 / NEC 2023 / IEC 60364")
            lines.append("")
            lines.append("─" * 65)
            
            # ═══════════════════════════════════════════
            # Section 0: Meter & Main Service
            # ═══════════════════════════════════════════
            if calculations:
                total_load = 0
                total_current = 0
                for panel_id, panel_calc in calculations.items():
                    if isinstance(panel_calc, dict):
                        total_load += panel_calc.get("total_va", 0)
                        total_current += panel_calc.get("demand_current", panel_calc.get("total_current", 0))
                
                if total_current > 0:
                    lines.append("")
                    lines.append("┌─────────────────────────────────────────────────────────────────┐")
                    lines.append("│  📟 SERVICE ENTRANCE (ระบบจ่ายไฟเข้าอาคาร)                       │")
                    lines.append("├─────────────────────────────────────────────────────────────────┤")
                    
                    # Main Breaker sizing: NEC 215.3 / วสท. = Load × 1.25 for continuous load
                    design_current = total_current * 1.25
                    
                    # Determine meter size (Thai standard: 5(15), 15(45), 30(100), 50(150))
                    # Main breaker must be >= design_current (with 1.25 factor)
                    if design_current <= 15:
                        meter_size = "5(15)A"
                        main_wire = "THW 4 mm²"
                        main_breaker = "16A 2P"
                    elif design_current <= 30:
                        meter_size = "15(45)A"
                        main_wire = "THW 6 mm²"
                        main_breaker = "32A 2P"
                    elif design_current <= 50:
                        meter_size = "30(100)A"
                        main_wire = "THW 10 mm²"
                        main_breaker = "50A 2P"
                    elif design_current <= 63:
                        meter_size = "30(100)A"
                        main_wire = "THW 16 mm²"
                        main_breaker = "63A 2P"
                    elif design_current <= 100:
                        meter_size = "30(100)A"
                        main_wire = "THW 25 mm²"
                        main_breaker = "100A 2P"
                    elif design_current <= 125:
                        meter_size = "50(150)A"
                        main_wire = "THW 35 mm²"
                        main_breaker = "125A 2P"
                    else:
                        meter_size = "50(150)A"
                        main_wire = "THW 50 mm²"
                        main_breaker = "150A 2P"
                    
                    # Ground wire (วสท.: same as phase for ≤16mm², 50% for larger)
                    ground_wire = main_wire.replace("THW", "THW-G")
                    
                    # [NEXIA] Default kA rating (calculated value)
                    ka_rating = "6kA"  # Default for normal distance
                    
                    # Check if injector has a recommendation (parse from warnings)
                    ka_injector_note = None
                    for warn in design_warnings:
                        if isinstance(warn, str) and "kA" in warn and "upgraded" in warn.lower():
                            # Extract kA value from warning like "[Safety] ... upgraded to 10kA ..."
                            import re
                            match = re.search(r'(\d+)kA', warn)
                            if match:
                                recommended_ka = match.group(1)
                                ka_injector_note = f"⚠️ Injector แนะนำ: ใช้ {recommended_ka}kA (ใกล้หม้อแปลง)"
                            break
                    
                    lines.append(f"│  มิเตอร์ไฟฟ้า      : {meter_size:<20} (การไฟฟ้าฯ)          │")
                    lines.append(f"│  สายเมน (L-N-G)    : {main_wire:<20} ท่อ EMT 1\"           │")
                    lines.append(f"│  Main Breaker      : {main_breaker} {ka_rating:<12} ตู้ MDB             │")
                    
                    # Show injector recommendation if different from default
                    if ka_injector_note:
                        lines.append(f"│  └─ {ka_injector_note:<55}│")
                    
                    lines.append(f"│  สายดิน            : {ground_wire:<20} (เขียว/เหลือง)      │")
                    lines.append("│  หลักดิน           : 5/8\" x 8 ฟุต           ค่าดิน ≤5Ω       │")
                    lines.append("└─────────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════
            # Section 1: Branch Circuits Table (Load Schedule Format)
            # ═══════════════════════════════════════════
            lines.append("")
            lines.append("┌─────────────────────────────────────────────────────────────────┐")
            lines.append("│  📋 LOAD SCHEDULE (ตารางโหลดวงจรย่อย)                            │")
            lines.append("├─────┬──────────────────────────┬────────┬───────┬───────────────┤")
            lines.append("│ Ckt │ รายละเอียด               │ โหลด(A)│ CB    │ สาย/ท่อ       │")
            lines.append("├─────┼──────────────────────────┼────────┼───────┼───────────────┤")
            
            # Room order priority for consistent display
            ROOM_ORDER = {
                "ห้องนั่งเล่น": 1, "ห้องครัว": 2, "ห้องน้ำ 1": 3, "ห้องน้ำ": 3,
                "ห้องเก็บของ": 4, "หน้าบ้าน": 5, "ข้างบ้าน": 6, "หลังบ้าน": 7,
                "โรงรถ": 8, "สวน": 9, "พื้นที่ส่วนกลาง": 10,
                "ห้องนอน 1": 11, "ห้องนอน 2": 12, "ห้องนอน 3": 13,
                "ห้องน้ำ 2": 14, "ห้องนอน": 15
            }
            
            def room_sort_key(item):
                room = item[0]
                return ROOM_ORDER.get(room, 99)
            
            circuit_num = 1
            for cid, b in breakers.items():
                if isinstance(b, dict) and b.get("circuit_info"):
                    name = b["circuit_info"].get("circuit_name", cid)
                    rating = b.get("breaker_rating", "?")
                    poles = b.get("poles", 1)
                    btype = b.get("breaker_type", "standard")
                    load_current = b.get("load_current", 0)
                    
                    # Calculate wire size from load current (วสท. standard)
                    if load_current <= 15:
                        wire_size = "2.5"
                    elif load_current <= 20:
                        wire_size = "4"
                    elif load_current <= 30:
                        wire_size = "6"
                    else:
                        wire_size = "10"
                    
                    # Determine icon based on circuit type
                    if "แอร์" in name or "AC" in name:
                        icon = "❄️"
                    elif "น้ำอุ่น" in name or "HEATER" in name:
                        icon = "🚿"
                    elif "ไฟ" in name:
                        icon = "💡"
                    elif "PUMP" in name or "ปั๊ม" in name:
                        icon = "💧"
                    else:
                        icon = "🔌"
                    
                    # Format breaker type: MCB or RCBO
                    if btype == "rcbo":
                        breaker_str = f"RCBO {rating}A/{poles}P"
                    else:
                        breaker_str = f"MCB {rating}A/{poles}P"
                    
                    # Display name - increase length to show full name
                    display_name = f"{icon} {name}"
                    if len(display_name) > 30:
                        display_name = display_name[:27] + "..."
                    
                    # Wire/conduit info
                    wire_conduit = f"{wire_size}mm²/½\""
                    
                    # Format as table row
                    lines.append(f"│ {circuit_num:>3} │ {display_name:<30} │ {load_current:>6.1f} │{breaker_str:>7}│ {wire_conduit:<13} │")
                    circuit_num += 1
                    
                    # Add sub-details for lighting circuits
                    if "ไฟแสงสว่าง" in name:
                        import re
                        floor_match = re.search(r'ชั้น\s*(\d+)', name)
                        if floor_match:
                            floor = int(floor_match.group(1))
                            if floor in lighting_by_floor:
                                sorted_rooms = sorted(lighting_by_floor[floor], key=room_sort_key)
                                total_watts = 0
                                total_fixtures = 0
                                for room, device, qty in sorted_rooms:
                                    watt_per_bulb = 20 if "20W" in device else 10
                                    total_w = watt_per_bulb * qty
                                    total_watts += total_w
                                    total_fixtures += qty
                                    # Fixed width: room details fit in column 2 (24 chars)
                                    # แสดงจำนวนดวงในแต่ละห้อง
                                    detail_text = f"  └─ {room}: {qty}ดวง"
                                    lines.append(f"│     │ {detail_text:<24}│        │       │               │")
                                total_amps = total_watts / 230
                                summary_text = f"  📊 รวม: {total_fixtures}ดวง ({total_amps:.1f}A)"
                                lines.append(f"│     │ {summary_text:<24}│        │       │               │")
                    
                    # Add sub-details for outlet circuits
                    # BUG FIX: Don't use outlets_by_floor (shows all floor outlets for EACH circuit)
                    # Instead, show only the summary from circuit notes (circuit already split correctly)
                    if "เต้ารับ" in name:
                        import re
                        floor_match = re.search(r'ชั้น\s*(\d+)', name)
                        circuit_num_match = re.search(r'\((\d+)\)', name)
                        
                        if floor_match:
                            floor = int(floor_match.group(1))
                            circuit_suffix = int(circuit_num_match.group(1)) if circuit_num_match else 1
                            
                            # Use circuit's notes for summary (already calculated correctly by circuit_grouper)
                            # circuit_notes removed - unused (SonarQube)
                            
                            # If we have outlets_by_floor, show them ONLY ONCE (first circuit for that floor)
                            # Track which floors we've displayed with a flag
                            # Track which floors we've displayed (local variable, not self attribute)
                            if floor in outlets_by_floor and floor not in outlets_displayed_floors:
                                sorted_rooms = sorted(outlets_by_floor[floor], key=room_sort_key)
                                total_outlets = 0
                                for room, qty in sorted_rooms:
                                    outlet_type = "คู่" if qty >= 2 else "เดี่ยว"
                                    total_outlets += qty
                                    detail_text = f"  └─ {room}: {outlet_type}×{qty}"
                                    lines.append(f"│     │ {detail_text:<24}│        │       │               │")
                                
                                # Calculate amps based on the CIRCUIT's load_current, not total floor
                                circuit_amps = load_current  # Already calculated with diversity factor
                                summary_text = f"  📊 รวม: {total_outlets}จุด ({circuit_amps:.1f}A)"
                                lines.append(f"│     │ {summary_text:<24}│        │       │               │")
                                
                                # Mark as displayed for first circuit only
                                outlets_displayed_floors.add(floor)
                            elif circuit_suffix > 1:
                                # For additional circuits (2, 3, ...), just show summary
                                summary_text = f"  📊 วงจรที่ {circuit_suffix} ({load_current:.1f}A)"
                                lines.append(f"│     │ {summary_text:<24}│        │       │               │")
            
            # Add spare circuits row
            lines.append(f"│ {circuit_num:>3} │ 🔲 Spare (สำรอง)          │    -   │ MCB 15A│ 2.5mm²/½\"     │")
            lines.append(f"│ {circuit_num+1:>3} │ 🔲 Spare (สำรอง)          │    -   │ MCB 15A│ 2.5mm²/½\"     │")
            lines.append("└─────┴──────────────────────────┴────────┴───────┴───────────────┘")
            
            # ═══════════════════════════════════════════
            # Section 2: Wire & Conduit Summary (Based on GROUPED CIRCUITS, not individual loads)
            # ═══════════════════════════════════════════
            lines.append("")
            lines.append("┌─────────────────────────────────────────────────────────────────┐")
            lines.append("│  📐 WIRE & CONDUIT SUMMARY (สรุปสายไฟและท่อร้อยสาย)             │")
            lines.append("├─────────────────────────────────────────────────────────────────┤")
            
            # Use breaker_selections (grouped circuits) instead of wire_sizing (individual loads)
            # This gives accurate circuit count
            wire_by_type = {
                "hvac": [],           # แอร์
                "water_heater": [],   # เครื่องทำน้ำอุ่น
                "lighting": [],       # ไฟแสงสว่าง
                "receptacle": [],     # เต้ารับ
                "pump": [],           # ปั๊มน้ำ
                "other": []           # อื่นๆ
            }
            
            for cid, breaker in breakers.items():
                if isinstance(breaker, dict) and breaker.get("circuit_info"):
                    info = breaker.get("circuit_info", {})
                    ctype = info.get("circuit_type", "other")
                    cname = info.get("circuit_name", "")
                    load_current = breaker.get("load_current", 0)
                    
                    # Detect circuit type from name if not set
                    if "AC" in cname or "แอร์" in cname:
                        ctype = "hvac"
                    elif "HEATER" in cname or "น้ำอุ่น" in cname:
                        ctype = "water_heater"
                    elif "ไฟ" in cname or "แสงสว่าง" in cname:
                        ctype = "lighting"
                    elif "เต้ารับ" in cname:
                        ctype = "receptacle"
                    elif "PUMP" in cname or "ปั๊ม" in cname:
                        ctype = "pump"
                    
                    # Determine wire size from current (วสท. standard)
                    # I < 15A → 2.5mm² (14 AWG), I < 20A → 4mm² (12 AWG), I < 30A → 6mm² (10 AWG)
                    if load_current <= 15:
                        wire_size = "2.5mm² (14 AWG)"
                        ground_size = "2.5mm²"
                    elif load_current <= 20:
                        wire_size = "4mm² (12 AWG)"
                        ground_size = "2.5mm²"
                    elif load_current <= 30:
                        wire_size = "6mm² (10 AWG)"
                        ground_size = "4mm²"
                    else:
                        wire_size = "10mm² (8 AWG)"
                        ground_size = "6mm²"
                    
                    if ctype in wire_by_type:
                        wire_by_type[ctype].append((wire_size, ground_size, load_current))
                    else:
                        wire_by_type["other"].append((wire_size, ground_size, load_current))
            
            # Display by circuit type with Thai names
            type_names = {
                "hvac": ("❄️", "แอร์"),
                "water_heater": ("🚿", "น้ำอุ่น"),
                "lighting": ("💡", "แสงสว่าง"),
                "receptacle": ("🔌", "เต้ารับ"),
                "pump": ("💧", "ปั๊มน้ำ"),
                "other": ("⚡", "อื่นๆ")
            }
            
            for ctype, circuits in wire_by_type.items():
                if circuits:
                    # Group same wire sizes
                    size_groups = {}
                    for wire_size, ground_size, load_current in circuits:
                        if wire_size not in size_groups:
                            size_groups[wire_size] = {"count": 0, "ground": ground_size}
                        size_groups[wire_size]["count"] += 1
                    
                    icon, label = type_names.get(ctype, ("⚡", "อื่นๆ"))
                    for size, info in size_groups.items():
                        lines.append(f"│  {icon} {label:<10}: {size:<18} × {info['count']} วงจร (G: {info['ground']}) │")
            
            lines.append("└─────────────────────────────────────────────────────────────────┘")
            
            if conduit_sizing:
                # ท่อร้อยสาย
                pass  # Already shown in wire summary
            
            # ═══════════════════════════════════════════
            # Section 3: Load Summary (Professional Format)
            # ═══════════════════════════════════════════
            lines.append("")
            lines.append("┌─────────────────────────────────────────────────────────────────┐")
            lines.append("│  ⚡ LOAD SUMMARY (สรุปโหลด)                                      │")
            lines.append("├─────────────────────────────────────────────────────────────────┤")
            
            if calculations:
                # MCP returns calculations per panel: {"MDP": {"total_va": 5700, "total_current": 29.41}}
                # Sum up all panels
                total_load = 0
                total_current = 0
                for panel_id, panel_calc in calculations.items():
                    if isinstance(panel_calc, dict):
                        total_load += panel_calc.get("total_va", 0)
                        total_current += panel_calc.get("demand_current", panel_calc.get("total_current", 0))
                
                if total_load:
                    lines.append(f"│  โหลดรวม (Connected Load)  : {total_load:>10,.0f} W ({total_load/1000:.1f} kW)          │")
                    lines.append(f"│  กระแสโหลด (Demand Current): {total_current:>10.1f} A                         │")
                    design_current = total_current * 1.25
                    lines.append(f"│  Design Current (×1.25)    : {design_current:>10.1f} A                         │")
                    # What-If: หากไม่ใส่เต้ารับในห้องน้ำ (ประหยัด per วสท. 2564: 180VA/outlet)
                    # ห้องน้ำมี 1 outlet = 180 VA (ไม่ใช่ 1200W!)
                    bathroom_outlet_count = 1  # ห้องน้ำปกติมี 1 เต้ารับ
                    bathroom_load_w = bathroom_outlet_count * 180  # 180 VA per outlet per วสท. 2564
                    load_without_bathroom = total_load - bathroom_load_w
                    current_without_bathroom = load_without_bathroom / 230
                    lines.append("├─────────────────────────────────────────────────────────────────┤")
                    lines.append("│  💡 หากไม่ใส่เต้ารับในห้องน้ำ:                                  │")
                    lines.append(f"│     โหลดรวม: {load_without_bathroom:>6,.0f} W (-{bathroom_load_w}W)                                │")
                    lines.append(f"│     กระแส: {current_without_bathroom:>5.1f}A (-{bathroom_load_w/230:.1f}A)                                         │")

            
            lines.append("├─────────────────────────────────────────────────────────────────┤")

            
            if compliance:
                is_compliant = compliance.get("compliant", False)
                nec_version = compliance.get("nec_version", "2023")
                if is_compliant:
                    lines.append(f"│  ✅ ผ่านมาตรฐาน NEC {nec_version} + วสท. 2001-56                          │")
                else:
                    lines.append(f"│  ❌ ไม่ผ่านมาตรฐาน NEC {nec_version}                                       │")
            
            lines.append("└─────────────────────────────────────────────────────────────────┘")
            
            # Show warnings
            # [NEXIA] Combine compliance warnings with injector warnings
            all_warnings = []
            if compliance:
                all_warnings.extend(compliance.get("warnings", []))
            if design_warnings:
                all_warnings.extend(design_warnings)
            
            if all_warnings:
                lines.append("")
                lines.append("📌 หมายเหตุ:")
                
                # [NEXIA] Show injector-specific warnings first (they're more important)
                injector_shown = set()
                for warn in design_warnings:
                    if isinstance(warn, str) and "[Safety]" in warn:
                        # N-G Link or kA warning
                        if "SUB-PANEL" in warn:
                            msg = "🚨 ตู้ย่อย: ห้ามต่อสาย N-G (Neutral-Ground) ที่ตู้นี้!"
                        elif "kA" in warn:
                            msg = f"⚡ {warn}"
                        else:
                            msg = f"⚠️ {warn}"
                        if msg not in injector_shown:
                            lines.append(f"• {msg}")
                            injector_shown.add(msg)
                
                # Show derating info if applied
                installation_area = site_context.get("installation_area", "")
                if installation_area and installation_area != "indoor":
                    area_names = {"outdoor": "กลางแดด", "high_temp": "ใต้หลังคาร้อน", "underground": "ใต้ดิน"}
                    area_th = area_names.get(installation_area, installation_area)
                    lines.append(f"• 🌡️ Derating Factor ใช้งาน: พื้นที่ {area_th} (สายไฟขนาดใหญ่ขึ้น)")
            
            # Now show compliance warnings (append to existing section, no new header)
            if compliance:
                warnings = compliance.get("warnings", [])
                if warnings:
                    # If no injector warnings were shown, add header now
                    if not all_warnings:
                        lines.append("")
                        lines.append("📌 หมายเหตุ:")
                    
                    # Translate common warnings to Thai
                    warning_translations = {
                        "typically requires dedicated circuit": "ควรแยกวงจรเฉพาะ",
                        "HVAC load": "โหลดแอร์",
                        "may require GFCI protection": "ควรติดตั้ง RCBO 30mA",
                        "may require AFCI protection": "ควรติดตั้ง AFCI",
                        "in dwelling units": "ในบ้านพักอาศัย",
                        "based on location": "ตามตำแหน่งติดตั้ง",
                        "Panel": "ตู้ไฟ",
                        "has no loads assigned": "ยังไม่มีโหลดกำหนด",
                        "Load": "โหลด"
                    }
                    
                    shown_warnings = set()  # Avoid duplicates
                    for warn in warnings[:5]:  # Show up to 5 warnings
                        if isinstance(warn, dict):
                            msg = warn.get("message", str(warn))
                        else:
                            msg = str(warn)
                        
                        # Translate to Thai
                        thai_msg = msg
                        for eng, thai in warning_translations.items():
                            thai_msg = thai_msg.replace(eng, thai)
                        
                        # Simplify AC warnings (don't repeat for each AC)
                        if "แอร์" in thai_msg and "แยกวงจร" in thai_msg:
                            simplified = "❄️ แอร์ทุกตัวควรแยกวงจรเฉพาะ + เบรกเกอร์ 2P"
                            if simplified not in shown_warnings:
                                lines.append(f"      • {simplified}")
                                shown_warnings.add(simplified)
                        elif "RCBO" in thai_msg or "GFCI" in thai_msg:
                            simplified = "🚿 เครื่องทำน้ำอุ่นต้องใช้ RCBO 30mA ป้องกันไฟดูด"
                            if simplified not in shown_warnings:
                                lines.append(f"      • {simplified}")
                                shown_warnings.add(simplified)
                        elif "AFCI" in thai_msg:
                            simplified = "🔌 เต้ารับในห้องนอนควรติดตั้ง AFCI ป้องกันไฟลัดวงจร (NEC 210.12)"
                            if simplified not in shown_warnings:
                                lines.append(f"      • {simplified}")
                                shown_warnings.add(simplified)
                        elif thai_msg not in shown_warnings:
                            lines.append(f"   • {thai_msg}")
                            shown_warnings.add(thai_msg)
            
            # ═══════════════════════════════════════════
            # Summary Footer with MCB Table (Bill of Materials)
            # ═══════════════════════════════════════════
            
            # Count MCB by size and type
            mcb_summary = {}  # (rating, poles, type) -> count
            for cid, b in breakers.items():
                if isinstance(b, dict) and b.get("circuit_info"):
                    rating = b.get("breaker_rating", 15)
                    poles = b.get("poles", 1)
                    btype = b.get("breaker_type", "standard")
                    key = (rating, poles, btype)
                    mcb_summary[key] = mcb_summary.get(key, 0) + 1
            
            total_circuits = sum(mcb_summary.values())
            spare_count = max(2, int(total_circuits * 0.2))
            total_mcb = total_circuits + spare_count
            
            lines.append("")
            lines.append("┌─────────────────────────────────────────────────────────────────┐")
            lines.append("│  📦 BILL OF MATERIALS (รายการอุปกรณ์)                            │")
            lines.append("├─────────────────────────────────────────────────────────────────┤")
            
            # Sort by rating then poles
            for (rating, poles, btype), count in sorted(mcb_summary.items()):
                if btype == "rcbo":
                    type_label = "RCBO 30mA"
                elif btype == "main":
                    type_label = "Main MCB"
                else:
                    type_label = "MCB"
                lines.append(f"│  {type_label} {rating}A/{poles}P                                : {count:>3} ตัว     │")
            
            lines.append(f"│  MCB Spare 15A/1P (สำรอง)                            : {spare_count:>3} ตัว     │")
            lines.append("├─────────────────────────────────────────────────────────────────┤")
            lines.append(f"│  รวม MCB ทั้งหมด: {total_mcb} ตัว ({total_circuits} ใช้งาน + {spare_count} สำรอง)              │")
            lines.append("└─────────────────────────────────────────────────────────────────┘")
            
            # Footer
            lines.append("")
            lines.append("═" * 65)
            lines.append("📋 เอกสารนี้จัดทำโดย ACA Mozart - AI Electrical Design System")
            lines.append("📞 ติดต่อวิศวกรผู้ออกแบบก่อนดำเนินการติดตั้ง")
            lines.append("═" * 65)
            
        else:
            # English version (simplified)
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
        # [CP4] Checkpoint: Conversion Input
        input_rooms = len(extracted.get("rooms", []))
        input_loads = len(extracted.get("loads", []))
        logger.info(f"[CP4-IN] Converting: {input_rooms} rooms, {input_loads} loads from LLM")
        
        # Get number of floors
        num_floors = extracted.get("num_floors", 1)
        
        # Build rooms with floor info
        rooms = []
        room_names = set()
        room_floor_map = {}  # Track which floor each room is on
        
        for r in extracted.get("rooms", []):
            name = r.get("name", "ห้อง")
            floor = r.get("floor") or 1  # Handle None from LLM
            rooms.append(RoomInput(
                name=name,
                type=r.get("type", "bedroom"),
                area_sqm=r.get("area_sqm"),  # Pass area if LLM extracted it
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
                quantity=l.get("quantity") or 1,  # Handle None from LLM
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
        
        # 4. Auto-fill Water Heater (ถ้าบอกว่ามีน้ำอุ่นแต่ LLM ไม่ได้ extract ครบ)
        # ตรวจสอบว่ามี heater ในห้องน้ำหรือยัง
        has_heater = any(
            "HEATER" in l.get("device", "") 
            for l in extracted.get("loads", [])
        )
        bathroom_rooms = [r for r in rooms if r.type == "bathroom"]
        if not has_heater and len(bathroom_rooms) > 0:
            # เช็คว่า query มีคำว่าน้ำอุ่นหรือไม่
            original_query = extracted.get("original_query", "").lower()
            if any(kw in original_query for kw in ["น้ำอุ่น", "น้ำร้อน", "heater", "ฮีทเตอร์"]):
                for br in bathroom_rooms:
                    loads.append(LoadInput(
                        room_name=br.name,
                        device="HEATER-4500W",
                        quantity=1,
                        floor=br.floor if hasattr(br, 'floor') else 1
                    ))
                    logger.info(f"🔧 Auto-added: น้ำอุ่น 4500W ใน {br.name}")
        
        # 5. Auto-fill Exterior Lighting (ถ้าบอกว่ามีโคมไฟหน้าบ้าน)
        exterior_rooms = [r for r in rooms if r.type == "exterior"]
        has_exterior_light = any(
            "LIGHT" in l.get("device", "") and l.get("room_name", "") in [r.name for r in exterior_rooms]
            for l in extracted.get("loads", [])
        )
        if not has_exterior_light and len(exterior_rooms) > 0:
            for er in exterior_rooms:
                loads.append(LoadInput(
                    room_name=er.name,
                    device="LIGHT-LED-10W",
                    quantity=2,  # 2 ดวงสำหรับหน้าบ้าน
                    floor=1
                ))
                logger.info(f"🔧 Auto-added: ไฟ LED หน้าบ้าน 10W x 2 ใน {er.name}")
        
        # [CP4] Checkpoint: Conversion Output
        logger.info(f"[CP4-OUT] Result: {len(rooms)} rooms, {len(loads)} loads ready for MCP")
        
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
            # Note: device codes are already normalized by this point
            # No transformation needed for LIGHT-LED*, SOCKET-16A, PUMP-750W
            
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
        
        # [CP6] Checkpoint: Build Design Response Entry
        rooms_count = len(req.rooms) if req.rooms else 0
        loads_count = len(req.loads) if req.loads else 0
        site_ctx = getattr(req, 'site_context', None)
        logger.info(f"[CP6] Building design: {rooms_count} rooms, {loads_count} loads")
        logger.info(f"[CP6] site_context: {site_ctx}")
        
        try:
            # 🆕 VALIDATION: Check if rooms/loads are empty before proceeding
            # This prevents sending empty data to MCP which results in only spare circuits
            if not req.rooms or len(req.rooms) == 0:
                logger.warning("❌ Empty rooms in design request - LLM extraction may have failed")
                missing_info = []
                if not req.rooms:
                    missing_info.append("ห้อง (rooms)")
                if not req.loads:
                    missing_info.append("อุปกรณ์ไฟฟ้า (loads)")
                
                return StandardResponse(
                    answer=f"""⚠️ ข้อมูลไม่ครบถ้วน - ไม่สามารถคำนวณได้

ข้อมูลที่ขาดหายไป: {', '.join(missing_info)}

กรุณาระบุข้อมูลให้ชัดเจน เช่น:
• ห้องแต่ละห้องมีอะไรบ้าง (ห้องนอน, ห้องครัว, ห้องน้ำ)
• อุปกรณ์ไฟฟ้าในแต่ละห้อง (แอร์, น้ำอุ่น, เตา, เต้ารับ)
• จำนวนชิ้นของอุปกรณ์แต่ละชนิด

ตัวอย่าง: "ออกแบบบ้าน 2 ชั้น มีห้องนอน 3 ห้อง แต่ละห้องมีแอร์ 1 ตัว เต้ารับ 3 จุด ห้องครัวมีเตาไฟฟ้า 1 เครื่อง"
""",
                    sources=[],
                    confidence="Low",
                    grounding_status="INSUFFICIENT_DATA",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=[],
                        retrieval_group="mcp"
                    )
                )
            
            if not req.loads or len(req.loads) == 0:
                logger.warning("❌ Empty loads in design request - LLM extraction may have failed")
                return StandardResponse(
                    answer=f"""⚠️ ไม่พบอุปกรณ์ไฟฟ้า - ไม่สามารถคำนวณได้

พบห้อง {len(req.rooms)} ห้อง แต่ไม่มีอุปกรณ์ไฟฟ้า

กรุณาระบุอุปกรณ์ไฟฟ้าในแต่ละห้อง เช่น:
• จำนวนหลอดไฟ LED
• จำนวนเต้ารับ (คู่/เดี่ยว)
• แอร์ (ถ้ามี) พร้อม BTU
• เครื่องทำน้ำอุ่น (ถ้ามี) พร้อมวัตต์
• เตาไฟฟ้า, ไมโครเวฟ, ตู้เย็น ฯลฯ

ตัวอย่าง: "ห้องนอนมีแอร์ 12000BTU 1 ตัว เต้ารับคู่ 3 จุด ไฟ LED 3 ดวง"
""",
                    sources=[],
                    confidence="Low",
                    grounding_status="INSUFFICIENT_DATA",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=[],
                        retrieval_group="mcp"
                    )
                )
            
            # 🆕 VALIDATION: Check if site_context is missing
            # This ensures Context Injectors (Derating, kA, N-G Link) work properly
            if not req.site_context:
                logger.warning("⚠️ Missing site_context in design request")
                return StandardResponse(
                    answer="""⚠️ กรุณาตอบคำถามเกี่ยวกับสถานที่ติดตั้ง

เพื่อความปลอดภัยในการคำนวณ กรุณาระบุข้อมูลต่อไปนี้:

1️⃣ **ระยะห่างจากหม้อแปลงไฟฟ้า**
   • น้อยกว่า 50 เมตร (ต้องใช้เบรกเกอร์ 10kA)
   • 50-100 เมตร
   • มากกว่า 100 เมตร

2️⃣ **พื้นที่ติดตั้งสายไฟ**
   • ภายในอาคาร (ปกติ)
   • อุณหภูมิสูง/ใต้หลังคา (Derate 20%)
   • กลางแจ้ง/ฝังดิน (Derate 30%)

3️⃣ **ประเภทตู้ไฟ**
   • ตู้เมน (Main Panel) - มี N-G Link
   • ตู้ย่อย (Sub Panel) - ห้าม N-G Link

ตัวอย่าง: "บ้าน 2 ชั้น ห้างหม้อแปลง 80 เมตร ติดตั้งภายในบ้าน เป็นตู้เมน"
""",
                    sources=[],
                    confidence="Low",
                    grounding_status="NEEDS_SITE_CONTEXT",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=[],
                        retrieval_group="mcp"
                    )
                )
            
            # Direct conversion to ProjectInputSpec (no LLM, preserves floor)
            project_input = self._convert_req_to_spec(req)
            logger.info(f"📦 Direct conversion: {len(project_input.rooms)} rooms, {len(project_input.loads)} loads")
            
            # Log floor info
            floor_counts = {}
            for load in project_input.loads:
                f = load.floor
                floor_counts[f] = floor_counts.get(f, 0) + 1
            logger.info(f"📊 Loads by floor: {floor_counts}")
            
            # Convert to MCP format (🆕 now with site_context!)
            adapter = McpAdapter()
            mcp_request = adapter.convert(project_input, req.site_context)
            
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
                # Format using new Card-style Markdown formatter
                result = mcp_response.to_dict()
                
                # Use new formatter (Card-style, Legend at top, critical warnings)
                formatted_text = format_design_report(result)
                
                return StandardResponse(
                    answer=formatted_text,
                    sources=[SourceRef(
                        file="MCP Core Calculation",
                        section="design_result",
                        score=1.0,
                        content="คำนวณตามมาตรฐาน วสท."
                    )],
                    confidence="High",
                    grounding_status="CALCULATED",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=["mcp_calculation"],
                        retrieval_group="mcp",
                        autolisp_code=mcp_response.autolisp_code,
                        readable_report=formatted_text,  # Use new formatter output
                        standards_markdown=mcp_response.standards_markdown
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
                loads = self._extract_loads_from_text(req.query)
                
                # 🆕 FIX: Proper validation - check for actual data, not just truthy dict
                has_rooms = loads and loads.get("rooms") and len(loads.get("rooms", [])) > 0
                has_loads = loads and loads.get("loads") and len(loads.get("loads", [])) > 0
                has_error = loads and "error" in loads
                
                # 🆕 ASK-BACK: ถ้าได้ข้อมูลไม่ครบ ให้ถามกลับแทนการ auto-fill
                if loads and not has_error:
                    if has_rooms and not has_loads:
                        # มีห้อง แต่ไม่มีอุปกรณ์ → ถามหาอุปกรณ์
                        room_names = [r.get("name", "?") for r in loads.get("rooms", [])]
                        logger.info(f"[ASK-BACK] Has rooms ({room_names}) but no loads - asking for loads")
                        return StandardResponse(
                            answer=f"""✅ ได้รับข้อมูลห้องแล้ว: {', '.join(room_names)}

❓ **กรุณาระบุอุปกรณ์ไฟฟ้าในแต่ละห้อง:**

ตัวอย่าง:
• "ห้องนั่งเล่น มีเต้ารับคู่ 6 จุด, ไฟ LED 20W 4 ดวง"
• "ห้องนอนทุกห้องมีแอร์ 12000BTU"
• "ห้องน้ำมีเครื่องทำน้ำอุ่น 4500W"
• "ห้องครัวมีเตาไฟฟ้า 3000W, ตู้เย็น, ไมโครเวฟ"
""",
                            sources=[],
                            confidence="Medium",
                            grounding_status="PARTIAL_DATA_NEED_LOADS",
                            metadata=AnswerMetadata(
                                llm_model=settings.MODEL_NAME_ANSWER,
                                retrieved_docs=[],
                                retrieval_group="mcp"
                            )
                        )
                    
                    if has_loads and not has_rooms:
                        # มีอุปกรณ์ แต่ไม่มีห้อง → ถามหาห้อง
                        load_devices = [l.get("device", "?") for l in loads.get("loads", [])[:5]]
                        logger.info(f"[ASK-BACK] Has loads ({load_devices}) but no rooms - asking for rooms")
                        return StandardResponse(
                            answer=f"""✅ ได้รับข้อมูลอุปกรณ์แล้ว: {', '.join(load_devices)}...

❓ **กรุณาระบุห้องในบ้าน:**

ตัวอย่าง:
• "บ้าน 2 ชั้น"
• "ชั้น 1 มี ห้องนั่งเล่น, ห้องครัว, ห้องน้ำ"
• "ชั้น 2 มี ห้องนอน 3 ห้อง, ห้องน้ำ"
""",
                            sources=[],
                            confidence="Medium",
                            grounding_status="PARTIAL_DATA_NEED_ROOMS",
                            metadata=AnswerMetadata(
                                llm_model=settings.MODEL_NAME_ANSWER,
                                retrieved_docs=[],
                                retrieval_group="mcp"
                            )
                        )
                
                # ผ่านได้เมื่อมีทั้ง rooms และ loads
                if has_rooms and has_loads and not has_error:
                    logger.info(f"📦 Extracted: {json.dumps(loads.get('rooms', []), ensure_ascii=False)[:200]}")
                    
                    # Convert to structured ProjectRequirements
                    project_req = self._convert_to_project_requirements(loads)
                    
                    # Debug: log floors
                    floor_info = {r.name: r.floor for r in project_req.rooms}
                    logger.info(f"🏠 Room floors: {floor_info}")
                    
                    # 🆕 FIX: Extract site_context from user's query
                    site_ctx = extract_site_context_from_text(req.query)
                    logger.info(f"🔍 Extracted site_context: {site_ctx}")
                    
                    # 🆕 FIX: Check if site_context is complete
                    is_complete, missing_fields = is_site_context_complete(site_ctx)
                    
                    if not is_complete:
                        # Return targeted prompt for missing fields
                        logger.warning(f"⚠️ Missing site_context fields: {missing_fields}")
                        prompt = build_missing_field_prompt(missing_fields)
                        return StandardResponse(
                            answer=prompt,
                            sources=[],
                            confidence="Low",
                            grounding_status="NEEDS_SITE_CONTEXT",
                            metadata=AnswerMetadata(
                                llm_model=settings.MODEL_NAME_ANSWER,
                                retrieved_docs=[],
                                retrieval_group="mcp"
                            )
                        )
                    
                    # Set site_context on project_req before MCP call
                    from app.models import SiteContext
                    project_req.site_context = SiteContext(
                        distance_to_transformer=site_ctx.get("distance_to_transformer", "more_than_100m"),
                        installation_area=site_ctx.get("installation_area", "indoor"),
                        panel_type=site_ctx.get("panel_type", "main"),
                        conduit_grouping=site_ctx.get("conduit_grouping", "1")
                    )
                    logger.info(f"✅ site_context set: {project_req.site_context}")
                    
                    # Chain to MCP Core for calculations
                    result = await self._build_design_response(project_req, req.language)
                    
                    logger.info("✅ Design response built successfully via NLP→MCP chain")
                    return result
                else:
                    # 🆕 FIX: Return helpful error instead of falling back to Q&A
                    # Q&A fallback caused empty Load Schedule (only spare circuits)
                    error_detail = loads.get("error", "Unknown") if loads else "No response"
                    rooms_found = len(loads.get("rooms", [])) if loads else 0
                    loads_found = len(loads.get("loads", [])) if loads else 0
                    logger.warning(f"⚠️ Extraction failed - error: {error_detail}, rooms: {rooms_found}, loads: {loads_found}")
                    return StandardResponse(
                        answer=f"""⚠️ ไม่สามารถดึงข้อมูลจากคำขอได้

🔍 Debug: พบ {rooms_found} ห้อง, {loads_found} โหลด, error: {error_detail}

ระบบตรวจพบว่าคุณต้องการออกแบบระบบไฟฟ้า แต่ไม่สามารถดึงรายละเอียดห้องและอุปกรณ์ได้

กรุณาระบุข้อมูลให้ชัดเจนขึ้น เช่น:
• "ออกแบบบ้าน 2 ชั้น"
• "ชั้น 1: ห้องนั่งเล่น 30 ตร.ม., ห้องครัว 15 ตร.ม., ห้องน้ำ 1 ห้อง"
• "ห้องนั่งเล่น มีเต้ารับคู่ 6 จุด, ไฟ LED 20W 4 ดวง"
• "ห้องครัวมีเตาไฟฟ้า 3000W, ไมโครเวฟ 1500W, ตู้เย็น 300W"
• "ห้องน้ำมีเครื่องทำน้ำอุ่น 4500W"

หรือใช้รูปแบบ: "บ้าน 2 ชั้น มีห้องนอน 3 ห้อง ทุกห้องมีแอร์ 12000BTU น้ำอุ่น 2 ตัว"
""",
                        sources=[],
                        confidence="Low",
                        grounding_status="EXTRACTION_FAILED",
                        metadata=AnswerMetadata(
                            llm_model=settings.MODEL_NAME_ANSWER,
                            retrieved_docs=[],
                            retrieval_group="mcp"
                        )
                    )
                    
            except Exception as e:
                logger.error(f"❌ Design chain failed: {e}")
                # 🆕 FIX: Return error message instead of silent fallback
                return StandardResponse(
                    answer=f"""❌ เกิดข้อผิดพลาดในการประมวลผล: {str(e)}

กรุณาลองใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบ""",
                    sources=[],
                    confidence="Low",
                    grounding_status="PROCESSING_ERROR",
                    metadata=AnswerMetadata(
                        llm_model=settings.MODEL_NAME_ANSWER,
                        retrieved_docs=[],
                        retrieval_group="mcp"
                    )
                )
        
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
    
    def _generate_clarifying_questions(
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
            questions = self._generate_clarifying_questions(req, missing_critical)
            
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
        plan_text = self._generate_spec_plan(req, context_str, examples_str)
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
    
    def retrieve_raw(self, req: RawRetrieveRequest) -> List[Dict[str, Any]]:
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
    
    def _generate_spec_plan(
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
        llm_issues = self._llm_semantic_check(spec, original_req)
        issues.extend(llm_issues)
        
        # Classify severity
        if not issues:
            return "PASS", []
        elif len(issues) <= 2 and not any("Invalid" in i for i in issues):
            return "WARN", issues
        else:
            return "FAIL", issues
    
    def _llm_semantic_check(
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
