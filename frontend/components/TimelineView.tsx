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

    // Auto-scroll to active node with container-aware centering
    useEffect(() => {
        if (activeNodeRef.current) {
            activeNodeRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            })
        }
    }, [activeClaimId])

    // Scroll Discoverability Nudge (Mount only)
    const containerRef = useRef<HTMLDivElement>(null)
    useEffect(() => {
        const el = containerRef.current
        if (!el) return
        // Tiny initial scroll to hint horizontally
        const timer = setTimeout(() => {
            el.scrollBy({ left: 24, behavior: 'smooth' })
        }, 800)
        return () => clearTimeout(timer)
    }, [])


    return (
        <div className="
            w-full
            bg-white/80 dark:bg-neutral-900/80
            backdrop-blur-xl
            border border-slate-200/60 dark:border-white/10
            rounded-lg
            flex flex-col
            overflow-hidden
            transition-colors duration-500
        ">
            {/* 1. Header (Research Grade) */}
            <div className="px-6 py-4 border-b border-slate-100 dark:border-white/5 bg-slate-50/60 dark:bg-neutral-900/60 transition-colors duration-500">
                <div className="flex items-baseline justify-between">
                    <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 tracking-tight">
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

            {/* 2. Scroll Viewport (Flagship Horizontal Interaction) */}
            <div className="relative group perspective-[1000px]">
                <div
                    ref={containerRef}
                    tabIndex={0}
                    onKeyDown={(e) => {
                        if (e.key === 'ArrowRight') e.currentTarget.scrollBy({ left: 120, behavior: 'smooth' })
                        if (e.key === 'ArrowLeft') e.currentTarget.scrollBy({ left: -120, behavior: 'smooth' })
                    }}
                    className="
                        flex gap-12 px-12 py-8
                        overflow-x-auto
                        scroll-smooth
                        snap-x snap-mandatory
                        no-scrollbar
                        focus:outline-none
                        relative z-0
                    "
                >
                    {/* Subtle Track Line (Background Layer) */}
                    <div className="absolute top-1/2 left-12 right-12 h-px bg-slate-200/70 dark:bg-white/5 -translate-y-1/2 z-[-1]" />

                    {sortedClaims.map((claim, idx) => (
                        <ClaimNode
                            key={idx}
                            claim={claim}
                            idx={idx}
                            isActive={activeClaimId === claim.claim_id}
                            onClaimClick={onClaimClick}
                            ref={activeClaimId === claim.claim_id ? activeNodeRef : null}
                        />
                    ))}
                </div>

                {/* Fades (Fixed Overlay Siblings - Z-20 forces top) */}
                {/* Left fade */}
                <div className="pointer-events-none absolute left-0 top-0 h-full w-12 bg-gradient-to-r from-white/80 dark:from-neutral-900 to-transparent z-20" />
                {/* Right fade */}
                <div className="pointer-events-none absolute right-0 top-0 h-full w-12 bg-gradient-to-l from-white/80 dark:from-neutral-900 to-transparent z-20" />
            </div>

            {/* 3. Legend (Simplified) */}
            <div className="border-t border-slate-200/60 dark:border-white/10 bg-slate-50/60 dark:bg-neutral-900/60 px-6 py-3 flex justify-center gap-8 transition-colors duration-500">
                <LegendItem color="bg-emerald-600" label="Supported" />
                <LegendItem color="bg-amber-400" label="Uncertain" />
                <LegendItem color="bg-red-500" label="Refuted" />
            </div>
        </div>
    )
}

function ClaimNode({ claim, idx, isActive, onClaimClick, ref }: any) {
    const verdict = (claim.verification?.verdict || "UNCERTAIN") as "SUPPORTED" | "SUPPORTED_WEAK" | "REFUTED" | "UNCERTAIN"

    const colors = {
        SUPPORTED: 'bg-emerald-600 shadow-[0_0_0_6px_rgba(16,185,129,0.1)] dark:shadow-[0_0_0_6px_rgba(16,185,129,0.05)]',
        SUPPORTED_WEAK: 'bg-emerald-600 shadow-[0_0_0_6px_rgba(16,185,129,0.1)] dark:shadow-[0_0_0_6px_rgba(16,185,129,0.05)]',
        REFUTED: 'bg-red-500 shadow-[0_0_0_6px_rgba(239,68,68,0.1)] dark:shadow-[0_0_0_6px_rgba(239,68,68,0.05)]',
        UNCERTAIN: 'bg-amber-400 shadow-[0_0_0_6px_rgba(251,191,36,0.1)] dark:shadow-[0_0_0_6px_rgba(251,191,36,0.05)]'
    }

    const color = colors[verdict] || colors.UNCERTAIN

    return (
        <div className="snap-center flex flex-col items-center gap-3 min-w-[72px] relative z-10">
            <button
                ref={ref}
                onClick={() => onClaimClick(claim.claim_id)}
                className={`
                    w-4 h-4 rounded-full
                    ${color}
                    transition-all duration-300 ease-out
                    hover:scale-110 hover:brightness-110
                    focus:outline-none 
                    ${isActive ? 'scale-125 ring-4 ring-slate-100 dark:ring-white/10 brightness-110' : 'opacity-90'}
                `}
                aria-label={`Select claim ${idx + 1}`}
            />
            <span className={`text-[10px] font-mono transition-colors ${isActive ? 'text-slate-900 dark:text-white font-bold' : 'text-slate-400 dark:text-neutral-500'}`}>
                C{idx + 1}
            </span>

            {/* Active Anchor Pedestal */}
            {isActive && (
                <div className="absolute -bottom-3 w-6 h-px bg-slate-300 dark:bg-white/20 blur-[0.5px] animate-in fade-in duration-500" />
            )}
        </div>
    )
}

function LegendItem({ color, label }: { color: string, label: string }) {
    return (
        <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${color}`} />
            <span className="text-[11px] text-slate-500 dark:text-neutral-400 font-medium">{label}</span>
        </div>
    )
}
