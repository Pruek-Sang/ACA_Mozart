import { Send } from 'lucide-react';
import { useState, useRef, KeyboardEvent } from 'react';

interface InputBarProps {
    onSend: (text: string) => void;
    disabled?: boolean;
}

export function InputBar({ onSend, disabled }: InputBarProps) {
    const [text, setText] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = () => {
        if (text.trim() && !disabled) {
            onSend(text.trim());
            setText('');
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInput = () => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    };

    return (
        <footer className="bg-bgSecondary/80 backdrop-blur-sm border-t border-gray-800 p-4 shrink-0">
            <div className="max-w-3xl mx-auto relative">
                <div className="flex gap-3 items-end bg-bgInput p-2 rounded-xl border border-gray-700 focus-within:border-accentMozart transition-colors shadow-lg">
                    <textarea
                        ref={textareaRef}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onInput={handleInput}
                        onKeyDown={handleKeyDown}
                        rows={1}
                        className="flex-1 bg-transparent text-white placeholder-gray-500 px-3 py-2 focus:outline-none resize-none max-h-32"
                        placeholder="พิมพ์ข้อความ... (เช่น 'ออกแบบไฟห้องครัว')"
                        disabled={disabled}
                    />
                    <button
                        onClick={handleSend}
                        disabled={disabled || !text.trim()}
                        className="p-2.5 rounded-lg bg-accentMozart hover:bg-indigo-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
                <div className="text-center mt-2">
                    <span className="text-[10px] text-gray-600">
                        Powered by ACA Mozart Gateway (Port 8000)
                    </span>
                </div>
            </div>
        </footer>
    );
}
