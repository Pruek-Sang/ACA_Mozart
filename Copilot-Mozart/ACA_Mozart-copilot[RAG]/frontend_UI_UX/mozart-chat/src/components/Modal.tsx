// src/components/Modal.tsx
// Generic modal component for popups

import React from 'react';
import { X } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    maxWidth?: string;
}

export function Modal({ isOpen, onClose, title, children, maxWidth = '900px' }: ModalProps) {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content"
                style={{ maxWidth }}
                onClick={(e) => e.stopPropagation()}
            >
                {title && (
                    <div className="modal-header">
                        <h2>{title}</h2>
                        <button onClick={onClose} className="modal-close-btn">
                            <X size={20} />
                        </button>
                    </div>
                )}
                <div className="modal-body">
                    {children}
                </div>
            </div>
        </div>
    );
}

export default Modal;
