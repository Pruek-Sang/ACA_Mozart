/**
 * API Service Layer
 * 
 * Centralized API calls for the Mozart Frontend.
 * All network requests go through Gateway, which proxies to RAG/MCP.
 * 
 * Architecture:
 *   Frontend → Gateway (CORS) → RAG Service → MCP Core
 * 
 * Why separate file:
 * - Single source of truth for API endpoints
 * - Easy to mock for testing
 * - Clean separation from UI components
 */

import { buildApiUrl } from './utils';
import { getAccessToken } from './supabase';
import type { SiteContext, DisplayData, AuditRow, PDFData, SLDData } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface AskRequest {
    query: string;
    language: 'th' | 'en';
    site_context?: SiteContext;
    context_hint?: string[];
}

export interface AskResponse {
    answer: string;
    grounding_status?: string;
    confidence?: 'High' | 'Medium' | 'Low';
    metadata?: {
        readable_report?: string;
        mcp_result?: unknown;
        session_id?: string;
        // 🆕 Computed Data Layer
        display_data?: DisplayData;
        audit_results?: AuditRow[];
        pdf_data?: PDFData;
        sld_data?: SLDData;  // Fixed: was Record<string, unknown>
    };
    error?: string;
}

export interface ApiError {
    type: 'network' | 'backend' | 'frontend';
    status?: number;
    message: string;
    details?: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Ask the design system a question or request a design
 * 
 * @param payload - Query with optional site context
 * @param sessionId - Optional session ID for stateful editing
 * @returns Response with answer and optional design result
 * @throws ApiError on failure
 */
export async function askDesign(
    payload: AskRequest,
    sessionId?: string
): Promise<AskResponse> {
    const token = await getAccessToken();

    // 🆕 Include session_id in URL if provided
    const url = sessionId
        ? buildApiUrl(`/api/v1/ask?session_id=${sessionId}`)
        : buildApiUrl('/api/v1/ask');

    console.log('🚀 API: Sending request to', url);
    console.log('🔐 Auth:', token ? 'Token attached' : 'No token');
    console.log('📋 Session:', sessionId || 'none');

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify(payload)
    });

    console.log('📥 Response status:', response.status);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const apiError = new Error(`API Error: ${response.status}`) as any;
        apiError.response = {
            status: response.status,
            data: errorData
        };
        throw apiError;
    }

    const data = await response.json();
    console.log('📦 Response data keys:', Object.keys(data));

    return data;
}

/**
 * Start a new design session
 * Sessions remember site_context across multiple turns
 */
export async function startSession(): Promise<{ session_id: string }> {
    const token = await getAccessToken();

    const response = await fetch(buildApiUrl('/api/v1/session/start'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    });

    if (!response.ok) {
        throw new Error('Failed to start session');
    }

    return response.json();
}

/**
 * Get current session status
 */
export async function getSessionStatus(sessionId: string): Promise<any> {
    const token = await getAccessToken();

    const response = await fetch(buildApiUrl(`/api/v1/session/${sessionId}`), {
        method: 'GET',
        headers: {
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    });

    if (!response.ok) {
        throw new Error('Session not found');
    }

    return response.json();
}

/**
 * Health check - verify Gateway is reachable
 */
export async function healthCheck(): Promise<boolean> {
    try {
        const response = await fetch(buildApiUrl('/'), {
            method: 'GET'
        });
        return response.ok;
    } catch {
        return false;
    }
}
