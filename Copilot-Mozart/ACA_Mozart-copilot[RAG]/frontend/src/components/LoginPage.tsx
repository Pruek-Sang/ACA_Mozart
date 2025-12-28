import { useState } from 'react';
import { supabase } from '../lib/supabase';
import { cn } from '../lib/utils';
import { LogIn, Mail, Lock, Loader2, AlertCircle } from 'lucide-react';

interface LoginPageProps {
    onLoginSuccess: () => void;
}

/**
 * LoginPage - หน้า Login/Signup
 * 
 * - รองรับ Email + Password
 * - แสดง Error ชัดเจน
 * - Industrial Design Theme
 */
export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'login' | 'signup'>('login');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            if (mode === 'login') {
                // Login
                const { error } = await supabase.auth.signInWithPassword({
                    email,
                    password,
                });
                if (error) throw error;
            } else {
                // Signup
                const { error } = await supabase.auth.signUp({
                    email,
                    password,
                });
                if (error) throw error;
                // แจ้งให้ยืนยัน email
                setError('✅ ลงทะเบียนสำเร็จ! กรุณาตรวจสอบ Email เพื่อยืนยัน');
                setIsLoading(false);
                return;
            }

            onLoginSuccess();
        } catch (err: any) {
            console.error('Auth error:', err);
            setError(err.message || 'เกิดข้อผิดพลาด');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-sky-600 rounded-2xl mb-4">
                        <LogIn size={32} className="text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-white">Mozart Design System</h1>
                    <p className="text-slate-400 text-sm mt-2">ระบบออกแบบไฟฟ้าอัจฉริยะ</p>
                </div>

                {/* Login Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    {/* Mode Toggle */}
                    <div className="flex bg-slate-800 rounded-lg p-1 mb-6">
                        <button
                            type="button"
                            onClick={() => setMode('login')}
                            className={cn(
                                "flex-1 py-2 text-sm font-medium rounded-md transition-colors",
                                mode === 'login'
                                    ? 'bg-sky-600 text-white'
                                    : 'text-slate-400 hover:text-white'
                            )}
                        >
                            เข้าสู่ระบบ
                        </button>
                        <button
                            type="button"
                            onClick={() => setMode('signup')}
                            className={cn(
                                "flex-1 py-2 text-sm font-medium rounded-md transition-colors",
                                mode === 'signup'
                                    ? 'bg-sky-600 text-white'
                                    : 'text-slate-400 hover:text-white'
                            )}
                        >
                            สมัครใหม่
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Email */}
                        <div className="space-y-1">
                            <label className="text-xs text-slate-500 uppercase font-mono tracking-wider">
                                Email
                            </label>
                            <div className="relative">
                                <Mail size={18} className="absolute left-3 top-3 text-slate-500" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="your@email.com"
                                    required
                                    disabled={isLoading}
                                    className={cn(
                                        "w-full bg-slate-950 border border-slate-700 text-white",
                                        "pl-10 pr-4 py-3 rounded-lg",
                                        "focus:border-sky-500 focus:outline-none",
                                        "placeholder-slate-600 font-mono text-sm",
                                        "disabled:opacity-50"
                                    )}
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1">
                            <label className="text-xs text-slate-500 uppercase font-mono tracking-wider">
                                Password
                            </label>
                            <div className="relative">
                                <Lock size={18} className="absolute left-3 top-3 text-slate-500" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                    disabled={isLoading}
                                    className={cn(
                                        "w-full bg-slate-950 border border-slate-700 text-white",
                                        "pl-10 pr-4 py-3 rounded-lg",
                                        "focus:border-sky-500 focus:outline-none",
                                        "placeholder-slate-600 font-mono text-sm",
                                        "disabled:opacity-50"
                                    )}
                                />
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className={cn(
                                "p-3 rounded-lg text-sm flex items-start gap-2",
                                error.startsWith('✅')
                                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                    : 'bg-red-500/10 text-red-400 border border-red-500/30'
                            )}>
                                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className={cn(
                                "w-full bg-sky-600 hover:bg-sky-500 text-white",
                                "py-3 rounded-lg font-medium",
                                "transition-colors flex items-center justify-center gap-2",
                                "disabled:opacity-50 disabled:cursor-not-allowed"
                            )}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 size={18} className="animate-spin" />
                                    กำลังดำเนินการ...
                                </>
                            ) : mode === 'login' ? (
                                'เข้าสู่ระบบ'
                            ) : (
                                'สมัครสมาชิก'
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-600 text-xs mt-6">
                    Powered by Supabase Auth
                </p>
            </div>
        </div>
    );
};
