"use client"
import React, { useEffect, useState } from 'react'
import { ShieldCheck, Activity, AlertOctagon, BookOpen, AlertTriangle } from 'lucide-react'

// Custom hook for scroll progress
function useScrollProgress() {
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        const handleScroll = () => {
            const totalHeight = document.documentElement.scrollHeight - window.innerHeight
            const scrollPosition = window.scrollY
            setProgress(totalHeight > 0 ? scrollPosition / totalHeight : 0)
        }

        window.addEventListener('scroll', handleScroll, { passive: true })
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    return progress
}

export default function InfoPage() {
    const scrollProgress = useScrollProgress()

    return (
        <div className="max-w-4xl mx-auto py-16 px-6 bg-noise min-h-screen font-sans relative">

            {/* Scroll Progress Indicator - CSS only */}
            <div
                className="fixed top-0 left-0 h-1 bg-gradient-to-r from-emerald-500 to-emerald-400 z-50 transition-transform duration-100"
                style={{ width: `${scrollProgress * 100}%` }}
            />

            {/* Dark Mode Safe Container */}
            <div className="
                relative z-10
                bg-white/90 dark:bg-neutral-900/85
                backdrop-blur-xl
                rounded-2xl
                border border-slate-200 dark:border-white/10
                p-8 md:p-12
                shadow-sm
                animate-in fade-in slide-in-from-bottom-4 duration-700
            ">

                {/* Header */}
                <div className="mb-20 border-b border-slate-200 dark:border-white/10 pb-8">
                    <div className="text-xs font-mono font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-4">
                        Technical Documentation v1.1
                    </div>
                    <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-4 tracking-tight">Epistemic Audit Protocol</h1>
                    <p className="text-xl text-slate-500 dark:text-slate-300 font-light max-w-2xl leading-relaxed">
                        Standard operating procedures for the verification of analytical integrity in AI-generated text.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-12 gap-12">

                    {/* Sidebar Navigation */}
                    <div className="md:col-span-3">
                        <nav className="sticky top-12 space-y-1">
                            <NavHeader>Sections</NavHeader>
                            <NavLink href="#scope">1. Operational Scope</NavLink>
                            <NavLink href="#lifecycle">2. Verification Lifecycle</NavLink>
                            <NavLink href="#taxonomy">3. Hallucination Taxonomy</NavLink>
                            <NavLink href="#polarity">4. Epistemic Polarity</NavLink>
                            <NavLink href="#scoring">5. Risk Calibration</NavLink>
                            <NavLink href="#limits">6. System Limits</NavLink>
                        </nav>
                    </div>

                    {/* Content */}
                    <div className="md:col-span-9 space-y-20">

                        {/* 1. Scope */}
                        <section id="scope">
                            <SectionHeader number="01" title="Operational Scope" />
                            <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-6">
                                The Epistemic Audit Engine is a post-generation integrity layer. It evaluates text not for semantic quality,
                                but for <strong>evidentiary support</strong>. Its primary function is to detect and flag instances where
                                language certainty exceeds the available structured evidence.
                            </p>
                            <div className="bg-slate-50 dark:bg-neutral-900 border border-slate-100 dark:border-white/10 rounded-lg p-6 grid grid-cols-1 sm:grid-cols-2 gap-8">
                                <div>
                                    <div className="font-semibold text-slate-900 dark:text-slate-100 mb-2 text-sm flex items-center gap-2">
                                        <ShieldCheck className="w-4 h-4 text-green-600" /> System Capabilities
                                    </div>
                                    <ul className="text-sm text-slate-600 dark:text-slate-300 space-y-2 list-disc list-inside">
                                        <li>Consistency verification vs. Graph</li>
                                        <li>Grounding of specific entities</li>
                                        <li>Detection of false precision</li>
                                        <li>Calibration of confidence intervals</li>
                                    </ul>
                                </div>
                                <div>
                                    <div className="font-semibold text-slate-900 dark:text-slate-100 mb-2 text-sm flex items-center gap-2">
                                        <AlertTriangle className="w-4 h-4 text-amber-500" /> Out of Scope
                                    </div>
                                    <ul className="text-sm text-slate-600 dark:text-slate-300 space-y-2 list-disc list-inside">
                                        <li>Moral or ethical judgment</li>
                                        <li>Subjective literary critique</li>
                                        <li>Binary &quot;Truth&quot; determination</li>
                                        <li>Intent analysis</li>
                                    </ul>
                                </div>
                            </div>
                        </section>

                        {/* 3. Taxonomy */}
                        <section id="taxonomy">
                            <SectionHeader number="03" title="Hallucination Taxonomy" />
                            <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-8">
                                The engine classifies epistemic failures into six distinct codes.
                                These codes determine the severity of the risk score penalty.
                            </p>

                            <div className="border border-slate-200 dark:border-white/10 rounded-lg overflow-hidden bg-white dark:bg-neutral-900 shadow-sm">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 dark:bg-neutral-800 border-b border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-200 font-medium">
                                        <tr>
                                            <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider">Code</th>
                                            <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider">Type</th>
                                            <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider">Definition</th>
                                            <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider hidden sm:table-cell">Example</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                                        <TableRow code="H1" type="Unsupported Assertion" def="Fact stated without evidence" ex="&quot;X is proven to be Y&quot;" />
                                        <TableRow code="H2" type="False Precision" def="Fabricated specificity" ex="&quot;97.32% effective&quot;" />
                                        <TableRow code="H3" type="Overconfidence" def="Certainty > Evidence" ex="&quot;Definitely caused&quot;" />
                                        <TableRow code="H4" type="Illegitimate Inference" def="Unsupported causality" ex="&quot;X caused Y&quot;" />
                                        <TableRow code="H5" type="Cross-Claim Inconsistency" def="Internal contradiction" ex="Claims disagree" />
                                        <TableRow code="H6" type="Narrative Laundering" def="Opinion presented as fact" ex="Editorial tone" />
                                    </tbody>
                                </table>
                            </div>
                        </section>

                        {/* 5. Scoring */}
                        <section id="scoring">
                            <SectionHeader number="05" title="Risk Scoring & Humility" />
                            <div className="prose prose-slate dark:prose-invert text-slate-600 dark:text-slate-300 max-w-none">
                                <p>
                                    The <strong>Epistemic Risk Score (0.0 - 1.0)</strong> is a composite metric derived from the weighted sum of
                                    hallucination penalties, normalized by document length.
                                </p>
                                <div className="my-6 p-6 bg-slate-900 dark:bg-neutral-800 text-slate-300 dark:text-slate-200 rounded-xl border border-slate-800 dark:border-white/10 relative overflow-hidden">
                                    {/* Subtle glow accent */}
                                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500/50 via-emerald-500/20 to-transparent" />
                                    <h4 className="text-white font-semibold mb-2 text-sm">The Humility Bonus</h4>
                                    <p className="text-sm leading-relaxed">
                                        The system rewards epistemic hygiene. If a text contains a claim that cannot be verified,
                                        but the language used is appropriately tentative (e.g., &quot;suggests,&quot; &quot;likely,&quot; &quot;sources indicate&quot;),
                                        the penalty is reduced by up to 50%. This incentivizes <strong>calibrated uncertainty</strong> over
                                        unsupported confidence.
                                    </p>
                                </div>
                            </div>
                        </section>

                        {/* 6. Limits */}
                        <section id="limits">
                            <SectionHeader number="06" title="System Limits & Liability" />
                            <div className="p-6 border-l-4 border-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-r-lg">
                                <h3 className="font-bold text-amber-900 dark:text-amber-100 mb-2 flex items-center gap-2">
                                    <AlertOctagon className="w-5 h-5" /> Human-in-the-Loop Required
                                </h3>
                                <p className="text-amber-800 dark:text-amber-200/80 text-sm leading-relaxed">
                                    This tool is a decision-support instrument, not a decision-maker.
                                    It should never be effectively used to automate censorship, moderation, or publishing decisions
                                    without expert review. Hallucination detection is probabilistic, not deterministic.
                                </p>
                            </div>
                        </section>

                    </div>
                </div>
            </div>
        </div>
    )
}

// Components
function SectionHeader({ number, title }: any) {
    return (
        <div className="flex items-center gap-4 mb-6">
            <span className="text-xs font-mono font-bold text-slate-300 dark:text-slate-600">{number}</span>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">{title}</h2>
        </div>
    )
}

function NavHeader({ children }: any) {
    return <div className="px-3 py-2 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">{children}</div>
}

function NavLink({ href, children }: any) {
    return (
        <a href={href} className="block px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-white/5 rounded transition-colors">
            {children}
        </a>
    )
}

function TableRow({ code, type, def, ex }: any) {
    return (
        <tr className="group hover:bg-slate-50/50 dark:hover:bg-white/5 transition-colors">
            <td className="px-6 py-4 font-mono text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-neutral-800/30 group-hover:bg-slate-100/50 dark:group-hover:bg-white/10">{code}</td>
            <td className="px-6 py-4 font-semibold text-slate-800 dark:text-slate-200">{type}</td>
            <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{def}</td>
            <td className="px-6 py-4 text-slate-500 dark:text-slate-400 font-mono text-xs hidden sm:table-cell opacity-75">{ex}</td>
        </tr>
    )
}
