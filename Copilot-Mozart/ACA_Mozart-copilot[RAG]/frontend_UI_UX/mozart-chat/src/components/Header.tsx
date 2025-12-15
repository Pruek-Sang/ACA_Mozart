import { Sparkles, Trash2, Settings } from 'lucide-react';

interface HeaderProps {
    onClear: () => void;
    onSettings: () => void;
}

export function Header({ onClear, onSettings }: HeaderProps) {
    return (
        <header className="h-16 border-b border-gray-800 bg-bgSecondary/80 backdrop-blur-sm flex items-center justify-between px-6 shrink-0">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accentMozart to-accentAmadeus flex items-center justify-center text-white font-bold shadow-lg shadow-purple-900/20">
                    <Sparkles className="w-5 h-5" />
                </div>
                <div>
                    <h1 className="text-lg font-semibold tracking-wide">Mozart</h1>
                    <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-xs text-textSecondary">Online</span>
                    </div>
                </div>
            </div>
            <div className="flex items-center gap-2">
                <button
                    onClick={onClear}
                    title="Clear Chat"
                    className="p-2 rounded-lg hover:bg-white/5 transition-colors text-textSecondary hover:text-white"
                >
                    <Trash2 className="w-6 h-6" />
                </button>
                <button
                    onClick={onSettings}
                    title="Settings"
                    className="p-2 rounded-lg hover:bg-white/5 transition-colors text-textSecondary hover:text-white"
                >
                    <Settings className="w-6 h-6" />
                </button>
            </div>
        </header>
    );
}
