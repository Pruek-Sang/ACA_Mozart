/**
 * Professional Electrical Symbols (IEEE/IEC Style)
 * 
 * Updated with proper electrical schematic symbols
 * Follows IEEE Std 315 and IEC 60617
 * 
 * Author: Fixia
 * Date: 2026-01-03
 */

// cn import removed - not used in SVG symbols

interface SymbolProps {
    size?: number;
    color?: string;
    label?: string;
    rating?: string;
    className?: string;
}

// === METER SYMBOL ===
// Circle with kWh text (standard energy meter symbol)
export const SldSymbolMeter = ({ size = 50, color = "currentColor", label }: SymbolProps) => (
    <g>
        {/* Circle body */}
        <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 3}
            stroke={color}
            strokeWidth="2"
            fill="none"
        />
        {/* kWh text */}
        <text
            x={size / 2}
            y={size / 2 - 2}
            textAnchor="middle"
            fill={color}
            fontSize={size / 4}
            fontFamily="Arial, sans-serif"
            fontWeight="bold"
        >
            kWh
        </text>
        {/* Power symbol below */}
        <text
            x={size / 2}
            y={size / 2 + 12}
            textAnchor="middle"
            fill={color}
            fontSize={size / 6}
            fontFamily="Arial, sans-serif"
        >
            ⚡
        </text>
        {/* Label */}
        {label && (
            <text
                x={size / 2}
                y={size + 12}
                textAnchor="middle"
                fill={color}
                fontSize={10}
                fontFamily="Arial, sans-serif"
            >
                {label}
            </text>
        )}
    </g>
);

// === MAIN CIRCUIT BREAKER (MCCB) ===
// IEC style with disconnect symbol
export const SldSymbolMainCB = ({ size = 50, color = "currentColor", rating, label }: SymbolProps) => (
    <g>
        {/* Background box */}
        <rect
            x={2}
            y={2}
            width={size - 4}
            height={size - 4}
            stroke={color}
            strokeWidth="2"
            fill="rgba(99, 102, 241, 0.1)"
            rx="4"
        />
        {/* Switch/disconnect symbol - angled line */}
        <line
            x1={size * 0.2}
            y1={size * 0.7}
            x2={size * 0.5}
            y2={size * 0.3}
            stroke={color}
            strokeWidth="3"
        />
        {/* Terminal dots */}
        <circle cx={size * 0.2} cy={size * 0.75} r={4} fill={color} />
        <circle cx={size * 0.5} cy={size * 0.25} r={4} fill={color} />
        {/* Thermal/magnetic trip coil */}
        <rect
            x={size * 0.6}
            y={size * 0.3}
            width={size * 0.25}
            height={size * 0.4}
            stroke={color}
            strokeWidth="1.5"
            fill="none"
        />
        {/* Rating text */}
        {rating && (
            <text
                x={size / 2}
                y={size + 12}
                textAnchor="middle"
                fill={color}
                fontSize={10}
                fontFamily="Arial, sans-serif"
                fontWeight="bold"
            >
                {rating}
            </text>
        )}
        {/* Label */}
        {label && (
            <text
                x={size / 2}
                y={size + 24}
                textAnchor="middle"
                fill="#6b7280"
                fontSize={9}
                fontFamily="Arial, sans-serif"
            >
                {label}
            </text>
        )}
    </g>
);

// === MCB (Miniature Circuit Breaker) ===
// Smaller breaker symbol
export const SldSymbolMCB = ({ size = 40, color = "currentColor", rating }: SymbolProps) => (
    <g>
        {/* Box */}
        <rect
            x={2}
            y={2}
            width={size - 4}
            height={size - 4}
            stroke={color}
            strokeWidth="1.5"
            fill="rgba(59, 130, 246, 0.05)"
            rx="3"
        />
        {/* Switch line */}
        <line
            x1={size * 0.25}
            y1={size * 0.7}
            x2={size * 0.75}
            y2={size * 0.3}
            stroke={color}
            strokeWidth="2"
        />
        {/* Terminal circles */}
        <circle cx={size * 0.25} cy={size * 0.7} r={3} fill={color} />
        <circle cx={size * 0.75} cy={size * 0.3} r={3} fill={color} />
        {/* Rating */}
        {rating && (
            <text
                x={size / 2}
                y={size + 10}
                textAnchor="middle"
                fill={color}
                fontSize={9}
                fontFamily="Arial, sans-serif"
            >
                {rating}
            </text>
        )}
    </g>
);

// === RCBO (Residual Current Breaker with Overcurrent) ===
// MCB + earth leakage symbol
export const SldSymbolRCBO = ({ size = 45, color = "currentColor", rating }: SymbolProps) => (
    <g>
        {/* Box with earth leakage indication */}
        <rect
            x={2}
            y={2}
            width={size - 4}
            height={size - 4}
            stroke={color}
            strokeWidth="1.5"
            fill="rgba(34, 197, 94, 0.05)"
            rx="3"
        />
        {/* Switch line */}
        <line
            x1={size * 0.2}
            y1={size * 0.65}
            x2={size * 0.55}
            y2={size * 0.35}
            stroke={color}
            strokeWidth="2"
        />
        {/* Terminal circles */}
        <circle cx={size * 0.2} cy={size * 0.65} r={3} fill={color} />
        <circle cx={size * 0.55} cy={size * 0.35} r={3} fill={color} />
        {/* Test button (small rectangle) */}
        <rect
            x={size * 0.65}
            y={size * 0.2}
            width={size * 0.2}
            height={size * 0.25}
            stroke={color}
            strokeWidth="1"
            fill="none"
        />
        <text
            x={size * 0.75}
            y={size * 0.38}
            textAnchor="middle"
            fill={color}
            fontSize={6}
        >
            T
        </text>
        {/* Earth symbol */}
        <g transform={`translate(${size * 0.65}, ${size * 0.55})`}>
            <line x1={0} y1={0} x2={size * 0.2} y2={0} stroke={color} strokeWidth="1.5" />
            <line x1={3} y1={4} x2={size * 0.2 - 3} y2={4} stroke={color} strokeWidth="1" />
            <line x1={6} y1={8} x2={size * 0.2 - 6} y2={8} stroke={color} strokeWidth="0.8" />
        </g>
        {/* Rating */}
        {rating && (
            <text
                x={size / 2}
                y={size + 10}
                textAnchor="middle"
                fill="#22c55e"
                fontSize={9}
                fontFamily="Arial, sans-serif"
                fontWeight="bold"
            >
                {rating}
            </text>
        )}
        {/* RCBO label */}
        <text
            x={size / 2}
            y={size + 22}
            textAnchor="middle"
            fill="#6b7280"
            fontSize={8}
            fontFamily="Arial, sans-serif"
        >
            RCBO
        </text>
    </g>
);

