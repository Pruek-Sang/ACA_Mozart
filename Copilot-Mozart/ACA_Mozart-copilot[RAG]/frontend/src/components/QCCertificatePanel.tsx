import React from 'react';
import { Award, CheckCircle, AlertTriangle, XCircle, FileText, Shield } from 'lucide-react';
import { cn } from '../lib/utils';
import type { QCCertificateData, ValidationItem, CircuitVDValidation } from '../types';

/**
 * QCCertificatePanel - Display formal QC Assumptions Certificate
 * 
 * Features:
 * - Header with company name and document info
 * - Validation status tables with ✓/⚠️/❌ indicators
 * - Summary PASS/WARN/FAIL counts
 * - Professional formal document layout
 */

interface QCCertificatePanelProps {
    qcData: QCCertificateData | null | undefined;
    className?: string;
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    if (status.includes('OK') || status.includes('✓')) {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-emerald-500/20 text-emerald-400">
                <CheckCircle size={12} /> OK
            </span>
        );
    }
    if (status.includes('WARN') || status.includes('⚠')) {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-amber-500/20 text-amber-400">
                <AlertTriangle size={12} /> WARN
            </span>
        );
    }
    if (status.includes('FAIL') || status.includes('❌')) {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-red-500/20 text-red-400">
                <XCircle size={12} /> FAIL
            </span>
        );
    }
    return <span className="text-slate-400">{status}</span>;
};

