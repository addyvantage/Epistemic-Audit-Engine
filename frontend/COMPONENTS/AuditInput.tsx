"use client"
import React from 'react'
import { ArrowRight, Loader2 } from 'lucide-react'

interface AuditInputProps {
    onAudit: (text: string) => void
    isLoading: boolean
}

export function AuditInput({ onAudit, isLoading }: AuditInputProps) {
    const [text, setText] = React.useState("")

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (text.trim() && !isLoading) {
            onAudit(text)
        }
    }

    // Refactored: Container holds the visual border/bg. Textarea is transparent.
    // Controls are absolutely positioned inside with z-index to ensure clickability.

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
            <div className="relative group bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all focus-within:border-slate-300 focus-within:shadow-lg">

                <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Paste AI-generated or analytical text to audit..."
                    className="w-full h-56 p-6 pb-20 rounded-2xl bg-transparent border-none resize-none text-lg text-slate-800 outline-none placeholder:text-slate-300 font-sans leading-relaxed"
                    disabled={isLoading}
                />

                {/* Controls Container: Absolute Layout inside the white box */}
                <div className="absolute bottom-4 right-4 flex items-center gap-4 z-20 bg-white/50 backdrop-blur-sm rounded-xl pl-2 py-1 pr-1">
                    <span className={`text-xs text-slate-400 font-mono transition-opacity select-none ${text ? 'opacity-100' : 'opacity-0'}`}>
                        {text.length} chars
                    </span>

                    <button
                        type="submit"
                        disabled={!text.trim() || isLoading}
                        className="inline-flex items-center justify-center px-6 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-xl hover:bg-slate-800 disabled:opacity-0 disabled:scale-95 disabled:pointer-events-none transition-all shadow-lg shadow-slate-900/10 active:scale-95"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                Run Audit
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </>
                        )}
                    </button>
                </div>

            </div>
        </form>
    )
}
