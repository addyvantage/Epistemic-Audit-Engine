"use client"
import React from 'react'
import { AuditedText } from '@/components/AuditedText'

export default function TestPage() {
    const sourceText = `Google was founded in 1998 by Larry Page. Critics argue that it is a monopoly. It is an amazing company. Some say it controls the internet. It was created in a garage.`

    // Indices (approx):
    // "Google was founded in 1998" -> 0 to 26
    // "Critics argue that it is a monopoly" -> 42 to 78
    // "it is a monopoly" -> 61 to 77 (Contested)
    // "amazing" -> 89 to 96 (Evaluative)
    // "controls the internet" -> 114 to 135 (Meta-discourse / Narrative)
    // "created" -> 144 to 151 (Derived/Implicit)

    // Simulating Backend Response
    const mockClaims = [
        {
            claim_id: "c1",
            claim_text: "Google was founded in 1998",
            claim_type: "TEMPORAL",
            epistemic_status: "VERIFIED",
            verification: { verdict: "SUPPORTED", confidence: 0.95 },
            epistemic_polarity: "OBJECT_LEVEL"
        },
        {
            claim_id: "c2",
            claim_text: "it is a monopoly",
            claim_type: "RELATION",
            epistemic_status: "CONTESTED", // Fix 2
            verification: { verdict: "INSUFFICIENT_EVIDENCE", confidence: 0.0 }, // Contested usually unverified
            epistemic_polarity: "OBJECT_LEVEL"
        },
        {
            claim_id: "c3",
            claim_text: "amazing",
            claim_type: "FACTUAL_ATTRIBUTE", // Evaluative
            epistemic_status: "ASSERTED",
            verification: { verdict: "INSUFFICIENT_EVIDENCE", confidence: 0.0 },
            epistemic_polarity: "OBJECT_LEVEL"
        },
        {
            claim_id: "c4",
            claim_text: "controls the internet",
            claim_type: "RELATION", // Narrative
            epistemic_status: "ASSERTED",
            verification: { verdict: "REFUTED", confidence: 0.8 },
            epistemic_polarity: "OBJECT_LEVEL"
        },
        {
            claim_id: "c5",
            claim_text: "created in a garage", // Derived/Implicit
            claim_type: "TEMPORAL",
            epistemic_status: "ASSERTED",
            verification: { verdict: "SUPPORTED_WEAK", confidence: 0.7 },
            epistemic_polarity: "OBJECT_LEVEL",
            highlight_type: "IMPLICIT_FACT" // Fix 3
        }
    ]

    return (
        <div className="min-h-screen bg-slate-50 p-12">
            <h1 className="text-3xl font-bold mb-8">Epistemic Highlighting Test Suite</h1>

            <div className="mb-12">
                <h2 className="text-xl font-bold mb-4">Legend</h2>
                <div className="flex gap-4 text-sm">
                    <span className="px-3 py-1 bg-green-100 rounded border border-green-200">Supported</span>
                    <span className="px-3 py-1 bg-amber-100 rounded border border-amber-200">Uncertain</span>
                    <span className="px-3 py-1 bg-red-100 rounded border border-red-200">Refuted</span>
                    <span className="px-3 py-1 border-b-2 border-dotted border-slate-500 italic">Contested (Subtle)</span>
                    <span className="px-3 py-1 text-slate-400">Evaluative (Ignored)</span>
                </div>
            </div>

            <AuditedText sourceText={sourceText} claims={mockClaims} mode="RESEARCH" />
        </div>
    )
}
