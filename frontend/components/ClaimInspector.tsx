"use client"

import { ExternalLink, ShieldCheck, AlertTriangle, XCircle } from "lucide-react"
import { motion } from "framer-motion"
import { PREMIUM_EASE } from "@/lib/motion-variants"

// TypeScript Fix for Framer Motion
const MotionAside = motion.aside as any

type Props = {
    claim: any
    onClose: () => void
    mode?: "DEMO" | "RESEARCH"
}

const verdictStyles: Record<string, any> = {
    SUPPORTED: {
        bg: "bg-emerald-50 dark:bg-emerald-950/30",
        border: "border-emerald-200 dark:border-emerald-500/20",
        text: "text-emerald-900 dark:text-emerald-100",
        icon: ShieldCheck,
        label: "Supported",
        description: "Supported by authoritative sources."
    },
    REFUTED: {
        bg: "bg-rose-50 dark:bg-rose-950/30",
        border: "border-rose-200 dark:border-rose-500/20",
        text: "text-rose-900 dark:text-rose-100",
        icon: XCircle,
        label: "Refuted",
        description: "Contradicted by authoritative sources."
    },
    INSUFFICIENT_EVIDENCE: {
        bg: "bg-amber-50 dark:bg-amber-950/30",
        border: "border-amber-200 dark:border-amber-500/20",
        text: "text-amber-900 dark:text-amber-100",
        icon: AlertTriangle,
        label: "Insufficient Evidence",
        description: "No conclusive evidence found in knowledge graph."
    },
    SUPPORTED_WEAK: {
        bg: "bg-teal-50 dark:bg-teal-950/30",
        border: "border-teal-100 dark:border-teal-500/20",
        text: "text-teal-900 dark:text-teal-100",
        icon: ShieldCheck,
        label: "Weakly Supported",
        description: "Partially supported by available sources."
    }
}

