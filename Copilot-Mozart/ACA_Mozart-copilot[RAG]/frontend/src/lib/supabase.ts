import { createClient } from '@supabase/supabase-js';

/**
 * Supabase Client Configuration
 * 
 * ⚠️ ใช้ anon_key เท่านั้น (ปลอดภัยสำหรับ Frontend)
 * ❌ ห้ามใช้ service_role_key ใน Frontend!
 */

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
    console.error('❌ Missing Supabase environment variables!');
    console.error('   Required: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY');
    console.error('   Current URL:', supabaseUrl ? '✅ Set' : '❌ Missing');
    console.error('   Current Key:', supabaseAnonKey ? '✅ Set' : '❌ Missing');
}

/**
 * Supabase Client Instance
 * - ใช้สำหรับ Auth, Database, Storage
 * - Auto-refresh token
 * 
 * ⚠️ ถ้า env vars หาย จะไม่ crash แต่ auth จะไม่ทำงาน
 */
export const supabase = createClient(
    supabaseUrl || 'https://placeholder.supabase.co',
    supabaseAnonKey || 'placeholder-key',
    {
        auth: {
            persistSession: true,
            autoRefreshToken: true,
            detectSessionInUrl: true,
        }
    }
);

/**
 * ดึง Access Token สำหรับส่งไป Backend
 * @returns JWT Token string หรือ null
 */
export async function getAccessToken(): Promise<string | null> {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
}

/**
 * ดึงข้อมูล User ปัจจุบัน
 */
export async function getCurrentUser() {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
}

/**
 * Logout
 */
export async function signOut() {
    const { error } = await supabase.auth.signOut();
    if (error) {
        console.error('Logout error:', error);
        throw error;
    }
}
