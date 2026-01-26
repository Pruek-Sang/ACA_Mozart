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
 * 🆕 Load entry in session (matches Supabase session.loads schema)
 * Used for EDIT mode - stores simplified load info after CREATE
 */
export interface LoadEntry {
    device: string;        // circuit_name from display_data
    room_name: string;     // room or floor from display_data
    floor?: number;        // floor number (1 or 2)
    quantity?: number;     // optional quantity
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
        boq_data?: BOQData; // 🆕 BOQ with price_source
    };
}

/**
 * 🆕 Computed Display Data from Backend
 * Updated: Added summary section fields for professional load table
 */
export interface DisplayData {
    // === EXISTING FIELDS (KEEP - DO NOT REMOVE!) ===
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
    explainable_warnings?: ExplainableWarning[];
    assumptions?: AssumptionItem[];
    errors: string[];
    phase_balance?: Record<string, number>;

    // === NEW FIELDS (Optional - Summary Section) ===
    // Total Load by Phase
    total_load_va?: number;         // Total VA
    total_load_va_l1?: number;      // Phase L1 total
    total_load_va_l2?: number;      // Phase L2 total
    total_load_va_l3?: number;      // Phase L3 total

    // Demand Calculation
    demand_factor?: number;         // 0.78 etc.
    demand_load_va?: number;        // After demand factor

    // Main Equipment Details
    main_cb_type?: string;          // MCCB 3P 100AF/100AT
    main_cb_ic_ka?: number;         // 10kA at 400V
    main_feeder_size?: string;      // 50 Sq.mm
    main_feeder_type?: string;      // IEC01 (THW)
    main_feeder_grd?: string;       // G-16 Sq.mm
    main_raceway_type?: string;     // IMC / PVC / EMT
    main_raceway_size?: string;     // 2"

    // Audit Summary (for when all values are correct)
    rcbo_count?: number;            // Count of RCBO circuits
    mcb_count?: number;             // Count of MCB circuits

    // === 3-PHASE FIELDS ===
    is_three_phase?: boolean;       // True if 3-phase system
    voltage_system?: string;        // "1PH-230V" or "3PH-400V"
    line_voltage_v?: number;        // 230 or 400
    phase_voltage_v?: number;       // 230 (1PH or 3PH line-to-neutral)
    phase_balance_l1_kw?: number;   // L1 total kW
    phase_balance_l2_kw?: number;   // L2 total kW
    phase_balance_l3_kw?: number;   // L3 total kW
    phase_imbalance_percent?: number; // Imbalance %

    // === SOLAR PV FIELDS ===
    has_solar?: boolean;            // True if solar system present
    solar_capacity_kw?: number;     // Panel DC capacity in kW
    solar_system_type?: string;     // 'On-Grid (Net Metering)'
    solar_inverter?: SolarInverterData;     // Inverter specs
    solar_dc_circuit?: SolarCircuitData;    // DC circuit specs
    solar_ac_circuit?: SolarCircuitData;    // AC circuit specs
    solar_net_metering?: SolarNetMeteringData; // Net metering status
    solar_protection?: SolarProtectionItem[]; // Protection requirements
    solar_energy_estimate?: SolarEnergyEstimate; // Energy production estimate
    solar_net_impact?: SolarNetImpact;      // Load reduction info
    solar_warnings?: string[];      // Solar-specific warnings

    // 🆕 QC Certificate Data
    qc_certificate?: QCCertificateData;
}

/**
 * 🆕 Circuit Data from Backend
 * Updated: Added professional load table fields (all new fields are optional for backward compat)
 */
export interface CircuitData {
    // === EXISTING FIELDS (KEEP - DO NOT REMOVE!) ===
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

    // === NEW FIELDS (Optional - Professional Load Table) ===
    circuit_no?: number;           // CCT No. (1, 2, 3...)

    // Connection Load (VA) - 3-phase ready
    load_va_l1?: number;           // Phase L1 (for 1-phase: all here)
    load_va_l2?: number;           // Phase L2 (0 for 1-phase)
    load_va_l3?: number;           // Phase L3 (0 for 1-phase)
    total_va?: number;             // Total VA

