"use client"
import React from 'react'

interface ExplainabilityToggleProps {
    mode: 'CASUAL' | 'EXPERT'
    onChange: (mode: 'CASUAL' | 'EXPERT') => void
}

export function ExplainabilityToggle({ mode, onChange }: ExplainabilityToggleProps) {
    return (
        <div className="flex items-center bg-slate-100 rounded-lg p-1 w-fit shadow-inner border border-slate-200">
            <button
                onClick={() => onChange('CASUAL')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${mode === 'CASUAL'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
            >
                Casual
            </button>
            <button
                onClick={() => onChange('EXPERT')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${mode === 'EXPERT'
                        ? 'bg-slate-800 text-white shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
            >
                Expert
            </button>
        </div>
    )
}
