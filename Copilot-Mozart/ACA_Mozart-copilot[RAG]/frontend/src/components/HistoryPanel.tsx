import React, { useState } from 'react';
import { History, ChevronDown, ChevronRight, Plus, Minus, Edit3, Clock } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * HistoryPanel - Display version history with diffs
 * 
 * Features:
 * - Timeline view
 * - Expandable diffs per version
 * - Color-coded changes
 */

interface FieldChange {
    field: string;
    label: string;
    before?: any;
    after?: any;
    changeType: 'added' | 'removed' | 'modified';
}

interface RevisionDiff {
    fromVersion: number;
    toVersion: number;
    timestamp: string;
    summary: string;
    changes: FieldChange[];
    changeCount: number;
}

interface HistoryPanelProps {
    history: RevisionDiff[];
    currentVersion: number;
    onRevert?: (version: number) => void;
    className?: string;
}

const CHANGE_CONFIG = {
    added: {
        icon: Plus,
        bgColor: 'bg-emerald-500/10',
        textColor: 'text-emerald-400',
        borderColor: 'border-emerald-500/30',
    },
    removed: {
        icon: Minus,
        bgColor: 'bg-red-500/10',
        textColor: 'text-red-400',
        borderColor: 'border-red-500/30',
    },
    modified: {
        icon: Edit3,
        bgColor: 'bg-amber-500/10',
        textColor: 'text-amber-400',
        borderColor: 'border-amber-500/30',
    },
};

export const HistoryPanel: React.FC<HistoryPanelProps> = ({
    history,
    currentVersion,
    onRevert,
    className,
}) => {
    const [expandedVersions, setExpandedVersions] = useState<Set<number>>(new Set());

    const toggleVersion = (version: number) => {
        const newSet = new Set(expandedVersions);
        if (newSet.has(version)) {
            newSet.delete(version);
        } else {
            newSet.add(version);
        }
        setExpandedVersions(newSet);
    };

    const formatTime = (isoString: string) => {
        const date = new Date(isoString);
        return date.toLocaleString('th-TH', {
            day: '2-digit',
            month: '2-digit',
            year: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className={cn(
            "bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden",
            className
        )}>
            {/* Header */}
            <div className="flex items-center gap-3 p-4 border-b border-slate-800">
                <div className={cn(
                    "flex items-center justify-center w-8 h-8 rounded-lg",
                    "bg-gradient-to-br from-sky-500/20 to-blue-500/20 border border-sky-500/30"
                )}>
                    <History size={16} className="text-sky-400" />
                </div>
                <div>
                    <h3 className="text-sm font-medium text-white">ประวัติการแก้ไข</h3>
                    <p className="text-xs text-slate-400">
                        เวอร์ชันปัจจุบัน: v{currentVersion} • {history.length} การเปลี่ยนแปลง
                    </p>
                </div>
            </div>

            {/* Timeline */}
            <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-7 top-0 bottom-0 w-px bg-slate-700" />

                {history.length === 0 ? (
                    <div className="p-6 text-center text-slate-500 text-sm">
                        ยังไม่มีประวัติการแก้ไข
                    </div>
                ) : (
                    <div className="space-y-1 p-2">
                        {history.map((diff) => (
                            <div key={diff.toVersion} className="relative">
                                {/* Timeline dot */}
                                <div className={cn(
                                    "absolute left-5 top-4 w-5 h-5 rounded-full border-2",
                                    "flex items-center justify-center z-10",
                                    diff.toVersion === currentVersion
                                        ? "bg-sky-500 border-sky-400"
                                        : "bg-slate-800 border-slate-600"
                                )}>
                                    <span className="text-[10px] text-white font-bold">
                                        {diff.toVersion}
                                    </span>
                                </div>

                                {/* Content */}
                                <div className="ml-12 mr-2">
                                    <button
                                        onClick={() => toggleVersion(diff.toVersion)}
                                        className={cn(
                                            "w-full text-left p-3 rounded-lg transition-colors",
                                            expandedVersions.has(diff.toVersion)
                                                ? "bg-slate-800"
                                                : "hover:bg-slate-800/50"
                                        )}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                {expandedVersions.has(diff.toVersion) ? (
                                                    <ChevronDown size={14} className="text-slate-500" />
                                                ) : (
                                                    <ChevronRight size={14} className="text-slate-500" />
                                                )}
                                                <span className="text-sm text-white">
                                                    v{diff.fromVersion} → v{diff.toVersion}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                                <Clock size={12} />
                                                {formatTime(diff.timestamp)}
                                            </div>
                                        </div>
                                        <p className="text-xs text-slate-400 mt-1 ml-5">
                                            {diff.summary}
                                        </p>
                                    </button>

                                    {/* Expanded changes */}
                                    {expandedVersions.has(diff.toVersion) && (
                                        <div className="mt-2 ml-5 space-y-2 pb-3">
                                            {diff.changes.map((change, idx) => {
                                                const config = CHANGE_CONFIG[change.changeType];
                                                const Icon = config.icon;

                                                return (
                                                    <div
                                                        key={idx}
                                                        className={cn(
                                                            "flex items-start gap-2 p-2 rounded border",
                                                            config.bgColor,
                                                            config.borderColor
                                                        )}
                                                    >
                                                        <Icon size={14} className={cn("mt-0.5", config.textColor)} />
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-xs text-slate-300">
                                                                {change.label}
                                                            </p>
                                                            {change.changeType === 'modified' && (
                                                                <div className="flex items-center gap-2 mt-1 text-xs font-mono">
                                                                    <span className="text-slate-500">
                                                                        {String(change.before)}
                                                                    </span>
                                                                    <span className="text-slate-500">→</span>
                                                                    <span className={config.textColor}>
                                                                        {String(change.after)}
                                                                    </span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}

                                            {onRevert && diff.toVersion !== currentVersion && (
                                                <button
                                                    onClick={() => onRevert(diff.toVersion)}
                                                    className={cn(
                                                        "w-full mt-2 px-3 py-2 rounded text-xs",
                                                        "bg-slate-700 hover:bg-slate-600 text-slate-300",
                                                        "transition-colors"
                                                    )}
                                                >
                                                    กลับไปใช้เวอร์ชันนี้
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default HistoryPanel;
