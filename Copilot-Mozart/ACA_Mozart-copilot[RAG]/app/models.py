"""
Data Models - The Divine Schemas
All Pydantic models with strict typing following MCP Contract

Philosophy: Ordo ab Chao (Order from Chaos)
- No loose Dict types
- Every field has explicit type and purpose
- Aligned with MCP DESIGN HANDOVER v2.0
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from enum import Enum


# =============================================================================
# Knowledge Layer Models (Folder-Based Architecture)
# =============================================================================

class KnowledgeFolder(str, Enum):
    """
    Enumeration of knowledge folders
    
    RAG recognizes exactly 4 folders:
    - db: Catalog snapshots + DB contracts
    - example: Few-shot examples  
    - mcp: MCP design docs
    - standard: Thai electrical standards
    """
    DB = "db"
    EXAMPLE = "example"
    MCP = "mcp"
    STANDARD = "standard"


class DocumentMeta(BaseModel):
    """
    Metadata for a knowledge document
    
    Philosophy:
    - All files in 4 folders are visible to RAG
    - knowledge_index.json provides metadata/priority (not whitelist)
    - Unindexed files still loadable (lower priority)
    """
    # Identity
    id: Optional[str] = Field(None, description="Document ID from knowledge_index.json (if exists)")
    path: str = Field(..., description="Absolute file path")
    rel_path: str = Field(..., description="Path relative to KNOWLEDGE_ROOT")
    folder: KnowledgeFolder = Field(..., description="Which of 4 folders this belongs to")
    
    # Metadata (from knowledge_index.json if exists)
    group: Optional[str] = Field(None, description="Document group (e.g., 'mcp_spec', 'catalog_schema')")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    version: Optional[str] = Field(None, description="Document version")
    language: Optional[str] = Field("th", description="Document language")
    
    # Computed
    priority: int = Field(default=50, description="Retrieval priority (higher = more important)")



# =============================================================================
# Common Models
# =============================================================================

class SourceRef(BaseModel):
    """Reference to a source document"""
    file: str = Field(..., description="Source file path or doc_id")
    section: str = Field(default="N/A", description="Section within document")
    score: Optional[float] = Field(None, description="Relevance score if from retrieval")
    content: Optional[str] = Field(None, description="Short snippet of retrieved content for auditing/judge")


# =============================================================================
# Layer 1: QA / Answer Endpoints
# =============================================================================

class QueryRequest(BaseModel):
    """Request for /api/v1/ask endpoint"""
    query: str = Field(..., description="User's question in natural language")
    context_hint: List[str] = Field(
        default_factory=list,
        description="Knowledge groups to search, e.g., ['thai_standard', 'mcp_spec']"
    )
    language: Literal["th", "en"] = Field(
        default="th",
        description="Response language (Thai or English)"
    )
    filters: Optional[Dict[str, str]] = Field(None, description="Optional advanced filters for retrieval")


class AnswerMetadata(BaseModel):
    """Metadata for /api/v1/ask responses"""
    llm_model: str = Field(..., description="LLM model used")
    retrieved_docs: List[str] = Field(default_factory=list, description="Document IDs retrieved")
    retrieval_group: Optional[str] = Field(None, description="Knowledge groups searched")
    # MCP outputs (for design requests)
    autolisp_code: Optional[str] = Field(None, description="Generated AutoLISP code for AutoCAD")
    readable_report: Optional[str] = Field(None, description="Human-readable report from MCP (Markdown)")
    standards_markdown: Optional[str] = Field(None, description="Design standards summary")


class StandardResponse(BaseModel):
    """Response from /api/v1/ask endpoint"""
    answer: str = Field(..., description="Answer in Thai, grounded in context")
    sources: List[SourceRef] = Field(default_factory=list, description="Sources used for answer")
    confidence: Literal["High", "Medium", "Low"] = Field(..., description="Confidence level")
    grounding_status: str = Field(..., description="Grounding validation result")
    metadata: 'AnswerMetadata' = Field(..., description="LLM and retrieval metadata")


# =============================================================================
# Layer 2: Spec Generation (MCP Alignment)
# =============================================================================

class RoomInput(BaseModel):
    """Room specification from user (human-readable)"""
    name: str = Field(..., description="Room name e.g., 'ห้องนอน 1'")
    type: str = Field(..., description="Room type e.g., 'bedroom', 'kitchen'")
    area_sqm: Optional[float] = Field(None, description="Area in square meters")
    floor: int = Field(default=1, description="Floor number (1, 2, etc.)")


class LoadInput(BaseModel):
    """Load specification from user (human-readable)"""
    room_name: str = Field(..., description="Which room this load belongs to")
    device: str = Field(..., description="Device name e.g., 'AC_12000BTU', 'OUTLET_16A'")
    quantity: int = Field(default=1, description="Number of devices")
    power_kw: Optional[float] = Field(None, description="Total power in kW if known")
    floor: int = Field(default=1, description="Floor number for circuit grouping")


class ProjectRequirements(BaseModel):
    """
    Input from engineer/user (human-readable format)
    Used as input to /api/v1/mcp_spec
    """
    project_name: str = Field(..., description="Project name")
    building_type: str = Field(..., description="Building type e.g., 'residential', 'commercial'")
    voltage_system: str = Field(..., description="Voltage system code e.g., 'TH_1PH_230V'")
    location: Optional[str] = Field(None, description="Location e.g., 'Bangkok'")
    
    rooms: List[RoomInput] = Field(default_factory=list, description="List of rooms")
    loads: List[LoadInput] = Field(default_factory=list, description="List of electrical loads")
    user_constraints: List[str] = Field(default_factory=list, description="User constraints e.g., 'split_kitchen_circuit'")


# --- MCP Contract Models (Strict Schema) ---

class ProjectInfo(BaseModel):
    """Project metadata for MCP"""
    project_name: str
    building_type: str  # Normalized: RESIDENTIAL, COMMERCIAL, etc.
    spec_version: str = "2.0"


class ElectricalSystem(BaseModel):
    """Electrical system specification"""
    voltage_system: str  # e.g., TH_1PH_230V, TH_3PH_380V
    earthing: str = "TT"  # TT, TN-S, etc.


class RoomSpec(BaseModel):
    """
    Room specification for MCP
    Aligned with MCP DESIGN HANDOVER v2.0
    """
    room_id: str = Field(..., description="Unique room ID e.g., 'R1', 'R2'")
    name: str = Field(..., description="Room name")
    room_type: str = Field(..., description="Type: BEDROOM, KITCHEN, LIVING, BATHROOM, etc.")
    template_code: str = Field(..., description="Room template code e.g., 'ROOMT-BEDROOM-STD'")
    area_sqm: Optional[float] = Field(None, description="Area in m²")


class LoadSpec(BaseModel):
    """
    Load specification for MCP
    Aligned with MCP DESIGN HANDOVER v2.0
    """
    load_id: str = Field(..., description="Unique load ID e.g., 'L1', 'L2'")
    room_id: str = Field(..., description="Reference to room_id")
    device_code: str = Field(..., description="Device code e.g., 'AC-12000BTU', 'SOCKET-16A'")
    qty: int = Field(default=1, description="Quantity")
    notes: Optional[str] = Field(None, description="Additional notes")
    floor: int = Field(default=1, description="Floor number for circuit grouping")


class Constraints(BaseModel):
    """Project constraints"""
    rule_profile_id: str = Field(..., description="Rule profile e.g., 'TH_RESIDENTIAL_LV'")
    user_constraints: List[str] = Field(default_factory=list, description="User-specified constraints")


class ProjectInputSpec(BaseModel):
    """
    Complete specification for MCP Core v2
    This is the CONTRACT between RAG and MCP
    
    Philosophy: This is the "divine scroll" that MCP reads
    - Every field strictly typed
    - No ambiguity, no hallucination space
    """
    project_info: ProjectInfo
    electrical_system: ElectricalSystem
    rooms: List[RoomSpec]
    loads: List[LoadSpec]
    constraints: Constraints


class StandardsProfile(BaseModel):
    """Standards profile metadata"""
    rule_profile_id: str = Field(..., description="Rule profile applied")
    notes: Optional[str] = Field(None, description="Additional notes about standards")


class LlmMetadata(BaseModel):
    """
    LLM generation metadata for audit trail
    Added in v3.2 per HOW_TO_FIX_RAG_v2
    """
    model: str = Field(..., description="LLM model used e.g., 'gemini-1.5-pro'")
    retrieved_docs: List[str] = Field(default_factory=list, description="Document IDs used for context")
    temperature: float = Field(default=0.0, description="Generation temperature")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Generation timestamp")


class McpSpecResponse(BaseModel):
    """
    Complete response from /api/v1/mcp_spec
    Ready to forward to MCP Core /mcp/v2/run
    """
    project_input: ProjectInputSpec = Field(..., description="The core spec for MCP")
    standards_profile: StandardsProfile = Field(..., description="Standards used")
    llm_metadata: LlmMetadata = Field(..., description="LLM generation audit trail")


class InsufficientDataError(BaseModel):
    """
    Error body for HTTP 422 when requirements incomplete
    
    Used in /api/v1/mcp_spec when data insufficient to generate spec.
    NOT a response type - used in HTTPException detail only.
    """
    error: str = Field(default="Insufficient project requirements", description="Error message")
    missing_fields: List[str] = Field(default_factory=list, description="Fields that are missing/incomplete")
    questions: List[str] = Field(default_factory=list, description="Clarifying questions for user")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions to fix")


# =============================================================================
# Layer 3: Raw Retrieval
# =============================================================================

class RawRetrieveRequest(BaseModel):
    """Request for debugging retrieval"""
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    filters: Optional[Dict[str, str]] = None


# =============================================================================
# Layer 4: Management
# =============================================================================

class IngestRequest(BaseModel):
    """Request to ingest a document into vector DB"""
    file_path: str = Field(..., description="Absolute path to file")


class DeleteRequest(BaseModel):
    """Request to delete documents from vector DB"""
    source_path: str = Field(..., description="Source path pattern to delete")


# =============================================================================
# Trust Log Models (Canonical Funnel Pattern)
# =============================================================================

class McpSpecTrustRecord(BaseModel):
    """
    Trust record for every /api/v1/mcp_spec call
    Follows Canonical Funnel philosophy: full audit trail
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = Field(..., description="Unique request ID (UUID)")
    user_id: Optional[str] = Field(None, description="User ID if available")
    
    # Input
    project_requirements: Dict[str, Any] = Field(..., description="Raw input requirements")
    
    # Context
    retrieved_doc_ids: List[str] = Field(default_factory=list, description="Documents retrieved")
    
    # LLM
    llm_model: str = Field(..., description="LLM model used")
    llm_plan_text: Optional[str] = Field(None, description="Human-readable plan (Phase 4)")
    raw_llm_output: str = Field(..., description="Raw LLM response before parsing")
    
    # Validation
    parse_success: bool = Field(..., description="Did JSON parse succeed?")
    validation_errors: List[str] = Field(default_factory=list, description="Pydantic validation errors")
    
    # Output
    project_input: Optional[Dict[str, Any]] = Field(None, description="Parsed ProjectInputSpec if successful")
    
    # Downstream
    forwarded_to_mcp: bool = Field(default=False, description="Was this forwarded to MCP?")
    
    # Note: datetime serialization is handled automatically by Pydantic V2
