// src/features/loadschedule/tableParser.ts
// Parse chat text response into structured table data

export interface LoadRow {
    id: string;
    category: string;
    room: string;
    quantity: number;
    unit: string;
    load: number;
    editable: boolean;
}

export interface LoadScheduleData {
    projectName: string;
    totalLoad: number;
    totalCurrent: number;
    designCurrent: number;
    rows: LoadRow[];
}

/**
 * Parse load schedule text from chat response
 */
export function parseLoadScheduleText(text: string): LoadScheduleData {
    const data: LoadScheduleData = {
        projectName: 'โครงการออกแบบไฟฟ้า',
        totalLoad: 0,
        totalCurrent: 0,
        designCurrent: 0,
        rows: []
    };

    const lines = text.split('\n');
    let currentCategory = '';
    let rowId = 0;

    for (const line of lines) {
        // Parse total load
        const loadMatch = line.match(/โหลดรวม.*?:\s*([\d,]+)\s*W/);
        if (loadMatch) {
            data.totalLoad = Number.parseInt(loadMatch[1].replace(/,/g, ''), 10);
        }

        // Parse current
        const currentMatch = line.match(/กระแส.*?:\s*([\d.]+)\s*A/);
        if (currentMatch) {
            data.totalCurrent = Number.parseFloat(currentMatch[1]);
        }

        // Parse design current
        const designMatch = line.match(/Design Current.*?:\s*([\d.]+)\s*A/);
        if (designMatch) {
            data.designCurrent = Number.parseFloat(designMatch[1]);
        }

        // Detect category (💡 ไฟแสงสว่าง, 🔌 เต้ารับ, ❄️ แอร์, etc.)
        const categoryMatch = line.match(/│\s*\d+\s*│\s*(💡|🔌|❄️|🚿|🔥)\s*(.+?)(?:\s*│|$)/);
        if (categoryMatch) {
            currentCategory = categoryMatch[2].trim();
        }

        // Detect room with quantity (└─ ห้องนั่งเล่น: 5ดวง)
        const roomMatch = line.match(/└─\s*(.+?):\s*(?:คู่×)?(\d+)/);
        if (roomMatch && currentCategory) {
            const roomName = roomMatch[1].trim();
            const quantity = Number.parseInt(roomMatch[2], 10);

            // Determine if editable based on category
            const isEditable = currentCategory.includes('ไฟ') ||
                currentCategory.includes('เต้ารับ') ||
                currentCategory.includes('แอร์');

            // Estimate load per item
            let loadPerItem = 100; // default
            if (currentCategory.includes('ไฟ')) loadPerItem = 100;
            if (currentCategory.includes('เต้ารับ')) loadPerItem = 180;
            if (currentCategory.includes('แอร์')) loadPerItem = 1200;

            data.rows.push({
                id: `row-${rowId++}`,
                category: currentCategory,
                room: roomName,
                quantity,
                unit: currentCategory.includes('ไฟ') ? 'ดวง' :
                    currentCategory.includes('เต้ารับ') ? 'คู่' :
                        currentCategory.includes('แอร์') ? 'BTU' : 'ชุด',
                load: quantity * loadPerItem,
                editable: isEditable
            });
        }
    }

    return data;
}

/**
 * Calculate total load from rows
 */
export function calculateTotalLoad(rows: LoadRow[]): number {
    return rows.reduce((sum, row) => sum + row.load, 0);
}
