"use client"
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, ShieldCheck, Search, Scale, AlertTriangle, FileText, Landmark, Globe, FileSearch, XCircle, AlertOctagon } from 'lucide-react'
import Link from 'next/link'

// --- Hooks ---

/**
 * useGuidedCursor
 * 
 * Encapsulates the epistemic cursor positioning logic.
 * re-anchors on font load, resize, and state changes.
 */
function useGuidedCursor(
    containerRef: React.RefObject<HTMLDivElement | null>,
    claimRefs: React.MutableRefObject<{ [key: string]: HTMLSpanElement | null }>,
    targetId: string | undefined, // The current claim we should be looking at
    demoState: string,
    viewMode: 'GUIDED' | 'EXPERT'
) {
    const [cursorPos, setCursorPos] = useState({ x: -40, y: 300 })

    const updateCursor = useCallback(() => {
        if (!containerRef.current || viewMode === 'EXPERT') return

        const containerRect = containerRef.current.getBoundingClientRect()
        let targetX = -40
        let targetY = containerRect.height / 2

        // Logic: specific states anchor to text, others anchor to neutral layout positions
        if (['MOVE_TO_CLAIM', 'DWELL_ON_CLAIM', 'EXPLAIN', 'READING'].includes(demoState) && targetId) {
            const targetEl = claimRefs.current[targetId]
            if (targetEl) {
                const rect = targetEl.getBoundingClientRect()
                // Relativize to container
                targetX = (rect.left - containerRect.left) + (rect.width / 2)
                targetY = (rect.top - containerRect.top) + (rect.height / 2)
            } else {
                if (process.env.NODE_ENV === 'development') {
                    console.warn(`[EpistemicAudit] Cursor target missing: ${targetId}`)
                }
            }
        }

        setCursorPos({ x: targetX, y: targetY })
    }, [containerRef, claimRefs, targetId, demoState, viewMode])

    // Event Listeners for Stability
    useEffect(() => {
        updateCursor()

        const handleResize = () => updateCursor()
        // Broad font loading listener necessary for layout shift correctness
        const handleFonts = () => updateCursor()

        window.addEventListener('resize', handleResize)
        // @ts-ignore - document.fonts is valid in modern browsers
        if (document.fonts) {
            // @ts-ignore
            document.fonts.ready.then(handleFonts)
            // @ts-ignore
            document.fonts.addEventListener('loadingdone', handleFonts)
        }

        return () => {
            window.removeEventListener('resize', handleResize)
            // @ts-ignore
            if (document.fonts) {
                // @ts-ignore
                document.fonts.removeEventListener('loadingdone', handleFonts)
            }
        }
    }, [updateCursor])

    return cursorPos
}

// --- Components ---

