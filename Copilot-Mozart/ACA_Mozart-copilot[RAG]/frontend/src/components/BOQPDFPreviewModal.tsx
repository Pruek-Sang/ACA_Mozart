/**
 * BOQ PDF Preview Modal
 * 
 * 🆕 REFACTORED: Now displays detailed items from boqData.sections
 *    matching BOQTab web display (Brand, Spec, Price per item)
 */
import React, { useRef, useState } from 'react';
import { X, Download, Printer, Loader2, FileSpreadsheet } from 'lucide-react';
import type { DesignResult, BOQData } from '../types';
import html2pdf from 'html2pdf.js';
import * as XLSX from 'xlsx';

interface BOQPDFPreviewModalProps {
    data: DesignResult;
    boqData?: BOQData | null;
    isOpen: boolean;
    onClose: () => void;
}

export const BOQPDFPreviewModal: React.FC<BOQPDFPreviewModalProps> = ({
    data,
    boqData,
    isOpen,
    onClose
}) => {
    const contentRef = useRef<HTMLDivElement>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    if (!isOpen) return null;

    // Check if we have backend data
    const useBackendData = boqData && boqData.sections && boqData.sections.length > 0;
    const priceSource = boqData?.price_source || 'local_fallback';
    const priceWarning = boqData?.price_valid_warning || 'ราคาประมาณการ';

    console.log('[BOQ-PDF] useBackendData:', useBackendData);
    console.log('[BOQ-PDF] sections count:', boqData?.sections?.length || 0);

    // === PDF DOWNLOAD ===
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

    // === EXCEL DOWNLOAD (REFACTORED) ===
    const handleDownloadExcel = () => {
        const excelData: (string | number)[][] = [
            ['BILL OF QUANTITIES (BOQ)'],
            ['โปรเจกต์:', data.data?.project_name || 'บ้านพักอาศัย'],
            ['วันที่:', new Date().toLocaleDateString('th-TH')],
            ['แหล่งราคา:', priceSource === 'prices.csv' ? 'ฐานข้อมูลราคา' : 'Catalog Fallback'],
            [],
        ];

        if (useBackendData && boqData) {
            // Use backend data
            excelData.push(['ลำดับ', 'รายการ', 'จำนวน', 'หน่วย', 'ค่าวัสดุ', 'ค่าแรง', 'รวม']);

            boqData.sections.forEach(section => {
                // Section header
                excelData.push([section.section_id, section.section_name, '', '', '', '', '']);

                // Items
                section.items.forEach(item => {
                    excelData.push([
                        item.item_no,
                        item.description + (item.remark ? ` (${item.remark})` : ''),
                        item.quantity,
                        item.unit,
                        item.material_total,
                        item.labor_total,
                        item.total_price
                    ]);
                });

                // Section total
                excelData.push(['', `รวม ${section.section_id}`, '', '', '', '', section.section_total]);
                excelData.push([]); // Empty row
            });

            // Grand totals
            excelData.push([]);
            excelData.push(['', '', '', '', 'รวมค่าวัสดุ', '', boqData.subtotal_material]);
            excelData.push(['', '', '', '', 'รวมค่าแรง', '', boqData.subtotal_labor]);
            excelData.push(['', '', '', '', 'รวมก่อน VAT', '', boqData.grand_total]);
            excelData.push(['', '', '', '', `VAT ${boqData.vat_percent}%`, '', boqData.vat_amount]);
            excelData.push(['', '', '', '', 'รวมทั้งสิ้น', '', boqData.final_total]);
        } else {
            // Fallback message
            excelData.push(['⚠️ ไม่มีข้อมูล BOQ จาก Backend - กรุณาคำนวณใหม่']);
        }

        const ws = XLSX.utils.aoa_to_sheet(excelData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'BOQ');

        ws['!cols'] = [
            { wch: 10 }, { wch: 45 }, { wch: 10 }, { wch: 8 },
            { wch: 14 }, { wch: 14 }, { wch: 14 }
        ];

        XLSX.writeFile(wb, `BOQ_${new Date().toISOString().split('T')[0]}.xlsx`);
        console.log('[BOQ-EXCEL] Downloaded successfully');
    };

    // === RENDER BACKEND DATA TABLE ===
    const renderBackendDataTable = () => {
        if (!boqData || !boqData.sections) return null;

        return (
            <>
                {boqData.sections.map((section, sectionIndex) => (
                    <React.Fragment key={section.section_id}>
                        {/* Section Header Row */}
                        <tr className="bg-gray-200">
                            <td className="border border-black p-1 font-bold text-center">
                                {section.section_id}
                            </td>
                            <td colSpan={5} className="border border-black p-1 font-bold">
                                {section.section_name}
                            </td>
                        </tr>

                        {/* Item Rows */}
                        {section.items.map((item, itemIndex) => (
                            <tr key={`${section.section_id}-${item.item_no}`} className={itemIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                <td className="border border-black p-1 text-center text-[10px]">
                                    {item.item_no}
                                </td>
                                <td className="border border-black p-1 text-[10px]">
                                    {item.description}
                                    {item.remark && <span className="text-gray-500 ml-1">({item.remark})</span>}
                                </td>
                                <td className="border border-black p-1 text-center text-[10px]">
                                    {item.quantity} {item.unit}
                                </td>
                                <td className="border border-black p-1 text-right text-[10px]">
                                    {item.material_total.toLocaleString()}
                                </td>
                                <td className="border border-black p-1 text-right text-[10px]">
                                    {item.labor_total.toLocaleString()}
                                </td>
                                <td className="border border-black p-1 text-right font-bold text-[10px]">
                                    {item.total_price.toLocaleString()}
                                </td>
                            </tr>
                        ))}

                        {/* Section Total Row */}
                        <tr className="bg-gray-100">
                            <td colSpan={5} className="border border-black p-1 text-right font-bold text-[10px]">
                                รวม {section.section_id}
                            </td>
                            <td className="border border-black p-1 text-right font-bold text-[10px]">
                                {section.section_total.toLocaleString()}
                            </td>
                        </tr>

                        {/* Spacer row between sections (except last) */}
                        {sectionIndex < boqData.sections.length - 1 && (
                            <tr><td colSpan={6} className="border-0 h-1"></td></tr>
                        )}
                    </React.Fragment>
                ))}
            </>
        );
    };

    // === RENDER FALLBACK TABLE (no backend data) ===
    const renderFallbackTable = () => (
        <tr>
            <td colSpan={6} className="border border-black p-4 text-center text-red-600">
                ⚠️ ไม่มีข้อมูล BOQ จาก Backend<br />
                กรุณาคำนวณใหม่เพื่อรับข้อมูลราคา
            </td>
        </tr>
    );

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 w-full max-w-4xl h-[90vh] rounded-xl border border-slate-700 flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <Printer size={20} className="text-amber-400" />
                        BOQ Preview (Bill of Quantities)
                        {useBackendData && (
                            <span className="text-xs px-2 py-0.5 bg-green-900/50 text-green-400 rounded">
                                ✅ Backend Data
                            </span>
                        )}
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
                        <div className="text-center font-bold mb-4 uppercase text-lg border-b-2 border-black pb-2">
                            BILL OF QUANTITIES (BOQ)
                        </div>

                        {/* Project Info */}
                        <div className="border border-black mb-4 text-sm">
                            <div className="grid grid-cols-2 gap-1 p-2">
                                <div><strong>PROJECT:</strong> {data.data?.project_name || 'บ้านพักอาศัย'}</div>
                                <div><strong>DATE:</strong> {new Date().toLocaleDateString('th-TH')}</div>
                                <div>
                                    <strong>PRICE SOURCE:</strong>{' '}
                                    {priceSource === 'prices.csv' ? '✅ ฐานข้อมูลราคา' : '⚠️ Catalog Fallback'}
                                </div>
                                <div><strong>VALID:</strong> {priceWarning}</div>
                            </div>
                        </div>

                        {/* BOQ Table */}
                        <table className="w-full text-xs border-collapse border border-black mb-4">
                            <thead>
                                <tr className="bg-gray-300 font-bold text-center">
                                    <th className="border border-black p-1 w-12">ลำดับ</th>
                                    <th className="border border-black p-1">รายการ</th>
                                    <th className="border border-black p-1 w-16">จำนวน</th>
                                    <th className="border border-black p-1 w-20">ค่าวัสดุ</th>
                                    <th className="border border-black p-1 w-20">ค่าแรง</th>
                                    <th className="border border-black p-1 w-20">รวม</th>
                                </tr>
                            </thead>
                            <tbody>
                                {useBackendData ? renderBackendDataTable() : renderFallbackTable()}
                            </tbody>

                            {/* Grand Total Footer */}
                            {useBackendData && boqData && (
                                <tfoot>
                                    <tr className="bg-gray-200">
                                        <td colSpan={3} className="border border-black p-1 font-bold text-right">
                                            รวมค่าดำเนินการ
                                        </td>
                                        <td className="border border-black p-1 text-right font-bold">
                                            {boqData.subtotal_material.toLocaleString()}
                                        </td>
                                        <td className="border border-black p-1 text-right font-bold">
                                            {boqData.subtotal_labor.toLocaleString()}
                                        </td>
                                        <td className="border border-black p-1 text-right font-bold">
                                            {boqData.grand_total.toLocaleString()}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colSpan={5} className="border border-black p-1 font-bold text-right">
                                            VAT {boqData.vat_percent}%
                                        </td>
                                        <td className="border border-black p-1 text-right">
                                            {boqData.vat_amount.toLocaleString()}
                                        </td>
                                    </tr>
                                    <tr className="bg-gray-300">
                                        <td colSpan={5} className="border border-black p-1 font-bold text-right text-base">
                                            รวมทั้งสิ้น
                                        </td>
                                        <td className="border border-black p-1 text-right font-bold text-base">
                                            {boqData.final_total.toLocaleString()} ฿
                                        </td>
                                    </tr>
                                </tfoot>
                            )}
                        </table>

                        {/* Notes */}
                        <div className="text-xs border border-black p-2">
                            <div className="font-bold mb-1">หมายเหตุ:</div>
                            <ul className="list-disc pl-4 space-y-0.5">
                                <li>ราคาจาก: {priceSource === 'prices.csv' ? 'ฐานข้อมูลราคาอัพเดท' : 'Catalog เริ่มต้น'}</li>
                                <li>ไม่รวมค่าขนส่งและค่าใช้จ่ายอื่นๆ</li>
                                <li>{priceWarning}</li>
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
