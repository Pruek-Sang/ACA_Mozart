import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, FileSpreadsheet, FileText, Eye } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * DownloadDropdown - Beautiful dropdown for download options
 * 
 * Features:
 * - Gradient button with hover effects
 * - Animated dropdown with smooth transitions
 * - Keyboard navigation (Arrow keys, Escape, Enter)
 * - Click outside to close
 * - Three options: Excel, PDF, Preview
 */

export interface DownloadOption {
    id: 'excel' | 'pdf' | 'preview';
    label: string;
    icon: React.ReactNode;
    description: string;
    color: string;
}

interface DownloadDropdownProps {
    onDownloadExcel: () => void;
    onDownloadPDF: () => void;
    onPreview: () => void;
    disabled?: boolean;
}

export const DownloadDropdown: React.FC<DownloadDropdownProps> = ({
    onDownloadExcel,
    onDownloadPDF,
    onPreview,
    disabled = false,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [focusedIndex, setFocusedIndex] = useState(-1);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);

    const options: DownloadOption[] = [
        {
            id: 'excel',
            label: 'Download Excel',
            icon: <FileSpreadsheet size={18} />,
            description: 'ตารางละเอียด 18 columns',
            color: 'text-emerald-400',
        },
        {
            id: 'pdf',
            label: 'Download PDF',
            icon: <FileText size={18} />,
            description: 'เอกสารพร้อมพิมพ์',
            color: 'text-rose-400',
        },
        {
            id: 'preview',
            label: 'Print Preview',
            icon: <Eye size={18} />,
            description: 'ดูตัวอย่างก่อนพิมพ์',
            color: 'text-sky-400',
        },
    ];

    // Handle option selection
    const handleSelect = useCallback((optionId: DownloadOption['id']) => {
        setIsOpen(false);
        setFocusedIndex(-1);

        switch (optionId) {
            case 'excel':
                onDownloadExcel();
                break;
            case 'pdf':
                onDownloadPDF();
                break;
            case 'preview':
                onPreview();
                break;
        }
    }, [onDownloadExcel, onDownloadPDF, onPreview]);

    // Click outside to close
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
                setFocusedIndex(-1);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    // Keyboard navigation
    const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
        if (!isOpen) {
            if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown') {
                event.preventDefault();
                setIsOpen(true);
                setFocusedIndex(0);
            }
            return;
        }

        switch (event.key) {
            case 'Escape':
                setIsOpen(false);
                setFocusedIndex(-1);
                buttonRef.current?.focus();
                break;
            case 'ArrowDown':
                event.preventDefault();
                setFocusedIndex(prev => (prev + 1) % options.length);
                break;
            case 'ArrowUp':
                event.preventDefault();
                setFocusedIndex(prev => (prev - 1 + options.length) % options.length);
                break;
            case 'Enter':
            case ' ':
                event.preventDefault();
                if (focusedIndex >= 0) {
                    handleSelect(options[focusedIndex].id);
                }
                break;
        }
    }, [isOpen, focusedIndex, options, handleSelect]);

    return (
        <div ref={dropdownRef} className="relative">
            {/* Main Button - Gradient with animation */}
            <button
                ref={buttonRef}
                onClick={() => setIsOpen(!isOpen)}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                className={cn(
                    // Base styles
                    "flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm",
                    "transition-all duration-300 ease-out",
                    // Gradient background
                    "bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600",
                    // Hover effect
                    "hover:from-violet-500 hover:via-purple-500 hover:to-indigo-500",
                    "hover:shadow-lg hover:shadow-purple-500/25",
                    // Active state
                    "active:scale-95",
                    // Text
                    "text-white",
                    // Disabled state
                    disabled && "opacity-50 cursor-not-allowed",
                    // Open state
                    isOpen && "ring-2 ring-purple-400 ring-offset-2 ring-offset-slate-950"
                )}
                aria-haspopup="listbox"
                aria-expanded={isOpen}
            >
                {/* Icon with subtle animation */}
                <span className="relative">
                    <FileSpreadsheet size={16} className="text-purple-200" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                </span>

                <span>Download</span>

                {/* Chevron with rotation */}
                <ChevronDown
                    size={16}
                    className={cn(
                        "transition-transform duration-200",
                        isOpen && "rotate-180"
                    )}
                />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div
                    className={cn(
                        "absolute right-0 mt-2 w-64",
                        "bg-slate-900/95 backdrop-blur-xl",
                        "border border-slate-700/50",
                        "rounded-xl shadow-2xl shadow-black/50",
                        "overflow-hidden",
                        "z-50",
                        // Animation
                        "animate-in fade-in-0 zoom-in-95 duration-200"
                    )}
                    role="listbox"
                >
                    {/* Header */}
                    <div className="px-4 py-3 border-b border-slate-700/50">
                        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                            เลือกรูปแบบ
                        </p>
                    </div>

                    {/* Options */}
                    <div className="py-2">
                        {options.map((option, index) => (
                            <button
                                key={option.id}
                                onClick={() => handleSelect(option.id)}
                                onMouseEnter={() => setFocusedIndex(index)}
                                className={cn(
                                    "w-full flex items-start gap-3 px-4 py-3",
                                    "text-left transition-colors duration-150",
                                    // Hover/Focus state
                                    focusedIndex === index
                                        ? "bg-slate-800/80"
                                        : "hover:bg-slate-800/50",
                                    // Active state
                                    "active:bg-slate-700/50"
                                )}
                                role="option"
                                aria-selected={focusedIndex === index}
                            >
                                {/* Icon */}
                                <span className={cn(
                                    "flex items-center justify-center w-9 h-9 rounded-lg",
                                    "bg-slate-800 border border-slate-700",
                                    option.color
                                )}>
                                    {option.icon}
                                </span>

                                {/* Text */}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-white">
                                        {option.label}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-0.5">
                                        {option.description}
                                    </p>
                                </div>

                                {/* Keyboard hint */}
                                {focusedIndex === index && (
                                    <span className="text-xs text-slate-500 self-center">
                                        ↵
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Footer */}
                    <div className="px-4 py-2 border-t border-slate-700/50 bg-slate-800/30">
                        <p className="text-xs text-slate-500 flex items-center gap-2">
                            <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400 font-mono">↑↓</kbd>
                            <span>เลื่อน</span>
                            <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400 font-mono">Esc</kbd>
                            <span>ปิด</span>
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DownloadDropdown;
