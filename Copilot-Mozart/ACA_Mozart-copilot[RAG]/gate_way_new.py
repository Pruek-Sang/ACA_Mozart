# -*- coding: utf-8 -*-
"""
Gateway - The Divine Router
Routes user requests between MOZART (RAG/MCP) and AMADEUS (AGI/Chat)

Architecture:
    User → Gateway → [MOZART] → RAG Service → MCP Core → AutoLISP/DXF
                  → [AMADEUS] → AGI Service (general chat)

Philosophy: Intelligent Intent Classification
- LLM-based routing (understands context, slang, mixed languages)
- Regex fallback for reliability
- Dialogue state management for multi-turn conversations
"""

import os
import re
import time
import logging
import uuid
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

# =============================================================================
# Configuration
# =============================================================================

logger = logging.getLogger("Aura.Gateway")

# Service endpoints (configurable via environment)
LLM_ROUTER_ENDPOINT = os.getenv("LLM_ROUTER_ENDPOINT", "http://localhost:11434/api/generate")
LLM_ROUTER_MODEL = os.getenv("LLM_ROUTER_MODEL", "qwen2.5:0.5b")
DIALOGUE_MANAGER_ENDPOINT = os.getenv("DIALOGUE_MANAGER_ENDPOINT", "http://localhost:8082")
MOZART_ENDPOINT = os.getenv("MOZART_ENDPOINT", "http://localhost:8080")  # RAG Service
AMADEUS_ENDPOINT = os.getenv("AMADEUS_ENDPOINT", "http://localhost:8081")  # AGI Service


# =============================================================================
# Models
# =============================================================================

class IntentMode(str, Enum):
    """Routing destination modes"""
    MOZART = "MOZART"    # RAG/Engineering - technical questions, MCP specs
    AMADEUS = "AMADEUS"  # AGI/Chat - general conversation, philosophy


class RoutingDecision(BaseModel):
    """Result of intent classification"""
    mode: IntentMode = Field(..., description="Routing destination")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    reasoning: str = Field(..., description="Why this routing was chosen")
    keywords: List[str] = Field(default_factory=list, description="Matched keywords")


class GatewayRequest(BaseModel):
    """Incoming request to gateway"""
    input: str = Field(..., description="User input text")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Dialogue session ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class GatewayResponse(BaseModel):
    """Response from gateway"""
    mode: IntentMode = Field(..., description="Which service handled this")
    data: Dict[str, Any] = Field(..., description="Response data from service")
    processing_time_ms: int = Field(..., description="Total processing time")
    trace_id: str = Field(..., description="Request trace ID")
    routing_decision: RoutingDecision = Field(..., description="How routing was decided")


# =============================================================================
# Intent Router
# =============================================================================

# Technical keywords for MOZART routing (regex fallback)
MOZART_KEYWORDS = [
    # Thai
    r"ออกแบบ.*ไฟ", r"คำนวณ", r"voltage", r"แรงดัน", r"กระแส", r"โหลด",
    r"วงจร", r"circuit", r"สาย", r"cable", r"เบรกเกอร์", r"breaker",
    r"ขนาด", r"sizing", r"มาตรฐาน", r"standard", r"วสท", r"ห้อง.*ไฟ",
    r"autocad", r"autolisp", r"dxf", r"mcp", r"spec",
    # English
    r"electrical", r"design", r"wire", r"panel", r"load", r"power",
    r"watt", r"amp", r"volt", r"ground", r"earthing"
]

# Compiled regex patterns
_MOZART_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in MOZART_KEYWORDS]


