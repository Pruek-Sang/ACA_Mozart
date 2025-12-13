// src/features/floorplan/RoomBlock.tsx
import React, { useMemo } from 'react';
import { ZoneStyles } from './layout.logic';
import type { LayoutRoom, LoadData } from './layout.logic';
import {
  BedDouble,
  Utensils,
  Bath,
  Sofa,
  CarFront,
  Warehouse,
  Briefcase,
  Trees,
  Sun,
  Lightbulb,
  Zap,
  Power
} from 'lucide-react';

interface RoomBlockProps {
  room: LayoutRoom;
}

const RoomBlock: React.FC<RoomBlockProps> = ({ room }) => {
  const styles = ZoneStyles[room.zone];
  const delayStyle = { animationDelay: `${room.index * 0.1}s` };

  // **[NEW]** Helper to get icon based on room type
  const RoomIcon = useMemo(() => {
    const type = room.room_type.toUpperCase();
    if (type.includes('BED')) return BedDouble;
    if (type.includes('KITCHEN') || type.includes('DINING')) return Utensils;
    if (type.includes('BATH') || type.includes('TOILET')) return Bath;
    if (type.includes('LIVING') || type.includes('RECEPTION')) return Sofa;
    if (type.includes('GARAGE') || type.includes('PARKING')) return CarFront;
    if (type.includes('STORAGE') || type.includes('PUMP')) return Warehouse;
    if (type.includes('OFFICE') || type.includes('STUDY')) return Briefcase;
    if (type.includes('GARDEN') || type.includes('TERRACE')) return Trees;
    return Sun; // Default
  }, [room.room_type]);

  // **[NEW]** Helper to get load icon
  const getLoadIcon = (type: string) => {
    if (type === 'LIGHT') return <Lightbulb className="w-3 h-3 text-yellow-200" />;
    if (type === 'OUTLET') return <Zap className="w-3 h-3 text-blue-200" />;
    if (type === 'SWITCH') return <Power className="w-3 h-3 text-green-200" />;
    return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
  };

  return (
    <div
      id={`room-${room.id}`}
      style={delayStyle}
      className={`
        relative group
        w-40 h-32 md:w-48 md:h-36
        flex flex-col items-center justify-center
        rounded-xl border backdrop-blur-md
        transition-all duration-300 ease-out
        hover:scale-105 hover:shadow-xl hover:z-20
        cursor-default select-none
        animate-fadeIn opacity-0 fill-mode-forwards
        ${styles.container}
        ${styles.border}
      `}
    >
      {/* Zone Badge */}
      <div className={`
        absolute top-2 right-2 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider opacity-70
        border border-white/10
        ${styles.text}
      `}>
        {room.zone}
      </div>

      {/* Main Icon */}
      <div className={`mb-2 p-2 rounded-full bg-white/5 shadow-inner ${styles.icon}`}>
        <RoomIcon className="w-6 h-6 md:w-8 md:h-8" />
      </div>

      {/* Room Name */}
      <div className="text-center px-2 w-full">
        <h4 className={`text-sm md:text-base font-semibold truncate ${styles.text}`}>
          {room.name}
        </h4>
        <p className="text-[10px] text-gray-400 font-mono mt-0.5">
          ID: {room.id.slice(0, 4)}
        </p>
      </div>

      {/* **[NEW]** Loads Simulation */}
      {room.loads && room.loads.length > 0 && (
        <div className="absolute bottom-2 left-2 right-2 flex justify-center gap-1 flex-wrap">
          {room.loads.map((load: LoadData, idx: number) => (
            <div key={`${load.id}-${idx}`} title={load.name} className="p-0.5 bg-black/20 rounded hover:bg-black/40 transition-colors">
              {getLoadIcon(load.type)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RoomBlock;
