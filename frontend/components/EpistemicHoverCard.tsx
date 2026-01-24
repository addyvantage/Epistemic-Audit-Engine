
import React from 'react'

interface HoverCardProps {
    claim: any
    position: { x: number, y: number }
    visible: boolean
    explainabilityMode?: "CASUAL" | "EXPERT"
}

export function EpistemicHoverCard({ claim, position, visible, explainabilityMode = "CASUAL" }: HoverCardProps) {
    if (!claim) return null

    const isExpert = explainabilityMode === "EXPERT"

    // --- EPISTEMIC ANALYSIS ---
    const verdict = claim.verification?.verdict || "UNCERTAIN"
    const isRefuted = verdict === "REFUTED"
    const isSupported = verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK"
    const isUncertain = !isRefuted && !isSupported

    // Reasoning (Expert vs Casual)
    const rawReasoning = claim.verification?.reasoning
        || claim.analysis?.content
        || "No specific reasoning provided by the engine."

    // Casual transformation (Simple example, can be richer)
    const reasoning = isExpert ? rawReasoning : rawReasoning.replace(/epistemic|polarity|predicate/gi, "claim logic")

    // Evidence
    const sources = claim.verification?.evidence || []
    const hasSources = sources.length > 0

    // --- STYLING LOGIC (v1.6.2 Final Consistency) ---
    let bgClass = "bg-amber-50/83 border-amber-300 shadow-xl"
    let statusColor = "bg-amber-500"
    let headerLabel = isExpert ? "UNCERTAIN / INSUFFICIENT" : "Needs more evidence"
    let accentColor = "bg-amber-500/80"
    let riskFillWidth = '50%'
    let riskLabel = "Moderate Impact"
    let citationTint = "border-amber-400 group-hover:border-amber-500 hover:shadow-[0_0_8px_rgba(245,158,11,0.2)]"

    if (isRefuted) {
        bgClass = "bg-red-50/80 border-red-300 shadow-[0_8px_32px_-4px_rgba(220,38,38,0.12)]"
        statusColor = "bg-red-500"
        headerLabel = isExpert ? "REFUTED" : "Evidence contradicts this"
        accentColor = "bg-red-500/80"
        riskFillWidth = '85%'
        riskLabel = "High Impact"
        citationTint = "border-red-400 group-hover:border-red-500 hover:shadow-[0_0_8px_rgba(220,38,38,0.2)]"
    } else if (isSupported) {
        bgClass = "bg-emerald-50/80 border-emerald-300 shadow-[0_8px_32px_-4px_rgba(5,150,105,0.12)]"
        statusColor = "bg-emerald-500"
        headerLabel = isExpert ? "SUPPORTED" : "Verified"
        accentColor = "bg-emerald-500/80"
        riskFillWidth = '15%'
        riskLabel = "Low Impact"
        citationTint = "border-emerald-400 group-hover:border-emerald-500 hover:shadow-[0_0_8px_rgba(16,185,129,0.2)]"
    }

    // --- ANIMATION DELAYS ---
    const staggerBase = "transition-all duration-500 ease-out"
    const delay1 = visible ? "opacity-100 translate-y-0 delay-75" : "opacity-0 translate-y-1"
    const delay2 = visible ? "opacity-100 translate-y-0 delay-100" : "opacity-0 translate-y-1"
    const delay3 = visible ? "opacity-100 translate-y-0 delay-150" : "opacity-0 translate-y-1"
    const delay4 = visible ? "opacity-100 translate-y-0 delay-200" : "opacity-0 translate-y-1"

    return (
        <div
            role="tooltip"
            className={`fixed z-50 w-80 rounded-2xl border backdrop-blur-xl pointer-events-auto transition-all duration-300 ease-out origin-bottom 
                ${bgClass} 
                ${visible ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-98 translate-y-4'}`}
            style={{
                left: position.x,
                top: position.y - 24,
                transform: `translate(-50%, -100%) ${visible ? 'translateY(0) scale(1)' : 'translateY(12px) scale(0.98)'}`
            }}
        >
            {/* Header */}
            <div className={`px-5 py-4 flex items-center justify-between rounded-t-2xl border-b border-black/5 ${staggerBase} ${delay1}`}>
                <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${statusColor} shadow-[0_0_8px_rgba(0,0,0,0.1)]`} />
                    <div className="flex flex-col">
                        <span className="font-bold font-mono text-[10px] uppercase tracking-[0.2em] opacity-80">{headerLabel}</span>
                        {isExpert && (
                            <span className="text-[9px] opacity-40 font-mono uppercase tracking-[0.1em]">
                                {claim.claim_type} • {claim.epistemic_polarity}
                            </span>
                        )}
                    </div>
                </div>
                {/* Confidence Badge */}
                <div className="flex flex-col items-end">
                    <span className="text-[10px] font-mono font-bold opacity-60">
                        {isSupported || isRefuted ? "VERIFIABLE" : "INDETERMINATE"}
                    </span>
                    {isExpert && claim.verification?.confidence !== undefined && (
                        <span className="text-[9px] opacity-40 font-mono">
                            C: {(claim.verification.confidence * 100).toFixed(0)}%
                        </span>
                    )}
                </div>
            </div>

            <div className="p-6 space-y-6">

                {/* 1. Reasoning */}
                <div className={`${staggerBase} ${delay2}`}>
                    <h4 className="text-[10px] uppercase opacity-40 font-bold tracking-[0.15em] mb-2">{isExpert ? "EPISTEMIC RATIONALE" : "Why this was flagged"}</h4>
                    <p className="text-sm text-slate-900 leading-relaxed font-serif italic opacity-90">
                        {reasoning}
                    </p>
                </div>

                {/* 2. Qualitative Risk Bar */}
                <div className={`${staggerBase} ${delay3}`}>
                    <div className="flex justify-between items-end mb-2">
                        <h4 className="text-[10px] uppercase opacity-40 font-bold tracking-[0.15em]">{isExpert ? "RISK CONTRIBUTION" : "Impact on overall risk"}</h4>
                        <span className="text-[10px] font-bold text-slate-500 tracking-tight">{riskLabel}</span>
                    </div>
                    <div className="h-1.5 w-full bg-black/5 rounded-full overflow-hidden border border-black/5">
                        <div
                            className={`h-full rounded-full ${accentColor} opacity-90 transition-all duration-1000 ease-out`}
                            style={{ width: visible ? riskFillWidth : '0%' }}
                        />
                    </div>
                </div>

                {/* 3. Evidence Snapshot (Semantic Fix v1.6.0) */}
                <div className={`${staggerBase} ${delay4}`}>
                    <h4 className="text-[10px] uppercase opacity-40 font-bold tracking-[0.15em] mb-2">Evidence Snapshot</h4>

                    {hasSources ? (
                        <div className="flex flex-wrap gap-2">
                            {sources.slice(0, 3).map((s: any, idx: number) => (
                                <CitationChip key={idx} source={s} tintClass={citationTint} />
                            ))}
                            {sources.length > 3 && (
                                <span className="text-[9px] opacity-30 font-bold self-center tracking-tighter">+ {sources.length - 3} MORE</span>
                            )}
                        </div>
                    ) : (
                        <div className={`p-4 border rounded-xl flex flex-col items-center justify-center gap-2 ${isSupported ? "bg-emerald-500/5 border-emerald-200" : "bg-amber-500/5 border-dashed border-amber-300"
                            }`}>
                            <p className="text-[11px] font-medium opacity-60 text-center leading-tight">
                                {isSupported
                                    ? (isExpert ? "Verified via structured knowledge graph (canonical predicate match)." : "Verified using authoritative structured records.")
                                    : "No authoritative source could be confidently linked."}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

function CitationChip({ source, tintClass }: { source: any, tintClass: string }) {
    const excerpt = source.snippet || source.text || source.explanation || "No preview text available."
    const cleanExcerpt = excerpt.length > 200 ? excerpt.slice(0, 200) + "..." : excerpt
    const domain = source.source || "Database"

    return (
        <div className="group relative">
            <div className={`cursor-help flex items-center gap-2 px-3 py-1.5 bg-black/5 backdrop-blur-sm border-l-4 rounded-lg transition-all duration-200 ${tintClass}`}>
                <span className="text-[10px] font-bold opacity-80 tracking-tight max-w-[100px] truncate uppercase">{domain}</span>
            </div>

            {/* Preview Panel (v1.6.0 Polish) */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-72 bg-slate-900/95 backdrop-blur-lg text-slate-100 p-4 rounded-xl shadow-2xl opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 group-hover:pointer-events-auto transition-all duration-300 ease-out z-[60] border border-white/10">
                <div className="flex items-center justify-between mb-3 border-b border-white/10 pb-2">
                    <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-400">{domain}</span>
                    {source.url && (
                        <a href={source.url} target="_blank" rel="noreferrer" className="text-[10px] font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
                            VIEW SOURCE ↗
                        </a>
                    )}
                </div>
                <p className="text-[13px] font-serif leading-relaxed opacity-90 indent-4 tracking-tight">
                    "{cleanExcerpt}"
                </p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-6 border-transparent border-t-slate-900/95" />
            </div>
        </div>
    )
}
