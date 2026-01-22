"use client"
import React from 'react'

interface EpistemicHighlightProps {
    children: React.ReactNode
    onClick: () => void
    isActive: boolean
    claimId: string
    verdict: string
    polarity?: string
}

export function EpistemicHighlight({ children, onClick, isActive, claimId, verdict, polarity }: EpistemicHighlightProps) {
    const getColorClass = () => {
        if (polarity === "META_EPISTEMIC") return "highlight-slate"
        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") return "highlight-green"
        if (verdict === "REFUTED") return "highlight-red"
        return "highlight-amber"
    }

    return (
        <span
            className={`epistemic-highlight ${getColorClass()} relative group ${isActive ? 'ring-2 ring-slate-400 ring-offset-1 rounded-sm' : ''}`}
            onClick={(e) => {
                e.stopPropagation();
                onClick();
            }}
        >
            {children}
            {/* Tooltip on Hover */}
            <span className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 px-2 py-1 bg-slate-800 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-20 font-mono">
                {claimId} • {verdict}
            </span>
        </span>
    )
}
