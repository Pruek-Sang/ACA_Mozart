// src/components/EditableValue.tsx
// Inline editable value component for chat messages

import React, { useState, useRef, useEffect } from 'react';

interface EditableValueProps {
    value: string | number;
    type: 'number' | 'text';
    suffix?: string; // e.g., "ดวง", "BTU", "คู่"
    editable?: boolean;
    onChange?: (newValue: string | number) => void;
    min?: number;
    max?: number;
}

const EditableValue: React.FC<EditableValueProps> = ({
    value,
    type,
    suffix = '',
    editable = true,
    onChange,
    min = 0,
    max = 999
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(String(value));
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    const handleClick = () => {
        if (editable) {
            setIsEditing(true);
            setEditValue(String(value));
        }
    };

    const handleBlur = () => {
        setIsEditing(false);
        if (type === 'number') {
            const numValue = Number.parseInt(editValue, 10);
            if (!Number.isNaN(numValue) && numValue >= min && numValue <= max) {
                onChange?.(numValue);
            }
        } else {
            onChange?.(editValue);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleBlur();
        }
        if (e.key === 'Escape') {
            setIsEditing(false);
            setEditValue(String(value));
        }
    };

    if (isEditing) {
        return (
            <span className="editable-value editing">
                <input
                    ref={inputRef}
                    type={type}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={handleBlur}
                    onKeyDown={handleKeyDown}
                    className="editable-input"
                    min={min}
                    max={max}
                />
                {suffix && <span className="editable-suffix">{suffix}</span>}
            </span>
        );
    }

    return (
        <span
            className={`editable-value ${editable ? 'clickable' : 'readonly'}`}
            onClick={handleClick}
            onKeyDown={(e) => e.key === 'Enter' && handleClick()}
            role={editable ? 'button' : undefined}
            tabIndex={editable ? 0 : undefined}
            title={editable ? 'คลิกเพื่อแก้ไข' : 'ไม่สามารถแก้ไขได้'}
        >
            <span className="editable-display">{value}</span>
            {suffix && <span className="editable-suffix">{suffix}</span>}
            {editable && <span className="edit-icon">✏️</span>}
        </span>
    );
};

export default EditableValue;
