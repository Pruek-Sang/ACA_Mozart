// src/features/floorplan/FloorPlanVisualizer.tsx
import React, { useEffect, useRef, useState } from 'react';
import { calculateLayout } from './layout.logic';
import type { RoomData, FloorLayout, WireData } from './layout.logic';
import RoomBlock from './RoomBlock';
import { Sparkles, Map } from 'lucide-react';

interface FloorPlanVisualizerProps {
  rooms: RoomData[];
}

const FloorPlanVisualizer: React.FC<FloorPlanVisualizerProps> = ({ rooms }) => {
  const floorLayouts: FloorLayout[] = calculateLayout(rooms);
  const containerRef = useRef<HTMLDivElement>(null);
  const [wires, setWires] = useState<Array<{ id: string; d: string; color: string }>>([]);

  // **[NEW]** Calculate SVG paths for wires after render
  useEffect(() => {
    if (!containerRef.current) return;

    const newWires: Array<{ id: string; d: string; color: string }> = [];

    floorLayouts.forEach(floor => {
      floor.wires.forEach((wire: WireData) => {
        const fromEl = document.getElementById(`room-${wire.fromRoomId}`);
        const toEl = document.getElementById(`room-${wire.toRoomId}`);

        if (fromEl && toEl) {
          const fromRect = fromEl.getBoundingClientRect();
          const toRect = toEl.getBoundingClientRect();
          const containerRect = containerRef.current!.getBoundingClientRect();

          // Calculate center points relative to the container
          const x1 = fromRect.left + fromRect.width / 2 - containerRect.left;
          const y1 = fromRect.top + fromRect.height / 2 - containerRect.top;
          const x2 = toRect.left + toRect.width / 2 - containerRect.left;
          const y2 = toRect.top + toRect.height / 2 - containerRect.top;

          // Create a curved path (cubic bezier)
          const midX = (x1 + x2) / 2;
          const midY = (y1 + y2) / 2;
          // Curve intensity
          const offset = 40;

          let d = '';
          // Simple heuristic for curve direction based on relative position
          if (Math.abs(x1 - x2) > Math.abs(y1 - y2)) {
            // Horizontal connection -> curve up/down
            d = `M ${x1} ${y1} Q ${midX} ${midY - offset} ${x2} ${y2}`;
          } else {
            // Vertical connection -> curve left/right
            d = `M ${x1} ${y1} Q ${midX - offset} ${midY} ${x2} ${y2}`;
          }

          // **Extracted Color from Tailwind class map (simplified mapping for SVG stroke)**
          // Note: Tailwind classes like 'text-emerald-400' are CSS. For SVG stroke we need actual colors.
          // For MVP we map zone to hex approximations matching the Tailwind palette.
          let strokeColor = '#9CA3AF'; // default gray
          if (wire.zone === 'PUBLIC') strokeColor = '#34D399'; // emerald-400
          if (wire.zone === 'SERVICE') strokeColor = '#FBBF24'; // amber-400
          if (wire.zone === 'PRIVATE') strokeColor = '#FB7185'; // rose-400
          if (wire.zone === 'OUTDOOR') strokeColor = '#94A3B8'; // slate-400

          newWires.push({ id: wire.id, d, color: strokeColor });
        }
      });
    });

    setWires(newWires);
  }, [rooms, floorLayouts.length]); // Re-run when rooms change

  // Empty State - Beautifully styled
  if (floorLayouts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8 space-y-6 animate-fadeIn">
        <div className="w-24 h-24 rounded-full bg-bgSecondary/50 border border-gray-800 flex items-center justify-center shadow-2xl shadow-indigo-500/10">
          <Map className="w-10 h-10 text-gray-600" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-semibold text-gray-300">เริ่มการออกแบบ</h3>
          <p className="text-gray-500 max-w-xs mx-auto">
            พิมพ์ความต้องการของคุณทางซ้ายมือ เช่น <br />
            <span className="text-accentMozart">"ออกแบบบ้าน 2 ชั้น 3 ห้องนอน"</span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-6 relative" ref={containerRef}>

      {/* **[NEW]** SVG Overlay for Wires */}
      <svg className="absolute inset-0 pointer-events-none z-0 w-full h-full" style={{ minHeight: '100%' }}>
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#6B7280" opacity="0.5" />
          </marker>
        </defs>
        {wires.map(wire => (
          <path
            key={wire.id}
            d={wire.d}
            stroke={wire.color}
            strokeWidth="2"
            fill="none"
            strokeDasharray="5,5"
            className="animate-[dash_20s_linear_infinite]"
            opacity="0.6"
          />
        ))}
      </svg>

      <div className="relative z-10 space-y-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-accentMozart/10 border border-accentMozart/20">
            <Sparkles className="w-5 h-5 text-accentMozart" />
          </div>
          <h2 className="text-xl font-semibold text-gray-100">Floor Plan & Zoning</h2>
        </div>

        {floorLayouts.map((floorData: FloorLayout) => (
          <div key={floorData.floor} className="space-y-4 animate-fadeIn">
            <div className="flex items-center gap-4">
              <h3 className="text-sm font-medium text-textSecondary uppercase tracking-wider">
                ชั้นที่ {floorData.floor}
              </h3>
              <div className="h-px bg-gray-800 flex-1" />
            </div>

            <div className="grid gap-6 p-6 rounded-2xl bg-bgSecondary/30 border border-gray-800/50 backdrop-blur-sm shadow-xl relative overflow-hidden group">
              {/* Subtle grid background */}
              <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none" />

              {floorData.rows.map((row, rowIndex: number) => (
                <div key={rowIndex} className="flex flex-wrap justify-center gap-6 relative z-10">
                  {row.map(room => (
                    <RoomBlock key={room.id} room={room} />
                  ))}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FloorPlanVisualizer;
