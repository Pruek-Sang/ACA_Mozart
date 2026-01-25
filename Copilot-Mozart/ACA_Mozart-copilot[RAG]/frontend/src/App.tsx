import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { ChatPanel } from './components/ChatPanel';
import { ContextPanel } from './components/ContextPanel';
import { ResultViewer } from './components/ResultViewer';
import { LoginPage } from './components/LoginPage';
import { FeedbackModal } from './components/FeedbackModal';
import { ProjectSelector } from './components/ProjectSelector';
import { HealthPanel } from './components/HealthPanel';  // 🩺 Health Panel
import { useHealthTracker } from './hooks/useHealthTracker';  // 🩺 Health Tracker
import type {
  ChatMessage,
  SiteContext,
  DesignResult,
  SLDData,
  BOQData  // 🆕 BOQ data from backend
} from './types';
import { classifyError } from './lib/utils';
import { supabase, signOut } from './lib/supabase';
import { askDesign, startSession } from './lib/api';
import { logger } from './lib/logger';
import { LogOut, User as UserIcon, MessageSquareHeart, FolderOpen, Trash2, Undo2 } from 'lucide-react';

/**
 * App - Main Application Controller
 * 
 * Layout: Split Screen (Left: Chat+Context, Right: Results)
 * Logic: Handles API calls, state management, and Authentication
 * 
 * ⚠️ NO BLACK BOX: All errors are classified and displayed
 */
