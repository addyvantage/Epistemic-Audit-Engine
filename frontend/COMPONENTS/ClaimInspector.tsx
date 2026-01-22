"use client"

import { ExternalLink, ShieldCheck, AlertTriangle, XCircle } from "lucide-react"

type Props = {
    claim: any
    onClose: () => void
    mode?: "DEMO" | "RESEARCH"
}

const verdictStyles: Record<string, any> = {
    SUPPORTED: {
        bg: "bg-green-50",
        border: "border-green-200",
        text: "text-green-800",
        icon: ShieldCheck,
        label: "Supported",
        description: "Supported by authoritative sources."
    },
    REFUTED: {
        bg: "bg-red-50",
        border: "border-red-200",
        text: "text-red-800",
        icon: XCircle,
        label: "Refuted",
        description: "Contradicted by authoritative sources."
    },
    INSUFFICIENT_EVIDENCE: {
        bg: "bg-amber-50",
        border: "border-amber-200",
        text: "text-amber-800",
        icon: AlertTriangle,
        label: "Insufficient Evidence",
        description: "No conclusive evidence found in knowledge graph."
    },
    SUPPORTED_WEAK: {
        bg: "bg-green-50",
        border: "border-green-100",
        text: "text-green-700",
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

    // NORMALIZATION LOGIC
    const structuredSources = (claim.evidence?.wikidata || []).map((e: any) => ({
        label: e.property?.replace(/P\d+/, '').trim() || "Property Match",
        value: String(e.value),
        url: e.source_url
    })).slice(0, 3)

    // Combined narrative sources (Wikipedia + Grokipedia)
    const primarySources = (claim.evidence?.wikipedia || []).map((e: any) => ({
        title: "Wikipedia Article",
        snippet: e.snippet,
        url: e.url
    })).concat((claim.evidence?.grokipedia || []).map((e: any) => ({
        title: "Narrative Context",
        snippet: e.text,
        url: null
    }))).slice(0, 3)

    const hasEvidence = structuredSources.length > 0 || primarySources.length > 0

    // TEMPLATED REASONING
    const reasoning = {
        SUPPORTED: `This claim is supported because it aligns with structured records found in the knowledge graph${structuredSources.length > 0 ? ', specifically regarding ' + structuredSources[0].label : ''}.`,
        REFUTED: `This claim is refuted because it contradicts authoritative records${structuredSources.length > 0 ? ' regarding ' + structuredSources[0].label : ''}.`,
        INSUFFICIENT_EVIDENCE: "This claim is marked as uncertain because no matching records were found in the connected knowledge bases."
    }[verdict as string] || "Evidence analysis inconclusive."

    return (
        <aside className="fixed right-0 top-0 h-full w-[420px] bg-white border-l border-slate-200 shadow-2xl z-50 overflow-y-auto animate-in slide-in-from-right duration-300 font-sans flex flex-col">

            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100 bg-white/95 backdrop-blur-sm sticky top-0 z-20">
                <h2 className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-semibold">
                    Epistemic Verification
                </h2>
                <button onClick={onClose} className="text-slate-400 hover:text-slate-900 transition-colors p-1 hover:bg-slate-100 rounded-full">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto pb-10">
                {/* 1. Verdict (Forensic Label) */}
                <div className="px-6 pt-6">
                    <div className={`p-4 rounded-lg border ${style.bg} ${style.border} flex items-start gap-3 mb-6`}>
                        <Icon className={`w-5 h-5 shrink-0 ${style.text} mt-0.5`} />
                        <div>
                            <div className={`font-bold text-sm ${style.text} mb-1`}>{style.label}</div>
                            <div className="text-xs text-slate-600 leading-relaxed font-mono opacity-80">
                                Confidence: {(confidence * 100).toFixed(0)}%
                            </div>
                        </div>
                    </div>

                    {/* 2. Quoted Claim */}
                    <blockquote className="text-lg font-medium text-slate-800 leading-relaxed border-l-4 border-slate-200 pl-4 mb-2 italic">
                        “{claim.claim_text}”
                    </blockquote>
                </div>

                <div className="w-full h-px bg-slate-100 my-6" />

                {/* 3. Analysis */}
                <div className="px-6">
                    <h3 className="text-xs font-bold text-slate-900 mb-2 uppercase tracking-wide">Analysis</h3>
                    <p className="text-sm text-slate-600 leading-relaxed">
                        {reasoning}
                    </p>
                </div>

                <div className="w-full h-px bg-slate-100 my-6" />

                {/* 4. Evidence Sources */}
                <div className="px-6">
                    <h3 className="text-xs font-bold text-slate-900 mb-4 flex items-center justify-between uppercase tracking-wide">
                        <span>Evidence Sources</span>
                        {hasEvidence && <span className="text-[10px] font-normal text-slate-400">{structuredSources.length + primarySources.length} Records</span>}
                    </h3>

                    {!hasEvidence && (
                        <div className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg text-center border border-slate-100 cursor-default">
                            No authoritative records linked.
                        </div>
                    )}

                    <div className="space-y-6">
                        {/* Structured Evidence Block */}
                        {structuredSources.length > 0 && (
                            <div className="space-y-3">
                                <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Structured Knowledge Graph</div>
                                {structuredSources.map((s: any, i: number) => (
                                    <div key={i} className="bg-slate-50 border border-slate-100 rounded p-3">
                                        <div className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">{s.label}</div>
                                        <div className="text-sm text-slate-900 font-medium mb-1 line-clamp-2">
                                            <span className="bg-yellow-100 px-1 rounded box-decoration-clone leading-relaxed">{s.value}</span>
                                        </div>
                                        {s.url && (
                                            <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-slate-400 hover:text-slate-600 flex items-center gap-1 mt-1">
                                                KB Record <ExternalLink className="w-2.5 h-2.5" />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Narrative Evidence Block */}
                        {primarySources.length > 0 && (
                            <div className="space-y-3">
                                <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Narrative Corpal Evidence</div>
                                {primarySources.map((s: any, i: number) => (
                                    <div key={i + 10} className="bg-white border border-slate-200 rounded p-3 shadow-sm">
                                        <div className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-2">{s.title}</div>

                                        {/* Highlighted Snippet - Marker Style */}
                                        <div className="text-sm text-slate-800 leading-relaxed mb-2">
                                            <span className="bg-yellow-100 px-1 rounded box-decoration-clone leading-[1.6]">
                                                “{s.snippet
                                                    ? s.snippet
                                                    : "No extractable passage was returned by this source. Evidence linkage is structural rather than textual."}”
                                            </span>
                                        </div>

                                        {s.url && (
                                            <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-blue-600 hover:underline flex items-center gap-1">
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
        </aside>
    )
}
