// src/features/floorplan/FloorPlanVisualizer.tsx
// Version 3: New drag-drop floor grid with beautiful design

import React, { useMemo } from 'react';
import { Sparkles, LayoutGrid } from 'lucide-react';
import FloorGrid from './FloorGrid';
import type { GridRoom } from './FloorGrid';
import { parseRoomsFromText, getFloors } from './roomParser';
import './floorplan.css';

// Legacy type for backward compatibility
interface RoomData {
  id: string;
  name: string;
  type?: string;
  floor?: number;
  zone?: string;
}

interface FloorPlanVisualizerProps {
  rooms: RoomData[];
  chatText?: string; // Optional: raw chat text to parse rooms from
}

const FloorPlanVisualizer: React.FC<FloorPlanVisualizerProps> = ({ rooms, chatText }) => {
  // Convert legacy rooms to GridRoom format or parse from chat text
  const gridRooms = useMemo((): GridRoom[] => {
    // Priority 1: Parse from chatText if provided
    if (chatText && chatText.length > 0) {
      const parsed = parseRoomsFromText(chatText);
      if (parsed.length > 0) return parsed;
    }

    // Priority 2: Convert from rooms prop
    if (rooms && rooms.length > 0) {
      return rooms.map((room, index) => ({
        id: room.id || `room-${index}`,
        name: room.name || 'ห้อง',
        type: mapRoomType(room.type || room.name),
        floor: room.floor || 1
      }));
    }

    return [];
  }, [rooms, chatText]);

  // Get sorted floors (descending: floor 2 first)
  const floors = useMemo(() => getFloors(gridRooms), [gridRooms]);

  // Get rooms for each floor
  const getRoomsForFloor = (floor: number): GridRoom[] => {
    return gridRooms.filter(r => r.floor === floor);
  };

  // Empty State - Beautiful placeholder
  if (gridRooms.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8 space-y-6 animate-fadeIn">
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center shadow-2xl shadow-indigo-500/10">
          <LayoutGrid className="w-10 h-10 text-indigo-400" />
        </div>
        <div className="space-y-3">
          <h3 className="text-xl font-semibold text-gray-200">เริ่มออกแบบผังบ้าน</h3>
          <p className="text-gray-400 max-w-xs mx-auto leading-relaxed">
            พิมพ์ความต้องการของคุณทางซ้ายมือ เช่น<br />
            <span className="text-indigo-400 font-medium">"บ้าน 2 ชั้น 3 ห้องนอน 2 ห้องน้ำ"</span>
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>ลากเพื่อจัดเรียงห้อง</span>
          <span className="text-gray-600">•</span>
          <span>ช่องว่างคือกำแพง</span>
        </div>
      </div>
    );
  }

  return (
    <div className="floor-grid-wrapper">
      {/* Header */}
      <div className="floor-grid-header">
        <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/10">
          <Sparkles className="w-5 h-5 text-indigo-400" />
        </div>
        <h2>ผังห้อง</h2>
        <div className="flex-1" />
        <span className="text-xs text-gray-500 bg-white/5 px-3 py-1 rounded-full">
          {gridRooms.filter(r => r.type !== 'wall').length} ห้อง • {floors.length} ชั้น
        </span>
      </div>

      {/* Floor Grids */}
      {floors.map(floor => (
        <FloorGrid
          key={floor}
          floor={floor}
          rooms={getRoomsForFloor(floor)}
        />
      ))}
    </div>
  );
};

/**
 * Map room type string to GridRoom type
 */
function mapRoomType(typeOrName: string): GridRoom['type'] {
  const s = (typeOrName || '').toLowerCase();

  if (s.includes('living') || s.includes('นั่งเล่น')) return 'living';
  if (s.includes('kitchen') || s.includes('ครัว')) return 'kitchen';
  if (s.includes('bedroom') || s.includes('นอน')) return 'bedroom';
  if (s.includes('bathroom') || s.includes('น้ำ')) return 'bathroom';
  if (s.includes('storage') || s.includes('เก็บ')) return 'storage';
  if (s.includes('garage') || s.includes('รถ')) return 'garage';
  if (s.includes('exterior') || s.includes('ระเบียง') || s.includes('สวน')) return 'exterior';

  return 'bedroom'; // default
}

export default FloorPlanVisualizer;
