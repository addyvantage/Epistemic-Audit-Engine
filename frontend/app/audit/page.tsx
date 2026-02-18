"use client"

import React, { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Database, FileCheck, Globe, Loader2, Search, Scale } from 'lucide-react'
import { AuditInput } from '@/components/AuditInput'
import { AuditSummary } from '@/components/AuditSummary'
import { AuditedText } from '@/components/AuditedText'
import { TimelineView } from '@/components/TimelineView'
import { ExplainabilityToggle } from '@/components/ExplainabilityToggle'
import { ClaimInspectorPanel } from '@/components/ClaimInspectorPanel'

type Phase = 'INPUT' | 'PROCESSING' | 'RESULTS'
type ClaimsView = 'LIST' | 'TIMELINE'

const PROCESSING_STEPS = [
    { id: 'extract', label: 'Extracting claims', icon: Search },
    { id: 'query', label: 'Retrieving evidence', icon: Database },
    { id: 'verify', label: 'Verifying claims', icon: FileCheck },
    { id: 'calibrate', label: 'Calibrating risk', icon: Scale },
]

const HEALTH_CACHE_KEY = 'epistemic_audit_backend_health_ok_v1'
const HEALTH_BACKOFF_MS = [0, 250, 600, 1000]

async function sleep(ms: number): Promise<void> {
    if (ms <= 0) return
    await new Promise((resolve) => setTimeout(resolve, ms))
}

function verdictChipStyle(verdict: string): string {
    switch (verdict) {
        case 'SUPPORTED':
        case 'SUPPORTED_WEAK':
            return 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800'
        case 'PARTIALLY_SUPPORTED':
            return 'bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-800'
        case 'REFUTED':
            return 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-800'
        default:
            return 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800'
    }
}

function verdictLabel(verdict: string): string {
    switch (verdict) {
        case 'SUPPORTED':
        case 'SUPPORTED_WEAK':
            return 'Supported'
        case 'PARTIALLY_SUPPORTED':
            return 'Partially supported'
        case 'REFUTED':
            return 'Refuted'
        default:
            return 'Uncertain'
    }
}

function claimSourceMeta(claim: any): Array<{ key: string; label: string; count: number; Icon: any }> {
    const evidence = claim?.evidence || {}
    return [
        { key: 'primary_document', label: 'Primary documents', count: (evidence.primary_document || []).length, Icon: FileCheck },
        { key: 'wikidata', label: 'Wikidata', count: (evidence.wikidata || []).length, Icon: Database },
        { key: 'wikipedia', label: 'Wikipedia', count: (evidence.wikipedia || []).length, Icon: Globe },
    ].filter((item) => item.count > 0)
}