// Section 1: Hero
const HeroSection = () => (
    <section className="min-h-screen flex flex-col items-center justify-center text-center px-4 relative overflow-hidden bg-white">
        <motion.div
            {...({
                animate: { opacity: [0.3, 0.5, 0.3] },
                transition: { duration: 8, repeat: Infinity, ease: "easeInOut" },
                className: "absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(241,245,249,1),rgba(255,255,255,0))] -z-10 pointer-events-none"
            } as any)}
        />

        <div className="max-w-5xl mx-auto">
            <motion.div
                {...({
                    initial: { opacity: 0, y: 12 },
                    animate: { opacity: 1, y: 0 },
                    transition: { duration: 0.6, ease: "easeOut" },
                    className: "inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 text-slate-600 text-[11px] font-semibold tracking-wider uppercase mb-8 border border-slate-200"
                } as any)}
            >
                <ShieldCheck className="w-3.5 h-3.5" />
                Research Preview • Epistemic Analysis
            </motion.div>

            <motion.h1
                {...({
                    initial: { opacity: 0, y: 12 },
                    animate: { opacity: 1, y: 0 },
                    transition: { duration: 0.6, delay: 0.1, ease: "easeOut" },
                    className: "text-5xl md:text-7xl font-bold text-slate-900 tracking-tight mb-8 leading-[1.1]"
                } as any)}
            >
                Audit the epistemic integrity <br />
                of AI-generated text.
            </motion.h1>

            <motion.p
                {...({
                    initial: { opacity: 0, y: 12 },
                    animate: { opacity: 1, y: 0 },
                    transition: { duration: 0.6, delay: 0.18, ease: "easeOut" },
                    className: "text-xl md:text-2xl text-slate-500 max-w-3xl mx-auto mb-12 leading-relaxed font-light"
                } as any)}
            >
                Not fact-checking. Not binary verification. <br className="hidden md:block" />
                A risk-aware analysis of confidence versus evidence.
            </motion.p>

            {/* v1.7 Hero Navigation: Dual Entry */}
            <motion.div
                {...({
                    initial: { opacity: 0, y: 12 },
                    animate: { opacity: 1, y: 0 },
                    transition: { duration: 0.6, delay: 0.26, ease: "easeOut" },
                    className: "flex flex-col md:flex-row items-center justify-center gap-4"
                } as any)}
            >
                <Link href="/audit">
                    <motion.button
                        whileHover="hover"
                        whileTap="tap"
                        variants={{
                            hover: { y: -2 },
                            tap: { scale: 0.98 }
                        }}
                        className="group relative inline-flex items-center gap-2.5 px-8 py-4 bg-slate-900 text-white rounded-full font-medium tracking-wide text-sm shadow-md transition-shadow hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
                        aria-label="Run an epistemic audit"
                        {...({} as any)}
                    >
                        <span>Run an Epistemic Audit</span>
                        <motion.span
                            variants={{
                                hover: { x: 3 },
                                tap: { x: 0 }
                            }}
                            transition={{ duration: 0.2, ease: "easeOut" }}
                        >
                            <ArrowRight className="w-4 h-4" />
                        </motion.span>
                    </motion.button>
                </Link>

                <Link href="/how-it-works">
                    <motion.button
                        whileHover="hover"
                        whileTap="tap"
                        variants={{
                            hover: { backgroundColor: "rgba(248, 250, 252, 0.8)" },
                            tap: { scale: 0.98 }
                        }}
                        className="group relative inline-flex items-center px-8 py-4 bg-transparent border border-slate-200 text-slate-600 rounded-full font-medium tracking-wide text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
                        aria-label="View methodology"
                        {...({} as any)}
                    >
                        <span>View Methodology</span>
                    </motion.button>
                </Link>
            </motion.div>
        </div>
    </section>
)

