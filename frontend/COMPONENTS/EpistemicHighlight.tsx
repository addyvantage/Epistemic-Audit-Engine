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

export function EpistemicHighlight({ children, onClick, onMouseEnter, onMouseLeave, onFocus, onBlur, isActive, claimId, verdict, polarity, isContested, isDerived }: EpistemicHighlightProps) {
    const getColorClass = () => {
        if (isDerived) return "border-b-2 border-slate-300 text-slate-600 border-dashed"
        if (isContested) return "border-b-2 border-dotted border-slate-400 italic text-slate-700"
        if (polarity === "META_EPISTEMIC") return "highlight-slate"
        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") return "highlight-green"
        if (verdict === "REFUTED") return "highlight-red"
        return "highlight-amber"
    }

    const getFocusRing = () => {
        if (verdict === "REFUTED") return "focus:ring-red-400"
        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") return "focus:ring-emerald-400"
        return "focus:ring-amber-400"
    }

    const getAriaLabel = () => {
        if (verdict === "REFUTED") return "Claim refuted"
        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") return "Claim verified"
        return "Claim uncertain"
    }

    return (
        <span
            tabIndex={0}
            role="button"
            aria-label={getAriaLabel()}
            className={`${isContested ? '' : 'epistemic-highlight'} ${getColorClass()} relative group cursor-pointer outline-none focus:ring-2 focus:ring-offset-2 rounded-sm transition-all ${getFocusRing()} ${isActive ? 'ring-2 ring-slate-400 ring-offset-1 rounded-sm' : ''}`}
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
        >
            {children}
            {/* Hover Glow Pulse (Micro-Animation) */}
            <span className={`absolute bottom-0 left-0 w-full h-0.5 opacity-0 group-hover:animate-pulse-once group-hover:opacity-100 focus:opacity-100 transition-all duration-300 ${verdict === "REFUTED" ? "bg-red-400/50 shadow-[0_0_8px_rgba(248,113,113,0.6)]" :
                (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") ? "bg-emerald-400/50 shadow-[0_0_8px_rgba(52,211,153,0.6)]" :
                    "bg-amber-400/50 shadow-[0_0_8px_rgba(251,191,36,0.6)]"
                }`} />
        </span>
    )
}