function MobileInspectorDrawer({
    open,
    claim,
    explainabilityMode,
    onClose,
}: {
    open: boolean
    claim: any | null
    explainabilityMode: 'CASUAL' | 'EXPERT'
    onClose: () => void
}) {
    useEffect(() => {
        if (!open) return
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') onClose()
        }
        window.addEventListener('keydown', onKeyDown)
        return () => window.removeEventListener('keydown', onKeyDown)
    }, [open, onClose])

    if (!open) return null

    return (
        <div className="lg:hidden fixed inset-0 z-50" aria-hidden={!open}>
            <button
                type="button"
                className="absolute inset-0 bg-black/30"
                onClick={onClose}
                aria-label="Close inspector"
            />
            <div className="absolute inset-x-0 bottom-0 h-[78vh] rounded-t-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black shadow-2xl p-3">
                <ClaimInspectorPanel
                    claim={claim}
                    onClose={onClose}
                    explainabilityMode={explainabilityMode}
                    className="h-full"
                />
            </div>
        </div>
    )
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
    const [claimsView, setClaimsView] = useState<ClaimsView>('LIST')
    const [claimQuery, setClaimQuery] = useState('')

    const isLoading = phase === 'PROCESSING'

    useEffect(() => {
        if (phase !== 'PROCESSING') return

        setCurrentStep(0)
        const interval = setInterval(() => {
            setCurrentStep((prev) => {
                const next = prev + 1
                return next >= PROCESSING_STEPS.length ? PROCESSING_STEPS.length - 1 : next
            })
        }, 1200)

        return () => clearInterval(interval)
    }, [phase])

    useEffect(() => {
        if (phase !== 'RESULTS' || !selectedClaimId) return
        const scrollContainer = document.getElementById('source-document-scroll')
        if (!scrollContainer) return

        const target = scrollContainer.querySelector(`[data-claim-id="${selectedClaimId}"]`) as HTMLElement | null
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' })
        }
    }, [phase, selectedClaimId, result?.claims])

    const ensureBackendReady = async (): Promise<boolean> => {
        if (typeof window !== 'undefined' && sessionStorage.getItem(HEALTH_CACHE_KEY) === 'ok') {
            return true
        }

        for (const delay of HEALTH_BACKOFF_MS) {
            await sleep(delay)
            try {
                const response = await fetch('/api/health', { cache: 'no-store' })
                if (!response.ok) continue

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

    const handleAudit = async (text: string) => {
        setError(null)
        setSourceText(text)
        setResult(null)
        setSelectedClaimId(null)
        setClaimsView('LIST')
        setClaimQuery('')

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
            const firstClaimId = data?.claims?.[0]?.claim_id || null
            setSelectedClaimId(firstClaimId)
            setPhase('RESULTS')
        } catch (e: any) {
            setError(e.message)
            setPhase('INPUT')
        }
    }

    const resetAudit = () => {
        setResult(null)
        setPhase('INPUT')
        setSelectedClaimId(null)
        setCurrentStep(0)
        setClaimQuery('')
        setClaimsView('LIST')
        setError(null)
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

    const allClaims = useMemo(() => result?.claims || [], [result])

    const filteredClaims = useMemo(() => {
        const q = claimQuery.trim().toLowerCase()
        if (!q) return allClaims
        return allClaims.filter((claim: any) => {
            const verdict = claim?.verification?.verdict || ''
            return (
                String(claim?.claim_text || '').toLowerCase().includes(q) ||
                String(claim?.predicate || '').toLowerCase().includes(q) ||
                String(verdict).toLowerCase().includes(q)
            )
        })
    }, [allClaims, claimQuery])

    const selectedClaim = useMemo(() => {
        if (!allClaims.length || !selectedClaimId) return null
        return allClaims.find((c: any) => c.claim_id === selectedClaimId) || null
    }, [allClaims, selectedClaimId])

    const sourceLength = sourceText.length

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-black text-slate-900 dark:text-slate-100 transition-colors duration-300">
            <header className="sticky top-0 z-30 border-b border-slate-200 dark:border-white/10 bg-white/95 dark:bg-black/95 backdrop-blur">
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold tracking-tight">Epistemic Audit</div>
                    <div className="flex items-center gap-2 sm:gap-3">
                        <ExplainabilityToggle mode={explainabilityMode} onChange={setExplainabilityMode} />
                        <div className="inline-flex rounded-md border border-slate-200 dark:border-white/10 p-0.5 bg-slate-100 dark:bg-white/5">
                            <button
                                onClick={() => setMode('DEMO')}
                                className={`px-2.5 py-1 text-xs font-medium rounded ${mode === 'DEMO' ? 'bg-white dark:bg-black text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
                            >
                                Demo
                            </button>
                            <button
                                onClick={() => setMode('RESEARCH')}
                                className={`px-2.5 py-1 text-xs font-medium rounded ${mode === 'RESEARCH' ? 'bg-white dark:bg-black text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
                            >
                                Research
                            </button>
                        </div>
                        <button
                            onClick={resetAudit}
                            className="text-xs sm:text-sm px-3 py-1.5 rounded-md border border-slate-200 dark:border-white/10 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5"
                        >
                            New audit
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-[1600px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
                {phase === 'INPUT' ? (
                    <div className="max-w-3xl mx-auto pt-10 sm:pt-16">
                        <div className="text-center mb-8">
                            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Start an Audit</h1>
                            <p className="mt-3 text-slate-500 dark:text-slate-400 text-base sm:text-lg">Submit text to evaluate factual support and contradictions.</p>
                        </div>

                        <div className="rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black p-4 sm:p-6">
                            <AuditInput onAudit={handleAudit} isLoading={isLoading} />
                        </div>

                        {error ? (
                            <div className="mt-4 rounded-lg border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 px-4 py-3 text-sm text-center">
                                {error}
                            </div>
                        ) : null}
                    </div>
                ) : null}

                {phase === 'PROCESSING' ? (
                    <div className="max-w-2xl mx-auto pt-16 sm:pt-24">
                        <div className="rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black p-6 sm:p-8">
                            <div className="flex items-center justify-center mb-6">
                                <Loader2 className="w-8 h-8 text-slate-700 dark:text-slate-300 animate-spin" />
                            </div>

                            <div className="flex items-center justify-center gap-2 flex-wrap mb-5">
                                {PROCESSING_STEPS.map((step, idx) => {
                                    const Icon = step.icon
                                    const isActive = idx === currentStep
                                    const isComplete = idx < currentStep
                                    return (
                                        <div
                                            key={step.id}
                                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] border ${
                                                isActive
                                                    ? 'border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-white/10 text-slate-800 dark:text-slate-200'
                                                    : isComplete
                                                        ? 'border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-white/5 text-slate-500 dark:text-slate-400'
                                                        : 'border-slate-200 dark:border-white/10 text-slate-400 dark:text-slate-500'
                                            }`}
                                        >
                                            {isComplete ? <CheckCircle2 className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
                                            <span>{step.label}</span>
                                        </div>
                                    )
                                })}
                            </div>

                            <p className="text-center text-sm sm:text-base font-medium text-slate-800 dark:text-slate-100">
                                {PROCESSING_STEPS[currentStep]?.label || PROCESSING_STEPS[0].label}
                            </p>
                            <p className="text-center mt-1 text-xs text-slate-500 dark:text-slate-400">
                                {mode === 'DEMO' ? 'Running Demo mode with a fast verification budget.' : 'Running Research mode with full verification depth.'}
                            </p>
                        </div>
                    </div>
                ) : null}

                {phase === 'RESULTS' && result ? (
                    <div className="space-y-4">
                        <AuditSummary overallRisk={finalLabel} hallucinationScore={finalScore} summary={normalizedSummary} />

                        <div className="grid grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)_360px] gap-4 items-start">
                            <aside className="rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black h-[calc(100vh-200px)] min-h-[520px] overflow-hidden flex flex-col">
                                <div className="p-4 border-b border-slate-200 dark:border-white/10 space-y-3">
                                    <div className="flex items-center justify-between gap-2">
                                        <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Claims</h2>
                                        <span className="text-xs text-slate-500 dark:text-slate-400">{filteredClaims.length}/{allClaims.length}</span>
                                    </div>
                                    <div className="relative">
                                        <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                                        <input
                                            value={claimQuery}
                                            onChange={(e) => setClaimQuery(e.target.value)}
                                            placeholder="Search claims"
                                            className="w-full pl-8 pr-3 py-2 text-sm rounded-md border border-slate-200 dark:border-white/10 bg-white dark:bg-black text-slate-800 dark:text-slate-100 placeholder:text-slate-400"
                                        />
                                    </div>
                                    <div className="inline-flex rounded-md border border-slate-200 dark:border-white/10 p-0.5 bg-slate-100 dark:bg-white/5">
                                        <button
                                            onClick={() => setClaimsView('LIST')}
                                            className={`px-2.5 py-1 text-xs font-medium rounded ${claimsView === 'LIST' ? 'bg-white dark:bg-black text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
                                        >
                                            List
                                        </button>
                                        <button
                                            onClick={() => setClaimsView('TIMELINE')}
                                            className={`px-2.5 py-1 text-xs font-medium rounded ${claimsView === 'TIMELINE' ? 'bg-white dark:bg-black text-slate-900 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-400'}`}
                                        >
                                            Timeline
                                        </button>
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto p-3">
                                    {claimsView === 'LIST' ? (
                                        <div className="space-y-2">
                                            {filteredClaims.map((claim: any) => {
                                                const verdict = claim?.verification?.verdict || 'UNCERTAIN'
                                                const sources = claimSourceMeta(claim)
                                                const isActive = selectedClaimId === claim.claim_id

                                                return (
                                                    <button
                                                        key={claim.claim_id}
                                                        onClick={() => setSelectedClaimId(claim.claim_id)}
                                                        className={`w-full text-left rounded-lg border px-3 py-2.5 transition ${
                                                            isActive
                                                                ? 'border-slate-400 dark:border-slate-500 bg-slate-50 dark:bg-white/10'
                                                                : 'border-slate-200 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/5'
                                                        }`}
                                                    >
                                                        <div className="flex items-center justify-between gap-2 mb-1.5">
                                                            <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${verdictChipStyle(verdict)}`}>
                                                                {verdictLabel(verdict)}
                                                            </span>
                                                            <span className="inline-flex items-center gap-1 text-slate-400">
                                                                {sources.map((source) => {
                                                                    const Icon = source.Icon
                                                                    return (
                                                                        <span key={`${claim.claim_id}-${source.key}`} title={`${source.label}: ${source.count}`} className="inline-flex items-center gap-0.5">
                                                                            <Icon className="w-3 h-3" />
                                                                            <span className="text-[10px]">{source.count}</span>
                                                                        </span>
                                                                    )
                                                                })}
                                                            </span>
                                                        </div>
                                                        <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-200 line-clamp-1">
                                                            {claim.claim_text}
                                                        </p>
                                                    </button>
                                                )
                                            })}
                                            {filteredClaims.length === 0 ? (
                                                <p className="text-xs text-slate-500 dark:text-slate-400 px-1 py-2">No claims match your search.</p>
                                            ) : null}
                                        </div>
                                    ) : (
                                        <TimelineView
                                            claims={filteredClaims}
                                            onClaimClick={setSelectedClaimId}
                                            activeClaimId={selectedClaimId}
                                            explainabilityMode={explainabilityMode}
                                        />
                                    )}
                                </div>
                            </aside>

                            <section className="rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black min-h-[520px] h-[calc(100vh-200px)] overflow-hidden flex flex-col">
                                <div className="h-14 px-4 border-b border-slate-200 dark:border-white/10 flex items-center justify-between gap-3">
                                    <div>
                                        <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">Source</div>
                                        <div className="text-xs text-slate-500 dark:text-slate-400">{sourceLength.toLocaleString()} characters</div>
                                    </div>
                                    <button
                                        onClick={() => navigator.clipboard?.writeText(sourceText)}
                                        className="text-xs px-2.5 py-1.5 rounded-md border border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5"
                                    >
                                        Copy
                                    </button>
                                </div>
                                <div id="source-document-scroll" className="flex-1 overflow-y-auto py-8 px-5 sm:px-8">
                                    <AuditedText
                                        sourceText={sourceText}
                                        claims={allClaims}
                                        mode={mode}
                                        selectedClaimId={selectedClaimId}
                                        onSelectClaim={setSelectedClaimId}
                                        explainabilityMode={explainabilityMode}
                                        showInlineInspector={false}
                                    />
                                </div>
                            </section>

                            <aside className="hidden lg:block rounded-xl border border-slate-200 dark:border-white/10 bg-white dark:bg-black h-[calc(100vh-200px)] min-h-[520px] overflow-hidden">
                                <ClaimInspectorPanel
                                    claim={selectedClaim}
                                    explainabilityMode={explainabilityMode}
                                    className="h-full rounded-none border-0"
                                />
                            </aside>
                        </div>
                    </div>
                ) : null}
            </main>

            <MobileInspectorDrawer
                open={Boolean(selectedClaim)}
                claim={selectedClaim}
                explainabilityMode={explainabilityMode}
                onClose={() => setSelectedClaimId(null)}
            />
        </div>
    )
}
