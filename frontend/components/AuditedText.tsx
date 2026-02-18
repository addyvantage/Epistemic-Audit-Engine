import React, { useState, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { EpistemicHighlight } from './EpistemicHighlight'
import { ClaimInspector } from './ClaimInspector'

interface AuditedTextProps {
    sourceText: string
    claims: any[]
    mode?: "DEMO" | "RESEARCH"
    selectedClaimId?: string | null
    onSelectClaim?: (id: string | null) => void
    explainabilityMode?: 'CASUAL' | 'EXPERT'
    showInlineInspector?: boolean
}

import { EpistemicHoverCard } from './EpistemicHoverCard'

export function AuditedText({
    sourceText,
    claims,
    mode = "DEMO",
    selectedClaimId,
    onSelectClaim,
    explainabilityMode = 'CASUAL',
    showInlineInspector = true
}: AuditedTextProps) {
    const [hoveredClaim, setHoveredClaim] = useState<any | null>(null)
    const [hoverPos, setHoverPos] = useState({ x: 0, y: 0 })

    const handleMouseEnter = (claim: any, e: React.MouseEvent) => {
        setHoveredClaim(claim);
        setHoverPos({ x: e.clientX, y: e.clientY });
    };

    const handleFocus = (claim: any, e: React.FocusEvent) => {
        const rect = (e.target as HTMLElement).getBoundingClientRect();
        setHoveredClaim(claim);
        setHoverPos({ x: rect.left + rect.width / 2, y: rect.top });
    };

    const handleMouseLeave = () => {
        setHoveredClaim(null);
    };

    const handleBlur = () => {
        // Delay blur to allow clicking inside card if needed
        setTimeout(() => {
            setHoveredClaim(null);
        }, 100);
    };



    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                setHoveredClaim(null);
                onSelectClaim?.(null);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onSelectClaim]);

    // Naive text segmenter: Split text by finding claim occurrences
    // In a real production system, backend would return offsets.
    // Here we assume sequential finding for v1.2 constraints.

    // v1.3.2 FIX 2: Relax Eligibility (Highlight All Asserted)
    const ELIGIBLE_TYPES = ["TEMPORAL", "RELATION", "FACTUAL_ATTRIBUTE"]
    const ELIGIBLE_STATUS = ["ASSERTED", "VERIFIED", "CONTESTED"]
    const VALID_VERDICTS = ["SUPPORTED", "SUPPORTED_WEAK", "UNCERTAIN", "REFUTED"]

    const isEligible = (c: any) => {
        // Must be an active claim type
        if (!ELIGIBLE_TYPES.includes(c.claim_type)) return false

        // CONTESTED always shows
        if (c.epistemic_status === "CONTESTED") return true

        // META/NON_ASSERTIVE -> Context only (Gray) -> But usually excluded from Highlighting unless we want gray text?
        // User says "META_REPORTED -> gray italic (context only)". 
        // Previously we returned false. Now we might allow it but render differently? 
        // "Only exclude META_REPORTED / NON_ASSERTIVE" -> So return FALSE for them.
        if (c.claim_type === "META_REPORTED" || c.epistemic_status === "NON_ASSERTIVE") return false

        // ASSERTED claims MUST be highlighted regardless of verdict (unless filtered above)
        // Check if verdict exists? Even if pending, we highlight.
        // But usually pipeline produces verdict.
        return true
    }

    // v1.3.2 FIX 1: Normalized Fuzzy Matcher
    const normalize = (s: string) => {
        return s.toLowerCase()
            .replace(/[^\w\s]/g, "")
            .replace(/\s+/g, " ")
            .trim()
    }

    const findApproximateSpan = (source: string, claimText: string, searchFrom: number): { start: number, end: number, score: number } | null => {
        const srcSlice = source.slice(searchFrom)
        const normClaim = normalize(claimText)
        const claimTokens = normClaim.split(" ").filter(t => t.length > 2) // Ignore very short words

        if (claimTokens.length === 0) return null

        // Sliding window strategy? 
        // Simplify: Find first occurrence of significant tokens.
        // Or strictly follow pseudocode: "tokenOverlap"

        // Heuristic: Try to find the sequence of tokens in reasonable proximity.
        // Given we don't have n-gram index, we scan.
        // But 'indexOf' on normalized string is a good first step.

        const normSrc = normalize(srcSlice)
        const idx = normSrc.indexOf(normClaim)

        // Strategy: First try simple normalized index (fastest)
        if (idx !== -1) {
            // ... (existing mapped logic or just return it?) 
            // Without mapping, we don't have original indices.
            // So we still need regex or heuristic mapping.
            // Let's just fall through to Regex if simple match fails to give indices, 
            // OR use regex as primary method for "Approximate Span".
        }

        // Regex Search (Primary Fuzzy Mechanism)
        const pattern = claimTokens.map(t => {
            return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        }).join("[\\s\\S]{0,50}?")

        try {
            const regex = new RegExp(pattern, "i")
            const match = srcSlice.match(regex)
            if (match && match.index !== undefined) {
                return {
                    start: searchFrom + match.index,
                    end: searchFrom + match.index + match[0].length,
                    score: 1.0
                }
            }
        } catch (e) {
            // Regex fail
        }

        return null

        // Fallback: If strict token sequence fails, looking for high overlap?
        // User asked for token overlap in sliding window.
        // Optimization: Just look for the span that contains most tokens.
        return null
    }

    const renderText = () => {
        let lastIndex = 0
        const elements = []

        // v1.3.3 FIX: Pre-compute Spans and Sort
        // This solves the greedy ordering problem where earlier claims in text 
        // are processed later in the array.

        // v1.7 FIX: Dual Mode Highlighting
        // Mode A (Overview): No selection -> Show all eligible
        // Mode B (Focus): Selection -> Show only selected

        const claimsToRender = selectedClaimId
            ? claims.filter(c => c.claim_id === selectedClaimId)
            : claims.filter(isEligible);

        const preparedClaims = claimsToRender
            // We skip isEligible check ensures we can inspect even 'hidden' claims if explicitly selected
            .map(c => {
                // v1.4 FIX: Use Exact Backend Offsets
                if (typeof c.start_char === 'number' && typeof c.end_char === 'number') {
                    // Defensive Bounds Check
                    if (c.start_char < 0 || c.end_char > sourceText.length) {
                        return null
                    }
                    if (c.start_char >= c.end_char) {
                        return null
                    }
                    return { claim: c, start: c.start_char, end: c.end_char }
                }
                return null
            })
            .filter((item): item is { claim: any, start: number, end: number } => item !== null)
            .sort((a, b) => a.start - b.start)

        for (const item of preparedClaims) {
            const { claim, start, end } = item

            // v1.3.3 FIX 2: Relaxed Density Check (Non-Overlap)
            // Only skip if this claim effectively starts BEFORE the last one ended.
            // Allow small overlap? User suggested strict non-overlap `start < lastIndex`.
            // User fix 2 says "start < lastIndex continue".
            // User Fix 4 says "Allow small overlaps (option)". 
            // We'll stick to strict non-overlap for correctness first.

            if (start < lastIndex) continue

            // Text before
            if (start > lastIndex) {
                elements.push(<span key={`text-${lastIndex}`}>{sourceText.slice(lastIndex, start)}</span>)
            }

            // Determine styling
            const isContested = claim.epistemic_status === "CONTESTED"
            const isDerived = claim.is_derived || claim.highlight_type === "IMPLICIT_FACT"

            elements.push(
                <EpistemicHighlight
                    key={claim.claim_id}
                    claimId={claim.claim_id}
                    isActive={selectedClaimId === claim.claim_id}
                    verdict={claim.verification?.verdict || "UNCERTAIN"}
                    polarity={claim.epistemic_polarity}
                    isContested={isContested}
                    isDerived={isDerived}
                    onClick={() => onSelectClaim?.(claim.claim_id)}
                    onMouseEnter={(e) => handleMouseEnter(claim, e)}
                    onMouseLeave={handleMouseLeave}
                    onFocus={(e) => handleFocus(claim, e)}
                    onBlur={handleBlur}
                >
                    {sourceText.slice(start, end)}
                </EpistemicHighlight>
            )
            lastIndex = end
        }

        // Remaining
        if (lastIndex < sourceText.length) {
            elements.push(<span key={`text-${lastIndex}`}>{sourceText.slice(lastIndex)}</span>)
        }
        return elements
    }

    const activeClaim = claims.find(c => c.claim_id === selectedClaimId)

    return (
        <div className="relative">
            <div className="prose prose-slate dark:prose-invert max-w-3xl mx-auto leading-loose text-slate-700 dark:text-neutral-300 bg-transparent p-8 font-serif transition-colors duration-500">
                {claims.length > 0 ? renderText() : sourceText}
            </div>

            <AnimatePresence>
                {showInlineInspector && selectedClaimId && (
                    <ClaimInspector
                        key="inspector-sidebar" // Key is important for AnimatePresence
                        claim={activeClaim}
                        onClose={() => onSelectClaim?.(null)}
                        mode={mode}
                    />
                )}
            </AnimatePresence>

            <EpistemicHoverCard
                claim={hoveredClaim}
                position={hoverPos}
                visible={!!hoveredClaim}
                explainabilityMode={explainabilityMode}
            />
        </div>
    )
}
