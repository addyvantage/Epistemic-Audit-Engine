"use client"

import React from "react"
import { AlertTriangle, CheckCircle2, ExternalLink, XCircle } from "lucide-react"

type Props = {
    claim: any | null
}

const verdictStyles: Record<string, { label: string; chip: string; icon: any }> = {
    SUPPORTED: {
        label: "Supported",
        chip: "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/50",
        icon: CheckCircle2,
    },
    SUPPORTED_WEAK: {
        label: "Weakly Supported",
        chip: "bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-700/50",
        icon: CheckCircle2,
    },
    REFUTED: {
        label: "Refuted",
        chip: "bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-700/50",
        icon: XCircle,
    },
    INSUFFICIENT_EVIDENCE: {
        label: "Insufficient Evidence",
        chip: "bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700/50",
        icon: AlertTriangle,
    },
    UNCERTAIN: {
        label: "Uncertain",
        chip: "bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700/50",
        icon: AlertTriangle,
    },
}

function EvidenceCard({ title, snippet, value, url }: { title: string; snippet?: string; value?: string; url?: string }) {
    return (
        <div className="rounded-lg border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.02] p-3">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">{title}</div>
            {value ? <div className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-1">{value}</div> : null}
            {snippet ? <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{snippet}</p> : null}
            {url ? (
                <a href={url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1 text-[11px] text-sky-600 dark:text-sky-400">
                    Source <ExternalLink className="w-3 h-3" />
                </a>
            ) : null}
        </div>
    )
}

export function ClaimInspectorPanel({ claim }: Props) {
    if (!claim) {
        return (
            <aside className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.02] backdrop-blur-sm p-6 min-h-[420px]">
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">Claim Inspector</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Select a highlighted claim to inspect evidence.
                </p>
            </aside>
        )
    }

    const verdict = claim.verification?.verdict || "UNCERTAIN"
    const confidence = Number(claim.verification?.confidence ?? 0)
    const style = verdictStyles[verdict] || verdictStyles.UNCERTAIN
    const VerdictIcon = style.icon

    const primary = claim.evidence?.primary_document || []
    const wikidata = claim.evidence?.wikidata || []
    const wikipedia = claim.evidence?.wikipedia || []
    const grokipedia = claim.evidence?.grokipedia || []

    const contradictedBy: string[] = claim.verification?.contradicted_by || []
    const hallucinations = claim.hallucinations || []

    return (
        <aside className="rounded-2xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.02] backdrop-blur-sm p-5 lg:p-6 space-y-5 lg:sticky lg:top-24">
            <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Claim Inspector</h3>
                <div className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${style.chip}`}>
                    <VerdictIcon className="w-3.5 h-3.5" />
                    {style.label}
                </div>
            </div>

            <div className="rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50/70 dark:bg-black/20 p-4">
                <p className="text-sm leading-relaxed text-slate-800 dark:text-slate-100">{claim.claim_text}</p>
                <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    Confidence: {(confidence * 100).toFixed(0)}%
                </div>
            </div>

            {hallucinations.length > 0 ? (
                <div className="space-y-2">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">Flags</div>
                    {hallucinations.map((h: any, i: number) => (
                        <div key={`${h.hallucination_type}-${i}`} className="rounded-lg border border-rose-200 dark:border-rose-700/50 bg-rose-50 dark:bg-rose-900/20 p-3">
                            <div className="text-xs font-semibold text-rose-700 dark:text-rose-300">{h.hallucination_type || "Hallucination"}</div>
                            <div className="text-xs text-rose-700/90 dark:text-rose-200/90 mt-1">{h.reason}</div>
                        </div>
                    ))}
                </div>
            ) : null}

            {contradictedBy.length > 0 ? (
                <div>
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Contradicted By</div>
                    <div className="flex flex-wrap gap-2">
                        {contradictedBy.map((id) => (
                            <span key={id} className="rounded-md bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 px-2 py-1 text-[11px] font-mono">
                                {id}
                            </span>
                        ))}
                    </div>
                </div>
            ) : null}

            <details open className="space-y-3">
                <summary className="cursor-pointer text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">Evidence</summary>
                <div className="space-y-2">
                    {primary.map((e: any, i: number) => (
                        <EvidenceCard
                            key={`primary-${i}`}
                            title={`Primary Document ${e.document_type || ""}`.trim()}
                            value={e.value}
                            snippet={e.snippet}
                        />
                    ))}
                    {wikidata.map((e: any, i: number) => (
                        <EvidenceCard
                            key={`wikidata-${i}`}
                            title={`Wikidata ${e.property || ""}`.trim()}
                            value={String(e.value ?? "")}
                            snippet={e.snippet}
                            url={e.url}
                        />
                    ))}
                    {wikipedia.map((e: any, i: number) => (
                        <EvidenceCard
                            key={`wikipedia-${i}`}
                            title="Wikipedia"
                            snippet={e.snippet || e.sentence}
                            url={e.url}
                        />
                    ))}
                    {grokipedia.map((e: any, i: number) => (
                        <EvidenceCard
                            key={`grokipedia-${i}`}
                            title="Grokipedia"
                            snippet={e.snippet || e.text || e.excerpt}
                            url={e.url}
                        />
                    ))}
                    {primary.length + wikidata.length + wikipedia.length + grokipedia.length === 0 ? (
                        <p className="text-xs text-slate-500 dark:text-slate-400">No evidence items available.</p>
                    ) : null}
                </div>
            </details>
        </aside>
    )
}
