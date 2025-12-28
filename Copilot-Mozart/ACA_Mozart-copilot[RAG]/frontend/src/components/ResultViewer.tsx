import React, { useState } from 'react';
import { Table, FileImage, ClipboardCheck, Box, Download } from 'lucide-react';
import type { DesignResult, LoadResult } from '../types';
import { cn } from '../lib/utils';

type ViewMode = 'table' | 'audit' | 'sld';

interface ResultViewerProps {
    data: DesignResult | null;
    isLoading: boolean;
}

/**
 * ResultViewer - พื้นที่แสดงผลลัพธ์การออกแบบ
 * 
 * ตำแหน่ง: ขวา (กินพื้นที่หลัก)
 * หน้าที่: แสดง Table, Audit Report, SLD Image
 */
export const ResultViewer: React.FC<ResultViewerProps> = ({ data, isLoading }) => {
    const [activeTab, setActiveTab] = useState<ViewMode>('table');

    // Loading State
    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center bg-slate-950">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="font-mono text-sky-500 animate-pulse">CALCULATING...</p>
                    <p className="text-slate-600 text-xs mt-2">กำลังคำนวณระบบไฟฟ้า</p>
                </div>
            </div>
        );
    }

    // Empty State
    if (!data) {
        return (
            <div className="h-full flex items-center justify-center bg-slate-950 border-l border-slate-800">
                <div className="text-center">
                    <Box size={48} className="text-slate-800 mx-auto mb-4" />
                    <p className="text-slate-500 font-mono text-sm">NO DATA LOADED</p>
                    <p className="text-slate-700 text-xs mt-2">พิมพ์คำสั่งเพื่อเริ่มออกแบบ</p>
                </div>
            </div>
        );
    }

    // Tab Buttons
    const tabs: { id: ViewMode; label: string; icon: React.ReactNode }[] = [
        { id: 'table', label: 'Load Table', icon: <Table size={16} /> },
        { id: 'audit', label: 'Audit', icon: <ClipboardCheck size={16} /> },
        { id: 'sld', label: 'SLD', icon: <FileImage size={16} /> },
    ];

    return (
        <div className="h-full flex flex-col bg-slate-950 border-l border-slate-800">
            {/* Toolbar */}
            <div className="h-14 border-b border-slate-800 flex items-center justify-between px-4 bg-slate-900">
                {/* Tabs */}
                <div className="flex items-center space-x-4">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "flex items-center space-x-2 text-sm px-3 py-1.5 rounded transition-colors",
                                activeTab === tab.id
                                    ? 'text-sky-400 bg-sky-500/10'
                                    : 'text-slate-500 hover:text-slate-300'
                            )}
                        >
                            {tab.icon}
                            <span>{tab.label}</span>
                        </button>
                    ))}
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2">
                    {data.data?.total_power_kw && (
                        <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded">
                            Total: {data.data.total_power_kw.toFixed(2)} kW
                        </span>
                    )}
                    <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors">
                        <Download size={16} />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 p-6 overflow-auto">

                {/* Load Table Tab */}
                {activeTab === 'table' && data.data?.loads && (
                    <div className="border border-slate-800 rounded-lg overflow-hidden">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-900 text-slate-400 font-mono text-xs uppercase">
                                <tr>
                                    <th className="p-3 border-b border-slate-700">ห้อง/อุปกรณ์</th>
                                    <th className="p-3 border-b border-slate-700">Power (kW)</th>
                                    <th className="p-3 border-b border-slate-700">Current (A)</th>
                                    <th className="p-3 border-b border-slate-700">Breaker</th>
                                    <th className="p-3 border-b border-slate-700">Wire Size</th>
                                    <th className="p-3 border-b border-slate-700">VD%</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {data.data.loads.map((item: LoadResult, idx: number) => (
                                    <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                                        <td className="p-3">
                                            <div className="text-slate-300">{item.device_name}</div>
                                            <div className="text-slate-600 text-xs">{item.room_name}</div>
                                        </td>
                                        <td className="p-3 font-mono text-slate-400">{item.power_kw.toFixed(2)}</td>
                                        <td className="p-3 font-mono text-sky-400 font-bold">{item.current_a.toFixed(2)}</td>
                                        <td className="p-3 font-mono text-slate-300">{item.breaker_size}A</td>
                                        <td className="p-3 font-mono text-slate-300">{item.wire_size}</td>
                                        <td className="p-3 font-mono">
                                            <span className={cn(
                                                item.voltage_drop_percent && item.voltage_drop_percent > 3
                                                    ? 'text-amber-400'
                                                    : 'text-emerald-400'
                                            )}>
                                                {item.voltage_drop_percent?.toFixed(2) ?? '-'}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Audit Tab */}
                {activeTab === 'audit' && (
                    <div>
                        {data.data?.audit_table ? (
                            <div className="border border-slate-800 rounded-lg overflow-hidden">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-900 text-slate-400 font-mono text-xs uppercase">
                                        <tr>
                                            <th className="p-3 border-b border-slate-700">รายการตรวจสอบ</th>
                                            <th className="p-3 border-b border-slate-700">ค่า User</th>
                                            <th className="p-3 border-b border-slate-700">ค่าแนะนำ</th>
                                            <th className="p-3 border-b border-slate-700">สถานะ</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800">
                                        {data.data.audit_table.map((row, idx) => (
                                            <tr key={idx} className="hover:bg-slate-900/50">
                                                <td className="p-3 text-slate-300">{row.check}</td>
                                                <td className="p-3 font-mono text-slate-400">{String(row.user_value)}</td>
                                                <td className="p-3 font-mono text-slate-400">{String(row.recommended_value)}</td>
                                                <td className="p-3">
                                                    <span className={cn(
                                                        "px-2 py-1 rounded text-xs font-bold uppercase",
                                                        row.status === 'PASS' && 'bg-emerald-500/20 text-emerald-400',
                                                        row.status === 'FAIL' && 'bg-red-500/20 text-red-400',
                                                        row.status === 'WARN' && 'bg-amber-500/20 text-amber-400'
                                                    )}>
                                                        {row.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center text-slate-500 py-20">
                                <ClipboardCheck size={48} className="mx-auto mb-4 text-slate-700" />
                                <p>ไม่มีข้อมูล Audit</p>
                            </div>
                        )}
                    </div>
                )}

                {/* SLD Tab */}
                {activeTab === 'sld' && (
                    <div className="flex justify-center items-start">
                        {data.data?.sld_image_url ? (
                            <img
                                src={data.data.sld_image_url}
                                alt="Single Line Diagram"
                                className="max-w-full border border-slate-800 rounded-lg shadow-2xl"
                            />
                        ) : (
                            <div className="text-center text-slate-500 py-20">
                                <FileImage size={48} className="mx-auto mb-4 text-slate-700" />
                                <p>ยังไม่มี SLD</p>
                                <p className="text-xs text-slate-600 mt-2">Backend ยังไม่ส่งภาพมา</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Warnings */}
                {data.data?.warnings && data.data.warnings.length > 0 && (
                    <div className="mt-6 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                        <h4 className="text-amber-400 font-bold text-sm mb-2">⚠️ Warnings</h4>
                        <ul className="text-amber-300 text-sm space-y-1">
                            {data.data.warnings.map((w, i) => (
                                <li key={i}>• {w}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
};
