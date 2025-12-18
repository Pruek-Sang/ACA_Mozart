// Auth Context - ให้ทั้ง app เข้าถึง auth state ได้
// ใช้ร่วมกับ useAuth hook

import { createContext, useContext, type ReactNode } from 'react'
import { useAuth } from '../hooks/useAuth'
import type { User, Session } from '@supabase/supabase-js'

interface AuthContextType {
    user: User | null
    session: Session | null
    loading: boolean
    error: string | null
    signIn: (email: string, password: string) => Promise<boolean>
    signUp: (email: string, password: string, fullName?: string) => Promise<boolean>
    signOut: () => Promise<void>
    clearError: () => void
    isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
    children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
    const auth = useAuth()

    const value: AuthContextType = {
        ...auth,
        isAuthenticated: !!auth.user,
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuthContext(): AuthContextType {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuthContext must be used within an AuthProvider')
    }
    return context
}
