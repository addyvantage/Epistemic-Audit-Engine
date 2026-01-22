"use client"
import React, { useState } from 'react'
import { EpistemicHighlight } from './EpistemicHighlight'
import { ClaimInspector } from './ClaimInspector'

interface AuditedTextProps {
    sourceText: string
    claims: any[]
    mode?: "DEMO" | "RESEARCH"
}

export function AuditedText({ sourceText, claims, mode = "DEMO" }: AuditedTextProps) {
    const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null)

    // Naive text segmenter: Split text by finding claim occurrences
    // In a real production system, backend would return offsets.
    // Here we assume sequential finding for v1.2 constraints.

    const renderText = () => {
        let lastIndex = 0
        const elements = []

        // Sort claims by order? Assumed ordered.
        // We need to match claim text to source text unique occurrences.
        // This is heuristic-based because fragments might repeat.

        // Strategy: Greedy match from lastIndex.
        for (const claim of claims) {
            const txt = claim.claim_text
            const idx = sourceText.indexOf(txt, lastIndex)

            if (idx !== -1) {
                // Push plain text before
                if (idx > lastIndex) {
                    elements.push(<span key={`text-${lastIndex}`}>{sourceText.slice(lastIndex, idx)}</span>)
                }

                // Push Highlighted Claim
                elements.push(
                    <EpistemicHighlight
                        key={claim.claim_id}
                        claimId={claim.claim_id}
                        isActive={selectedClaimId === claim.claim_id}
                        verdict={claim.verification.verdict}
                        polarity={claim.epistemic_polarity}
                        onClick={() => setSelectedClaimId(claim.claim_id)}
                    >
                        {sourceText.slice(idx, idx + txt.length)}
                    </EpistemicHighlight>
                )

                lastIndex = idx + txt.length
            }
        }

        // Remaining text
        if (lastIndex < sourceText.length) {
            elements.push(<span key={`text-${lastIndex}`}>{sourceText.slice(lastIndex)}</span>)
        }

        return elements
    }

    const activeClaim = claims.find(c => c.claim_id === selectedClaimId)

    return (
        <div className="relative">
            <div className="prose prose-slate max-w-3xl mx-auto leading-loose text-slate-800 bg-white p-8 rounded-xl shadow-sm border border-slate-100 font-serif">
                {claims.length > 0 ? renderText() : sourceText}
            </div>

            {/* Overlay Inspector */}
            {selectedClaimId && (
                <ClaimInspector
                    claim={activeClaim}
                    onClose={() => setSelectedClaimId(null)}
                    mode={mode}
                />
            )}
        </div>
    )
}
