import { useState, useRef } from 'react';
import type { KeyboardEvent } from 'react';

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

    return (
        <div className="p-4">
            {/* Card Container - matching Uiverse.io design */}
            <div className="relative bg-white rounded-xl shadow-lg overflow-hidden">
                {/* Textarea */}
                <textarea
                    ref={textareaRef}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="p-4 pb-14 block w-full h-48 bg-gray-100 border-none text-gray-900 text-sm focus:outline-none focus:ring-0 resize-none placeholder-gray-500"
                    placeholder="💡 ลองถาม: (เช่น 'ออกแบบไฟห้องครัว')"
                    disabled={disabled}
                />

                {/* Bottom Toolbar - Uiverse.io style */}
                <div className="absolute bottom-0 inset-x-0 p-2 bg-white border-t border-gray-100">
                    <div className="flex justify-between items-center">
                        {/* Left Icons */}
                        <div className="flex items-center">
                            {/* Image Upload */}
                            <button
                                type="button"
                                className="inline-flex justify-center items-center w-10 h-10 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
                                title="แนบรูปภาพ"
                            >
                                <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                                </svg>
                            </button>

                            {/* Attach File */}
                            <button
                                type="button"
                                className="inline-flex justify-center items-center w-10 h-10 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
                                title="แนบไฟล์"
                            >
                                <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.112 2.13" />
                                </svg>
                            </button>

                            {/* Emoji */}
                            <button
                                type="button"
                                className="inline-flex justify-center items-center w-10 h-10 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
                                title="Emoji"
                            >
                                <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 15.182a4.5 4.5 0 0 1-6.364 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" />
                                </svg>
                            </button>
                        </div>

                        {/* Right Icons */}
                        <div className="flex items-center gap-x-1">
                            {/* Microphone */}
                            <button
                                type="button"
                                className="inline-flex justify-center items-center w-10 h-10 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
                                title="บันทึกเสียง"
                            >
                                <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                                </svg>
                            </button>

                            {/* Send Button - Blue like Uiverse.io */}
                            <button
                                type="button"
                                onClick={handleSend}
                                disabled={disabled || !text.trim()}
                                className="inline-flex justify-center items-center w-10 h-10 rounded-lg text-white bg-blue-400 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-300"
                                title="ส่งข้อความ"
                            >
                                <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Credit */}
            <div className="text-center mt-2">
                <span className="text-[10px] text-gray-500">
                    Powered by ACA Mozart Gateway
                </span>
            </div>
        </div>
    );
}

