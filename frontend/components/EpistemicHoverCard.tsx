import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PREMIUM_EASE } from '@/lib/motion-variants'

// TypeScript Fix for Framer Motion props
const MotionDiv = motion.div as any

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
    const isPartiallySupported = verdict === "PARTIALLY_SUPPORTED"
    // const isUncertain = !isRefuted && !isSupported

    // Reasoning (Expert vs Casual)
    const rawReasoning = claim.verification?.reasoning
        || claim.analysis?.content
        || "No specific reasoning provided by the engine."

    // Casual transformation
    const reasoning = isExpert ? rawReasoning : rawReasoning.replace(/epistemic|polarity|predicate/gi, "claim logic")

    // Evidence Sufficiency (v1.5) - explicit categorization for accurate messaging
    const evidenceSufficiency = claim.verification?.evidence_sufficiency || "ES_ABSENT"
    const evidenceSummary = claim.verification?.evidence_summary || {}

    // Compute if we have used evidence to display as chips
    const usedWikidata = evidenceSummary.wikidata?.used_items || []
    const usedWikipedia = evidenceSummary.wikipedia?.used_items || []
    const usedPrimary = evidenceSummary.primary_document?.used_items || []
    const hasUsedEvidence = usedWikidata.length > 0 || usedWikipedia.length > 0 || usedPrimary.length > 0

    // Track if evidence was retrieved (even if not used)
    const totalRetrieved = (evidenceSummary.wikidata?.total || 0) +
        (evidenceSummary.wikipedia?.total || 0) +
        (evidenceSummary.primary_document?.total || 0)

    // Evidence message based on sufficiency category
    const getEvidenceMessage = () => {
        switch (evidenceSufficiency) {
            case "ES_VERIFIED":
                return isExpert
                    ? "Verified via structured knowledge graph alignment."
                    : "Verified using authoritative records."
            case "ES_CORROBORATED":
                return isExpert
                    ? "Corroborated by textual evidence (NLI entailment)."
                    : "Supported by textual sources."
            case "ES_EVALUATED":
                return isExpert
                    ? "Evidence retrieved but insufficient for verification."
                    : "Evidence found but not conclusive."
            case "ES_ABSENT":
            default:
                return isExpert
                    ? "No relevant evidence retrieved from knowledge sources."
                    : "No matching records found."
        }
    }

    // --- STYLING LOGIC (v1.6.2 Final Consistency) ---
    let bgClass = "bg-amber-50/90 dark:bg-neutral-900/95 border-amber-300 dark:border-white/10 shadow-xl"
    let statusColor = "bg-amber-500"
    let headerLabel = isExpert ? "UNCERTAIN / INSUFFICIENT" : "Needs more evidence"
    let accentColor = "bg-amber-500/80"
    let riskFillWidth = '50%'
    let riskLabel = "Moderate Impact"
    let citationTint = "border-amber-400 group-hover:border-amber-500 hover:shadow-[0_0_8px_rgba(245,158,11,0.2)]"

    if (isRefuted) {
        bgClass = "bg-red-50/90 dark:bg-neutral-900/95 border-red-300 dark:border-white/10 shadow-[0_8px_32px_-4px_rgba(220,38,38,0.12)]"
        statusColor = "bg-red-500"
        headerLabel = isExpert ? "REFUTED" : "Evidence contradicts this"
        accentColor = "bg-red-500/80"
        riskFillWidth = '85%'
        riskLabel = "High Impact"
        citationTint = "border-red-400 group-hover:border-red-500 hover:shadow-[0_0_8px_rgba(220,38,38,0.2)]"
    } else if (isSupported) {
        bgClass = "bg-emerald-50/90 dark:bg-neutral-900/95 border-emerald-300 dark:border-white/10 shadow-[0_8px_32px_-4px_rgba(5,150,105,0.12)]"
        statusColor = "bg-emerald-500"
        headerLabel = isExpert ? "SUPPORTED" : "Supported"
        accentColor = "bg-emerald-500/80"
        riskFillWidth = '15%'
        riskLabel = "Low Impact"
        citationTint = "border-emerald-400 group-hover:border-emerald-500 hover:shadow-[0_0_8px_rgba(16,185,129,0.2)]"
    } else if (isPartiallySupported) {
        bgClass = "bg-teal-50/90 dark:bg-neutral-900/95 border-teal-300 dark:border-white/10 shadow-[0_8px_32px_-4px_rgba(13,148,136,0.12)]"
        statusColor = "bg-teal-500"
        headerLabel = isExpert ? "PARTIALLY_SUPPORTED" : "Partially supported"
        accentColor = "bg-teal-500/80"
        riskFillWidth = '35%'
        riskLabel = "Moderate Impact"
        citationTint = "border-teal-400 group-hover:border-teal-500 hover:shadow-[0_0_8px_rgba(13,148,136,0.2)]"
    }

    // Motion Container Variants
    const containerVariants = {
        hidden: {
            opacity: 0,
            y: 10,
            scale: 0.96,
            transition: { duration: 0.2, ease: PREMIUM_EASE }
        },
        visible: {
            opacity: 1,
            y: 0,
            scale: 1,
            transition: {
                duration: 0.4,
                ease: PREMIUM_EASE,
                staggerChildren: 0.08,
                delayChildren: 0.1
            }
        },
        exit: {
            opacity: 0,
            scale: 0.96,
            transition: { duration: 0.2 }
        }
    }

    const itemVariants = {
        hidden: { opacity: 0, y: 5 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: PREMIUM_EASE } }
    }

    return (
        <AnimatePresence>
            {visible && (
                <div
                    className="fixed z-50 pointer-events-none"
                    style={{
                        left: position.x,
                        top: position.y - 24,
                        transform: 'translate(-50%, -100%)'
                    }}
                >
                    <MotionDiv
                        role="tooltip"
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        className={`w-80 rounded-2xl border backdrop-blur-xl pointer-events-auto origin-bottom overflow-hidden ${bgClass}`}
                    >
                        {/* Header */}
                        <MotionDiv variants={itemVariants} className="px-5 py-4 flex items-center justify-between border-b border-black/5 dark:border-white/10 bg-white/40 dark:bg-white/5">
                            <div className="flex items-center gap-3">
                                <div className={`w-2.5 h-2.5 rounded-full ${statusColor} shadow-sm`} />
                                <div className="flex flex-col">
                                    <span className="font-bold font-mono text-[10px] uppercase tracking-[0.2em] opacity-80 text-slate-800 dark:text-neutral-200">{headerLabel}</span>
                                    {isExpert && (
                                        <span className="text-[9px] opacity-50 font-mono uppercase tracking-[0.1em] text-slate-600 dark:text-neutral-400">
                                            {claim.claim_type} • {claim.epistemic_polarity}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex flex-col items-end">
                                <span className="text-[10px] font-mono font-bold opacity-60 text-slate-700 dark:text-neutral-300">
                                    {isSupported || isRefuted || isPartiallySupported ? "VERIFIABLE" : "INDETERMINATE"}
                                </span>
                                {isExpert && claim.verification?.confidence !== undefined && (
                                    <span className="text-[9px] opacity-40 font-mono text-slate-500 dark:text-neutral-400">
                                        C: {(claim.verification.confidence * 100).toFixed(0)}%
                                    </span>
                                )}
                            </div>
                        </MotionDiv>

                        <div className="p-6 space-y-6">
                            {/* 1. Reasoning */}
                            <MotionDiv variants={itemVariants}>
                                <h4 className="text-[10px] uppercase opacity-50 font-bold tracking-[0.15em] mb-2 text-slate-900 dark:text-neutral-400">{isExpert ? "EPISTEMIC RATIONALE" : "Why this was flagged"}</h4>
                                <p className="text-sm text-slate-800 dark:text-neutral-200 leading-relaxed font-serif italic">
                                    {reasoning}
                                </p>
                            </MotionDiv>

                            {/* 2. Qualitative Risk Bar */}
                            <MotionDiv variants={itemVariants}>
                                <div className="flex justify-between items-end mb-2">
                                    <h4 className="text-[10px] uppercase opacity-50 font-bold tracking-[0.15em] text-slate-900 dark:text-neutral-400">{isExpert ? "RISK CONTRIBUTION" : "Impact on overall risk"}</h4>
                                    <span className="text-[10px] font-bold text-slate-600 dark:text-neutral-400 tracking-tight">{riskLabel}</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-200/50 dark:bg-white/10 rounded-full overflow-hidden border border-black/5 dark:border-transparent">
                                    <MotionDiv
                                        initial={{ width: 0 }}
                                        animate={{ width: riskFillWidth }}
                                        transition={{ duration: 0.8, ease: PREMIUM_EASE, delay: 0.2 }}
                                        className={`h-full rounded-full ${accentColor}`}
                                    />
                                </div>
                            </MotionDiv>

                            {/* 3. Evidence Snapshot */}
                            <MotionDiv variants={itemVariants}>
                                <h4 className="text-[10px] uppercase font-bold tracking-[0.15em] mb-2 text-slate-500 dark:text-neutral-400 opacity-100">Evidence Snapshot</h4>

                                {hasUsedEvidence ? (
                                    <div className="flex flex-wrap gap-2">
                                        {/* Show primary documents first (highest authority) */}
                                        {usedPrimary.slice(0, 2).map((s: any, idx: number) => (
                                            <CitationChip key={`pd-${idx}`} source={{...s, source: s.authority || "PRIMARY"}} tintClass={citationTint} />
                                        ))}
                                        {/* Then Wikidata */}
                                        {usedWikidata.slice(0, 2).map((s: any, idx: number) => (
                                            <CitationChip key={`wd-${idx}`} source={{...s, source: "Wikidata"}} tintClass={citationTint} />
                                        ))}
                                        {/* Then Wikipedia */}
                                        {usedWikipedia.slice(0, 2).map((s: any, idx: number) => (
                                            <CitationChip key={`wp-${idx}`} source={{...s, source: "Wikipedia"}} tintClass={citationTint} />
                                        ))}
                                        {/* Show count for additional sources */}
                                        {(() => {
                                            const totalUsed = usedPrimary.length + usedWikidata.length + usedWikipedia.length
                                            const shown = Math.min(2, usedPrimary.length) + Math.min(2, usedWikidata.length) + Math.min(2, usedWikipedia.length)
                                            if (totalUsed > shown) {
                                                return <span className="text-[9px] opacity-30 font-bold self-center tracking-tighter text-slate-500 dark:text-neutral-400">+ {totalUsed - shown} MORE</span>
                                            }
                                            return null
                                        })()}
                                    </div>
                                ) : (
                                    <div className={`p-4 rounded-xl border border-dashed backdrop-blur-xl shadow-sm transition-colors duration-300
                                        ${evidenceSufficiency === "ES_EVALUATED"
                                            ? "bg-amber-50/50 dark:bg-amber-900/10 border-amber-300 dark:border-amber-500/30"
                                            : isSupported
                                                ? "bg-emerald-50/70 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-500/30"
                                                : "bg-slate-100/70 dark:bg-neutral-900/30 border-slate-300 dark:border-white/10"
                                        }`}>
                                        <p className="text-[13px] font-medium leading-relaxed text-center text-slate-600 dark:text-neutral-400">
                                            {getEvidenceMessage()}
                                        </p>
                                        {/* Show retrieved count when evidence exists but wasn't sufficient */}
                                        {evidenceSufficiency === "ES_EVALUATED" && totalRetrieved > 0 && (
                                            <p className="text-[10px] mt-2 text-center text-amber-600 dark:text-amber-400 opacity-70">
                                                {evidenceSummary.wikipedia?.total || 0} passages reviewed, {evidenceSummary.wikidata?.total || 0} structured records checked
                                            </p>
                                        )}
                                    </div>
                                )}
                            </MotionDiv>
                        </div>
                    </MotionDiv>
                </div>
            )}
        </AnimatePresence>
    )
}

function CitationChip({ source, tintClass }: { source: any, tintClass: string }) {
    const excerpt = source.snippet || source.text || source.explanation || "No preview text available."
    const cleanExcerpt = excerpt.length > 200 ? excerpt.slice(0, 200) + "..." : excerpt
    const domain = source.source || "Database" || "Source"

    return (
        <div className="group relative">
            <div className={`cursor-help flex items-center gap-2 px-3 py-1.5 bg-black/5 dark:bg-white/5 backdrop-blur-sm border-l-2 rounded-md transition-all duration-200 ${tintClass}`}>
                <span className="text-[10px] font-bold opacity-80 tracking-tight max-w-[100px] truncate uppercase text-slate-700 dark:text-neutral-300">{domain}</span>
            </div>

            {/* Preview Panel */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-72 bg-slate-900 dark:bg-black text-slate-100 p-4 rounded-xl shadow-2xl opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 group-hover:pointer-events-auto transition-all duration-300 ease-out z-[60] border border-white/10">
                <div className="flex items-center justify-between mb-3 border-b border-white/10 pb-2">
                    <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-400">{domain}</span>
                    {source.url && (
                        <a href={source.url} target="_blank" rel="noreferrer" className="text-[10px] font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
                            OPEN ↗
                        </a>
                    )}
                </div>
                <p className="text-[12px] font-serif leading-relaxed opacity-90 indent-0 tracking-wide text-slate-300">
                    "{cleanExcerpt}"
                </p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-[6px] border-transparent border-t-slate-900 dark:border-t-black" />
            </div>
        </div>
    )
}
