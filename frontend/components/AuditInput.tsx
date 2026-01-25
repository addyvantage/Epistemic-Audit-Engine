"use client"
import React from 'react'
import { ArrowRight, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface AuditInputProps {
    onAudit: (text: string) => void
    isLoading: boolean
}

const MAX_CHARS = 5000

export function AuditInput({ onAudit, isLoading }: AuditInputProps) {
    const [text, setText] = React.useState("")
    const [isFocused, setIsFocused] = React.useState(false)

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (text.trim() && !isLoading) {
            onAudit(text)
        }
    }

    const charCount = text.length
    const charRatio = charCount / MAX_CHARS
    const counterColor = charRatio > 0.9 ? "text-red-500" : charRatio > 0.7 ? "text-amber-500" : "text-slate-400"

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
            <motion.div
                {...({
                    initial: false,
                    animate: {
                        borderColor: isFocused
                            ? 'rgba(16, 185, 129, 0.4)' // Emerald focus ring for terminal feel
                            : 'rgba(226, 232, 240, 0.1)',
                        boxShadow: isFocused
                            ? '0 0 0 1px rgba(16, 185, 129, 0.4), 0 10px 40px -10px rgba(0,0,0,0.5)' // Glow
                            : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                    },
                    // Glassmorphism card: Premium Dark Mode
                    className: "relative bg-white dark:bg-white/[0.02] dark:backdrop-blur-xl rounded-2xl border border-slate-200 dark:border-white/5 overflow-hidden transition-all duration-500 ease-out shadow-lg dark:shadow-none"
                } as any)}
            >
                {/* Scrollable Input Area */}
                <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        placeholder="Paste AI-generated or analytical text to audit..."
                        className="w-full min-h-[224px] p-6 pb-20 bg-transparent border-none resize-none text-lg text-slate-800 dark:text-slate-200 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-600 font-sans leading-relaxed selection:bg-emerald-500/30 selection:text-emerald-200"
                        disabled={isLoading}
                    />
                </div>

                {/* Fixed Footer Actions */}
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-white/80 dark:bg-white/10 backdrop-blur-md border-t border-slate-100 dark:border-white/5 flex items-center justify-between z-20">
                    <div className="flex items-center gap-2 pl-2">
                        <span className={`text-[11px] font-mono font-medium transition-colors duration-300 ${counterColor}`}>
                            <AnimatePresence mode="wait">
                                <motion.span
                                    key={charCount}
                                    initial={{ opacity: 0, y: 2 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -2 }}
                                    transition={{ duration: 0.15 }}
                                >
                                    {charCount.toLocaleString()}
                                </motion.span>
                            </AnimatePresence>
                            <span className="opacity-40"> / {MAX_CHARS.toLocaleString()} characters</span>
                        </span>
                    </div>

                    <motion.button
                        {...({
                            type: "submit",
                            disabled: !text.trim() || isLoading,
                            whileHover: !isLoading && text.trim() ? {
                                y: -1,
                                boxShadow: '0 4px 20px rgba(16, 185, 129, 0.2)',
                            } : {},
                            whileTap: !isLoading && text.trim() ? { scale: 0.97 } : {},
                            className: "inline-flex items-center justify-center px-6 py-2.5 bg-slate-900 dark:bg-emerald-600 text-white text-sm font-medium tracking-wide rounded-xl disabled:opacity-30 disabled:pointer-events-none transition-all shadow-lg shadow-slate-900/10 dark:shadow-none hover:dark:bg-emerald-500"
                        } as any)}
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                Run Audit
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </>
                        )}
                    </motion.button>
                </div>
            </motion.div>
        </form >
    )
}
