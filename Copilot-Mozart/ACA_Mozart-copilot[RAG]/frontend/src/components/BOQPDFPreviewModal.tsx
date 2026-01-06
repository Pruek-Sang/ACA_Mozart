import React, { useRef, useState } from 'react';
import { X, Download, Printer, Loader2, FileSpreadsheet } from 'lucide-react';
import type { DesignResult, LoadResult } from '../types';
import html2pdf from 'html2pdf.js';
import * as XLSX from 'xlsx';

interface BOQPDFPreviewModalProps {
    data: DesignResult;
    isOpen: boolean;
    onClose: () => void;
}

/**
 * BOQ PDF Preview Modal
 * Black & White A4 Landscape format matching professional standards
 */
export const BOQPDFPreviewModal: React.FC<BOQPDFPreviewModalProps> = ({ data, isOpen, onClose }) => {
    const contentRef = useRef<HTMLDivElement>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    if (!isOpen) return null;

    const loads = data.data?.loads || [];
    const circuitCount = loads.length || 1;

    // 🔧 DEBUG
    console.log('[BOQ-PDF-DEBUG] loads:', loads.length);
    console.log('[BOQ-PDF-DEBUG] sample load:', loads[0]);

    // Price Catalog (cheapest brands)
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

    // Calculate E.1 (Main Cable)
    const e1_material = (50 * PRICES.MAIN_WIRE_M) + (15 * 62) + (18 * PRICES.MAIN_CONDUIT_M) + 1000;
    const e1_labor = Math.round(e1_material * PRICES.LABOR_PERCENT);
    const e1_total = e1_material + e1_labor;

    // Calculate E.2 (Load Center + Breakers)
    const lcPrice = circuitCount > 18 ? PRICES.LC_30 : PRICES.LC_18;
    const lcSlots = circuitCount > 18 ? 30 : 18;
    const mainBreakerPrice = 2884;
    const mcbTotal = mcbCount * PRICES.MCB_1P;
    const rcboTotal = rcboCount * PRICES.RCBO_1P;
    const e2_material = lcPrice + mainBreakerPrice + mcbTotal + rcboTotal + 1000;
    const e2_labor = 4000;
    const e2_total = e2_material + e2_labor;

    // Calculate E.3 (Branch Wiring)
    const wireLength = circuitCount * 15;
    const e3_material = (wireLength * PRICES.WIRE_2_5 * 3) + (wireLength * PRICES.PVC_HALF) + 5000;
    const e3_labor = Math.round(e3_material * PRICES.LABOR_PERCENT);
    const e3_total = e3_material + e3_labor;

    // Grand totals
    const totalMaterial = e1_material + e2_material + e3_material;
    const totalLabor = e1_labor + e2_labor + e3_labor;
    const grandTotal = totalMaterial + totalLabor;
    const vat = Math.round(grandTotal * 0.07);
    const finalTotal = grandTotal + vat;

    console.log('[BOQ-PDF-DEBUG] totals:', { e1_total, e2_total, e3_total, grandTotal, finalTotal });

    const handleDownloadPDF = async () => {
        if (!contentRef.current) return;
        setIsGenerating(true);

        const opt = {
            margin: 5,
            filename: `BOQ-${data.data?.project_name || 'Project'}.pdf`,
            image: { type: 'jpeg' as const, quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'portrait' as const }
        };

        try {
            await html2pdf().set(opt).from(contentRef.current).save();
        } catch (error) {
            console.error("[BOQ-PDF] Generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownloadExcel = () => {
        const excelData = [
            ['BILL OF QUANTITIES (BOQ)'],
            ['โปรเจกต์:', data.data?.project_name || 'บ้านพักอาศัย'],
            ['จำนวนวงจร:', circuitCount],
            [],
            ['หมวด', 'รายการ', 'จำนวน', 'หน่วย', 'ราคา/หน่วย', 'ค่าวัสดุ', 'ค่าแรง', 'รวม'],
            ['E.1', 'สายเมนไฟฟ้าแรงต่ำ + ท่อ EMT', 1, 'ชุด', e1_material, e1_material, e1_labor, e1_total],
            ['E.2', `ตู้ไฟฟ้า LC-${lcSlots} + Main CB + Branch CBs`, 1, 'ชุด', e2_material, e2_material, e2_labor, e2_total],
            ['', `- Load Center ${lcSlots} ช่อง`, 1, 'ชุด', lcPrice, '', '', ''],
            ['', `- Main MCB 2P ${data.data?.main_breaker || 100}AT`, 1, 'ตัว', mainBreakerPrice, '', '', ''],
            ['', `- MCB 1P (Branch)`, mcbCount, 'ตัว', PRICES.MCB_1P, '', '', ''],
            ['', `- RCBO 1P 30mA`, rcboCount, 'ตัว', PRICES.RCBO_1P, '', '', ''],
            ['E.3', `สายไฟฟ้า + ท่อ PVC (${wireLength} ม.)`, 1, 'ชุด', e3_material, e3_material, e3_labor, e3_total],
            [],
            ['', '', '', '', 'รวมค่าวัสดุ', totalMaterial, '', ''],
            ['', '', '', '', 'รวมค่าแรง', '', totalLabor, ''],
            ['', '', '', '', 'รวมก่อน VAT', '', '', grandTotal],
            ['', '', '', '', 'VAT 7%', '', '', vat],
            ['', '', '', '', 'รวมทั้งสิ้น', '', '', finalTotal],
        ];

        const ws = XLSX.utils.aoa_to_sheet(excelData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'BOQ');

        ws['!cols'] = [
            { wch: 8 }, { wch: 35 }, { wch: 8 }, { wch: 8 },
            { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }
        ];

        XLSX.writeFile(wb, `BOQ_${new Date().toISOString().split('T')[0]}.xlsx`);
        console.log('[BOQ-EXCEL] Downloaded successfully');
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 w-full max-w-4xl h-[90vh] rounded-xl border border-slate-700 flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <Printer size={20} className="text-amber-400" />
                        BOQ Preview (Bill of Quantities)
                    </h3>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleDownloadExcel}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer"
                        >
                            <FileSpreadsheet size={16} />
                            Excel
                        </button>
                        <button
                            onClick={handleDownloadPDF}
                            disabled={isGenerating}
                            className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 cursor-pointer"
                        >
                            {isGenerating ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                            PDF
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors cursor-pointer"
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Preview Area */}
                <div className="flex-1 overflow-y-auto p-8 bg-slate-800 flex justify-center">
                    {/* A4 Portrait Container - Black & White */}
                    <div
                        ref={contentRef}
                        className="bg-white text-black w-[210mm] min-h-[297mm] h-fit p-[15mm] shadow-lg"
                        style={{ fontFamily: 'Sarabun, sans-serif' }}
                    >
                        {/* Title */}
                        <div className="text-center font-bold mb-6 uppercase text-lg border-b-2 border-black pb-2">
                            BILL OF QUANTITIES (BOQ)
                        </div>

                        {/* Project Info */}
                        <div className="border border-black mb-4 text-sm">
                            <div className="grid grid-cols-2 gap-1 p-2">
                                <div><strong>PROJECT:</strong> {data.data?.project_name || 'บ้านพักอาศัย'}</div>
                                <div><strong>DATE:</strong> {new Date().toLocaleDateString('th-TH')}</div>
                                <div><strong>CIRCUITS:</strong> {circuitCount} วงจร ({mcbCount} MCB + {rcboCount} RCBO)</div>
                                <div><strong>MAIN CB:</strong> {data.data?.main_cb_type || `MCCB 2P ${data.data?.main_breaker || 100}AT`}</div>
                            </div>
                        </div>

                        {/* BOQ Table */}
                        <table className="w-full text-xs border-collapse border border-black mb-4">
                            <thead>
                                <tr className="bg-gray-200 font-bold text-center">
                                    <th className="border border-black p-1 w-12">หมวด</th>
                                    <th className="border border-black p-1">รายการ</th>
                                    <th className="border border-black p-1 w-16">จำนวน</th>
                                    <th className="border border-black p-1 w-20">ค่าวัสดุ</th>
                                    <th className="border border-black p-1 w-20">ค่าแรง</th>
                                    <th className="border border-black p-1 w-20">รวม</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td className="border border-black p-1 font-bold text-center">E.1</td>
                                    <td className="border border-black p-1">สายเมนไฟฟ้าแรงต่ำ + ท่อ EMT</td>
                                    <td className="border border-black p-1 text-center">1 ชุด</td>
                                    <td className="border border-black p-1 text-right">{e1_material.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right">{e1_labor.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right font-bold">{e1_total.toLocaleString()}</td>
                                </tr>
                                <tr>
                                    <td className="border border-black p-1 font-bold text-center">E.2</td>
                                    <td className="border border-black p-1">ตู้ไฟฟ้า LC-{lcSlots} + เบรกเกอร์</td>
                                    <td className="border border-black p-1 text-center">1 ชุด</td>
                                    <td className="border border-black p-1 text-right">{e2_material.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right">{e2_labor.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right font-bold">{e2_total.toLocaleString()}</td>
                                </tr>
                                {/* E.2 Details */}
                                <tr className="text-[10px] bg-gray-50">
                                    <td className="border border-black p-1"></td>
                                    <td className="border border-black p-1 pl-4">- Load Center {lcSlots} ช่อง</td>
                                    <td className="border border-black p-1 text-center">1</td>
                                    <td className="border border-black p-1 text-right">{lcPrice.toLocaleString()}</td>
                                    <td className="border border-black p-1"></td>
                                    <td className="border border-black p-1"></td>
                                </tr>
                                <tr className="text-[10px] bg-gray-50">
                                    <td className="border border-black p-1"></td>
                                    <td className="border border-black p-1 pl-4">- Main CB 2P {data.data?.main_breaker || 100}AT</td>
                                    <td className="border border-black p-1 text-center">1</td>
                                    <td className="border border-black p-1 text-right">{mainBreakerPrice.toLocaleString()}</td>
                                    <td className="border border-black p-1"></td>
                                    <td className="border border-black p-1"></td>
                                </tr>
                                {mcbCount > 0 && (
                                    <tr className="text-[10px] bg-gray-50">
                                        <td className="border border-black p-1"></td>
                                        <td className="border border-black p-1 pl-4">- MCB 1P (Branch)</td>
                                        <td className="border border-black p-1 text-center">{mcbCount}</td>
                                        <td className="border border-black p-1 text-right">{mcbTotal.toLocaleString()}</td>
                                        <td className="border border-black p-1"></td>
                                        <td className="border border-black p-1"></td>
                                    </tr>
                                )}
                                {rcboCount > 0 && (
                                    <tr className="text-[10px] bg-gray-50">
                                        <td className="border border-black p-1"></td>
                                        <td className="border border-black p-1 pl-4">- RCBO 1P 30mA (น้ำอุ่น/เปียก)</td>
                                        <td className="border border-black p-1 text-center">{rcboCount}</td>
                                        <td className="border border-black p-1 text-right">{rcboTotal.toLocaleString()}</td>
                                        <td className="border border-black p-1"></td>
                                        <td className="border border-black p-1"></td>
                                    </tr>
                                )}
                                <tr>
                                    <td className="border border-black p-1 font-bold text-center">E.3</td>
                                    <td className="border border-black p-1">สายไฟฟ้า + ท่อ PVC ({wireLength} ม.)</td>
                                    <td className="border border-black p-1 text-center">1 ชุด</td>
                                    <td className="border border-black p-1 text-right">{e3_material.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right">{e3_labor.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right font-bold">{e3_total.toLocaleString()}</td>
                                </tr>
                            </tbody>
                            <tfoot>
                                <tr className="bg-gray-200">
                                    <td colSpan={3} className="border border-black p-1 font-bold text-right">รวมค่าดำเนินการ</td>
                                    <td className="border border-black p-1 text-right font-bold">{totalMaterial.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right font-bold">{totalLabor.toLocaleString()}</td>
                                    <td className="border border-black p-1 text-right font-bold">{grandTotal.toLocaleString()}</td>
                                </tr>
                                <tr>
                                    <td colSpan={5} className="border border-black p-1 font-bold text-right">VAT 7%</td>
                                    <td className="border border-black p-1 text-right">{vat.toLocaleString()}</td>
                                </tr>
                                <tr className="bg-gray-300">
                                    <td colSpan={5} className="border border-black p-1 font-bold text-right text-lg">รวมทั้งสิ้น</td>
                                    <td className="border border-black p-1 text-right font-bold text-lg">{finalTotal.toLocaleString()} ฿</td>
                                </tr>
                            </tfoot>
                        </table>

                        {/* Notes */}
                        <div className="text-xs border border-black p-2">
                            <div className="font-bold mb-1">หมายเหตุ:</div>
                            <ul className="list-disc pl-4 space-y-0.5">
                                <li>ราคาประมาณการใช้ยี่ห้อราคาถูก (Yazaki, Schneider, PRI)</li>
                                <li>ไม่รวมค่าขนส่งและค่าใช้จ่ายอื่นๆ</li>
                                <li>ค่าแรง 35% ของค่าวัสดุ (สายเมน/สายย่อย) หรือ 4,000 บาท (ตู้ไฟ)</li>
                            </ul>
                        </div>

                        {/* Footer */}
                        <div className="text-center text-xs mt-4 pt-2 border-t border-black">
                            GENERATED BY ACA MOZART AI | {new Date().toLocaleDateString('th-TH')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BOQPDFPreviewModal;
