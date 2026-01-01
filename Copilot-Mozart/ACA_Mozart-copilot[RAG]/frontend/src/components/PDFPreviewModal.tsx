import React, { useRef, useState } from 'react';
import { X, Download, Printer, Loader2 } from 'lucide-react';
import type { DesignResult } from '../types';
// @ts-ignore
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
            margin: 10,
            filename: `Electrical-Design-${new Date().toISOString().split('T')[0]}.pdf`,
            image: { type: 'jpeg' as const, quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'portrait' as const }
        };

        try {
            await html2pdf().set(opt).from(element).save();
            // Don't auto-close, let user decide
        } catch (error) {
            console.error("PDF Generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const loads = data.data?.loads || [];
    const totalLoad = loads.reduce((sum: number, item: any) => sum + (item.load_va_l1 || item.power_kw * 1000 || 0), 0);

    // Generate Rows for empty space filling (optional) or just list

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 w-full max-w-4xl h-[90vh] rounded-xl border border-slate-700 flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <Printer size={20} className="text-sky-400" />
                        Print Preview (BOQ)
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
                    {/* A4 Paper Container - Scaled visual wrapper */}
                    <div
                        ref={contentRef}
                        className="bg-white text-black w-[210mm] min-h-[297mm] h-fit p-[15mm] shadow-lg relative"
                        style={{ fontSize: '10pt', fontFamily: 'Sarabun, sans-serif' }}
                    >
                        {/* Header */}
                        <div className="border-b-2 border-black pb-4 mb-6 flex justify-between items-start">
                            <div className="flex items-center gap-3">
                                {/* Logo Placeholder */}
                                <div className="w-12 h-12 bg-black text-white flex items-center justify-center font-bold rounded">AM</div>
                                <div>
                                    <h1 className="text-xl font-bold uppercase leading-none">ACA Mozart</h1>
                                    <p className="text-xs text-gray-500">AI Electrical Design System</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <h2 className="text-lg font-bold uppercase text-gray-800">Load Schedule</h2>
                                <p className="text-sm text-gray-600">Ref: {data.data?.project_name || 'Project-001'}</p>
                                <p className="text-xs text-gray-500">{new Date().toLocaleDateString()}</p>
                            </div>
                        </div>

                        {/* Project Info Grid */}
                        <div className="grid grid-cols-2 gap-x-8 gap-y-2 mb-6 text-sm border-b border-gray-300 pb-6">
                            <div className="grid grid-cols-[100px_1fr]">
                                <span className="font-bold text-gray-600">Project:</span>
                                <span>{data.data?.project_name || 'Residential House'}</span>
                                <span className="font-bold text-gray-600">Building:</span>
                                <span>{data.data?.building_type || 'Residential'}</span>
                                <span className="font-bold text-gray-600">Standard:</span>
                                <span>EIT 2001-56 / NEC 2023</span>
                            </div>
                            <div className="grid grid-cols-[100px_1fr]">
                                <span className="font-bold text-gray-600">Meter:</span>
                                <span>{data.data?.meter_size || '15(45)A'}</span>
                                <span className="font-bold text-gray-600">Main CB:</span>
                                <span>{data.data?.main_cb_rating}A ({data.data?.main_cb_type || 'MCB'})</span>
                                <span className="font-bold text-gray-600">Main Feeder:</span>
                                <span>{data.data?.main_feeder_size || '-'} mm² ({data.data?.main_feeder_type})</span>
                            </div>
                        </div>

                        {/* Load Table */}
                        <div className="mb-6">
                            <h3 className="font-bold mb-2 uppercase text-sm border-l-4 border-black pl-2">Branch Circuits</h3>
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr className="bg-gray-100 border-b-2 border-black">
                                        <th className="py-2 px-1 text-center font-bold w-12">Ckt</th>
                                        <th className="py-2 px-2 text-left font-bold">Description</th>
                                        <th className="py-2 px-1 text-center font-bold w-16">Load (VA)</th>
                                        <th className="py-2 px-1 text-center font-bold w-16">Breaker</th>
                                        <th className="py-2 px-1 text-center font-bold w-20">Wire</th>
                                        <th className="py-2 px-1 text-center font-bold w-16">Conduit</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loads.map((load: any, i: number) => (
                                        <tr key={i} className="border-b border-gray-200">
                                            <td className="py-2 px-1 text-center font-mono text-gray-500">{i + 1}</td>
                                            <td className="py-2 px-2 font-medium">{load.device_name}</td>
                                            <td className="py-2 px-1 text-center">{Math.round(load.load_va_l1 || 0)}</td>
                                            <td className="py-2 px-1 text-center">{load.breaker_size}A</td>
                                            <td className="py-2 px-1 text-center">{load.wire_size?.replace(' mm²', '')}</td>
                                            <td className="py-2 px-1 text-center">{load.conduit_size}</td>
                                        </tr>
                                    ))}
                                    {/* Footer */}
                                    <tr className="font-bold bg-gray-100 border-t-2 border-black">
                                        <td colSpan={2} className="py-2 px-2 text-right">TOTAL LOAD</td>
                                        <td className="py-2 px-1 text-center">{Math.round(totalLoad)} VA</td>
                                        <td colSpan={3} className="py-2 px-1"></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        {/* Footer Note */}
                        <div className="absolute bottom-[15mm] left-[15mm] right-[15mm] text-[10px] text-gray-400 border-t border-gray-200 pt-2 flex justify-between">
                            <span>Generated by ACA Mozart AI</span>
                            <span>Page 1/1</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
