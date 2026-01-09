import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, History, X } from 'lucide-react';
import type { ChatMessage } from '../types';
import { cn } from '../lib/utils';
import { ChatBubble } from './ChatBubble';
import { HistoryPanel } from './HistoryPanel';

// Mock history data for demonstration
const MOCK_HISTORY: Array<{
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
}> = [
        {
            fromVersion: 1,
            toVersion: 2,
            timestamp: new Date().toISOString(),
            summary: "เพิ่มแอร์ 18000 BTU ห้องนอน 1",
            changes: [
                { field: "ac_bedroom1", label: "แอร์ห้องนอน 1", before: "12000 BTU", after: "18000 BTU", changeType: "modified" }
            ],
            changeCount: 1
        }
    ];

interface ChatPanelProps {
    messages: ChatMessage[];
    onSendMessage: (text: string) => void;
    isLoading: boolean;
    revisionHistory?: typeof MOCK_HISTORY;
}

/**
 * ChatPanel - หน้าต่างแชทสำหรับสั่งงาน
 * 
 * ตำแหน่ง: ซ้ายบน
 * หน้าที่: รับคำสั่งจาก User และแสดง Response/Error
 * 🆕 Added: History panel toggle
 */
export const ChatPanel: React.FC<ChatPanelProps> = ({
    messages,
    onSendMessage,
    isLoading,
    revisionHistory = []
}) => {
    const [input, setInput] = useState('');
    const [showHistory, setShowHistory] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;
        onSendMessage(input);
        setInput('');
    };

    return (
        <div className="flex flex-col h-full bg-slate-950 border-r border-slate-800 relative">
            {/* Chat Header with History Toggle */}
            <div className="p-4 border-b border-slate-800 bg-slate-900 flex items-center justify-between">
                <h2 className="text-slate-400 font-mono text-xs uppercase tracking-widest flex items-center gap-2">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                    Command Interface
                </h2>

                {/* History Toggle Button */}
                <button
                    onClick={() => setShowHistory(!showHistory)}
                    className={cn(
                        "flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors",
                        showHistory
                            ? "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                            : "text-slate-500 hover:text-sky-400 hover:bg-slate-800"
                    )}
                    data-testid="history-toggle-button"
                >
                    <History size={12} />
                    ประวัติ
                </button>
            </div>

            {/* History Panel Sidebar */}
            {showHistory && (
                <div className="absolute right-0 top-12 bottom-0 w-80 bg-slate-900 border-l border-slate-700 z-10 flex flex-col">
                    <div className="flex items-center justify-between p-3 border-b border-slate-800">
                        <span className="text-sm text-slate-300 font-medium">ประวัติการแก้ไข</span>
                        <button
                            onClick={() => setShowHistory(false)}
                            className="p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-slate-300"
                        >
                            <X size={14} />
                        </button>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        <HistoryPanel
                            history={revisionHistory.length > 0 ? revisionHistory : MOCK_HISTORY}
                            currentVersion={revisionHistory.length + 1}
                            className="border-0"
                        />
                    </div>
                </div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-slate-500 text-center mt-10">
                        <p className="font-mono text-sm">READY FOR INPUT</p>
                        <p className="text-xs mt-2">System: พิมพ์คำสั่ง เช่น "ออกแบบบ้าน 2 ชั้น"</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <ChatBubble key={`msg-${msg.timestamp?.getTime() || idx}`} message={msg} />
                ))}

                {/* Loading Indicator */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center gap-2 text-slate-400">
                            <Loader2 size={16} className="animate-spin" />
                            <span className="font-mono text-sm">กำลังประมวลผล...</span>
                        </div>
                    </div>
                )}

                {/* Auto-scroll anchor */}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-slate-900">
                <div className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="พิมพ์คำสั่ง (เช่น 'ออกแบบบ้าน 2 ชั้น')..."
                        disabled={isLoading}
                        className={cn(
                            "w-full bg-slate-950 text-white pl-4 pr-12 py-3 rounded-lg",
                            "border border-slate-700 focus:border-sky-500 focus:outline-none",
                            "font-mono text-sm placeholder-slate-600",
                            "transition-colors duration-200",
                            isLoading && "opacity-50 cursor-not-allowed"
                        )}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className={cn(
                            "absolute right-2 top-2 p-2 rounded",
                            "text-slate-400 hover:text-white hover:bg-slate-800",
                            "transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        )}
                    >
                        <Send size={18} />
                    </button>
                </div>
            </form>
        </div>
    );
};
