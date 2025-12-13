
// src/features/floorplan/layout.logic.ts

/**
 * นี่คือ "สมอง" ของการจัดวาง Floor Plan ทั้งหมด
 * หน้าที่ของมันคือรับรายการห้อง (rooms) เข้ามา แล้วส่งคืนเป็นโครงสร้าง Layout
 * ที่พร้อมให้ Component นำไปวาดเป็นภาพได้ทันที โดยใช้หลัก Zoning & Adjacency
 */

// 1. กำหนดประเภทของโซนและสี
export enum RoomZone {
  PUBLIC = 'PUBLIC',
  SERVICE = 'SERVICE',
  PRIVATE = 'PRIVATE',
  OUTDOOR = 'OUTDOOR',
}

export const ZoneColors: Record<RoomZone, string> = {
  [RoomZone.PUBLIC]: '#A7F3D0',   // สีเขียว Mint
  [RoomZone.SERVICE]: '#FEF08A',  // สีเหลือง Lemon
  [RoomZone.PRIVATE]: '#FECACA',  // สีแดง Rose
  [RoomZone.OUTDOOR]: '#E5E7EB',  // สีเทา
};

// 2. Mapping ประเภทห้องจาก Backend ไปยัง Zone ที่เรากำหนด
const roomTypeToZone: Record<string, RoomZone> = {
  // Public Zone
  LIVING_ROOM: RoomZone.PUBLIC,
  FOYER: RoomZone.PUBLIC,
  RECEPTION: RoomZone.PUBLIC,

  // Service Zone
  KITCHEN: RoomZone.SERVICE,
  DINING: RoomZone.SERVICE,
  LAUNDRY: RoomZone.SERVICE,

  // Private Zone
  BEDROOM: RoomZone.PRIVATE,
  BATHROOM: RoomZone.PRIVATE,
  OFFICE: RoomZone.PRIVATE,
  MASTER_BEDROOM: RoomZone.PRIVATE,

  // Outdoor Zone
  GARAGE: RoomZone.OUTDOOR,
  PUMP_ROOM: RoomZone.OUTDOOR,
  GARDEN: RoomZone.OUTDOOR,
};

// 3. Interface สำหรับข้อมูลห้องและ Layout ที่จะส่งออกไป
export interface RoomData {
  id: string;
  name: string;
  room_type: string;
  floor: number;
}

export interface LayoutRoom extends RoomData {
  zone: RoomZone;
}

export interface FloorLayout {
  floor: number;
  // Layout จะเป็น Array ของ Array (Grid) เพื่อให้วาดง่าย
  // เช่น [[Room1, Room2], [Room3]]
  rows: LayoutRoom[][];
}

// 4. ฟังก์ชันหลัก: อัลกอริทึมการคำนวณ Layout
export const calculateLayout = (rooms: RoomData[]): FloorLayout[] => {
  if (!rooms || rooms.length === 0) {
    return [];
  }

  // Step 1: แปลงข้อมูลดิบและกำหนด Zone ให้แต่ละห้อง
  const layoutRooms: LayoutRoom[] = rooms.map(room => ({
    ...room,
    zone: roomTypeToZone[room.room_type.toUpperCase()] || RoomZone.PRIVATE,
  }));

  // Step 2: จัดกลุ่มห้องตาม "ชั้น"
  const roomsByFloor = layoutRooms.reduce<Record<number, LayoutRoom[]>>((acc, room) => {
    (acc[room.floor] = acc[room.floor] || []).push(room);
    return acc;
  }, {});

  // Step 3: สร้าง Layout ของแต่ละชั้น
  const finalLayouts = Object.keys(roomsByFloor).map(floorStr => {
    const floor = parseInt(floorStr);
    const floorRooms = roomsByFloor[floor];

    // จัดเรียงห้องตาม Zone: OUTDOOR -> PUBLIC -> SERVICE -> PRIVATE
    const sortedRooms = [...floorRooms].sort((a, b) => {
      const zoneOrder = [RoomZone.OUTDOOR, RoomZone.PUBLIC, RoomZone.SERVICE, RoomZone.PRIVATE];
      return zoneOrder.indexOf(a.zone) - zoneOrder.indexOf(b.zone);
    });

    // สร้าง Grid Layout แบบง่ายๆ (วาง 3 ห้องต่อแถว)
    const rows: LayoutRoom[][] = [];
    for (let i = 0; i < sortedRooms.length; i += 3) {
      rows.push(sortedRooms.slice(i, i + 3));
    }
    
    return { floor, rows };
  });

  // จัดเรียงชั้นจากมากไปน้อย (ชั้น 2 อยู่บน ชั้น 1 อยู่ล่าง)
  return finalLayouts.sort((a, b) => b.floor - a.floor);
};

