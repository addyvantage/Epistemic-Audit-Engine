"use client"
import Link from 'next/link'
import { ArrowRight, ShieldCheck } from 'lucide-react'

export default function LandingPage() {
    return (
        <div className="min-h-[calc(100vh-140px)] flex flex-col items-center justify-center text-center px-4 relative overflow-hidden">
            {/* Subtle Background Glow - Static */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-50/50 rounded-full blur-3xl -z-10 pointer-events-none" />

            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium mb-6 border border-slate-200">
                    <ShieldCheck className="w-3 h-3" />
                    Research Preview v1.1
                </div>

                <h1 className="text-5xl md:text-6xl font-bold text-slate-900 tracking-tight mb-6 max-w-4xl mx-auto leading-tight">
                    Audit the epistemic integrity <br />
                    of AI-generated text.
                </h1>

                <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed font-light">
                    Not fact-checking. Not binary verification. <br />
                    A risk-aware analysis of confidence versus evidence.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link
                        href="/audit"
                        className="group relative inline-flex items-center justify-center px-8 py-3.5 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-all shadow-sm hover:shadow-md"
                    >
                        Start Audit
                        <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-0.5 transition-transform" />
                    </Link>

                    <Link
                        href="/info"
                        className="inline-flex items-center justify-center px-8 py-3.5 bg-white text-slate-600 text-sm font-medium rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
                    >
                        Learn Methodology
                    </Link>
                </div>
            </div>

            <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto text-left opacity-80">
                <div className="p-6 rounded-xl border border-slate-100 bg-white/50 backdrop-blur-sm">
                    <div className="text-xs font-mono text-slate-400 mb-2">01. DECOMPOSITION</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Atomic Claims</h3>
                    <p className="text-sm text-slate-500">Breaks text into falsifiable units, isolating facts from rhetoric.</p>
                </div>
                <div className="p-6 rounded-xl border border-slate-100 bg-white/50 backdrop-blur-sm">
                    <div className="text-xs font-mono text-slate-400 mb-2">02. VERIFICATION</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Structured Evidence</h3>
                    <p className="text-sm text-slate-500"> Checks against Wikidata knowledge graph, not just LLM consensus.</p>
                </div>
                <div className="p-6 rounded-xl border border-slate-100 bg-white/50 backdrop-blur-sm">
                    <div className="text-xs font-mono text-slate-400 mb-2">03. CALIBRATION</div>
                    <h3 className="font-semibold text-slate-800 mb-1">Epistemic Risk</h3>
                    <p className="text-sm text-slate-500">Penalizes overconfidence. Rewards epistemic humility.</p>
                </div>
            </div>
        </div>
    )
}