// === BUS BAR ===
export const SldSymbolBusBar = ({ size = 100, color = "currentColor" }: SymbolProps) => (
    <g>
        {/* Horizontal bus bar */}
        <rect
            x={0}
            y={0}
            width={size}
            height={8}
            fill={color}
            rx={2}
        />
    </g>
);

// === LOAD SYMBOL ===
// Generic load (circle with arrow or label)
export const SldSymbolLoad = ({ size = 35, color = "currentColor", label }: SymbolProps) => (
    <g>
        {/* Circle */}
        <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 2}
            stroke={color}
            strokeWidth="1.5"
            fill="rgba(156, 163, 175, 0.1)"
        />
        {/* Arrow or load indicator */}
        <path
            d={`M${size / 2} ${size * 0.25} L${size / 2} ${size * 0.75} M${size * 0.35} ${size * 0.6} L${size / 2} ${size * 0.75} L${size * 0.65} ${size * 0.6}`}
            stroke={color}
            strokeWidth="1.5"
            fill="none"
        />
        {/* Label */}
        {label && (
            <text
                x={size / 2}
                y={size + 10}
                textAnchor="middle"
                fill={color}
                fontSize={8}
                fontFamily="Arial, sans-serif"
            >
                {label}
            </text>
        )}
    </g>
);

// === WIRE/CONNECTION LINE ===
interface WireProps {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    color?: string;
    label?: string;
}

export const SldWire = ({ x1, y1, x2, y2, color = "currentColor", label }: WireProps) => {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;

    return (
        <g>
            <line
                x1={x1} y1={y1}
                x2={x2} y2={y2}
                stroke={color}
                strokeWidth="2"
            />
            {label && (
                <text
                    x={midX}
                    y={midY - 5}
                    textAnchor="middle"
                    fill={color}
                    fontSize={8}
                    fontFamily="Arial, sans-serif"
                    style={{ transform: 'rotate(-45deg)', transformOrigin: `${midX}px ${midY}px` }}
                >
                    {label}
                </text>
            )}
        </g>
    );
};

// === AC UNIT SYMBOL ===
export const SldSymbolAC = ({ size = 40, color = "currentColor", label }: SymbolProps) => (
    <g>
        <rect
            x={2} y={2}
            width={size - 4} height={size - 4}
            stroke={color} strokeWidth="1.5"
            fill="rgba(59, 130, 246, 0.1)"
            rx="3"
        />
        {/* AC wave symbol */}
        <path
            d={`M${size * 0.2} ${size / 2} Q${size * 0.35} ${size * 0.3} ${size / 2} ${size / 2} T${size * 0.8} ${size / 2}`}
            stroke={color}
            strokeWidth="1.5"
            fill="none"
        />
        {/* Snowflake */}
        <text
            x={size / 2}
            y={size * 0.75}
            textAnchor="middle"
            fill={color}
            fontSize={10}
        >
            ❄
        </text>
        {label && (
            <text
                x={size / 2} y={size + 10}
                textAnchor="middle" fill={color} fontSize={8}
            >
                {label}
            </text>
        )}
    </g>
);

// === WATER HEATER SYMBOL ===
export const SldSymbolWaterHeater = ({ size = 40, color = "currentColor", label }: SymbolProps) => (
    <g>
        <rect
            x={2} y={2}
            width={size - 4} height={size - 4}
            stroke={color} strokeWidth="1.5"
            fill="rgba(239, 68, 68, 0.1)"
            rx="3"
        />
        {/* Heating element zigzag */}
        <path
            d={`M${size * 0.2} ${size * 0.5} L${size * 0.35} ${size * 0.3} L${size * 0.5} ${size * 0.5} L${size * 0.65} ${size * 0.3} L${size * 0.8} ${size * 0.5}`}
            stroke="#ef4444"
            strokeWidth="2"
            fill="none"
        />
        {/* Water drop */}
        <text
            x={size / 2}
            y={size * 0.75}
            textAnchor="middle"
            fill="#3b82f6"
            fontSize={10}
        >
            💧
        </text>
        {label && (
            <text
                x={size / 2} y={size + 10}
                textAnchor="middle" fill={color} fontSize={8}
            >
                {label}
            </text>
        )}
    </g>
);

export default {
    SldSymbolMeter,
    SldSymbolMainCB,
    SldSymbolMCB,
    SldSymbolRCBO,
    SldSymbolBusBar,
    SldSymbolLoad,
    SldWire,
    SldSymbolAC,
    SldSymbolWaterHeater,
};
