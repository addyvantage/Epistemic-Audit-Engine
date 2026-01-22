import React, { useState } from 'react';
import { auditText } from '../api/audit';
import RiskSummary from '../components/RiskSummary';
import ClaimCard from '../components/ClaimCard';
import AuditedTextView from '../components/AuditedTextView';
import { Loader2, RefreshCw } from 'lucide-react';

const AuditPage = () => {
    const [input, setInput] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedClaimId, setSelectedClaimId] = useState(null);

    const handleAudit = async () => {
        if (!input.trim()) return;
        setLoading(true);
        setError(null);
        setSelectedClaimId(null);
        try {
            const data = await auditText(input);
            setResult(data);
        } catch (err) {
            setError("Audit failed. Ensure backend is running.");
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setResult(null);
        setError(null);
        setSelectedClaimId(null);
    };

    const handleLocate = (claim) => {
        setSelectedClaimId(claim.claim_id);
        setTimeout(() => {
            const el = document.getElementById(`text-claim-${claim.claim_id}`);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    };

    const handleClaimSelect = (claimId) => {
        setSelectedClaimId(claimId);
        setTimeout(() => {
            const el = document.getElementById(`card-claim-${claimId}`);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    };

    return (
        <div className="max-w-7xl mx-auto px-6 py-12">
            <header className="mb-8 flex justify-between items-end border-b border-slate-700 pb-6">
                <div>
                    <h1 className="text-4xl font-bold font-serif mb-2 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
                        Epistemic Audit Engine
                    </h1>
                    <p className="text-slate-400 font-mono text-sm">Phase 7: Inline Epistemic Highlighting</p>
                </div>
                {result && (
                    <button onClick={handleReset} className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm font-mono uppercase">
                        <RefreshCw className="w-4 h-4" /> New Audit
                    </button>
                )}
            </header>

            {!result ? (
                /* Input Mode */
                <div className="max-w-4xl mx-auto animate-fade-in-up">
                    <div className="relative mb-6">
                        <textarea
                            className="w-full h-64 bg-slate-900 border border-slate-700 rounded-xl p-6 font-serif text-lg leading-relaxed focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all resize-none shadow-inner text-slate-200"
                            placeholder="Paste text for epistemic verification..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                        />
                        <div className="absolute bottom-6 right-6 text-xs text-slate-500 font-mono">
                            {input.length} chars
                        </div>
                    </div>

                    <button
                        onClick={handleAudit}
                        disabled={loading || !input.trim()}
                        className="w-full py-4 bg-audit-accent hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-bold tracking-wide transition-all shadow-lg shadow-blue-500/20 flex justify-center items-center gap-2 text-white"
                    >
                        {loading ? <Loader2 className="animate-spin" /> : "RUN AUDIT SEQUENCE"}
                    </button>

                    {error && <div className="mt-4 p-4 bg-rose-500/10 text-rose-400 border border-rose-500/30 rounded-lg text-center">{error}</div>}
                </div>
            ) : (
                /* Report Mode (Phase 7 Layout) */
                <div className="animate-fade-in-up grid grid-cols-12 gap-8">
                    {/* Top: Audited Text View */}
                    <div className="col-span-12 bg-slate-900 rounded-xl border border-slate-700 p-8 shadow-2xl mb-8 relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 opacity-50"></div>
                        <h3 className="font-mono text-xs uppercase opacity-50 mb-4 tracking-widest">Source Text (Audited)</h3>
                        <AuditedTextView
                            text={input}
                            claims={result.claims}
                            onSelectClaim={handleClaimSelect}
                            selectedClaimId={selectedClaimId}
                        />
                    </div>

                    {/* Bottom Split: Risk & Claims */}
                    <div className="col-span-4 space-y-6">
                        <div className="sticky top-6">
                            <RiskSummary
                                risk={result.overall_risk}
                                score={result.hallucination_score}
                                summary={result.summary}
                            />

                            {/* Legend Panel */}
                            <div className="p-4 rounded-xl border border-slate-700 bg-slate-900/50 text-xs text-slate-400 space-y-2 font-mono">
                                <div className="flex items-center gap-2"><span className="w-3 h-3 bg-emerald-500/20 border border-emerald-500/50 rounded"></span> Supported</div>
                                <div className="flex items-center gap-2"><span className="w-3 h-3 bg-rose-500/20 border border-rose-500/50 rounded font-bold">R</span> Refuted</div>
                                <div className="flex items-center gap-2"><span className="w-3 h-3 bg-amber-500/20 border-b-2 border-dashed border-amber-500/50"></span> Insufficient</div>
                                <div className="flex items-center gap-2"><span className="w-3 h-3 bg-purple-500/20 border border-purple-500/50 rounded"></span> Hallucination</div>
                            </div>
                        </div>
                    </div>

                    <div className="col-span-8">
                        <div className="flex justify-between items-end border-b border-slate-700 pb-2 mb-6">
                            <h3 className="font-mono text-sm uppercase opacity-70">Claim Inspection ({result.claims.length})</h3>
                        </div>

                        <div className="space-y-4">
                            {result.claims
                                .sort((a, b) => {
                                    // Basic sort: Has Hallucination -> Refuted -> Insufficient -> Supported
                                    const scoreA = (a.hallucinations?.length || 0) * 10 + (a.verification.verdict === 'REFUTED' ? 5 : 0);
                                    const scoreB = (b.hallucinations?.length || 0) * 10 + (b.verification.verdict === 'REFUTED' ? 5 : 0);
                                    return scoreB - scoreA;
                                })
                                .map((claim) => (
                                    <ClaimCard
                                        key={claim.claim_id}
                                        claim={claim}
                                        onLocate={handleLocate}
                                        isSelected={selectedClaimId === claim.claim_id}
                                    />
                                ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AuditPage;
