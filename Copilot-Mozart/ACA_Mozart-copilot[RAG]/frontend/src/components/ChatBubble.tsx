import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import Markdown from 'react-markdown';
import { cn } from '../lib/utils';
import type { ChatMessage } from '../types';

/**
 * ChatBubble - Individual message bubble with expand/collapse for long text
 * 
 * Features:
 * - Collapsible long messages (>150px)
 * - Preserves newlines with whitespace-pre-wrap
 * - Markdown rendering for bot messages
 * - Error type styling
 */

interface ChatBubbleProps {
    message: ChatMessage;
}

const MAX_HEIGHT = 150; // pixels before showing "show more"

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [needsExpand, setNeedsExpand] = useState(false);
    const contentRef = React.useRef<HTMLDivElement>(null);

    // Check if content needs expand button
    React.useEffect(() => {
        if (contentRef.current) {
            setNeedsExpand(contentRef.current.scrollHeight > MAX_HEIGHT);
        }
    }, [message.content]);

    const isUser = message.role === 'user';

    return (
        <div className={cn(
            "flex",
            isUser ? 'justify-end' : 'justify-start'
        )}>
            <div className={cn(
                "max-w-[85%] rounded-lg p-3 text-sm border relative",
                // User Message - Gradient blue
                isUser && "bg-gradient-to-br from-sky-500 to-blue-600 text-white border-transparent shadow-lg shadow-sky-500/20",
                // System/Assistant Normal
                !isUser && !message.error_type && "bg-slate-900 text-slate-300 border-slate-800",
                // Error Messages
                message.error_type === 'backend_error' && "bg-red-500/10 text-red-400 border-red-500/30 font-mono",
                message.error_type === 'frontend_error' && "bg-orange-500/10 text-orange-400 border-orange-500/30 font-mono",
                message.error_type === 'network_error' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/30 font-mono"
            )}>
                {/* Error Type Badge */}
                {message.error_type && (
                    <div className="text-[10px] uppercase tracking-wider mb-1 opacity-70">
                        {message.error_type.replace('_', ' ')}
                    </div>
                )}

                {/* Content Container */}
                <div
                    ref={contentRef}
                    className={cn(
                        "overflow-hidden transition-all duration-300",
                        !isExpanded && needsExpand && "max-h-[150px]"
                    )}
                    style={{
                        maxHeight: isExpanded ? 'none' : (needsExpand ? MAX_HEIGHT : 'none')
                    }}
                >
                    {/* Unified Markdown Rendering for BOTH User and Bot */}
                    <div className={cn(
                        "markdown-content",
                        isUser ? "text-white" : "text-slate-300"
                    )}>
                        <Markdown
                            components={{
                                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                                ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                                li: ({ children }) => <li className="mb-0.5">{children}</li>,
                                strong: ({ children }) => (
                                    <strong className={cn("font-bold", isUser ? "text-yellow-200" : "text-sky-200")}>
                                        {children}
                                    </strong>
                                ),
                                code: ({ children }) => (
                                    <code className={cn(
                                        "px-1 py-0.5 rounded font-mono text-xs",
                                        isUser ? "bg-white/20" : "bg-black/30"
                                    )}>
                                        {children}
                                    </code>
                                ),
                                pre: ({ children }) => (
                                    <pre className={cn(
                                        "p-2 rounded-md overflow-x-auto text-xs my-2",
                                        isUser ? "bg-white/10" : "bg-black/50"
                                    )}>
                                        {children}
                                    </pre>
                                ),
                                h1: ({ children }) => <h1 className="text-lg font-bold mb-2 opacity-90">{children}</h1>,
                                h2: ({ children }) => <h2 className="text-base font-semibold mb-2 opacity-90">{children}</h2>,
                                h3: ({ children }) => <h3 className="text-sm font-semibold mb-1 opacity-80">{children}</h3>,
                                h4: ({ children }) => <h4 className="text-xs font-bold uppercase tracking-wider mb-1 opacity-70">{children}</h4>,
                                a: ({ href, children }) => (
                                    <a href={href} target="_blank" rel="noopener noreferrer"
                                        className={cn("hover:underline", isUser ? "text-white underline" : "text-sky-400")}>
                                        {children}
                                    </a>
                                ),
                            }}
                        >
                            {message.content}
                        </Markdown>
                    </div>
                </div>

                {/* Gradient overlay when collapsed */}
                {needsExpand && !isExpanded && (
                    <div className={cn(
                        "absolute bottom-8 left-0 right-0 h-8 pointer-events-none",
                        isUser
                            ? "bg-gradient-to-t from-blue-600 to-transparent"
                            : "bg-gradient-to-t from-slate-900 to-transparent"
                    )} />
                )}

                {/* Expand/Collapse Button */}
                {needsExpand && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className={cn(
                            "mt-2 flex items-center gap-1 text-xs transition-colors",
                            isUser
                                ? "text-sky-200 hover:text-white"
                                : "text-slate-400 hover:text-slate-200"
                        )}
                    >
                        {isExpanded ? (
                            <>
                                <ChevronUp size={14} />
                                <span>ย่อข้อความ</span>
                            </>
                        ) : (
                            <>
                                <ChevronDown size={14} />
                                <span>ดูเพิ่มเติม</span>
                            </>
                        )}
                    </button>
                )}
            </div>
        </div>
    );
};

export default ChatBubble;