function App() {
  // === AUTH STATE ===
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isGuestMode, setIsGuestMode] = useState(false);  // 🆕 Guest mode state

  // === CHAT STATE ===
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'system',
      content: '🔧 Mozart Design System พร้อมใช้งาน\n\nพิมพ์คำสั่ง เช่น:\n• "ออกแบบบ้าน 2 ชั้น ห้องนอน 2 ห้องน้ำ 2"\n• "เพิ่มแอร์ 12000 BTU ห้องนอน 1"',
      timestamp: new Date()
    }
  ]);

  // === SITE CONTEXT STATE ===
  const [context, setContext] = useState<SiteContext>({
    distance_to_transformer: 'less_than_50m',
    installation_area: 'indoor',
    panel_type: 'main',
    conduit_grouping: '1'
  });

  // === UI STATE ===
  const [isDirty, setIsDirty] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [resultData, setResultData] = useState<DesignResult | null>(null);
  const [sldData, setSldData] = useState<SLDData | null>(null);  // 🆕 SLD data
  const [boqData, setBoqData] = useState<BOQData | null>(null);  // 🆕 BOQ data from backend
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);  // 🆕 Feedback modal

  // === 🆕 SESSION STATE ===
  // 🔧 FIX: Initialize from localStorage to persist across refresh
  const [sessionId, setSessionId] = useState<string | null>(() => {
    const saved = localStorage.getItem('mozart_session_id');
    return saved || null;
  });
  // 🔧 FIX 2026-01-25: Use ref to ensure handleSubmit always has latest sessionId
  // React useState is async, so we need ref for immediate reads
  const sessionIdRef = useRef<string | null>(sessionId);
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);
  
  const [projectName, setProjectName] = useState(() => {
    const saved = localStorage.getItem('mozart_project_name');
    return saved || 'บ้านนายสมหญิง';
  });
  const [isSessionLoading, setIsSessionLoading] = useState(true);

  // === 🩺 HEALTH TRACKER ===
  const healthTracker = useHealthTracker();
  const showDebug = useMemo(() => globalThis.location.search.includes('debug=true'), []);

  // === AUTH EFFECT ===
  useEffect(() => {
    // ดึง Session ปัจจุบัน
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setIsAuthLoading(false);

      if (session) {
        logger.info('App initialized: Auth session found', { email: session.user.email });
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  // Track changes in Context to show "MODIFIED" badge
  useEffect(() => {
    setIsDirty(true);
  }, [context]);

  // === 🆕 PERSIST SESSION TO LOCALSTORAGE ===
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('mozart_session_id', sessionId);
    }
  }, [sessionId]);

  useEffect(() => {
    if (projectName) {
      localStorage.setItem('mozart_project_name', projectName);
    }
  }, [projectName]);

  // === 🆕 AUTO-START SESSION (only if no saved session) ===
  useEffect(() => {
    // 1. Wait until Auth is fully loaded
    if (isAuthLoading) {
      return;
    }

    // 2. Skip if not logged in AND not in Guest mode
    if (!session && !isGuestMode) {
      console.log('[SESSION-DEBUG] No auth session and not guest, skipping.');
      return;
    }

    const fetchSessionData = async (id: string) => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || '';
        const token = session?.access_token;
        logger.debug(`[SESSION] Fetching data for ${id}...`);

        const res = await fetch(`${API_URL}/api/v1/session/${id}/data`, {
          headers: {
            ...(token && { 'Authorization': `Bearer ${token}` })
          }
        });

        // 🆕 FIX: Handle failed fetch (404 = stale session ID)
        if (!res.ok) {
          console.warn(`[SESSION-FIX] ❌ Fetch failed (${res.status}) for ${id.slice(0, 8)}...`);
          console.warn('[SESSION-FIX] 🧹 Clearing stale localStorage and creating new session...');

          // Clear stale data
          localStorage.removeItem('mozart_session_id');
          localStorage.removeItem('mozart_project_name');
          setSessionId(null);

          // Create new session
          try {
            const result = await startSession();
            setSessionId(result.session_id);
            setProjectName(result.project_name || 'บ้านนายสมหญิง');
            console.log(`[SESSION-FIX] ✅ New session created: ${result.session_id.slice(0, 8)}...`);
            logger.info('[SESSION-FIX] Created new session after stale ID', { sessionId: result.session_id });
          } catch (createError: unknown) {
            const errMsg = createError instanceof Error ? createError.message : String(createError);
            console.error('[SESSION-FIX] ❌ Failed to create new session:', errMsg);
            logger.error('❌ Failed to create new session', { error: errMsg });
          }

          setIsSessionLoading(false);
          return;
        }

        // Success path - restore data
        const data = await res.json();
        logger.info('[SESSION-RESTORE] Data restored', { sessionId: id, projectName: data.project_name });

        // 🆕 Verbose logging for debugging
        console.log('[SESSION-RESTORE] === Session Data ===');
        console.log('[SESSION-RESTORE] Project:', data.project_name);
        console.log('[SESSION-RESTORE] Has MCP Response:', !!data.mcp_response);
        console.log('[SESSION-RESTORE] Has Display Data:', !!data.mcp_response?.display_data);
        console.log('[SESSION-RESTORE] Has BOQ Data:', !!data.mcp_response?.boq_data);
        if (data.mcp_response?.boq_data) {
          console.log('[SESSION-RESTORE] BOQ Price Source:', data.mcp_response.boq_data.price_source);
          console.log('[SESSION-RESTORE] BOQ Sections:', data.mcp_response.boq_data.sections?.length || 0);
        }

        // 🩺 Track Session Restore Success
        healthTracker.trackSessionRestore({
          hasDisplayData: !!data.mcp_response?.display_data,
          hasBoqData: !!data.mcp_response?.boq_data,
          hasSldData: !!data.mcp_response?.sld_data,
          hasMessages: (data.messages?.length || 0) > 0,
          messageCount: data.messages?.length || 0
        });
        healthTracker.trackCrudRead(id, true);

        if (data.project_name) setProjectName(data.project_name);

        // Restore Result Data
        if (data.mcp_response?.display_data) {
          const displayData = data.mcp_response.display_data;
          setResultData({
            success: true,
            message: 'Design restored',
            data: {
              loads: (displayData.circuits || []).map((ckt: Record<string, unknown>) => ({
                room_name: ckt.room || ckt.floor || '',
                device_name: ckt.circuit_name,
                power_kw: ckt.total_kw,
                current_a: ckt.total_current,
                breaker_size: ckt.breaker_rating,
                wire_size: `${ckt.wire_size} mm²`,
                conduit_size: ckt.conduit_size,
                voltage_drop_percent: ckt.vd_percent,
                // Full mapping for PDF support
                load_va_l1: ckt.load_va_l1 || ckt.total_va || 0,
                load_va_l2: ckt.load_va_l2 || 0,
                load_va_l3: ckt.load_va_l3 || 0,
                total_va: ckt.total_va || 0,
                breaker_type: ckt.breaker_type || 'MCB',
                breaker_poles: ckt.breaker_poles || 1,
                breaker_ic_ka: ckt.breaker_ic_ka || 6,
                wire_type: ckt.wire_type || 'IEC01',
                conduit_type: ckt.conduit_type || 'PVC',
                requires_rcbo: ckt.requires_rcbo || false,
                remark: ckt.remark || '',
              })),
              warnings: displayData.warnings || [],
              explainable_warnings: displayData.explainable_warnings,
              assumptions: displayData.assumptions,
              total_power_kw: displayData.total_kw,
              main_breaker: Number.parseInt(displayData.main_breaker) || 0,
              audit_table: data.mcp_response?.audit_results,
              project_name: displayData.project_name,
              demand_factor: displayData.demand_factor,
              main_cb_type: displayData.main_cb_type,
              main_feeder_size: displayData.main_feeder_size,
              main_feeder_type: displayData.main_feeder_type,
              main_raceway_size: displayData.main_raceway_size,
              main_raceway_type: displayData.main_raceway_type,
              // 🆕 QC Certificate (for session restore)
              qc_certificate: displayData.qc_certificate,
            }
          });
        }

        // Restore SLD
        if (data.mcp_response?.sld_data) {
          setSldData(data.mcp_response.sld_data);
        }

        // 🆕 Restore BOQ Data
        if (data.mcp_response?.boq_data) {
          console.log('[SESSION-RESTORE] Setting BOQ data...');
          setBoqData(data.mcp_response.boq_data as BOQData);
        }

        // 🆕 Restore Chat Messages
        if (data.messages && Array.isArray(data.messages) && data.messages.length > 0) {
          console.log('[SESSION-RESTORE] Restoring messages:', data.messages.length);
          const restoredMessages = data.messages.map((msg: Record<string, unknown>) => ({
            role: msg.role as 'user' | 'assistant' | 'system',
            content: msg.content as string,
            timestamp: msg.timestamp ? new Date(msg.timestamp as string | number) : new Date()
          }));
          setMessages(restoredMessages);
        }

        setIsSessionLoading(false);
      } catch (e: unknown) {
        const errMsg = e instanceof Error ? e.message : String(e);
        console.error('[SESSION-FIX] ❌ Network error:', errMsg);
        logger.warn('[SESSION] Fetch failed', { error: errMsg, sessionId: id });

        // 🆕 FIX: Also handle network errors - clear stale and create new
        localStorage.removeItem('mozart_session_id');
        setSessionId(null);

        try {
          const result = await startSession();
          setSessionId(result.session_id);
          setProjectName(result.project_name || 'บ้านนายสมหญิง');
          console.log(`[SESSION-FIX] ✅ New session created after error: ${result.session_id.slice(0, 8)}...`);
        } catch {
          // Intentionally empty - all session creation attempts failed
          console.error('[SESSION-FIX] ❌ All session attempts failed');
        }

        setIsSessionLoading(false);
      }
    };

    const initSession = async () => {
      // ✅ Case 1: Check LocalStorage FIRST (Priority)
      const savedSessionId = localStorage.getItem('mozart_session_id');

      // Use saved ID if available AND matches current state (or state is empty)
      const targetId = savedSessionId || sessionId;

      if (targetId) {
        // Restore existing session
        if (targetId !== sessionId) setSessionId(targetId); // Sync state
        await fetchSessionData(targetId);
      } else {
        // ✅ Case 2: Only create NEW session if absolutely no ID exists
        try {
          logger.info('🚀 Starting new session...', { from: 'initSession' });
          const result = await startSession();
          setSessionId(result.session_id);
          setProjectName(result.project_name || 'บ้านนายสมหญิง');
          logger.info('✅ Session started successfully', { sessionId: result.session_id });
        } catch (error: unknown) {
          const errMsg = error instanceof Error ? error.message : String(error);
          logger.error('❌ Failed to create session', { error: errMsg });
        } finally {
          setIsSessionLoading(false);
        }
      }
    };

    initSession();
  }, [isAuthLoading, session, isGuestMode, sessionId]); // Run when Auth status settles OR Guest mode activated OR SessionID changes

  // === LOGOUT HANDLER ===
  const handleLogout = async () => {
    try {
      await signOut();
      setMessages([{
        role: 'system',
        content: '👋 ออกจากระบบแล้ว',
        timestamp: new Date()
      }]);
      setResultData(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // === 🆕 CLEAR HANDLER (Soft Delete) ===
  const handleClear = async () => {
    const confirmClear = window.confirm(
      '⚠️ ต้องการล้างข้อมูลทั้งหมดหรือไม่?\n\n' +
      '- ข้อความแชททั้งหมดจะหายไป\n' +
      '- ผลการคำนวณจะหายไป\n' +
      '- ข้อมูลจะถูกเก็บไว้ในประวัติ (ไม่ลบถาวร)'
    );

    if (!confirmClear) return;

    try {
      // 1. Call soft-delete API (mark as deleted in DB)
      if (sessionId) {
        const apiUrl = import.meta.env.VITE_API_URL || '';
        await fetch(`${apiUrl}/api/v1/session/${sessionId}?confirm=CONFIRM`, {
          method: 'DELETE',
        });
        console.log('[CLEAR] Soft-deleted session:', sessionId);
      }

      // 2. Clear all UI state
      setMessages([{
        role: 'system',
        content: '🧹 ล้างข้อมูลเรียบร้อย! พร้อมเริ่มต้นใหม่',
        timestamp: new Date()
      }]);
      setResultData(null);
      setSldData(null);
      setBoqData(null);

      // 3. Clear localStorage and create new session
      console.log('[CLEAR] Clear request sent to API');

    } catch (error) {
      console.error('[CLEAR] Error:', error);
      // Still clear UI even if API fails
      setMessages([{
        role: 'system',
        content: '🧹 ล้างข้อมูล UI แล้ว (แต่อาจมีข้อมูลเก่าใน server)',
        timestamp: new Date()
      }]);
      setResultData(null);
      setSldData(null);
      setBoqData(null);
    } finally {
      // 3. Always clear localStorage and reset session ID
      localStorage.removeItem('mozart_session_id');
      localStorage.removeItem('mozart_project_name');
      setSessionId(null);
      setProjectName('โปรเจกต์ใหม่');
      console.log('[CLEAR] Local session cleared');
    }
  };

  // === 🆕 PHASE 5: UNDO HANDLER ===
  const handleUndo = async () => {
    if (!sessionId) {
      console.log('[UNDO] No session to undo');
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/undo?session_id=${sessionId}`, {
        method: 'POST',
        headers: {
          ...(session?.access_token && { 'Authorization': `Bearer ${session.access_token}` })
        }
      });

      const data = await response.json();

      if (data.success && data.data) {
        // Refresh the page with restored data
        setMessages(prev => [...prev, {
          role: 'system',
          content: data.message || '↩️ ย้อนกลับสำเร็จ',
          timestamp: new Date()
        }]);

        // TODO: Trigger recalculation with restored loads
        console.log('[UNDO] Restored:', data.data);
      } else {
        setMessages(prev => [...prev, {
          role: 'system',
          content: data.message || '⚠️ ไม่สามารถย้อนกลับได้',
          timestamp: new Date()
        }]);
      }
    } catch (e) {
      console.error('[UNDO] Error:', e);
      setMessages(prev => [...prev, {
        role: 'system',
        content: '❌ เกิดข้อผิดพลาดในการย้อนกลับ',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // === FEEDBACK HANDLER ===
  const handleFeedbackSubmit = async (feedback: {
    type: string;
    rating: string | null;
    message: string;
  }) => {
    try {
      console.log('[FEEDBACK] Submitting to API:', feedback);

      // 🆕 Send to backend API
      const token = await (await import('./lib/supabase')).supabase.auth.getSession()
        .then(res => res.data.session?.access_token);

      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          ...feedback,
          session_id: sessionId,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        console.warn('[FEEDBACK] API not available, logged locally');
      } else {
        console.log('[FEEDBACK] Submitted successfully');
      }
    } catch (error) {
      console.error('[FEEDBACK] Submit error (fallback to local):', error);
      // Don't throw - allow graceful degradation
    }
  };

  // === CORE LOGIC: API CALL ===
  const handleSubmit = useCallback(async (userPrompt: string) => {
    // 1. Add User Message to Chat
    const newUserMsg: ChatMessage = {
      role: 'user',
      content: userPrompt,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);
    setIsDirty(false);

    try {
      // 🔧 FIX 2026-01-25: Use ref for immediate access to latest sessionId
      // React state might be stale in callbacks due to batched updates
      const currentSessionId = sessionIdRef.current;
      console.log('[SESSION-DEBUG] handleSubmit - sessionId ref:', currentSessionId);
      console.log('[SESSION-DEBUG] handleSubmit - sessionId state:', sessionId);
      console.log('[SESSION-DEBUG] handleSubmit - localStorage:', localStorage.getItem('mozart_session_id'));

      // 🩺 Track API Request
      healthTracker.trackApiRequest('/api/v1/ask', {
        method: 'POST',
        sessionId: currentSessionId,
        body: { query: userPrompt }
      });

      // 2. Call API via centralized api.ts module (with session_id)
      const data = await askDesign({
        query: userPrompt,
        language: 'th',
        site_context: context
      }, currentSessionId || undefined);

      // 🩺 Track API Response
      healthTracker.trackApiResponse(200, data, '/api/v1/ask');

      console.log('[SESSION-DEBUG] askDesign returned, checking metadata.display_data:', !!data.metadata?.display_data);

      // 3. Add Success Message
      const sysMsg: ChatMessage = {
        role: 'assistant',
        content: data.answer || '✅ คำนวณเสร็จสิ้น ดูผลลัพธ์ทางขวา',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, sysMsg]);

      // 4. Update Result Data from Computed Data Layer
      const displayData = data.metadata?.display_data;
      if (displayData) {
        // 🆕 Use structured data from Backend
        console.log('[DATA-DEBUG] displayData.circuits:', displayData.circuits?.length || 0, 'items');
        console.log('[DATA-DEBUG] Sample circuit:', displayData.circuits?.[0]);

        setResultData({
          success: true,
          message: 'Design calculated',
          data: {
            loads: (displayData.circuits || []).map((ckt: {
              room?: string;
              floor?: string;
              circuit_name: string;
              total_kw: number;
              total_current: number;
              total_watts?: number;
              total_va?: number;
              load_va_l1?: number;
              load_va_l2?: number;
              load_va_l3?: number;
              breaker_rating: number;
              breaker_type?: string;
              breaker_poles?: number;
              breaker_ic_ka?: number;
              breaker_af?: number;
              breaker_at?: number;
              wire_size: string;
              wire_size_l?: string;
              wire_size_n?: string;
              wire_size_grd?: string;
              wire_type?: string;
              ground_size?: string;
              conduit_size?: string;
              conduit_type?: string;
              vd_percent?: number;
              requires_rcbo?: boolean;
              remark?: string;
            }) => ({
              room_name: ckt.room || ckt.floor || '',
              device_name: ckt.circuit_name,
              power_kw: ckt.total_kw,
              current_a: ckt.total_current,
              breaker_size: ckt.breaker_rating,
              wire_size: `${ckt.wire_size} mm²`,
              conduit_size: ckt.conduit_size,
              voltage_drop_percent: ckt.vd_percent,
              // 🔧 FIX: Add fields needed by PDF
              load_va_l1: ckt.load_va_l1 || ckt.total_va || Math.round(ckt.total_kw * 1000) || 0,
              load_va_l2: ckt.load_va_l2 || 0,
              load_va_l3: ckt.load_va_l3 || 0,
              total_va: ckt.total_va || Math.round(ckt.total_kw * 1000) || 0,
              breaker_type: ckt.breaker_type || 'MCB',
              breaker_poles: ckt.breaker_poles || 1,
              breaker_ic_ka: ckt.breaker_ic_ka || 6,
              breaker_af: ckt.breaker_af || ckt.breaker_rating,
              breaker_at: ckt.breaker_at || ckt.breaker_rating,
              wire_size_l: ckt.wire_size_l || ckt.wire_size,
              wire_size_n: ckt.wire_size_n || ckt.wire_size,
              wire_size_grd: ckt.wire_size_grd || ckt.ground_size || '2.5',
              wire_type: ckt.wire_type || 'IEC01',
              ground_size: ckt.ground_size || '2.5',
              conduit_type: ckt.conduit_type || 'PVC',
              requires_rcbo: ckt.requires_rcbo || false,
              remark: ckt.remark || '',
            })),
            warnings: displayData.warnings || [],
            explainable_warnings: displayData.explainable_warnings,
            assumptions: displayData.assumptions,
            total_power_kw: displayData.total_kw,
            main_breaker: Number.parseInt(displayData.main_breaker) || 0,
            audit_table: data.metadata?.audit_results || undefined,
            // 🔧 FIX: Add summary fields for PDF
            project_name: displayData.project_name,
            demand_factor: displayData.demand_factor,
            main_cb_type: displayData.main_cb_type,
            main_feeder_size: displayData.main_feeder_size,
            main_feeder_type: displayData.main_feeder_type,
            main_raceway_size: displayData.main_raceway_size,
            main_raceway_type: displayData.main_raceway_type,
            // 🆕 QC Certificate
            qc_certificate: displayData.qc_certificate,
          }
        });


        // 🆕 Set SLD data from API response
        if (data.metadata?.sld_data) {
          setSldData(data.metadata.sld_data as unknown as SLDData);
        }

        // 🆕 Set BOQ data from API response
        if (data.metadata?.boq_data) {
          console.log('[BOQ-DEBUG] Setting boqData from API:', {
            sections: data.metadata.boq_data.sections?.length,
            price_source: data.metadata.boq_data.price_source
          });
          setBoqData(data.metadata.boq_data as BOQData);
        }
      } else if (data.metadata?.readable_report) {
        // Fallback: Backend ยังไม่ส่ง display_data (backward compat)
        setResultData({
          success: true,
          message: 'Design calculated (legacy mode)',
          data: {
            loads: [],
            warnings: ['ระบบยังใช้ format เก่า ดู Markdown report'],
          }
        });
      }

    } catch (error: unknown) {
      console.error('❌ ERROR OCCURRED:', error);
      const errorString = error instanceof Error ? error.message : String(error);
      logger.error('Design submission error', { error: errorString });

      // 🩺 Track Error
      healthTracker.trackError(errorString, 'API_CALL');

      const errorDetails = classifyError(error);

      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `${errorDetails.message}${errorDetails.details ? '\n\n' + errorDetails.details : ''}`,
        timestamp: new Date(),
        error_type: `${errorDetails.type}_error` as 'frontend_error' | 'backend_error' | 'network_error'
      };

      setMessages(prev => [...prev, errorMsg]);

    } finally {
      setIsLoading(false);
    }
  }, [context, sessionId, healthTracker]);

  // === AUTH LOADING STATE ===
  if (isAuthLoading) {
    return (
      <div className="h-screen w-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400 font-mono text-sm">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // === NOT LOGGED IN: SHOW LOGIN PAGE OR GUEST MODE ===
  if (!session && !isGuestMode) {
    return (
      <LoginPage
        onLoginSuccess={() => { }}
        onGuestMode={() => setIsGuestMode(true)}
      />
    );
  }

  // === LOGGED IN: SHOW MAIN APP ===
  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-200 font-sans flex flex-col overflow-hidden">

      {/* TOP BAR: User Info + Project Selector */}
      <div className="h-12 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <UserIcon size={16} />
            <span className="font-mono">{user?.email || '👤 Guest (24 ชม.)'}</span>
          </div>

          {/* 🆕 Project Selector (New/Load/Delete) */}
          <div className="border-l border-slate-700 pl-4">
            {isSessionLoading ? (
              <div className="flex items-center gap-2 text-slate-500 text-sm">
                <FolderOpen size={16} className="animate-pulse" />
                <span className="italic">กำลังโหลด...</span>
              </div>
            ) : (
              <ProjectSelector
                currentSessionId={sessionId}
                currentProjectName={projectName}
                onSessionChange={async (newSessionId, newProjectName) => {
                  console.log('[SESSION-SWITCH] Changing from', sessionId?.slice(0, 8), 'to', newSessionId.slice(0, 8));

                  // 🔧 FIX 2026-01-25: Update ref IMMEDIATELY (sync) before anything else!
                  // This ensures handleSubmit reads the correct sessionId even before re-render
                  sessionIdRef.current = newSessionId;

                  // 1. Clear old data immediately to prevent overlap
                  setResultData(null);
                  setSldData(null);
                  setMessages([{
                    role: 'system',
                    content: `📂 โหลดโปรเจค "${newProjectName}"...`,
                    timestamp: new Date()
                  }]);

                  // 2. Update state and localStorage
                  setSessionId(newSessionId);
                  setProjectName(newProjectName);
                  localStorage.setItem('mozart_session_id', newSessionId);
                  localStorage.setItem('mozart_project_name', newProjectName);

                  // 3. Actually load the new session's data!
                  try {
                    const token = session?.access_token;
                    const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/session/${newSessionId}/data`, {
                      headers: { ...(token && { 'Authorization': `Bearer ${token}` }) }
                    });

                    if (res.ok) {
                      const data = await res.json();
                      console.log('[SESSION-SWITCH] Loaded data:', data.project_name);

                      // Restore result data if exists
                      if (data.mcp_response?.display_data) {
                        const displayData = data.mcp_response.display_data;
                        setResultData({
                          success: true,
                          message: 'Design restored',
                          data: {
                            loads: (displayData.circuits || []).map((ckt: Record<string, unknown>) => ({
                              room_name: ckt.room || ckt.floor || '',
                              device_name: ckt.circuit_name,
                              power_kw: ckt.total_kw,
                              current_a: ckt.total_current,
                              breaker_size: ckt.breaker_rating,
                              wire_size: `${ckt.wire_size} mm²`,
                              conduit_size: ckt.conduit_size,
                              voltage_drop_percent: ckt.vd_percent,
                              total_va: ckt.total_va || 0,
                            })),
                            warnings: displayData.warnings || [],
                            total_power_kw: displayData.total_kw,
                            main_breaker: Number.parseInt(displayData.main_breaker) || 0,
                            audit_table: data.mcp_response?.audit_results,
                          }
                        });
                      }

                      // Restore messages
                      if (data.messages?.length > 0) {
                        setMessages(data.messages.map((msg: Record<string, unknown>) => ({
                          role: msg.role as 'user' | 'assistant' | 'system',
                          content: msg.content as string,
                          timestamp: msg.timestamp ? new Date(msg.timestamp as string) : new Date()
                        })));
                      } else {
                        setMessages([{
                          role: 'system',
                          content: `✅ โหลดโปรเจค "${newProjectName}" สำเร็จ!`,
                          timestamp: new Date()
                        }]);
                      }
                    } else {
                      console.warn('[SESSION-SWITCH] Failed to load data, status:', res.status);
                    }
                  } catch (e) {
                    console.error('[SESSION-SWITCH] Error loading session:', e);
                  }
                }}
                onNewProject={() => {
                  // Clear chat and results for new project
                  setMessages([{
                    role: 'system',
                    content: '🆕 เริ่มโปรเจกต์ใหม่! พิมพ์คำสั่งออกแบบได้เลย',
                    timestamp: new Date()
                  }]);
                  setResultData(null);
                  setSldData(null);
                }}
              />
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* 🆕 Phase 5: Undo Button */}
          <button
            onClick={handleUndo}
            disabled={isLoading}
            className="flex items-center gap-2 text-slate-400 hover:text-blue-400 text-sm transition-colors disabled:opacity-50"
            title="ย้อนกลับการแก้ไขล่าสุด"
          >
            <Undo2 size={16} />
            <span>ย้อนกลับ</span>
          </button>

          {/* 🆕 Clear Button */}
          <button
            onClick={handleClear}
            className="flex items-center gap-2 text-slate-400 hover:text-orange-400 text-sm transition-colors"
            title="ล้างข้อมูลทั้งหมด"
          >
            <Trash2 size={16} />
            <span>ล้างข้อมูล</span>
          </button>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-slate-400 hover:text-red-400 text-sm transition-colors"
          >
            <LogOut size={16} />
            <span>ออกจากระบบ</span>
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT COLUMN: Controls - 480px (+20% from original 400px) */}
        <div className="w-[480px] flex flex-col shrink-0">
          <div className="flex-1 min-h-0">
            <ChatPanel
              messages={messages}
              onSendMessage={handleSubmit}
              isLoading={isLoading}
              revisionHistory={resultData?.data?.revision_history || []}
            />
          </div>
          <ContextPanel
            context={context}
            onContextChange={setContext}
            isDirty={isDirty}
          />
        </div>

        {/* RIGHT COLUMN: Results */}
        <div className="flex-1">
          <ResultViewer
            data={resultData}
            isLoading={isLoading}
            sldData={sldData}
            boqData={boqData}  // 🆕 Pass BOQ data from backend
          />
        </div>
      </div>

      {/* 🆕 Floating Feedback Button */}
      <button
        onClick={() => setIsFeedbackOpen(true)}
        className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-3 
                   bg-gradient-to-r from-cyan-600 to-blue-600 
                   hover:from-cyan-500 hover:to-blue-500
                   text-white rounded-full shadow-lg shadow-cyan-500/25
                   transition-all z-40"
        title="ให้ Feedback"
      >
        <MessageSquareHeart size={20} />
        <span className="text-sm font-medium">Feedback</span>
      </button>

      {/* 🆕 Feedback Modal */}
      <FeedbackModal
        isOpen={isFeedbackOpen}
        onClose={() => setIsFeedbackOpen(false)}
        onSubmit={handleFeedbackSubmit}
      />

      {/* 🩺 Health Panel (Show only in debug mode: ?debug=true) */}
      {showDebug && (
        <HealthPanel
          tracker={healthTracker}
          localStorageSessionId={localStorage.getItem('mozart_session_id')}
          localStorageProjectName={localStorage.getItem('mozart_project_name')}
          reactSessionId={sessionId}
          reactProjectName={projectName}
        />
      )}
    </div>
  );
}

export default App;
