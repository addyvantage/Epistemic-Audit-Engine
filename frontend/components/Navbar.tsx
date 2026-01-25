"use client"
import Link from 'next/link'
import { ShieldCheck, Github, Moon, Sun } from 'lucide-react'
import { useTheme } from "@/app/providers/ThemeProvider"

export function Navbar() {
    const { theme, toggleTheme } = useTheme()

    return (
        <nav className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-border-subtle bg-white/80 dark:bg-black/90 backdrop-blur-md transition-colors duration-500">
            <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-slate-900 dark:text-slate-100">
                    <ShieldCheck className="w-5 h-5 text-slate-900 dark:text-slate-100" />
                    Epistemic Audit
                </Link>

                <div className="flex items-center gap-6 text-sm font-medium text-slate-500 dark:text-slate-400">
                    <Link href="/audit" className="hover:text-slate-900 dark:hover:text-slate-200 transition-colors">Audit</Link>
                    <Link href="/how-it-works" className="hover:text-slate-900 dark:hover:text-slate-200 transition-colors">How it works</Link>

                    {/* Theme Toggle */}
                    <button
                        onClick={toggleTheme}
                        aria-label="Toggle theme"
                        className="p-2 rounded-full bg-slate-100 dark:bg-graphite text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-charcoal transition-colors"
                    >
                        {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                    </button>

                    <div className="h-4 w-px bg-slate-200 dark:bg-border-subtle" />
                    <a href="https://github.com/addyvantage/epistemic-audit-engine" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 dark:hover:text-slate-200 transition-colors">
                        <Github className="w-5 h-5" />
                    </a>
                </div>
            </div>
        </nav>
    )
}
