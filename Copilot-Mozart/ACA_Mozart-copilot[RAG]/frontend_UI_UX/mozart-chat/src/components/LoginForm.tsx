// Login Form Component - สำหรับ Login/Register
// ใช้ Supabase Auth โดยตรง - ไม่ใช้ mock

import React, { useState } from 'react'
import { useAuthContext } from '../contexts/AuthContext'

interface LoginFormProps {
    onSuccess?: () => void
}

export function LoginForm({ onSuccess }: LoginFormProps) {
    const { signIn, signUp, loading, error, clearError } = useAuthContext()
    const [isRegister, setIsRegister] = useState(false)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [fullName, setFullName] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        clearError()

        let success: boolean
        if (isRegister) {
            success = await signUp(email, password, fullName)
        } else {
            success = await signIn(email, password)
        }

        if (success && onSuccess) {
            onSuccess()
        }
    }

    const toggleMode = () => {
        setIsRegister(!isRegister)
        clearError()
    }

    return (
        <div className="login-form-container">
            <form onSubmit={handleSubmit} className="login-form">
                <h2 className="login-title">
                    {isRegister ? 'สร้างบัญชีใหม่' : 'เข้าสู่ระบบ'}
                </h2>

                {error && (
                    <div className="login-error">
                        {error}
                    </div>
                )}

                {isRegister && (
                    <div className="form-group">
                        <label htmlFor="fullName">ชื่อ-นามสกุล</label>
                        <input
                            id="fullName"
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="กรอกชื่อ-นามสกุล"
                            className="form-input"
                        />
                    </div>
                )}

                <div className="form-group">
                    <label htmlFor="email">อีเมล</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="email@example.com"
                        required
                        className="form-input"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">รหัสผ่าน</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="อย่างน้อย 6 ตัวอักษร"
                        required
                        minLength={6}
                        className="form-input"
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="login-button"
                >
                    {loading ? 'กำลังดำเนินการ...' : isRegister ? 'สร้างบัญชี' : 'เข้าสู่ระบบ'}
                </button>

                <p className="toggle-mode">
                    {isRegister ? 'มีบัญชีอยู่แล้ว?' : 'ยังไม่มีบัญชี?'}
                    <button type="button" onClick={toggleMode} className="toggle-button">
                        {isRegister ? 'เข้าสู่ระบบ' : 'สร้างบัญชีใหม่'}
                    </button>
                </p>
            </form>

            <style>{`
        .login-form-container {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100%;
          padding: 20px;
        }
        
        .login-form {
          background: rgba(30, 30, 40, 0.9);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 32px;
          width: 100%;
          max-width: 400px;
          backdrop-filter: blur(20px);
        }
        
        .login-title {
          font-size: 24px;
          font-weight: 600;
          color: #fff;
          margin-bottom: 24px;
          text-align: center;
        }
        
        .login-error {
          background: rgba(220, 38, 38, 0.2);
          border: 1px solid rgba(220, 38, 38, 0.5);
          color: #fca5a5;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 16px;
          font-size: 14px;
        }
        
        .form-group {
          margin-bottom: 16px;
        }
        
        .form-group label {
          display: block;
          color: #aaa;
          font-size: 14px;
          margin-bottom: 6px;
        }
        
        .form-input {
          width: 100%;
          padding: 12px 16px;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #fff;
          font-size: 16px;
          outline: none;
          transition: border-color 0.2s;
        }
        
        .form-input:focus {
          border-color: #6366f1;
        }
        
        .form-input::placeholder {
          color: #666;
        }
        
        .login-button {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: opacity 0.2s, transform 0.2s;
          margin-top: 8px;
        }
        
        .login-button:hover:not(:disabled) {
          opacity: 0.9;
          transform: translateY(-1px);
        }
        
        .login-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .toggle-mode {
          text-align: center;
          color: #888;
          font-size: 14px;
          margin-top: 20px;
        }
        
        .toggle-button {
          background: none;
          border: none;
          color: #6366f1;
          cursor: pointer;
          margin-left: 4px;
          font-size: 14px;
        }
        
        .toggle-button:hover {
          text-decoration: underline;
        }
      `}</style>
        </div>
    )
}
