import React from 'react'
import { ShieldCheck, Activity, AlertOctagon, BookOpen, AlertTriangle } from 'lucide-react'

export default function InfoPage() {
    return (
        <div className="max-w-4xl mx-auto py-16 px-6 bg-noise min-h-screen font-sans text-slate-800">

            {/* Header - Manual Style */}
            <div className="mb-20 border-b border-slate-200 pb-8">
                <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest mb-4">
                    Technical Documentation v1.1
                </div>
                <h1 className="text-4xl font-bold text-slate-900 mb-4 tracking-tight">Epistemic Audit Protocol</h1>
                <p className="text-xl text-slate-500 font-light max-w-2xl leading-relaxed">
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
                        <p className="text-slate-600 leading-relaxed mb-6">
                            The Epistemic Audit Engine is a post-generation integrity layer. It evaluates text not for semantic quality,
                            but for <strong>evidentiary support</strong>. Its primary function is to detect and flag instances where
                            language certainty exceeds the available structured evidence.
                        </p>
                        <div className="bg-slate-50 border border-slate-100 rounded-lg p-6 grid grid-cols-1 sm:grid-cols-2 gap-8">
                            <div>
                                <div className="font-semibold text-slate-900 mb-2 text-sm flex items-center gap-2">
                                    <ShieldCheck className="w-4 h-4 text-green-600" /> System Capabilities
                                </div>
                                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                                    <li>Consistency verification vs. Graph</li>
                                    <li>Grounding of specific entities</li>
                                    <li>Detection of false precision</li>
                                    <li>Calibration of confidence intervals</li>
                                </ul>
                            </div>
                            <div>
                                <div className="font-semibold text-slate-900 mb-2 text-sm flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4 text-amber-500" /> Out of Scope
                                </div>
                                <ul className="text-sm text-slate-600 space-y-2 list-disc list-inside">
                                    <li>Moral or ethical judgment</li>
                                    <li>Subjective literary critique</li>
                                    <li>Binary "Truth" determination</li>
                                    <li>Intent analysis</li>
                                </ul>
                            </div>
                        </div>
                    </section>

                    {/* 3. Taxonomy */}
                    <section id="taxonomy">
                        <SectionHeader number="03" title="Hallucination Taxonomy" />
                        <p className="text-slate-600 leading-relaxed mb-8">
                            The engine classifies epistemic failures into six distinct codes.
                            These codes determine the severity of the risk score penalty.
                        </p>

                        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-sm">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                                    <tr>
                                        <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider">Code</th>
                                        <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider">Type</th>
                                        <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider">Definition</th>
                                        <th className="px-6 py-3 font-mono text-xs uppercase tracking-wider hidden sm:table-cell">Example</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    <TableRow code="H1" type="Unsupported Assertion" def="Fact stated without evidence" ex="“X is proven to be Y”" />
                                    <TableRow code="H2" type="False Precision" def="Fabricated specificity" ex="“97.32% effective”" />
                                    <TableRow code="H3" type="Overconfidence" def="Certainty > Evidence" ex="“Definitely caused”" />
                                    <TableRow code="H4" type="Illegitimate Inference" def="Unsupported causality" ex="“X caused Y”" />
                                    <TableRow code="H5" type="Cross-Claim Inconsistency" def="Internal contradiction" ex="Claims disagree" />
                                    <TableRow code="H6" type="Narrative Laundering" def="Opinion presented as fact" ex="Editorial tone" />
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* 5. Scoring */}
                    <section id="scoring">
                        <SectionHeader number="05" title="Risk Scoring & Humility" />
                        <div className="prose prose-slate text-slate-600 max-w-none">
                            <p>
                                The <strong>Epistemic Risk Score (0.0 - 1.0)</strong> is a composite metric derived from the weighted sum of
                                hallucination penalties, normalized by document length.
                            </p>
                            <div className="my-6 p-6 bg-slate-900 text-slate-300 rounded-xl">
                                <h4 className="text-white font-semibold mb-2 text-sm">The Humility Bonus</h4>
                                <p className="text-sm leading-relaxed">
                                    The system rewards epistemic hygiene. If a text contains a claim that cannot be verified,
                                    but the language used is appropriately tentative (e.g., "suggests," "likely," "sources indicate"),
                                    the penalty is reduced by up to 50%. This incentivizes <strong>calibrated uncertainty</strong> over
                                    unsupported confidence.
                                </p>
                            </div>
                        </div>
                    </section>

                    {/* 6. Limits */}
                    <section id="limits">
                        <SectionHeader number="06" title="System Limits & Liability" />
                        <div className="p-6 border-l-4 border-amber-400 bg-amber-50">
                            <h3 className="font-bold text-amber-900 mb-2 flex items-center gap-2">
                                <AlertOctagon className="w-5 h-5" /> Human-in-the-Loop Required
                            </h3>
                            <p className="text-amber-800 text-sm leading-relaxed">
                                This tool is a decision-support instrument, not a decision-maker.
                                It should never be effectively used to automate censorship, moderation, or publishing decisions
                                without expert review. Hallucination detection is probabilistic, not deterministic.
                            </p>
                        </div>
                    </section>

                </div>
            </div>
        </div>
    )
}

// Components
function SectionHeader({ number, title }: any) {
    return (
        <div className="flex items-center gap-4 mb-6">
            <span className="text-xs font-mono font-bold text-slate-300">{number}</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{title}</h2>
        </div>
    )
}

function NavHeader({ children }: any) {
    return <div className="px-3 py-2 text-xs font-bold text-slate-400 uppercase tracking-widest">{children}</div>
}

function NavLink({ href, children }: any) {
    return (
        <a href={href} className="block px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded transition-colors">
            {children}
        </a>
    )
}

function TableRow({ code, type, def, ex }: any) {
    return (
        <tr className="group hover:bg-slate-50/50 transition-colors">
            <td className="px-6 py-4 font-mono text-xs font-bold text-slate-500 bg-slate-50/50 group-hover:bg-slate-100/50">{code}</td>
            <td className="px-6 py-4 font-semibold text-slate-800">{type}</td>
            <td className="px-6 py-4 text-slate-600">{def}</td>
            <td className="px-6 py-4 text-slate-500 font-mono text-xs hidden sm:table-cell opacity-75">{ex}</td>
        </tr>
    )
}
