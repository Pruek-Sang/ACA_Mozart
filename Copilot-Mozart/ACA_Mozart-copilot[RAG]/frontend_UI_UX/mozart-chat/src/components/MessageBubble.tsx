import { Bot, User, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import type { Message } from '../types/gateway';

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const [copied, setCopied] = useState(false);
    const isUser = message.role === 'user';

    const handleCopy = async () => {
        await navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const getModeColor = () => {
        if (message.mode === 'AMADEUS') return 'text-accentAmadeus';
        if (message.mode === 'MOZART') return 'text-accentMozart';
        return 'text-gray-400';
    };

    const getModeBadge = () => {
        if (!message.mode || message.mode === 'SYSTEM') return null;
        const colorClass =
            message.mode === 'AMADEUS'
                ? 'border-purple-500/50 text-purple-300 bg-purple-900/20'
                : 'border-indigo-500/50 text-indigo-300 bg-indigo-900/20';
        return (
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${colorClass}`}>
                {message.mode}
            </span>
        );
    };

    return (
        <div
            className={`flex gap-4 max-w-3xl mx-auto animate-fadeIn ${isUser ? 'flex-row-reverse' : ''
                }`}
        >
            {/* Avatar */}
            {isUser ? (
                <div className="w-8 h-8 rounded-full bg-userBubble flex items-center justify-center shrink-0 mt-1 shadow-lg shadow-blue-900/30">
                    <User className="w-5 h-5 text-white" />
                </div>
            ) : (
                <div className="w-8 h-8 rounded-full bg-bgSecondary border border-gray-700 flex items-center justify-center shrink-0 mt-1">
                    <Bot className={`w-5 h-5 ${getModeColor()}`} />
                </div>
            )}

            {/* Content */}
            <div className={`space-y-1 max-w-[85%] md:max-w-[75%]`}>
                <div className={`flex items-center gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
                    <span className="text-sm font-medium text-textSecondary">
                        {isUser ? 'You' : message.mode || 'System'}
                    </span>
                    {getModeBadge()}
                </div>
                <div className="relative group">
                    <div
                        className={`px-4 py-3 rounded-2xl shadow-sm leading-relaxed break-words ${isUser
                                ? 'bg-userBubble text-white rounded-tr-none'
                                : 'bg-botBubble text-gray-100 rounded-tl-none'
                            }`}
                    >
                        {isUser ? (
                            <p className="whitespace-pre-wrap">{message.content}</p>
                        ) : (
                            <div
                                className="markdown-body prose prose-invert max-w-none"
                                dangerouslySetInnerHTML={{ __html: formatMarkdown(message.content) }}
                            />
                        )}
                    </div>
                    {/* Copy button */}
                    {!isUser && (
                        <button
                            onClick={handleCopy}
                            className="absolute top-2 right-2 p-1.5 rounded-md hover:bg-white/10 text-textSecondary opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Copy"
                        >
                            {copied ? (
                                <Check className="w-4 h-4 text-green-400" />
                            ) : (
                                <Copy className="w-4 h-4" />
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

/** Simple markdown formatter (for demo, consider using marked or react-markdown) */
function formatMarkdown(text: string): string {
    return text
        .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}
