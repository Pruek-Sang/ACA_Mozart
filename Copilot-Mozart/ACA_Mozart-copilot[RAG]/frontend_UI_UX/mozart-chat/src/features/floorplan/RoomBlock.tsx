// src/features/floorplan/RoomBlock.tsx
import React, { useMemo, useState } from 'react';
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
  Power,
  GripVertical
} from 'lucide-react';

interface RoomBlockProps {
  room: LayoutRoom;
  onDragStart?: (room: LayoutRoom) => void;
  onDragEnd?: () => void;
}

const RoomBlock: React.FC<RoomBlockProps> = ({ room, onDragStart, onDragEnd }) => {
  const styles = ZoneStyles[room.zone];
  const delayStyle = { animationDelay: `${room.index * 0.1}s` };
  const [isDragging, setIsDragging] = useState(false);

  // Helper to get icon based on room type
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

  // Helper to get load icon
  const getLoadIcon = (type: string) => {
    if (type === 'LIGHT') return <Lightbulb className="w-3 h-3 text-yellow-200" />;
    if (type === 'OUTLET') return <Zap className="w-3 h-3 text-blue-200" />;
    if (type === 'SWITCH') return <Power className="w-3 h-3 text-green-200" />;
    return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
  };

  const handleDragStart = (e: React.DragEvent) => {
    setIsDragging(true);
    e.dataTransfer.setData('text/plain', room.id);
    onDragStart?.(room);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    onDragEnd?.();
  };

  return (
    <div
      id={`room-${room.id}`}
      style={delayStyle}
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      className={`
        relative group
        w-28 h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 lg:w-40 lg:h-40
        flex flex-col items-center justify-between p-2
        rounded-xl border border-white/10 backdrop-blur-md
        transition-all duration-300 ease-out
        hover:scale-105 hover:shadow-2xl hover:shadow-white/10 hover:z-20 hover:border-white/30
        cursor-grab active:cursor-grabbing select-none
        animate-fadeIn opacity-0 fill-mode-forwards
        shadow-lg shadow-black/20
        ${isDragging ? 'opacity-50 scale-95' : ''}
        ${styles.container}
        ${styles.border}
      `}
    >
      {/* Drag Handle */}
      <div className="absolute top-1 left-1 opacity-0 group-hover:opacity-50 transition-opacity">
        <GripVertical className="w-3 h-3 text-white/50" />
      </div>

      {/* Zone Badge - top right */}
      <div className={`
        absolute top-1 right-1 px-1 py-0.5 rounded text-[8px] sm:text-[9px] font-bold uppercase tracking-wide opacity-60
        border border-white/10
        ${styles.text}
      `}>
        {room.zone}
      </div>

      {/* Main Icon - centered top area */}
      <div className={`mt-3 p-1.5 sm:p-2 rounded-full bg-white/5 shadow-inner ${styles.icon}`}>
        <RoomIcon className="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7" />
      </div>

      {/* Room Name - bottom area, NOT blocking icon */}
      <div className="text-center w-full mt-auto">
        <h4 className={`text-[10px] sm:text-xs md:text-sm font-semibold truncate px-1 ${styles.text}`}>
          {room.name}
        </h4>
        <p className="text-[8px] text-gray-400 font-mono">
          ID: {room.id.slice(0, 4)}
        </p>
      </div>

      {/* Loads Simulation - absolute bottom */}
      {room.loads && room.loads.length > 0 && (
        <div className="absolute -bottom-1 left-1 right-1 flex justify-center gap-0.5 flex-wrap">
          {room.loads.slice(0, 4).map((load: LoadData, idx: number) => (
            <div key={`${load.id}-${idx}`} title={load.name} className="p-0.5 bg-black/30 rounded hover:bg-black/50 transition-colors">
              {getLoadIcon(load.type)}
            </div>
          ))}
          {room.loads.length > 4 && (
            <span className="text-[8px] text-gray-400">+{room.loads.length - 4}</span>
          )}
        </div>
      )}
    </div>
  );
};

export default RoomBlock;
