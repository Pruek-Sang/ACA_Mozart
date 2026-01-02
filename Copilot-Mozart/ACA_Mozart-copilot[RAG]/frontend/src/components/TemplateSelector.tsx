import React, { useState } from 'react';
import { Settings, Check, ChevronDown, Plus, Edit2, Trash2 } from 'lucide-react';
import { cn } from '../lib/utils';

/**
 * TemplateSelector - Select and manage design templates
 */

interface TemplateDefaults {
    powerFactor: number;
    safetyFactor: number;
    vdLimitBranch: number;
    wastage: number;
    preferredBrand: string;
    conduitType: string;
}

interface Template {
    id: string;
    name: string;
    description: string;
    isDefault: boolean;
    isSystem: boolean;
    defaults: TemplateDefaults;
}

interface TemplateSelectorProps {
    templates: Template[];
    selectedId: string;
    onSelect: (id: string) => void;
    onEdit?: (id: string) => void;
    onDelete?: (id: string) => void;
    onCreateNew?: () => void;
    className?: string;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
    templates,
    selectedId,
    onSelect,
    onEdit,
    onDelete,
    onCreateNew,
    className,
}) => {
    const [isOpen, setIsOpen] = useState(false);

    const selectedTemplate = templates.find(t => t.id === selectedId);

    return (
        <div className={cn("relative", className)}>
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "w-full flex items-center justify-between gap-3 p-3 rounded-lg",
                    "bg-slate-800 border border-slate-700 hover:border-slate-600",
                    "transition-colors"
                )}
            >
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "flex items-center justify-center w-8 h-8 rounded-lg",
                        "bg-gradient-to-br from-cyan-500/20 to-blue-500/20",
                        "border border-cyan-500/30"
                    )}>
                        <Settings size={16} className="text-cyan-400" />
                    </div>
                    <div className="text-left">
                        <p className="text-sm font-medium text-white">
                            {selectedTemplate?.name || 'เลือก Template'}
                        </p>
                        <p className="text-xs text-slate-400">
                            {selectedTemplate?.description || 'กดเพื่อเลือก'}
                        </p>
                    </div>
                </div>
                <ChevronDown
                    className={cn(
                        "text-slate-400 transition-transform",
                        isOpen && "rotate-180"
                    )}
                    size={18}
                />
            </button>

            {/* Dropdown */}
            {isOpen && (
                <div className={cn(
                    "absolute top-full left-0 right-0 mt-2 z-50",
                    "bg-slate-900 border border-slate-700 rounded-lg shadow-xl",
                    "overflow-hidden animate-in fade-in-0 zoom-in-95"
                )}>
                    {/* Templates List */}
                    <div className="max-h-64 overflow-y-auto">
                        {templates.map((template) => (
                            <div
                                key={template.id}
                                className={cn(
                                    "flex items-center justify-between p-3 cursor-pointer",
                                    "border-b border-slate-800 last:border-b-0",
                                    selectedId === template.id
                                        ? "bg-cyan-500/10"
                                        : "hover:bg-slate-800/50"
                                )}
                                onClick={() => {
                                    onSelect(template.id);
                                    setIsOpen(false);
                                }}
                            >
                                <div className="flex items-center gap-3">
                                    {/* Selection indicator */}
                                    <div className={cn(
                                        "w-5 h-5 rounded-full border-2 flex items-center justify-center",
                                        selectedId === template.id
                                            ? "border-cyan-500 bg-cyan-500"
                                            : "border-slate-600"
                                    )}>
                                        {selectedId === template.id && (
                                            <Check size={12} className="text-white" />
                                        )}
                                    </div>

                                    <div>
                                        <p className={cn(
                                            "text-sm font-medium",
                                            selectedId === template.id ? "text-cyan-400" : "text-white"
                                        )}>
                                            {template.name}
                                        </p>
                                        <p className="text-xs text-slate-400">
                                            {template.description}
                                        </p>
                                    </div>
                                </div>

                                {/* Actions */}
                                {!template.isSystem && (
                                    <div className="flex items-center gap-1">
                                        {onEdit && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onEdit(template.id);
                                                }}
                                                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
                                            >
                                                <Edit2 size={14} />
                                            </button>
                                        )}
                                        {onDelete && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onDelete(template.id);
                                                }}
                                                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        )}
                                    </div>
                                )}

                                {template.isSystem && (
                                    <span className="text-[10px] px-2 py-0.5 bg-slate-700 text-slate-400 rounded">
                                        System
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Create New Button */}
                    {onCreateNew && (
                        <button
                            onClick={() => {
                                onCreateNew();
                                setIsOpen(false);
                            }}
                            className={cn(
                                "w-full flex items-center gap-2 p-3",
                                "border-t border-slate-800",
                                "text-cyan-400 hover:bg-cyan-500/10 transition-colors"
                            )}
                        >
                            <Plus size={16} />
                            <span className="text-sm">สร้าง Template ใหม่</span>
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

export default TemplateSelector;
