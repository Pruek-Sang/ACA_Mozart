// src/features/loadschedule/LoadScheduleEditor.tsx
// Professional Load Schedule Editor with PDF export (matches วิศวกรไฟฟ้า format)

import React, { useMemo, useRef } from 'react';
import { Download, X } from 'lucide-react';
import { parseLoadScheduleText, type LoadScheduleData } from './tableParser';
import './loadschedule.css';

interface LoadScheduleEditorProps {
    chatText: string;
    onClose?: () => void;
}

const LoadScheduleEditor: React.FC<LoadScheduleEditorProps> = ({ chatText, onClose }) => {
    // Parse chat text into structured data
    const data: LoadScheduleData = useMemo(() => parseLoadScheduleText(chatText), [chatText]);
    const tableRef = useRef<HTMLDivElement>(null);

    // Export to PDF
    const exportToPDF = async () => {
        if (!tableRef.current) return;

        // Dynamic import html2pdf
        const html2pdf = (await import('html2pdf.js')).default;

        const opt = {
            margin: [10, 5, 10, 5] as [number, number, number, number],
            filename: `LoadSchedule_${new Date().toLocaleDateString('th-TH')}.pdf`,
            image: { type: 'jpeg' as const, quality: 0.98 },
            html2canvas: {
                scale: 2,
                useCORS: true,
                letterRendering: true
            },
            jsPDF: {
                unit: 'mm' as const,
                format: 'a4' as const,
                orientation: 'landscape' as const  // Landscape for wide table
            }
        };

        html2pdf().set(opt).from(tableRef.current).save();
    };

    // Empty state
    if (data.floors.length === 0) {
        return (
            <div className="load-schedule-empty">
                <p>ไม่พบข้อมูลตารางโหลด</p>
                <p className="text-sm text-gray-500">ส่งข้อความออกแบบบ้านก่อนเพื่อดูตาราง</p>
            </div>
        );
    }

    return (
        <div className="load-schedule-editor">
            {/* Header */}
            <div className="lse-header">
                <h2>📋 ตารางโหลดไฟฟ้า (Load Schedule)</h2>
                <div className="lse-actions">
                    <button onClick={exportToPDF} className="lse-export-btn">
                        <Download size={16} />
                        ดาวน์โหลด PDF
                    </button>
                    {onClose && (
                        <button onClick={onClose} className="lse-close-btn">
                            <X size={16} />
                        </button>
                    )}
                </div>
            </div>

            {/* PDF Content */}
            <div ref={tableRef} className="lse-pdf-content">
                {/* Print Header */}
                <div className="lse-print-header">
                    <h1>ตารางโหลดไฟฟ้า (LOAD SCHEDULE)</h1>
                    <p>วันที่: {new Date().toLocaleDateString('th-TH', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })}</p>
                </div>

                {/* Panel Info Header */}
                <table className="lse-panel-info">
                    <tbody>
                        <tr>
                            <td className="label">PANEL NAME</td>
                            <td className="value">MDB-1</td>
                            <td className="label">MAIN BUS CAPACITY</td>
                            <td className="value">{data.mainBreaker || '100A'}</td>
                            <td className="label">SYSTEM</td>
                            <td className="value">1Φ 230V 50Hz</td>
                        </tr>
                        <tr>
                            <td className="label">LOCATION</td>
                            <td className="value">ตู้เมน</td>
                            <td className="label">มิเตอร์</td>
                            <td className="value">{data.meterSize || '30(100)A'}</td>
                            <td className="label">สายเมน</td>
                            <td className="value">{data.mainWire || 'THW 25mm²'}</td>
                        </tr>
                    </tbody>
                </table>

                {/* Main Circuit Table */}
                <table className="lse-circuit-table">
                    <thead>
                        <tr className="header-main">
                            <th rowSpan={2}>CCT.</th>
                            <th rowSpan={2}>DESCRIPTION</th>
                            <th colSpan={3} className="group-header">CONNECTION LOAD (VA)</th>
                            <th colSpan={5} className="group-header">CIRCUIT BREAKER</th>
                            <th colSpan={2} className="group-header">WIRE (mm²)</th>
                            <th rowSpan={2}>VD%</th>
                            <th rowSpan={2}>REMARK</th>
                        </tr>
                        <tr className="header-sub">
                            <th>L1</th>
                            <th>L2</th>
                            <th>L3</th>
                            <th>TYPE</th>
                            <th>POLE</th>
                            <th>Ic(kA)</th>
                            <th>AF</th>
                            <th>AT</th>
                            <th>L/N</th>
                            <th>GRD</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.floors.map((floor) => (
                            <React.Fragment key={floor.name}>
                                {/* Floor Header */}
                                <tr className="floor-header">
                                    <td colSpan={14}>{floor.name} (รวม {floor.totalWatts.toLocaleString()} W)</td>
                                </tr>
                                {/* Circuits */}
                                {floor.circuits.map((circuit) => {
                                    const watts = circuit.kW * 1000;
                                    const breakerParts = circuit.breaker.match(/(\w+)\s*(\d+)A[\/]?(\d+)?P?/i);
                                    const breakerType = breakerParts?.[1] || 'MCB';
                                    const breakerAt = breakerParts?.[2] || '';
                                    const breakerPoles = breakerParts?.[3] || '1';
                                    const wireMatch = circuit.wireSize.match(/([\d\.]+)/);
                                    const wireSize = wireMatch?.[1] || '2.5';

                                    return (
                                        <tr key={circuit.id} className={circuit.notes.includes('RCBO') ? 'highlight-row' : ''}>
                                            <td className="center">{circuit.circuitNum}</td>
                                            <td className="description">{circuit.circuitName}</td>
                                            <td className="va-cell">{watts}</td>
                                            <td className="va-cell">-</td>
                                            <td className="va-cell">-</td>
                                            <td className="center">{breakerType}</td>
                                            <td className="center">{breakerPoles}P</td>
                                            <td className="center">6</td>
                                            <td className="center">{breakerAt}</td>
                                            <td className="center">{breakerAt}</td>
                                            <td className="center">{wireSize}</td>
                                            <td className="center">{parseFloat(wireSize) >= 4 ? '4' : '2.5'}</td>
                                            <td className="center vd-cell">{circuit.vdPercent.toFixed(1)}</td>
                                            <td className="notes">{circuit.notes}</td>
                                        </tr>
                                    );
                                })}
                            </React.Fragment>
                        ))}
                    </tbody>
                    <tfoot>
                        <tr className="total-row">
                            <td colSpan={2} className="total-label">TOTAL LOAD (VA)</td>
                            <td className="va-cell total">{data.totalLoad.toLocaleString()}</td>
                            <td className="va-cell">-</td>
                            <td className="va-cell">-</td>
                            <td colSpan={9}></td>
                        </tr>
                        <tr className="summary-row">
                            <td colSpan={2}>DEMAND CURRENT</td>
                            <td colSpan={3}>{data.totalCurrent.toFixed(1)} A</td>
                            <td colSpan={9}></td>
                        </tr>
                        <tr className="summary-row">
                            <td colSpan={2}>DESIGN CURRENT (×1.25)</td>
                            <td colSpan={3}>{data.designCurrent.toFixed(1)} A</td>
                            <td colSpan={9}></td>
                        </tr>
                    </tfoot>
                </table>

                {/* Breaker Summary */}
                {data.breakerSummary.length > 0 && (
                    <div className="lse-breaker-summary">
                        <h3>สรุปเบรกเกอร์</h3>
                        <table className="lse-summary-table">
                            <thead>
                                <tr>
                                    <th>ขนาด</th>
                                    <th>จำนวน</th>
                                    <th>วงจร</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.breakerSummary.map((row, idx) => (
                                    <tr key={idx}>
                                        <td>{row.size}</td>
                                        <td className="center">{row.count}</td>
                                        <td>{row.circuits}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Warnings */}
                {data.warnings.length > 0 && (
                    <div className="lse-warnings">
                        <h3>⚠️ คำเตือนจากระบบ</h3>
                        <ul>
                            {data.warnings.map((warning, idx) => (
                                <li key={idx}>{warning}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Footer */}
                <div className="lse-print-footer">
                    <p>สร้างโดย Mozart AI • ตามมาตรฐาน วสท. 2001-56 และ NEC 2023</p>
                </div>
            </div>
        </div>
    );
};

export default LoadScheduleEditor;
