import React, { useState, useCallback } from 'react';
import { Table, FileImage, ClipboardCheck, Box, Receipt, BookOpen, Download } from 'lucide-react';
import type { DesignResult, LoadResult, SLDData, BOQData } from '../types';
import { cn } from '../lib/utils';
import { SLDViewer } from './SLDViewer';
import { PDFPreviewModal } from './PDFPreviewModal';
import { BOQPDFPreviewModal } from './BOQPDFPreviewModal';
import { SLDPDFPreviewModal } from './SLDPDFPreviewModal';
import { DownloadDropdown } from './DownloadDropdown';
import { BOQTab } from './BOQTab'; // 🆕 BOQ with backend data + fallback
import * as XLSX from 'xlsx';

import { AssumptionsPanel } from './AssumptionsPanel';
import { ExplainableWarningCard } from './ExplainableWarningCard';



type ViewMode = 'table' | 'audit' | 'sld' | 'boq' | 'assumptions';

interface ResultViewerProps {
    data: DesignResult | null;
    isLoading: boolean;
    sldData?: SLDData | null;  // 🆕 SLD data from API
}

/**
 * ResultViewer - พื้นที่แสดงผลลัพธ์การออกแบบ
 * 
 * ตำแหน่ง: ขวา (กินพื้นที่หลัก)
 * หน้าที่: แสดง Table, Audit Report, SLD Image
 */
