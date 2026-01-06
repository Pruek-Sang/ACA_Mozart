import React, { useRef, useState } from 'react';
import { X, Download, Printer, Loader2 } from 'lucide-react';
import type { DesignResult } from '../types';
import html2pdf from 'html2pdf.js';

interface PDFPreviewModalProps {
    data: DesignResult;
    isOpen: boolean;
    onClose: () => void;
}

export const PDFPreviewModal: React.FC<PDFPreviewModalProps> = ({ data, isOpen, onClose }) => {
    const contentRef = useRef<HTMLDivElement>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    if (!isOpen) return null;

    const handleDownload = async () => {
        if (!contentRef.current) return;
        setIsGenerating(true);

        const element = contentRef.current;
        const opt = {
            margin: 5,
            filename: `Panel-Schedule-${data.data?.project_name || 'Project'}.pdf`,
            image: { type: 'jpeg' as const, quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'landscape' as const } // Landscape for wide table
        };

        try {
            await html2pdf().set(opt).from(element).save();
        } catch (error) {
            console.error("PDF Generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const allCircuits = (data.metadata?.display_data?.circuits as any[]) || data.data?.grouped_circuits || data.data?.loads || [];
    const loads = allCircuits; // Use circuits as the primary list
    const mainBreaker = data.data?.main_breaker || 50;
    const mainCbType = data.data?.main_cb_type || "MCB";
    const mainWire = data.data?.main_feeder_size || "16";
    const mainWireType = data.data?.main_feeder_type || "IEC01";
    const mainConduit = data.data?.main_raceway_size || "1\"";
    const mainConduitType = data.data?.main_raceway_type || "EMT";

    // 🔧 DEBUG: Log what data PDF is receiving
    console.log('[PDF-DEBUG] circuits count:', loads.length);
    if (loads.length > 0) console.log('[PDF-DEBUG] sample circuit:', loads[0]);

    // Categorize Loads for Footer - use total_watts or connected_load from circuit data
    const getLoadVA = (l: any) => {
        // Try circuit computed fields first (single source of truth)
        if (l.load_va_l1 !== undefined) return l.load_va_l1;
        if (l.total_watts !== undefined) return l.total_watts;

        // Fallback to legacy fields
        return l.total_va || Math.round((l.power_kw || 0) * 1000) || 0;
    };

    const lightingLoad = loads.filter((l: any) => l.device_name?.toLowerCase().includes('light') || l.device_name?.includes('แสงสว่าง')).reduce((sum: number, l: any) => sum + getLoadVA(l), 0);
    const receptacleLoad = loads.filter((l: any) => l.device_name?.toLowerCase().includes('socket') || l.device_name?.includes('เต้ารับ')).reduce((sum: number, l: any) => sum + getLoadVA(l), 0);
    const heaterLoad = loads.filter((l: any) => l.device_name?.toLowerCase().includes('water') || l.device_name?.includes('น้ำอุ่น')).reduce((sum: number, l: any) => sum + getLoadVA(l), 0);
    const acLoad = loads.filter((l: any) => l.device_name?.toLowerCase().includes('air') || l.device_name?.includes('แอร์')).reduce((sum: number, l: any) => sum + getLoadVA(l), 0);
    const spareLoad = loads.filter((l: any) => l.device_name?.toLowerCase().includes('spare')).reduce((sum: number, l: any) => sum + getLoadVA(l), 0);

    const totalConnectedLoad = loads.reduce((sum: number, l: any) => sum + getLoadVA(l), 0);
    const demandFactor = data.data?.demand_factor || 0.8;
    const demandLoad = totalConnectedLoad * demandFactor;

    console.log('[PDF-DEBUG] category totals:', { lightingLoad, receptacleLoad, heaterLoad, acLoad, totalConnectedLoad });


    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 w-full max-w-6xl h-[90vh] rounded-xl border border-slate-700 flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <Printer size={20} className="text-sky-400" />
                        Print Preview (Panel Schedule)
                    </h3>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleDownload}
                            disabled={isGenerating}
                            className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 cursor-pointer"
                        >
                            {isGenerating ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                            Download PDF
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors cursor-pointer"
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Preview Area (Scrollable) */}
                <div className="flex-1 overflow-y-auto p-8 bg-slate-800 flex justify-center">
                    {/* A4 Landscape Container */}
                    <div
                        ref={contentRef}
                        className="bg-white text-black w-[297mm] min-h-[210mm] h-fit p-[10mm] shadow-lg relative"
                        style={{ fontFamily: 'Sarabun, sans-serif' }}
                    >
                        {/* Title */}
                        <div className="text-center font-bold mb-4 uppercase text-lg underline">
                            240 VAC. PANEL BOARD SCHEDULE FOR
                        </div>

                        {/* Panel Info Box */}
                        <div className="border-2 border-black mb-1 text-xs font-bold uppercase">
                            <div className="grid grid-cols-[150px_1fr_150px_1fr_150px_1fr] gap-x-2 p-1 border-b border-black">
                                <div>PANEL NO.</div>
                                <div>: LP-1</div>
                                <div>CAPACITY</div>
                                <div>: {loads.length} CKT.</div>
                                <div>PROJECT</div>
                                <div className="truncate">: {data.data?.project_name || 'RESIDENTIAL'}</div>
                            </div>
                            <div className="grid grid-cols-[150px_1fr_150px_1fr_150px_1fr] gap-x-2 p-1 border-b border-black">
                                <div>UP STREAM PANEL</div>
                                <div>: MDB</div>
                                <div>MAIN BUSBAR</div>
                                <div>: 100 A</div>
                                <div>LOCATION</div>
                                <div>: INDOOR</div>
                            </div>
                            <div className="grid grid-cols-[150px_1fr_150px_1fr_150px_1fr] gap-x-2 p-1">
                                <div>MAIN CIRCUIT BREAKER</div>
                                <div>: {mainCbType} 2P {mainBreaker} AT</div>
                                <div>IC {'>='}</div>
                                <div>: 10 kA At 240 VAC</div>
                                <div>MOUNTING</div>
                                <div>: WALL MOUNTED</div>
                            </div>
                        </div>

                        {/* Main Table */}
                        <div className="border-2 border-black border-t-0">
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    {/* Header Row 1 */}
                                    <tr className="border-b border-black text-center font-bold">
                                        <td className="border-r border-black w-8" rowSpan={2}>CKT.<br />NO.</td>
                                        <td className="border-r border-black" rowSpan={2}>DESCRIPTION</td>

                                        {/* CB Group */}
                                        <td className="border-r border-black w-[25%]" colSpan={4}>CB</td>

                                        {/* Wire Group */}
                                        <td className="border-r border-black w-[15%]" colSpan={2}>WIRE</td>

                                        {/* Conduit Group */}
                                        <td className="border-r border-black w-[15%]" colSpan={2}>CONDUIT</td>

                                        <td className="w-24" rowSpan={2}>CONNECTED<br />LOAD IN VA.</td>
                                    </tr>
                                    {/* Header Row 2 */}
                                    <tr className="border-b-2 border-black text-center font-bold h-8">
                                        <td className="border-r border-black w-10">NO POLE</td>
                                        <td className="border-r border-black w-8">AT</td>
                                        <td className="border-r border-black w-10">TYPE</td>
                                        <td className="border-r border-black w-8">IC {'>='}</td>

                                        <td className="border-r border-black w-16">SIZE</td>
                                        <td className="border-r border-black w-10">TYPE</td>

                                        <td className="border-r border-black w-10">SIZE</td>
                                        <td className="border-r border-black w-10">TYPE</td>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loads.map((load: any, i: number) => {
                                        // Wire format: "2x2.5/2.5G"
                                        const wireSize = load.wire_size || load.wire_size_l || '2.5';
                                        const wireL = wireSize.replace(' mm²', '');
                                        const wireG = load.ground_size || load.wire_size_grd || '2.5';
                                        const wireStr = `2x${wireL}/${wireG}G`;

                                        // Breaker Info
                                        const poles = load.breaker_poles || 1;
                                        const at = load.breaker_rating || load.breaker_at || load.breaker_size;
                                        const type = load.breaker_type || 'MCB';
                                        const ic = load.ic_ka || load.breaker_ic_ka || 6;
                                        const name = load.circuit_name || load.device_name || load.name || 'Unknown';

                                        return (
                                            <tr key={i} className="border-b border-black h-7 text-center hover:bg-gray-50">
                                                <td className="border-r border-black font-bold">{i + 1}</td>
                                                <td className="border-r border-black text-left px-2 font-medium truncate max-w-[200px]">{name}</td>

                                                {/* CB */}
                                                <td className="border-r border-black">{poles}</td>
                                                <td className="border-r border-black font-bold">{at}</td>
                                                <td className="border-r border-black text-[10px]">{type}</td>
                                                <td className="border-r border-black">{ic}</td>

                                                {/* Wire */}
                                                <td className="border-r border-black">{wireStr}</td>
                                                <td className="border-r border-black">{load.wire_type || 'IEC01'}</td>

                                                {/* Conduit */}
                                                <td className="border-r border-black">{load.conduit_size || load.trade_size || '1/2"'}</td>
                                                <td className="border-r border-black">{load.conduit_type || 'EMT'}</td>

                                                {/* Load */}
                                                <td className="font-bold text-right px-2">{getLoadVA(load).toLocaleString()}</td>
                                            </tr>
                                        );
                                    })}

                                    {/* Fill Empty Rows to keep form height consistent (Optional - skipped for now) */}
                                </tbody>
                            </table>
                        </div>

                        {/* Footer Section */}
                        <div className="border-2 border-black border-t-0 flex text-xs font-bold uppercase">
                            {/* Feeder Info */}
                            <div className="w-[45%] border-r-2 border-black p-2 flex flex-col justify-center space-y-2">
                                <div className="flex">
                                    <span className="w-28">FEEDER CABLE :</span>
                                    <span>{mainWire} Sq.mm ({mainWireType})</span>
                                </div>
                                <div className="flex ml-28">
                                    <span>in {mainConduitType} Dia {mainConduit}</span>
                                </div>
                            </div>

                            {/* Load Breakdown */}
                            <div className="w-[30%] border-r-2 border-black text-xs">
                                <div className="grid grid-cols-[1fr_20px_60px_30px] border-b border-black py-1 px-2">
                                    <span>LIGHTING</span><span>=</span><span className="text-right">{lightingLoad}</span><span className="pl-1">VA</span>
                                </div>
                                <div className="grid grid-cols-[1fr_20px_60px_30px] border-b border-black py-1 px-2">
                                    <span>RECEPTACLE</span><span>=</span><span className="text-right">{receptacleLoad}</span><span className="pl-1">VA</span>
                                </div>
                                <div className="grid grid-cols-[1fr_20px_60px_30px] border-b border-black py-1 px-2">
                                    <span>WATER HEATER</span><span>=</span><span className="text-right">{heaterLoad}</span><span className="pl-1">VA</span>
                                </div>
                                <div className="grid grid-cols-[1fr_20px_60px_30px] border-b border-black py-1 px-2">
                                    <span>A/C</span><span>=</span><span className="text-right">{acLoad}</span><span className="pl-1">VA</span>
                                </div>
                                <div className="grid grid-cols-[1fr_20px_60px_30px] py-1 px-2">
                                    <span>SPARE</span><span>=</span><span className="text-right">{spareLoad}</span><span className="pl-1">VA</span>
                                </div>
                            </div>

                            {/* Totals */}
                            <div className="w-[25%] flex flex-col">
                                <div className="flex-1"></div>
                                <div className="border-t-2 border-black grid grid-cols-[1fr_60px_30px] py-2 px-2 items-center bg-gray-100">
                                    <span>CONNECTED LOAD :</span>
                                    <span className="text-right font-extrabold text-sm">{totalConnectedLoad.toLocaleString()}</span>
                                    <span className="pl-1">VA</span>
                                </div>
                                <div className="border-t-2 border-black grid grid-cols-[1fr_60px_30px] py-2 px-2 items-center bg-gray-100">
                                    <span>DEMAND LOAD (80 %) :</span>
                                    <span className="text-right font-extrabold text-sm">{demandLoad.toLocaleString()}</span>
                                    <span className="pl-1">VA</span>
                                </div>
                            </div>
                        </div>

                        {/* Note */}
                        <div className="border-2 border-black border-t-0 p-2 text-xs font-bold uppercase flex justify-between">
                            <div>NOTE : ELCB = EARTH LEAKAGE CIRCUIT BREAKER 30 mA</div>
                            <div>GENERATED BY ACA MOZART AI</div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};
