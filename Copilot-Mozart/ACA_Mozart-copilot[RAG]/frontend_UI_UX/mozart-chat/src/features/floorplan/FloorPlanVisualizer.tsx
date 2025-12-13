
// src/features/floorplan/FloorPlanVisualizer.tsx

import React from 'react';
import { calculateLayout, RoomData } from './layout.logic';
import RoomBlock from './RoomBlock';

interface FloorPlanVisualizerProps {
  rooms: RoomData[]; // รับข้อมูลห้องดิบๆ มาจาก App.tsx
}

const FloorPlanVisualizer: React.FC<FloorPlanVisualizerProps> = ({ rooms }) => {
  // เรียกใช้ "สมอง" เพื่อคำนวณ Layout
  const floorLayouts = calculateLayout(rooms);

  if (floorLayouts.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#6B7280' }}>
        <p>รอรับข้อมูลการออกแบบ...</p>
        <p>ลองพิมพ์ "ออกแบบบ้าน 2 ชั้น 3 ห้องนอน" ทางซ้ายมือ</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem', fontFamily: 'sans-serif' }}>
      <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>ผังห้องและโซน (Floor Plan & Zoning)</h2>
      {floorLayouts.map(({ floor, rows }) => (
        <div key={floor} style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '500', color: '#4B5563', marginBottom: '0.5rem' }}>
            ชั้นที่ {floor}
          </h3>
          <div style={{ border: '1px solid #D1D5DB', borderRadius: '0.5rem', padding: '0.5rem' }}>
            {rows.map((row, rowIndex) => (
              <div key={rowIndex} style={{ display: 'flex', justifyContent: 'center', alignItems: 'stretch' }}>
                {row.map(room => (
                  <RoomBlock key={room.id} room={room} />
                ))}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default FloorPlanVisualizer;
