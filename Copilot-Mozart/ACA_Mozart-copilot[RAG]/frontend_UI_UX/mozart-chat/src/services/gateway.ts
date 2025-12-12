/**
 * API Service for communicating with ACA Mozart Gateway
 */

import { API_CONFIG } from '../config/api.config';
import type { GatewayRequest, GatewayResponse, HealthResponse } from '../types/gateway';

/**
 * Send a message to the Gateway's /orchestrate endpoint
 */
export async function sendMessage(
    input: string,
    apiKey: string,
    context?: Record<string, unknown>
): Promise<GatewayResponse> {
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
