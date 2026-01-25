"use client"
import React, { useState, useEffect } from 'react'
import { AuditInput } from '@/components/AuditInput'
import { AuditSummary } from '@/components/AuditSummary'
import { AuditedText } from '@/components/AuditedText'
import { Loader2 } from 'lucide-react'
import { TimelineView } from '@/components/TimelineView'
import { ExplainabilityToggle } from '@/components/ExplainabilityToggle'


// System Phases
type Phase = "INPUT" | "PROCESSING" | "RESULTS"

const LOADING_STATES = [
    "Extracting atomic claims from text...",
    "Querying Wikidata knowledge graph...",
    "Retrieving authoritative evidence sources...",
    "Checking for cross-claim inconsistencies...",
    "Calibrating final risk scores..."
]

export default function AuditPage() {
    const [phase, setPhase] = useState<Phase>("INPUT")
    const [result, setResult] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)
    const [sourceText, setSourceText] = useState("")
    const [loadingMsg, setLoadingMsg] = useState(LOADING_STATES[0])
    const [mode, setMode] = useState<"DEMO" | "RESEARCH">("DEMO")
    const [explainabilityMode, setExplainabilityMode] = useState<'CASUAL' | 'EXPERT'>('CASUAL')
    const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null)

    // Simulate loading steps for visual weight
    useEffect(() => {
        if (phase !== "PROCESSING") return;
        let i = 0;
        const interval = setInterval(() => {
            i = (i + 1) % LOADING_STATES.length
            setLoadingMsg(LOADING_STATES[i])
        }, 1200)
        return () => clearInterval(interval)
    }, [phase])

    const handleAudit = async (text: string) => {
        setPhase("PROCESSING")
        setError(null)
        setSourceText(text)
        setResult(null)

        try {
            const res = await fetch('/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, mode: "demo" })
            })

            if (!res.ok) throw new Error("Audit failed. Backend might be offline.")

            const data = await res.json()
            setResult(data)
            setPhase("RESULTS")
        } catch (e: any) {
            setError(e.message)
            setPhase("INPUT")
        }
    }

    return (
        <div className="min-h-screen bg-transparent font-sans text-slate-900 dark:text-slate-100 pb-20 transition-colors duration-500">

            {/* Top Bar (SaaS Identity) */}
            {/* Top Bar (Toolbar - Only in Results) */}
            {phase === "RESULTS" && (
                <div className="h-16 flex items-center justify-end px-6 border-b border-slate-200 dark:border-border-subtle bg-white/80 dark:bg-black/90 backdrop-blur-sm sticky top-0 z-30">
                    <div className="flex bg-slate-100 dark:bg-white/[0.02] rounded-lg p-1">
                        <button
                            onClick={() => setMode("DEMO")}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === "DEMO" ? "bg-white dark:bg-white/10 shadow text-slate-900 dark:text-slate-100" : "text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-slate-200"}`}
                        >
                            Demo
                        </button>
                        <button
                            onClick={() => setMode("RESEARCH")}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === "RESEARCH" ? "bg-white dark:bg-white/[0.08] shadow text-slate-900 dark:text-slate-100" : "text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-slate-200"}`}
                        >
                            Research
                        </button>
                    </div>
                </div>
            )}

            <div className="max-w-5xl mx-auto px-6 py-12">

                {/* PHASE 1: INPUT */}
                {phase === "INPUT" && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-3xl mx-auto pt-10">
                        <div className="text-center mb-12">
                            <h1 className="text-3xl md:text-4xl font-medium text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-slate-50 dark:via-slate-300 dark:to-slate-50 animate-text-shimmer tracking-[-0.035em] mb-4">Initialize Audit</h1>
                            <p className="text-xl text-slate-500 dark:text-slate-400 font-light">
                                Input text for epistemic verification.
                            </p>
                        </div>

                        <AuditInput onAudit={handleAudit} isLoading={false} />

                        {error && (
                            <div className="mt-8 p-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg text-center border border-red-100 dark:border-red-800 text-sm">
                                {error}
                            </div>
                        )}
                    </div>
                )}

                {/* PHASE 2: PROCESSING */}
                {phase === "PROCESSING" && (
                    <div className="flex flex-col items-center justify-center pt-32 animate-in fade-in duration-700">
                        <div className="relative w-16 h-16 mb-8 group">
                            <div className="absolute inset-0 bg-slate-200 dark:bg-white/5 rounded-full blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-1000"></div>
                            <Loader2 className="w-16 h-16 text-slate-900 dark:text-slate-100 animate-spin relative z-10" />
                        </div>
                        <p className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2 animate-pulse">{loadingMsg}</p>
                        <p className="text-sm text-slate-400 dark:text-slate-500 font-mono">Running logic checks...</p>
                    </div>
                )}

                {/* PHASE 3/4: RESULTS */}
                {phase === "RESULTS" && result && (
                    <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-12">

                        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                            <div>
                                <h2 className="text-2xl font-medium text-slate-900 dark:text-slate-50 tracking-[-0.03em]">Audit Report</h2>
                                <p className="text-slate-400 text-xs mt-1">v1.6.2 Epistemic Interface</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <ExplainabilityToggle mode={explainabilityMode} onChange={setExplainabilityMode} />
                                <button
                                    onClick={() => { setResult(null); setPhase("INPUT"); setSelectedClaimId(null); }}
                                    className="text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors underline underline-offset-4"
                                >
                                    New Audit
                                </button>
                            </div>
                        </div>

                        {/* Dominant Summary Card */}
                        <div className="relative">
                            <div className="absolute -inset-4 bg-slate-200/50 dark:bg-white/[0.02] rounded-3xl blur-2xl -z-10" />
                            {(() => {

                                // Use Backend Values Directly (Canonical Contract v1.3.9)
                                console.log("RAW RISK FROM BACKEND:", result.hallucination_score, result.overall_risk)

                                const finalScore = typeof result.hallucination_score === "number"
                                    ? Math.max(0, Math.min(1, result.hallucination_score))
                                    : 0.0
                                const finalLabel = result.overall_risk || "HIGH"

                                // Use Backend Summary (No Frontend Recalculation)
                                const summ = result.summary || {}
                                const normalizedSummary = {
                                    Verified: summ.supported || 0,
                                    Refuted: summ.refuted || 0,
                                    Uncertain: (summ.uncertain || 0) + (summ.insufficient || 0),
                                    Claims: summ.epistemic_claims || summ.total_asserted_claims || 0
                                }

                                return (
                                    <>
                                        <AuditSummary
                                            overallRisk={finalLabel}
                                            hallucinationScore={finalScore}
                                            summary={normalizedSummary}
                                        />
                                        {finalScore === 0 && normalizedSummary.Uncertain > 0 && (
                                            <div className="mt-2 text-center">
                                                <span className="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 px-2 py-1 rounded border border-amber-100 dark:border-amber-900/50">
                                                    Risk is driven by uncertainty, not verified correctness.
                                                </span>
                                            </div>
                                        )}
                                    </>
                                )
                            })()}
                        </div>

                        {/* Evidence / Document View */}
                        <div className="bg-[#fafafa] dark:bg-black rounded-none md:rounded-xl border border-slate-200 dark:border-border-subtle shadow-sm relative overflow-hidden">
                            {/* Document Header */}
                            <div className="px-8 py-6 border-b border-slate-200 dark:border-border-subtle bg-white dark:bg-black flex items-center justify-between">
                                <div className="text-xs font-mono uppercase tracking-widest text-slate-400 font-bold">Source Document</div>
                                {mode === "RESEARCH" && (
                                    <div className="flex gap-4 text-[10px] uppercase font-mono text-slate-500 dark:text-slate-400">
                                        <span>H1: Unsupported</span>
                                        <span>H3: Overconfidence</span>
                                        <span>H5: Inconsistent</span>
                                    </div>
                                )}
                            </div>

                            {/* The Paper - CONSTRAINED HEIGHT */}
                            <div className="flex flex-col lg:flex-row">
                                <div className="flex-1 py-12 px-8 md:px-12 bg-white dark:bg-black shadow-sm border-r border-slate-100 dark:border-border-subtle max-h-[600px] overflow-y-auto">
                                    <AuditedText
                                        sourceText={sourceText}
                                        claims={result.claims}
                                        mode={mode}
                                        selectedClaimId={selectedClaimId}
                                        onSelectClaim={setSelectedClaimId}
                                        explainabilityMode={explainabilityMode}
                                    />
                                </div>
                                <div className="w-full lg:w-80 bg-slate-50/30 dark:bg-white/[0.02] p-6 flex flex-col gap-6 overflow-y-auto max-h-[600px]">
                                    <TimelineView
                                        claims={result.claims}
                                        onClaimClick={setSelectedClaimId}
                                        activeClaimId={selectedClaimId}
                                        explainabilityMode={explainabilityMode}
                                    />

                                    <div className="p-4 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-lg text-xs text-slate-500 dark:text-neutral-400 leading-relaxed shadow-sm">
                                        <b className="text-slate-700 dark:text-slate-300 block mb-1">Timeline Insights</b>
                                        Nodes represent atomic claims in order of appearance. Click a node to scroll/inspect.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
