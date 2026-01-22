import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

const AuditedTextView = ({ text, claims, onSelectClaim, selectedClaimId }) => {
    // 1. Map text to segments (Sentences)
    // We assume claims cover the text coverage we care about (sentences).
    // We need to handle gaps (non-declarative sentences?) -> Render as plain text.

    const segments = useMemo(() => {
        if (!text || !claims) return [];

        // Group claims by unique span (start, end)
        const spanMap = {};
        claims.forEach(claim => {
            const range = `${claim.span.start}-${claim.span.end}`;
            if (!spanMap[range]) {
                spanMap[range] = {
                    start: claim.span.start,
                    end: claim.span.end,
                    claims: []
                };
            }
            spanMap[range].claims.push(claim);
        });

        // Convert to list and sort
        const spanList = Object.values(spanMap).sort((a, b) => a.start - b.start);

        // Fill gaps with plain text
        const finalSegments = [];
        let cursor = 0;

        spanList.forEach(span => {
            if (span.start > cursor) {
                // Gap
                finalSegments.push({
                    text: text.slice(cursor, span.start),
                    type: 'raw',
                    start: cursor
                });
            }

            // Sentence Segment
            finalSegments.push({
                text: text.slice(span.start, span.end),
                type: 'audit',
                claims: span.claims,
                start: span.start,
                end: span.end
            });
            cursor = span.end;
        });

        if (cursor < text.length) {
            finalSegments.push({
                text: text.slice(cursor),
                type: 'raw',
                start: cursor
            });
        }

        return finalSegments;

    }, [text, claims]);

    const getSegmentStyle = (segmentClaims) => {
        // Aggregation Logic
        // Priority: Refuted > Hallucinated > Insufficient > SupportedWeak > Supported

        // Define all used variables to avoid ReferenceError
        let hasRefuted = false;
        let hasHallucination = false;
        let hasInsufficient = false;
        let hasSupportedWeak = false;
        let hasSupported = false;

        segmentClaims.forEach(c => {
            const v = c.verification?.verdict;
            const h = c.hallucinations?.length > 0;

            if (v === 'REFUTED') hasRefuted = true;
            if (h) hasHallucination = true;
            if (v === 'INSUFFICIENT_EVIDENCE') hasInsufficient = true;
            if (v === 'SUPPORTED_WEAK') hasSupportedWeak = true;
            if (v === 'SUPPORTED') hasSupported = true;
        });

        const isSelected = selectedClaimId && segmentClaims.some(c => c.claim_id === selectedClaimId);

        let classes = "transition-all duration-300 cursor-pointer border-b-2 ";

        if (isSelected) {
            classes += " bg-white/10 shadow-[0_0_15px_rgba(255,255,255,0.1)] ";
        } else {
            classes += " hover:bg-white/5 ";
        }

        if (hasRefuted) {
            return classes + "border-rose-500 bg-rose-500/10 font-bold decoration-rose-500/50";
        }
        if (hasHallucination) {
            // H6 Purple, H1-H4 Red/Amber? Design says H1/H4 Red Glow.
            return classes + "border-purple-500 bg-purple-500/10 italic decoration-purple-500/50";
        }
        if (hasInsufficient) {
            return classes + "border-amber-500 border-dashed bg-amber-500/5 decoration-amber-500/50";
        }
        if (hasSupportedWeak) {
            return classes + "border-lime-500 bg-lime-500/5 decoration-lime-500/50";
        }
        if (hasSupported) {
            return classes + "border-emerald-500 bg-emerald-500/5 decoration-emerald-500/50";
        }

        return classes + "border-slate-700";
    };

    return (
        <div className="font-serif text-lg leading-loose text-slate-300 whitespace-pre-wrap">
            {segments.map((seg, i) => {
                if (seg.type === 'raw') {
                    return <span key={i} className="opacity-60">{seg.text}</span>;
                }

                // Audit Segment
                const claimIds = seg.claims.map(c => c.claim_id);

                // Determine Interaction
                const handleClick = () => {
                    onSelectClaim(claimIds[0]); // Select first claim by default or toggle list?
                };

                return (
                    <motion.span
                        key={i}
                        id={`text-claim-${claimIds[0]}`}
                        className={getSegmentStyle(seg.claims)}
                        onClick={handleClick}
                        whileHover={{ scale: 1.005 }}
                    >
                        {seg.text}
                        {/* Inline Badges? Maybe too noisy. Just highlight. */}
                    </motion.span>
                );
            })}
        </div>
    );
};

export default AuditedTextView;
