"use client"
import React, { useEffect, useState } from 'react'
import { ArrowRight, Loader2, Terminal } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { PREMIUM_EASE } from '@/lib/motion-variants'

// --- TypeScript Fix ---
const MotionDiv = motion.div as any
const MotionSpan = motion.span as any
const MotionButton = motion.button as any


interface AuditInputProps {
    onAudit: (text: string) => void
    isLoading: boolean
}

const MAX_CHARS = 5000

export function AuditInput({ onAudit, isLoading }: AuditInputProps) {
    const [text, setText] = React.useState("")
    const [isFocused, setIsFocused] = React.useState(false)
    const [breathPhase, setBreathPhase] = useState(0)

    // Breathing animation cycle
    useEffect(() => {
        if (!isFocused && !text.trim()) {
            const interval = setInterval(() => {
                setBreathPhase((prev) => (prev + 1) % 2)
            }, 3000)
            return () => clearInterval(interval)
        }
    }, [isFocused, text])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (text.trim() && !isLoading) {
            onAudit(text)
        }
    }

    const charCount = text.length
    const charRatio = charCount / MAX_CHARS
    const counterColor = charRatio > 0.9 ? "text-red-500" : charRatio > 0.7 ? "text-amber-500" : "text-slate-400"

    // Determine glow state
    const getGlowState = () => {
        if (isFocused) {
            return {
                borderColor: 'rgba(16, 185, 129, 0.5)',
                boxShadow: '0 0 0 1px rgba(16, 185, 129, 0.5), 0 0 30px rgba(16, 185, 129, 0.15), 0 10px 40px -10px rgba(0,0,0,0.5)'
            }
        }
        if (!text.trim()) {
            // Breathing state when empty and not focused
            return {
                borderColor: breathPhase === 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.2)',
                boxShadow: breathPhase === 0
                    ? '0 0 0 1px rgba(16, 185, 129, 0.1), 0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    : '0 0 0 2px rgba(16, 185, 129, 0.15), 0 0 20px rgba(16, 185, 129, 0.08), 0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }
        }
        return {
            borderColor: 'rgba(226, 232, 240, 0.1)',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
        }
    }

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
            <MotionDiv
                initial={false}
                animate={getGlowState()}
                transition={{ duration: 1.5, ease: PREMIUM_EASE }}
                className="relative bg-white dark:bg-white/[0.02] dark:backdrop-blur-xl rounded-2xl border border-slate-200 dark:border-white/5 overflow-hidden shadow-lg dark:shadow-none"
            >
                {/* Terminal hint when empty */}
                <AnimatePresence>
                    {!text.trim() && !isFocused && (
                        <MotionDiv
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute top-4 right-4 flex items-center gap-2 text-[10px] font-mono text-slate-400 dark:text-slate-600 uppercase tracking-widest z-10"
                        >
                            <Terminal className="w-3 h-3" />
                            <span>Ready for input</span>
                        </MotionDiv>
                    )}
                </AnimatePresence>

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
                                <MotionSpan
                                    key={charCount}
                                    initial={{ opacity: 0, y: 2 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -2 }}
                                    transition={{ duration: 0.15 }}
                                >
                                    {charCount.toLocaleString()}
                                </MotionSpan>
                            </AnimatePresence>
                            <span className="opacity-40"> / {MAX_CHARS.toLocaleString()} characters</span>
                        </span>
                    </div>

                    <MotionButton
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
                    </MotionButton>
                </div>
            </MotionDiv>
        </form >
    )
}
