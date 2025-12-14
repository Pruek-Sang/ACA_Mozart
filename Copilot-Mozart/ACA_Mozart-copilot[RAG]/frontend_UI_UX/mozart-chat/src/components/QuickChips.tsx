import { useState, useEffect } from 'react';
import { QUICK_SUGGESTIONS } from '../config/api.config';

interface QuickChipsProps {
    onSelect: (text: string) => void;
    visible: boolean;
}

export function QuickChips({ onSelect, visible }: QuickChipsProps) {
    const [isVisible, setIsVisible] = useState(visible);
    const [isFading, setIsFading] = useState(false);

    useEffect(() => {
        if (visible) {
            setIsVisible(true);
            setIsFading(false);

            // Start fade-out after 2.5 seconds
            const fadeTimer = setTimeout(() => {
                setIsFading(true);
            }, 2500);

            // Completely hide after fade animation (0.5s)
            const hideTimer = setTimeout(() => {
                setIsVisible(false);
            }, 3000);

            return () => {
                clearTimeout(fadeTimer);
                clearTimeout(hideTimer);
            };
        } else {
            setIsVisible(false);
            setIsFading(false);
        }
    }, [visible]);

    if (!isVisible) return null;

    return (
        <div
            className={`max-w-3xl mx-auto transition-opacity duration-500 ${isFading ? 'opacity-0' : 'opacity-100 animate-fadeIn'}`}
        >
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
