/**
 * Professional Electrical Symbols (IEEE/IEC Style)
 * Note: These are functional components for SVG rendering inside <svg> elements
 */

interface SymbolProps {
    size?: number;
    color?: string;
}

export const SldSymbolMeter = ({ size = 40, color = "currentColor" }: SymbolProps) => (
    <g>
        <rect x="0" y="0" width={size} height={size} stroke={color} fill="none" strokeWidth="2" />
        <text x={size / 2} y={size / 2 + 5} textAnchor="middle" fill={color} fontSize={size / 2.5} fontFamily="sans-serif" fontWeight="bold">kWh</text>
    </g>
);

export const SldSymbolCB = ({ size = 40, color = "currentColor" }: SymbolProps) => (
    <g>
        {/* Main Breaker Box */}
        <rect x="0" y="0" width={size} height={size} stroke={color} fill="none" strokeWidth="2" rx="4" />
        {/* Switch Symbol */}
        <path d={`M${size * 0.3} ${size * 0.7} L${size * 0.7} ${size * 0.3}`} stroke={color} strokeWidth="2" />
        <text x={size * 0.8} y={size * 0.9} textAnchor="end" fill={color} fontSize={size / 4}>CB</text>
    </g>
);

export const SldSymbolMCB = ({ size = 40, color = "currentColor" }: SymbolProps) => (
    <g>
        <rect x="0" y="0" width={size} height={size} stroke={color} fill="none" strokeWidth="1.5" rx="4" />
        <path d={`M${size * 0.3} ${size * 0.7} L${size * 0.7} ${size * 0.3}`} stroke={color} strokeWidth="1.5" />
    </g>
);
