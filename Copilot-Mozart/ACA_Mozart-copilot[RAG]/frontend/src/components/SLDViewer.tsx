import React from 'react';
import type { SLDData, SLDNode, SLDEdge } from '../types';

interface SLDViewerProps {
    data: SLDData | null;
}

/**
 * SLDViewer - Real-time Single Line Diagram Renderer
 * 
 * Features:
 * - SVG-based rendering (vector, scalable)
 * - Color-coded by node type
 * - Real-time updates when data changes (React re-render)
 * - Responsive to canvas size
 */
export const SLDViewer: React.FC<SLDViewerProps> = ({ data }) => {
    if (!data || !data.nodes || data.nodes.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-slate-500">
                <div className="text-center">
                    <svg className="w-16 h-16 mx-auto mb-4 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                    </svg>
                    <p className="font-mono text-sm">NO SLD DATA</p>
                    <p className="text-xs mt-1">ยังไม่มีข้อมูลวงจร</p>
                </div>
            </div>
        );
    }

    const { nodes, edges, metadata } = data;
    const width = metadata?.canvas_width || 800;
    const height = metadata?.canvas_height || 600;

    return (
        <div className="w-full h-full overflow-auto bg-slate-950 p-4">
            {/* Title */}
            <div className="text-center mb-4">
                <h3 className="text-lg font-bold text-white">
                    Single Line Diagram
                </h3>
                <p className="text-sm text-slate-400">
                    {metadata?.project_name || 'ระบบไฟฟ้า'} | {metadata?.total_kw?.toFixed(1) || 0} kW | {metadata?.circuit_count || 0} วงจร
                </p>
            </div>

            {/* SVG Diagram */}
            <svg
                viewBox={`0 0 ${width} ${height}`}
                className="w-full border border-slate-800 rounded-lg bg-slate-900"
                style={{ minHeight: '400px', maxHeight: '600px' }}
            >
                <defs>
                    {/* Glow filters */}
                    <filter id="glow-cyan" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="glow-green" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Background Grid */}
                <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1e293b" strokeWidth="0.5" />
                </pattern>
                <rect width="100%" height="100%" fill="url(#grid)" />

                {/* Render Edges (lines) first - behind nodes */}
                {edges.map((edge) => (
                    <EdgeLine key={edge.id} edge={edge} nodes={nodes} />
                ))}

                {/* Render Nodes */}
                {nodes.map((node) => (
                    <NodeBox key={node.id} node={node} />
                ))}
            </svg>

            {/* Legend */}
            <div className="mt-4 flex flex-wrap gap-4 justify-center text-xs">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-emerald-500/30 border border-emerald-500"></div>
                    <span className="text-slate-400">มิเตอร์</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-amber-500/30 border border-amber-500"></div>
                    <span className="text-slate-400">Main CB</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-cyan-500/30 border border-cyan-500"></div>
                    <span className="text-slate-400">Branch CB</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-purple-500/30 border border-purple-500"></div>
                    <span className="text-slate-400">RCBO</span>
                </div>
            </div>
        </div>
    );
};

/**
 * Node Box Component - renders a single node
 */
const NodeBox: React.FC<{ node: SLDNode }> = ({ node }) => {
    const colors = getNodeColors(node.type);
    const lines = node.label.split('\n');

    return (
        <g>
            {/* Node rectangle */}
            <rect
                x={node.x}
                y={node.y}
                width={node.width}
                height={node.height}
                rx={8}
                ry={8}
                fill={colors.bg}
                stroke={colors.border}
                strokeWidth={2}
                filter={colors.glow ? `url(#${colors.glow})` : undefined}
                className="transition-all duration-300 hover:brightness-125"
            />

            {/* Icon */}
            {node.data?.icon && (
                <text
                    x={node.x + 10}
                    y={node.y + node.height / 2 + 5}
                    fontSize={16}
                >
                    {node.data.icon}
                </text>
            )}

            {/* Label - first line */}
            <text
                x={node.x + node.width / 2}
                y={node.y + node.height / 2 - (lines.length > 1 ? 6 : 0)}
                textAnchor="middle"
                fill={colors.text}
                fontSize={11}
                fontWeight="bold"
                fontFamily="system-ui, sans-serif"
            >
                {lines[0]}
            </text>

            {/* Label - second line (if exists) */}
            {lines[1] && (
                <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height / 2 + 12}
                    textAnchor="middle"
                    fill={colors.subtext}
                    fontSize={10}
                    fontFamily="system-ui, sans-serif"
                >
                    {lines[1]}
                </text>
            )}

            {/* Wire size (if exists) */}
            {node.data?.wire && (
                <text
                    x={node.x + node.width / 2}
                    y={node.y + node.height + 12}
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize={9}
                    fontFamily="monospace"
                >
                    {node.data.wire}
                </text>
            )}
        </g>
    );
};

/**
 * Edge Line Component - renders connection between nodes
 */
const EdgeLine: React.FC<{ edge: SLDEdge; nodes: SLDNode[] }> = ({ edge, nodes }) => {
    const source = nodes.find(n => n.id === edge.source);
    const target = nodes.find(n => n.id === edge.target);

    if (!source || !target) return null;

    // Calculate connection points
    const x1 = source.x + source.width / 2;
    const y1 = source.y + source.height;
    const x2 = target.x + target.width / 2;
    const y2 = target.y;

    // Mid point for L-shaped path
    const midY = (y1 + y2) / 2;

    // Create path: vertical down, horizontal, vertical down
    const path = `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;

    return (
        <path
            d={path}
            fill="none"
            stroke="#0ea5e9"
            strokeWidth={2}
            strokeLinecap="round"
            className="transition-all duration-300"
            filter="url(#glow-cyan)"
        />
    );
};

/**
 * Get colors based on node type
 */
function getNodeColors(type: string): {
    bg: string;
    border: string;
    text: string;
    subtext: string;
    glow?: string;
} {
    switch (type) {
        case 'meter':
            return {
                bg: 'rgba(34, 197, 94, 0.1)',    // emerald
                border: '#22c55e',
                text: '#4ade80',
                subtext: '#86efac',
                glow: 'glow-green'
            };
        case 'main_breaker':
            return {
                bg: 'rgba(245, 158, 11, 0.1)',   // amber
                border: '#f59e0b',
                text: '#fbbf24',
                subtext: '#fcd34d',
            };
        case 'rcbo':
            return {
                bg: 'rgba(139, 92, 246, 0.2)',   // purple
                border: '#8b5cf6',
                text: '#a78bfa',
                subtext: '#c4b5fd',
            };
        case 'branch_breaker':
        default:
            return {
                bg: 'rgba(14, 165, 233, 0.1)',   // cyan
                border: '#0ea5e9',
                text: '#38bdf8',
                subtext: '#7dd3fc',
            };
    }
}

export default SLDViewer;