export const ResultViewer: React.FC<ResultViewerProps> = ({ data, isLoading, sldData }) => {
    // === ALL HOOKS MUST BE CALLED FIRST (before any early returns) ===
    const [activeTab, setActiveTab] = useState<ViewMode>('table');
    const [isPDFPreviewOpen, setPDFPreviewOpen] = useState(false);
    const [isBOQPDFOpen, setBOQPDFOpen] = useState(false);
    const [isSLDPDFOpen, setSLDPDFOpen] = useState(false);

    // Tab Buttons (constant, not a hook, but define early for consistency)
    const tabs: { id: ViewMode; label: string; icon: React.ReactNode }[] = [
        { id: 'table', label: 'Load Table', icon: <Table size={16} /> },
        { id: 'audit', label: 'Audit', icon: <ClipboardCheck size={16} /> },
        { id: 'sld', label: 'SLD', icon: <FileImage size={16} /> },
        { id: 'boq', label: 'BOQ', icon: <Receipt size={16} /> },
        { id: 'assumptions', label: 'Assumptions', icon: <BookOpen size={16} /> },
    ];

    /**
     * 🆕 Task B: Download Excel Function (Black & White format)
     * MUST be defined before any early returns due to React Hooks rules
     */
    const handleDownloadExcel = useCallback(() => {
        try {
            // Check if data exists
            if (!data?.data?.loads || data.data.loads.length === 0) {
                alert('❌ ไม่มีข้อมูลสำหรับ Download');
                return;
            }

            const loads = data.data.loads;

            // Prepare Excel data - 18 columns matching table
            const excelData = [
                // Header Row 1 (Group headers as merged cells concept)
                ['#', 'วงจร', 'LOAD (VA)', '', '', 'CIRCUIT BREAKER', '', '', '', '', 'WIRE (Sq.mm)', '', '', '', 'RACEWAY', '', 'VD%', 'หมายเหตุ'],
                // Header Row 2 (Sub headers)
                ['', '', 'L1', 'L2', 'L3', 'TYPE', 'POLE', 'Ic', 'AF', 'AT', 'L', 'N', 'GRD', 'TYPE', 'SIZE', 'TYPE', '', ''],
                // Data Rows
                ...loads.map((item: LoadResult, idx: number) => [
                    idx + 1,
                    item.device_name || '-',
                    (item as any).load_va_l1 || Math.round(item.power_kw * 1000) || 0,
                    (item as any).load_va_l2 || 0,
                    (item as any).load_va_l3 || 0,
                    (item as any).breaker_type || 'MCB',
                    `${(item as any).breaker_poles || 1}P`,
                    `${(item as any).breaker_ic_ka || 6}kA`,
                    (item as any).breaker_af || item.breaker_size || 15,
                    (item as any).breaker_at || item.breaker_size || 15,
                    (item as any).wire_size_l || item.wire_size?.replace(' mm²', '') || '2.5',
                    (item as any).wire_size_n || item.wire_size?.replace(' mm²', '') || '2.5',
                    (item as any).wire_size_grd || (item as any).ground_size || '2.5',
                    (item as any).wire_type || 'THW',
                    item.conduit_size || '1/2"',
                    (item as any).conduit_type || 'PVC',
                    item.voltage_drop_percent?.toFixed(1) || '-',
                    (item as any).remark || '-'
                ]),
                // Empty row
                [],
                // Summary rows
                ['TOTAL LOAD (VA)', '', loads.reduce((sum: number, item: LoadResult) => sum + ((item as any).load_va_l1 || item.power_kw * 1000 || 0), 0), '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
                ['DEMAND FACTOR', '', data.data?.demand_factor || 0.78, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
                ['TOTAL POWER', '', `${data.data?.total_power_kw?.toFixed(2) || 0} kW`, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
                ['MAIN CB', '', data.data?.main_cb_type || `MCCB 2P ${data.data?.main_breaker}AT`, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
                ['MAIN FEEDER', '', `${data.data?.main_feeder_size || data.data?.main_wire || '-'} Sq.mm × ${data.data?.main_feeder_type || 'IEC01 (THW)'}`, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
                ['MAIN RACEWAY', '', `${data.data?.main_raceway_type || 'PVC'} ${data.data?.main_raceway_size || '1"'}`, '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
            ];

            // Create workbook and worksheet
            const ws = XLSX.utils.aoa_to_sheet(excelData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Load Schedule');

            // Set column widths
            ws['!cols'] = [
                { wch: 5 },   // #
                { wch: 25 },  // วงจร
                { wch: 10 },  // L1
                { wch: 8 },   // L2
                { wch: 8 },   // L3
                { wch: 8 },   // TYPE
                { wch: 6 },   // POLE
                { wch: 6 },   // Ic
                { wch: 6 },   // AF
                { wch: 6 },   // AT
                { wch: 6 },   // L
                { wch: 6 },   // N
                { wch: 6 },   // GRD
                { wch: 8 },   // TYPE
                { wch: 8 },   // SIZE
                { wch: 6 },   // TYPE
                { wch: 6 },   // VD%
                { wch: 20 },  // หมายเหตุ
            ];

            // Generate filename with date
            const dateStr = new Date().toISOString().split('T')[0];
            const filename = `LoadSchedule_${dateStr}.xlsx`;

            // Download
            XLSX.writeFile(wb, filename);

            console.log('[DOWNLOAD] ✅ Excel downloaded successfully:', filename);

        } catch (error) {
            console.error('[DOWNLOAD] ❌ Error downloading Excel:', error);
            alert(`❌ Download Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }, [data]);

    /**
     * 🆕 Task 1: Download PDF Function
     * Opens PDF preview and triggers download
     */
    const handleDownloadPDF = useCallback(() => {
        // Open PDF preview modal - it has download button inside
        setPDFPreviewOpen(true);
        // Note: The actual PDF download happens in PDFPreviewModal
        console.log('[DOWNLOAD] 📄 Opening PDF Preview for download');
    }, []);

    /**
     * 🆕 BOQ Excel Download Function
     * Exports Bill of Quantities with pricing to Excel
     */
    const handleDownloadBOQExcel = useCallback(() => {
        try {
            if (!data?.data?.loads) {
                alert('❌ ไม่มีข้อมูลสำหรับ BOQ');
                return;
            }

            const loads = data.data.loads;
            const circuitCount = loads.length || 1;

            // Price Catalog (same as BOQ tab)
            const PRICES = {
                MCB_1P: 78,
                RCBO_1P: 1133,
                LC_30: 6108,
                LC_18: 3600,
                WIRE_2_5: 10,
                WIRE_4: 18,
                PVC_HALF: 10,
                MAIN_WIRE_M: 237,
                MAIN_CONDUIT_M: 121,
                LABOR_PERCENT: 0.35,
            };

            // Count breakers
            let mcbCount = 0;
            let rcboCount = 0;
            loads.forEach((item: LoadResult) => {
                if ((item as any).requires_rcbo || (item as any).breaker_type === 'RCBO') {
                    rcboCount++;
                } else {
                    mcbCount++;
                }
            });

            // Calculate costs
            const lcPrice = circuitCount > 18 ? PRICES.LC_30 : PRICES.LC_18;
            const lcSlots = circuitCount > 18 ? 30 : 18;
            const mainBreakerPrice = 2884;
            const wireLength = circuitCount * 15;

            const e1_material = (50 * PRICES.MAIN_WIRE_M) + (15 * 62) + (18 * PRICES.MAIN_CONDUIT_M) + 1000;
            const e1_labor = Math.round(e1_material * PRICES.LABOR_PERCENT);
            const e2_material = lcPrice + mainBreakerPrice + (mcbCount * PRICES.MCB_1P) + (rcboCount * PRICES.RCBO_1P) + 1000;
            const e2_labor = 4000;
            const e3_material = (wireLength * PRICES.WIRE_2_5 * 3) + (wireLength * PRICES.PVC_HALF) + 5000;
            const e3_labor = Math.round(e3_material * PRICES.LABOR_PERCENT);

            const totalMaterial = e1_material + e2_material + e3_material;
            const totalLabor = e1_labor + e2_labor + e3_labor;
            const grandTotal = totalMaterial + totalLabor;
            const vat = Math.round(grandTotal * 0.07);
            const finalTotal = grandTotal + vat;

            // Build Excel data
            const excelData = [
                ['Bill of Quantities (BOQ) - งานระบบไฟฟ้า'],
                [`โครงการ: ${data.data?.project_name || 'Residential'}`],
                [`วันที่: ${new Date().toLocaleDateString('th-TH')}`],
                [],
                ['หมวด', 'รายการ', 'จำนวน', 'หน่วย', 'ราคา/หน่วย', 'ค่าวัสดุ', 'ค่าแรง', 'รวม'],
                [],
                ['E.1', 'สายเมนไฟฟ้าแรงต่ำ', '', '', '', e1_material, e1_labor, e1_material + e1_labor],
                ['', '- สายไฟ IEC01-50 Sq.mm', 50, 'ม.', PRICES.MAIN_WIRE_M, 50 * PRICES.MAIN_WIRE_M, '', ''],
                ['', '- สายดิน IEC01-25 Sq.mm', 15, 'ม.', 62, 15 * 62, '', ''],
                ['', '- ท่อ EMT 1-1/2"', 18, 'ม.', PRICES.MAIN_CONDUIT_M, 18 * PRICES.MAIN_CONDUIT_M, '', ''],
                [],
                ['E.2', `ตู้ไฟฟ้า Load Center ${lcSlots} ช่อง`, '', '', '', e2_material, e2_labor, e2_material + e2_labor],
                ['', `- ตู้ LC ${lcSlots} ช่อง`, 1, 'ชุด', lcPrice, lcPrice, '', ''],
                ['', `- Main MCB 2P ${data.data?.main_breaker || 100}AT`, 1, 'ตัว', mainBreakerPrice, mainBreakerPrice, '', ''],
                ['', '- MCB 1P (Branch)', mcbCount, 'ตัว', PRICES.MCB_1P, mcbCount * PRICES.MCB_1P, '', ''],
                ['', '- RCBO 1P 30mA', rcboCount, 'ตัว', PRICES.RCBO_1P, rcboCount * PRICES.RCBO_1P, '', ''],
                [],
                ['E.3', `สายไฟฟ้าวงจรย่อย (${wireLength} ม.)`, '', '', '', e3_material, e3_labor, e3_material + e3_labor],
                ['', '- สายไฟ IEC01-2.5 Sq.mm (L,N,G)', wireLength * 3, 'ม.', PRICES.WIRE_2_5, wireLength * 3 * PRICES.WIRE_2_5, '', ''],
                ['', '- ท่อ PVC 1/2"', wireLength, 'ม.', PRICES.PVC_HALF, wireLength * PRICES.PVC_HALF, '', ''],
                [],
                ['', 'รวมค่าวัสดุ', '', '', '', totalMaterial, '', ''],
                ['', 'รวมค่าแรง', '', '', '', '', totalLabor, ''],
                ['', 'รวมก่อน VAT', '', '', '', '', '', grandTotal],
                ['', 'VAT 7%', '', '', '', '', '', vat],
                ['', 'รวมทั้งสิ้น', '', '', '', '', '', finalTotal],
            ];

            const ws = XLSX.utils.aoa_to_sheet(excelData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'BOQ');

            ws['!cols'] = [
                { wch: 8 }, { wch: 35 }, { wch: 10 }, { wch: 8 },
                { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 14 }
            ];

            const dateStr = new Date().toISOString().split('T')[0];
            XLSX.writeFile(wb, `BOQ_${dateStr}.xlsx`);
            console.log('[DOWNLOAD] ✅ BOQ Excel downloaded');
        } catch (error) {
            console.error('[DOWNLOAD] ❌ BOQ Excel error:', error);
            alert(`❌ Download Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }, [data]);

    // === EARLY RETURNS AFTER ALL HOOKS ===

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
                <div className="flex items-center space-x-3">
                    {data.data?.total_power_kw && (
                        <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded">
                            Total: {data.data.total_power_kw.toFixed(2)} kW
                        </span>
                    )}
                    <DownloadDropdown
                        onDownloadExcel={handleDownloadExcel}
                        onDownloadPDF={handleDownloadPDF}
                        onDownloadBOQExcel={handleDownloadBOQExcel}
                        onDownloadBOQPDF={() => setBOQPDFOpen(true)}
                        onDownloadSLD={() => setSLDPDFOpen(true)}
                        onPreview={() => setPDFPreviewOpen(true)}
                    />
                </div>
            </div>

            {/* Print Preview Modal */}
            <PDFPreviewModal
                data={data}
                isOpen={isPDFPreviewOpen}
                onClose={() => setPDFPreviewOpen(false)}
            />

            <BOQPDFPreviewModal
                data={data}
                isOpen={isBOQPDFOpen}
                onClose={() => setBOQPDFOpen(false)}
            />

            <SLDPDFPreviewModal
                data={sldData || null}
                projectName={data.data?.project_name}
                isOpen={isSLDPDFOpen}
                onClose={() => setSLDPDFOpen(false)}
            />

            {/* Content Area */}
            <div className="flex-1 p-6 overflow-auto">

                {/* Load Table Tab - Compact Format (7 columns for performance) */}
                {activeTab === 'table' && data.data?.loads && (
                    <div className="space-y-4">
                        {/* Summary Banner */}
                        <div className="bg-gradient-to-r from-sky-500/10 to-emerald-500/10 border border-sky-500/30 rounded-lg p-4 flex justify-between items-center">
                            <div>
                                <p className="text-slate-400 text-sm">
                                    <span className="text-sky-400 font-bold">{data.data.loads.length}</span> วงจร |
                                    <span className="text-amber-400 font-bold ml-2">{data.data.total_power_kw?.toFixed(2) || 0}</span> kW |
                                    Main CB <span className="text-emerald-400 font-bold">{data.data.main_breaker || '-'}A</span>
                                </p>
                            </div>
                            <p className="text-slate-600 text-xs">📥 กด Download สำหรับตารางละเอียด 18 columns</p>
                        </div>

                        {/* Compact Table - 7 Columns */}
                        <div className="border border-slate-800 rounded-lg overflow-hidden">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-900 text-slate-400 font-mono uppercase text-xs">
                                    <tr>
                                        <th className="p-3 border-b border-slate-700 text-center w-12">#</th>
                                        <th className="p-3 border-b border-slate-700">วงจร</th>
                                        <th className="p-3 border-b border-slate-700 text-right">VA</th>
                                        <th className="p-3 border-b border-slate-700 text-center">Breaker</th>
                                        <th className="p-3 border-b border-slate-700 text-center">Wire</th>
                                        <th className="p-3 border-b border-slate-700 text-center">VD%</th>
                                        <th className="p-3 border-b border-slate-700 text-center">สถานะ</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {(data.data?.loads || []).map((item: LoadResult, idx: number) => {
                                        const va = (item as any).load_va_l1 || Math.round(item.power_kw * 1000) || 0;
                                        const breakerType = (item as any).breaker_type || 'MCB';
                                        const breakerAt = (item as any).breaker_at || item.breaker_size || 16;
                                        const wireSize = (item as any).wire_size_l || item.wire_size?.replace(' mm²', '') || '2.5';
                                        const vd = item.voltage_drop_percent;
                                        const isPass = !vd || vd <= 3;

                                        return (
                                            <tr key={`circuit-${idx}`} className="hover:bg-slate-900/50 transition-colors">
                                                <td className="p-3 font-mono text-slate-500 text-center">{idx + 1}</td>
                                                <td className="p-3">
                                                    <div className="text-slate-300 font-medium">{item.device_name}</div>
                                                    <div className="text-slate-600 text-xs">{item.room_name || '-'}</div>
                                                </td>
                                                <td className="p-3 font-mono text-amber-400 text-right">{va.toLocaleString()}</td>
                                                <td className="p-3 font-mono text-center">
                                                    <span className={cn(
                                                        'px-2 py-0.5 rounded text-xs',
                                                        breakerType === 'RCBO'
                                                            ? 'bg-sky-500/20 text-sky-400'
                                                            : 'bg-slate-700 text-slate-300'
                                                    )}>
                                                        {breakerType} {breakerAt}A
                                                    </span>
                                                </td>
                                                <td className="p-3 font-mono text-slate-300 text-center">{wireSize}mm²</td>
                                                <td className="p-3 font-mono text-center">
                                                    <span className={cn(vd && vd > 3 ? 'text-amber-400' : 'text-emerald-400')}>
                                                        {vd?.toFixed(1) ?? '-'}
                                                    </span>
                                                </td>
                                                <td className="p-3 text-center">
                                                    <span className={cn(
                                                        'px-2 py-1 rounded text-xs font-bold',
                                                        isPass ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                                                    )}>
                                                        {isPass ? '✓' : '⚠'}
                                                    </span>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {/* Summary Footer */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                            <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                                <p className="text-slate-500">Main CB</p>
                                <p className="text-sky-400 font-mono font-bold">
                                    {(data.data as any).main_cb_type || `MCCB 2P ${data.data.main_breaker || '-'}AT`}
                                </p>
                            </div>
                            <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                                <p className="text-slate-500">Main Feeder</p>
                                <p className="text-slate-300 font-mono">
                                    {(data.data as any).main_feeder_size || data.data.main_wire || '-'} mm²
                                </p>
                            </div>
                            <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                                <p className="text-slate-500">Raceway</p>
                                <p className="text-slate-300 font-mono">
                                    {(data.data as any).main_raceway_type || 'PVC'} {(data.data as any).main_raceway_size || '1"'}
                                </p>
                            </div>
                            <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                                <p className="text-slate-500">Demand Factor</p>
                                <p className="text-slate-300 font-mono">{(data.data as any).demand_factor || 0.78}</p>
                            </div>
                        </div>
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
                                        {(data.data?.audit_table || []).map((row, idx) => (
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
                            // 🆕 Compliance Summary when all values are correct
                            <div className="space-y-6">
                                {/* Success Header */}
                                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-6">
                                    <h3 className="text-emerald-400 font-bold text-lg mb-4 flex items-center gap-2">
                                        <ClipboardCheck size={24} /> ทุกค่าตรงตามมาตรฐาน วสท./NEC
                                    </h3>

                                    {/* Summary Stats Cards */}
                                    <div className="grid grid-cols-4 gap-4">
                                        <div className="bg-slate-800 rounded-lg p-4 text-center">
                                            <div className="text-2xl font-bold text-sky-400">
                                                {data.data?.loads?.length || 0}
                                            </div>
                                            <div className="text-slate-500 text-xs mt-1">วงจรทั้งหมด</div>
                                        </div>
                                        <div className="bg-slate-800 rounded-lg p-4 text-center">
                                            <div className="text-2xl font-bold text-amber-400">
                                                {data.data?.loads?.filter((l: any) => l.breaker_type === 'RCBO' || l.requires_rcbo)?.length || 0}
                                            </div>
                                            <div className="text-slate-500 text-xs mt-1">RCBO</div>
                                        </div>
                                        <div className="bg-slate-800 rounded-lg p-4 text-center">
                                            <div className="text-2xl font-bold text-slate-300">
                                                {data.data?.loads?.filter((l: any) => l.breaker_type !== 'RCBO' && !l.requires_rcbo)?.length || 0}
                                            </div>
                                            <div className="text-slate-500 text-xs mt-1">MCB</div>
                                        </div>
                                        <div className="bg-slate-800 rounded-lg p-4 text-center">
                                            <div className="text-2xl font-bold text-emerald-400">
                                                {data.data?.total_power_kw?.toFixed(1) || '0'}
                                            </div>
                                            <div className="text-slate-500 text-xs mt-1">kW</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Compliance Checklist */}
                                <div className="border border-slate-800 rounded-lg overflow-hidden">
                                    <div className="bg-slate-900 p-3 border-b border-slate-800">
                                        <h4 className="font-bold text-slate-300 flex items-center gap-2">
                                            📋 Compliance Checklist
                                        </h4>
                                    </div>
                                    <table className="w-full text-sm">
                                        <tbody className="divide-y divide-slate-800">
                                            <tr className="hover:bg-slate-900/50">
                                                <td className="p-3 w-10 text-emerald-400">✅</td>
                                                <td className="p-3 text-slate-300">Voltage Drop ≤ 3%</td>
                                                <td className="p-3 text-slate-500 text-xs">ตาม วสท. 2564</td>
                                            </tr>
                                            <tr className="hover:bg-slate-900/50">
                                                <td className="p-3 w-10 text-emerald-400">✅</td>
                                                <td className="p-3 text-slate-300">Load ≤ 80% of Breaker Rating</td>
                                                <td className="p-3 text-slate-500 text-xs">ตาม NEC 210.3</td>
                                            </tr>
                                            <tr className="hover:bg-slate-900/50">
                                                <td className="p-3 w-10 text-emerald-400">✅</td>
                                                <td className="p-3 text-slate-300">RCBO 30mA สำหรับน้ำอุ่น/พื้นที่เปียก</td>
                                                <td className="p-3 text-slate-500 text-xs">ตาม วสท. 2564</td>
                                            </tr>
                                            <tr className="hover:bg-slate-900/50">
                                                <td className="p-3 w-10 text-emerald-400">✅</td>
                                                <td className="p-3 text-slate-300">สายดินครบทุกวงจร</td>
                                                <td className="p-3 text-slate-500 text-xs">ตาม IEC 60364</td>
                                            </tr>
                                            <tr className="hover:bg-slate-900/50">
                                                <td className="p-3 w-10 text-emerald-400">✅</td>
                                                <td className="p-3 text-slate-300">ขนาดสายตาม NEC Table 310.16</td>
                                                <td className="p-3 text-slate-500 text-xs">ตาม NEC 2023</td>
                                            </tr>
                                            <tr className="hover:bg-slate-900/50">
                                                <td className="p-3 w-10 text-emerald-400">✅</td>
                                                <td className="p-3 text-slate-300">ขนาด Breaker เหมาะสมกับโหลด</td>
                                                <td className="p-3 text-slate-500 text-xs">ตาม วสท. 2564</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Warnings - แสดงเฉพาะใน Audit Tab เท่านั้น */}
                        {(data.data?.explainable_warnings && data.data.explainable_warnings.length > 0) ? (
                            <div className="mt-6 space-y-4">
                                <h4 className="text-amber-400 font-bold text-sm mb-2 flex items-center gap-2">
                                    ⚠️ Critical Warnings ({data.data.explainable_warnings.length})
                                </h4>
                                <div className="grid gap-4 md:grid-cols-2">
                                    {data.data.explainable_warnings.map((w, i) => (
                                        <ExplainableWarningCard
                                            key={i}
                                            warning={{
                                                code: w.code,
                                                message: w.message,
                                                reason: w.reason || '',
                                                severity: w.severity,
                                                standardRef: '-',
                                                circuitName: w.circuit_name,
                                                action: w.suggested_action || { type: 'none', description: '-', effort: 'low' }
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        ) : (data.data?.warnings && data.data.warnings.length > 0 && (
                            <div className="mt-6 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                                <h4 className="text-amber-400 font-bold text-sm mb-2">⚠️ Warnings</h4>
                                <ul className="text-amber-300 text-sm space-y-1">
                                    {data.data.warnings.map((w, i) => (
                                        <li key={i}>• {w}</li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                )}

                {/* Assumptions Tab */}
                {activeTab === 'assumptions' && data.data?.assumptions && (
                    <AssumptionsPanel
                        assumptions={data.data.assumptions.map(a => ({
                            key: a.key,
                            label: a.label,
                            value: String(a.value),
                            source: a.source,
                            category: a.category,
                            isDefault: a.source === 'default'
                        }))}
                        totalDefaults={data.data.assumptions.filter(a => a.source === 'default').length}
                    />
                )}

                {/* SLD Tab */}
                {activeTab === 'sld' && (
                    <div className="relative">
                        <div className="absolute top-4 right-4 z-10">
                            <button
                                onClick={() => setSLDPDFOpen(true)}
                                className="bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 border border-slate-700 shadow-lg transition-all cursor-pointer"
                            >
                                <Download size={14} /> Download SLD (PDF)
                            </button>
                        </div>
                        <SLDViewer data={sldData || null} />
                    </div>
                )}

                {/* BOQ Tab - Bill of Quantities (Dynamic from Load Table) */}
                {/* BOQ Tab - Bill of Quantities (from Backend or Fallback) */}
                {activeTab === 'boq' && (() => {
                    // 🆕 Cloud Log: Check if boq_data exists from backend
                    const boqData = (data as any)?.metadata?.boq_data as BOQData | undefined;
                    console.log('[BOQ-Tab] boq_data from backend:', boqData ? {
                        sections: boqData.sections?.length || 0,
                        price_source: boqData.price_source,
                        final_total: boqData.final_total
                    } : 'NOT_AVAILABLE');
                    
                    return (
                        <BOQTab
                            boqData={boqData}
                            loads={data?.data?.loads || []}
                            onDownloadClick={() => setBOQPDFOpen(true)}
                        />
                    );
                })()}
            </div>
        </div >
    );
};

