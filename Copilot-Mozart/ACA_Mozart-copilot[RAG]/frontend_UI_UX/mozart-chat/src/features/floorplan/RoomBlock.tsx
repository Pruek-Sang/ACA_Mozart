
// src/features/floorplan/RoomBlock.tsx

import React from 'react';
import { LayoutRoom, ZoneColors } from './layout.logic';

interface RoomBlockProps {
  room: LayoutRoom;
}

// นี่คือ Component ที่แสดงผลห้อง 1 บล็อก
// มันจะแสดงชื่อห้อง และมีสีพื้นหลังตาม Zone ที่ได้รับมา

const RoomBlock: React.FC<RoomBlockProps> = ({ room }) => {
  const backgroundColor = ZoneColors[room.zone];

  return (
    <div
      style={{
        backgroundColor: backgroundColor,
        border: '1px solid #9CA3AF', // border-gray-400
        borderRadius: '0.375rem',   // rounded-md
        padding: '1rem',            // p-4
        margin: '0.5rem',           // m-2
        textAlign: 'center',
        minWidth: '100px',
        flex: 1,
      }}
    >
      <p style={{ fontWeight: '500', color: '#1F2937' }}>{room.name}</p>
    </div>
  );
};

export default RoomBlock;
