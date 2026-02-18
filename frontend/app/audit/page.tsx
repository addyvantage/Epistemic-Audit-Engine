"use client"

import React, { useEffect, useMemo, useState } from 'react'
import { Loader2, CheckCircle2, Search, Database, FileCheck, Scale } from 'lucide-react'
import { AuditInput } from '@/components/AuditInput'
import { AuditSummary } from '@/components/AuditSummary'
import { AuditedText } from '@/components/AuditedText'
import { TimelineView } from '@/components/TimelineView'
import { ExplainabilityToggle } from '@/components/ExplainabilityToggle'
import { InspectorOverlay } from '@/components/InspectorOverlay'

type Phase = 'INPUT' | 'PROCESSING' | 'RESULTS'

const PROCESSING_STEPS = [
    { id: 'extract', label: 'Extracting claims', icon: Search },
    { id: 'query', label: 'Querying evidence', icon: Database },
    { id: 'verify', label: 'Verifying claims', icon: FileCheck },
    { id: 'calibrate', label: 'Calibrating risk', icon: Scale },
]

const HEALTH_CACHE_KEY = 'epistemic_audit_backend_health_ok_v1'
const HEALTH_BACKOFF_MS = [0, 250, 600, 1000]

async function sleep(ms: number): Promise<void> {
    if (ms <= 0) return
    await new Promise((resolve) => setTimeout(resolve, ms))
}

