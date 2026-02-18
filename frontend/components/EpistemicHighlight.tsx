"use client"
import React from 'react'

interface EpistemicHighlightProps {
    children: React.ReactNode
    onClick: () => void
    onMouseEnter: (e: React.MouseEvent) => void
    onMouseLeave: () => void
    onFocus?: (e: React.FocusEvent) => void
    onBlur?: () => void
    isActive: boolean
    claimId: string
    verdict: string
    polarity?: string
    isContested?: boolean
    isDerived?: boolean
}

const HIGHLIGHT_CLASS_MAP: Record<string, string> = {
    SUPPORTED: "bg-emerald-200/50 dark:bg-emerald-500/30 text-emerald-900 dark:text-emerald-100",
    SUPPORTED_WEAK: "bg-emerald-200/50 dark:bg-emerald-500/30 text-emerald-900 dark:text-emerald-100",
    PARTIALLY_SUPPORTED: "bg-teal-200/50 dark:bg-teal-500/30 text-teal-900 dark:text-teal-100",
    REFUTED: "bg-red-200/50 dark:bg-red-500/30 text-red-900 dark:text-red-100",
    UNCERTAIN: "bg-amber-200/50 dark:bg-amber-500/30 text-amber-900 dark:text-amber-100",
    META_EPISTEMIC: "bg-slate-100 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300",
}

const FOCUS_RING_MAP: Record<string, string> = {
    SUPPORTED: "focus:ring-emerald-400",
    SUPPORTED_WEAK: "focus:ring-emerald-400",
    PARTIALLY_SUPPORTED: "focus:ring-teal-400",
    REFUTED: "focus:ring-red-400",
    UNCERTAIN: "focus:ring-amber-400",
}

export function EpistemicHighlight({ children, onClick, onMouseEnter, onMouseLeave, onFocus, onBlur, isActive, claimId, verdict, polarity, isContested, isDerived }: EpistemicHighlightProps) {

    // Static JIT-safe class resolution
    const colorClass = HIGHLIGHT_CLASS_MAP[polarity === "META_EPISTEMIC" ? "META_EPISTEMIC" : verdict] || HIGHLIGHT_CLASS_MAP.UNCERTAIN

    const getOtherClasses = () => {
        if (isDerived) return "border-b-2 border-slate-300 dark:border-white/20 text-slate-600 dark:text-slate-400 border-dashed"
        if (isContested) return "border-b-2 border-dotted border-red-400 text-slate-700 dark:text-slate-300"
        return ""
    }

    const getAriaLabel = () => {
        if (verdict === "REFUTED") return "Claim refuted"
        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") return "Claim verified"
        if (verdict === "PARTIALLY_SUPPORTED") return "Claim partially supported"
        return "Claim uncertain"
    }

    return (
        <span
            tabIndex={0}
            role="button"
            aria-label={getAriaLabel()}
            className={`
                relative isolate 
                px-0.5 rounded-sm 
                cursor-pointer 
                transition-all duration-200 
                outline-none 
                ${colorClass}
                ${getOtherClasses()}
                ${FOCUS_RING_MAP[verdict] || "focus:ring-amber-400"} 
                ${isActive ? 'ring-2 ring-slate-400 dark:ring-white/50 ring-offset-1 dark:ring-offset-black rounded-sm z-20' : 'z-auto'}
                group
            `}
            onClick={(e) => {
                e.stopPropagation();
                onClick();
            }}
            onMouseEnter={onMouseEnter}
            onMouseLeave={onMouseLeave}
            onFocus={onFocus}
            onBlur={onBlur}
            onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onClick();
                }
            }}
            style={{ boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone' }}
        >
            {children}
            {/* Hover Glow Pulse (Micro-Animation) */}
            <span className={`
                absolute bottom-0 left-0 w-full h-full 
                opacity-0 group-hover:opacity-100 
                transition-opacity duration-300 
                pointer-events-none 
                rounded-sm
                ${verdict === "REFUTED" ? "bg-red-400/20" :
                    (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") ? "bg-emerald-400/20" :
                        verdict === "PARTIALLY_SUPPORTED" ? "bg-teal-400/20" :
                        "bg-amber-400/20"
                }`}
            />
        </span>
    )
}
