import type { Config } from 'tailwindcss'

const config: Config = {
    darkMode: 'class',
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx}',
        './pages/**/*.{js,ts,jsx,tsx}',
    ],
    safelist: [
        "bg-emerald-200/50",
        "dark:bg-emerald-500/30",
        "text-emerald-900",
        "dark:text-emerald-100",
        "bg-red-200/50",
        "dark:bg-red-500/30",
        "text-red-900",
        "dark:text-red-100",
        "bg-amber-200/50",
        "dark:bg-amber-500/30",
        "text-amber-900",
        "dark:text-amber-100",
        "bg-slate-100",
        "dark:bg-slate-800/50",
        "text-slate-700",
        "dark:text-slate-300",
        "isolate",
        "dark:bg-neutral-900",
        "dark:bg-neutral-900/60",
        "dark:bg-neutral-900/80",
        "dark:border-white/10",
    ],
    theme: {
        extend: {
            colors: {
                // Cinematic Research Theme (Dark Mode) - GRAPHITE BASE
                obsidian: "#0A0A0B",      // Base background (Deep Graphite)
                charcoal: "#111113",      // Cards (Slightly lighter graphite)
                graphite: "#1A1A1C",      // Panels
                modal: "#0A0A0B",         // Modals
                "border-subtle": "rgba(255, 255, 255, 0.08)", // Increased visibility for 000 on 000 contrast

                // Surface Elevation System (4-tier)
                surface: {
                    void: "transparent",
                    base: "rgba(255, 255, 255, 0.02)",
                    elevated: "rgba(255, 255, 255, 0.04)",
                    modal: "rgba(255, 255, 255, 0.06)",
                },

                // Border Elevation System
                "border-surface": {
                    base: "rgba(255, 255, 255, 0.05)",
                    elevated: "rgba(255, 255, 255, 0.08)",
                    modal: "rgba(255, 255, 255, 0.10)",
                    glow: "rgba(16, 185, 129, 0.30)",
                },

                // Epistemic Verdict Colors
                epistemic: {
                    supported: "rgba(34, 197, 94, 0.18)",       // muted green
                    insufficient: "rgba(245, 158, 11, 0.22)",  // amber
                    refuted: "rgba(239, 68, 68, 0.22)",         // red
                    meta: "rgba(160, 160, 160, 0.18)",          // Neutral Gray (No Slate)
                    highlight: "rgba(255, 235, 120, 0.45)"      // marker yellow
                },

                // Glow Colors (for box-shadows and borders)
                glow: {
                    emerald: "rgba(16, 185, 129, 0.15)",
                    "emerald-strong": "rgba(16, 185, 129, 0.25)",
                    white: "rgba(255, 255, 255, 0.08)",
                    amber: "rgba(245, 158, 11, 0.15)",
                    red: "rgba(239, 68, 68, 0.15)",
                }
            },
            fontFamily: {
                sans: ['var(--font-primary)', 'system-ui', 'sans-serif'],
                // Scoped utility for raw text input - specific terminal stack
                input: ['Menlo', 'SF Mono', 'Monaco', 'Consolas', '"Liberation Mono"', 'monospace'],
            },
            animation: {
                'text-shimmer': 'text-shimmer 8s linear infinite',
                'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
                'fade-in': 'fade-in 0.5s ease-out',
                'slide-up': 'slide-up 0.5s ease-out',
                'count-up': 'count-up 1.5s ease-out',
            },
            keyframes: {
                'text-shimmer': {
                    '0%, 100%': {
                        'background-size': '200% 200%',
                        'background-position': 'left center'
                    },
                    '50%': {
                        'background-size': '200% 200%',
                        'background-position': 'right center'
                    }
                },
                'glow-pulse': {
                    '0%, 100%': {
                        'box-shadow': '0 0 20px rgba(16, 185, 129, 0.1), inset 0 0 20px rgba(16, 185, 129, 0.02)'
                    },
                    '50%': {
                        'box-shadow': '0 0 30px rgba(16, 185, 129, 0.2), inset 0 0 30px rgba(16, 185, 129, 0.05)'
                    }
                },
                'fade-in': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' }
                },
                'slide-up': {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' }
                },
                'count-up': {
                    '0%': { opacity: '0', transform: 'scale(0.8)' },
                    '50%': { opacity: '1', transform: 'scale(1.02)' },
                    '100%': { opacity: '1', transform: 'scale(1)' }
                }
            },
            boxShadow: {
                'glow-sm': '0 0 10px rgba(16, 185, 129, 0.1)',
                'glow-md': '0 0 20px rgba(16, 185, 129, 0.15)',
                'glow-lg': '0 0 30px rgba(16, 185, 129, 0.2)',
                'glow-xl': '0 0 40px rgba(16, 185, 129, 0.25), 0 0 80px rgba(16, 185, 129, 0.1)',
                'inner-glow': 'inset 0 0 20px rgba(16, 185, 129, 0.05)',
                'elevated': '0 10px 40px rgba(0, 0, 0, 0.3)',
                'elevated-lg': '0 20px 60px rgba(0, 0, 0, 0.4)',
            }
        },
    },
    plugins: [],
}
export default config
