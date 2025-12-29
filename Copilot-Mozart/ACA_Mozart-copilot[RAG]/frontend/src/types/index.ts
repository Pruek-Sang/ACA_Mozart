// --- TYPES: Mozart Frontend (Corrected to match API Contract) ---
// ใช้ snake_case ตรงๆ ตาม Backend เพื่อความเรียบง่าย

// === REQUEST MODELS (Frontend -> Backend) ===

/**
 * บริบทสถานที่ติดตั้ง (Required สำหรับ /api/v1/design)
 * Matches: API_Contract_Frontend.md
 */
export interface SiteContext {
    distance_to_transformer: 'less_than_50m' | '50_100m' | 'more_than_100m';
    installation_area: 'indoor' | 'high_temp' | 'outdoor' | 'underground';
    panel_type: 'main' | 'sub';
    conduit_grouping: '1' | '2-3' | '4-6';
}

/**
 * ข้อมูลห้อง
 */
export interface RoomInput {
    name: string;
    type: string; // bedroom, bathroom, kitchen, etc.
    floor: number;
}

/**
 * ข้อมูลโหลดไฟฟ้า (Request)
 */
export interface LoadInput {
    room_name: string;
    device: string;      // Device code: AC-12000BTU, HEATER-4500W, etc.
    quantity: number;
    power_kw?: number;   // Optional: ถ้ารู้กำลังไฟ
    floor?: number;
    branch_distance_m?: number; // ระยะจากตู้ไฟ (meters)
}

/**
 * Request สำหรับ /api/v1/ask
 */
export interface AskRequest {
    query: string;
    context_hint?: string[];
    language?: 'th' | 'en';
    site_context?: SiteContext;
}

/**
 * Request สำหรับ /api/v1/design
 */
export interface DesignRequest {
    project_name: string;
    building_type: 'residential' | 'commercial';
    voltage_system: 'TH_1PH_230V' | 'TH_3PH_380V';
    rooms: RoomInput[];
    loads: LoadInput[];
    site_context: SiteContext;
}

// === RESPONSE MODELS (Backend -> Frontend) ===

/**
 * Source reference จาก RAG
 */
export interface SourceRef {
    file: string;
    section?: string;
    score: number;
}

/**
 * Response จาก /api/v1/ask
 */
export interface AskResponse {
    answer: string;       // Markdown
    sources: SourceRef[];
    confidence: 'High' | 'Medium' | 'Low';
    grounding_status?: string;
    metadata?: {
        llm_model?: string;
        retrieved_docs?: string[];
        readable_report?: string;
        autolisp_code?: string;
        // 🆕 Computed Data Layer - structured JSON
        display_data?: DisplayData;
        audit_results?: AuditRow[];
        pdf_data?: PDFData;
        sld_data?: Record<string, unknown>;
    };
}

/**
 * 🆕 Computed Display Data from Backend
 */
export interface DisplayData {
    project_name: string;
    total_watts: number;
    total_kw: number;
    demand_current: number;
    design_current: number;
    meter_size: string;
    main_wire: string;
    main_breaker: string;
    circuits: CircuitData[];
    circuit_count: number;
    warnings: string[];
    errors: string[];
    phase_balance?: Record<string, number>;
}

/**
 * 🆕 Circuit Data from Backend
 */
export interface CircuitData {
    circuit_name: string;
    circuit_id: string;
    floor: string;
    room: string;
    total_watts: number;
    total_kw: number;
    total_current: number;
    breaker_rating: number;
    breaker_poles: number;
    breaker_type: string;
    wire_size: string;
    ground_size: string;
    conduit_size: string;
    vd_percent: number;
    requires_rcbo: boolean;
    num_loads: number;
    notes: string[];
}

/**
 * 🆕 PDF/BOQ Data from Backend
 */
