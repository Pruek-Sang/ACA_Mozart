/**
 * 🩺 Health Panel Component
 * 
 * Real-time debug panel showing:
 * - Frontend State (localStorage vs React state)
 * - CRUD Operations status
 * - Edit Injector status
 * - Last API Request/Response
 * - Timeline of events
 * 
 * Usage: Add ?debug=true to URL to show this panel
 */

import React, { useState } from 'react';
import { X, ChevronDown, ChevronRight, Activity, Database, Edit3, Globe, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import type { HealthTracker } from '../hooks/useHealthTracker';

interface HealthPanelProps {
    tracker: HealthTracker;
    localStorageSessionId: string | null;
    localStorageProjectName: string | null;
    reactSessionId: string | null;
    reactProjectName: string | null;
    onClose?: () => void;
}

const StatusIcon: React.FC<{ status: 'success' | 'failed' | 'pending' | 'idle' | 'never_called' | 'not_found' }> = ({ status }) => {
    switch (status) {
        case 'success':
            return <CheckCircle size={14} className="text-green-400" />;
        case 'failed':
        case 'not_found':
            return <XCircle size={14} className="text-red-400" />;
        case 'pending':
            return <RefreshCw size={14} className="text-blue-400 animate-spin" />;
        case 'never_called':
            return <AlertCircle size={14} className="text-orange-400" />;
        default:
            return <div className="w-3.5 h-3.5 rounded-full bg-slate-600" />;
    }
};

const StatusBadge: React.FC<{ match: boolean; label: string }> = ({ match, label }) => (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${match ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
        {match ? '✅' : '❌'} {label}
    </span>
);

const Section: React.FC<{
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    defaultOpen?: boolean;
}> = ({ title, icon, children, defaultOpen = true }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="border border-slate-700 rounded-lg overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-2 p-2 bg-slate-800 hover:bg-slate-700 transition-colors text-left"
            >
                {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                {icon}
                <span className="text-sm font-medium">{title}</span>
            </button>
            {isOpen && (
                <div className="p-2 bg-slate-900/50 text-xs font-mono space-y-1">
                    {children}
                </div>
            )}
        </div>
    );
};

export const HealthPanel: React.FC<HealthPanelProps> = ({
    tracker,
    localStorageSessionId,
    localStorageProjectName,
    reactSessionId,
    reactProjectName,
    onClose,
}) => {
    const [isMinimized, setIsMinimized] = useState(false);

    const sessionIdMatch = localStorageSessionId === reactSessionId;
    const projectNameMatch = localStorageProjectName === reactProjectName;

    // Format session ID for display
    const formatId = (id: string | null) => id ? `${id.slice(0, 8)}...` : 'null';

    if (isMinimized) {
        return (
            <button
                onClick={() => setIsMinimized(false)}
                className={`fixed bottom-4 right-4 z-[200] p-3 rounded-full shadow-lg ${tracker.isHealthy ? 'bg-green-600 hover:bg-green-500' : 'bg-red-600 hover:bg-red-500 animate-pulse'
                    } transition-colors`}
                title="Health Panel"
            >
                <Activity size={20} className="text-white" />
            </button>
        );
    }

    return (
        <div className="fixed bottom-4 right-4 z-[200] w-96 max-h-[80vh] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-slate-800 border-b border-slate-700">
                <div className="flex items-center gap-2">
                    <Activity size={18} className={tracker.isHealthy ? 'text-green-400' : 'text-red-400'} />
                    <span className="font-semibold text-sm">🩺 Health Panel</span>
                    {tracker.isHealthy ? (
                        <span className="text-xs px-2 py-0.5 bg-green-900/50 text-green-400 rounded">HEALTHY</span>
                    ) : (
                        <span className="text-xs px-2 py-0.5 bg-red-900/50 text-red-400 rounded animate-pulse">ISSUES</span>
                    )}
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setIsMinimized(true)}
                        className="p-1 hover:bg-slate-700 rounded transition-colors"
                        title="Minimize"
                    >
                        <ChevronDown size={16} />
                    </button>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-slate-700 rounded transition-colors"
                            title="Close"
                        >
                            <X size={16} />
                        </button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {/* Frontend State */}
                <Section title="Frontend State" icon={<Database size={14} className="text-blue-400" />}>
                    <div className="space-y-1">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">localStorage.session_id:</span>
                            <span className="text-white">{formatId(localStorageSessionId)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">React sessionId:</span>
                            <span className="text-white">{formatId(reactSessionId)}</span>
                        </div>
                        <div className="flex justify-end">
                            <StatusBadge match={sessionIdMatch} label={sessionIdMatch ? 'SYNCED' : 'MISMATCH'} />
                        </div>
                        <hr className="border-slate-700 my-1" />
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">localStorage.project_name:</span>
                            <span className="text-white truncate max-w-[120px]">{localStorageProjectName || 'null'}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">React projectName:</span>
                            <span className="text-white truncate max-w-[120px]">{reactProjectName || 'null'}</span>
                        </div>
                        <div className="flex justify-end">
                            <StatusBadge match={projectNameMatch} label={projectNameMatch ? 'SYNCED' : 'MISMATCH'} />
                        </div>
                    </div>
                </Section>

                {/* CRUD Operations */}
                <Section title="CRUD Operations" icon={<Database size={14} className="text-purple-400" />}>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(tracker.crudStatus).map(([op, status]) => (
                            <div key={op} className="flex items-center gap-2 p-1 rounded bg-slate-800">
                                <StatusIcon status={status} />
                                <span className="uppercase text-slate-400">{op}:</span>
                                <span className={`${status === 'success' ? 'text-green-400' :
                                        status === 'failed' || status === 'not_found' ? 'text-red-400' :
                                            status === 'never_called' ? 'text-orange-400' :
                                                'text-slate-500'
                                    }`}>
                                    {status}
                                </span>
                            </div>
                        ))}
                    </div>
                </Section>

                {/* Edit Injector */}
                <Section title="Edit Injector" icon={<Edit3 size={14} className="text-amber-400" />}>
                    <div className="space-y-1">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Intent:</span>
                            <span className={tracker.editInjectorStatus.intent === 'EDIT' ? 'text-amber-400' : 'text-blue-400'}>
                                {tracker.editInjectorStatus.intent || 'N/A'}
                            </span>
                        </div>
                        {tracker.editInjectorStatus.query && (
                            <div className="text-slate-500 text-[10px] truncate">
                                "{tracker.editInjectorStatus.query}"
                            </div>
                        )}
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Previous Design:</span>
                            {tracker.editInjectorStatus.previousDesignLoaded ? (
                                <span className="text-green-400">✅ LOADED</span>
                            ) : (
                                <span className="text-orange-400">⚠️ NOT_LOADED</span>
                            )}
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Merge Result:</span>
                            <span className={
                                tracker.editInjectorStatus.mergeResult === 'success' ? 'text-green-400' :
                                    tracker.editInjectorStatus.mergeResult === 'fallback' ? 'text-orange-400' :
                                        'text-slate-500'
                            }>
                                {tracker.editInjectorStatus.mergeResult?.toUpperCase() || 'N/A'}
                            </span>
                        </div>
                        {tracker.editInjectorStatus.fallbackReason && (
                            <div className="text-red-400 text-[10px]">
                                Reason: {tracker.editInjectorStatus.fallbackReason}
                            </div>
                        )}
                    </div>
                </Section>

                {/* Last API Request */}
                <Section title="Last API Request" icon={<Globe size={14} className="text-cyan-400" />}>
                    {tracker.lastRequest ? (
                        <div className="space-y-1">
                            <div className="flex items-center justify-between">
                                <span className="text-slate-400">Endpoint:</span>
                                <span className="text-cyan-400 text-[10px]">{tracker.lastRequest.endpoint}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-slate-400">Sent session_id:</span>
                                <span className="text-white">{formatId(tracker.lastRequest.sentSessionId)}</span>
                            </div>
                            {tracker.gatewayForwardedSessionId !== null && (
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400">Gateway forwarded:</span>
                                    {tracker.gatewayForwardedSessionId ? (
                                        <span className="text-green-400">✅ YES</span>
                                    ) : (
                                        <span className="text-red-400">❌ NO</span>
                                    )}
                                </div>
                            )}
                            {tracker.lastResponse && (
                                <>
                                    <hr className="border-slate-700 my-1" />
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">Response:</span>
                                        <span className={tracker.lastResponse.status < 400 ? 'text-green-400' : 'text-red-400'}>
                                            {tracker.lastResponse.status}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${tracker.lastResponse.hasDisplayData ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                                            display_data: {tracker.lastResponse.hasDisplayData ? '✅' : '❌'}
                                        </span>
                                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${tracker.lastResponse.hasBoqData ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                                            boq_data: {tracker.lastResponse.hasBoqData ? '✅' : '❌'}
                                        </span>
                                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${tracker.lastResponse.hasSldData ? 'bg-green-900/50 text-green-400' : 'bg-slate-700 text-slate-400'}`}>
                                            sld_data: {tracker.lastResponse.hasSldData ? '✅' : '—'}
                                        </span>
                                    </div>
                                    {tracker.lastResponse.errorMessage && (
                                        <div className="text-red-400 text-[10px] p-1 bg-red-900/20 rounded">
                                            Error: {tracker.lastResponse.errorMessage}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    ) : (
                        <div className="text-slate-500 text-center py-2">No requests yet</div>
                    )}
                </Section>

                {/* Timeline */}
                <Section title="Timeline" icon={<Clock size={14} className="text-green-400" />} defaultOpen={false}>
                    {tracker.events.length > 0 ? (
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                            {[...tracker.events].reverse().map((event) => (
                                <div
                                    key={event.id}
                                    className={`flex items-start gap-2 p-1 rounded text-[10px] ${event.success ? 'bg-slate-800' : 'bg-red-900/20'
                                        }`}
                                >
                                    <span className="text-slate-500 whitespace-nowrap">
                                        {event.timestamp.toLocaleTimeString('th-TH')}
                                    </span>
                                    <span className={event.success ? 'text-green-400' : 'text-red-400'}>
                                        [{event.type}]
                                    </span>
                                    <span className="text-slate-400 truncate flex-1">
                                        {JSON.stringify(event.details).slice(0, 50)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-slate-500 text-center py-2">No events recorded</div>
                    )}
                </Section>
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-slate-700 bg-slate-800 flex items-center justify-between">
                <span className="text-[10px] text-slate-500">
                    Events: {tracker.events.length}
                </span>
                <button
                    onClick={tracker.clearAll}
                    className="text-[10px] px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
                >
                    Clear All
                </button>
            </div>
        </div>
    );
};
