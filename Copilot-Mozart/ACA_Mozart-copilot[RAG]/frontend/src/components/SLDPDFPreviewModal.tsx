import React, { useRef, useState, useEffect } from 'react';
import { X, Download, Printer, Loader2 } from 'lucide-react';
import type { SLDData, SLDNode, SLDEdge } from '../types';
import html2pdf from 'html2pdf.js';

interface SLDPDFPreviewModalProps {
    data: SLDData | null;
    projectName?: string;
    isOpen: boolean;
    onClose: () => void;
}

/**
 * SLD PDF Preview Modal
 * Black & White A4 Landscape format for professional printing
 */
export const SLDPDFPreviewModal: React.FC<SLDPDFPreviewModalProps> = ({ data, projectName, isOpen, onClose }) => {
    const contentRef = useRef<HTMLDivElement>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    // 🔧 DEBUG
    useEffect(() => {
        if (isOpen && data) {
            console.log('[SLD-PDF-DEBUG] nodes:', data.nodes?.length || 0);
            console.log('[SLD-PDF-DEBUG] edges:', data.edges?.length || 0);
            console.log('[SLD-PDF-DEBUG] metadata:', data.metadata);
        }
    }, [isOpen, data]);

    if (!isOpen) return null;

    if (!data || !data.nodes || data.nodes.length === 0) {
        return (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                <div className="bg-slate-900 rounded-xl border border-slate-700 p-8 text-center">
                    <p className="text-slate-400">ไม่มีข้อมูล SLD</p>
                    <button
                        onClick={onClose}
                        className="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white cursor-pointer"
                    >
                        ปิด
                    </button>
                </div>
            </div>
        );
    }

    const { nodes, edges, metadata } = data;
    const width = metadata?.canvas_width || 800;
    const height = metadata?.canvas_height || 600;

    const handleDownload = async () => {
        if (!contentRef.current) return;
        setIsGenerating(true);

        const opt = {
            margin: 5,
            filename: `SLD-${projectName || metadata?.project_name || 'Project'}.pdf`,
            image: { type: 'jpeg' as const, quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'landscape' as const }
        };

        try {
            await html2pdf().set(opt).from(contentRef.current).save();
            console.log('[SLD-PDF] Downloaded successfully');
        } catch (error) {
            console.error("[SLD-PDF] Generation failed", error);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 w-full max-w-6xl h-[90vh] rounded-xl border border-slate-700 flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <Printer size={20} className="text-sky-400" />
                        SLD Print Preview (Black & White)
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

                {/* Preview Area */}
                <div className="flex-1 overflow-y-auto p-8 bg-slate-800 flex justify-center">
                    {/* A4 Landscape Container - Black & White */}
                    <div
                        ref={contentRef}
                        className="bg-white text-black w-[297mm] min-h-[210mm] h-fit p-[10mm] shadow-lg"
                        style={{ fontFamily: 'Sarabun, sans-serif' }}
                    >
                        {/* Title */}
                        <div className="text-center font-bold mb-4 uppercase text-lg border-b-2 border-black pb-2">
                            SINGLE LINE DIAGRAM (SLD)
                        </div>

                        {/* Project Info */}
                        <div className="flex justify-between text-xs mb-4 border-b border-black pb-2">
                            <div><strong>PROJECT:</strong> {projectName || metadata?.project_name || 'RESIDENTIAL'}</div>
                            <div><strong>TOTAL:</strong> {metadata?.total_kw?.toFixed(1) || 0} kW | {metadata?.circuit_count || 0} วงจร</div>
                            <div><strong>DATE:</strong> {new Date().toLocaleDateString('th-TH')}</div>
                        </div>

                        {/* Black & White SVG Diagram */}
                        <svg
                            viewBox={`0 0 ${width} ${height}`}
                            className="w-full border border-black"
                            style={{ minHeight: '350px', maxHeight: '500px', background: 'white' }}
                        >
                            {/* Background Grid (light gray for print) */}
                            <pattern id="grid-bw" width="20" height="20" patternUnits="userSpaceOnUse">
                                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e5e5" strokeWidth="0.5" />
                            </pattern>
                            <rect width="100%" height="100%" fill="url(#grid-bw)" />

                            {/* Render Edges (black lines) */}
                            {edges.map((edge) => (
                                <EdgeLineBW key={edge.id} edge={edge} nodes={nodes} />
                            ))}

                            {/* Render Nodes (black & white) */}
                            {nodes.map((node) => (
                                <NodeBoxBW key={node.id} node={node} />
                            ))}
                        </svg>

                        {/* Legend */}
                        <div className="mt-4 flex flex-wrap gap-6 justify-center text-xs border-t border-black pt-2">
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-black rounded-full"></div>
                                <span>มิเตอร์ (kWh)</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-black"></div>
                                <span>Main CB</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border border-black"></div>
                                <span>Branch CB</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 border border-black bg-gray-300"></div>
                                <span>RCBO</span>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="text-center text-xs mt-4 pt-2 border-t border-black">
                            GENERATED BY ACA MOZART AI
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

/**
 * Black & White Node Box
 */
const NodeBoxBW: React.FC<{ node: SLDNode }> = ({ node }) => {
    const lines = node.label.split('\n');
    const isMeter = node.type === 'meter';
    const isMain = node.type === 'main_breaker';
    const isRCBO = node.type === 'rcbo';

    return (
        <g>
            {/* Box - different styles per type */}
            {isMeter ? (
                // Meter: Circle
                <circle
                    cx={node.x + node.width / 2}
                    cy={node.y + node.height / 2}
                    r={Math.min(node.width, node.height) / 2 - 5}
                    fill="white"
                    stroke="black"
                    strokeWidth={2}
                />
            ) : (
                // CB: Rectangle
                <rect
                    x={node.x}
                    y={node.y}
                    width={node.width}
                    height={node.height}
                    fill={isRCBO ? '#e5e5e5' : 'white'}
                    stroke="black"
                    strokeWidth={isMain ? 3 : 1.5}
                    rx={2}
                />
            )}

            {/* Label - first line */}
            <text
                x={node.x + node.width / 2}
                y={node.y + node.height / 2 + 5}
                textAnchor="middle"
                fill="black"
                fontSize={10}
                fontWeight="bold"
                fontFamily="Arial, sans-serif"
            >
                {lines[0]}
            </text>

            {/* Label - second line */}
            {lines[1] && (
                <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height / 2 + 18}
                    textAnchor="middle"
                    fill="black"
                    fontSize={9}
                    fontFamily="Arial, sans-serif"
                >
                    {lines[1]}
                </text>
            )}

            {/* Wire Info */}
            {node.data?.wire && (
                <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height + 12}
                    textAnchor="middle"
                    fill="black"
                    fontSize={8}
                    fontFamily="monospace"
                >
                    {node.data.wire}
                </text>
            )}
        </g>
    );
};

/**
 * Black & White Edge Line
 */
const EdgeLineBW: React.FC<{ edge: SLDEdge; nodes: SLDNode[] }> = ({ edge, nodes }) => {
    const source = nodes.find(n => n.id === edge.source);
    const target = nodes.find(n => n.id === edge.target);

    if (!source || !target) return null;

    const x1 = source.x + source.width / 2;
    const y1 = source.y + source.height;
    const x2 = target.x + target.width / 2;
    const y2 = target.y;

    const midY = (y1 + y2) / 2;
    const path = `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;

    return (
        <path
            d={path}
            fill="none"
            stroke="black"
            strokeWidth={1.5}
            strokeLinecap="round"
        />
    );
};

export default SLDPDFPreviewModal;
