/**
 * 🩺 Health Tracker Hook
 * 
 * Tracks all session, API, CRUD, and Edit operations
 * for debugging via the Health Panel
 */

import { useReducer, useCallback, useMemo } from 'react';

// Event Types
export type HealthEventType =
    | 'SESSION_CREATE'
    | 'SESSION_LOAD'
    | 'SESSION_RESTORE'
    | 'CRUD_CREATE'
    | 'CRUD_READ'
    | 'CRUD_UPDATE'
    | 'CRUD_DELETE'
    | 'EDIT_INTENT'
    | 'EDIT_MERGE'
    | 'PREVIOUS_DESIGN_LOAD'
    | 'API_REQUEST'
    | 'API_RESPONSE'
    | 'API_ERROR'
    | 'GATEWAY_PROXY'
    | 'FRONTEND_STATE_CHANGE';

export interface HealthEvent {
    id: string;
    type: HealthEventType;
    timestamp: Date;
    success: boolean;
    details: Record<string, unknown>;
}

export interface RequestInfo {
    endpoint: string;
    method: string;
    sentSessionId: string | null;
    sentProjectName: string | null;
    body: unknown;
    timestamp: Date;
}

export interface ResponseInfo {
    status: number;
    receivedSessionId: string | null;
    receivedProjectName: string | null;
    hasBoqData: boolean;
    hasDisplayData: boolean;
    hasSldData: boolean;
    hasMessages: boolean;
    errorMessage?: string;
    timestamp: Date;
}

export interface CrudStatus {
    create: 'idle' | 'pending' | 'success' | 'failed';
    read: 'idle' | 'pending' | 'success' | 'failed' | 'not_found';
    update: 'idle' | 'pending' | 'success' | 'failed' | 'never_called';
    delete: 'idle' | 'pending' | 'success' | 'failed';
}

export interface EditInjectorStatus {
    intent: 'CREATE' | 'EDIT' | null;
    query: string | null;
    previousDesignLoaded: boolean;
    mergeResult: 'success' | 'fallback' | 'pending' | null;
    fallbackReason?: string;
}

interface HealthState {
    events: HealthEvent[];
    lastRequest: RequestInfo | null;
    lastResponse: ResponseInfo | null;
    crudStatus: CrudStatus;
    editInjectorStatus: EditInjectorStatus;
    gatewayForwardedSessionId: boolean | null;
}

type HealthAction =
    | { type: 'ADD_EVENT'; payload: HealthEvent }
    | { type: 'SET_LAST_REQUEST'; payload: RequestInfo }
    | { type: 'SET_LAST_RESPONSE'; payload: ResponseInfo }
    | { type: 'UPDATE_CRUD_STATUS'; payload: Partial<CrudStatus> }
    | { type: 'UPDATE_EDIT_STATUS'; payload: Partial<EditInjectorStatus> }
    | { type: 'SET_GATEWAY_FORWARD'; payload: boolean }
    | { type: 'CLEAR_ALL' };

const initialState: HealthState = {
    events: [],
    lastRequest: null,
    lastResponse: null,
    crudStatus: {
        create: 'idle',
        read: 'idle',
        update: 'never_called',
        delete: 'idle',
    },
    editInjectorStatus: {
        intent: null,
        query: null,
        previousDesignLoaded: false,
        mergeResult: null,
    },
    gatewayForwardedSessionId: null,
};

function healthReducer(state: HealthState, action: HealthAction): HealthState {
    switch (action.type) {
        case 'ADD_EVENT':
            return {
                ...state,
                events: [...state.events.slice(-49), action.payload], // Keep last 50 events
            };
        case 'SET_LAST_REQUEST':
            return { ...state, lastRequest: action.payload };
        case 'SET_LAST_RESPONSE':
            return { ...state, lastResponse: action.payload };
        case 'UPDATE_CRUD_STATUS':
            return { ...state, crudStatus: { ...state.crudStatus, ...action.payload } };
        case 'UPDATE_EDIT_STATUS':
            return { ...state, editInjectorStatus: { ...state.editInjectorStatus, ...action.payload } };
        case 'SET_GATEWAY_FORWARD':
            return { ...state, gatewayForwardedSessionId: action.payload };
        case 'CLEAR_ALL':
            return initialState;
        default:
            return state;
    }
}

function generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
}

export function useHealthTracker() {
    const [state, dispatch] = useReducer(healthReducer, initialState);

    // === Session Tracking ===
    const trackSessionCreate = useCallback((sessionId: string) => {
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'SESSION_CREATE',
                timestamp: new Date(),
                success: true,
                details: { sessionId: sessionId.slice(0, 8) + '...' },
            },
        });
        dispatch({ type: 'UPDATE_CRUD_STATUS', payload: { create: 'success' } });
    }, []);

    const trackSessionLoad = useCallback((sessionId: string, success: boolean, error?: string) => {
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'SESSION_LOAD',
                timestamp: new Date(),
                success,
                details: { sessionId: sessionId.slice(0, 8) + '...', error },
            },
        });
        dispatch({ type: 'UPDATE_CRUD_STATUS', payload: { read: success ? 'success' : 'not_found' } });
    }, []);

    const trackSessionRestore = useCallback((data: {
        hasDisplayData: boolean;
        hasBoqData: boolean;
        hasSldData: boolean;
        hasMessages: boolean;
        messageCount?: number;
    }) => {
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'SESSION_RESTORE',
                timestamp: new Date(),
                success: data.hasDisplayData || data.hasBoqData,
                details: data,
            },
        });
    }, []);

    // === CRUD Operations ===
    const trackCrudCreate = useCallback((sessionId: string) => {
        dispatch({ type: 'UPDATE_CRUD_STATUS', payload: { create: 'success' } });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'CRUD_CREATE',
                timestamp: new Date(),
                success: true,
                details: { sessionId: sessionId.slice(0, 8) + '...' },
            },
        });
    }, []);

    const trackCrudRead = useCallback((sessionId: string, found: boolean) => {
        dispatch({ type: 'UPDATE_CRUD_STATUS', payload: { read: found ? 'success' : 'not_found' } });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'CRUD_READ',
                timestamp: new Date(),
                success: found,
                details: { sessionId: sessionId.slice(0, 8) + '...', found },
            },
        });
    }, []);

    const trackCrudUpdate = useCallback((sessionId: string, success: boolean) => {
        dispatch({ type: 'UPDATE_CRUD_STATUS', payload: { update: success ? 'success' : 'failed' } });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'CRUD_UPDATE',
                timestamp: new Date(),
                success,
                details: { sessionId: sessionId.slice(0, 8) + '...' },
            },
        });
    }, []);

    const trackCrudDelete = useCallback((sessionId: string, success: boolean) => {
        dispatch({ type: 'UPDATE_CRUD_STATUS', payload: { delete: success ? 'success' : 'failed' } });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'CRUD_DELETE',
                timestamp: new Date(),
                success,
                details: { sessionId: sessionId.slice(0, 8) + '...' },
            },
        });
    }, []);

    // === Edit Injector ===
    const trackEditIntent = useCallback((intent: 'CREATE' | 'EDIT', query: string) => {
        dispatch({ type: 'UPDATE_EDIT_STATUS', payload: { intent, query: query.slice(0, 50) + '...' } });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'EDIT_INTENT',
                timestamp: new Date(),
                success: true,
                details: { intent, query: query.slice(0, 50) + '...' },
            },
        });
    }, []);

    const trackEditMerge = useCallback((success: boolean, fallbackReason?: string) => {
        dispatch({
            type: 'UPDATE_EDIT_STATUS',
            payload: { mergeResult: success ? 'success' : 'fallback', fallbackReason }
        });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'EDIT_MERGE',
                timestamp: new Date(),
                success,
                details: { result: success ? 'MERGED' : 'FALLBACK', fallbackReason },
            },
        });
    }, []);

    const trackPreviousDesignLoad = useCallback((loaded: boolean) => {
        dispatch({ type: 'UPDATE_EDIT_STATUS', payload: { previousDesignLoaded: loaded } });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'PREVIOUS_DESIGN_LOAD',
                timestamp: new Date(),
                success: loaded,
                details: { loaded },
            },
        });
    }, []);

    // === API Tracking ===
    const trackApiRequest = useCallback((endpoint: string, options: {
        method?: string;
        sessionId: string | null;
        projectName?: string | null;
        body?: unknown;
    }) => {
        const requestInfo: RequestInfo = {
            endpoint,
            method: options.method || 'POST',
            sentSessionId: options.sessionId,
            sentProjectName: options.projectName || null,
            body: options.body,
            timestamp: new Date(),
        };
        dispatch({ type: 'SET_LAST_REQUEST', payload: requestInfo });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'API_REQUEST',
                timestamp: new Date(),
                success: true,
                details: {
                    endpoint,
                    sessionId: options.sessionId?.slice(0, 8) + '...',
                    hasBody: !!options.body,
                },
            },
        });

        // Check gateway forwarding
        if (endpoint.includes('session_id=')) {
            dispatch({ type: 'SET_GATEWAY_FORWARD', payload: true });
        }
    }, []);

    const trackApiResponse = useCallback((status: number, data: any, endpoint?: string) => {
        const responseInfo: ResponseInfo = {
            status,
            receivedSessionId: data?.session_id || data?.metadata?.session_id || null,
            receivedProjectName: data?.project_name || data?.metadata?.project_name || null,
            hasBoqData: !!(data?.metadata?.boq_data || data?.boq_data),
            hasDisplayData: !!(data?.metadata?.display_data || data?.display_data),
            hasSldData: !!(data?.metadata?.sld_data || data?.sld_data),
            hasMessages: !!(data?.messages && data.messages.length > 0),
            timestamp: new Date(),
        };
        dispatch({ type: 'SET_LAST_RESPONSE', payload: responseInfo });
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'API_RESPONSE',
                timestamp: new Date(),
                success: status >= 200 && status < 300,
                details: {
                    status,
                    endpoint,
                    hasBoqData: responseInfo.hasBoqData,
                    hasDisplayData: responseInfo.hasDisplayData,
                },
            },
        });
    }, []);

    const trackError = useCallback((error: string, context?: string) => {
        dispatch({
            type: 'ADD_EVENT',
            payload: {
                id: generateEventId(),
                type: 'API_ERROR',
                timestamp: new Date(),
                success: false,
                details: { error, context },
            },
        });
        if (state.lastResponse) {
            dispatch({
                type: 'SET_LAST_RESPONSE',
                payload: { ...state.lastResponse, errorMessage: error },
            });
        }
    }, [state.lastResponse]);

    // === Clear ===
    const clearAll = useCallback(() => {
        dispatch({ type: 'CLEAR_ALL' });
    }, []);

    // === Computed Values ===
    const isHealthy = useMemo(() => {
        const crudOk = state.crudStatus.create !== 'failed' &&
            state.crudStatus.read !== 'failed' &&
            state.crudStatus.update !== 'failed';
        const apiOk = !state.lastResponse?.errorMessage &&
            (state.lastResponse?.status ?? 200) < 400;
        return crudOk && apiOk;
    }, [state.crudStatus, state.lastResponse]);

    return {
        // State
        events: state.events,
        lastRequest: state.lastRequest,
        lastResponse: state.lastResponse,
        crudStatus: state.crudStatus,
        editInjectorStatus: state.editInjectorStatus,
        gatewayForwardedSessionId: state.gatewayForwardedSessionId,
        isHealthy,

        // Session
        trackSessionCreate,
        trackSessionLoad,
        trackSessionRestore,

        // CRUD
        trackCrudCreate,
        trackCrudRead,
        trackCrudUpdate,
        trackCrudDelete,

        // Edit
        trackEditIntent,
        trackEditMerge,
        trackPreviousDesignLoad,

        // API
        trackApiRequest,
        trackApiResponse,
        trackError,

        // Utility
        clearAll,
    };
}

export type HealthTracker = ReturnType<typeof useHealthTracker>;
