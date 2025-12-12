import { QUICK_SUGGESTIONS } from '../config/api.config';

interface QuickChipsProps {
    onSelect: (text: string) => void;
    visible: boolean;
}

export function QuickChips({ onSelect, visible }: QuickChipsProps) {
    if (!visible) return null;

    return (
        <div className="max-w-3xl mx-auto animate-fadeIn">
            <p className="text-sm text-textSecondary mb-3 ml-12">💡 ลองถาม:</p>
            <div className="flex flex-wrap gap-2 ml-12">
                {QUICK_SUGGESTIONS.map((suggestion, index) => (
                    <button
                        key={index}
                        onClick={() => onSelect(suggestion.text)}
                        className="px-4 py-2 bg-bgInput border border-gray-700 rounded-full text-sm hover:border-accentMozart hover:text-accentMozart transition-all"
                    >
                        {suggestion.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
