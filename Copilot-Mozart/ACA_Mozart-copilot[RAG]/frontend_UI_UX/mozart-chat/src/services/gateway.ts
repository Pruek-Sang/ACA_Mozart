/**
 * API Service for communicating with ACA Mozart Gateway
 */

import { API_CONFIG } from '../config/api.config';
import type { GatewayRequest, GatewayResponse, HealthResponse } from '../types/gateway';

/**
 * Send a message to the Gateway's /orchestrate endpoint
 */
// Mock Data for UI Verification
const MOCK_DATA = {
    answer: "นี่คือตัวอย่างการออกแบบสำหรับบ้าน 2 ชั้นตามที่คุณต้องการค่ะ\n\n- ชั้น 1: ประกอบด้วยห้องนั่งเล่น, ห้องครัว และห้องรับประทานอาหาร\n- ชั้น 2: เป็นโซนพักผ่อน มีห้องนอนใหญ่และห้องนอนเล็ก\n\nสามารถดูรายละเอียดในแผนผังด้านขวาได้เลยนะคะ",
    rooms: [
        // Floor 1
        { id: '101', name: 'Living Room', room_type: 'LIVING_ROOM', floor: 1, loads: [{ id: 'l1', type: 'LIGHT', name: 'Main Light' }, { id: 'l2', type: 'OUTLET', name: 'TV Outlet' }] },
        { id: '102', name: 'Kitchen', room_type: 'KITCHEN', floor: 1, loads: [{ id: 'k1', type: 'LIGHT', name: 'Kitchen Light' }, { id: 'k2', type: 'OUTLET', name: 'Fridge' }] },
        { id: '103', name: 'Dining', room_type: 'DINING', floor: 1, loads: [{ id: 'd1', type: 'LIGHT', name: 'Chandelier' }] },

        // Floor 2
        { id: '201', name: 'Master Bedroom', room_type: 'MASTER_BEDROOM', floor: 2, loads: [{ id: 'm1', type: 'LIGHT', name: 'Main Light' }, { id: 'm2', type: 'SWITCH', name: 'Bed Switch' }] },
        { id: '202', name: 'Bedroom 2', room_type: 'BEDROOM', floor: 2, loads: [{ id: 'b1', type: 'LIGHT', name: 'Light' }] },
        { id: '203', name: 'Bathroom', room_type: 'BATHROOM', floor: 2, loads: [{ id: 'bt1', type: 'LIGHT', name: 'Bath Light' }] },
    ]
};

export async function sendMessage(
    input: string,
    apiKey: string,
    context?: Record<string, unknown>
): Promise<GatewayResponse> {
    // **[MOCK MODE]** Immediate return for UI testing
    if (API_CONFIG.MOCK_MODE) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
        return {
            mode: 'MOZART',
            data: MOCK_DATA,
            processing_time_ms: 500,
            trace_id: 'mock-trace-123',
            routing_decision: { mode: 'MOZART', confidence: 1.0, reasoning: 'Mock Mode', keywords: [] }
        };
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT_MS);

    try {
        const response = await fetch(`${API_CONFIG.GATEWAY_URL}/orchestrate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey,
            },
            body: JSON.stringify({
                input,
                context,
            } as GatewayRequest),
            signal: controller.signal,
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        return response.json();
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Test connection to Gateway (health check)
 */
export async function testConnection(apiKey: string): Promise<boolean> {
    try {
        const response = await fetch(`${API_CONFIG.GATEWAY_URL}/`, {
            method: 'GET',
            headers: {
                'X-API-Key': apiKey,
            },
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Get Gateway health status
 */
export async function getHealth(): Promise<HealthResponse | null> {
    try {
        const response = await fetch(`${API_CONFIG.GATEWAY_URL}/`);
        if (!response.ok) return null;
        return response.json();
    } catch {
        return null;
    }
}

/**
 * Extract the display message from Gateway response
 */
export function extractDisplayMessage(data: Record<string, unknown>): string {
    // Try common response formats
    if (typeof data.answer === 'string') return data.answer;
    if (typeof data.response === 'string') return data.response;
    if (typeof data.message === 'string') return data.message;

    // Return formatted JSON for structured data
    return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
}

/**
 * Check if the response contains structured data (for JSON Editor)
 */
export function hasStructuredData(data: Record<string, unknown>): boolean {
    // Check if it has common spec/project keys
    const structuredKeys = ['rooms', 'loads', 'project_name', 'voltage_system', 'spec', 'json'];
    return structuredKeys.some((key) => key in data);
}
