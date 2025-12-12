/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                bgPrimary: '#0D0D0D',
                bgSecondary: '#1A1A1A',
                bgInput: '#2D2D2D',
                textPrimary: '#FFFFFF',
                textSecondary: '#A0A0A0',
                accentMozart: '#6366F1',
                accentAmadeus: '#A855F7',
                userBubble: '#3B82F6',
                botBubble: '#374151',
            },
            fontFamily: {
                sans: ['Inter', 'Noto Sans Thai', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