export default function AuditPage() {
    const [phase, setPhase] = useState<Phase>('INPUT')
    const [result, setResult] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)
    const [sourceText, setSourceText] = useState('')
    const [currentStep, setCurrentStep] = useState(0)
    const [mode, setMode] = useState<'DEMO' | 'RESEARCH'>('DEMO')
    const [explainabilityMode, setExplainabilityMode] = useState<'CASUAL' | 'EXPERT'>('CASUAL')
    const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null)
    const isLoading = phase === 'PROCESSING'

    useEffect(() => {
        if (phase !== 'PROCESSING') return

        setCurrentStep(0)
        const lastStep = PROCESSING_STEPS.length - 1

        const interval = setInterval(() => {
            setCurrentStep((prev) => {
                if (prev >= lastStep) {
                    clearInterval(interval)
                    return prev
                }
                return prev + 1
            })
        }, 1100)

        return () => clearInterval(interval)
    }, [phase])

    const handleAudit = async (text: string) => {
        setError(null)
        setSourceText(text)
        setResult(null)
        setSelectedClaimId(null)

        const isBackendReady = await ensureBackendReady()
        if (!isBackendReady) {
            setPhase('INPUT')
            setError('Backend not ready')
            return
        }

        setPhase('PROCESSING')

        try {
            const res = await fetch('/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, mode: mode.toLowerCase() }),
            })

            if (!res.ok) throw new Error('Audit failed. Backend might be offline.')

            const data = await res.json()
            setResult(data)
            setPhase('RESULTS')
        } catch (e: any) {
            setError(e.message)
            setPhase('INPUT')
        }
    }

    const ensureBackendReady = async (): Promise<boolean> => {
        if (typeof window !== 'undefined' && sessionStorage.getItem(HEALTH_CACHE_KEY) === 'ok') {
            return true
        }

        for (const delay of HEALTH_BACKOFF_MS) {
            await sleep(delay)
            try {
                const response = await fetch('/api/health', { cache: 'no-store' })
                if (!response.ok) {
                    continue
                }

                const payload = await response.json()
                const statusOk = payload?.status === 'ok'
                const pipelineReady = payload?.pipeline_ready === true
                const pidValid =
                    payload?.pid === undefined ||
                    (typeof payload.pid === 'number' && Number.isFinite(payload.pid))

                if (statusOk && pipelineReady && pidValid) {
                    if (typeof window !== 'undefined') {
                        sessionStorage.setItem(HEALTH_CACHE_KEY, 'ok')
                    }
                    return true
                }
            } catch {
                // Retry with short backoff.
            }
        }

        return false
    }

    const finalScore = useMemo(() => {
        if (typeof result?.hallucination_score !== 'number') return 0
        return Math.max(0, Math.min(1, result.hallucination_score))
    }, [result])

    const finalLabel = useMemo(() => {
        return result?.overall_risk || 'HIGH'
    }, [result])

    const normalizedSummary = useMemo(() => {
        const summ = result?.summary || {}
        return {
            Verified: summ.supported || 0,
            Refuted: summ.refuted || 0,
            Uncertain: (summ.uncertain || 0) + (summ.insufficient || 0),
            Claims: summ.epistemic_claims || summ.total_asserted_claims || 0,
        }
    }, [result])

    const selectedClaim = useMemo(() => {
        if (!result?.claims || !selectedClaimId) return null
        return result.claims.find((c: any) => c.claim_id === selectedClaimId) || null
    }, [result, selectedClaimId])

    return (
        <div className="min-h-screen bg-transparent font-sans text-slate-900 dark:text-slate-100 pb-16 transition-colors duration-500">
            {phase === 'RESULTS' ? (
                <div className="h-16 flex items-center justify-end px-6 border-b border-slate-200 dark:border-border-subtle bg-white/80 dark:bg-black/90 backdrop-blur-sm sticky top-0 z-30">
                    <div className="flex items-center gap-4">
                        <ExplainabilityToggle mode={explainabilityMode} onChange={setExplainabilityMode} />
                        <div className="flex bg-slate-100 dark:bg-white/[0.02] rounded-lg p-1">
                            <button
                                onClick={() => setMode('DEMO')}
                                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === 'DEMO' ? 'bg-white dark:bg-white/10 shadow text-slate-900 dark:text-slate-100' : 'text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                            >
                                Demo
                            </button>
                            <button
                                onClick={() => setMode('RESEARCH')}
                                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === 'RESEARCH' ? 'bg-white dark:bg-white/[0.08] shadow text-slate-900 dark:text-slate-100' : 'text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                            >
                                Research
                            </button>
                        </div>
                        <button
                            onClick={() => {
                                setResult(null)
                                setPhase('INPUT')
                                setSelectedClaimId(null)
                                setCurrentStep(0)
                            }}
                            className="text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors underline underline-offset-4"
                        >
                            New Audit
                        </button>
                    </div>
                </div>
            ) : null}

            <div className="max-w-6xl mx-auto px-6 py-12">
                {phase === 'INPUT' ? (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-3xl mx-auto pt-10">
                        <div className="text-center mb-12">
                            <h1 className="text-3xl md:text-4xl font-medium text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-slate-50 dark:via-slate-300 dark:to-slate-50 animate-text-shimmer tracking-[-0.035em] mb-4">
                                Initialize Audit
                            </h1>
                            <p className="text-xl text-slate-500 dark:text-slate-400 font-light mb-6">
                                Input text for epistemic verification.
                            </p>
                            <div className="inline-flex bg-slate-100 dark:bg-white/[0.02] rounded-lg p-1">
                                <button
                                    onClick={() => setMode('DEMO')}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === 'DEMO' ? 'bg-white dark:bg-white/10 shadow text-slate-900 dark:text-slate-100' : 'text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                                >
                                    Demo
                                </button>
                                <button
                                    onClick={() => setMode('RESEARCH')}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${mode === 'RESEARCH' ? 'bg-white dark:bg-white/[0.08] shadow text-slate-900 dark:text-slate-100' : 'text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                                >
                                    Research
                                </button>
                            </div>
                        </div>

                        <AuditInput onAudit={handleAudit} isLoading={isLoading} />

                        {error ? (
                            <div className="mt-8 p-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg text-center border border-red-100 dark:border-red-800 text-sm animate-in fade-in duration-300">
                                {error}
                            </div>
                        ) : null}
                    </div>
                ) : null}

                {phase === 'PROCESSING' ? (
                    <div className="flex flex-col items-center justify-center pt-24 animate-in fade-in duration-500">
                        <div className="relative w-20 h-20 mb-10">
                            <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-xl animate-pulse" />
                            <Loader2 className="w-20 h-20 text-emerald-500 animate-spin relative z-10" />
                        </div>

                        <div className="flex items-center gap-2 mb-8">
                            {PROCESSING_STEPS.map((step, idx) => {
                                const Icon = step.icon
                                const isActive = idx === currentStep
                                const isComplete = idx < currentStep
                                return (
                                    <div
                                        key={step.id}
                                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-mono uppercase tracking-wider transition-all duration-300 ${
                                            isActive
                                                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 scale-105'
                                                : isComplete
                                                    ? 'bg-white/5 border-white/10 text-slate-400'
                                                    : 'bg-transparent border-white/5 text-slate-600 opacity-50'
                                        }`}
                                    >
                                        {isComplete ? (
                                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                        ) : (
                                            <Icon className="w-3 h-3" />
                                        )}
                                        <span className="hidden md:inline">{step.label}</span>
                                    </div>
                                )
                            })}
                        </div>

                        <p className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                            {PROCESSING_STEPS[currentStep]?.label || PROCESSING_STEPS[0].label}
                        </p>
                        <p className="text-sm text-slate-400 dark:text-slate-500 font-mono">Running deterministic pipeline checks…</p>
                    </div>
                ) : null}

                {phase === 'RESULTS' && result ? (
                    <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-8">
                        <div className="relative">
                            <div className="absolute -inset-4 bg-slate-200/50 dark:bg-white/[0.02] rounded-3xl blur-2xl -z-10" />
                            <AuditSummary overallRisk={finalLabel} hallucinationScore={finalScore} summary={normalizedSummary} />
                            {finalScore === 0 && normalizedSummary.Uncertain > 0 ? (
                                <div className="mt-2 text-center animate-in fade-in duration-500 delay-500">
                                    <span className="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 px-2 py-1 rounded border border-amber-100 dark:border-amber-900/50">
                                        Risk is driven by uncertainty, not verified correctness.
                                    </span>
                                </div>
                            ) : null}
                        </div>

                        <section className="rounded-2xl border border-slate-200 dark:border-border-subtle bg-white/70 dark:bg-black/40 backdrop-blur-sm p-4">
                            <TimelineView
                                claims={result.claims}
                                onClaimClick={setSelectedClaimId}
                                activeClaimId={selectedClaimId}
                                explainabilityMode={explainabilityMode}
                            />
                        </section>

                        <section className="grid grid-cols-1 gap-6 items-start">
                            <div className="rounded-2xl border border-slate-200 dark:border-border-subtle bg-white dark:bg-black shadow-sm overflow-hidden">
                                <div className="px-8 py-5 border-b border-slate-200 dark:border-border-subtle bg-white/90 dark:bg-black/80">
                                    <div className="text-xs font-mono uppercase tracking-widest text-slate-400 font-bold">Source Document</div>
                                </div>

                                <div id="source-document-scroll" className="py-14 px-10 md:px-16 max-h-[700px] overflow-y-auto">
                                    <AuditedText
                                        sourceText={sourceText}
                                        claims={result.claims}
                                        mode={mode}
                                        selectedClaimId={selectedClaimId}
                                        onSelectClaim={setSelectedClaimId}
                                        explainabilityMode={explainabilityMode}
                                        showInlineInspector={false}
                                    />
                                </div>
                            </div>
                        </section>

                        <InspectorOverlay
                            open={!!selectedClaim}
                            claim={selectedClaim}
                            onClose={() => setSelectedClaimId(null)}
                        />
                    </div>
                ) : null}
            </div>
        </div>
    )
}
