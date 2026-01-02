import React, { useState } from 'react';
import { X, MessageSquare, Star, Bug, Lightbulb, CheckCircle, Send } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * FeedbackModal - Collect user feedback during pilot testing
 * 
 * Features:
 * - Feedback type selection
 * - Star rating
 * - Text input
 * - Quick submit
 */

type FeedbackType = 'bug_report' | 'feature_request' | 'accuracy_issue' | 'ui_feedback' | 'general';
type Rating = 'excellent' | 'good' | 'okay' | 'poor' | 'terrible';

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (feedback: {
        type: FeedbackType;
        rating: Rating | null;
        message: string;
    }) => void;
}

const FEEDBACK_TYPES = [
    { id: 'bug_report' as FeedbackType, icon: Bug, label: 'รายงานบัค', color: 'text-red-400' },
    { id: 'feature_request' as FeedbackType, icon: Lightbulb, label: 'ขอ Feature', color: 'text-amber-400' },
    { id: 'accuracy_issue' as FeedbackType, icon: CheckCircle, label: 'ความถูกต้อง', color: 'text-blue-400' },
    { id: 'ui_feedback' as FeedbackType, icon: MessageSquare, label: 'หน้าตา/UX', color: 'text-purple-400' },
    { id: 'general' as FeedbackType, icon: Star, label: 'ทั่วไป', color: 'text-emerald-400' },
];

const RATINGS: { value: Rating; label: string; emoji: string }[] = [
    { value: 'excellent', label: 'ยอดเยี่ยม', emoji: '😍' },
    { value: 'good', label: 'ดี', emoji: '😊' },
    { value: 'okay', label: 'พอใช้', emoji: '😐' },
    { value: 'poor', label: 'ไม่ค่อยดี', emoji: '😕' },
    { value: 'terrible', label: 'แย่', emoji: '😞' },
];

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
    isOpen,
    onClose,
    onSubmit,
}) => {
    const [selectedType, setSelectedType] = useState<FeedbackType>('general');
    const [selectedRating, setSelectedRating] = useState<Rating | null>(null);
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!message.trim()) return;

        setIsSubmitting(true);

        try {
            await onSubmit({
                type: selectedType,
                rating: selectedRating,
                message: message.trim(),
            });

            setIsSubmitted(true);

            // Reset after delay
            setTimeout(() => {
                setIsSubmitted(false);
                setMessage('');
                setSelectedRating(null);
                setSelectedType('general');
                onClose();
            }, 2000);
        } catch (error) {
            console.error('Feedback submission error:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSubmitted) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center">
                <div className="absolute inset-0 bg-black/70" />
                <div className="relative bg-slate-900 rounded-2xl p-8 text-center animate-in zoom-in-95">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                        <CheckCircle className="w-8 h-8 text-emerald-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                        ขอบคุณสำหรับ Feedback!
                    </h3>
                    <p className="text-sm text-slate-400">
                        เราจะนำไปปรับปรุงระบบต่อไป
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className={cn(
                "relative w-full max-w-lg mx-4",
                "bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl",
                "animate-in zoom-in-95"
            )}>
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-slate-800">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <MessageSquare className="w-5 h-5 text-cyan-400" />
                        ให้ Feedback
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-5 space-y-5">
                    {/* Feedback Type */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">
                            ประเภท Feedback
                        </label>
                        <div className="flex flex-wrap gap-2">
                            {FEEDBACK_TYPES.map((type) => {
                                const Icon = type.icon;
                                return (
                                    <button
                                        key={type.id}
                                        onClick={() => setSelectedType(type.id)}
                                        className={cn(
                                            "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm",
                                            "transition-all",
                                            selectedType === type.id
                                                ? "bg-slate-800 border-cyan-500/50"
                                                : "border-slate-700 hover:border-slate-600"
                                        )}
                                    >
                                        <Icon size={16} className={type.color} />
                                        <span className="text-white">{type.label}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Rating */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">
                            ความพึงพอใจ (ไม่บังคับ)
                        </label>
                        <div className="flex gap-2 justify-center">
                            {RATINGS.map((rating) => (
                                <button
                                    key={rating.value}
                                    onClick={() => setSelectedRating(
                                        selectedRating === rating.value ? null : rating.value
                                    )}
                                    className={cn(
                                        "flex flex-col items-center gap-1 p-3 rounded-xl",
                                        "transition-all",
                                        selectedRating === rating.value
                                            ? "bg-cyan-500/20 border border-cyan-500/50 scale-110"
                                            : "hover:bg-slate-800 border border-transparent"
                                    )}
                                    title={rating.label}
                                >
                                    <span className="text-2xl">{rating.emoji}</span>
                                    <span className="text-[10px] text-slate-400">{rating.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Message */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">
                            รายละเอียด *
                        </label>
                        <textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="อธิบายรายละเอียด feedback ของคุณ..."
                            rows={4}
                            className={cn(
                                "w-full px-4 py-3 rounded-lg",
                                "bg-slate-800 border border-slate-700",
                                "text-white placeholder-slate-500",
                                "focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500",
                                "resize-none"
                            )}
                        />
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 p-5 border-t border-slate-800">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                    >
                        ยกเลิก
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={!message.trim() || isSubmitting}
                        className={cn(
                            "flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium",
                            "bg-gradient-to-r from-cyan-600 to-blue-600",
                            "text-white shadow-lg shadow-cyan-500/25",
                            "hover:from-cyan-500 hover:to-blue-500",
                            "disabled:opacity-50 disabled:cursor-not-allowed",
                            "transition-all"
                        )}
                    >
                        <Send size={16} />
                        <span>{isSubmitting ? 'กำลังส่ง...' : 'ส่ง Feedback'}</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FeedbackModal;
