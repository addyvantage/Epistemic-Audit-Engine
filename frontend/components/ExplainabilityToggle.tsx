"use client"
import React from 'react'

interface ExplainabilityToggleProps {
    mode: 'CASUAL' | 'EXPERT'
    onChange: (mode: 'CASUAL' | 'EXPERT') => void
}

export function ExplainabilityToggle({ mode, onChange }: ExplainabilityToggleProps) {
    return (
        <div className="
            flex items-center 
            bg-white/70 dark:bg-neutral-900/60 
            rounded-lg p-1 w-fit 
            border border-slate-200 dark:border-white/10
            backdrop-blur-sm
        ">
            <button
                onClick={() => onChange('CASUAL')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${mode === 'CASUAL'
                    ? 'bg-white dark:bg-white/10 text-slate-900 dark:text-neutral-100 shadow-sm'
                    : 'text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-neutral-300'
                    }`}
            >
                Casual
            </button>
            <button
                onClick={() => onChange('EXPERT')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${mode === 'EXPERT'
                    ? 'bg-slate-800 dark:bg-white/10 text-white dark:text-neutral-100 shadow-sm'
                    : 'text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-neutral-300'
                    }`}
            >
                Expert
            </button>
        </div>
    )
}
