import React from 'react';
import { motion } from 'framer-motion';

const RiskSummary = ({ risk, score, summary }) => {
    const getColor = (r) => {
        if (r === 'LOW') return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
        if (r === 'MEDIUM') return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
        return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-6 rounded-xl border ${getColor(risk)} mb-8 backdrop-blur-sm`}
        >
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-sm font-mono uppercase tracking-wider opacity-70">Overall Risk Level</h2>
                    <div className="text-4xl font-bold mt-1 tracking-tight">{risk}</div>
                </div>
                <div className="text-right">
                    <h2 className="text-sm font-mono uppercase tracking-wider opacity-70">Hallucination Score</h2>
                    <div className="text-4xl font-mono font-bold mt-1">{score}</div>
                </div>
            </div>

            <div className="mt-6 pt-4 border-t border-white/10 grid grid-cols-3 gap-4 text-center">
                <Stat label="Unsupported" value={summary?.unsupported_claims || 0} />
                <Stat label="False Specificity" value={summary?.false_specificity || 0} />
                <Stat label="Overconfidence" value={summary?.overconfident_language || 0} />
            </div>
        </motion.div>
    );
};

const Stat = ({ label, value }) => (
    <div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-xs font-mono opacity-60 uppercase">{label}</div>
    </div>
);

export default RiskSummary;
