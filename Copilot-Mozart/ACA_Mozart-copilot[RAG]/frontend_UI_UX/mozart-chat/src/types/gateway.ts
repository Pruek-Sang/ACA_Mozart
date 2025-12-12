/**
 * TypeScript interfaces for Gateway API communication
 */

/** Request body for /orchestrate endpoint */
export interface GatewayRequest {
    input: string;
    user_id?: string;
    session_id?: string;
    context?: Record<string, unknown>;
}

/** Routing decision made by the Gateway */
export interface RoutingDecision {
    mode: 'MOZART' | 'AMADEUS';
    confidence: number;
    reasoning: string;
    keywords: string[];
}

/** Response from /orchestrate endpoint */
export interface GatewayResponse {
    mode: 'MOZART' | 'AMADEUS';
    data: Record<string, unknown>;
    processing_time_ms: number;
    trace_id: string;
    routing_decision: RoutingDecision;
}

/** Health check response from / endpoint */
export interface HealthResponse {
    service: string;
    status: string;
    routes: {
        MOZART: string;
        AMADEUS: string;
    };
}

/** Chat message in the UI */
export interface Message {
    id: string;
    role: 'user' | 'bot' | 'system';
    content: string;
    mode?: 'MOZART' | 'AMADEUS' | 'SYSTEM';
    timestamp: Date;
    rawData?: Record<string, unknown>; // For JSON Editor
}

/** Chat state */
export interface ChatState {
    messages: Message[];
    isTyping: boolean;
    apiKey: string;
    isAuthenticated: boolean;
}
