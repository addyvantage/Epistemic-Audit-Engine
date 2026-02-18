"use client"

import React, { useMemo } from "react"
import { AlertTriangle, CheckCircle2, ExternalLink, X, XCircle } from "lucide-react"

type Props = {
    claim: any | null
    onClose?: () => void
    className?: string
}

type EvidenceItem = {
    id: string
    title: string
    snippet: string
    explanation: string
    url?: string
    source: "primary_document" | "wikidata" | "wikipedia" | "grokipedia"
    score: number
    value?: string
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

const WIKIDATA_LABELS: Record<string, string> = {
    P159: "Headquarters",
    P131: "Administrative Area",
    P276: "Location",
    P17: "Country",
    P169: "CEO",
    P112: "Founder",
    P749: "Parent Organization",
    P355: "Subsidiary",
    P127: "Owned By",
    P571: "Inception",
    P569: "Date of Birth",
    P570: "Date of Death",
}

function EvidenceCard({ item }: { item: EvidenceItem }) {
    return (
        <div className="rounded-lg border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.02] p-3 space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">{item.title}</div>
            {item.value ? <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{item.value}</div> : null}
            <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">{item.snippet || "No narrative snippet found"}</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">Explanation: {item.explanation}</p>
            {item.url ? (
                <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-sky-600 dark:text-sky-400"
                >
                    Source <ExternalLink className="w-3 h-3" />
                </a>
            ) : null}
        </div>
    )
}

function normalizeEvidence(claim: any): EvidenceItem[] {
    const verification = claim?.verification || {}
    const verdict = verification.verdict || "UNCERTAIN"
    const usedEvidenceIds = new Set<string>(verification.used_evidence_ids || [])
    const contradictedBy = new Set<string>(verification.contradicted_by || [])

    const primary = (claim?.evidence?.primary_document || []).map((item: any, idx: number): EvidenceItem => {
        const id = item.evidence_id || `primary-${idx}`
        return {
            id,
            title: `Primary Document ${item.document_type || ""}`.trim(),
            snippet: item.snippet || "No narrative snippet found",
            explanation: contradictedBy.has(id)
                ? "This primary record conflicts with the claim."
                : "This primary record provides direct supporting context.",
            source: "primary_document",
            score: item.score || 0,
            value: item.value,
            url: item.url,
        }
    })

    const wikidata = (claim?.evidence?.wikidata || []).map((item: any, idx: number): EvidenceItem => {
        const id = item.evidence_id || `wikidata-${idx}`
        const property = item.property || ""
        const propLabel = WIKIDATA_LABELS[property] || property || "Wikidata"
        return {
            id,
            title: `Wikidata ${propLabel}`,
            snippet: item.snippet || "No narrative snippet found",
            explanation: contradictedBy.has(id)
                ? `Structured record contradicts the claim for ${propLabel.toLowerCase()}.`
                : usedEvidenceIds.has(id)
                    ? `Structured record supports the claim for ${propLabel.toLowerCase()}.`
                    : `Related structured record for ${propLabel.toLowerCase()}.`,
            source: "wikidata",
            score: item.score || 0,
            value: String(item.value ?? ""),
            url: item.url,
        }
    })

    const wikipedia = (claim?.evidence?.wikipedia || []).map((item: any, idx: number): EvidenceItem => {
        const id = item.evidence_id || `wikipedia-${idx}`
        const snippet = item.snippet || item.sentence || "No narrative snippet found"
        return {
            id,
            title: "Wikipedia",
            snippet,
            explanation:
                item.explanation ||
                (contradictedBy.has(id)
                    ? "Narrative sentence indicates a conflicting fact."
                    : "Narrative sentence provides contextual evidence for this claim."),
            source: "wikipedia",
            score: item.score || 0,
            url: item.url,
        }
    })

    const grokipedia = (claim?.evidence?.grokipedia || []).map((item: any, idx: number): EvidenceItem => {
        const id = item.evidence_id || `grokipedia-${idx}`
        return {
            id,
            title: "Grokipedia",
            snippet: item.snippet || item.text || item.excerpt || "No narrative snippet found",
            explanation: "Supplementary narrative context.",
            source: "grokipedia",
            score: item.score || 0,
            url: item.url,
        }
    })

    const combined: EvidenceItem[] = [...primary, ...wikidata, ...wikipedia, ...grokipedia]

    const sourcePrioritySupported: Record<EvidenceItem["source"], number> = {
        primary_document: 0,
        wikidata: 1,
        wikipedia: 2,
        grokipedia: 3,
    }

    const sourcePriorityRefuted: Record<EvidenceItem["source"], number> = {
        wikidata: 0,
        wikipedia: 1,
        primary_document: 2,
        grokipedia: 3,
    }

    combined.sort((a: EvidenceItem, b: EvidenceItem) => {
        const aRef = contradictedBy.has(a.id) ? 1 : 0
        const bRef = contradictedBy.has(b.id) ? 1 : 0
        const aSup = usedEvidenceIds.has(a.id) ? 1 : 0
        const bSup = usedEvidenceIds.has(b.id) ? 1 : 0

        if (verdict === "REFUTED") {
            if (aRef !== bRef) return bRef - aRef
            if (sourcePriorityRefuted[a.source] !== sourcePriorityRefuted[b.source]) {
                return sourcePriorityRefuted[a.source] - sourcePriorityRefuted[b.source]
            }
            return b.score - a.score
        }

        if (verdict === "SUPPORTED" || verdict === "SUPPORTED_WEAK") {
            if (aSup !== bSup) return bSup - aSup
            if (sourcePrioritySupported[a.source] !== sourcePrioritySupported[b.source]) {
                return sourcePrioritySupported[a.source] - sourcePrioritySupported[b.source]
            }
            return b.score - a.score
        }

        if (sourcePrioritySupported[a.source] !== sourcePrioritySupported[b.source]) {
            return sourcePrioritySupported[a.source] - sourcePrioritySupported[b.source]
        }
        return b.score - a.score
    })

    return combined
}

export function ClaimInspectorPanel({ claim, onClose, className = "" }: Props) {
    if (!claim) {
        return (
            <aside className={`rounded-2xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.02] backdrop-blur-sm p-6 min-h-[420px] ${className}`.trim()}>
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

    const contradictedBy: string[] = claim.verification?.contradicted_by || []
    const hallucinations = claim.hallucinations || []

    const evidenceItems = useMemo(() => normalizeEvidence(claim), [claim])

    return (
        <aside className={`rounded-2xl border border-slate-200 dark:border-white/10 bg-white/95 dark:bg-[#0A0A0A]/95 backdrop-blur-sm p-5 lg:p-6 space-y-5 overflow-y-auto ${className}`.trim()}>
            <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Epistemic Verification</h3>
                <div className="flex items-center gap-2">
                    <div className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${style.chip}`}>
                        <VerdictIcon className="w-3.5 h-3.5" />
                        {style.label}
                    </div>
                    {onClose ? (
                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-full p-1.5 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-white/10"
                            aria-label="Close claim inspector"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    ) : null}
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
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">Hallucination Flags</div>
                    {hallucinations.map((flag: any, index: number) => (
                        <div key={`${flag.hallucination_type}-${index}`} className="rounded-lg border border-rose-200 dark:border-rose-700/50 bg-rose-50 dark:bg-rose-900/20 p-3">
                            <div className="text-xs font-semibold text-rose-700 dark:text-rose-300">{flag.hallucination_type || "Hallucination"}</div>
                            <div className="text-xs text-rose-700/90 dark:text-rose-200/90 mt-1">{flag.reason}</div>
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
                    {evidenceItems.map((item) => (
                        <EvidenceCard key={item.id} item={item} />
                    ))}
                    {evidenceItems.length === 0 ? (
                        <p className="text-xs text-slate-500 dark:text-slate-400">No evidence items available.</p>
                    ) : null}
                </div>
            </details>
        </aside>
    )
}