export interface PDFData {
    project_info: {
        name: string;
        total_kw: number;
        demand_current: number;
        design_current: number;
    };
    floors: Array<{
        floor: string;
        display_name: string;
        circuits: Array<Record<string, unknown>>;
        total_kw: number;
    }>;
    main_equipment: Record<string, string>;
    phase_balance: Record<string, number>;
}

/**
 * 🆕 SLD (Single Line Diagram) Node
 */
export interface SLDNode {
    id: string;
    type: 'meter' | 'main_breaker' | 'branch_breaker' | 'rcbo' | 'load';
    label: string;
    x: number;
    y: number;
    width: number;
    height: number;
    data: {
        icon?: string;
        breaker?: string;
        wire?: string;
        current?: string;
        kw?: number;
        rcbo?: boolean;
        [key: string]: unknown;
    };
}

/**
 * 🆕 SLD Edge (connection between nodes)
 */
export interface SLDEdge {
    id: string;
    source: string;
    target: string;
    style: 'solid' | 'dashed';
}

/**
 * 🆕 Complete SLD Data from Backend
 */
export interface SLDData {
    nodes: SLDNode[];
    edges: SLDEdge[];
    metadata: {
        project_name: string;
        total_kw: number;
        demand_current: number;
        circuit_count: number;
        canvas_width: number;
        canvas_height: number;
    };
}

/**
 * โหลดไฟฟ้าที่คำนวณแล้ว (Response)
 */
export interface LoadResult {
    id?: string;
    room_name: string;
    device_name: string;
    power_kw: number;
    current_a: number;
    breaker_size: number;
    wire_size: string;
    conduit_size?: string;
    voltage_drop_percent?: number;
    phase?: number;
    warnings?: string[];
}

/**
 * Audit Row สำหรับตารางตรวจสอบ
 */
export interface AuditRow {
    check: string;
    user_value: string | number;
    recommended_value: string | number;
    status: 'PASS' | 'FAIL' | 'WARN';
}

/**
 * House Block สำหรับ Layout
 */
export interface HouseBlock {
    id: string;
    label: string;
    position: { x: number; y: number };
    status?: 'normal' | 'overload';
}

/**
 * Response จาก /api/v1/design (Full Design)
 * NOTE: ยังต้อง verify กับ Backend จริง (Smoke Test)
 */
export interface DesignResult {
    success: boolean;
    message: string;
    data?: {
        loads: LoadResult[];
        audit_table?: AuditRow[];
        sld_image_url?: string;  // หรืออาจเป็น base64
        house_layout?: HouseBlock[];
        total_power_kw?: number;
        main_breaker?: number;
        warnings?: string[];
    };
}

// === UI STATE MODELS ===

/**
 * Chat Message สำหรับ UI
 */
export interface ChatMessage {
    role: 'user' | 'system' | 'assistant';
    content: string;
    timestamp: Date;
    error_type?: 'frontend_error' | 'backend_error' | 'network_error';
}

/**
 * Error Response จาก Backend
 */
export interface ErrorResponse {
    error: string;
    missing_fields?: string[];
    retry_after?: number;
}

// === DEVICE CODES (ตัวอย่าง) ===
export const DEVICE_CODES = {
    'AC-12000BTU': { name: 'แอร์ 12000 BTU', power_kw: 1.4 },
    'AC-18000BTU': { name: 'แอร์ 18000 BTU', power_kw: 2.0 },
    'HEATER-3500W': { name: 'เครื่องทำน้ำอุ่น 3500W', power_kw: 3.5 },
    'HEATER-4500W': { name: 'เครื่องทำน้ำอุ่น 4500W', power_kw: 4.5 },
    'INDUCTION-3000W': { name: 'เตาแม่เหล็กไฟฟ้า', power_kw: 3.0 },
    'OUTLET-16A': { name: 'ปลั๊กไฟ 16A', power_kw: 0.18 },
    'LIGHT-10W': { name: 'หลอดไฟ LED 10W', power_kw: 0.01 },
} as const;
