import './globals.css'
import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import Link from 'next/link'
import { ShieldCheck, Github } from 'lucide-react'

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

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
            <body className={`${inter.variable} ${mono.variable} font-sans bg-slate-50 min-h-screen flex flex-col`}>
                {/* Navigation */}
                <nav className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/80 backdrop-blur-md">
                    <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
                        <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
                            <ShieldCheck className="w-5 h-5 text-slate-900" />
                            Epistemic Audit
                        </Link>

                        <div className="flex items-center gap-6 text-sm font-medium text-slate-500">
                            <Link href="/audit" className="hover:text-slate-900 transition-colors">Audit</Link>
                            <Link href="/info" className="hover:text-slate-900 transition-colors">How it works</Link>
                            <div className="h-4 w-px bg-slate-200" />
                            <a href="https://github.com/addyvantage/epistemic-audit-engine" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 transition-colors">
                                <Github className="w-5 h-5" />
                            </a>
                        </div>
                    </div>
                </nav>

                <main className="flex-1">
                    {children}
                </main>

                <footer className="py-8 text-center text-xs text-slate-400 border-t border-slate-200 mt-auto bg-white">
                    Epistemic Audit Engine v1.1 (Frozen Phase) • Research Artifact
                </footer>
            </body>
        </html>
    )
}
