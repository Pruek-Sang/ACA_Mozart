import React from 'react';
import { AlertTriangle, AlertCircle, Info, Wrench, ArrowRight } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * ExplainableWarning - Display QC warning with reason and suggested action
 * 
 * Features:
 * - Severity color coding
 * - Reason explanation
 * - Suggested action with before/after
 * - Effort indicator
 */

interface SuggestedAction {
    type: string;
    description: string;
    beforeValue?: string;
    afterValue?: string;
    effort: 'low' | 'medium' | 'high';
}

interface Warning {
    code: string;
    message: string;
    reason: string;
    severity: 'critical' | 'warning' | 'info';
    standardRef: string;
    circuitName?: string;
    action: SuggestedAction;
}

interface ExplainableWarningCardProps {
    warning: Warning;
    className?: string;
}

const SEVERITY_CONFIG = {
    critical: {
        icon: AlertCircle,
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/30',
        textColor: 'text-red-400',
        label: 'ต้องแก้ไข',
    },
    warning: {
        icon: AlertTriangle,
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/30',
        textColor: 'text-amber-400',
        label: 'ควรแก้ไข',
    },
    info: {
        icon: Info,
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/30',
        textColor: 'text-blue-400',
        label: 'แนะนำ',
    },
};

const EFFORT_CONFIG = {
    low: { label: 'ง่าย', color: 'text-emerald-400 bg-emerald-500/10' },
    medium: { label: 'ปานกลาง', color: 'text-amber-400 bg-amber-500/10' },
    high: { label: 'ซับซ้อน', color: 'text-red-400 bg-red-500/10' },
};

export const ExplainableWarningCard: React.FC<ExplainableWarningCardProps> = ({
    warning,
    className,
}) => {
    const config = SEVERITY_CONFIG[warning.severity] || SEVERITY_CONFIG.info;
    const Icon = config.icon;
    const effortConfig = EFFORT_CONFIG[warning.action.effort] || EFFORT_CONFIG.low;

    return (
        <div className={cn(
            "rounded-lg border p-4",
            config.bgColor,
            config.borderColor,
            className
        )}>
            {/* Header */}
            <div className="flex items-start gap-3">
                <Icon className={cn("w-5 h-5 mt-0.5 flex-shrink-0", config.textColor)} />
                <div className="flex-1 min-w-0">
                    {/* Title Row */}
                    <div className="flex items-center justify-between gap-2">
                        <h4 className={cn("font-medium text-sm", config.textColor)}>
                            {warning.message}
                        </h4>
                        <span className={cn(
                            "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded",
                            config.bgColor, config.textColor
                        )}>
                            {config.label}
                        </span>
                    </div>

                    {/* Circuit Name */}
                    {warning.circuitName && (
                        <p className="text-xs text-slate-400 mt-1">
                            วงจร: <span className="font-mono">{warning.circuitName}</span>
                        </p>
                    )}

                    {/* Reason */}
                    <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                        {warning.reason}
                    </p>

                    {/* Standard Reference */}
                    {warning.standardRef && warning.standardRef !== '-' && (
                        <p className="text-xs text-slate-500 mt-1">
                            อ้างอิง: {warning.standardRef}
                        </p>
                    )}
                </div>
            </div>

            {/* Suggested Action */}
            <div className="mt-4 pt-3 border-t border-slate-700/50">
                <div className="flex items-center gap-2 mb-2">
                    <Wrench className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-medium text-slate-300">แนะนำ</span>
                    <span className={cn("text-[10px] px-1.5 py-0.5 rounded", effortConfig.color)}>
                        {effortConfig.label}
                    </span>
                </div>

                <p className="text-sm text-white">
                    {warning.action.description}
                </p>

                {/* Before/After */}
                {(warning.action.beforeValue || warning.action.afterValue) && (
                    <div className="flex items-center gap-2 mt-2 text-xs">
                        {warning.action.beforeValue && (
                            <span className="px-2 py-1 bg-slate-800 rounded text-slate-400 font-mono">
                                {warning.action.beforeValue}
                            </span>
                        )}
                        {warning.action.beforeValue && warning.action.afterValue && (
                            <ArrowRight className="w-4 h-4 text-slate-500" />
                        )}
                        {warning.action.afterValue && (
                            <span className="px-2 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded text-emerald-400 font-mono">
                                {warning.action.afterValue}
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ExplainableWarningCard;
