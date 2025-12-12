/**
 * API Configuration for ACA Mozart Gateway
 */

export const API_CONFIG = {
    /** Gateway base URL - configurable via environment variable */
    GATEWAY_URL: import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000',

    /** LocalStorage key for API key */
    STORAGE_KEY: 'aca_mozart_api_key',

    /** Request timeout in milliseconds */
    TIMEOUT_MS: 60000,
};

/**
 * Theme colors matching the ACA Mozart dark design
 */
export const THEME = {
    bgPrimary: '#0D0D0D',
    bgSecondary: '#1A1A1A',
    bgInput: '#2D2D2D',
    textPrimary: '#FFFFFF',
    textSecondary: '#A0A0A0',
    accentMozart: '#6366F1',
    accentAmadeus: '#A855F7',
    userBubble: '#3B82F6',
    botBubble: '#374151',
};

/**
 * Quick action suggestions for the chat
 */
export const QUICK_SUGGESTIONS = [
    { label: '🍳 ออกแบบไฟครัว', text: 'ออกแบบไฟห้องครัวให้หน่อย' },
    { label: '⚡ คำนวณ Voltage Drop', text: 'คำนวณ voltage drop สาย 50 เมตร' },
    { label: '📋 มาตรฐาน วสท.', text: 'มาตรฐาน วสท. สำหรับบ้านพักอาศัย' },
    { label: '❄️ สายไฟแอร์', text: 'ขนาดสายไฟสำหรับแอร์ 18000 BTU' },
];