    // Circuit Breaker Details
    breaker_ic_ka?: number;        // kA rating (6, 10, 15)
    breaker_af?: number;           // Frame size (AF)
    breaker_at?: number;           // Trip rating (AT)

    // Wire/Cable Details
    wire_size_l?: string;          // Line wire (copy of wire_size)
    wire_size_n?: string;          // Neutral wire
    wire_size_grd?: string;        // Ground wire (copy of ground_size)
    wire_type?: string;            // IEC01 (THW)

    // Raceway Details
    conduit_type?: string;         // PVC / EMT / IMC

    // Summary
    remark?: string;               // Combined notes as string
}

// ============================
// 🆕 QC CERTIFICATE TYPES
// ============================

/**
 * Single validation item with status
 */
export interface ValidationItem {
    parameter: string;
    value: string;
    standard: string;
    valid_range: string;
    status: '✓ OK' | '⚠️ WARN' | '❌ FAIL' | string;
}

/**
 * Per-circuit VD validation
 */
export interface CircuitVDValidation {
    circuit_name: string;
    vd_percent: number;
    limit: number;
    status: '✓ OK' | '⚠️ WARN' | '❌ FAIL' | string;
}

/**
 * 🆕 QC Certificate Data from Backend
 * Contains formal validation results for Design Assumptions Certificate
 */
export interface QCCertificateData {
    document_id: string;
    company_name: string;
    project_name: string;
    date_generated: string;
    valid_until: string;
    revision: string;
    total_kw: number;
    main_breaker: string;
    circuit_count: number;

    // Validation sections
    static_params: ValidationItem[];
    vd_limits: ValidationItem[];
    circuit_vd_validation: CircuitVDValidation[];

    // Distance info
    default_circuit_count: number;
    default_circuits: Array<{ name: string; distance_m: number }>;

    // Summary
    summary: {
        pass_count: number;
        warn_count: number;
        fail_count: number;
        total_count: number;
    };

    // Scope & References
    scope_items: string[];
    references: string[];
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
 * 🆕 BOQ Item (single line in BOQ)
 */
export interface BOQItem {
    item_no: string;
    description: string;
    quantity: number;
    unit: string;
    material_unit_price: number;
    material_total: number;
    labor_unit_price: number;
    labor_total: number;
    total_price: number;
    remark: string;
}

/**
 * 🆕 BOQ Section (E.1, E.2, E.3)
 */
export interface BOQSection {
    section_id: string;
    section_name: string;
    items: BOQItem[];
    section_total: number;
}

/**
 * 🆕 Complete BOQ Data from Backend
 */
export interface BOQData {
    project_name: string;
    date: string;
    sections: BOQSection[];
    subtotal_material: number;
    subtotal_labor: number;
    grand_total: number;
    vat_percent: number;
    vat_amount: number;
    final_total: number;
    price_valid_date: string;
    price_valid_warning: string;
    price_source: 'prices.csv' | 'catalog_fallback' | 'error';
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

    // Legacy / Alternative fields found in usage
    total_watts?: number;
    total_va?: number;
    circuit_name?: string;
    // More legacy fallbacks
    name?: string;
    trade_size?: string;
    ic_ka?: number | string;
    breaker_rating?: number;

    // Optional fields for Excel Export (Professional Load Table)
    load_va_l1?: number;
    load_va_l2?: number;
    load_va_l3?: number;
    breaker_type?: string;
    breaker_poles?: number;
    breaker_ic_ka?: number | string;
    breaker_af?: number;
    breaker_at?: number;
    wire_size_l?: string;
    wire_size_n?: string;
    wire_size_grd?: string;
    ground_size?: string;
    wire_type?: string;
    conduit_type?: string;
    remark?: string;
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
        main_wire?: string;  // 🆕 Main wire size
        warnings?: string[];
        explainable_warnings?: ExplainableWarning[];
        assumptions?: AssumptionItem[];

