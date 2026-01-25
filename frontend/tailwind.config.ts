import type { Config } from 'tailwindcss'

const config: Config = {
    darkMode: 'class',
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
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
                epistemic: {
                    supported: "rgba(34, 197, 94, 0.18)",       // muted green
                    insufficient: "rgba(245, 158, 11, 0.22)",  // amber
                    refuted: "rgba(239, 68, 68, 0.22)",         // red
                    meta: "rgba(160, 160, 160, 0.18)",          // Neutral Gray (No Slate)
                    highlight: "rgba(255, 235, 120, 0.45)"      // marker yellow
                }
            },
            fontFamily: {
                sans: ['var(--font-primary)', 'system-ui', 'sans-serif'],
                // Scoped utility for raw text input - specific terminal stack
                input: ['Menlo', 'SF Mono', 'Monaco', 'Consolas', '"Liberation Mono"', 'monospace'],
            },
            animation: {
                'text-shimmer': 'text-shimmer 8s linear infinite',
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
                }
            }
        },
    },
    plugins: [],
}
export default config
