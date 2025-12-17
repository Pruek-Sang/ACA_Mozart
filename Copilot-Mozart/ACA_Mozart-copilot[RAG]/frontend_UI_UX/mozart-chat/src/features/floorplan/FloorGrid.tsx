// src/features/floorplan/FloorGrid.tsx
// Drag-and-drop grid for rooms (3x2 per floor)

import React, { useState } from 'react';

export interface GridRoom {
    id: string;
    name: string;
    type: 'living' | 'kitchen' | 'bedroom' | 'bathroom' | 'storage' | 'garage' | 'exterior' | 'wall';
    floor: number;
}

interface FloorGridProps {
    floor: number;
    rooms: GridRoom[];
    onRoomsReorder?: (rooms: GridRoom[]) => void;
}

// สีตามประเภทห้อง (จิตวิทยาการออกแบบ)
const ROOM_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
    living: {
        bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', // ม่วง-ฟ้า: ผ่อนคลาย
        text: '#ffffff',
        icon: '🛋️'
    },
    kitchen: {
        bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', // ชมพู-ส้ม: อบอุ่น
        text: '#ffffff',
        icon: '🍳'
    },
    bedroom: {
        bg: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', // ฟ้าอ่อน-ชมพูอ่อน: สงบ
        text: '#2d3748',
        icon: '🛏️'
    },
    bathroom: {
        bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', // ฟ้า: สะอาด
        text: '#ffffff',
        icon: '🚿'
    },
    storage: {
        bg: 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)', // ม่วงอ่อน: เรียบง่าย
        text: '#2d3748',
        icon: '📦'
    },
    garage: {
        bg: 'linear-gradient(135deg, #536976 0%, #292e49 100%)', // เทาเข้ม: แข็งแกร่ง
        text: '#ffffff',
        icon: '🚗'
    },
    exterior: {
        bg: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', // เขียว: ธรรมชาติ
        text: '#ffffff',
        icon: '🌳'
    },
    wall: {
        bg: 'linear-gradient(135deg, rgba(60,60,70,0.8) 0%, rgba(40,40,50,0.9) 100%)',
        text: 'rgba(255,255,255,0.4)',
        icon: '🧱'
    }
};

// Wall pattern SVG
const WallPattern = () => (
    <svg className="absolute inset-0 w-full h-full opacity-30" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <pattern id="brick-pattern" width="20" height="10" patternUnits="userSpaceOnUse">
                <rect width="20" height="10" fill="transparent" />
                <line x1="0" y1="5" x2="20" y2="5" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
                <line x1="10" y1="0" x2="10" y2="5" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
                <line x1="0" y1="5" x2="0" y2="10" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
                <line x1="20" y1="5" x2="20" y2="10" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#brick-pattern)" />
    </svg>
);

const FloorGrid: React.FC<FloorGridProps> = ({ floor, rooms, onRoomsReorder }) => {
    // Fill remaining slots with "wall"
    const gridSlots = 6; // 3x2
    const filledRooms: GridRoom[] = [
        ...rooms,
        ...Array(Math.max(0, gridSlots - rooms.length)).fill(null).map((_, i) => ({
            id: `wall-${floor}-${i}`,
            name: 'กำแพง',
            type: 'wall' as const,
            floor
        }))
    ].slice(0, gridSlots);

    const [gridRooms, setGridRooms] = useState<GridRoom[]>(filledRooms);
    const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
    const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

    const handleDragStart = (e: React.DragEvent, index: number) => {
        setDraggedIndex(index);
        e.dataTransfer.effectAllowed = 'move';
        // Add a small delay to allow the drag image to be captured
        setTimeout(() => {
            (e.target as HTMLElement).style.opacity = '0.5';
        }, 0);
    };

    const handleDragEnd = (e: React.DragEvent) => {
        (e.target as HTMLElement).style.opacity = '1';
        setDraggedIndex(null);
        setDragOverIndex(null);
    };

    const handleDragOver = (e: React.DragEvent, index: number) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        setDragOverIndex(index);
    };

    const handleDrop = (e: React.DragEvent, dropIndex: number) => {
        e.preventDefault();
        if (draggedIndex === null || draggedIndex === dropIndex) return;

        // Swap the rooms
        const newRooms = [...gridRooms];
        const temp = newRooms[draggedIndex];
        newRooms[draggedIndex] = newRooms[dropIndex];
        newRooms[dropIndex] = temp;

        setGridRooms(newRooms);
        onRoomsReorder?.(newRooms);
        setDraggedIndex(null);
        setDragOverIndex(null);
    };

    return (
        <div className="floor-container">
            <h3 className="floor-title">
                <span className="floor-icon">🏠</span> ชั้น {floor}
            </h3>
            <div className="room-grid">
                {gridRooms.map((room, index) => {
                    const colorConfig = ROOM_COLORS[room.type] || ROOM_COLORS.wall;
                    const isWall = room.type === 'wall';
                    const isDragging = draggedIndex === index;
                    const isDragOver = dragOverIndex === index && draggedIndex !== index;

                    return (
                        <div
                            key={room.id}
                            className={`room-card ${room.type} ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''}`}
                            style={{ background: colorConfig.bg }}
                            draggable={!isWall}
                            onDragStart={(e) => handleDragStart(e, index)}
                            onDragEnd={handleDragEnd}
                            onDragOver={(e) => handleDragOver(e, index)}
                            onDrop={(e) => handleDrop(e, index)}
                        >
                            {isWall && <WallPattern />}
                            <div className="room-content">
                                <span className="room-icon">{colorConfig.icon}</span>
                                <span className="room-name" style={{ color: colorConfig.text }}>
                                    {room.name}
                                </span>
                            </div>
                            {!isWall && (
                                <div className="drag-hint">⋮⋮</div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default FloorGrid;
