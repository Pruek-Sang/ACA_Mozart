import { Key, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { testConnection } from '../services/gateway';

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
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="bg-bgSecondary border border-gray-700 rounded-2xl p-8 w-[90%] max-w-md shadow-2xl animate-fadeIn">
                <div className="text-center mb-6">
                    <div className="w-16 h-16 bg-bgInput rounded-full flex items-center justify-center mx-auto mb-4">
                        <Key className="w-8 h-8 text-accentAmadeus" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Authentication Required</h2>
                    <p className="text-textSecondary text-sm">
                        กรุณาใส่ API Key เพื่อเข้าใช้งานระบบ (เก็บในเครื่องของคุณเท่านั้น)
                    </p>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-400 mb-1 ml-1">
                            GATEWAY / GOOGLE API KEY
                        </label>
                        <input
                            type="password"
                            value={key}
                            onChange={(e) => setKey(e.target.value)}
                            className="w-full bg-bgInput border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accentAmadeus transition-colors"
                            placeholder="sk-..."
                        />
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-accentMozart to-accentAmadeus text-white font-bold py-3 rounded-xl hover:opacity-90 transition-opacity shadow-lg shadow-purple-900/30 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>กำลังทดสอบ...</span>
                            </>
                        ) : (
                            <span>ทดสอบ & เข้าสู่ระบบ</span>
                        )}
                    </button>

                    {error && (
                        <p className="text-red-500 text-xs text-center">{error}</p>
                    )}
                    {success && (
                        <p className="text-green-500 text-xs text-center">✅ เชื่อมต่อสำเร็จ!</p>
                    )}
                </div>
            </div>
        </div>
    );
}
