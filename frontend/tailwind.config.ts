import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                border: "hsl(var(--foreground) / 0.1)",
                epistemic: {
                    supported: "rgba(34, 197, 94, 0.18)",       // muted green
                    insufficient: "rgba(245, 158, 11, 0.22)",  // amber
                    refuted: "rgba(239, 68, 68, 0.22)",         // red
                    meta: "rgba(148, 163, 184, 0.18)",          // slate
                    highlight: "rgba(255, 235, 120, 0.45)"      // marker yellow
                }
            },
            fontFamily: {
                mono: ['JetBrains Mono', 'monospace'],
            },
        },
    },
    plugins: [],
}
export default config