export function ClaimInspector({ claim, onClose, mode = "DEMO" }: Props) {
    const verdict = claim.verification?.verdict || "INSUFFICIENT_EVIDENCE"
    const confidence = claim.verification?.confidence ?? 0
    const style = verdictStyles[verdict] || verdictStyles.INSUFFICIENT_EVIDENCE
    const Icon = style.icon

    // PRIMARY DOCUMENTS (Priority 1)
    const primaryDocs = (claim.evidence?.primary_document || []).map((e: any) => ({
        label: `PRIMARY DOCUMENT — ${e.authority || 'SEC'} ${e.document_type || 'Filing'} (${e.filing_year || ''})`,
        fact: e.fact,
        value: e.value,
        snippet: e.snippet,
        source: "SEC"
    }))

    // NORMALIZATION LOGIC
    // Structured (Priority 2)
    const structuredSources = (claim.evidence?.wikidata || []).map((e: any) => ({
        label: e.property?.replace(/P\d+/, '').trim() || "Property Match",
        value: String(e.value),
        url: e.source_url
    })).slice(0, 3)

    // Combined narrative sources (Priority 3)
    const narrativeSources = (claim.evidence?.wikipedia || []).map((e: any) => ({
        title: "Wikipedia Article",
        snippet: e.snippet,
        url: e.url
    })).concat((claim.evidence?.grokipedia || []).map((e: any) => ({
        title: "Narrative Context",
        snippet: e.text,
        url: null
    }))).slice(0, 3)

    const hasEvidence = primaryDocs.length > 0 || structuredSources.length > 0 || narrativeSources.length > 0

    // Evidence Sufficiency (v1.5) - for accurate messaging
    const evidenceSufficiency = claim.verification?.evidence_sufficiency || "ES_ABSENT"

    // TEMPLATED REASONING - Updated for evidence sufficiency awareness
    const reasoning = {
        SUPPORTED: primaryDocs.length > 0
            ? "This claim is supported by primary documents with high confidence."
            : evidenceSufficiency === "ES_VERIFIED"
                ? "This claim is verified via structured knowledge graph alignment."
                : "This claim is corroborated by textual evidence.",
        REFUTED: `This claim is refuted because it contradicts authoritative records${primaryDocs.length > 0 ? ' from primary documents' : ''}.`,
        INSUFFICIENT_EVIDENCE: evidenceSufficiency === "ES_EVALUATED"
            ? "Evidence was retrieved but did not meet verification thresholds."
            : "No matching records were found in the connected knowledge bases.",
        UNCERTAIN: evidenceSufficiency === "ES_EVALUATED"
            ? "Evidence suggests partial support but lacks sufficient corroboration."
            : "Unable to reach a conclusive verdict with available evidence."
    }[verdict as string] || "Evidence analysis inconclusive."

    return (
        <MotionAside
            initial={{ x: "100%", opacity: 0.5 }}
            animate={{ x: "0%", opacity: 1 }}
            exit={{ x: "100%", opacity: 0, transition: { duration: 0.3, ease: PREMIUM_EASE } }}
            transition={{ duration: 0.5, ease: PREMIUM_EASE }}
            className="fixed right-0 top-0 h-full w-[420px] bg-white/95 dark:bg-[#0A0A0A]/95 backdrop-blur-3xl border-l border-slate-200 dark:border-white/5 shadow-2xl z-50 overflow-y-auto font-sans flex flex-col"
        >

            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 dark:border-white/5 bg-white/50 dark:bg-white/5 backdrop-blur-md sticky top-0 z-20">
                <h2 className="text-[10px] font-mono uppercase tracking-widest text-slate-400 dark:text-neutral-500 font-semibold">
                    Epistemic Verification
                </h2>
                <button onClick={onClose} className="text-slate-400 dark:text-neutral-500 hover:text-slate-900 dark:hover:text-neutral-200 transition-colors p-1 hover:bg-slate-100 dark:hover:bg-white/5 rounded-full">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto pb-10">
                {/* Hallucination Alerts (v1.1) */}
                {claim.hallucinations && claim.hallucinations.length > 0 && (
                    <div className="px-6 pt-6 pb-2">
                        {claim.hallucinations.map((h: any, i: number) => (
                            <div key={i} className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-500/20 rounded p-3 flex flex-col gap-1 mb-2">
                                <div className="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wide flex items-center gap-2">
                                    <AlertTriangle className="w-3 h-3" />
                                    {h.hallucination_type ? h.hallucination_type.replace(/_/g, " ") : "Hallucination Detected"}
                                </div>
                                <div className="text-sm text-rose-800 dark:text-rose-200 leading-tight font-medium">
                                    {h.reason}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* 1. Verdict (Forensic Label) */}
                <div className="px-6 pt-2">
                    <div className={`p-4 rounded-lg border ${style.bg} ${style.border} flex items-start gap-3 mb-6`}>
                        <Icon className={`w-5 h-5 shrink-0 ${style.text} mt-0.5`} />
                        <div>
                            <div className={`font-bold text-sm ${style.text} mb-1`}>{style.label}</div>
                            <div className="text-xs text-slate-600 dark:text-neutral-400 leading-relaxed font-mono opacity-80">
                                Confidence: {(confidence * 100).toFixed(0)}%
                            </div>
                        </div>
                    </div>

                    {/* 2. Quoted Claim */}
                    <blockquote className="text-lg font-medium text-slate-800 dark:text-neutral-200 leading-relaxed border-l-4 border-slate-200 dark:border-white/10 pl-4 mb-2 italic">
                        “{claim.claim_text}”
                    </blockquote>
                </div>

                <div className="w-full h-px bg-slate-100 dark:bg-white/5 my-6" />

                {/* 3. Analysis */}
                <div className="px-6">
                    <h3 className="text-xs font-bold text-slate-900 dark:text-neutral-100 mb-2 uppercase tracking-wide">Analysis</h3>
                    <p className="text-sm text-slate-600 dark:text-neutral-400 leading-relaxed">
                        {reasoning}
                    </p>
                </div>

                <div className="w-full h-px bg-slate-100 dark:bg-white/5 my-6" />

                {/* 4. Evidence Sources */}
                <div className="px-6">
                    <h3 className="text-xs font-bold text-slate-900 dark:text-neutral-100 mb-4 flex items-center justify-between uppercase tracking-wide">
                        <span>Evidence Sources</span>
                        {hasEvidence && <span className="text-[10px] font-normal text-slate-400 dark:text-neutral-500">{primaryDocs.length + structuredSources.length + narrativeSources.length} Records</span>}
                    </h3>

                    {!hasEvidence && (
                        <div className={`text-sm italic p-4 rounded-lg text-center border cursor-default ${evidenceSufficiency === "ES_EVALUATED"
                                ? "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-500/30"
                                : "text-slate-400 dark:text-neutral-500 bg-slate-50 dark:bg-white/5 border-slate-100 dark:border-white/5"
                            }`}>
                            {evidenceSufficiency === "ES_EVALUATED"
                                ? "Evidence retrieved but insufficient for verification."
                                : "No authoritative records linked."}
                        </div>
                    )}

                    <div className="space-y-6">
                        {/* PRIMARY DOCUMENT BLOCK */}
                        {primaryDocs.length > 0 && (
                            <div className="space-y-3">
                                <div className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 uppercase font-bold flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-indigo-600 dark:bg-indigo-400 animate-pulse" />
                                    Primary Documents
                                </div>
                                {primaryDocs.map((s: any, i: number) => (
                                    <div key={i} className="bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-500/30 rounded-lg p-4 shadow-sm relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 p-2 opacity-5 dark:opacity-[0.03] font-bold text-6xl text-indigo-900 dark:text-indigo-100 select-none z-0 group-hover:scale-110 transition-transform duration-700 ease-out">SEC</div>
                                        <div className="relative z-10">
                                            <div className="text-xs font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wide mb-2 border-b border-indigo-200 dark:border-indigo-500/30 pb-2">{s.label}</div>

                                            <div className="flex justify-between items-baseline mb-2">
                                                <span className="text-xs text-indigo-700 dark:text-indigo-300 font-semibold uppercase">{s.fact}</span>
                                                <span className="text-lg font-bold text-indigo-900 dark:text-indigo-100">{s.value}</span>
                                            </div>

                                            {s.snippet && (
                                                <div className="text-xs text-indigo-800 dark:text-indigo-200 italic leading-relaxed bg-white/60 dark:bg-black/20 p-2 rounded border border-indigo-100 dark:border-indigo-500/10">
                                                    “{s.snippet}”
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Structured Evidence Block */}
                        {structuredSources.length > 0 && (
                            <div className="space-y-3">
                                <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Structured Knowledge Graph</div>
                                {structuredSources.map((s: any, i: number) => (
                                    <div key={i} className="bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5 rounded p-3">
                                        <div className="text-xs font-semibold text-slate-700 dark:text-neutral-400 uppercase tracking-wide mb-1">{s.label}</div>
                                        <div className="text-sm text-slate-900 dark:text-neutral-200 font-medium mb-1 line-clamp-2">
                                            <span className="bg-yellow-100 dark:bg-yellow-900/30 px-1 rounded box-decoration-clone leading-relaxed text-slate-900 dark:text-yellow-100">{s.value}</span>
                                        </div>
                                        {s.url && (
                                            <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-slate-400 dark:text-neutral-500 hover:text-slate-600 dark:hover:text-neutral-300 flex items-center gap-1 mt-1">
                                                KB Record <ExternalLink className="w-2.5 h-2.5" />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Narrative Evidence Block */}
                        {narrativeSources.length > 0 && (
                            <div className="space-y-3">
                                <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Narrative Corpal Evidence</div>
                                {narrativeSources.map((s: any, i: number) => (
                                    <div key={i + 10} className="bg-white dark:bg-neutral-900/60 border border-slate-200 dark:border-white/10 rounded p-3 shadow-sm">
                                        <div className="text-xs font-semibold text-slate-700 dark:text-neutral-400 uppercase tracking-wide mb-2">{s.title}</div>

                                        {/* Highlighted Snippet - Marker Style */}
                                        <div className="text-sm text-slate-800 dark:text-neutral-300 leading-relaxed mb-2">
                                            <span className="bg-yellow-100 dark:bg-yellow-900/20 px-1 rounded box-decoration-clone leading-[1.6] text-slate-900 dark:text-neutral-200">
                                                “{s.snippet
                                                    ? s.snippet
                                                    : "Supported by structured records; no narrative passage available."}”
                                            </span>
                                        </div>

                                        {s.url && (
                                            <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                                                View Source <ExternalLink className="w-2.5 h-2.5" />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* 5. Research Flags (Mode Dependent) */}
                {mode === "RESEARCH" && (
                    <>
                        <div className="w-full h-px bg-slate-100 my-6" />
                        <div className="px-6 pb-6">
                            <div className="text-[10px] font-mono text-red-400 mb-3 uppercase tracking-widest font-bold">Research Flags</div>
                            <div className="space-y-2">
                                {claim.hallucinations?.map((h: any, i: number) => (
                                    <div key={i} className="p-2 bg-red-50 border border-red-100 rounded text-xs text-red-800 font-mono">
                                        <strong>[{h.hallucination_type}]</strong> {h.reason}
                                    </div>
                                ))}
                                {!claim.hallucinations?.length && <div className="text-xs text-slate-400 italic">No flags detected.</div>}
                                <div className="mt-2 text-xs text-slate-500 font-mono">Polarity: {claim.epistemic_polarity}</div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </MotionAside>
    )
}
