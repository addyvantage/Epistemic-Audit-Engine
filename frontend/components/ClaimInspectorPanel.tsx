"use client"

import React, { useEffect, useMemo, useState } from "react"
import { AlertTriangle, CheckCircle2, ExternalLink, X, XCircle } from "lucide-react"

type Props = {
    claim: any | null
    onClose?: () => void
    className?: string
    explainabilityMode?: "CASUAL" | "EXPERT"
}

type EvidenceItem = {
    reactKey: string
    evidenceId?: string
    title: string
    snippet: string
    explanation: string
    url?: string
    source: "primary_document" | "wikidata" | "wikipedia" | "grokipedia"
    score: number
    value?: string
    badges: string[]
}

type DisplayVerdict = "SUPPORTED" | "PARTIALLY_SUPPORTED" | "REFUTED" | "UNCERTAIN"
type InspectorTab = "VERDICT" | "EVIDENCE" | "DEBUG"

const verdictStyles: Record<DisplayVerdict, { label: string; chip: string; icon: any }> = {
    SUPPORTED: {
        label: "Supported",
        chip: "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/50",
        icon: CheckCircle2,
    },
    PARTIALLY_SUPPORTED: {
        label: "Partially supported",
        chip: "bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-700/50",
        icon: AlertTriangle,
    },
    REFUTED: {
        label: "Refuted",
        chip: "bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-700/50",
        icon: XCircle,
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

const FACET_LABELS: Record<string, string> = {
    INCEPTION: "Inception / Founded",
    HQ: "Headquarters",
    NONPROFIT: "Non-profit status",
    NATIONALITY: "Nationality",
    OWNERSHIP: "Ownership",
    TEMPORAL_GENERIC: "Temporal detail",
}

function EvidenceCard({ item }: { item: EvidenceItem }) {
    return (
        <article className="rounded-lg border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.02] p-3 space-y-2.5">
            <div className="flex items-center justify-between gap-2">
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">{item.title}</div>
                <div className="flex items-center gap-1 flex-wrap justify-end">
                    {item.badges.map((badge) => (
                        <span
                            key={`${item.reactKey}-${badge}`}
                            className="px-1.5 py-0.5 rounded border border-slate-200 dark:border-white/10 text-[10px] text-slate-500 dark:text-slate-400"
                        >
                            {badge}
                        </span>
                    ))}
                </div>
            </div>
            {item.value ? <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{item.value}</div> : null}
            <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">{item.snippet || "No narrative snippet found"}</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">{item.explanation}</p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed">Evidence ID: {item.evidenceId || "missing evidence_id"}</p>
            {item.url ? (
                <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-sky-600 dark:text-sky-400"
                >
                    Open source <ExternalLink className="w-3 h-3" />
                </a>
            ) : null}
        </article>
    )
}

function dedupeEvidence(items: EvidenceItem[]): EvidenceItem[] {
    const byEvidenceId = new Map<string, EvidenceItem>()
    const withoutId: EvidenceItem[] = []

    for (const item of items) {
        if (!item.evidenceId) {
            withoutId.push(item)
            continue
        }
        if (!byEvidenceId.has(item.evidenceId)) {
            byEvidenceId.set(item.evidenceId, item)
        }
    }

    return [...Array.from(byEvidenceId.values()), ...withoutId]
}

function alignmentBadges(alignment: any): string[] {
    if (!alignment) return []
    const badges: string[] = []
    if (alignment.subject_match === true) badges.push("subject")
    if (alignment.predicate_match === true) badges.push("predicate")
    if (alignment.object_match === true) badges.push("object")
    if (alignment.temporal_match === true) badges.push("temporal")
    return badges
}

function normalizeEvidence(claim: any): EvidenceItem[] {
    const verification = claim?.verification || {}
    const verdict = verification.verdict || "UNCERTAIN"
    const usedEvidenceIds = new Set<string>(verification.used_evidence_ids || [])
    const contradictedBy = new Set<string>(verification.contradicted_by || [])

    const primary = (claim?.evidence?.primary_document || []).map((item: any, idx: number): EvidenceItem => {
        const evidenceId = typeof item.evidence_id === "string" ? item.evidence_id : undefined
        return {
            reactKey: `primary-${idx}`,
            evidenceId,
            title: `Primary Document ${item.document_type || ""}`.trim(),
            snippet: item.snippet || "No narrative snippet found",
            explanation:
                item.explanation ||
                (evidenceId && contradictedBy.has(evidenceId)
                    ? "This primary document conflicts with the claim."
                    : "This primary document provides direct supporting context."),
            source: "primary_document",
            score: item.score || 0,
            value: item.value,
            url: item.url,
            badges: ["primary"],
        }
    })

    const wikidata = (claim?.evidence?.wikidata || []).map((item: any, idx: number): EvidenceItem => {
        const evidenceId = typeof item.evidence_id === "string" ? item.evidence_id : undefined
        const property = item.property || ""
        const propLabel = WIKIDATA_LABELS[property] || property || "Wikidata"
        const contextOnlyTemporal = item.support_type === "CONTEXT_ONLY_TEMPORAL"
        const badges = [
            `wikidata:${property || "unknown"}`,
            ...alignmentBadges(item.alignment),
        ]
        if (typeof item.score === "number" && item.score > 0) {
            badges.push(`score:${item.score.toFixed(2)}`)
        }
        return {
            reactKey: `wikidata-${idx}`,
            evidenceId,
            title: `Wikidata ${propLabel}`,
            snippet: item.snippet || "No narrative snippet found",
            explanation:
                item.explanation ||
                (evidenceId && contradictedBy.has(evidenceId)
                    ? `Structured record contradicts the claim for ${propLabel.toLowerCase()}.`
                    : contextOnlyTemporal
                        ? `Context evidence: ${propLabel.toLowerCase()} is listed, but this claim has no temporal constraint.`
                        : evidenceId && usedEvidenceIds.has(evidenceId)
                            ? `Structured record supports the claim for ${propLabel.toLowerCase()}.`
                            : `Related structured record for ${propLabel.toLowerCase()}.`),
            source: "wikidata",
            score: item.score || 0,
            value: String(item.value ?? ""),
            url: item.url,
            badges,
        }
    })

    const wikipedia = (claim?.evidence?.wikipedia || []).map((item: any, idx: number): EvidenceItem => {
        const evidenceId = typeof item.evidence_id === "string" ? item.evidence_id : undefined
        const snippet = item.snippet || item.sentence || "No narrative snippet found"
        const badges = ["wikipedia"]
        if (item.section_anchor) badges.push(`section:${item.section_anchor}`)
        if (typeof item.score === "number" && item.score > 0) badges.push(`score:${item.score.toFixed(2)}`)
        return {
            reactKey: `wikipedia-${idx}`,
            evidenceId,
            title: "Wikipedia",
            snippet,
            explanation:
                item.explanation ||
                (evidenceId && contradictedBy.has(evidenceId)
                    ? "Narrative sentence indicates a conflicting fact."
                    : "Narrative sentence provides contextual evidence for this claim."),
            source: "wikipedia",
            score: item.score || 0,
            url: item.url,
            badges,
        }
    })

    const grokipedia = (claim?.evidence?.grokipedia || []).map((item: any, idx: number): EvidenceItem => {
        const evidenceId = typeof item.evidence_id === "string" ? item.evidence_id : undefined
        return {
            reactKey: `grokipedia-${idx}`,
            evidenceId,
            title: "Grokipedia",
            snippet: item.snippet || item.text || item.excerpt || "No narrative snippet found",
            explanation: item.explanation || "Supplementary narrative context.",
            source: "grokipedia",
            score: item.score || 0,
            url: item.url,
            badges: ["grokipedia"],
        }
    })

    const combined: EvidenceItem[] = [...primary, ...wikidata, ...wikipedia, ...grokipedia]

    combined.sort((a: EvidenceItem, b: EvidenceItem) => {
        const aRef = a.evidenceId && contradictedBy.has(a.evidenceId) ? 1 : 0
        const bRef = b.evidenceId && contradictedBy.has(b.evidenceId) ? 1 : 0
        const aSup = a.evidenceId && usedEvidenceIds.has(a.evidenceId) ? 1 : 0
        const bSup = b.evidenceId && usedEvidenceIds.has(b.evidenceId) ? 1 : 0

        if (verdict === "REFUTED") {
            if (aRef !== bRef) return bRef - aRef
            return b.score - a.score
        }

        if (verdict === "SUPPORTED") {
            if (aSup !== bSup) return bSup - aSup
            return b.score - a.score
        }

        return b.score - a.score
    })

    return dedupeEvidence(combined)
}

function getDisplayVerdict(claim: any): DisplayVerdict {
    const rawVerdict = claim?.verification?.verdict || "UNCERTAIN"
    const facetStatus = claim?.verification?.facet_status || {}
    const facetValues = Object.values(facetStatus) as string[]
    const hasSupportedFacet = facetValues.some((value) => value === "SUPPORTED")
    const hasUnknownFacet = facetValues.some((value) => value === "UNKNOWN")

    if (rawVerdict === "REFUTED") return "REFUTED"
    if (rawVerdict === "PARTIALLY_SUPPORTED") return "PARTIALLY_SUPPORTED"
    if (rawVerdict === "SUPPORTED") {
        if (hasSupportedFacet && hasUnknownFacet) {
            return "PARTIALLY_SUPPORTED"
        }
        return "SUPPORTED"
    }

    return "UNCERTAIN"
}

export function ClaimInspectorPanel({ claim, onClose, className = "", explainabilityMode = "CASUAL" }: Props) {
    const [activeTab, setActiveTab] = useState<InspectorTab>("VERDICT")

    useEffect(() => {
        setActiveTab("VERDICT")
    }, [claim?.claim_id, explainabilityMode])

    if (!claim) {
        return (
            <aside className={`rounded-2xl border border-slate-200 dark:border-white/10 bg-white/80 dark:bg-white/[0.02] p-6 min-h-[420px] ${className}`.trim()}>
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-2">Claim Inspector</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    Select a highlighted claim to inspect evidence.
                </p>
            </aside>
        )
    }

    const confidence = Number(claim.verification?.confidence ?? 0)
    const displayVerdict = getDisplayVerdict(claim)
    const style = verdictStyles[displayVerdict]
    const VerdictIcon = style.icon

    const contradictedBy: string[] = Array.from(new Set(claim.verification?.contradicted_by || []))
    const hallucinations = claim.hallucinations || []
    const facetStatus = claim.verification?.facet_status || {}
    const reasoning = claim.verification?.reasoning || "No specific reasoning provided."
    const evidenceItems = useMemo(() => normalizeEvidence(claim), [claim])

    const tabs: Array<{ key: InspectorTab; label: string }> = [
        { key: "VERDICT", label: "Verdict" },
        { key: "EVIDENCE", label: "Evidence" },
    ]
    if (explainabilityMode === "EXPERT") {
        tabs.push({ key: "DEBUG", label: "Debug" })
    }

    useEffect(() => {
        if (process.env.NODE_ENV === "production") return
        const rawVerdict = claim?.verification?.verdict
        if (rawVerdict === "SUPPORTED" && displayVerdict === "PARTIALLY_SUPPORTED") {
            console.warn("Claim metadata mismatch: SUPPORTED verdict with unresolved facets. Display downgraded to PARTIALLY_SUPPORTED.")
        }
    }, [claim, displayVerdict])

    return (
        <aside className={`rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black p-4 lg:p-5 space-y-4 overflow-y-auto ${className}`.trim()}>
            <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Inspector</h3>
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

            <div className="inline-flex rounded-md border border-slate-200 dark:border-white/10 p-0.5 bg-slate-100 dark:bg-white/5">
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`px-2.5 py-1 text-xs font-medium rounded ${activeTab === tab.key ? 'bg-white dark:bg-black text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {activeTab === "VERDICT" ? (
                <div className="space-y-4">
                    <div className="rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50/70 dark:bg-black/20 p-4 space-y-2">
                        <p className="text-sm leading-relaxed text-slate-800 dark:text-slate-100">{claim.claim_text}</p>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Confidence: {(confidence * 100).toFixed(0)}%</div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{reasoning}</p>
                    </div>

                    {Object.keys(facetStatus).length > 0 ? (
                        <div>
                            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Claim facets</div>
                            <div className="space-y-1.5">
                                {Object.entries(facetStatus).map(([facet, status]) => (
                                    <div key={facet} className="flex items-center justify-between rounded-md border border-slate-200 dark:border-white/10 px-2.5 py-1.5 text-xs">
                                        <span className="text-slate-700 dark:text-slate-200">{FACET_LABELS[facet] || facet}</span>
                                        <span className="text-slate-500 dark:text-slate-400">
                                            {status === "SUPPORTED" ? "Supported ✅" : status === "CONTRADICTED" ? "Contradicted ❌" : "Unknown ?"}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : null}

                    {hallucinations.length > 0 ? (
                        <div className="space-y-2">
                            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">Hallucination flags</div>
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
                            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Contradicted by</div>
                            <div className="flex flex-wrap gap-2">
                                {contradictedBy.map((id) => (
                                    <span key={id} className="rounded-md bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300 px-2 py-1 text-[11px] font-mono">
                                        {id}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ) : null}
                </div>
            ) : null}

            {activeTab === "EVIDENCE" ? (
                <div className="space-y-2">
                    {evidenceItems.map((item) => (
                        <EvidenceCard key={item.evidenceId || item.reactKey} item={item} />
                    ))}
                    {evidenceItems.length === 0 ? (
                        <p className="text-xs text-slate-500 dark:text-slate-400">No evidence items available.</p>
                    ) : null}
                </div>
            ) : null}

            {activeTab === "DEBUG" && explainabilityMode === "EXPERT" ? (
                <div className="space-y-3">
                    <div>
                        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Verification payload</div>
                        <pre className="text-[11px] whitespace-pre-wrap break-words rounded-md border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-black p-2.5 text-slate-700 dark:text-slate-300">
                            {JSON.stringify(claim.verification || {}, null, 2)}
                        </pre>
                    </div>
                    <div>
                        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Evidence status</div>
                        <pre className="text-[11px] whitespace-pre-wrap break-words rounded-md border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-black p-2.5 text-slate-700 dark:text-slate-300">
                            {JSON.stringify(claim.evidence_status || {}, null, 2)}
                        </pre>
                    </div>
                </div>
            ) : null}
        </aside>
    )
}
