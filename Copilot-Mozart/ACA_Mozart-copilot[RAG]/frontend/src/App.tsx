import { useState, useEffect } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { ChatPanel } from './components/ChatPanel';
import { ContextPanel } from './components/ContextPanel';
import { ResultViewer } from './components/ResultViewer';
import { LoginPage } from './components/LoginPage';
import { FeedbackModal } from './components/FeedbackModal';
import type {
  ChatMessage,
  SiteContext,
  DesignResult,
  SLDData
} from './types';
import { classifyError } from './lib/utils';
import { supabase, signOut } from './lib/supabase';
import { askDesign } from './lib/api';
import { LogOut, User as UserIcon, MessageSquareHeart } from 'lucide-react';

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
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);  // 🆕 Feedback modal

  // === AUTH EFFECT ===
  useEffect(() => {
    // ดึง Session ปัจจุบัน
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setIsAuthLoading(false);
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

  // === FEEDBACK HANDLER ===
  const handleFeedbackSubmit = async (feedback: {
    type: string;
    rating: string | null;
    message: string;
  }) => {
    try {
      console.log('[FEEDBACK] Submitted:', feedback);
      // TODO: Send to backend when API ready
      // await fetch('/api/feedback', { method: 'POST', body: JSON.stringify(feedback) });
    } catch (error) {
      console.error('[FEEDBACK] Submit error:', error);
      throw error;  // Re-throw to show error in modal
    }
  };

  // === CORE LOGIC: API CALL ===
  const handleSubmit = async (userPrompt: string) => {
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
      // 2. Call API via centralized api.ts module
      const data = await askDesign({
        query: userPrompt,
        language: 'th',
        site_context: context
      });

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
              breaker_rating: number;
              wire_size: string;
              conduit_size?: string;
              vd_percent?: number;
            }) => ({
              room_name: ckt.room || ckt.floor || '',
              device_name: ckt.circuit_name,
              power_kw: ckt.total_kw,
              current_a: ckt.total_current,
              breaker_size: ckt.breaker_rating,
              wire_size: `${ckt.wire_size} mm²`,
              conduit_size: ckt.conduit_size,
              voltage_drop_percent: ckt.vd_percent,
            })),
            warnings: displayData.warnings || [],
            explainable_warnings: displayData.explainable_warnings,
            assumptions: displayData.assumptions,
            total_power_kw: displayData.total_kw,
            main_breaker: Number.parseInt(displayData.main_breaker) || 0,
            audit_table: data.metadata?.audit_results || undefined,
          }
        });

        // 🆕 Set SLD data from API response
        if (data.metadata?.sld_data) {
          setSldData(data.metadata.sld_data as unknown as SLDData);
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

    } catch (error: any) {
      console.error('❌ ERROR OCCURRED:', error);

      const errorDetails = classifyError(error);

      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `${errorDetails.message}${errorDetails.details ? '\n\n' + errorDetails.details : ''}`,
        timestamp: new Date(),
        error_type: `${errorDetails.type}_error` as any
      };

      setMessages(prev => [...prev, errorMsg]);

    } finally {
      setIsLoading(false);
    }
  };

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

  // === NOT LOGGED IN: SHOW LOGIN PAGE ===
  if (!session) {
    return <LoginPage onLoginSuccess={() => { }} />;
  }

  // === LOGGED IN: SHOW MAIN APP ===
  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-200 font-sans flex flex-col overflow-hidden">

      {/* TOP BAR: User Info */}
      <div className="h-12 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <UserIcon size={16} />
          <span className="font-mono">{user?.email}</span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-slate-400 hover:text-red-400 text-sm transition-colors"
        >
          <LogOut size={16} />
          <span>ออกจากระบบ</span>
        </button>
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
    </div>
  );
}

export default App;