// Section 2: Capabilities
const CapabilitiesSection = () => {
    const cards = [
        {
            title: "Atomic Claims",
            desc: "Breaks text into falsifiable units, separating factual assertions from rhetoric.",
            glyph: <Search className="w-5 h-5 text-slate-400" />
        },
        {
            title: "Structured Evidence",
            desc: "Evaluates claims against knowledge graphs and authoritative records — not model consensus.",
            glyph: <Globe className="w-5 h-5 text-slate-400" />
        },
        {
            title: "Epistemic Risk",
            desc: "Penalizes unsupported confidence. Rewards calibrated uncertainty.",
            glyph: <AlertTriangle className="w-5 h-5 text-slate-400" />
        }
    ]

    return (
        <section className="py-32 px-4 bg-slate-50/50">
            <div className="max-w-6xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {cards.map((card, idx) => (
                        <motion.div
                            key={card.title}
                            {...({
                                initial: { opacity: 0, scale: 0.98, y: 20 },
                                whileInView: { opacity: 1, scale: 1, y: 0 },
                                transition: { duration: 0.5, delay: idx * 0.1, ease: "easeOut" },
                                className: "p-8 rounded-2xl bg-white border border-slate-200/60 shadow-sm hover:border-slate-400 transition-colors group"
                            } as any)}
                        >
                            <div className="mb-6 p-3 w-fit rounded-lg bg-slate-50 group-hover:bg-slate-100 transition-colors">
                                {card.glyph}
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-black transition-colors">{card.title}</h3>
                            <p className="text-slate-500 leading-relaxed font-light">{card.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    )
}

// Section 3: Positioning
const PositioningSection = () => (
    <section className="py-32 px-4 bg-white border-y border-slate-100">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div>
                <motion.h2
                    {...({
                        initial: { opacity: 0, x: -20 },
                        whileInView: { opacity: 1, x: 0 },
                        className: "text-4xl font-bold text-slate-900 mb-8 leading-tight"
                    } as any)}
                >
                    Why hallucinations <br />aren’t binary
                </motion.h2>
                <motion.div
                    {...({
                        initial: { opacity: 0, y: 10 },
                        whileInView: { opacity: 1, y: 0 },
                        transition: { delay: 0.2 },
                        className: "space-y-6"
                    } as any)}
                >
                    <p className="text-lg text-slate-600 font-light leading-relaxed">
                        Modern AI failures are rarely outright falsehoods.
                        They are overconfident claims weakly grounded in evidence.
                    </p>
                    <p className="text-lg text-slate-600 font-light leading-relaxed">
                        This system is designed to surface that risk — explicitly.
                        By decomposing text into discrete nodes of inquiry, we move past "True/False" toward "Calibrated/Uncalibrated."
                    </p>
                </motion.div>
            </div>

            <div className="relative p-12 rounded-3xl bg-slate-900 overflow-hidden min-h-[400px] flex flex-col justify-center">
                <div className="relative z-10 flex flex-col gap-6">
                    {['Text', 'Claims', 'Evidence', 'Risk Score'].map((item, idx) => (
                        <div key={item} className="flex items-center gap-4">
                            <motion.div
                                {...({
                                    initial: { width: 0, opacity: 0 },
                                    whileInView: { width: '100%', opacity: 1 },
                                    transition: { duration: 1.2, delay: idx * 0.3, ease: "easeInOut" },
                                    className: "h-0.5 bg-slate-700 relative"
                                } as any)}
                            >
                                {idx < 3 && (
                                    <motion.div
                                        {...({
                                            initial: { opacity: 0 },
                                            whileInView: { opacity: 1 },
                                            transition: { delay: (idx + 1) * 0.3 },
                                            className: "absolute -right-1 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-slate-500 shadow-[0_0_10px_rgba(255,255,255,0.2)]"
                                        } as any)}
                                    />
                                )}
                            </motion.div>
                            <span className="text-xs font-mono text-slate-400 uppercase tracking-widest whitespace-nowrap min-w-[100px]">{item}</span>
                        </div>
                    ))}
                </div>
                <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_50%_50%,rgba(51,65,85,0.5),transparent)]" />
            </div>
        </div>
    </section>
)

// Section 4: Showcase (Guided/Expert)
type DemoState = 'ENTRY' | 'INTENT_PAUSE' | 'MOVE_TO_CLAIM' | 'DWELL_ON_CLAIM' | 'EXPLAIN' | 'READING' | 'EXIT_RITUAL' | 'INSPECT_FREELY'
type ViewMode = 'GUIDED' | 'EXPERT'

