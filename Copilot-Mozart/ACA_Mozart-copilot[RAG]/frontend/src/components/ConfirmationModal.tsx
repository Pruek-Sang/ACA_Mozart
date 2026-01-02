import React, { useState } from 'react';
import { X, AlertCircle, ChevronRight } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * ConfirmationModal - Ask user for confirmation on edge cases
 * 
 * Features:
 * - Multiple choice options
 * - Custom input option
 * - Keyboard shortcuts
 * - Beautiful animations
 */

interface ConfirmationOption {
    id: string;
    label: string;
    value: any;
    isDefault: boolean;
    description?: string;
}

interface ConfirmationRequest {
    confirmationId: string;
    confirmationType: string;
    title: string;
    message: string;
    context: Record<string, any>;
    options: ConfirmationOption[];
    allowsCustom: boolean;
    customInputLabel?: string;
}

interface ConfirmationModalProps {
    request: ConfirmationRequest;
    isOpen: boolean;
    onConfirm: (optionId: string, customValue?: any) => void;
    onCancel: () => void;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
    request,
    isOpen,
    onConfirm,
    onCancel,
}) => {
    const [selectedId, setSelectedId] = useState<string>(
        request.options.find(o => o.isDefault)?.id || request.options[0]?.id || ''
    );
    const [customValue, setCustomValue] = useState<string>('');
    const [showCustomInput, setShowCustomInput] = useState(false);

    if (!isOpen) return null;

    const handleOptionClick = (optionId: string) => {
        setSelectedId(optionId);
        if (optionId === 'custom' && request.allowsCustom) {
            setShowCustomInput(true);
        } else {
            setShowCustomInput(false);
        }
    };

    const handleConfirm = () => {
        if (selectedId === 'custom' && request.allowsCustom) {
            onConfirm(selectedId, customValue);
        } else {
            onConfirm(selectedId);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={onCancel}
            />

            {/* Modal */}
            <div className={cn(
                "relative w-full max-w-md mx-4",
                "bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl",
                "animate-in zoom-in-95 duration-200"
            )}>
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "flex items-center justify-center w-10 h-10 rounded-xl",
                            "bg-gradient-to-br from-amber-500/20 to-orange-500/20",
                            "border border-amber-500/30"
                        )}>
                            <AlertCircle className="w-5 h-5 text-amber-400" />
                        </div>
                        <h2 className="text-lg font-semibold text-white">
                            {request.title}
                        </h2>
                    </div>
                    <button
                        onClick={onCancel}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-5">
                    <p className="text-slate-300 text-sm mb-5">
                        {request.message}
                    </p>

                    {/* Options */}
                    <div className="space-y-3">
                        {request.options.map((option) => (
                            <button
                                key={option.id}
                                onClick={() => handleOptionClick(option.id)}
                                className={cn(
                                    "w-full flex items-center gap-4 p-4 rounded-xl border transition-all",
                                    selectedId === option.id
                                        ? "bg-violet-500/10 border-violet-500/50"
                                        : "bg-slate-800/50 border-slate-700 hover:border-slate-600"
                                )}
                            >
                                {/* Radio */}
                                <div className={cn(
                                    "w-5 h-5 rounded-full border-2 flex items-center justify-center",
                                    selectedId === option.id
                                        ? "border-violet-500 bg-violet-500"
                                        : "border-slate-500"
                                )}>
                                    {selectedId === option.id && (
                                        <div className="w-2 h-2 rounded-full bg-white" />
                                    )}
                                </div>

                                {/* Label */}
                                <div className="flex-1 text-left">
                                    <p className={cn(
                                        "font-medium",
                                        selectedId === option.id ? "text-white" : "text-slate-300"
                                    )}>
                                        {option.label}
                                    </p>
                                    {option.description && (
                                        <p className="text-xs text-slate-400 mt-0.5">
                                            {option.description}
                                        </p>
                                    )}
                                </div>

                                {/* Default badge */}
                                {option.isDefault && (
                                    <span className="text-xs px-2 py-0.5 bg-slate-700 text-slate-400 rounded">
                                        แนะนำ
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Custom Input */}
                    {showCustomInput && request.allowsCustom && (
                        <div className="mt-4 pt-4 border-t border-slate-800">
                            <label className="block text-sm text-slate-400 mb-2">
                                {request.customInputLabel || 'ระบุค่า'}
                            </label>
                            <input
                                type="text"
                                value={customValue}
                                onChange={(e) => setCustomValue(e.target.value)}
                                placeholder="ระบุค่า..."
                                autoFocus
                                className={cn(
                                    "w-full px-4 py-3 rounded-lg",
                                    "bg-slate-800 border border-slate-700",
                                    "text-white placeholder-slate-500",
                                    "focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
                                )}
                            />
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 p-5 border-t border-slate-800">
                    <button
                        onClick={onCancel}
                        className={cn(
                            "px-4 py-2 rounded-lg text-sm font-medium",
                            "text-slate-400 hover:text-white hover:bg-slate-800",
                            "transition-colors"
                        )}
                    >
                        ยกเลิก
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={showCustomInput && !customValue}
                        className={cn(
                            "flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium",
                            "bg-gradient-to-r from-violet-600 to-purple-600",
                            "text-white shadow-lg shadow-violet-500/25",
                            "hover:from-violet-500 hover:to-purple-500",
                            "disabled:opacity-50 disabled:cursor-not-allowed",
                            "transition-all"
                        )}
                    >
                        <span>ยืนยัน</span>
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;
