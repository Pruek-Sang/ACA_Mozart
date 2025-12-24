// src/components/AuditPane.tsx
// แสดง Audit Report จาก Backend (ขวา)
// Replaces FloorPlanVisualizer - 2025-12-25

import { useMemo } from 'react';
import { CheckCircle, XCircle, AlertTriangle, ClipboardCheck } from 'lucide-react';

interface AuditPaneProps {
    chatText: string; // ข้อความจาก bot response
}

interface AuditItem {
    circuit: string;
    item: string;
    userValue: string;
    autoValue: string;
    status: 'PASS' | 'FAIL' | 'WARN';
}

// Parse Audit section from markdown
function parseAuditFromMarkdown(text: string): AuditItem[] {
    const items: AuditItem[] = [];

    // Find Audit Report section
    const auditMatch = text.match(/## 🔍 รายงานตรวจสอบ[\s\S]*?\|[\s\S]*?(?=##|$)/);
    if (!auditMatch) return items;

    const auditSection = auditMatch[0];

    // Parse table rows (skip header and separator)
    const rows = auditSection.split('\n').filter(line =>
        line.startsWith('|') &&
        !line.includes('---') &&
        !line.includes('โหลด') &&
        !line.includes('รายการ')
    );

    for (const row of rows) {
        const cells = row.split('|').map(c => c.trim()).filter(c => c);
        if (cells.length >= 5) {
            // Extract value from HTML span if present
            const userValMatch = cells[2].match(/<b>([^<]+)<\/b>/) || [null, cells[2]];
            const userValue = userValMatch[1] || cells[2];

            // Determine status from emoji
            let status: 'PASS' | 'FAIL' | 'WARN' = 'PASS';
            if (cells[4].includes('❌')) status = 'FAIL';
            else if (cells[4].includes('⚠️')) status = 'WARN';

            items.push({
                circuit: cells[0],
                item: cells[1],
                userValue: userValue,
                autoValue: cells[3],
                status
            });
        }
    }

    return items;
}

// Check if text contains audit section
function hasAuditSection(text: string): boolean {
    return text.includes('🔍 รายงานตรวจสอบ') || text.includes('Audit Report');
}

export function AuditPane({ chatText }: AuditPaneProps) {
    const auditItems = useMemo(() => parseAuditFromMarkdown(chatText), [chatText]);
    const hasAudit = hasAuditSection(chatText);

    const passCount = auditItems.filter(i => i.status === 'PASS').length;
    const failCount = auditItems.filter(i => i.status === 'FAIL').length;
    const warnCount = auditItems.filter(i => i.status === 'WARN').length;

    return (
        <div className="h-full flex flex-col bg-gradient-to-br from-gray-900/90 to-gray-950/90 rounded-3xl border border-gray-700/50 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-700/50 bg-gray-800/30">
                <div className="flex items-center gap-3">
                    <ClipboardCheck className="w-6 h-6 text-indigo-400" />
                    <h2 className="text-lg font-semibold text-white">🔍 Audit Report</h2>
                </div>
                <p className="text-sm text-gray-400 mt-1">
                    ตรวจสอบค่าที่ผู้ใช้ระบุ vs ค่าที่ระบบแนะนำ
                </p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                {!hasAudit ? (
                    // No audit data
                    <div className="h-full flex flex-col items-center justify-center text-center">
                        <div className="w-20 h-20 rounded-full bg-gray-800/50 flex items-center justify-center mb-4">
                            <ClipboardCheck className="w-10 h-10 text-gray-600" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-400 mb-2">
                            ยังไม่มีข้อมูล Audit
                        </h3>
                        <p className="text-sm text-gray-500 max-w-xs">
                            ลองป้อนค่า breaker หรือ wire size เช่น:<br />
                            <span className="text-indigo-400">"น้ำอุ่น 3500W 16a"</span>
                        </p>
                    </div>
                ) : auditItems.length === 0 ? (
                    // Has audit section but no items parsed
                    <div className="h-full flex flex-col items-center justify-center text-center">
                        <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
                        <h3 className="text-lg font-medium text-green-400">
                            ไม่มีรายการ Audit
                        </h3>
                        <p className="text-sm text-gray-400">
                            ไม่พบค่าที่ผู้ใช้ระบุเอง
                        </p>
                    </div>
                ) : (
                    // Show audit items
                    <div className="space-y-4">
                        {/* Summary */}
                        <div className="flex gap-4 mb-6">
                            <div className="flex-1 bg-green-900/30 rounded-xl p-4 border border-green-700/30">
                                <div className="flex items-center gap-2">
                                    <CheckCircle className="w-5 h-5 text-green-400" />
                                    <span className="text-2xl font-bold text-green-400">{passCount}</span>
                                </div>
                                <p className="text-xs text-green-300/70 mt-1">ผ่าน</p>
                            </div>
                            {warnCount > 0 && (
                                <div className="flex-1 bg-yellow-900/30 rounded-xl p-4 border border-yellow-700/30">
                                    <div className="flex items-center gap-2">
                                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                                        <span className="text-2xl font-bold text-yellow-400">{warnCount}</span>
                                    </div>
                                    <p className="text-xs text-yellow-300/70 mt-1">เตือน</p>
                                </div>
                            )}
                            <div className="flex-1 bg-red-900/30 rounded-xl p-4 border border-red-700/30">
                                <div className="flex items-center gap-2">
                                    <XCircle className="w-5 h-5 text-red-400" />
                                    <span className="text-2xl font-bold text-red-400">{failCount}</span>
                                </div>
                                <p className="text-xs text-red-300/70 mt-1">ไม่ผ่าน</p>
                            </div>
                        </div>

                        {/* Audit Items */}
                        <div className="space-y-3">
                            {auditItems.map((item, idx) => (
                                <div
                                    key={idx}
                                    className={`p-4 rounded-xl border ${item.status === 'FAIL'
                                            ? 'bg-red-900/20 border-red-700/40'
                                            : item.status === 'WARN'
                                                ? 'bg-yellow-900/20 border-yellow-700/40'
                                                : 'bg-green-900/20 border-green-700/40'
                                        }`}
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium text-white">{item.circuit}</span>
                                        {item.status === 'FAIL' ? (
                                            <XCircle className="w-5 h-5 text-red-400" />
                                        ) : item.status === 'WARN' ? (
                                            <AlertTriangle className="w-5 h-5 text-yellow-400" />
                                        ) : (
                                            <CheckCircle className="w-5 h-5 text-green-400" />
                                        )}
                                    </div>
                                    <div className="flex items-center gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-400">{item.item}: </span>
                                            <span className={`font-bold ${item.status === 'FAIL' ? 'text-red-400' :
                                                    item.status === 'WARN' ? 'text-yellow-400' : 'text-green-400'
                                                }`}>
                                                {item.userValue}
                                            </span>
                                        </div>
                                        <span className="text-gray-500">vs</span>
                                        <div>
                                            <span className="text-gray-400">แนะนำ: </span>
                                            <span className="text-blue-400 font-medium">{item.autoValue}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-gray-700/50 bg-gray-800/20">
                <p className="text-xs text-gray-500 text-center">
                    ค่าที่แนะนำอ้างอิงจากมาตรฐาน วสท. 2564
                </p>
            </div>
        </div>
    );
}

export default AuditPane;
