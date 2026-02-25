/** @type {import('tailwindcss').Config} */
export default {
    content: [
        './index.html',
        './src/**/*.{js,ts,jsx,tsx}',
    ],
    theme: {
        extend: {
            colors: {
                bg: {
                    primary: '#0a0a0f',
                    secondary: '#12121a',
                    tertiary: '#1a1a25',
                    card: '#141420',
                },
                accent: {
                    green: '#00ff88',
                    amber: '#ffb300',
                    red: '#ff3b3b',
                    blue: '#4a9eff',
                },
                text: {
                    primary: '#e0e0e0',
                    secondary: '#888899',
                    muted: '#555566',
                },
            },
            fontFamily: {
                mono: ['"JetBrains Mono"', 'monospace'],
                sans: ['"Inter"', 'sans-serif'],
            },
            animation: {
                'pulse-live': 'pulse-live 2s ease-in-out infinite',
                'slide-in': 'slide-in 0.35s ease-out',
                'count-up': 'count-up 0.6s ease-out',
            },
            keyframes: {
                'pulse-live': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.4 },
                },
                'slide-in': {
                    from: { opacity: 0, transform: 'translateY(-12px)' },
                    to: { opacity: 1, transform: 'translateY(0)' },
                },
            },
        },
    },
    plugins: [],
};
