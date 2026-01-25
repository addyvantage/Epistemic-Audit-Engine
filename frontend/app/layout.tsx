import './globals.css'
import type { Metadata } from 'next'
import Link from 'next/link'
import { ShieldCheck, Github } from 'lucide-react'
import { ThemeProvider } from "@/app/providers/ThemeProvider"

import { Navbar } from "@/components/Navbar"

export const metadata: Metadata = {
    title: 'Epistemic Audit Engine',
    description: 'Research-grade verification of AI outputs.',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <head>
                <script
                    dangerouslySetInnerHTML={{
                        __html: `
                            try {
                                if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                                    document.documentElement.classList.add('dark')
                                } else {
                                    document.documentElement.classList.remove('dark')
                                }
                            } catch (_) {}
                        `,
                    }}
                />
            </head>
            <body className={`font-sans bg-white dark:bg-black min-h-screen flex flex-col antialiased transition-colors duration-500 selection:bg-emerald-500/20 selection:text-emerald-200`}>
                <ThemeProvider>
                    <Navbar />

                    <main className="flex-1">
                        {children}
                    </main>

                    <footer className="py-8 text-center text-xs text-slate-400 dark:text-neutral-500 border-t border-slate-200 dark:border-white/5 mt-auto bg-white dark:bg-black transition-colors duration-300">
                        Epistemic Audit Engine v1.2 (Satoshi) • Research Artifact
                    </footer>
                </ThemeProvider>
            </body>
        </html>
    )
}
