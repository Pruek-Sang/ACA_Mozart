/**
 * ResultViewer Component Tests
 * 
 * Tests the critical Load Table display component.
 * Focus: Render stability, hooks order (no violations), empty/loading states
 */
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ResultViewer } from '../components/ResultViewer'

describe('ResultViewer', () => {
    // ═══════════════════════════════════════════════════════════════
    // 1. Empty State Tests (No Data)
    // ═══════════════════════════════════════════════════════════════
    describe('Empty State', () => {
        it('renders "NO DATA LOADED" when data is null', () => {
            render(<ResultViewer data={null} isLoading={false} />)
            expect(screen.getByText('NO DATA LOADED')).toBeInTheDocument()
        })

        it('shows instruction text when no data', () => {
            render(<ResultViewer data={null} isLoading={false} />)
            expect(screen.getByText('พิมพ์คำสั่งเพื่อเริ่มออกแบบ')).toBeInTheDocument()
        })
    })

    // ═══════════════════════════════════════════════════════════════
    // 2. Loading State Tests
    // ═══════════════════════════════════════════════════════════════
    describe('Loading State', () => {
        it('shows loading spinner when isLoading is true', () => {
            render(<ResultViewer data={null} isLoading={true} />)
            expect(screen.getByText('CALCULATING...')).toBeInTheDocument()
        })

        it('shows Thai loading text', () => {
            render(<ResultViewer data={null} isLoading={true} />)
            expect(screen.getByText('กำลังคำนวณระบบไฟฟ้า')).toBeInTheDocument()
        })
    })

    // ═══════════════════════════════════════════════════════════════
    // 3. Data Rendering Tests (Compact Table)
    // ═══════════════════════════════════════════════════════════════
    describe('With Data', () => {
        const mockData = {
            success: true,
            message: 'Test data',
            data: {
                loads: [
                    {
                        device_name: 'แอร์ห้องนอน 1',
                        power_kw: 2,
                        breaker_size: 20,
                        wire_size: '2.5 mm²',
                        conduit_size: '1/2"',
                        voltage_drop_percent: 1.2,
                    },
                    {
                        device_name: 'เครื่องทำน้ำอุ่น',
                        power_kw: 5,
                        breaker_size: 32,
                        wire_size: '4.0 mm²',
                        conduit_size: '3/4"',
                        voltage_drop_percent: 2.1,
                    },
                ],
                total_power_kw: 7,
                main_breaker: 63,
                demand_factor: 0.78,
            },
        }

        it('renders tab buttons', () => {
            render(<ResultViewer data={mockData as any} isLoading={false} />)
            expect(screen.getByText('Load Table')).toBeInTheDocument()
            expect(screen.getByText('Audit')).toBeInTheDocument()
            expect(screen.getByText('SLD')).toBeInTheDocument()
            expect(screen.getByText('BOQ')).toBeInTheDocument()
        })

        it('renders download button', () => {
            render(<ResultViewer data={mockData as any} isLoading={false} />)
            expect(screen.getByTitle('Download Excel')).toBeInTheDocument()
        })

        it('renders circuit data in table', () => {
            render(<ResultViewer data={mockData as any} isLoading={false} />)
            expect(screen.getByText('แอร์ห้องนอน 1')).toBeInTheDocument()
            expect(screen.getByText('เครื่องทำน้ำอุ่น')).toBeInTheDocument()
        })
    })

    // ═══════════════════════════════════════════════════════════════
    // 4. Hooks Stability Test (Critical!)
    // This ensures hooks are called in consistent order
    // ═══════════════════════════════════════════════════════════════
    describe('Hooks Stability', () => {
        it('does not crash when switching from loading to data', () => {
            const { rerender } = render(<ResultViewer data={null} isLoading={true} />)
            expect(screen.getByText('CALCULATING...')).toBeInTheDocument()

            // Simulate data arriving
            const mockData = {
                data: {
                    loads: [{ device_name: 'Test', power_kw: 1 }],
                    total_power_kw: 1,
                },
            }

            rerender(<ResultViewer data={mockData as any} isLoading={false} />)
            expect(screen.getByText('Test')).toBeInTheDocument()
        })

        it('does not crash when switching from data to empty', () => {
            const mockData = {
                data: {
                    loads: [{ device_name: 'Test', power_kw: 1 }],
                },
            }

            const { rerender } = render(<ResultViewer data={mockData as any} isLoading={false} />)
            expect(screen.getByText('Test')).toBeInTheDocument()

            rerender(<ResultViewer data={null} isLoading={false} />)
            expect(screen.getByText('NO DATA LOADED')).toBeInTheDocument()
        })
    })
})
