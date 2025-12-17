// src/features/floorplan/roomParser.ts
// Parse room information from chat text response

import type { GridRoom } from './FloorGrid';

/**
 * Parse rooms from the chat text response
 * Extracts room names and floor information from patterns like:
 * - "└─ ห้องนั่งเล่น: คู่×5"
 * - "ชั้น 1" / "ชั้น 2"
 */
export function parseRoomsFromText(text: string): GridRoom[] {
    const rooms: GridRoom[] = [];
    const lines = text.split('\n');
    let currentFloor = 1;
    const addedRooms = new Set<string>(); // Prevent duplicates

    for (const line of lines) {
        // Detect floor number
        const floorMatch = line.match(/ชั้น\s*(\d+)/);
        if (floorMatch) {
            currentFloor = Number.parseInt(floorMatch[1], 10);
        }

        // Detect room from "└─" pattern
        const roomMatch = line.match(/└─\s*(.+?):/);
        if (roomMatch) {
            const roomName = roomMatch[1].trim();
            const roomKey = `${roomName}-${currentFloor}`;

            if (!addedRooms.has(roomKey)) {
                addedRooms.add(roomKey);
                rooms.push({
                    id: `room-${rooms.length + 1}`,
                    name: roomName,
                    type: detectRoomType(roomName),
                    floor: currentFloor
                });
            }
        }
    }

    // If no rooms found from pattern, try alternative patterns
    if (rooms.length === 0) {
        return parseRoomsAlternative(text);
    }

    return rooms;
}

/**
 * Alternative parser for different text formats
 */
function parseRoomsAlternative(text: string): GridRoom[] {
    const rooms: GridRoom[] = [];
    const addedRooms = new Set<string>();

    // Pattern: "ห้องนอน", "ห้องครัว", "ห้องน้ำ", etc.
    const roomPatterns = [
        { pattern: /ห้องนอน\s*(\d*)/gi, type: 'bedroom' as const },
        { pattern: /ห้องนั่งเล่น/gi, type: 'living' as const },
        { pattern: /ห้องครัว/gi, type: 'kitchen' as const },
        { pattern: /ห้องน้ำ\s*(\d*)/gi, type: 'bathroom' as const },
        { pattern: /ห้องเก็บของ/gi, type: 'storage' as const },
        { pattern: /โรงรถ/gi, type: 'garage' as const },
        { pattern: /ระเบียง/gi, type: 'exterior' as const },
    ];

    // Simple floor detection
    const hasFloor2 = text.includes('ชั้น 2') || text.includes('ชั้น2');

    for (const { pattern, type } of roomPatterns) {
        let match;
        while ((match = pattern.exec(text)) !== null) {
            const roomName = match[0].trim();
            const num = match[1] || '';
            const fullName = num ? `${roomName}` : roomName;

            if (!addedRooms.has(fullName)) {
                addedRooms.add(fullName);

                // Assign floor based on room type heuristic
                let floor = 1;
                if (type === 'bedroom' && hasFloor2) {
                    floor = 2;
                }

                rooms.push({
                    id: `room-${rooms.length + 1}`,
                    name: fullName,
                    type,
                    floor
                });
            }
        }
    }

    return rooms;
}

/**
 * Detect room type from Thai room name
 */
function detectRoomType(roomName: string): GridRoom['type'] {
    const name = roomName.toLowerCase();

    if (name.includes('นั่งเล่น') || name.includes('living')) return 'living';
    if (name.includes('ครัว') || name.includes('kitchen')) return 'kitchen';
    if (name.includes('นอน') || name.includes('bedroom')) return 'bedroom';
    if (name.includes('น้ำ') || name.includes('bathroom') || name.includes('ห้องน้ำ')) return 'bathroom';
    if (name.includes('เก็บ') || name.includes('storage')) return 'storage';
    if (name.includes('รถ') || name.includes('garage')) return 'garage';
    if (name.includes('ระเบียง') || name.includes('นอกบ้าน') || name.includes('สวน')) return 'exterior';

    // Default to bedroom for unknown
    return 'bedroom';
}

/**
 * Group rooms by floor
 */
export function groupRoomsByFloor(rooms: GridRoom[]): Map<number, GridRoom[]> {
    const grouped = new Map<number, GridRoom[]>();

    for (const room of rooms) {
        if (!grouped.has(room.floor)) {
            grouped.set(room.floor, []);
        }
        grouped.get(room.floor)!.push(room);
    }

    return grouped;
}

/**
 * Get all unique floors from rooms
 */
export function getFloors(rooms: GridRoom[]): number[] {
    const floors = [...new Set(rooms.map(r => r.floor))];
    return floors.sort((a, b) => b - a); // Descending (floor 2 first)
}
