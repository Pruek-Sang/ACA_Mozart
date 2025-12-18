// Auth Hook - จัดการ Login/Register/Logout กับ Supabase
// ไม่มี mock - ทำงานจริงทั้งหมด

import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import type { User, Session } from '@supabase/supabase-js'

interface AuthState {
    user: User | null
    session: Session | null
    loading: boolean
    error: string | null
}

interface UseAuthReturn extends AuthState {
    signIn: (email: string, password: string) => Promise<boolean>
    signUp: (email: string, password: string, fullName?: string) => Promise<boolean>
    signOut: () => Promise<void>
    clearError: () => void
}

export function useAuth(): UseAuthReturn {
    const [state, setState] = useState<AuthState>({
        user: null,
        session: null,
        loading: true,
        error: null,
    })

    // ตรวจสอบ session เมื่อ mount
    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setState(prev => ({
                ...prev,
                session,
                user: session?.user ?? null,
                loading: false,
            }))
        })

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                setState(prev => ({
                    ...prev,
                    session,
                    user: session?.user ?? null,
                    loading: false,
                }))
            }
        )

        return () => subscription.unsubscribe()
    }, [])

    // Login
    const signIn = useCallback(async (email: string, password: string): Promise<boolean> => {
        setState(prev => ({ ...prev, loading: true, error: null }))

        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password,
            })

            if (error) {
                setState(prev => ({ ...prev, loading: false, error: error.message }))
                return false
            }

            setState(prev => ({
                ...prev,
                user: data.user,
                session: data.session,
                loading: false,
                error: null,
            }))
            return true
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Login failed'
            setState(prev => ({ ...prev, loading: false, error: message }))
            return false
        }
    }, [])

    // Register
    const signUp = useCallback(async (
        email: string,
        password: string,
        fullName?: string
    ): Promise<boolean> => {
        setState(prev => ({ ...prev, loading: true, error: null }))

        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        full_name: fullName || '',
                    },
                },
            })

            if (error) {
                setState(prev => ({ ...prev, loading: false, error: error.message }))
                return false
            }

            // Note: Supabase อาจต้อง confirm email ก่อน
            if (data.user && !data.session) {
                setState(prev => ({
                    ...prev,
                    loading: false,
                    error: 'กรุณายืนยัน email ก่อน login'
                }))
                return true // สมัครสำเร็จแต่ต้อง confirm
            }

            setState(prev => ({
                ...prev,
                user: data.user,
                session: data.session,
                loading: false,
                error: null,
            }))
            return true
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Registration failed'
            setState(prev => ({ ...prev, loading: false, error: message }))
            return false
        }
    }, [])

    // Logout
    const signOut = useCallback(async () => {
        setState(prev => ({ ...prev, loading: true }))
        await supabase.auth.signOut()
        setState({
            user: null,
            session: null,
            loading: false,
            error: null,
        })
    }, [])

    // Clear error
    const clearError = useCallback(() => {
        setState(prev => ({ ...prev, error: null }))
    }, [])

    return {
        ...state,
        signIn,
        signUp,
        signOut,
        clearError,
    }
}
