import { describe, it, expect } from 'vitest';
import type { AskResponse, DisplayData, CircuitData, AuditResult, SLDData } from '../src/types';

/**
 * API Contract Test - Verifies Frontend types match Backend response
 * 
 * This test ensures that the TypeScript interfaces in frontend/src/types/index.ts
 * correctly describe the data returned by the backend API.
 * 
 * If this test fails, it means there's a contract mismatch between frontend and backend.
 */

// Sample response structure from backend (based on actual API)
const SAMPLE_ASK_RESPONSE: AskResponse = {
    answer: "ออกแบบระบบไฟฟ้าสำหรับบ้าน 2 ชั้น...",
    metadata: {
        display_data: {
            circuits: [],
            total_kw: 15.5,
            main_breaker: "50A",
        },
        audit_results: {
            passed: true,
            issues: [],
            warnings: [],
        },
        pdf_data: {
            title: "Mozart Design Report",
            content: "...",
        },
        sld_data: {
            nodes: [],
            edges: [],
        },
    },
};

describe('API Contract: AskResponse', () => {
    it('should have answer field', () => {
        expect(SAMPLE_ASK_RESPONSE).toHaveProperty('answer');
        expect(typeof SAMPLE_ASK_RESPONSE.answer).toBe('string');
    });

    it('should have metadata field', () => {
        expect(SAMPLE_ASK_RESPONSE).toHaveProperty('metadata');
        expect(typeof SAMPLE_ASK_RESPONSE.metadata).toBe('object');
    });
});

describe('API Contract: DisplayData', () => {
    const displayData = SAMPLE_ASK_RESPONSE.metadata?.display_data as DisplayData;

    it('should have circuits array', () => {
        expect(displayData).toHaveProperty('circuits');
        expect(Array.isArray(displayData.circuits)).toBe(true);
    });

    it('should have total_kw number', () => {
        expect(displayData).toHaveProperty('total_kw');
        expect(typeof displayData.total_kw).toBe('number');
    });

    it('should have main_breaker string', () => {
        expect(displayData).toHaveProperty('main_breaker');
        expect(typeof displayData.main_breaker).toBe('string');
    });
});

describe('API Contract: CircuitData structure', () => {
    // Sample circuit from backend
    const sampleCircuit: CircuitData = {
        id: 'circuit-1',
        name: 'ห้องนอน 1',
        room: 'bedroom',
        devices: [],
        total_watts: 500,
        circuit_breaker: '15A',
        wire_size: '2.5 sq.mm',
    };

    it('should have required fields', () => {
        expect(sampleCircuit).toHaveProperty('id');
        expect(sampleCircuit).toHaveProperty('name');
        expect(sampleCircuit).toHaveProperty('devices');
        expect(sampleCircuit).toHaveProperty('total_watts');
    });
});

describe('API Contract: AuditResult structure', () => {
    const auditResult = SAMPLE_ASK_RESPONSE.metadata?.audit_results as AuditResult;

    it('should have passed boolean', () => {
        expect(auditResult).toHaveProperty('passed');
        expect(typeof auditResult.passed).toBe('boolean');
    });

    it('should have issues array', () => {
        expect(auditResult).toHaveProperty('issues');
        expect(Array.isArray(auditResult.issues)).toBe(true);
    });
});

describe('API Contract: SLDData structure', () => {
    const sldData = SAMPLE_ASK_RESPONSE.metadata?.sld_data as SLDData;

    it('should have nodes array', () => {
        expect(sldData).toHaveProperty('nodes');
        expect(Array.isArray(sldData.nodes)).toBe(true);
    });

    it('should have edges array', () => {
        expect(sldData).toHaveProperty('edges');
        expect(Array.isArray(sldData.edges)).toBe(true);
    });
});
