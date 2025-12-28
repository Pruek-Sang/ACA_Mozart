import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * cn() - รวม Tailwind Classes อย่างปลอดภัย
 * ใช้: cn("bg-red-500", isActive && "bg-blue-500")
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// === 🛑 NO BLACK BOX ZONE: Error Tracer ===

interface ClassifiedError {
    type: 'frontend' | 'backend' | 'network';
    message: string;
    details?: string;
}

/**
 * classifyError() - แยกประเภท Error ว่ามาจากที่ไหน
 * 
 * เหตุผล: เวลา Debug จะได้รู้ว่าต้องแก้ที่ Frontend หรือ Backend
 * 
 * @param error - Error object จาก catch block
 * @returns ClassifiedError พร้อม type และ message
 */
export function classifyError(error: any): ClassifiedError {

    // 1. Network Error (ไม่ต่ออินเทอร์เน็ต / Server ล่ม / CORS)
    if (
        error.code === 'ERR_NETWORK' ||
        error.message?.includes('Failed to fetch') ||
        error.message?.includes('Network Error')
    ) {
        return {
            type: 'network',
            message: '⚠️ ไม่สามารถเชื่อมต่อกับ Server ได้',
            details: 'ตรวจสอบ: Internet, VPN, หรือ Server อาจล่ม'
        };
    }

    // 2. Backend Error (ส่ง Status 4xx, 5xx)
    if (error.response) {
        const status = error.response.status;
        const serverMsg = error.response.data?.error || error.response.data?.message;

        let msg = `Backend Error (${status})`;

        if (status >= 500) {
            msg = `⛔ Server พังภายใน (${status})`;
        } else if (status === 401) {
            msg = '🔐 ไม่ได้รับอนุญาต (401) - ต้อง Login';
        } else if (status === 403) {
            msg = '🚫 ถูกปฏิเสธการเข้าถึง (403)';
        } else if (status === 404) {
            msg = '❓ ไม่พบ API Endpoint นี้ (404)';
        } else if (status === 422) {
            msg = '📝 ข้อมูลไม่ครบ (422)';
            if (error.response.data?.missing_fields) {
                msg += ` - ขาด: ${error.response.data.missing_fields.join(', ')}`;
            }
        } else if (status === 429) {
            msg = '⏳ เรียกใช้บ่อยเกินไป (429) - รอสักครู่';
        }

        return {
            type: 'backend',
            message: msg,
            details: serverMsg || undefined
        };
    }

    // 3. Frontend Error (Code เราผิดเอง / Logic Error)
    return {
        type: 'frontend',
        message: `🐛 UI Error: ${error.message || 'Unknown Error'}`,
        details: error.stack
    };
}

/**
 * API Base URL - ใช้สำหรับทุก API Call
 * ปรับได้ผ่าน Environment Variable
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

/**
 * buildApiUrl() - สร้าง Full URL สำหรับ API
 * @param endpoint - เช่น '/api/v1/design'
 */
export function buildApiUrl(endpoint: string): string {
    return `${API_BASE_URL}${endpoint}`;
}
