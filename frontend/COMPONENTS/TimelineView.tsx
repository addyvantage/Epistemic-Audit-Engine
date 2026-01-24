"use client"
import React, { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

interface TimelineViewProps {
    claims: any[]
    onClaimClick: (claimId: string) => void
    activeClaimId?: string | null
    explainabilityMode?: 'CASUAL' | 'EXPERT'
}

export function TimelineView({ claims, onClaimClick, activeClaimId, explainabilityMode = 'CASUAL' }: TimelineViewProps) {
    const scrollContainerRef = useRef<HTMLDivElement>(null)
    const activeNodeRef = useRef<HTMLDivElement>(null)

    if (!claims || claims.length === 0) return null

    // Sort claims by their appearance in text
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
                return "bg-emerald-500"
            case "REFUTED":
                return "bg-red-500"
            default:
                return "bg-amber-500"
        }
    }

    const getVerdictFocusRing = (verdict: string) => {
        switch (verdict) {
            case "SUPPORTED":
            case "SUPPORTED_WEAK":
                return "focus:ring-emerald-400"
            case "REFUTED":
                return "focus:ring-red-400"
            default:
                return "focus:ring-amber-400"
        }
    }

    return (
        <div className="w-full bg-slate-50/50 backdrop-blur-md border border-slate-200 rounded-xl p-6 mt-8">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Epistemic Timeline
            </h3>

            {/* Scrollable Container */}
            <div
                ref={scrollContainerRef}
                className="relative overflow-x-auto overflow-y-visible py-12 px-4 custom-scrollbar -mx-2"
            >
                <div className="flex items-center gap-12 min-w-max relative pb-4">
                    {/* Continuous Horizontal Line */}
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-200 -translate-y-1/2 z-0" />

                    {sortedClaims.map((claim, idx) => {
                        const isActive = activeClaimId === claim.claim_id
                        const verdict = claim.verification?.verdict || "UNCERTAIN"

                        const getCasualVerdict = (v: string) => {
                            if (v === "SUPPORTED" || v === "SUPPORTED_WEAK") return "Verified"
                            if (v === "REFUTED") return "Contradicted"
                            return "Uncertain"
                        }

                        const tooltipText = explainabilityMode === "CASUAL" ? getCasualVerdict(verdict) : verdict

                        return (
                            <div
                                key={claim.claim_id}
                                ref={isActive ? activeNodeRef : null}
                                className="relative group flex flex-col items-center shrink-0 z-10"
                            >
                                {/* Node */}
                                <motion.div
                                    {...({
                                        role: "button",
                                        tabIndex: 0,
                                        "aria-label": `Claim ${tooltipText.toLowerCase()}`,
                                        onFocus: (e: React.FocusEvent<HTMLElement>) => {
                                            e.currentTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                                        }
                                    } as any)}
                                    whileHover={{ scale: 1.2 }}
                                    whileTap={{ scale: 0.9 }}
                                    onClick={() => onClaimClick(claim.claim_id)}
                                    onKeyDown={(e: React.KeyboardEvent) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                            onClaimClick(claim.claim_id)
                                        }
                                    }}
                                    className={`w-4 h-4 rounded-full transition-all duration-300 cursor-pointer outline-none focus:ring-2 focus:ring-offset-2 ${getVerdictFocusRing(verdict)} ${getVerdictColor(verdict)} ${isActive ? 'ring-4 ring-offset-2 ring-slate-400' : 'group-hover:ring-4 group-hover:ring-offset-1 group-hover:ring-slate-300'
                                        }`}
                                />

                                {/* Tooltip (Simple) */}
                                <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 text-white text-[10px] py-1 px-2 rounded whitespace-nowrap z-20 pointer-events-none uppercase tracking-wider">
                                    {tooltipText}
                                </div>

                                {/* Order Number */}
                                <span className="mt-2 text-[10px] font-medium text-slate-400">
                                    {idx + 1}
                                </span>
                            </div>
                        )
                    })}
                </div>
            </div>

            <div className="mt-6 flex justify-center gap-6 text-[11px] font-medium text-slate-500">
                <div className="flex items-center gap-1.5 shrink-0">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" /> Supported
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                    <span className="w-2 h-2 rounded-full bg-amber-500" /> Uncertain / Weak
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                    <span className="w-2 h-2 rounded-full bg-red-500" /> Refuted
                </div>
            </div>
        </div>
    )
}