class LLMRouter:
    """
    LLM-based intent router with regex fallback
    
    WHY LLM over pure regex:
    - Understands context from dialogue history
    - Handles misspellings, slang, mixed Thai/English
    - Higher accuracy for ambiguous cases
    
    WHY regex fallback:
    - Reliability when LLM is unavailable
    - Faster response for obvious cases
    - No external dependency required
    """
    
    ROUTER_PROMPT = """You are an intent classifier for an engineering AI system.

The system has TWO modes:
1. MOZART (RAG/Engineering): Technical questions about electrical design, calculations, standards, AutoCAD, specifications
2. AMADEUS (AGI/Chat): General conversation, philosophy, ethics, jokes, non-technical questions

Examples:
User: "ออกแบบไฟห้องครัวให้หน่อย" → MOZART
User: "คำนวณ voltage drop ให้ที" → MOZART
User: "สร้าง spec บ้านให้หน่อย" → MOZART
User: "คุณคิดยังไงกับความหมายของชีวิต" → AMADEUS
User: "เล่าเรื่องตลกหน่อย" → AMADEUS
User: "สวัสดี เป็นอย่างไรบ้าง" → AMADEUS

User input: "{user_input}"

Respond ONLY with: MOZART or AMADEUS"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def route(
        self,
        user_input: str,
        dialogue_history: Optional[List[Dict]] = None
    ) -> RoutingDecision:
        """
        Route user input to appropriate service
        
        Strategy:
        1. Try LLM-based classification
        2. If LLM fails, fallback to regex
        3. Default to AMADEUS if uncertain
        """
        # Try LLM first
        try:
            return await self._route_with_llm(user_input, dialogue_history)
        except Exception as e:
            logger.warning(f"LLM router failed: {e}, using regex fallback")
            return self._route_with_regex(user_input)
    
    async def _route_with_llm(
        self,
        user_input: str,
        dialogue_history: Optional[List[Dict]] = None
    ) -> RoutingDecision:
        """Route using LLM classification"""
        prompt = self.ROUTER_PROMPT.format(user_input=user_input)
        
        # Add dialogue context if available
        if dialogue_history:
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in dialogue_history[-3:]
            ])
            prompt = f"Previous context:\n{context}\n\n{prompt}"
        
        response = await self.client.post(
            LLM_ROUTER_ENDPOINT,
            json={
                "model": LLM_ROUTER_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        
        result = response.json()
        answer = result.get("response", "").strip().upper()
        
        if "MOZART" in answer:
            return RoutingDecision(
                mode=IntentMode.MOZART,
                confidence=0.90,
                reasoning="LLM detected technical/engineering intent",
                keywords=["llm_classified"]
            )
        else:
            return RoutingDecision(
                mode=IntentMode.AMADEUS,
                confidence=0.90,
                reasoning="LLM detected conversational intent",
                keywords=["llm_classified"]
            )
    
    def _route_with_regex(self, user_input: str) -> RoutingDecision:
        """Fallback routing using regex patterns"""
        matched_keywords = []
        
        for pattern in _MOZART_PATTERNS:
            if pattern.search(user_input):
                matched_keywords.append(pattern.pattern)
        
        if matched_keywords:
            return RoutingDecision(
                mode=IntentMode.MOZART,
                confidence=0.7 + (0.05 * min(len(matched_keywords), 6)),
                reasoning=f"Regex matched {len(matched_keywords)} technical keywords",
                keywords=matched_keywords[:5]
            )
        else:
            return RoutingDecision(
                mode=IntentMode.AMADEUS,
                confidence=0.6,
                reasoning="No technical keywords found, routing to general chat",
                keywords=[]
            )


# =============================================================================
# Service Proxy
# =============================================================================

class ServiceProxy:
    """Proxy for calling downstream services"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        await self.client.aclose()
    
    def _extract_site_context(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract site_context from natural language Thai text.
        
        Returns dict with fields if detected, None if nothing found.
        """
        import re
        
        context = {}
        
        # 1. Distance to transformer (ระยะหม้อแปลง)
        if re.search(r'(?:หม้อแปลง|transformer).*(?:น้อยกว่า|ใกล้|<)\s*50', text):
            context['distance_to_transformer'] = 'less_than_50m'
        elif re.search(r'(?:หม้อแปลง|transformer).*(?:50|ห้าสิบ).*(?:100|ร้อย)', text):
            context['distance_to_transformer'] = '50_100m'
        elif re.search(r'(?:หม้อแปลง|transformer).*(?:มากกว่า|ไกล|>)\s*100', text):
            context['distance_to_transformer'] = 'more_than_100m'
        elif re.search(r'\d+\s*(?:เมตร|m)', text):
            # Try to extract number
            match = re.search(r'(\d+)\s*(?:เมตร|m)', text)
            if match:
                distance = int(match.group(1))
                if distance < 50:
                    context['distance_to_transformer'] = 'less_than_50m'
                elif distance <= 100:
                    context['distance_to_transformer'] = '50_100m'
                else:
                    context['distance_to_transformer'] = 'more_than_100m'
        
        # 2. Installation area (พื้นที่ติดตั้ง)
        if re.search(r'(?:ภายใน|indoor|ในบ้าน|ในอาคาร)', text):
            context['installation_area'] = 'indoor'
        elif re.search(r'(?:ใต้หลังคา|หลังคา|ร้อน|อุณหภูมิสูง|high.?temp)', text):
            context['installation_area'] = 'high_temp'
        elif re.search(r'(?:กลางแจ้ง|outdoor|นอกบ้าน|นอกอาคาร)', text):
            context['installation_area'] = 'outdoor'
        elif re.search(r'(?:ฝังดิน|underground|ใต้ดิน)', text):
            context['installation_area'] = 'underground'
        
        # 3. Panel type (ประเภทตู้)
        if re.search(r'(?:ตู้เมน|main\s*panel|mdb|ตู้หลัก)', text):
            context['panel_type'] = 'main'
        elif re.search(r'(?:ตู้ย่อย|sub\s*panel|db|ตู้รอง)', text):
            context['panel_type'] = 'sub'
        
        # 4. Conduit grouping (optional - default to 1)
        if re.search(r'(?:รวมท่อ|ท่อรวม|grouping|bundle)', text):
            if re.search(r'(?:4|5|6|สี่|ห้า|หก)\s*(?:วงจร|circuit)', text):
                context['conduit_grouping'] = '4-6'
            elif re.search(r'(?:2|3|สอง|สาม)\s*(?:วงจร|circuit)', text):
                context['conduit_grouping'] = '2-3'
        
        return context if context else None
    
    def _is_new_project(self, text: str) -> bool:
        """
        Detect if user is starting a new project (should start fresh session).
        
        Returns True for:
        - "ออกแบบบ้าน 2 ชั้น" (new design)
        - "project ใหม่", "เริ่มใหม่" (explicit new)
        """
        import re
        
        new_project_patterns = [
            r'ออกแบบ.*(บ้าน|อาคาร|คอนโด|โรงงาน)',  # Design + building type
            r'(project|โปรเจค|งาน)\s*(ใหม่|new)',     # Explicit new project
            r'(เริ่ม|start)\s*(ใหม่|new|fresh)',      # Start fresh
            r'reset|ล้าง|ยกเลิก',                    # Reset keywords
        ]
        
        for pattern in new_project_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_site_context_answer(self, text: str) -> bool:
        """
        Detect if user is answering site context questions (should continue session).
        
        Returns True for:
        - "หม้อแปลง 80 เมตร" (transformer distance)
        - "ติดตั้งในบ้าน" (installation area)
        - "ตู้เมน" (panel type)
        """
        import re
        
        # If text contains site_context keywords but NOT design keywords
        site_keywords = [
            r'หม้อแปลง|transformer',
            r'เมตร|meter|m\b',
            r'ภายใน|indoor|ในบ้าน',
            r'กลางแจ้ง|outdoor|นอกบ้าน',
            r'ใต้หลังคา|ร้อน|high.?temp',
            r'ตู้เมน|main\s*panel|mdb',
            r'ตู้ย่อย|sub\s*panel',
            r'ฝังดิน|underground',
        ]
        
        design_keywords = [
            r'ออกแบบ|design',
            r'ห้อง\s*\d+|bedroom|ห้องนอน',
            r'ชั้น\s*\d+|floor'
        ]
        
        has_site = any(re.search(p, text, re.IGNORECASE) for p in site_keywords)
        has_design = any(re.search(p, text, re.IGNORECASE) for p in design_keywords)
        
        # Site context answer = has site keywords but NO new design request
        return has_site and not has_design
    
    async def call_mozart(self, request: GatewayRequest, trace_id: str) -> Dict[str, Any]:
        """
        Call MOZART (RAG Service)
        
        Routes to:
        - /api/v1/design for design requests (spec + MCP calculation)
        - /api/v1/mcp_spec for spec-only requests
        - /api/v1/ask for general questions
        """
        try:
            # [CP1] Checkpoint: Gateway Entry
            query_len = len(request.input)
            has_session = hasattr(request, 'session_id') and request.session_id
            logger.info(f"[CP1] Gateway: query={query_len} chars, session={'Yes' if has_session else 'No'}")
            
            user_input_lower = request.input.lower()
            
            # Check if this is a design request (wants full calculation)
            is_design_request = any(kw in user_input_lower for kw in [
                "ออกแบบ", "design", "คำนวณ", "sizing", "calculate",
                "breaker", "wire", "สาย", "เบรกเกอร์"
            ])
            
            # Check if this is a spec request (wants spec only)
            is_spec_request = any(kw in user_input_lower for kw in [
                "spec", "สร้าง", "generate", "json"
            ])
            
            # Route to appropriate endpoint
            if is_design_request and hasattr(request, 'context') and request.context:
                # Full design with calculation - needs ProjectRequirements
                endpoint = f"{MOZART_ENDPOINT}/api/v1/design"
                payload = request.context.get("project_requirements", {
                    "project_name": "Gateway Request",
                    "building_type": "residential",
                    "voltage_system": "TH_1PH_230V",
                    "rooms": [],
                    "loads": []
                })
            elif is_spec_request and hasattr(request, 'context') and request.context:
                # Spec only - needs ProjectRequirements
                endpoint = f"{MOZART_ENDPOINT}/api/v1/mcp_spec"
                payload = request.context.get("project_requirements", {
                    "project_name": "Gateway Request",
                    "building_type": "residential",
                    "voltage_system": "TH_1PH_230V",
                    "rooms": [],
                    "loads": []
                })
            else:
                # =====================================================================
                # 🆕 SESSION-AWARE NLP FLOW
                # =====================================================================
                
                # 1. Check if user is answering site_context AND has session
                if request.session_id and self._is_site_context_answer(user_input_lower):
                    logger.info(f"[{trace_id}] Site context answer detected - using session design flow")
                    
                    # Extract site_context and update session
                    site_context = self._extract_site_context(user_input_lower)
                    
                    if site_context:
                        # Update session's site_context
                        await self.client.post(
                            f"{MOZART_ENDPOINT}/api/v1/session/{request.session_id}/site",
                            json={"answers": [
                                {"field_name": k, "value": v} 
                                for k, v in site_context.items()
                            ]},
                            headers={"X-Trace-ID": trace_id}
                        )
                    
                    # Get session's remembered requirements and design
                    endpoint = f"{MOZART_ENDPOINT}/api/v1/session/{request.session_id}"
                    session_resp = await self.client.get(endpoint)
                    
                    if session_resp.status_code == 200:
                        session_data = session_resp.json()
                        partial_req = session_data.get("partial_requirements", {})
                        
                        if partial_req.get("rooms") or partial_req.get("loads"):
                            # Has remembered data - proceed to design
                            # TODO: Call /session/{id}/design with partial_req
                            logger.info(f"[{trace_id}] Session has remembered data, proceeding to design")
                    
                    # For now, pass to ask endpoint (will get site_context error → trigger design)
                    endpoint = f"{MOZART_ENDPOINT}/api/v1/ask"
                    payload = {
                        "query": request.input,
                        "context_hint": [],
                        "language": "th"
                    }
                    if site_context:
                        payload["site_context"] = site_context
                
                # 2. Check if new project (should start fresh session)
                elif self._is_new_project(user_input_lower):
                    logger.info(f"[{trace_id}] New project detected - starting fresh session")
                    
                    # Start new session
                    session_resp = await self.client.post(
                        f"{MOZART_ENDPOINT}/api/v1/session/start",
                        headers={"X-Trace-ID": trace_id}
                    )
                    
                    if session_resp.status_code == 200:
                        session_data = session_resp.json()
                        new_session_id = session_data.get("session_id")
                        logger.info(f"[{trace_id}] Created session: {new_session_id}")
                    
                    # Pass to ask endpoint for design extraction
                    endpoint = f"{MOZART_ENDPOINT}/api/v1/ask"
                    site_context = self._extract_site_context(user_input_lower)
                    
                    payload = {
                        "query": request.input,
                        "context_hint": [],
                        "language": "th"
                    }
                    if site_context:
                        payload["site_context"] = site_context
                
                # 3. Regular question (no session needed)
                else:
                    endpoint = f"{MOZART_ENDPOINT}/api/v1/ask"
                    site_context = self._extract_site_context(user_input_lower)
                    
                    payload = {
                        "query": request.input,
                        "context_hint": [],
                        "language": "th"
                    }
                    
                    if site_context:
                        payload["site_context"] = site_context
                        logger.info(f"[{trace_id}] Extracted site_context: {site_context}")
            
            logger.info(f"[{trace_id}] Calling {endpoint}")
            
            response = await self.client.post(
                endpoint,
                json=payload,
                headers={"X-Trace-ID": trace_id}
            )
            response.raise_for_status()
            
            # [CP1] Validate response before returning
            result = response.json()
            
            # Check if response indicates an error from RAG
            if isinstance(result, dict):
                if result.get("grounding_status") == "EXTRACTION_FAILED":
                    logger.warning(f"[{trace_id}] RAG extraction failed - check CP3/CP4 logs")
                elif result.get("grounding_status") == "NEEDS_SITE_CONTEXT":
                    logger.info(f"[{trace_id}] RAG needs site_context - returning prompt")
                elif not result.get("answer"):
                    logger.warning(f"[{trace_id}] RAG returned empty answer")
                else:
                    logger.info(f"[{trace_id}] RAG returned valid response")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[{trace_id}] MOZART HTTP error: {e}")
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"[{trace_id}] MOZART call failed: {e}")
            return {"error": str(e)}
    
    async def call_amadeus(self, request: GatewayRequest, trace_id: str) -> Dict[str, Any]:
        """
        Call AMADEUS (AGI Service)
        
        For general conversation and non-technical queries
        """
        try:
            response = await self.client.post(
                f"{AMADEUS_ENDPOINT}/chat",
                json={
                    "message": request.input,
                    "user_id": request.user_id,
                    "session_id": request.session_id
                },
                headers={"X-Trace-ID": trace_id}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AMADEUS HTTP error: {e}")
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"AMADEUS call failed: {e}")
            return {"error": str(e)}


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="ACA Mozart Gateway",
    version="1.0.0",
    description="Intent Router for MOZART (RAG/MCP) and AMADEUS (AGI) services"
)

# Security: CORS configuration from environment
# Set ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com
# For development, use ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restricted to specified origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Only needed methods
    allow_headers=["Content-Type", "Authorization", "X-Trace-ID", "X-API-Key"],
)

# =============================================================================
# Rate Limiting (Security)
# =============================================================================
# 30 requests per minute per IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =============================================================================
# Security Headers Middleware
# =============================================================================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Global instances
router = LLMRouter()
proxy = ServiceProxy()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await router.close()
    await proxy.close()


@app.get("/")
async def health():
    """Health check"""
    return {
        "service": "ACA Mozart Gateway",
        "status": "alive",
        "routes": {
            "MOZART": MOZART_ENDPOINT,
            "AMADEUS": AMADEUS_ENDPOINT
        }
    }


@app.post("/orchestrate", response_model=GatewayResponse)
async def orchestrate(
    request: GatewayRequest,
    x_trace_id: Optional[str] = Header(None)
) -> GatewayResponse:
    """
    Main orchestration endpoint
    
    Flow:
    1. Classify intent (MOZART vs AMADEUS)
    2. Route to appropriate service
    3. Return response with routing metadata
    
    Dialogue Support:
    - If session_id provided, maintains conversation context
    - Multi-turn dialogues supported via Dialogue Manager
    """
    start_time = time.time()
    trace_id = x_trace_id or f"gateway-{uuid.uuid4().hex[:12]}"
    
    logger.info(f"[{trace_id}] Orchestrating: {request.input[:50]}...")
    
    # Check for dialogue session
    if request.session_id:
        dialogue_response = await _handle_dialogue_turn(request, trace_id)
        
        if dialogue_response.get("ready_for_mcp"):
            # Dialogue complete → Execute via MOZART
            data = await proxy.call_mozart(request, trace_id)
            return GatewayResponse(
                mode=IntentMode.MOZART,
                data={"dialogue": dialogue_response, "result": data},
                processing_time_ms=int((time.time() - start_time) * 1000),
                trace_id=trace_id,
                routing_decision=RoutingDecision(
                    mode=IntentMode.MOZART,
                    confidence=1.0,
                    reasoning="Dialogue completed, executing MCP",
                    keywords=["dialogue_complete"]
                )
            )
        else:
            # Continue dialogue
            return GatewayResponse(
                mode=IntentMode.MOZART,
                data=dialogue_response,
                processing_time_ms=int((time.time() - start_time) * 1000),
                trace_id=trace_id,
                routing_decision=RoutingDecision(
                    mode=IntentMode.MOZART,
                    confidence=1.0,
                    reasoning="Dialogue in progress",
                    keywords=["dialogue_turn"]
                )
            )
    
    # No session → Route by intent
    decision = await router.route(request.input)
    logger.info(f"[{trace_id}] Routed to {decision.mode} (confidence={decision.confidence:.2f})")
    
    # Call appropriate service
    if decision.mode == IntentMode.MOZART:
        data = await proxy.call_mozart(request, trace_id)
    else:
        data = await proxy.call_amadeus(request, trace_id)
    
    return GatewayResponse(
        mode=decision.mode,
        data=data,
        processing_time_ms=int((time.time() - start_time) * 1000),
        trace_id=trace_id,
        routing_decision=decision
    )


async def _handle_dialogue_turn(request: GatewayRequest, trace_id: str) -> Dict[str, Any]:
    """
    Handle dialogue turn via Dialogue Manager
    
    Returns dict with:
    - ready_for_mcp: bool - whether dialogue is complete
    - response: str - next prompt or confirmation
    - collected_data: dict - data collected so far
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DIALOGUE_MANAGER_ENDPOINT}/dialogue/turn",
                json={
                    "session_id": request.session_id,
                    "user_id": request.user_id,
                    "user_input": request.input
                },
                headers={"X-Trace-ID": trace_id}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Dialogue Manager call failed: {e}")
        return {
            "ready_for_mcp": False,
            "error": str(e),
            "response": "ขออภัย ระบบ Dialogue มีปัญหา กรุณาลองใหม่"
        }


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("GATEWAY_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")