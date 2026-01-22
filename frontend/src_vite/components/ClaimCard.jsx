import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, AlertTriangle, CheckCircle, XCircle, HelpCircle, Search } from 'lucide-react';
import HallucinationBadge from './HallucinationBadge';

const ClaimCard = ({ claim, onLocate, isSelected }) => {
    const [expanded, setExpanded] = useState(isSelected || false);
    const cardRef = React.useRef(null);

    useEffect(() => {
        if (isSelected) {
            setExpanded(true);
            // Scroll to card if selected (optional, if we want bidirectional sync)
            cardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [isSelected]);

    const { claim_text, verification, hallucinations, subject_entity, object_entity, evidence } = claim;
    const verdict = verification?.verdict || "UNKNOWN";
    const confidence = verification?.confidence || 0.0;

    const getVerdictColor = (v) => {
        if (v === 'SUPPORTED') return 'text-emerald-400 border-l-4 border-emerald-500 bg-emerald-900/10';
        if (v === 'SUPPORTED_WEAK') return 'text-lime-400 border-l-4 border-lime-500 bg-lime-900/10';
        if (v === 'REFUTED') return 'text-rose-400 border-l-4 border-rose-500 bg-rose-900/10';
        return 'text-amber-400 border-l-4 border-amber-500 bg-amber-900/10';
    };

    const StatusIcon = () => {
        if (verdict === 'SUPPORTED') return <CheckCircle className="w-5 h-5 text-emerald-500" />;
        if (verdict === 'SUPPORTED_WEAK') return <CheckCircle className="w-5 h-5 text-lime-500" />;
        if (verdict === 'REFUTED') return <XCircle className="w-5 h-5 text-rose-500" />;
        return <HelpCircle className="w-5 h-5 text-amber-500" />;
    };

    return (
        <motion.div
            id={`card-claim-${claim.claim_id}`}
            ref={cardRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`mb-4 rounded-lg bg-audit-card border border-slate-700 overflow-hidden ${getVerdictColor(verdict)} ${isSelected ? 'ring-2 ring-blue-500 shadow-lg shadow-blue-500/20' : ''}`}
        >
            <div className="p-4 cursor-pointer hover:bg-white/5 transition-colors" onClick={() => setExpanded(!expanded)}>
                <div className="flex justify-between items-start">
                    <div className="flex-1 pr-4">
                        <div className="flex items-center gap-2 mb-2">
                            <StatusIcon />
                            <span className="font-mono font-bold text-sm tracking-wide">{verdict}</span>
                            <span className="text-xs opacity-60 font-mono">CONF: {confidence.toFixed(2)}</span>
                        </div>
                        <p className="text-lg font-serif leading-relaxed text-slate-100">"{claim_text}"</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={(e) => { e.stopPropagation(); onLocate(claim); }}
                            className="p-2 hover:bg-white/10 rounded-full text-slate-400 hover:text-white transition-colors"
                            title="Locate in Text"
                        >
                            <Search className="w-4 h-4" />
                        </button>
                        {expanded ? <ChevronUp className="w-5 h-5 opacity-50" /> : <ChevronDown className="w-5 h-5 opacity-50" />}
                    </div>
                </div>

                {hallucinations && hallucinations.length > 0 && (
                    <div className="mt-3">
                        {hallucinations.map((h, i) => (
                            <HallucinationBadge key={i} type={h.hallucination_type} severity={h.severity} />
                        ))}
                    </div>
                )}
            </div>

            {expanded && (
                <div className="p-4 border-t border-slate-700 bg-slate-900/50 text-sm">
                    {/* Entities */}
                    <div className="mb-4">
                        <h4 className="font-mono text-xs uppercase opacity-50 mb-2">Entities Presumed</h4>
                        <div className="flex gap-2 flex-wrap">
                            {subject_entity && <EntityBadge entity={subject_entity} role="SUBJ" />}
                            {object_entity && <EntityBadge entity={object_entity} role="OBJ" />}
                        </div>
                    </div>

                    {/* Hallucination Details */}
                    {hallucinations && hallucinations.length > 0 && (
                        <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded">
                            <h4 className="font-mono text-xs uppercase text-rose-400 mb-2 flex items-center gap-2">
                                <AlertTriangle className="w-3 h-3" /> Hallucination Analysis
                            </h4>
                            {hallucinations.map((h, i) => (
                                <div key={i} className="mb-2 last:mb-0">
                                    <div className="flex items-baseline gap-2">
                                        <span className="font-bold text-rose-300">{h.hallucination_type}</span>
                                        <span className="text-slate-300">{h.reason}</span>
                                    </div>
                                    <p className="text-xs text-slate-400 mt-1 pl-6">{h.explanation}</p>
                                    <div className="pl-6 mt-1 flex gap-2 font-mono text-[10px] opacity-60">
                                        {h.supporting_signals.map((sig, idx) => <span key={idx}>{sig}</span>)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Evidence */}
                    <div>
                        <h4 className="font-mono text-xs uppercase opacity-50 mb-2">Evidence Alignment</h4>

                        {/* Wikidata */}
                        {evidence?.wikidata?.length > 0 ? (
                            <div className="mb-2">
                                <h5 className="text-xs font-bold text-emerald-400 mb-1">Wikidata</h5>
                                {evidence.wikidata.map((ev, i) => (
                                    <div key={i} className="pl-2 border-l-2 border-emerald-500/30 mb-1">
                                        <div className="font-mono text-xs">{ev.property} → {ev.value}</div>
                                        <div className="text-[10px] opacity-50">Match: {JSON.stringify(ev.alignment)}</div>
                                    </div>
                                ))}
                            </div>
                        ) : <div className="text-xs opacity-40 mb-2">No Wikidata evidence found.</div>}

                        {/* Wikipedia */}
                        {evidence?.wikipedia?.length > 0 ? (
                            <div className="mb-2">
                                <h5 className="text-xs font-bold text-blue-400 mb-1">Wikipedia</h5>
                                {evidence.wikipedia.map((ev, i) => (
                                    <div key={i} className="pl-2 border-l-2 border-blue-500/30 mb-1">
                                        <div className="italic text-xs">"{ev.sentence}"</div>
                                    </div>
                                ))}
                            </div>
                        ) : null}
                    </div>
                </div>
            )}
        </motion.div>
    );
};

const EntityBadge = ({ entity, role }) => (
    <div className="px-2 py-1 bg-slate-800 rounded border border-slate-700 text-xs flex items-center gap-2">
        <span className="font-mono font-bold opacity-50">{role}</span>
        <span>{entity.text || entity.canonical_name}</span>
        {entity.resolution_status === 'RESOLVED' && <CheckCircle className="w-3 h-3 text-emerald-500" />}
    </div>
);

export default ClaimCard;
