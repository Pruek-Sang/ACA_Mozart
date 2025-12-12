import { useRef, useEffect } from 'react';
import { Bot } from 'lucide-react';
import type { Message } from '../types/gateway';
import { MessageBubble } from './MessageBubble';
import { QuickChips } from './QuickChips';

interface ChatPaneProps {
    messages: Message[];
    isTyping: boolean;
    onQuickSelect: (text: string) => void;
}

export function ChatPane({ messages, isTyping, onQuickSelect }: ChatPaneProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const showQuickChips = messages.length === 0;

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    return (
        <main
            ref={containerRef}
            className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth"
        >
            {/* Welcome Message */}
            {messages.length === 0 && (
                <div className="flex gap-4 max-w-3xl mx-auto animate-fadeIn">
                    <div className="w-8 h-8 rounded-full bg-bgSecondary border border-gray-700 flex items-center justify-center shrink-0 mt-1">
                        <Bot className="w-5 h-5 text-accentMozart" />
                    </div>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-textSecondary">System</span>
                        </div>
                        <div className="bg-botBubble text-gray-100 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm max-w-[85%] md:max-w-[75%] leading-relaxed">
                            สวัสดีค่ะ! Drafta (ในร่าง Avatar) พร้อมรับคำสั่งแล้วค่ะ 🤖
                            <br />
                            ลองใช้คำสั่งตัวอย่าง หรือพิมพ์คำถามที่ต้องการได้เลย
                        </div>
                    </div>
                </div>
            )}

            {/* Quick Chips */}
            <QuickChips visible={showQuickChips} onSelect={onQuickSelect} />

            {/* Messages */}
            {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
            ))}

            {/* Typing Indicator */}
            {isTyping && (
                <div className="flex gap-4 max-w-3xl mx-auto animate-fadeIn">
                    <div className="w-8 h-8 rounded-full bg-bgSecondary border border-gray-700 flex items-center justify-center shrink-0 mt-1">
                        <Bot className="w-5 h-5 text-gray-400" />
                    </div>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-textSecondary">Bot</span>
                        </div>
                        <div className="bg-botBubble text-gray-100 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm inline-block">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
