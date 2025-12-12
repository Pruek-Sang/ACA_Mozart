import { Loader2 } from 'lucide-react';
import { useState } from 'react';
import { testConnection } from '../services/gateway';

// ===== MOCK MODE: Set to true to bypass real API key validation =====
const MOCK_MODE = true;

interface ApiKeyModalProps {
    visible: boolean;
    onSave: (key: string) => void;
    initialKey?: string;
}

export function ApiKeyModal({ visible, onSave, initialKey = '' }: ApiKeyModalProps) {
    const [key, setKey] = useState(initialKey);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    if (!visible) return null;

    const handleSave = async () => {
        // ===== MOCK MODE: Skip API validation =====
        if (MOCK_MODE) {
            setSuccess(true);
            setTimeout(() => {
                onSave('mock-api-key');
            }, 500);
            return;
        }

        if (!key.trim()) {
            setError('กรุณากรอก API Key ก่อนดำเนินการต่อ');
            return;
        }

        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            const isConnected = await testConnection(key);

            if (isConnected) {
                setSuccess(true);
                setTimeout(() => {
                    onSave(key);
                }, 800);
            } else {
                setError('❌ ไม่สามารถเชื่อมต่อ Gateway ได้');
            }
        } catch {
            setError('❌ เกิดข้อผิดพลาดในการเชื่อมต่อ');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Container - 2x larger */}
            <div className="w-[95%] max-w-2xl animate-fadeIn">

                {/* ===== GLOSSY AUTH BOX (Fixed: White text visible) ===== */}
                <div
                    className="mb-8 p-10 rounded-3xl text-center relative overflow-hidden"
                    style={{
                        background: '#000000',
                        border: '2px solid #444',
                        boxShadow: `
              0 8px 60px rgba(0, 0, 0, 0.9),
              inset 0 2px 0 rgba(255, 255, 255, 0.15),
              inset 0 -2px 0 rgba(0, 0, 0, 0.5)
            `,
                    }}
                >
                    {/* Glossy shine effect */}
                    <div
                        className="absolute top-0 left-0 right-0 h-1/2 pointer-events-none"
                        style={{
                            background: 'linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 100%)',
                        }}
                    />
                    <h2
                        className="text-4xl font-bold tracking-wide relative z-10"
                        style={{ color: '#FFFFFF' }}
                    >
                        Authentication Required
                    </h2>
                </div>

                {/* ===== INPUT SECTION - 2x larger ===== */}
                <div className="space-y-6">
                    <div>
                        <label
                            htmlFor="api-key-input"
                            className="block text-sm font-medium text-gray-500 mb-3 ml-2 uppercase tracking-wider"
                        >
                            Gateway / Google API Key {MOCK_MODE && <span className="text-yellow-500">(MOCK MODE)</span>}
                        </label>
                        <input
                            id="api-key-input"
                            type="password"
                            value={key}
                            onChange={(e) => setKey(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                            className="w-full bg-black/70 border-2 border-gray-600 rounded-2xl px-6 py-5 text-white text-xl focus:outline-none focus:border-purple-500 transition-colors placeholder-gray-600"
                            placeholder={MOCK_MODE ? "(กด Enter หรือคลิกปุ่มด้านล่างเพื่อเข้าใช้งาน)" : "sk-..."}
                            autoFocus
                            disabled={MOCK_MODE}
                        />
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold py-5 rounded-2xl hover:opacity-90 transition-all shadow-lg shadow-purple-900/40 flex items-center justify-center gap-3 disabled:opacity-50 text-xl"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-6 h-6 animate-spin" />
                                <span>กำลังเชื่อมต่อ...</span>
                            </>
                        ) : MOCK_MODE ? (
                            <span>🔓 เข้าสู่ระบบ (Mock Mode)</span>
                        ) : (
                            <span>กรุณาใส่ API Key</span>
                        )}
                    </button>

                    {error && (
                        <p className="text-red-400 text-base text-center bg-red-900/20 py-3 rounded-xl">{error}</p>
                    )}
                    {success && (
                        <p className="text-green-400 text-base text-center bg-green-900/20 py-3 rounded-xl">✅ เชื่อมต่อสำเร็จ!</p>
                    )}
                </div>
            </div>
        </div>
    );
}
