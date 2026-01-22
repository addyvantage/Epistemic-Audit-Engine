import React from 'react';

const HallucinationBadge = ({ type, severity }) => {
    // H1-H6 mapping descriptions?
    const labels = {
        H1: "Unsupported",
        H2: "False Specificity",
        H3: "Overconfidence",
        H4: "Illegitimate Inference",
        H5: "Inconsistency",
        H6: "Narrative Laundering"
    };

    const color = severity === 'HIGH' ? 'bg-rose-500/20 text-rose-300 border-rose-500/50' : 'bg-amber-500/20 text-amber-300 border-amber-500/50';

    return (
        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-mono border ${color} mr-2 mb-2`}>
            <span className="font-bold mr-1">{type}</span>
            {labels[type] || type}
        </span>
    );
};

export default HallucinationBadge;