        // 🆕 Summary Section (from DisplayData)
        demand_factor?: number;
        main_cb_type?: string;
        main_cb_ic_ka?: number;
        main_feeder_size?: string;
        main_feeder_type?: string;
        main_feeder_grd?: string;
        main_raceway_type?: string;
        main_raceway_size?: string;
        rcbo_count?: number;
        mcb_count?: number;

        // 🆕 QC Certificate Data
        qc_certificate?: QCCertificateData;

        // 🆕 PDF/UI Explicit Fields
        project_name?: string;
        building_type?: string;
        meter_size?: string;
        main_cb_rating?: number;  // Alias for main_breaker if used
        calculations?: Record<string, unknown>;       // Allow any calculation data

        // 🆕 Revision History (for HistoryPanel)
        revision_history?: Array<{
            fromVersion: number;
            toVersion: number;
            timestamp: string;
            summary: string;
            changes: Array<{
                field: string;
                label: string;
                before: string;
                after: string;
                changeType: 'added' | 'removed' | 'modified';
            }>;
            changeCount: number;
        }>;
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

// === SOLAR PV TYPES ===

/**
 * Solar inverter specifications
 */
export interface SolarInverterData {
    rated_kw: number;
    panel_capacity_kw: number;
    efficiency: number;
    phase_type: string;        // '1-Phase' | '3-Phase'
    num_phases: number;
    ac_voltage: number;
    ac_current_a: number;
    type: string;              // 'Grid-Tie String Inverter'
}

/**
 * Solar DC/AC circuit specifications
 */
export interface SolarCircuitData {
    string_isc_a?: number;     // DC only
    design_current_a: number;
    wire_size_mm2: number;
    wire_type: string;
    dc_breaker_a?: number;     // DC only
    ac_breaker_a?: number;     // AC only
    breaker_type?: string;     // AC only
    dc_disconnect?: boolean;   // DC only
    ac_disconnect?: boolean;   // AC only
    num_strings?: number;      // DC only
    ac_current_a?: number;     // AC only
}

/**
 * Net metering eligibility info
 */
export interface SolarNetMeteringData {
    eligible_residential: boolean;
    requires_ct_meter: boolean;
    program: string;           // 'residential' | 'residential_ct' | 'commercial'
    capacity_kw: number;
    limit_kw: number;
    notes: string[];
}

/**
 * Solar protection requirement item
 */
export interface SolarProtectionItem {
    item: string;
    spec: string;
    location: string;
    mandatory: boolean;
}

/**
 * Solar energy production estimate
 */
export interface SolarEnergyEstimate {
    daily_kwh: number;
    monthly_kwh: number;
    annual_kwh: number;
    peak_sun_hours: number;
    system_efficiency: number;
}

/**
 * Solar load reduction impact
 */
export interface SolarNetImpact {
    load_reduction_watts: number;
    description: string;
}

// === DEVICE CODES (ตัวอย่าง) ===
export const DEVICE_CODES = {
    'AC-12000BTU': { name: 'แอร์ 12000 BTU', power_kw: 1.4 },
    'AC-18000BTU': { name: 'แอร์ 18000 BTU', power_kw: 2 },
    'HEATER-3500W': { name: 'เครื่องทำน้ำอุ่น 3500W', power_kw: 3.5 },
    'HEATER-4500W': { name: 'เครื่องทำน้ำอุ่น 4500W', power_kw: 4.5 },
    'INDUCTION-3000W': { name: 'เตาแม่เหล็กไฟฟ้า', power_kw: 3 },
    'OUTLET-16A': { name: 'ปลั๊กไฟ 16A', power_kw: 0.18 },
    'LIGHT-10W': { name: 'หลอดไฟ LED 10W', power_kw: 0.01 },
} as const;

// === NEW TYPES FOR FEATURES ===

export interface AssumptionItem {
    key: string;
    label: string;
    value: string | number;
    source: 'default' | 'user' | 'calculated';
    category: string;
}

export interface SuggestedAction {
    type: string;
    description: string;
    effort: 'low' | 'medium' | 'high';
}

export interface ExplainableWarning {
    code: string;
    message: string;
    severity: 'critical' | 'warning' | 'info';
    reason?: string;
    suggested_action?: SuggestedAction;
    circuit_name?: string;
}
