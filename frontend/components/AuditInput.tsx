"use client"
import React, { useEffect, useRef, useState } from 'react'
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
    const [toastMessage, setToastMessage] = useState("")
    const [isToastVisible, setIsToastVisible] = useState(false)
    const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const lastToastRef = useRef<{ message: string; at: number }>({ message: "", at: 0 })

    const clampText = (input: string): { value: string; didClamp: boolean } => {
        if (input.length <= MAX_CHARS) {
            return { value: input, didClamp: false }
        }

        return { value: input.slice(0, MAX_CHARS), didClamp: true }
    }

    const showToast = (message: string) => {
        const now = Date.now()
        if (lastToastRef.current.message === message && now - lastToastRef.current.at < 800) {
            return
        }
        lastToastRef.current = { message, at: now }
        setToastMessage(message)
        setIsToastVisible(true)

        if (toastTimerRef.current) {
            clearTimeout(toastTimerRef.current)
        }
        toastTimerRef.current = setTimeout(() => {
            setIsToastVisible(false)
        }, 2000)
    }

    // Breathing animation cycle
    useEffect(() => {
        if (!isFocused && !text.trim()) {
            const interval = setInterval(() => {
                setBreathPhase((prev) => (prev + 1) % 2)
            }, 3000)
            return () => clearInterval(interval)
        }
    }, [isFocused, text])

    useEffect(() => {
        return () => {
            if (toastTimerRef.current) {
                clearTimeout(toastTimerRef.current)
            }
        }
    }, [])

    const submitAudit = () => {
        if (isLoading) {
            return
        }

        if (text.length > MAX_CHARS) {
            showToast("Text exceeds 5000 characters.")
            return
        }

        if (!text.trim() || text.length === 0) {
            showToast("Paste text to audit first.")
            return
        }

        onAudit(text)
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        submitAudit()
    }

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const { value, didClamp } = clampText(e.target.value)
        setText(value)

        if (didClamp) {
            showToast("Character limit reached (5000 max). Extra text was not added.")
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        const isComposing = (e.nativeEvent as KeyboardEvent).isComposing

        if (e.key === "Enter" && !e.shiftKey) {
            if (isComposing) {
                return
            }
            e.preventDefault()
            submitAudit()
            return
        }

        if (isComposing || e.metaKey || e.ctrlKey || e.altKey) {
            return
        }

        if (e.key.length !== 1) {
            return
        }

        const selectionLength = e.currentTarget.selectionEnd - e.currentTarget.selectionStart
        if (text.length >= MAX_CHARS && selectionLength === 0) {
            e.preventDefault()
            showToast("Character limit reached (5000 max). Extra text was not added.")
        }
    }

    const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
        e.preventDefault()
        const pasteText = e.clipboardData.getData("text")
        const { selectionStart, selectionEnd } = e.currentTarget
        const next = `${text.slice(0, selectionStart)}${pasteText}${text.slice(selectionEnd)}`
        const { value, didClamp } = clampText(next)
        setText(value)
        if (didClamp) {
            showToast("Character limit reached (5000 max). Extra text was not added.")
        }
    }

    const handleDrop = (e: React.DragEvent<HTMLTextAreaElement>) => {
        const droppedText = e.dataTransfer.getData("text")
        if (!droppedText) {
            return
        }

        e.preventDefault()
        const { selectionStart, selectionEnd } = e.currentTarget
        const next = `${text.slice(0, selectionStart)}${droppedText}${text.slice(selectionEnd)}`
        const { value, didClamp } = clampText(next)
        setText(value)
        if (didClamp) {
            showToast("Character limit reached (5000 max). Extra text was not added.")
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
        <>
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
                            onChange={handleChange}
                            onKeyDown={handleKeyDown}
                            onPaste={handlePaste}
                            onDrop={handleDrop}
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
            </form>

            <AnimatePresence>
                {isToastVisible && (
                    <MotionDiv
                        initial={{ opacity: 0, y: 12, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 12, scale: 0.98 }}
                        transition={{ duration: 0.2, ease: PREMIUM_EASE }}
                        className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 px-4 py-2.5 rounded-xl border border-slate-200/80 dark:border-white/10 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md shadow-lg text-sm text-slate-700 dark:text-slate-200"
                        role="status"
                        aria-live="polite"
                    >
                        {toastMessage}
                    </MotionDiv>
                )}
            </AnimatePresence>
        </>
    )
}