const ShowcaseSection = () => {
    const [activeStep, setActiveStep] = useState(0)
    const [demoState, setDemoState] = useState<DemoState>('ENTRY')
    const [viewMode, setViewMode] = useState<ViewMode>('GUIDED')

    // Refs
    const containerRef = useRef<HTMLDivElement>(null)
    const claimRefs = useRef<{ [key: string]: HTMLSpanElement | null }>({})

    // Stages Configuration
    const stages = [
        {
            targetId: 'CLAIM_REVENUE',
            stepLabel: "Claim Isolation",
            header: "Atomic Unit Identified",
            body: "The system isolates this specific assertion as a falsifiable unit, stripping away rhetorical fluff.",
            microNote: "This enforces granular analysis over holistic reading.",
            footer: "Next: Querying trusted knowledge graphs.",
            risk: 15,
            color: "emerald",
            tag: "[QUANTITATIVE]",
            provenance: { type: "N/A", source: "Internal Logic", date: "Now" }
        },
        {
            targetId: 'CLAIM_ENTITY',
            stepLabel: "Evidence Matching",
            header: "Source Verification",
            body: "Comparing the claim against SEC EDGAR filings to verify the reported revenue figures.",
            microNote: "No reliance on large language model consensus.",
            footer: "Status: Strong evidence alignment found.",
            risk: 95,
            color: "emerald",
            tag: "[ATTRIBUTIONAL]",
            provenance: { type: "Structured", source: "SEC 10-K", date: "2024-Q4" }
        }
    ]
    const current = stages[activeStep]

    // Cursor Logic Hook
    const cursorPos = useGuidedCursor(
        containerRef,
        claimRefs,
        current.targetId,
        demoState,
        viewMode
    )

    // Finite State Machine (Deterministic Loop)
    useEffect(() => {
        if (viewMode === 'EXPERT' || demoState === 'INSPECT_FREELY') return

        let timer: NodeJS.Timeout

        // State Transition Logic
        const transition = () => {
            switch (demoState) {
                case 'ENTRY':
                    timer = setTimeout(() => setDemoState('INTENT_PAUSE'), 1000)
                    break
                case 'INTENT_PAUSE':
                    timer = setTimeout(() => setDemoState('MOVE_TO_CLAIM'), 300)
                    break
                case 'MOVE_TO_CLAIM':
                    timer = setTimeout(() => setDemoState('DWELL_ON_CLAIM'), 1200)
                    break
                case 'DWELL_ON_CLAIM':
                    timer = setTimeout(() => setDemoState('EXPLAIN'), 800)
                    break
                case 'EXPLAIN':
                    timer = setTimeout(() => setDemoState('READING'), 600)
                    break
                case 'READING':
                    timer = setTimeout(() => setDemoState('EXIT_RITUAL'), 4500)
                    break
                case 'EXIT_RITUAL':
                    timer = setTimeout(() => {
                        // Unconditional Loop
                        setActiveStep(prev => (prev + 1) % stages.length)
                        setDemoState('ENTRY')
                    }, 600) // 600ms pause before restart
                    break
            }
        }
        transition()
        return () => clearTimeout(timer)
    }, [demoState, viewMode])

    const isCardVisible = (demoState === 'EXPLAIN' || demoState === 'READING') && viewMode === 'GUIDED'
    const isHighlightActive = (['DWELL_ON_CLAIM', 'EXPLAIN', 'READING'].includes(demoState)) || viewMode === 'EXPERT'

    // Dynamic Card Positioning
    const [cardPos, setCardPos] = useState({ x: 0, y: 0 })

    useEffect(() => {
        const updateCardPos = () => {
            if (!containerRef.current || !current.targetId) return
            const targetEl = claimRefs.current[current.targetId]
            if (targetEl) {
                const cRect = containerRef.current.getBoundingClientRect()
                const tRect = targetEl.getBoundingClientRect()

                // Center X alignment
                const targetX = (tRect.left - cRect.left) + (tRect.width / 2)
                // Anchor Y: Just above the text line (approx 15px gap)
                // We use bottom-anchoring in CSS (translate-y-[-100%]) so y should be claim top.
                const targetY = (tRect.top - cRect.top) - 24

                setCardPos({ x: targetX, y: targetY })
            }
        }

        // Update on step/state change + resize
        updateCardPos()
        window.addEventListener('resize', updateCardPos)
        return () => window.removeEventListener('resize', updateCardPos)
    }, [activeStep, demoState, current.targetId])

    return (
        <section className="py-32 px-4 bg-slate-50">
            <div className="max-w-6xl mx-auto text-center mb-16 px-4">
                <div
                    className="inline-flex items-center gap-3 p-1.5 bg-slate-200/50 rounded-full mb-8 cursor-pointer select-none transition-colors hover:bg-slate-200"
                    onClick={() => {
                        setViewMode(prev => prev === 'GUIDED' ? 'EXPERT' : 'GUIDED')
                        if (viewMode === 'GUIDED') setDemoState('ENTRY') // Restart loop on toggle back
                    }}
                >
                    <span className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === 'GUIDED' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-400'}`}>Guided</span>
                    <span className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === 'EXPERT' ? 'bg-white shadow-sm text-slate-800' : 'text-slate-400'}`}>Expert</span>
                </div>

                <h2 className="text-3xl font-bold text-slate-900 mb-4">How the System Audits Claims</h2>
                <p className="text-slate-500 font-light max-w-2xl mx-auto leading-relaxed">
                    {viewMode === 'GUIDED' ? 'A slower, guided preview of the epistemic analysis process.' : 'Full inspection mode. Hover to analyze discrete claims directly.'}
                    <br className="hidden sm:block" />
                    Observe how discrete claims are isolated, cross-referenced, and scored for risk.
                </p>
            </div>

            <div className="max-w-4xl mx-auto relative group">
                <AnimatePresence>
                    {viewMode === 'GUIDED' && demoState !== 'INSPECT_FREELY' && (
                        <motion.div
                            key="cursor"
                            initial={false}
                            animate={{
                                x: cursorPos.x,
                                y: cursorPos.y,
                                scale: demoState === 'DWELL_ON_CLAIM' ? 0.9 : 1,
                                opacity: demoState === 'EXIT_RITUAL' ? 0 : 1
                            }}
                            transition={{
                                duration: demoState === 'MOVE_TO_CLAIM' ? 1.2 : 0.6,
                                ease: [0.25, 1, 0.5, 1],
                                type: "tween"
                            }}
                            className="absolute w-6 h-6 rounded-full border-2 border-slate-900/20 bg-slate-900/10 pointer-events-none z-50 flex items-center justify-center shadow-lg backdrop-blur-sm -translate-x-1/2 -translate-y-1/2"
                            style={{ top: 0, left: 0 }}
                            {...({} as any)}
                        >
                            <div className="w-1.5 h-1.5 bg-slate-900 rounded-full" />
                        </motion.div>
                    )}
                </AnimatePresence>

                <motion.div
                    ref={containerRef}
                    {...({
                        initial: { opacity: 0, y: 30 },
                        whileInView: { opacity: 1, y: 0 },
                        className: "bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-2xl relative min-h-[500px] flex flex-col"
                    } as any)}
                >
                    {/* Completion Message Removed */}

                    <AnimatePresence>
                        {isCardVisible && (
                            <motion.div
                                key="overlay-card"
                                initial={{ opacity: 0, scale: 0.95, y: cardPos.y + 10, x: cardPos.x, xPercent: -50, yPercent: -100 }}
                                animate={{
                                    opacity: 1,
                                    scale: 1,
                                    y: cardPos.y,
                                    x: cardPos.x,
                                    xPercent: -50,
                                    yPercent: -100
                                }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{
                                    type: "spring",
                                    stiffness: 300,
                                    damping: 30,
                                    opacity: { duration: 0.2 }
                                }}
                                className="absolute w-[340px] z-40 origin-bottom"
                                style={{ top: 0, left: 0 }}
                                {...({} as any)}
                            >
                                <div className={`p-6 rounded-2xl bg-white/95 backdrop-blur-xl border shadow-[0_20px_50px_rgba(0,0,0,0.1)] relative overflow-hidden transition-all duration-500 ${isHighlightActive ? `border-${current.color}-200 shadow-${current.color}-500/10` : 'border-slate-200/50'}`}>
                                    <div role="note" className="space-y-4 relative z-10">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2.5">
                                                <div className={`w-2 h-2 rounded-full bg-${current.color}-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]`} />
                                                <span className="text-[10px] font-black text-slate-800 uppercase tracking-[0.15em]">{current.header}</span>
                                            </div>
                                            <span className="text-[9px] font-mono text-slate-400 uppercase tracking-widest">Step {activeStep + 1} of {stages.length}</span>
                                        </div>
                                        <p className="text-[13px] text-slate-600 leading-relaxed font-medium">{current.body}</p>
                                        <motion.p
                                            key={`${activeStep}-note`}
                                            {...({
                                                initial: { opacity: 0 },
                                                animate: { opacity: 1 },
                                                transition: { delay: 1.5, duration: 1 },
                                                className: "text-[11px] text-slate-400 italic font-light"
                                            } as any)}
                                        >
                                            {current.microNote}
                                        </motion.p>
                                        <div className="pt-2 border-t border-slate-100 italic text-[11px] text-slate-400">
                                            {current.footer}
                                        </div>
                                        <div className="space-y-2 pt-1">
                                            <div className="flex justify-between text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                                                <span>Alignment Strength</span>
                                                <span className={`text-${current.color}-600`}>Strong</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden relative">
                                                <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 via-yellow-500/20 to-emerald-500/20" />
                                                <motion.div
                                                    {...({
                                                        initial: { width: 0 },
                                                        animate: { width: `${current.risk}%` },
                                                        transition: { duration: 0.8, delay: 0.2 },
                                                        className: `h-full bg-gradient-to-r from-slate-200 to-${current.color}-500 relative z-10 opacity-80`
                                                    } as any)}
                                                />
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100/50 mt-1">
                                            {Object.entries(current.provenance).map(([key, val]) => (
                                                <div key={key} className="flex flex-col">
                                                    <span className="text-[8px] text-slate-300 uppercase tracking-wider">{key}</span>
                                                    <span className="text-[9px] text-slate-500 font-mono">{val}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <div className="p-16 pt-32 flex-grow">
                        <div className="relative text-slate-700 font-light leading-relaxed max-w-2xl text-xl mx-auto space-y-8">
                            <div className="leading-relaxed select-none">
                                <motion.span
                                    ref={(el: HTMLSpanElement | null) => { claimRefs.current['CLAIM_ENTITY'] = el }}
                                    data-claim-id="CLAIM_ENTITY"
                                    {...({
                                        animate: {
                                            opacity: (isHighlightActive && activeStep === 1) ? 1 : 0.4,
                                            backgroundColor: (isHighlightActive && activeStep === 1) ? 'rgba(241, 245, 249, 1)' : 'transparent'
                                        },
                                        className: "px-1 rounded transition-colors duration-500 relative group/claim"
                                    } as any)}
                                >
                                    Alphabet Inc. reported
                                    {viewMode === 'EXPERT' && (
                                        <span className="absolute -top-4 left-0 text-[9px] font-mono text-slate-400 bg-slate-100 px-1 rounded border border-slate-200 opacity-0 group-hover/claim:opacity-100 transition-opacity uppercase tracking-wider whitespace-nowrap z-20">
                                            [SUBJECT: ENTITY]
                                        </span>
                                    )}
                                </motion.span> that its quarterly {' '}
                                <motion.span
                                    ref={(el: HTMLSpanElement | null) => { claimRefs.current['CLAIM_REVENUE'] = el }}
                                    data-claim-id="CLAIM_REVENUE"
                                    {...({
                                        animate: {
                                            backgroundColor: (isHighlightActive && activeStep === 0) ? 'rgba(209, 250, 229, 0.3)' : 'transparent',
                                            color: (isHighlightActive && activeStep === 0) ? '#065f46' : 'inherit'
                                        },
                                        className: "px-2 py-0.5 rounded-sm font-normal relative inline-block transition-all duration-500 group/claim"
                                    } as any)}
                                >
                                    revenue exceeded $20B in Q4
                                    {(isHighlightActive && activeStep === 0) && (
                                        <motion.span
                                            {...({
                                                layoutId: "shimmer",
                                                className: "absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent w-full skew-x-12",
                                                animate: { x: ['-100%', '200%'] },
                                                transition: { duration: 1.5, repeat: Infinity, ease: "linear" }
                                            } as any)}
                                        />
                                    )}
                                    {viewMode === 'EXPERT' && (
                                        <div className="absolute -top-4 left-0 flex gap-1 opacity-0 group-hover/claim:opacity-100 transition-opacity z-20">
                                            <span className="text-[9px] font-mono text-slate-400 bg-slate-100 px-1 rounded border border-slate-200 uppercase tracking-wider whitespace-nowrap">
                                                [PREDICATE: \u003E]
                                            </span>
                                            <span className="text-[9px] font-mono text-slate-400 bg-slate-100 px-1 rounded border border-slate-200 uppercase tracking-wider whitespace-nowrap">
                                                [QUANTIFIER: $20B]
                                            </span>
                                        </div>
                                    )}
                                </motion.span>
                                , marking a continuation of its fiscal growth trajectory in the advertising sector.
                            </div>
                        </div>
                    </div>

                    <div className="p-8 bg-slate-50/50 border-t border-slate-100 flex flex-col items-center gap-6">
                        <div className="relative flex items-center justify-center gap-12 w-full max-w-md">
                            {[0, 1, 2, 3, 4].map((i) => {
                                const isFocused = (activeStep === 0 && i === 3) || (activeStep === 1 && i === 0)
                                const isTimeActive = (isFocused && isHighlightActive) || viewMode === 'EXPERT'
                                return (
                                    <div key={i} className="relative flex flex-col items-center">
                                        <motion.div
                                            {...({
                                                animate: {
                                                    scale: isTimeActive && isFocused ? 1.5 : 1,
                                                    opacity: isTimeActive ? 1 : 0.4,
                                                    backgroundColor: isTimeActive && isFocused ? '#10b981' : '#cbd5e1'
                                                },
                                                transition: { duration: 0.4 },
                                                className: `w-2.5 h-2.5 rounded-full z-10 relative ${isTimeActive && isFocused ? 'ring-4 ring-emerald-100' : ''}`
                                            } as any)}
                                        />
                                    </div>
                                )
                            })}
                            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-200 -z-0 translate-y-[-1px]" />
                        </div>
                    </div>
                </motion.div>
            </div>
        </section>
    )
}

// Section 5: Serious Use
const SeriousUseSection = () => {
    const rows = [
        { label: "Research & Audit", icon: <FileSearch className="w-4 h-4" /> },
        { label: "Policy & Governance", icon: <Landmark className="w-4 h-4" /> },
        { label: "Journalism & Analysis", icon: <FileText className="w-4 h-4" /> },
        { label: "Model Evaluation", icon: <Scale className="w-4 h-4" /> }
    ]

    return (
        <section className="py-32 px-4 bg-white">
            <div className="max-w-4xl mx-auto">
                <h2 className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em] text-center mb-16">Designed for Strict Contexts</h2>
                <div className="space-y-4">
                    {rows.map((row, idx) => (
                        <motion.div
                            key={row.label}
                            {...({
                                initial: { opacity: 0, x: idx % 2 === 0 ? -12 : 12 },
                                whileInView: { opacity: 1, x: 0 },
                                className: "group flex items-center justify-between p-6 rounded-xl border border-slate-100 bg-slate-50/30 hover:bg-slate-50 transition-colors"
                            } as any)}
                        >
                            <div className="flex items-center gap-4">
                                <motion.div
                                    {...({
                                        initial: { rotate: 3 },
                                        whileInView: { rotate: 0 },
                                        className: "p-2 bg-white rounded-lg border border-slate-200 shadow-sm text-slate-500 group-hover:text-slate-900 transition-colors"
                                    } as any)}
                                >
                                    {row.icon}
                                </motion.div>
                                <span className="font-semibold text-slate-800">{row.label}</span>
                            </div>
                            <span className="text-sm text-slate-400 font-light italic">Built for traceability, not persuasion.</span>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    )
}

// Section: Failure Modes
const FailureModeSection = () => (
    <section className="py-24 px-4 bg-white border-t border-slate-100">
        <div className="max-w-3xl mx-auto text-left">
            <div className="flex items-center gap-3 mb-8 text-slate-500">
                <AlertOctagon className="w-5 h-5 opacity-50" />
                <h3 className="text-sm font-bold uppercase tracking-widest">Where This System Can Fail</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
                <div className="space-y-2">
                    <h4 className="text-xs font-mono font-semibold text-slate-900">1. Outdated Structured Data</h4>
                    <p className="text-sm text-slate-500 leading-relaxed font-light">
                        If knowledge references (e.g. SEC filings) are stale, the engine may flag recent valid claims as unsupported.
                    </p>
                </div>
                <div className="space-y-2">
                    <h4 className="text-xs font-mono font-semibold text-slate-900">2. Ambiguous Predicates</h4>
                    <p className="text-sm text-slate-500 leading-relaxed font-light">
                        Language with high semantic drift (e.g. "revolutionary") cannot be rigorously falsified.
                    </p>
                </div>
                <div className="space-y-2">
                    <h4 className="text-xs font-mono font-semibold text-slate-900">3. Registry Gaps</h4>
                    <p className="text-sm text-slate-500 leading-relaxed font-light">
                        Claims referencing private datasets or non-public events are invisible to the verification layer.
                    </p>
                </div>
                <div className="space-y-2">
                    <h4 className="text-xs font-mono font-semibold text-slate-900">4. Over-Compression</h4>
                    <p className="text-sm text-slate-500 leading-relaxed font-light">
                        Complex multi-part claims may be atomicized incorrectly, losing context.
                    </p>
                </div>
            </div>
        </div>
    </section>
)

// Section: Epistemic Refusal (Humility)
const RefusalSection = () => (
    <section className="py-24 px-4 bg-slate-50 border-t border-slate-100">
        <div className="max-w-3xl mx-auto text-center">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-12">System Constraints & Refusals</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
                {[
                    "Does NOT infer intent from text.",
                    "Does NOT deference to model consensus.",
                    "Does NOT collapse epistemic uncertainty.",
                    "Does NOT validate non-falsifiable rhetoric."
                ].map((item, i) => (
                    <div key={i} className="flex items-start gap-4 p-4 rounded-lg bg-white border border-slate-100 shadow-sm">
                        <XCircle className="w-5 h-5 text-slate-300 mt-0.5 shrink-0" />
                        <span className="text-sm text-slate-600 font-medium">{item}</span>
                    </div>
                ))}
            </div>
        </div>
    </section>
)

// Section 6: Boundaries (Final Section)
const BoundariesSection = () => (
    <section className="py-40 px-4 bg-slate-950 text-slate-300">
        <motion.div
            {...({
                initial: { opacity: 0 },
                whileInView: { opacity: 1 },
                className: "max-w-3xl mx-auto text-center space-y-12"
            } as any)}
        >
            <div>
                <h2 className="text-4xl font-light leading-tight tracking-tight mb-6">
                    This is not a truth oracle. <br />
                    It does not declare facts “true” or “false.”
                </h2>
                <p className="text-xl text-slate-500 font-light leading-relaxed">
                    It exposes epistemic gaps — where confidence exceeds evidence. <br />
                    A tool for human experts to audit the recursive overconfidence of large language models.
                </p>
            </div>

            {/* System Status Footer */}
            <div className="pt-20 flex flex-col items-center gap-2 border-t border-slate-900/50">
                <div className="inline-flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50"></div>
                    <div className="text-[10px] font-mono text-slate-600 uppercase tracking-widest">System Status: Active</div>
                </div>
                <div className="text-xs text-slate-700 font-light">
                    Epistemic Audit Engine v1.5.1 (Research Artifact)
                </div>
            </div>
        </motion.div>
    </section>
)

export default function LandingPage() {
    return (
        <div className="bg-white selection:bg-slate-900 selection:text-white overflow-x-hidden">
            <HeroSection />
            <CapabilitiesSection />
            <PositioningSection />
            <ShowcaseSection />
            <SeriousUseSection />
            <FailureModeSection />
            <RefusalSection />
            <BoundariesSection />
        </div>
    )
}
