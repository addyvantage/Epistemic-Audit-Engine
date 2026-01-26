import React, { useEffect, useState } from 'react'
import { Info } from 'lucide-react'
import { motion } from 'framer-motion'
import { PREMIUM_EASE } from '@/lib/motion-variants'

// --- TypeScript Fix ---
const MotionDiv = motion.div as any


interface AuditSummaryProps {
    overallRisk: "LOW" | "MEDIUM" | "HIGH"
    hallucinationScore: number
    summary: Record<string, number>
}

// Custom hook for count-up animation
function useCountUp(target: number, duration: number = 1500, delay: number = 300) {
    const [value, setValue] = useState(0)

    useEffect(() => {
        const timeout = setTimeout(() => {
            const startTime = Date.now()
            const animate = () => {
                const elapsed = Date.now() - startTime
                const progress = Math.min(elapsed / duration, 1)
                // Ease-out cubic
                const eased = 1 - Math.pow(1 - progress, 3)
                setValue(target * eased)
                if (progress < 1) {
                    requestAnimationFrame(animate)
                }
            }
            animate()
        }, delay)
        return () => clearTimeout(timeout)
    }, [target, duration, delay])

    return value
}

export function AuditSummary({ overallRisk, hallucinationScore, summary }: AuditSummaryProps) {
    const animatedScore = useCountUp(hallucinationScore, 1500, 300)
    const [progressWidth, setProgressWidth] = useState(0)

    useEffect(() => {
        const timeout = setTimeout(() => {
            setProgressWidth(hallucinationScore * 100)
        }, 500)
        return () => clearTimeout(timeout)
    }, [hallucinationScore])

    const riskColors = {
        LOW: "bg-green-100 text-green-800 border-green-200 shadow-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
        MEDIUM: "bg-amber-100 text-amber-800 border-amber-200 shadow-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800",
        HIGH: "bg-red-100 text-red-800 border-red-200 shadow-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800"
    }

    // Calculate percentage of claims verified
    // const totalClaims = Object.values(summary).reduce((a, b) => a + b, 0) || 1
    const totalClaims = summary.Claims || Object.values(summary).reduce((a, b) => a + b, 0) || 1
    const supported = summary.Verified || 0

    return (
        <div className="w-full p-8 rounded-xl border border-slate-100 dark:border-border-subtle bg-white dark:bg-charcoal shadow-sm grid grid-cols-1 md:grid-cols-3 gap-8 items-center transition-colors duration-500">

            {/* 1. Risk Badge */}
            <div className="flex flex-col justify-center border-r border-slate-100 dark:border-border-subtle pr-8">
                <div className="text-xs font-mono uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-2 font-semibold">Epistemic Risk</div>
                <div className={`inline-flex items-center justify-center py-3 px-6 rounded-lg text-2xl font-bold tracking-tight border shadow-sm ${riskColors[overallRisk]}`}>
                    {overallRisk}
                </div>
            </div>

            {/* 2. Score with Tooltip - Enhanced with Count-Up */}
            <div className="flex flex-col justify-center border-r border-slate-100 dark:border-border-subtle pr-8 relative">
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

                <MotionDiv
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, ease: PREMIUM_EASE }}
                    className="flex items-baseline gap-2"
                >
                    <span className="text-4xl font-bold text-slate-900 dark:text-slate-100 tracking-tighter tabular-nums">
                        {animatedScore.toFixed(2)}
                    </span>
                    <span className="text-sm text-slate-400 font-medium">/ 1.00</span>
                </MotionDiv>
                <div className="mt-2 h-2 w-full bg-slate-100 dark:bg-graphite rounded-full overflow-hidden">
                    <MotionDiv
                        initial={{ width: 0 }}
                        animate={{ width: `${progressWidth}%` }}
                        transition={{ duration: 1.2, delay: 0.3, ease: PREMIUM_EASE }}
                        className={`h-full rounded-full ${hallucinationScore < 0.3
                            ? 'bg-emerald-500'
                            : hallucinationScore < 0.6
                                ? 'bg-amber-500'
                                : 'bg-red-500'
                            }`}
                    />
                </div>
            </div>

            {/* 3. Stats Grid - Enhanced with Stagger */}
            <div className="grid grid-cols-2 gap-4">
                {[
                    { label: 'Claims', value: totalClaims, color: 'text-slate-800 dark:text-slate-200' },
                    { label: 'Verified', value: supported, color: 'text-emerald-600 dark:text-emerald-400' },
                    { label: 'Refuted', value: summary.Refuted || 0, color: 'text-red-600 dark:text-red-400' },
                    { label: 'Uncertain', value: summary.Uncertain || 0, color: 'text-amber-600 dark:text-amber-400' },
                ].map((stat, idx) => (
                    <MotionDiv
                        key={stat.label}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: 0.5 + idx * 0.1, ease: PREMIUM_EASE }}
                        className="bg-slate-50 dark:bg-graphite p-3 rounded-lg border border-slate-100 dark:border-border-subtle"
                    >
                        <div className="text-[10px] uppercase tracking-wide text-slate-400 font-semibold mb-1">{stat.label}</div>
                        <div className={`text-xl font-bold tabular-nums ${stat.color}`}>{stat.value}</div>
                    </MotionDiv>
                ))}
            </div>

        </div>
    )
}
