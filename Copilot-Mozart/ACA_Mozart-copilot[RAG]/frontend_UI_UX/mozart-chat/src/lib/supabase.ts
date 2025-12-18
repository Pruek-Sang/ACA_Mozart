// Supabase Client Configuration
// ใช้สำหรับ Authentication และ CRUD operations

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn('⚠️ Missing Supabase environment variables!')
    console.warn('Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env')
}

export const supabase = createClient(
    supabaseUrl || '',
    supabaseAnonKey || ''
)

// Types for database tables
export interface UserProfile {
    id: string
    full_name: string | null
    is_superuser: boolean
    created_at: string
    updated_at: string
}

export interface Project {
    id: string
    owner_id: string
    name: string
    description: string | null
    rooms: any[] | null  // JSONB
    loads: any | null    // JSONB
    sld_data: any | null // JSONB (for future Single Line Diagram)
    created_at: string
    updated_at: string
}
