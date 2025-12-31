import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

/**
 * ErrorBoundary - Catches React render errors
 * 
 * Prevents entire app from crashing on render error
 * Shows user-friendly error message instead of blank screen
 */
export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('🔴 React Error Boundary caught:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            // Custom fallback UI
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Default error UI
            return (
                <div className="h-full flex items-center justify-center bg-slate-950 p-8">
                    <div className="text-center max-w-md">
                        <div className="text-6xl mb-4">⚠️</div>
                        <h2 className="text-xl font-bold text-red-400 mb-2">
                            เกิดข้อผิดพลาดในการแสดงผล
                        </h2>
                        <p className="text-slate-400 text-sm mb-4">
                            {this.state.error?.message || 'Unknown error'}
                        </p>
                        <button
                            onClick={() => globalThis.location.reload()}
                            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg transition-colors"
                        >
                            🔄 รีเฟรชหน้า
                        </button>
                        <p className="text-slate-600 text-xs mt-4">
                            หากปัญหายังคงอยู่ กรุณาแจ้งทีมพัฒนา
                        </p>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
