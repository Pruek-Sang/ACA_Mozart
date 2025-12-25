// src/features/loadschedule/tableParser.ts
// Parse NEW Markdown table format from Mozart RAG response

export interface CircuitRow {
    id: string;
    circuitNum: number;
    circuitName: string;
    loads: string;
    kW: number;
    current: number;
    wireSize: string;
    breaker: string;
    vdPercent: number;
    notes: string;
    floor: string;
}

export interface LoadScheduleData {
    projectName: string;
    totalLoad: number;           // W
    totalCurrent: number;        // A
    designCurrent: number;       // A (×1.25)
    meterSize: string;
    mainWire: string;
    mainBreaker: string;
    floors: FloorData[];
    breakerSummary: BreakerSummaryRow[];
    warnings: string[];
}

export interface FloorData {
    name: string;
    totalWatts: number;
    circuits: CircuitRow[];
}

export interface BreakerSummaryRow {
    size: string;
    count: number;
    circuits: string;
}

/**
 * Parse NEW Markdown format from Mozart RAG response
 * 
 * Expected format:
 * | # | วงจร | โหลด | kW | A | สาย | CB | VD% | หมายเหตุ |
 * |:-:|------|------|----:|---:|-----|-----|----:|----------|
 * | 1 | HEATER-4500W in ห้องน้ำ | | 4.50 | 19.6 | 2.5mm² | MCB 25A/2P | 2.0 | ต้องใช้ RCBO |
 */
export function parseLoadScheduleText(text: string): LoadScheduleData {
    const data: LoadScheduleData = {
        projectName: 'โครงการออกแบบไฟฟ้า',
        totalLoad: 0,
        totalCurrent: 0,
        designCurrent: 0,
        meterSize: '',
        mainWire: '',
        mainBreaker: '',
        floors: [],
        breakerSummary: [],
        warnings: []
    };

    const lines = text.split('\n');
    let currentFloor: FloorData | null = null;
    let circuitId = 0;

    for (const line of lines) {
        // Parse summary info
        const loadMatch = line.match(/โหลดรวม[^|]*?[\|\：\:]?\s*([\d,\.]+)\s*(?:W|kW)/i);
        if (loadMatch) {
            let val = parseFloat(loadMatch[1].replace(/,/g, ''));
            if (line.toLowerCase().includes('kw')) val *= 1000;
            data.totalLoad = val;
        }

        const currentMatch = line.match(/กระแส(?:รวม)?[^|]*?[\|\：\:]?\s*([\d\.]+)\s*A/i);
        if (currentMatch) {
            data.totalCurrent = parseFloat(currentMatch[1]);
        }

        const designMatch = line.match(/Design Current[^|]*?[\|\：\:]?\s*([\d\.]+)\s*A/i);
        if (designMatch) {
            data.designCurrent = parseFloat(designMatch[1]);
        }

        const meterMatch = line.match(/มิเตอร์[^|]*?[\|\：\:]?\s*\*?\*?([^\*\|]+)\*?\*?/i);
        if (meterMatch) {
            data.meterSize = meterMatch[1].trim();
        }

        const wireMatch = line.match(/สายเมน[^|]*?[\|\：\:]?\s*\*?\*?([^\*\|]+)\*?\*?/i);
        if (wireMatch) {
            data.mainWire = wireMatch[1].trim();
        }

        const breakerMatch = line.match(/Main Breaker[^|]*?[\|\：\:]?\s*\*?\*?([^\*\|]+)\*?\*?/i);
        if (breakerMatch) {
            data.mainBreaker = breakerMatch[1].trim();
        }

        // Detect floor header: ### ชั้น 1 (รวม X W) or ### ชั้น 2
        const floorMatch = line.match(/^###\s*(ชั้น\s*\d+)[^\(]*(?:\(รวม\s*([\d,\.]+)\s*W\))?/i);
        if (floorMatch) {
            if (currentFloor && currentFloor.circuits.length > 0) {
                data.floors.push(currentFloor);
            }
            currentFloor = {
                name: floorMatch[1].trim(),
                totalWatts: floorMatch[2] ? parseFloat(floorMatch[2].replace(/,/g, '')) : 0,
                circuits: []
            };
            continue;
        }

        // Parse circuit table row: | 1 | HEATER-4500W in ห้องน้ำ | | 3.00 | 13.1 | 2.5mm² | MCB 20A/2P | 2.0 | notes |
        const circuitMatch = line.match(/^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*([\d\.]+)\s*\|\s*(.*?)\s*\|$/);
        if (circuitMatch && currentFloor) {
            currentFloor.circuits.push({
                id: `circuit-${circuitId++}`,
                circuitNum: parseInt(circuitMatch[1]),
                circuitName: circuitMatch[2].trim(),
                loads: circuitMatch[3].trim(),
                kW: parseFloat(circuitMatch[4]),
                current: parseFloat(circuitMatch[5]),
                wireSize: circuitMatch[6].trim(),
                breaker: circuitMatch[7].trim(),
                vdPercent: parseFloat(circuitMatch[8]),
                notes: circuitMatch[9].trim(),
                floor: currentFloor.name
            });
            continue;
        }

        // Parse breaker summary: | 15A/1P | 2 | ไฟแสงสว่าง ชั้น 1, ชั้น 2 |
        const breakerSummaryMatch = line.match(/^\|\s*(\d+A\/\d+P)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|$/);
        if (breakerSummaryMatch) {
            data.breakerSummary.push({
                size: breakerSummaryMatch[1],
                count: parseInt(breakerSummaryMatch[2]),
                circuits: breakerSummaryMatch[3].trim()
            });
            continue;
        }

        // Parse warnings (⚠️ lines)
        if (line.includes('⚠️') && !line.startsWith('|')) {
            const warningText = line.replace(/^[-\*]\s*/, '').trim();
            if (warningText) {
                data.warnings.push(warningText);
            }
        }
    }

    // Push last floor
    if (currentFloor && currentFloor.circuits.length > 0) {
        data.floors.push(currentFloor);
    }

    // Calculate totals from circuits if not found in summary
    if (data.totalLoad === 0 && data.floors.length > 0) {
        data.totalLoad = data.floors.reduce((sum, f) =>
            sum + f.circuits.reduce((s, c) => s + c.kW * 1000, 0), 0);
    }
    if (data.totalCurrent === 0 && data.totalLoad > 0) {
        data.totalCurrent = data.totalLoad / 230;
    }
    if (data.designCurrent === 0 && data.totalCurrent > 0) {
        data.designCurrent = data.totalCurrent * 1.25;
    }

    return data;
}

/**
 * Calculate total load from floors
 */
export function calculateTotalLoad(floors: FloorData[]): number {
    return floors.reduce((sum, floor) =>
        sum + floor.circuits.reduce((s, c) => s + c.kW * 1000, 0), 0);
}

/**
 * Legacy function for backwards compatibility
 */
export interface LoadRow {
    id: string;
    category: string;
    room: string;
    quantity: number;
    unit: string;
    load: number;
    editable: boolean;
}

export function parseLoadScheduleLegacy(text: string): { rows: LoadRow[] } {
    const data = parseLoadScheduleText(text);
    const rows: LoadRow[] = [];

    for (const floor of data.floors) {
        for (const circuit of floor.circuits) {
            rows.push({
                id: circuit.id,
                category: circuit.circuitName,
                room: floor.name,
                quantity: 1,
                unit: 'วงจร',
                load: circuit.kW * 1000,
                editable: false
            });
        }
    }

    return { rows };
}
