import React from 'react'
import { Info } from 'lucide-react'

interface AuditSummaryProps {
    overallRisk: "LOW" | "MEDIUM" | "HIGH"
    hallucinationScore: number
    summary: Record<string, number>
}

export function AuditSummary({ overallRisk, hallucinationScore, summary }: AuditSummaryProps) {
    const riskColors = {
        LOW: "bg-green-100 text-green-800 border-green-200 shadow-green-100",
        MEDIUM: "bg-amber-100 text-amber-800 border-amber-200 shadow-amber-100",
        HIGH: "bg-red-100 text-red-800 border-red-200 shadow-red-100"
    }

    // Calculate percentage of claims verified
    // const totalClaims = Object.values(summary).reduce((a, b) => a + b, 0) || 1
    const totalClaims = summary.Claims || Object.values(summary).reduce((a, b) => a + b, 0) || 1
    const supported = summary.Verified || 0

    return (
        <div className="w-full p-8 rounded-xl border border-slate-100 bg-white shadow-sm grid grid-cols-1 md:grid-cols-3 gap-8 items-center">

            {/* 1. Risk Badge */}
            <div className="flex flex-col justify-center border-r border-slate-100 pr-8">
                <div className="text-xs font-mono uppercase tracking-widest text-slate-400 mb-2 font-semibold">Epistemic Risk</div>
                <div className={`inline-flex items-center justify-center py-3 px-6 rounded-lg text-2xl font-bold tracking-tight border shadow-sm ${riskColors[overallRisk]}`}>
                    {overallRisk}
                </div>
            </div>

            {/* 2. Score with Tooltip */}
            <div className="flex flex-col justify-center border-r border-slate-100 pr-8 relative">
                <div className="text-xs font-mono uppercase tracking-widest text-slate-400 mb-2 font-semibold flex items-center gap-2 group cursor-help relative w-fit">
                    Risk Score
                    <Info className="w-3 h-3 text-slate-300 group-hover:text-slate-500 transition-colors" />

                    {/* Tooltip */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 bg-slate-900 text-slate-200 text-xs rounded-lg shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                        <div className="font-bold text-white mb-2 pb-1 border-b border-slate-700">Score Interpretation</div>
                        <div className="space-y-1 font-mono">
                            <div className="flex justify-between"><span className="text-green-400">0.0-0.2</span> <span>Well-grounded</span></div>
                            <div className="flex justify-between"><span className="text-amber-400">0.3-0.5</span> <span>Mixed</span></div>
                            <div className="flex justify-between"><span className="text-red-400">0.6+</span> <span>High Risk</span></div>
                        </div>
                    </div>
                </div>

                <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-slate-900 tracking-tighter">
                        {hallucinationScore.toFixed(2)}
                    </span>
                    <span className="text-sm text-slate-400 font-medium">/ 1.00</span>
                </div>
                <div className="mt-2 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-slate-900 rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${hallucinationScore * 100}%` }}
                    />
                </div>
            </div>

            {/* 3. Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <div className="text-[10px] uppercase tracking-wide text-slate-400 font-semibold mb-1">Claims</div>
                    <div className="text-xl font-bold text-slate-800">{totalClaims}</div>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <div className="text-[10px] uppercase tracking-wide text-slate-400 font-semibold mb-1">Verified</div>
                    <div className="text-xl font-bold text-green-700">{supported}</div>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <div className="text-[10px] uppercase tracking-wide text-slate-400 font-semibold mb-1">Refuted</div>
                    <div className="text-xl font-bold text-red-700">{summary.Refuted || 0}</div>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <div className="text-[10px] uppercase tracking-wide text-slate-400 font-semibold mb-1">Uncertain</div>
                    <div className="text-xl font-bold text-amber-700">{summary.Uncertain || 0}</div>
                </div>
            </div>

        </div>
    )
}
