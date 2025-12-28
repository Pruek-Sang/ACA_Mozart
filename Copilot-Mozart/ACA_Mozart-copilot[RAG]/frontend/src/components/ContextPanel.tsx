import React, { useState } from 'react';
import { Settings, AlertCircle, ChevronUp, ChevronDown } from 'lucide-react';
import type { SiteContext } from '../types';
import { cn } from '../lib/utils';

interface ContextPanelProps {
    context: SiteContext;
    onContextChange: (newContext: SiteContext) => void;
    isDirty: boolean;
}

/**
 * ContextPanel - แผงควบคุมค่าเงื่อนไขทางเทคนิค (Collapsible)
 * 
 * ตำแหน่ง: ซ้ายล่าง (ใต้ ChatPanel)
 * หน้าที่: ให้ User ปรับค่าโดยไม่ต้องพิมพ์ใน Chat
 * 
 * 🆕 Collapsible: กดยุบ/ขยายได้ เพื่อเพิ่มพื้นที่ Chat
 * 
 * ⚠️ Fields เหล่านี้ตรงกับ API Contract (snake_case)
 */
export const ContextPanel: React.FC<ContextPanelProps> = ({
    context,
    onContextChange,
    isDirty
}) => {
    // 🆕 Collapsible state - default expanded
    const [isExpanded, setIsExpanded] = useState(true);

    const handleChange = (key: keyof SiteContext, value: string) => {
        onContextChange({ ...context, [key]: value });
    };

    return (
        <div className="bg-slate-950 border-r border-slate-800 flex flex-col">
            {/* Header - Always visible, clickable to toggle */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-3 border-b border-t border-slate-800 flex justify-between items-center bg-slate-900 hover:bg-slate-800/50 transition-colors cursor-pointer w-full"
            >
                <div className="flex items-center space-x-2">
                    <Settings size={14} className="text-sky-500" />
                    <span className="text-xs text-slate-400 font-mono uppercase">Site Context</span>
                    {/* Collapsed indicator showing current values */}
                    {!isExpanded && (
                        <span className="text-[10px] text-slate-500 ml-2">
                            ({context.distance_to_transformer}, {context.installation_area})
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {isDirty && (
                        <span className="text-[10px] px-2 py-0.5 bg-amber-500 text-black font-bold rounded-full animate-pulse flex items-center gap-1">
                            <AlertCircle size={10} />
                            MODIFIED
                        </span>
                    )}
                    {/* Toggle Arrow */}
                    {isExpanded ? (
                        <ChevronDown size={16} className="text-slate-500" />
                    ) : (
                        <ChevronUp size={16} className="text-slate-500" />
                    )}
                </div>
            </button>

            {/* Settings Grid - Collapsible with animation */}
            <div
                className={cn(
                    "overflow-hidden transition-all duration-300 ease-in-out",
                    isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
                )}
            >
                <div className="p-4 space-y-4 overflow-y-auto">

                    {/* Distance to Transformer */}
                    <div className="space-y-1">
                        <label className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                            ระยะหม้อแปลง (Distance)
                        </label>
                        <select
                            value={context.distance_to_transformer}
                            onChange={(e) => handleChange('distance_to_transformer', e.target.value)}
                            className={cn(
                                "w-full bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded p-2",
                                "focus:border-sky-500 outline-none transition-colors"
                            )}
                        >
                            <option value="less_than_50m">น้อยกว่า 50m (kA สูง)</option>
                            <option value="50_100m">50-100m</option>
                            <option value="more_than_100m">มากกว่า 100m (kA ต่ำ)</option>
                        </select>
                    </div>

                    {/* Installation Area */}
                    <div className="space-y-1">
                        <label className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                            พื้นที่ติดตั้ง (Installation)
                        </label>
                        <select
                            value={context.installation_area}
                            onChange={(e) => handleChange('installation_area', e.target.value)}
                            className={cn(
                                "w-full bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded p-2",
                                "focus:border-sky-500 outline-none transition-colors"
                            )}
                        >
                            <option value="indoor">ในอาคาร (Indoor)</option>
                            <option value="high_temp">อุณหภูมิสูง (High Temp)</option>
                            <option value="outdoor">กลางแจ้ง (Outdoor)</option>
                            <option value="underground">ใต้ดิน (Underground)</option>
                        </select>
                    </div>

                    {/* Panel Type */}
                    <div className="space-y-1">
                        <label className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                            ประเภทตู้ไฟ (Panel Type)
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            {(['main', 'sub'] as const).map(type => (
                                <button
                                    key={type}
                                    onClick={() => handleChange('panel_type', type)}
                                    className={cn(
                                        "py-2 text-xs font-mono border rounded transition-colors uppercase",
                                        context.panel_type === type
                                            ? 'bg-sky-600 text-white border-sky-500'
                                            : 'bg-slate-900 text-slate-400 border-slate-700 hover:border-slate-500'
                                    )}
                                >
                                    {type === 'main' ? 'ตู้เมน' : 'ตู้ย่อย'}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Conduit Grouping */}
                    <div className="space-y-1">
                        <label className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                            จำนวนสายในท่อ (Conduit)
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                            {(['1', '2-3', '4-6'] as const).map(group => (
                                <button
                                    key={group}
                                    onClick={() => handleChange('conduit_grouping', group)}
                                    className={cn(
                                        "py-2 text-xs font-mono border rounded transition-colors",
                                        context.conduit_grouping === group
                                            ? 'bg-sky-600 text-white border-sky-500'
                                            : 'bg-slate-900 text-slate-400 border-slate-700 hover:border-slate-500'
                                    )}
                                >
                                    {group} เส้น
                                </button>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};
