import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    askDesign,
    startSession,
    listProjects,
    deleteProject,
    startSessionWithName
} from '../src/lib/api';
import * as supabase from '../src/lib/supabase';

// Mock Supabase token getter
vi.mock('../src/lib/supabase', () => ({
    getAccessToken: vi.fn()
}));

// Mock global fetch
const fetchMock = vi.fn();
globalThis.fetch = fetchMock;

describe('API Functions', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        // Default token mock
        (supabase.getAccessToken as any).mockResolvedValue('mock-token-123');
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('askDesign', () => {
        it('should send correct payload and headers', async () => {
            const mockResponse = { answer: 'Designed successfully' };
            fetchMock.mockResolvedValue({
                ok: true,
                json: async () => mockResponse,
                status: 200
            });

            const payload = { query: 'Design a house', language: 'th' as const };
            const result = await askDesign(payload);

            expect(result).toEqual(mockResponse);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/ask'),
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock-token-123',
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify(payload)
                })
            );
        });

        it('should append session_id to URL if provided', async () => {
            fetchMock.mockResolvedValue({
                ok: true,
                json: async () => ({}),
                status: 200
            });

            await askDesign({ query: 'test', language: 'en' }, 'sess-123');

            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('session_id=sess-123'),
                expect.anything()
            );
        });

        it('should throw error on failed response', async () => {
            fetchMock.mockResolvedValue({
                ok: false,
                status: 500,
                json: async () => ({ detail: 'Server Error' })
            });

            await expect(askDesign({ query: 'test', language: 'en' }))
                .rejects.toThrow();
        });
    });

    describe('startSession', () => {
        it('should call correct endpoint', async () => {
            const mockSession = { session_id: 'new-session' };
            fetchMock.mockResolvedValue({
                ok: true,
                json: async () => mockSession,
                status: 200
            });

            const result = await startSession();

            expect(result).toEqual(mockSession);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/session/start'),
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    describe('startSessionWithName', () => {
        it('should include project_name query param', async () => {
            // Mock success
            fetchMock.mockResolvedValue({
                ok: true,
                json: async () => ({ session_id: '123' }),
                status: 200
            });

            await startSessionWithName('My Villa');

            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('project_name=My%20Villa'),
                expect.anything()
            );
        });
    });

    describe('listProjects', () => {
        it('should return project list', async () => {
            const mockProjects = {
                projects: [{ session_id: '1', project_name: 'P1' }],
                storage: 'db'
            };
            fetchMock.mockResolvedValue({
                ok: true,
                json: async () => mockProjects,
                status: 200
            });

            const result = await listProjects();

            expect(result).toEqual(mockProjects);
            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/session/list'),
                expect.objectContaining({ method: 'GET' })
            );
        });
    });

    describe('deleteProject', () => {
        it('should throw if confirmation is missing', async () => {
            await expect(deleteProject('sess-1', 'WRONG'))
                .rejects.toThrow('Deletion requires typing CONFIRM');

            expect(fetchMock).not.toHaveBeenCalled();
        });

        it('should call delete endpoint if confirmed', async () => {
            fetchMock.mockResolvedValue({
                ok: true,
                json: async () => ({ status: 'deleted' }),
                status: 200
            });

            await deleteProject('sess-1', 'CONFIRM');

            expect(fetchMock).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/session/sess-1?confirm=CONFIRM'),
                expect.objectContaining({ method: 'DELETE' })
            );
        });
    });
});
