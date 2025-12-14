// src/features/floorplan/layout.logic.ts

/**
 * นี่คือ "สมอง" ของการจัดวาง Floor Plan ทั้งหมด
 * หน้าที่ของมันคือรับรายการห้อง (rooms) เข้ามา แล้วส่งคืนเป็นโครงสร้าง Layout
 * ที่พร้อมให้ Component นำไปวาดเป็นภาพได้ทันที โดยใช้หลัก Zoning & Adjacency
 */

// 1. กำหนดประเภทของโซน
export const RoomZone = {
  PUBLIC: 'PUBLIC',
  SERVICE: 'SERVICE',
  PRIVATE: 'PRIVATE',
  OUTDOOR: 'OUTDOOR',
} as const;

export type RoomZoneType = (typeof RoomZone)[keyof typeof RoomZone];

// **[UPDATED]** Use Tailwind classes instead of Hex codes for better theming
export const ZoneStyles: Record<RoomZoneType, { container: string; text: string; border: string; icon: string }> = {
  [RoomZone.PUBLIC]: {
    container: 'bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30',
    border: 'border-emerald-500/30',
    text: 'text-emerald-100 drop-shadow-md',
    icon: 'text-emerald-300',
  },
  [RoomZone.SERVICE]: {
    container: 'bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30',
    border: 'border-amber-500/30',
    text: 'text-amber-100 drop-shadow-md',
    icon: 'text-amber-300',
  },
  [RoomZone.PRIVATE]: {
    container: 'bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/30',
    border: 'border-rose-500/30',
    text: 'text-rose-100 drop-shadow-md',
    icon: 'text-rose-300',
  },
  [RoomZone.OUTDOOR]: {
    container: 'bg-slate-500/20 hover:bg-slate-500/30 border border-slate-500/30',
    border: 'border-slate-500/30',
    text: 'text-slate-100 drop-shadow-md',
    icon: 'text-slate-300',
  },
};

// 2. Mapping ประเภทห้องจาก Backend ไปยัง Zone ที่เรากำหนด
const roomTypeToZone: Record<string, RoomZoneType> = {
  // Public Zone
  LIVING_ROOM: RoomZone.PUBLIC,
  FOYER: RoomZone.PUBLIC,
  RECEPTION: RoomZone.PUBLIC,
  HALLWAY: RoomZone.PUBLIC,

  // Service Zone
  KITCHEN: RoomZone.SERVICE,
  DINING: RoomZone.SERVICE,
  LAUNDRY: RoomZone.SERVICE,
  STORAGE: RoomZone.SERVICE,
  GARAGE: RoomZone.SERVICE,
  PUMP_ROOM: RoomZone.SERVICE,

  // Private Zone
  BEDROOM: RoomZone.PRIVATE,
  BATHROOM: RoomZone.PRIVATE,
  OFFICE: RoomZone.PRIVATE,
  MASTER_BEDROOM: RoomZone.PRIVATE,
  WALK_IN_CLOSET: RoomZone.PRIVATE,

  // Outdoor Zone
  GARDEN: RoomZone.OUTDOOR,
  TERRACE: RoomZone.OUTDOOR,
  BALCONY: RoomZone.OUTDOOR,
};

// **[NEW]** Load Data Interface
export interface LoadData {
  id: string;
  type: string; // e.g., 'LIGHT', 'OUTLET', 'SWITCH'
  name: string;
}

// 3. Interface สำหรับข้อมูลห้องและ Layout ที่จะส่งออกไป
export interface RoomData {
  id: string;
  name: string;
  room_type: string;
  floor: number;
  loads?: LoadData[]; // **[NEW]** Support loads
}

export interface LayoutRoom extends RoomData {
  zone: RoomZoneType;
  index: number; // For animation stagger
}

// **[NEW]** Wire Connection Interface
export interface WireData {
  id: string;
  fromRoomId: string;
  toRoomId: string;
  zone: RoomZoneType;
}

export interface FloorLayout {
  floor: number;
  rows: LayoutRoom[][];
  wires: WireData[]; // **[NEW]** Connections for visualizer
}

// 4. ฟังก์ชันหลัก: อัลกอริทึมการคำนวณ Layout
export const calculateLayout = (rooms: RoomData[]): FloorLayout[] => {
  if (!rooms || rooms.length === 0) {
    return [];
  }

  // Step 1: แปลงข้อมูลดิบและกำหนด Zone ให้แต่ละห้อง
  const layoutRooms: LayoutRoom[] = rooms.map((room, index) => ({
    ...room,
    zone: roomTypeToZone[room.room_type.toUpperCase()] || RoomZone.PRIVATE,
    index,
  }));

  // Step 2: จัดกลุ่มห้องตาม "ชั้น"
  const roomsByFloor = layoutRooms.reduce<Record<number, LayoutRoom[]>>((acc, room) => {
    (acc[room.floor] = acc[room.floor] || []).push(room);
    return acc;
  }, {});

  // Step 3: สร้าง Layout ของแต่ละชั้น
  const zoneOrder: RoomZoneType[] = [RoomZone.OUTDOOR, RoomZone.PUBLIC, RoomZone.SERVICE, RoomZone.PRIVATE];

  const finalLayouts = Object.keys(roomsByFloor).map(floorStr => {
    const floor = parseInt(floorStr);
    const floorRooms = roomsByFloor[floor];

    // จัดเรียงห้องตาม Zone: OUTDOOR -> PUBLIC -> SERVICE -> PRIVATE
    const sortedRooms = [...floorRooms].sort((a, b) => {
      return zoneOrder.indexOf(a.zone) - zoneOrder.indexOf(b.zone);
    });

    // สร้าง Grid Layout แบบง่ายๆ (วาง 3 ห้องต่อแถว)
    const rows: LayoutRoom[][] = [];
    const roomsPerRow = 3;
    for (let i = 0; i < sortedRooms.length; i += roomsPerRow) {
      rows.push(sortedRooms.slice(i, i + roomsPerRow));
    }

    // **[NEW]** Generate Simple Wiring Connections
    // Connect rooms sequentially within the same zone to simulate a "circuit"
    const wires: WireData[] = [];

    // Group by zone to create intra-zone connections
    const roomsByZone: Record<string, LayoutRoom[]> = {};
    sortedRooms.forEach(room => {
      (roomsByZone[room.zone] = roomsByZone[room.zone] || []).push(room);
    });

    Object.entries(roomsByZone).forEach(([, zoneRooms]) => {
      for (let i = 0; i < zoneRooms.length - 1; i++) {
        wires.push({
          id: `wire-${zoneRooms[i].id}-${zoneRooms[i + 1].id}`,
          fromRoomId: zoneRooms[i].id,
          toRoomId: zoneRooms[i + 1].id,
          zone: zoneRooms[i].zone,
        });
      }
    });

    return { floor, rows, wires };
  });

  // จัดเรียงชั้นจากมากไปน้อย (ชั้น 2 อยู่บน ชั้น 1 อยู่ล่าง)
  return finalLayouts.sort((a, b) => b.floor - a.floor);
};
