// src/features/loadschedule/LoadScheduleEditor.tsx
// Editable load schedule table with PDF export

import React, { useState, useMemo, useRef } from 'react';
import { Download, Edit3, Check, X } from 'lucide-react';
import { parseLoadScheduleText, calculateTotalLoad } from './tableParser';
import type { LoadRow } from './tableParser';
import './loadschedule.css';

interface LoadScheduleEditorProps {
    chatText: string;
    onClose?: () => void;
}

const LoadScheduleEditor: React.FC<LoadScheduleEditorProps> = ({ chatText, onClose }) => {
    // Parse chat text into structured data
    const initialData = useMemo(() => parseLoadScheduleText(chatText), [chatText]);

    // State for editable rows
    const [rows, setRows] = useState<LoadRow[]>(initialData.rows);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editValue, setEditValue] = useState<string>('');
    const tableRef = useRef<HTMLDivElement>(null);

    // Calculate current totals
    const totalLoad = useMemo(() => calculateTotalLoad(rows), [rows]);
    const totalCurrent = totalLoad / 230;
    const designCurrent = totalCurrent * 1.25;

    // Start editing a cell
    const startEdit = (row: LoadRow) => {
        if (!row.editable) return;
        setEditingId(row.id);
        setEditValue(String(row.quantity));
    };

    // Save edit
    const saveEdit = (rowId: string) => {
        const newQuantity = Number.parseInt(editValue, 10);
        if (Number.isNaN(newQuantity) || newQuantity < 0) {
            setEditingId(null);
            return;
        }

        setRows(prev => prev.map(row => {
            if (row.id === rowId) {
                const loadPerItem = row.load / row.quantity || 100;
                return {
                    ...row,
                    quantity: newQuantity,
                    load: newQuantity * loadPerItem
                };
            }
            return row;
        }));
        setEditingId(null);
    };

    // Cancel edit
    const cancelEdit = () => {
        setEditingId(null);
        setEditValue('');
    };

    // Export to PDF
    const exportToPDF = async () => {
        if (!tableRef.current) return;

        // Dynamic import html2pdf
        const html2pdf = (await import('html2pdf.js')).default;

        const opt = {
            margin: [10, 10, 10, 10],
            filename: `ตารางโหลดไฟฟ้า_${new Date().toLocaleDateString('th-TH')}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: {
                scale: 2,
                useCORS: true,
                letterRendering: true
            },
            jsPDF: {
                unit: 'mm',
                format: 'a4',
                orientation: 'portrait'
            }
        };

        html2pdf().set(opt).from(tableRef.current).save();
    };

    // Empty state
    if (rows.length === 0) {
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
                <h2>📋 ตารางโหลดไฟฟ้า</h2>
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

            {/* Editable hint */}
            <div className="lse-hint">
                <Edit3 size={14} />
                <span>คลิกที่ตัวเลขสีม่วงเพื่อแก้ไข</span>
            </div>

            {/* Table */}
            <div ref={tableRef} className="lse-table-wrapper">
                <div className="lse-print-header">
                    <h1>ตารางคำนวณโหลดไฟฟ้า</h1>
                    <p>วันที่: {new Date().toLocaleDateString('th-TH', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })}</p>
                </div>

                <table className="lse-table">
                    <thead>
                        <tr>
                            <th>ประเภท</th>
                            <th>ห้อง</th>
                            <th>จำนวน</th>
                            <th>หน่วย</th>
                            <th>โหลด (W)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map(row => (
                            <tr key={row.id} className={row.editable ? 'editable-row' : ''}>
                                <td className="category-cell">{row.category}</td>
                                <td>{row.room}</td>
                                <td className="quantity-cell">
                                    {editingId === row.id ? (
                                        <div className="edit-input-wrapper">
                                            <input
                                                type="number"
                                                value={editValue}
                                                onChange={(e) => setEditValue(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') saveEdit(row.id);
                                                    if (e.key === 'Escape') cancelEdit();
                                                }}
                                                autoFocus
                                                min={0}
                                                className="edit-input"
                                            />
                                            <button onClick={() => saveEdit(row.id)} className="save-btn">
                                                <Check size={14} />
                                            </button>
                                            <button onClick={cancelEdit} className="cancel-btn">
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ) : (
                                        <span
                                            className={`quantity-value ${row.editable ? 'editable' : ''}`}
                                            onClick={() => startEdit(row)}
                                            onKeyDown={(e) => e.key === 'Enter' && startEdit(row)}
                                            role={row.editable ? 'button' : undefined}
                                            tabIndex={row.editable ? 0 : undefined}
                                        >
                                            {row.quantity}
                                            {row.editable && <Edit3 size={12} className="edit-icon" />}
                                        </span>
                                    )}
                                </td>
                                <td>{row.unit}</td>
                                <td className="load-cell">{row.load.toLocaleString()}</td>
                            </tr>
                        ))}
                    </tbody>
                    <tfoot>
                        <tr className="total-row">
                            <td colSpan={4}>โหลดรวม (Total Connected Load)</td>
                            <td className="load-cell">{totalLoad.toLocaleString()} W</td>
                        </tr>
                        <tr className="summary-row">
                            <td colSpan={4}>กระแสโหลด (Demand Current)</td>
                            <td className="load-cell">{totalCurrent.toFixed(1)} A</td>
                        </tr>
                        <tr className="summary-row">
                            <td colSpan={4}>Design Current (×1.25)</td>
                            <td className="load-cell">{designCurrent.toFixed(1)} A</td>
                        </tr>
                    </tfoot>
                </table>

                <div className="lse-print-footer">
                    <p>สร้างโดย Mozart AI • ตามมาตรฐาน วสท. 2001-56 และ NEC 2023</p>
                </div>
            </div>
        </div>
    );
};

export default LoadScheduleEditor;
