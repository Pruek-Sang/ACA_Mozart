import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Info, Settings, AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * AssumptionsPanel - Display design assumptions in collapsible panel
 * 
 * Features:
 * - Grouped by category
 * - Source indicators (default/user/calculated)
 * - Warning for many defaults
 */

export interface Assumption {
    key: string;
    label: string;
    value: string;
    source: 'default' | 'user' | 'calculated';
    category: string;
    isDefault: boolean;
}

interface AssumptionsPanelProps {
    assumptions: Assumption[];
    totalDefaults: number;
    className?: string;
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
    distance: <span className="text-blue-400">📏</span>,
    electrical: <span className="text-amber-400">⚡</span>,
    protection: <span className="text-green-400">🛡️</span>,
};

const CATEGORY_LABELS: Record<string, string> = {
    distance: 'ระยะทาง',
    electrical: 'ค่าทางไฟฟ้า',
    protection: 'การป้องกัน',
};

export const AssumptionsPanel: React.FC<AssumptionsPanelProps> = ({
    assumptions,
    totalDefaults,
    className,
}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

    // Group assumptions by category
    const grouped = assumptions.reduce((acc, item) => {
        const cat = item.category || 'other';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(item);
        return acc;
    }, {} as Record<string, Assumption[]>);

    const toggleCategory = (cat: string) => {
        const newSet = new Set(expandedCategories);
        if (newSet.has(cat)) {
            newSet.delete(cat);
        } else {
            newSet.add(cat);
        }
        setExpandedCategories(newSet);
    };

    return (
        <div className={cn(
            "bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden",
            className
        )}>
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className={cn(
                    "w-full flex items-center justify-between p-4",
                    "text-left transition-colors hover:bg-slate-800/50"
                )}
            >
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "flex items-center justify-center w-8 h-8 rounded-lg",
                        "bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30"
                    )}>
                        <Settings size={16} className="text-violet-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-medium text-white">
                            สมมติฐานที่ใช้ในการออกแบบ
                        </h3>
                        <p className="text-xs text-slate-400 mt-0.5">
                            {assumptions.length} รายการ • {totalDefaults} ค่าเริ่มต้น
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {totalDefaults > 5 && (
                        <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 border border-amber-500/30 rounded text-xs text-amber-400">
                            <AlertTriangle size={12} />
                            <span>ใช้ค่าเริ่มต้นหลายรายการ</span>
                        </div>
                    )}
                    {isExpanded ? (
                        <ChevronDown size={18} className="text-slate-400" />
                    ) : (
                        <ChevronRight size={18} className="text-slate-400" />
                    )}
                </div>
            </button>

            {/* Content */}
            {isExpanded && (
                <div className="border-t border-slate-800">
                    {Object.entries(grouped).map(([category, items]) => (
                        <div key={category} className="border-b border-slate-800/50 last:border-b-0">
                            {/* Category Header */}
                            <button
                                onClick={() => toggleCategory(category)}
                                className="w-full flex items-center gap-2 p-3 pl-4 text-left hover:bg-slate-800/30 transition-colors"
                            >
                                {expandedCategories.has(category) ? (
                                    <ChevronDown size={14} className="text-slate-500" />
                                ) : (
                                    <ChevronRight size={14} className="text-slate-500" />
                                )}
                                {CATEGORY_ICONS[category] || <Info size={14} className="text-slate-400" />}
                                <span className="text-lg text-slate-300">
                                    {CATEGORY_LABELS[category] || category}
                                </span>
                                <span className="text-xs text-slate-500">({items.length})</span>
                            </button>

                            {/* Category Items */}
                            {expandedCategories.has(category) && (
                                <div className="bg-slate-950/50 px-4 py-2">
                                    <table className="w-full text-base">
                                        <thead>
                                            <tr className="text-slate-500 border-b border-slate-800">
                                                <th className="py-2 text-left font-medium">รายการ</th>
                                                <th className="py-2 text-left font-medium">ค่าที่ใช้</th>
                                                <th className="py-2 text-left font-medium">แหล่งที่มา</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {items.map((item) => (
                                                <tr key={item.key} className="border-b border-slate-800/30 last:border-b-0">
                                                    <td className="py-2 text-slate-300">{item.label}</td>
                                                    <td className="py-2 font-mono text-white">{item.value}</td>
                                                    <td className="py-2">
                                                        <span className={cn(
                                                            "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs",
                                                            item.source === 'default' && "bg-slate-700 text-slate-300",
                                                            item.source === 'user' && "bg-emerald-500/20 text-emerald-400",
                                                            item.source === 'calculated' && "bg-sky-500/20 text-sky-400",
                                                        )}>
                                                            {item.source === 'default' && '⚙️ ค่าเริ่มต้น'}
                                                            {item.source === 'user' && '✏️ ผู้ใช้ระบุ'}
                                                            {item.source === 'calculated' && '🔢 คำนวณ'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AssumptionsPanel;