export const QCCertificatePanel: React.FC<QCCertificatePanelProps> = ({
    qcData,
    className,
}) => {
    if (!qcData) {
        return (
            <div className={cn("bg-slate-900/50 p-6 rounded-lg border border-slate-800", className)}>
                <p className="text-slate-400">QC Certificate data not available.</p>
            </div>
        );
    }

    const { summary } = qcData;
    const overallStatus = summary.fail_count > 0 ? 'FAIL' : summary.warn_count > 0 ? 'WARN' : 'PASS';

    return (
        <div className={cn("bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden", className)}>
            {/* Header */}
            <div className="bg-gradient-to-r from-violet-600/20 to-purple-600/20 p-6 border-b border-slate-700">
                <div className="flex items-center gap-4 mb-4">
                    <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-violet-500/20 border border-violet-500/30">
                        <Award size={24} className="text-violet-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">DESIGN ASSUMPTIONS CERTIFICATE</h2>
                        <p className="text-sm text-violet-300">{qcData.company_name}</p>
                    </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <span className="text-slate-400">Document No:</span>
                        <p className="font-mono text-white">{qcData.document_id}</p>
                    </div>
                    <div>
                        <span className="text-slate-400">Date:</span>
                        <p className="text-white">{qcData.date_generated}</p>
                    </div>
                    <div>
                        <span className="text-slate-400">Valid Until:</span>
                        <p className="text-white">{qcData.valid_until}</p>
                    </div>
                    <div>
                        <span className="text-slate-400">Revision:</span>
                        <p className="text-white">{qcData.revision}</p>
                    </div>
                </div>
            </div>

            {/* Project Info */}
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-medium text-slate-400 mb-2 flex items-center gap-2">
                    <FileText size={14} /> PROJECT INFORMATION
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <span className="text-slate-500">Project:</span>
                        <p className="font-medium text-white">{qcData.project_name}</p>
                    </div>
                    <div>
                        <span className="text-slate-500">Total Load:</span>
                        <p className="font-mono text-white">{qcData.total_kw.toFixed(2)} kW</p>
                    </div>
                    <div>
                        <span className="text-slate-500">Main Breaker:</span>
                        <p className="font-mono text-white">{qcData.main_breaker} A</p>
                    </div>
                    <div>
                        <span className="text-slate-500">Circuits:</span>
                        <p className="font-mono text-white">{qcData.circuit_count}</p>
                    </div>
                </div>
            </div>

            {/* Static Parameters Validation */}
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                    <Shield size={14} /> SECTION A: ELECTRICAL PARAMETERS
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-slate-500 border-b border-slate-700">
                                <th className="py-2 text-left">Parameter</th>
                                <th className="py-2 text-left">Value</th>
                                <th className="py-2 text-left">Standard</th>
                                <th className="py-2 text-left">Range</th>
                                <th className="py-2 text-left">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {qcData.static_params.map((param: ValidationItem, idx: number) => (
                                <tr key={idx} className="border-b border-slate-800/50">
                                    <td className="py-2 text-slate-300">{param.parameter}</td>
                                    <td className="py-2 font-mono text-white">{param.value}</td>
                                    <td className="py-2 text-slate-400">{param.standard}</td>
                                    <td className="py-2 text-slate-400">{param.valid_range}</td>
                                    <td className="py-2"><StatusBadge status={param.status} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* VD Limits */}
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-medium text-slate-400 mb-3">SECTION B: VOLTAGE DROP LIMITS</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-slate-500 border-b border-slate-700">
                                <th className="py-2 text-left">Limit Type</th>
                                <th className="py-2 text-left">Value</th>
                                <th className="py-2 text-left">Standard</th>
                                <th className="py-2 text-left">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {qcData.vd_limits.map((limit: ValidationItem, idx: number) => (
                                <tr key={idx} className="border-b border-slate-800/50">
                                    <td className="py-2 text-slate-300">{limit.parameter}</td>
                                    <td className="py-2 font-mono text-white">{limit.value}</td>
                                    <td className="py-2 text-slate-400">{limit.standard}</td>
                                    <td className="py-2"><StatusBadge status={limit.status} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Per-Circuit VD Validation */}
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-medium text-slate-400 mb-3">SECTION C: VOLTAGE DROP VALIDATION (Per Circuit)</h3>
                <div className="overflow-x-auto max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-slate-900">
                            <tr className="text-slate-500 border-b border-slate-700">
                                <th className="py-2 text-left">Circuit</th>
                                <th className="py-2 text-left">VD%</th>
                                <th className="py-2 text-left">Limit</th>
                                <th className="py-2 text-left">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {qcData.circuit_vd_validation.map((vd: CircuitVDValidation, idx: number) => (
                                <tr key={idx} className="border-b border-slate-800/50">
                                    <td className="py-2 text-slate-300">{vd.circuit_name}</td>
                                    <td className="py-2 font-mono text-white">{vd.vd_percent.toFixed(2)}%</td>
                                    <td className="py-2 text-slate-400">≤{vd.limit}%</td>
                                    <td className="py-2"><StatusBadge status={vd.status} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Distance Assumptions */}
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-medium text-slate-400 mb-2">SECTION D: DISTANCE ASSUMPTIONS</h3>
                <p className="text-sm text-slate-300">
                    Circuits using default distance: <span className="font-mono text-white">{qcData.default_circuit_count}</span>
                </p>
                {qcData.default_circuit_count > 0 && (
                    <p className="text-xs text-amber-400 mt-1">⚠️ See Audit Report for specific circuits</p>
                )}
            </div>

            {/* References */}
            <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-medium text-slate-400 mb-2">REFERENCES</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                    {qcData.references.map((ref: string, idx: number) => (
                        <li key={idx} className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                            {ref}
                        </li>
                    ))}
                </ul>
            </div>

            {/* Validation Summary */}
            <div className="p-4 bg-slate-800/30">
                <h3 className="text-sm font-medium text-slate-400 mb-3">VALIDATION SUMMARY</h3>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded">
                        <CheckCircle size={18} className="text-emerald-400" />
                        <div>
                            <span className="text-2xl font-bold text-emerald-400">{summary.pass_count}</span>
                            <p className="text-xs text-emerald-400/70">PASS</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/10 border border-amber-500/30 rounded">
                        <AlertTriangle size={18} className="text-amber-400" />
                        <div>
                            <span className="text-2xl font-bold text-amber-400">{summary.warn_count}</span>
                            <p className="text-xs text-amber-400/70">WARN</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded">
                        <XCircle size={18} className="text-red-400" />
                        <div>
                            <span className="text-2xl font-bold text-red-400">{summary.fail_count}</span>
                            <p className="text-xs text-red-400/70">FAIL</p>
                        </div>
                    </div>
                    <div className="ml-auto">
                        <span className={cn(
                            "px-4 py-2 rounded-lg font-bold text-lg",
                            overallStatus === 'PASS' && "bg-emerald-500/20 text-emerald-400",
                            overallStatus === 'WARN' && "bg-amber-500/20 text-amber-400",
                            overallStatus === 'FAIL' && "bg-red-500/20 text-red-400",
                        )}>
                            {overallStatus}
                        </span>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 bg-slate-950/50 text-center text-xs text-slate-500">
                Generated by Mozart Electrical Design System v2.0 • Valid for 30 days
            </div>
        </div>
    );
};

export default QCCertificatePanel;
