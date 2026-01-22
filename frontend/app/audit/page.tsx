"use client"
import React, { useState, useEffect } from 'react'
import { AuditInput } from '@/components/AuditInput'
import { AuditSummary } from '@/components/AuditSummary'
import { AuditedText } from '@/components/AuditedText'
import { Loader2 } from 'lucide-react'


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
        <div className="min-h-screen bg-noise bg-slate-50 font-sans text-slate-900 pb-20">

            {/* Top Bar (SaaS Identity) */}
            {/* Top Bar (Toolbar - Only in Results) */}
            {phase === "RESULTS" && (
                <div className="h-16 flex items-center justify-end px-6 border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-30">
                    <div className="flex bg-slate-100 rounded-lg p-1">
                        <button
                            onClick={() => setMode("DEMO")}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === "DEMO" ? "bg-white shadow text-slate-900" : "text-slate-500 hover:text-slate-700"}`}
                        >
                            Demo
                        </button>
                        <button
                            onClick={() => setMode("RESEARCH")}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === "RESEARCH" ? "bg-white shadow text-slate-900" : "text-slate-500 hover:text-slate-700"}`}
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
                            <h1 className="text-4xl font-bold text-slate-900 tracking-tight mb-4">Initialize Audit</h1>
                            <p className="text-xl text-slate-500 font-light">
                                Input text for epistemic verification.
                            </p>
                        </div>

                        <AuditInput onAudit={handleAudit} isLoading={false} />

                        {error && (
                            <div className="mt-8 p-4 bg-red-50 text-red-700 rounded-lg text-center border border-red-100 text-sm">
                                {error}
                            </div>
                        )}
                    </div>
                )}

                {/* PHASE 2: PROCESSING */}
                {phase === "PROCESSING" && (
                    <div className="flex flex-col items-center justify-center pt-32 animate-in fade-in duration-700">
                        <div className="relative w-16 h-16 mb-8 group">
                            <div className="absolute inset-0 bg-slate-200 rounded-full blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-1000"></div>
                            <Loader2 className="w-16 h-16 text-slate-900 animate-spin relative z-10" />
                        </div>
                        <p className="text-lg font-medium text-slate-900 mb-2 animate-pulse">{loadingMsg}</p>
                        <p className="text-sm text-slate-400 font-mono">Running logic checks...</p>
                    </div>
                )}

                {/* PHASE 3/4: RESULTS */}
                {phase === "RESULTS" && result && (
                    <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-12">

                        <div className="flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Audit Report</h2>
                            <button
                                onClick={() => { setResult(null); setPhase("INPUT"); }}
                                className="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors underline underline-offset-4"
                            >
                                Start New Audit
                            </button>
                        </div>

                        {/* Dominant Summary Card */}
                        <div className="relative">
                            <div className="absolute -inset-4 bg-slate-200/50 rounded-3xl blur-2xl -z-10" />
                            {(() => {
                                const verdictCounts: Record<string, number> = {
                                    SUPPORTED: 0,
                                    SUPPORTED_WEAK: 0,
                                    REFUTED: 0,
                                    INSUFFICIENT_EVIDENCE: 0
                                }

                                result.claims?.forEach((c: any) => {
                                    const v = c.verification?.verdict
                                    if (v && verdictCounts[v] !== undefined) {
                                        verdictCounts[v]++
                                    }
                                })

                                const normalizedSummary = {
                                    Verified: verdictCounts.SUPPORTED + verdictCounts.SUPPORTED_WEAK,
                                    Refuted: verdictCounts.REFUTED,
                                    Uncertain: verdictCounts.INSUFFICIENT_EVIDENCE,
                                    Claims: result.claims?.length || 0
                                }

                                return (
                                    <AuditSummary
                                        overallRisk={result.overall_risk}
                                        hallucinationScore={result.hallucination_score}
                                        summary={normalizedSummary}
                                    />
                                )
                            })()}
                        </div>

                        {/* Evidence / Document View */}
                        <div className="bg-[#fafafa] rounded-none md:rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
                            {/* Document Header */}
                            <div className="px-8 py-6 border-b border-slate-200 bg-white flex items-center justify-between">
                                <div className="text-xs font-mono uppercase tracking-widest text-slate-400 font-bold">Source Document</div>
                                {mode === "RESEARCH" && (
                                    <div className="flex gap-4 text-[10px] uppercase font-mono text-slate-500">
                                        <span>H1: Unsupported</span>
                                        <span>H3: Overconfidence</span>
                                        <span>H5: Inconsistent</span>
                                    </div>
                                )}
                            </div>

                            {/* The Paper - CONSTRAINED HEIGHT */}
                            <div className="max-w-3xl mx-auto py-12 px-8 md:px-12 bg-white shadow-sm my-8 border border-slate-100 max-h-[520px] overflow-y-auto">
                                <AuditedText sourceText={sourceText} claims={result.claims} mode={mode} />
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
