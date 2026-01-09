/**
 * BOQTab Component - Bill of Quantities
 * Uses boq_data from backend (with fallback to local calculation)
 */
import React from 'react';
import { Receipt, Download } from 'lucide-react';
import type { BOQData, LoadResult } from '../types';

interface BOQTabProps {
    boqData?: BOQData;
    loads?: LoadResult[];
    onDownloadClick: () => void;
}

export const BOQTab: React.FC<BOQTabProps> = ({ boqData, loads = [], onDownloadClick }) => {
    // 🆕 Check if we have backend data
    if (boqData && boqData.sections && boqData.sections.length > 0) {
        const priceSource = boqData.price_source || 'unknown';
        const isFallback = priceSource === 'catalog_fallback';

        return (
            <div className="space-y-6">
                {/* BOQ Header */}
                <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-lg p-6 flex justify-between items-start">
                    <div>
                        <h3 className="text-amber-400 font-bold text-lg mb-2 flex items-center gap-2">
                            <Receipt size={24} /> Bill of Quantities (BOQ)
                        </h3>
                        <p className="text-slate-400 text-sm">
                            จาก Backend: <span className="text-sky-400 font-bold">{boqData.sections.length}</span> หมวด
                        </p>
                        <p className={`text-xs mt-1 ${isFallback ? 'text-yellow-400' : 'text-emerald-400'}`}>
                            {isFallback ? '⚠️ ราคา Fallback (Hardcoded)' : '✅ ราคาจาก prices.csv'}
                        </p>
                    </div>
                    <button
                        onClick={onDownloadClick}
                        className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 shadow-lg transition-all cursor-pointer"
                    >
                        <Download size={16} /> Download Options
                    </button>
                </div>

                {/* Price Warning */}
                {boqData.price_valid_warning && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-yellow-300 text-sm">
                        {boqData.price_valid_warning}
                    </div>
                )}

                {/* Detailed BOQ Sections */}
                {boqData.sections.map((section) => (
                    <div key={section.section_id} className="border border-slate-800 rounded-lg overflow-hidden">
                        <div className="bg-slate-900 p-3 border-b border-slate-800">
                            <span className="text-amber-400 font-bold">{section.section_id}</span>
                            <span className="text-slate-400 ml-2">{section.section_name}</span>
                        </div>
                        <table className="w-full text-sm">
                            <thead className="bg-slate-900/50">
                                <tr>
                                    <th className="p-2 text-left text-slate-500 w-12">ลำดับ</th>
                                    <th className="p-2 text-left text-slate-500">รายการ</th>
                                    <th className="p-2 text-right text-slate-500 w-20">จำนวน</th>
                                    <th className="p-2 text-right text-slate-500 w-24">ค่าวัสดุ</th>
                                    <th className="p-2 text-right text-slate-500 w-24">ค่าแรง</th>
                                    <th className="p-2 text-right text-slate-500 w-28">รวม</th>
                                </tr>
                            </thead>
                            <tbody>
                                {section.items.map((item) => (
                                    <tr key={item.item_no} className="hover:bg-slate-900/50 border-b border-slate-800/50">
                                        <td className="p-2 text-slate-500">{item.item_no}</td>
                                        <td className="p-2 text-slate-300">
                                            {item.description}
                                            {item.remark && <span className="text-slate-500 ml-2">({item.remark})</span>}
                                        </td>
                                        <td className="p-2 text-right font-mono text-slate-400">{item.quantity} {item.unit}</td>
                                        <td className="p-2 text-right font-mono text-slate-400">{item.material_total.toLocaleString()} ฿</td>
                                        <td className="p-2 text-right font-mono text-slate-400">{item.labor_total.toLocaleString()} ฿</td>
                                        <td className="p-2 text-right font-mono text-emerald-400 font-bold">{item.total_price.toLocaleString()} ฿</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-slate-800/50">
                                <tr>
                                    <td colSpan={5} className="p-2 text-right text-slate-400 font-bold">รวม {section.section_id}</td>
                                    <td className="p-2 text-right font-mono text-sky-400 font-bold">{section.section_total.toLocaleString()} ฿</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                ))}

                {/* Grand Total */}
                <div className="border border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                        <tfoot className="bg-slate-800 font-mono">
                            <tr className="border-b border-slate-700">
                                <td className="p-3 text-right font-bold text-slate-400">รวมค่าวัสดุ</td>
                                <td className="p-3 text-right text-slate-400 w-32">{boqData.subtotal_material.toLocaleString()} ฿</td>
                            </tr>
                            <tr className="border-b border-slate-700">
                                <td className="p-3 text-right font-bold text-slate-400">รวมค่าแรง</td>
                                <td className="p-3 text-right text-slate-400">{boqData.subtotal_labor.toLocaleString()} ฿</td>
                            </tr>
                            <tr className="border-b border-slate-700">
                                <td className="p-3 text-right font-bold text-sky-400">รวมก่อน VAT</td>
                                <td className="p-3 text-right text-sky-400 font-bold">{boqData.grand_total.toLocaleString()} ฿</td>
                            </tr>
                            <tr className="border-b border-slate-700">
                                <td className="p-3 text-right font-bold text-slate-400">VAT {boqData.vat_percent}%</td>
                                <td className="p-3 text-right text-slate-400">{boqData.vat_amount.toLocaleString()} ฿</td>
                            </tr>
                            <tr>
                                <td className="p-3 text-right font-bold text-amber-400 text-lg">รวมทั้งสิ้น</td>
                                <td className="p-3 text-right text-emerald-400 font-bold text-xl">{boqData.final_total.toLocaleString()} ฿</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                {/* Notice */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
                    <p className="text-slate-500 text-xs text-center">
                        💡 Price Source: {priceSource} | Valid until: {boqData.price_valid_date || 'N/A'}
                    </p>
                </div>
            </div>
        );
    }

    // ⚠️ FALLBACK: Local calculation (no backend data)
    const circuitCount = loads.length || 1;
    const PRICES = {
        MCB_1P: 78, RCBO_1P: 1133, LC_30: 6108, LC_18: 3600,
        WIRE_2_5: 10, WIRE_4: 18, PVC_HALF: 10, MAIN_WIRE_M: 237,
        MAIN_CONDUIT_M: 121, LABOR_PERCENT: 0.35,
    };

    let mcbCount = 0, rcboCount = 0;
    loads.forEach((item) => {
        const loadItem = item as LoadResult & { requires_rcbo?: boolean; breaker_type?: string };
        if (loadItem.requires_rcbo || loadItem.breaker_type === 'RCBO') rcboCount++;
        else mcbCount++;
    });

    const e1_material = (50 * PRICES.MAIN_WIRE_M) + (15 * 62) + (18 * PRICES.MAIN_CONDUIT_M) + 1000;
    const e1_labor = Math.round(e1_material * PRICES.LABOR_PERCENT);
    const e1_total = e1_material + e1_labor;

    const lcPrice = circuitCount > 18 ? PRICES.LC_30 : PRICES.LC_18;
    const mainBreakerPrice = 2884;
    const e2_material = lcPrice + mainBreakerPrice + mcbCount * PRICES.MCB_1P + rcboCount * PRICES.RCBO_1P + 1000;
    const e2_labor = 4000;
    const e2_total = e2_material + e2_labor;

    const wireLength = circuitCount * 15;
    const e3_material = (wireLength * PRICES.WIRE_2_5 * 3) + (wireLength * PRICES.PVC_HALF) + 5000;
    const e3_labor = Math.round(e3_material * PRICES.LABOR_PERCENT);
    const e3_total = e3_material + e3_labor;

    const totalMaterial = e1_material + e2_material + e3_material;
    const totalLabor = e1_labor + e2_labor + e3_labor;
    const grandTotal = totalMaterial + totalLabor;
    const vat = Math.round(grandTotal * 0.07);
    const finalTotal = grandTotal + vat;

    return (
        <div className="space-y-6">
            {/* BOQ Header - Fallback Mode */}
            <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-lg p-6 flex justify-between items-start">
                <div>
                    <h3 className="text-amber-400 font-bold text-lg mb-2 flex items-center gap-2">
                        <Receipt size={24} /> Bill of Quantities (BOQ)
                    </h3>
                    <p className="text-slate-400 text-sm">
                        คำนวณจาก Load Schedule: <span className="text-sky-400 font-bold">{circuitCount}</span> วงจร
                        ({mcbCount} MCB + {rcboCount} RCBO)
                    </p>
                    <p className="text-yellow-400 text-xs mt-1">⚠️ ราคา Local Fallback (ไม่มี backend data)</p>
                </div>
                <button
                    onClick={onDownloadClick}
                    className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 shadow-lg transition-all cursor-pointer"
                >
                    <Download size={16} /> Download Options
                </button>
            </div>

            {/* Summary Table */}
            <div className="border border-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-slate-900">
                        <tr>
                            <th className="p-3 text-left text-slate-500 w-16">หมวด</th>
                            <th className="p-3 text-left text-slate-500">รายการ</th>
                            <th className="p-3 text-right text-slate-500">ค่าวัสดุ</th>
                            <th className="p-3 text-right text-slate-500">ค่าแรง</th>
                            <th className="p-3 text-right text-slate-500">รวม</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr className="hover:bg-slate-900/50">
                            <td className="p-3 font-bold text-amber-400">E.1</td>
                            <td className="p-3 text-slate-300">สายเมนไฟฟ้าแรงต่ำ + ท่อ EMT</td>
                            <td className="p-3 text-right font-mono text-slate-400">{e1_material.toLocaleString()} ฿</td>
                            <td className="p-3 text-right font-mono text-slate-400">{e1_labor.toLocaleString()} ฿</td>
                            <td className="p-3 text-right font-mono text-emerald-400 font-bold">{e1_total.toLocaleString()} ฿</td>
                        </tr>
                        <tr className="hover:bg-slate-900/50">
                            <td className="p-3 font-bold text-amber-400">E.2</td>
                            <td className="p-3 text-slate-300">ตู้ไฟฟ้า (LC + {mcbCount} MCB + {rcboCount} RCBO)</td>
                            <td className="p-3 text-right font-mono text-slate-400">{e2_material.toLocaleString()} ฿</td>
                            <td className="p-3 text-right font-mono text-slate-400">{e2_labor.toLocaleString()} ฿</td>
                            <td className="p-3 text-right font-mono text-emerald-400 font-bold">{e2_total.toLocaleString()} ฿</td>
                        </tr>
                        <tr className="hover:bg-slate-900/50">
                            <td className="p-3 font-bold text-amber-400">E.3</td>
                            <td className="p-3 text-slate-300">สายไฟฟ้า + ท่อ PVC ({wireLength} ม.)</td>
                            <td className="p-3 text-right font-mono text-slate-400">{e3_material.toLocaleString()} ฿</td>
                            <td className="p-3 text-right font-mono text-slate-400">{e3_labor.toLocaleString()} ฿</td>
                            <td className="p-3 text-right font-mono text-emerald-400 font-bold">{e3_total.toLocaleString()} ฿</td>
                        </tr>
                    </tbody>
                    <tfoot className="bg-slate-800 font-mono">
                        <tr className="border-t-2 border-slate-600">
                            <td colSpan={2} className="p-3 text-right font-bold text-slate-400">รวมค่าดำเนินการ</td>
                            <td className="p-3 text-right text-slate-400">{totalMaterial.toLocaleString()} ฿</td>
                            <td className="p-3 text-right text-slate-400">{totalLabor.toLocaleString()} ฿</td>
                            <td className="p-3 text-right text-sky-400 font-bold text-lg">{grandTotal.toLocaleString()} ฿</td>
                        </tr>
                        <tr>
                            <td colSpan={4} className="p-3 text-right font-bold text-slate-400">VAT 7%</td>
                            <td className="p-3 text-right text-slate-400">{vat.toLocaleString()} ฿</td>
                        </tr>
                        <tr className="border-t border-slate-700">
                            <td colSpan={4} className="p-3 text-right font-bold text-amber-400 text-lg">รวมทั้งสิ้น</td>
                            <td className="p-3 text-right text-emerald-400 font-bold text-xl">{finalTotal.toLocaleString()} ฿</td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            {/* Notice */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
                <p className="text-slate-500 text-xs text-center">
                    💡 ราคาประมาณการใช้ยี่ห้อถูกสุด (Yazaki, Schneider, PRI) | ไม่รวมค่าขนส่ง
                </p>
            </div>
        </div>
    );
};

export default BOQTab;
