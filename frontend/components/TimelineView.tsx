"use client"
import React, { useRef, useEffect } from 'react'

interface TimelineViewProps {
    claims: any[]
    onClaimClick: (claimId: string) => void
    activeClaimId?: string | null
    explainabilityMode?: 'CASUAL' | 'EXPERT'
}

export function TimelineView({ claims, onClaimClick, activeClaimId, explainabilityMode = 'CASUAL' }: TimelineViewProps) {
    const activeNodeRef = useRef<HTMLButtonElement>(null)

    if (!claims || claims.length === 0) return null

    // Sort claims by start_char
    const sortedClaims = [...claims].sort((a, b) => (a.start_char || 0) - (b.start_char || 0))

    // Auto-scroll to active node
    useEffect(() => {
        if (activeNodeRef.current) {
            activeNodeRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            })
        }
    }, [activeClaimId])

    const getVerdictColor = (verdict: string) => {
        switch (verdict) {
            case "SUPPORTED":
            case "SUPPORTED_WEAK":
                return "bg-emerald-600 border-emerald-700" // Deeper emerald
            case "REFUTED":
                return "bg-red-500 border-red-600"
            default:
                return "bg-amber-400 border-amber-500" // Muted amber
        }
    }

    return (
        <div className="w-full bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
            {/* 1. Header (Research Grade) */}
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-baseline justify-between">
                    <h3 className="text-sm font-semibold text-slate-800 tracking-tight">
                        Epistemic Timeline
                    </h3>
                    <span className="text-[10px] text-slate-400 font-mono">
                        N={sortedClaims.length}
                    </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5 font-medium">
                    Claim-level epistemic status across the document
                </p>
            </div>

            {/* 2. Timeline Visualization */}
            {/* Added pt-14 for tooltip clearance, overflow-y-hidden strict */}
            <div className="relative overflow-x-auto overflow-y-hidden px-6 pt-14 pb-8 custom-scrollbar">
                <div className="flex items-center gap-10 min-w-max relative z-0">
                    {/* Neutral Connecting Line */}
                    <div className="absolute top-2 left-0 right-0 h-px bg-slate-200 -z-10" />

                    {sortedClaims.map((claim, idx) => {
                        const isActive = activeClaimId === claim.claim_id
                        const verdict = claim.verification?.verdict || "UNCERTAIN"
                        const confidence = claim.verification?.confidence || 0.0

                        // Strict Labels
                        let label = "Uncertain"
                        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") label = "Supported"
                        if (verdict === "REFUTED") label = "Refuted"

                        return (
                            <div
                                key={claim.claim_id}
                                className="relative group flex flex-col items-center"
                            >
                                {/* Interaction Node (Static CSS only) */}
                                <button
                                    ref={isActive ? activeNodeRef : null}
                                    onClick={() => onClaimClick(claim.claim_id)}
                                    aria-label={`Claim ${idx + 1}: ${label}`}
                                    className={`
                                        w-3.5 h-3.5 rounded-full border transition-transform duration-200 ease-out
                                        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-400
                                        hover:scale-110 active:scale-95 cursor-pointer
                                        ${getVerdictColor(verdict)}
                                        ${isActive ? 'ring-2 ring-offset-2 ring-slate-800 scale-110' : ''}
                                    `}
                                />

                                {/* Index Label */}
                                <span className={`mt-3 text-[10px] font-mono leading-none transition-colors ${isActive ? 'text-slate-900 font-bold' : 'text-slate-400'}`}>
                                    C{idx + 1}
                                </span>

                                {/* Tooltip (Strictly Contained) */}
                                <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-150 pointer-events-none z-20">
                                    <div className="bg-slate-800 text-white text-[10px] py-1.5 px-2.5 rounded shadow-lg whitespace-nowrap flex flex-col items-center">
                                        <span className="font-medium text-slate-200">Claim {idx + 1}</span>
                                        <div className="border-t border-slate-600 w-full my-1 opacity-50"></div>
                                        <span className="font-bold tracking-wide">{label}</span>
                                        {confidence > 0 && (
                                            <span className="text-[9px] text-slate-400 font-mono mt-0.5">
                                                Conf: {confidence.toFixed(2)}
                                            </span>
                                        )}
                                    </div>
                                    {/* Tooltip Arrow */}
                                    <div className="w-1.5 h-1.5 bg-slate-800 rotate-45 mx-auto -mt-0.5"></div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* 3. Legend (Sentence Case, Muted) */}
            <div className="border-t border-slate-100 bg-slate-50/50 px-6 py-3 flex justify-center gap-8">
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-600" />
                    <span className="text-[11px] text-slate-500 font-medium">Supported</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    <span className="text-[11px] text-slate-500 font-medium">Uncertain</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-500" />
                    <span className="text-[11px] text-slate-500 font-medium">Refuted</span>
                </div>
            </div>
        </div>
    )
}
