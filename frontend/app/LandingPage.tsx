"use client"
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion'
import { ArrowRight, ShieldCheck, Search, Scale, AlertTriangle, FileText, Landmark, Globe, FileSearch, XCircle, AlertOctagon, Moon, Sun } from 'lucide-react'
import Link from 'next/link'
import {
    fadeUp,
    staggerContainer,
    staggerItem,
    scaleIn,
    dramaticReveal,
    listItem,
    viewportOnce,
    PREMIUM_EASE,
    cardLift
} from '@/lib/motion-variants'

// --- TypeScript Fix for Framer Motion 12 ---
const MotionDiv = motion.div as any
const MotionH1 = motion.h1 as any
const MotionH2 = motion.h2 as any
const MotionH3 = motion.h3 as any
const MotionP = motion.p as any
const MotionButton = motion.button as any
const MotionSpan = motion.span as any


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

// Section 1: Hero (Enhanced with Scroll Parallax)
const HeroSection = () => {
    const heroRef = useRef<HTMLElement | null>(null)
    const { scrollYProgress } = useScroll({
        target: heroRef as React.RefObject<HTMLElement>,
        offset: ["start start", "end start"]
    })

    // Parallax transforms
    const heroY = useTransform(scrollYProgress, [0, 1], [0, 150])
    const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
    const glowY = useTransform(scrollYProgress, [0, 1], [0, -100])
    const glowScale = useTransform(scrollYProgress, [0, 0.5], [1, 1.2])

    return (
        <section
            ref={heroRef}
            className="min-h-screen flex flex-col items-center justify-center text-center px-4 relative overflow-hidden bg-white dark:bg-transparent selection:bg-emerald-500/30"
        >
            {/* Enhanced Stage Light Glow with Parallax */}
            <MotionDiv
                style={{ y: glowY, scale: glowScale }}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] bg-emerald-500/10 blur-[150px] rounded-full pointer-events-none mix-blend-screen dark:mix-blend-plus-lighter opacity-0 dark:opacity-100 transition-opacity duration-1000"
            />

            {/* Secondary ambient glow */}
            <MotionDiv
                style={{ y: useTransform(scrollYProgress, [0, 1], [0, -50]) }}
                className="absolute top-1/4 right-1/4 w-[400px] h-[400px] bg-white/5 blur-[100px] rounded-full pointer-events-none opacity-0 dark:opacity-100"
            />

            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_20%,rgba(15,23,42,0.03),transparent_60%)] dark:hidden" />

            <MotionDiv
                style={{ y: heroY, opacity: heroOpacity }}
                className="max-w-5xl mx-auto relative z-10"
            >
                {/* Authority Badge - Enhanced */}
                <MotionDiv
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.8, ease: PREMIUM_EASE }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 dark:bg-emerald-500/10 text-slate-600 dark:text-emerald-400 text-[10px] font-bold tracking-widest uppercase mb-10 border border-slate-200 dark:border-emerald-500/20 backdrop-blur-md shadow-sm dark:shadow-glow-sm"
                >
                    <MotionDiv
                        animate={{ scale: [1, 1.2, 1], opacity: [0.7, 1, 0.7] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                        className="w-1.5 h-1.5 rounded-full bg-emerald-500"
                    />
                    Research Preview • System Online
                </MotionDiv>

                <MotionH1
                    initial={{ opacity: 0, y: 30, filter: "blur(10px)" }}
                    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    transition={{ duration: 1, delay: 0.15, ease: PREMIUM_EASE }}
                    className="text-5xl md:text-7xl font-medium tracking-[-0.03em] leading-[1.05] mb-8 text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:via-neutral-100 dark:to-neutral-400 drop-shadow-sm dark:drop-shadow-[0_0_30px_rgba(255,255,255,0.15)]"
                >
                    Audit where AI confidence <br />
                    exceeds evidence.
                </MotionH1>

                <MotionP
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.3, ease: PREMIUM_EASE }}
                    className="text-xl md:text-2xl text-slate-600 dark:text-neutral-400 max-w-3xl mx-auto mb-14 leading-relaxed font-light antialiased"
                >
                    Not fact-checking. Not binary verification. <br className="hidden md:block" />
                    A risk-aware analysis of confidence versus evidence.
                </MotionP>

                {/* Hero CTAs - Enhanced with stagger */}
                <MotionDiv
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.45, ease: PREMIUM_EASE }}
                    className="flex flex-col md:flex-row items-center justify-center gap-5"
                >
                    <Link href="/audit">
                        <MotionButton
                            whileHover={{ scale: 1.02, boxShadow: "0 15px 40px rgba(16,185,129,0.3)" }}
                            whileTap={{ scale: 0.98 }}
                            transition={{ duration: 0.2, ease: PREMIUM_EASE }}
                            className="group relative inline-flex items-center gap-3 px-8 py-4 rounded-full bg-slate-900 dark:bg-emerald-600 text-white font-medium text-sm shadow-[0_4px_10px_rgba(0,0,0,0.1),inset_0_1px_0_rgba(255,255,255,0.1)] dark:shadow-[0_10px_30px_rgba(16,185,129,0.25),inset_0_1px_0_rgba(255,255,255,0.2)] hover:bg-slate-800 dark:hover:bg-emerald-500 transition-all duration-300"
                            aria-label="Run an epistemic audit"
                        >
                            <span className="relative z-10 tracking-wide">Run Epistemic Audit</span>
                            <ArrowRight className="w-4 h-4 relative z-10 transition-transform group-hover:translate-x-1" />
                        </MotionButton>
                    </Link>

                    <Link href="/how-it-works">
                        <MotionButton
                            whileHover={{ scale: 1.02, borderColor: "rgba(255,255,255,0.2)" }}
                            whileTap={{ scale: 0.98 }}
                            transition={{ duration: 0.2, ease: PREMIUM_EASE }}
                            className="group relative inline-flex items-center px-8 py-4 bg-transparent border border-slate-200 dark:border-white/10 text-slate-600 dark:text-neutral-400 rounded-full font-medium tracking-wide text-sm transition-colors hover:border-slate-300 dark:hover:border-white/20 dark:hover:text-neutral-200"
                            aria-label="View methodology"
                        >
                            <span>Read Methodology</span>
                        </MotionButton>
                    </Link>
                </MotionDiv>
            </MotionDiv>

            {/* Scroll indicator */}
            <MotionDiv
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.5, duration: 1 }}
                style={{ opacity: useTransform(scrollYProgress, [0, 0.1], [1, 0]) }}
                className="absolute bottom-12 left-1/2 -translate-x-1/2"
            >
                <MotionDiv
                    animate={{ y: [0, 8, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    className="w-6 h-10 rounded-full border border-slate-300 dark:border-white/20 flex items-start justify-center p-2"
                >
                    <MotionDiv
                        animate={{ y: [0, 8, 0], opacity: [1, 0.3, 1] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                        className="w-1 h-2 rounded-full bg-slate-400 dark:bg-white/40"
                    />
                </MotionDiv>
            </MotionDiv>
        </section>
    )
}

// Section 2: Capabilities (Enhanced with Stagger)
const CapabilitiesSection = () => {
    const cards = [
        {
            title: "Atomic Claims",
            desc: "Prevents rhetorical masking of weak facts by isolating falsifiable units.",
            glyph: <Search className="w-5 h-5" />
        },
        {
            title: "Structured Evidence",
            desc: "Blocks hallucinations backed only by model consensus using authoritative knowledge graphs.",
            glyph: <Globe className="w-5 h-5" />
        },
        {
            title: "Epistemic Risk",
            desc: "Quantifies overconfidence instead of hiding it. Rewards calibrated uncertainty.",
            glyph: <AlertTriangle className="w-5 h-5" />
        }
    ]

    return (
        <section className="py-32 px-4 bg-transparent">
            <div className="max-w-6xl mx-auto">
                <MotionDiv
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={viewportOnce}
                    className="grid grid-cols-1 md:grid-cols-3 gap-8"
                >
                    {cards.map((card, idx) => (
                        <MotionDiv
                            key={card.title}
                            variants={staggerItem}
                            whileHover={{
                                borderColor: "rgba(255, 255, 255, 0.15)",
                                backgroundColor: "rgba(255, 255, 255, 0.02)",
                                transition: { duration: 0.3 }
                            }}
                            className="p-8 rounded-2xl border border-white/5 dark:border-neutral-800 hover:border-white/10 dark:hover:border-neutral-700 transition-all duration-500 group relative overflow-hidden"
                        >
                            {/* Hover glow effect */}
                            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-radial from-emerald-500/5 via-transparent to-transparent pointer-events-none" />

                            <div className="relative z-10">
                                <div className="mb-6 p-3 w-fit rounded-xl bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 group-hover:border-emerald-500/20 transition-all duration-300">
                                    {card.glyph}
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3 group-hover:text-black dark:group-hover:text-white transition-colors">{card.title}</h3>
                                <p className="text-slate-500 dark:text-slate-400 leading-relaxed font-light">{card.desc}</p>
                            </div>
                        </MotionDiv>
                    ))}
                </MotionDiv>
            </div>
        </section>
    )
}

// Section 3: Positioning (Enhanced)
const PositioningSection = () => (
    <section className="py-32 px-4 bg-transparent border-y border-slate-100 dark:border-border-subtle">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <MotionDiv
                initial="hidden"
                whileInView="visible"
                viewport={viewportOnce}
                variants={staggerContainer}
            >
                <MotionH2
                    variants={fadeUp}
                    className="text-3xl font-medium text-neutral-900 dark:text-neutral-200 mb-8 leading-tight tracking-[-0.02em]"
                >
                    Why hallucinations <br />aren't binary
                </MotionH2>
                <MotionDiv variants={fadeUp} className="space-y-6">
                    <p className="text-lg text-slate-600 dark:text-slate-400 font-light leading-relaxed">
                        Modern AI failures are rarely outright falsehoods.
                        They are overconfident claims weakly grounded in evidence.
                    </p>
                    <p className="text-lg text-slate-600 dark:text-slate-400 font-light leading-relaxed">
                        This system is designed to surface that risk — explicitly.
                        By decomposing text into discrete nodes of inquiry, we move past "True/False" toward "Calibrated/Uncalibrated."
                    </p>
                </MotionDiv>
            </MotionDiv>

            <MotionDiv
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={viewportOnce}
                transition={{ duration: 0.8, ease: PREMIUM_EASE }}
                className="relative p-12 rounded-3xl bg-neutral-900 dark:bg-neutral-900/80 border border-neutral-800 overflow-hidden min-h-[400px] flex flex-col justify-center"
            >
                {/* Background glow */}
                <div className="absolute inset-0 bg-gradient-radial from-emerald-500/10 via-transparent to-transparent opacity-50" />

                <div className="relative z-10 flex flex-col gap-6">
                    {['Text', 'Claims', 'Evidence', 'Risk Score'].map((item, idx) => (
                        <div key={item} className="flex items-center gap-4">
                            <MotionDiv
                                initial={{ width: 0, opacity: 0 }}
                                whileInView={{ width: '100%', opacity: 1 }}
                                viewport={{ once: true }}
                                transition={{ duration: 1.2, delay: idx * 0.3, ease: PREMIUM_EASE }}
                                className="h-0.5 bg-slate-700 relative"
                            >
                                {idx < 3 && (
                                    <MotionDiv
                                        initial={{ opacity: 0, scale: 0 }}
                                        whileInView={{ opacity: 1, scale: 1 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: (idx + 1) * 0.3, duration: 0.3 }}
                                        className="absolute -right-1 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                                    />
                                )}
                            </MotionDiv>
                            <span className="text-xs font-mono text-slate-400 uppercase tracking-widest whitespace-nowrap min-w-[100px]">{item}</span>
                        </div>
                    ))}
                </div>
                <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.05),transparent)]" />
            </MotionDiv>
        </div>
    </section >
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
    const [cardPos, setCardPos] = useState({ left: 0, top: 0, placement: 'above' })

    useEffect(() => {
        const updateCardPos = () => {
            if (!containerRef.current || !current.targetId) return
            const targetEl = claimRefs.current[current.targetId]
            if (targetEl) {
                const cRect = containerRef.current.getBoundingClientRect()
                const tRect = targetEl.getBoundingClientRect()

                // Step 1: Measure Geometry
                const cardWidth = 340
                const cardHeight = 260 // Hardcoded estimate for stable bounding
                const padding = 24
                const gap = 12

                // --- Horizontal Clamping (X-Axis) ---
                const claimCenterX = (tRect.left - cRect.left) + (tRect.width / 2)
                const idealLeft = claimCenterX - (cardWidth / 2)
                const minLeft = padding
                const maxLeft = cRect.width - cardWidth - padding
                const finalLeft = Math.max(minLeft, Math.min(idealLeft, maxLeft))

                // --- Vertical Clamping (Y-Axis) ---
                // bi-directional flipping logic to prevent top overflow
                const claimRelativeTop = tRect.top - cRect.top
                const claimRelativeBottom = tRect.bottom - cRect.top

                const candidateAbove = claimRelativeTop - cardHeight - gap
                const candidateBelow = claimRelativeBottom + gap

                let finalTop = candidateAbove // Default preference: Above
                let placement = 'above'

                // Decision Logic:
                const fitsAbove = candidateAbove >= padding
                const fitsBelow = (candidateBelow + cardHeight) <= (cRect.height - padding)

                if (fitsAbove) {
                    finalTop = candidateAbove
                    placement = 'above'
                } else if (fitsBelow) {
                    finalTop = candidateBelow
                    placement = 'below'
                } else {
                    // Fallback: Clamp strictly inside container
                    // Prefer keeping top visible over bottom if compressed
                    finalTop = Math.max(padding, Math.min(candidateAbove, cRect.height - cardHeight - padding))
                    placement = 'above'
                }

                setCardPos({ left: finalLeft, top: finalTop, placement })
            }
        }

        // Update on step/state change + resize
        updateCardPos()
        window.addEventListener('resize', updateCardPos)
        return () => window.removeEventListener('resize', updateCardPos)
    }, [activeStep, demoState, current.targetId])

    return (
        <section className="py-32 px-4 bg-transparent">
            <div className="max-w-6xl mx-auto text-center mb-16 px-4">
                <div
                    className="inline-flex items-center gap-3 p-1.5 bg-slate-200/50 dark:bg-white/5 rounded-full mb-8 cursor-pointer select-none transition-colors hover:bg-slate-200 dark:hover:bg-white/10 border border-transparent dark:border-white/5"
                    onClick={() => {
                        setViewMode(prev => prev === 'GUIDED' ? 'EXPERT' : 'GUIDED')
                        if (viewMode === 'GUIDED') setDemoState('ENTRY') // Restart loop on toggle back
                    }}
                >
                    <span className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === 'GUIDED' ? 'bg-white dark:bg-white/10 shadow-sm text-slate-800 dark:text-neutral-200' : 'text-slate-400 dark:text-neutral-500'}`}>Guided</span>
                    <span className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all ${viewMode === 'EXPERT' ? 'bg-white dark:bg-white/10 shadow-sm text-slate-800 dark:text-neutral-200' : 'text-slate-400 dark:text-neutral-500'}`}>Expert</span>
                </div>

                <h2 className="text-2xl font-medium text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-slate-50 dark:via-slate-300 dark:to-slate-50 animate-text-shimmer mb-4 tracking-[-0.02em]">How the System Audits Claims</h2>
                <p className="text-slate-500 dark:text-slate-400 font-light max-w-2xl mx-auto leading-relaxed">
                    {viewMode === 'GUIDED' ? 'A slower, guided preview of the epistemic analysis process.' : 'Full inspection mode. Hover to analyze discrete claims directly.'}
                    <br className="hidden sm:block" />
                    Observe how discrete claims are isolated, cross-referenced, and scored for risk.
                </p>
            </div>

            <div className="max-w-4xl mx-auto relative group">
                <AnimatePresence>
                    {viewMode === 'GUIDED' && demoState !== 'INSPECT_FREELY' && (
                        <MotionDiv
                            key="cursor"
                            initial={false}
                            animate={{
                                x: cursorPos.x,
                                y: cursorPos.y,
                                scale: demoState === 'DWELL_ON_CLAIM' ? 0.9 : 1,
                                opacity: demoState === 'EXIT_RITUAL' ? 0 : 1
                            }}
                            transition={{
                                type: "spring",
                                stiffness: 200,
                                damping: 30,
                                mass: 0.9
                            }}
                            className="absolute w-6 h-6 rounded-full border border-neutral-800 bg-neutral-900/50 pointer-events-none z-50 flex items-center justify-center backdrop-blur-sm -translate-x-1/2 -translate-y-1/2"
                            style={{ top: 0, left: 0 }}
                            {...({} as any)}
                        >
                            <div className="w-1.5 h-1.5 bg-slate-900 dark:bg-white rounded-full opacity-50" />
                        </MotionDiv>
                    )}
                </AnimatePresence>

                <MotionDiv
                    ref={containerRef}
                    {...({
                        initial: { opacity: 0, y: 30 },
                        whileInView: { opacity: 1, y: 0 },
                        className: "bg-white dark:bg-neutral-900/40 border border-slate-200 dark:border-neutral-800 rounded-3xl overflow-hidden relative min-h-[500px] flex flex-col transition-colors duration-300"
                    } as any)}
                >
                    {/* Cognitive Anchor Hint */}
                    <AnimatePresence>
                        {(activeStep === 0 && demoState === 'INTENT_PAUSE' && viewMode === 'GUIDED') && (
                            <MotionDiv
                                {...({
                                    initial: { opacity: 0, y: -10 },
                                    animate: { opacity: 1, y: 0 },
                                    exit: { opacity: 0 },
                                    className: "absolute top-8 left-1/2 -translate-x-1/2 bg-slate-900 dark:bg-black text-white text-[10px] uppercase font-bold tracking-widest px-3 py-1.5 rounded-full z-20 shadow-xl pointer-events-none border border-transparent dark:border-white/10"
                                } as any)}
                            >
                                Analyzing Independent Claims
                            </MotionDiv>
                        )}
                    </AnimatePresence>

                    <AnimatePresence>
                        {isCardVisible && (
                            <MotionDiv
                                key="overlay-card"
                                initial={{ opacity: 0, scale: 0.95, top: cardPos.top + 10, left: cardPos.left }}
                                animate={{
                                    opacity: 1,
                                    scale: 1,
                                    top: cardPos.top,
                                    left: cardPos.left
                                }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{
                                    type: "spring",
                                    stiffness: 300,
                                    damping: 30,
                                    opacity: { duration: 0.2 }
                                }}
                                className="absolute w-[340px] z-40 origin-top-left"
                                style={{ bottom: 'auto' }}
                                {...({} as any)}
                            >
                                {/* Visual Tether */}
                                <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible z-0">
                                    <line
                                        x1="50%"
                                        y1={cardPos.placement === 'above' ? "100%" : "0%"}
                                        x2="50%"
                                        y2={cardPos.placement === 'above' ? "calc(100% + 12px)" : "-12px"}
                                        stroke="currentColor"
                                        strokeWidth="1"
                                        strokeDasharray="4 4"
                                        className={(isHighlightActive && current.targetId === 'CLAIM_REVENUE') ? `text-${current.color}-400` : 'text-slate-300'}
                                    />
                                </svg>

                                <div className={`
                                    p-5 rounded-2xl
                                    bg-white/80 dark:bg-white/[0.06]
                                    backdrop-blur-xl

                                    border border-slate-200/60 dark:border-white/10

                                    shadow-[0_20px_40px_rgba(0,0,0,0.12)]
                                    dark:shadow-[0_20px_60px_rgba(0,0,0,0.6)]

                                    text-slate-700 dark:text-neutral-200

                                    transition-colors transition-shadow duration-300
                                    relative overflow-hidden
                                    ${(isHighlightActive && current.targetId === 'CLAIM_REVENUE') ? `border-emerald-500/50 dark:border-${current.color}-900/50` : ''}
                                `}>
                                    <div role="note" className="space-y-4 relative z-10">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2.5">
                                                <div className={`w-2 h-2 rounded-full bg-${current.color}-500 shadow-[0_0_8px_rgba(16,185,129,0.15)] dark:shadow-[0_0_8px_rgba(16,185,129,0.3)]`} />
                                                <span className="text-[10px] font-black text-slate-800 dark:text-neutral-100 uppercase tracking-[0.15em]">{current.header}</span>
                                            </div>
                                            <span className="text-[9px] font-mono text-slate-400 dark:text-neutral-500 uppercase tracking-widest">Step {activeStep + 1} of {stages.length}</span>
                                        </div>
                                        <p className="text-[13px] text-slate-600 dark:text-neutral-300 leading-relaxed font-medium">{current.body}</p>
                                        <MotionP
                                            key={`${activeStep}-note`}
                                            {...({
                                                initial: { opacity: 0 },
                                                animate: { opacity: 1 },
                                                transition: { delay: 1.5, duration: 1 },
                                                className: "text-[11px] text-slate-400 dark:text-neutral-400 italic font-light"
                                            } as any)}
                                        >
                                            {current.microNote}
                                        </MotionP>
                                        <div className="pt-2 border-t border-slate-200/50 dark:border-white/5 italic text-[10px] text-slate-400 dark:text-neutral-500/80">
                                            {current.footer}
                                        </div>
                                        <div className="space-y-2 pt-1">
                                            <div className="flex justify-between text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                                                <span>Alignment Strength</span>
                                                <span className={`text-${current.color}-600`}>Strong</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-200/70 dark:bg-white/10 rounded-full overflow-hidden relative">
                                                <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 via-yellow-500/20 to-emerald-500/20" />
                                                <MotionDiv
                                                    {...({
                                                        initial: { width: 0 },
                                                        animate: { width: `${current.risk}%` },
                                                        transition: { duration: 0.8, delay: 0.2 },
                                                        className: `h-full bg-gradient-to-r from-slate-200 to-${current.color}-500 relative z-10 opacity-90`
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
                            </MotionDiv>
                        )}
                    </AnimatePresence>

                    <div className="p-16 pt-32 flex-grow">
                        <div className="relative text-slate-700 dark:text-slate-300 font-light leading-relaxed max-w-2xl text-xl mx-auto space-y-8">
                            <div className="leading-relaxed select-none">
                                <MotionSpan
                                    ref={(el: HTMLSpanElement | null) => { claimRefs.current['CLAIM_ENTITY'] = el }}
                                    data-claim-id="CLAIM_ENTITY"
                                    {...({
                                        animate: {
                                            opacity: (isHighlightActive && activeStep === 1) ? 1 : 0.6,
                                            backgroundColor: (isHighlightActive && activeStep === 1) ? 'rgba(241, 245, 249, 1)' : 'transparent',
                                            // Dark mode override
                                            ...(isHighlightActive && activeStep === 1 ? { backgroundColor: 'rgba(51, 65, 85, 0.4)' } : {})
                                        },
                                        className: "px-1 rounded-lg transition-colors duration-500 relative group/claim dark:bg-opacity-20"
                                    } as any)}
                                >
                                    Alphabet Inc. reported
                                    {viewMode === 'EXPERT' && (
                                        <span className="absolute -top-4 left-0 text-[9px] font-mono text-slate-400 bg-slate-100 dark:bg-slate-800 px-1 rounded border border-slate-200 dark:border-slate-700 opacity-0 group-hover/claim:opacity-100 transition-opacity uppercase tracking-wider whitespace-nowrap z-20">
                                            [SUBJECT: ENTITY]
                                        </span>
                                    )}
                                </MotionSpan> that its quarterly {' '}
                                <MotionSpan
                                    ref={(el: HTMLSpanElement | null) => { claimRefs.current['CLAIM_REVENUE'] = el }}
                                    data-claim-id="CLAIM_REVENUE"
                                    style={{
                                        // Specific dark mode color handling in style prop for reliability
                                        ['--highlight-bg' as any]: (isHighlightActive && activeStep === 0) ? 'rgba(16, 185, 129, 0.25)' : 'rgba(16, 185, 129, 0.12)',
                                        ['--highlight-text' as any]: (isHighlightActive && activeStep === 0) ? '#064e3b' : '#065f46',
                                        ['--highlight-border' as any]: (isHighlightActive && activeStep === 0) ? '#10b981' : 'rgba(16, 185, 129, 0.3)'
                                    }}
                                    {...({
                                        animate: {
                                            backgroundColor: (isHighlightActive && activeStep === 0) ? 'rgba(16, 185, 129, 0.25)' : 'rgba(16, 185, 129, 0.12)',
                                            color: (isHighlightActive && activeStep === 0) ? '#064e3b' : '#065f46',
                                            borderColor: (isHighlightActive && activeStep === 0) ? '#10b981' : 'rgba(16, 185, 129, 0.3)'
                                        },
                                        className: "px-2 py-0.5 rounded-sm border-l-2 font-normal relative inline-block transition-all duration-500 group/claim dark:!text-emerald-300 dark:!bg-emerald-900/20 dark:!border-emerald-500/40"
                                    } as any)}
                                >
                                    revenue exceeded $20B in Q4
                                    {(isHighlightActive && activeStep === 0) && (
                                        <MotionSpan
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
                                            <span className="text-[9px] font-mono text-slate-400 bg-slate-100 dark:bg-slate-800 px-1 rounded border border-slate-200 dark:border-slate-700 uppercase tracking-wider whitespace-nowrap">
                                                [PREDICATE: \u003E]
                                            </span>
                                            <span className="text-[9px] font-mono text-slate-400 bg-slate-100 dark:bg-slate-800 px-1 rounded border border-slate-200 dark:border-slate-700 uppercase tracking-wider whitespace-nowrap">
                                                [QUANTIFIER: $20B]
                                            </span>
                                        </div>
                                    )}
                                </MotionSpan>
                                , marking a continuation of its fiscal growth trajectory in the advertising sector.
                            </div>
                        </div>
                    </div>

                    <div className="p-8 bg-slate-50/50 dark:bg-white/5 border-t border-slate-100 dark:border-white/5 flex flex-col items-center gap-6 transition-colors duration-300">
                        <div className="relative flex items-center justify-center gap-12 w-full max-w-md">
                            {[0, 1, 2, 3, 4].map((i) => {
                                const isFocused = (activeStep === 0 && i === 3) || (activeStep === 1 && i === 0)
                                const isTimeActive = (isFocused && isHighlightActive) || viewMode === 'EXPERT'
                                return (
                                    <div key={i} className="relative flex flex-col items-center">
                                        <MotionDiv
                                            {...({
                                                animate: {
                                                    opacity: isTimeActive ? 1 : 0.4,
                                                    backgroundColor: isTimeActive && isFocused ? '#10b981' : '#cbd5e1',
                                                    scale: isTimeActive && isFocused ? [1, 1.3, 1] : 1
                                                },
                                                transition: { duration: 0.4, repeat: isTimeActive && isFocused ? Infinity : 0, repeatDelay: 2 },
                                                className: `w-2.5 h-2.5 rounded-full z-10 relative ${isTimeActive && isFocused ? 'ring-4 ring-emerald-100 dark:ring-emerald-900' : ''}`
                                            } as any)}
                                        />
                                    </div>
                                )
                            })}
                            <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-100 dark:bg-slate-800/50 -z-0 translate-y-[-1px]" />
                        </div>
                    </div>
                </MotionDiv>
            </div >
        </section >
    )
}

// Section 5: Serious Use (Enhanced)
const SeriousUseSection = () => {
    const rows = [
        { label: "Research & Audit", icon: <FileSearch className="w-4 h-4" /> },
        { label: "Policy & Governance", icon: <Landmark className="w-4 h-4" /> },
        { label: "Journalism & Analysis", icon: <FileText className="w-4 h-4" /> },
        { label: "Model Evaluation", icon: <Scale className="w-4 h-4" /> }
    ]

    return (
        <section className="py-32 px-4 bg-transparent">
            <div className="max-w-4xl mx-auto">
                <MotionH2
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={viewportOnce}
                    className="text-xs font-bold text-slate-400 uppercase tracking-[0.2em] text-center mb-16"
                >
                    Designed for Strict Contexts
                </MotionH2>
                <MotionDiv
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={viewportOnce}
                    className="space-y-4"
                >
                    {rows.map((row, idx) => (
                        <MotionDiv
                            key={row.label}
                            variants={listItem}
                            whileHover={{
                                borderColor: "rgba(255, 255, 255, 0.15)",
                                x: 4,
                                transition: { duration: 0.2 }
                            }}
                            className="group flex items-center justify-between p-6 rounded-xl border border-white/5 dark:border-neutral-800 hover:border-white/10 dark:hover:border-neutral-700 transition-all duration-300"
                        >
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-white dark:bg-white/5 rounded-lg border border-slate-200 dark:border-white/10 shadow-sm text-slate-500 dark:text-neutral-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 group-hover:border-emerald-500/20 transition-all duration-300">
                                    {row.icon}
                                </div>
                                <span className="font-semibold text-slate-800 dark:text-slate-200">{row.label}</span>
                            </div>
                            <span className="text-sm text-slate-400 dark:text-slate-500 font-light italic hidden md:block">Built for traceability, not persuasion.</span>
                        </MotionDiv>
                    ))}
                </MotionDiv>
            </div>
        </section>
    )
}

// Section: Failure Modes (Enhanced)
const FailureModeSection = () => {
    const failures = [
        {
            title: "1. Outdated Structured Data",
            desc: "If knowledge references (e.g. SEC filings) are stale, the engine may flag recent valid claims as unsupported.",
            note: "(Disclosure: Latency gap ~24h)"
        },
        {
            title: "2. Ambiguous Predicates",
            desc: "Language with high semantic drift (e.g. \"revolutionary\") cannot be rigorously falsified.",
            note: null
        },
        {
            title: "3. Registry Gaps",
            desc: "Claims referencing private datasets or non-public events are invisible to the verification layer.",
            note: null
        },
        {
            title: "4. Over-Compression",
            desc: "Complex multi-part claims may be atomicized incorrectly, losing context.",
            note: null
        }
    ]

    return (
        <section className="py-24 px-4 bg-transparent border-t border-slate-100 dark:border-slate-900">
            <div className="max-w-3xl mx-auto text-left">
                <MotionDiv
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={viewportOnce}
                    className="flex items-center gap-3 mb-8 text-slate-500 dark:text-slate-400"
                >
                    <AlertOctagon className="w-5 h-5 opacity-50" />
                    <h3 className="text-sm font-bold uppercase tracking-widest">Where This System Can Fail</h3>
                </MotionDiv>

                <MotionDiv
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={viewportOnce}
                    className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6"
                >
                    {failures.map((item) => (
                        <MotionDiv key={item.title} variants={staggerItem} className="space-y-2">
                            <h4 className="text-xs font-mono font-semibold text-slate-900 dark:text-slate-200">{item.title}</h4>
                            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed font-light">
                                {item.desc}
                                {item.note && <span className="text-slate-400 dark:text-slate-500 italic"> {item.note}</span>}
                            </p>
                        </MotionDiv>
                    ))}
                </MotionDiv>
            </div>
        </section>
    )
}

// Section: Epistemic Refusal (Humility) - Enhanced
const RefusalSection = () => {
    const refusals = [
        "Does NOT infer intent from text.",
        "Does NOT deference to model consensus.",
        "Does NOT collapse epistemic uncertainty.",
        "Does NOT validate non-falsifiable rhetoric."
    ]

    return (
        <section className="py-24 px-4 bg-transparent border-t border-slate-100 dark:border-slate-900">
            <div className="max-w-3xl mx-auto text-center">
                <MotionH3
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={viewportOnce}
                    className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-12"
                >
                    System Constraints & Refusals
                </MotionH3>
                <MotionDiv
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={viewportOnce}
                    className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left"
                >
                    {refusals.map((item, i) => (
                        <MotionDiv
                            key={i}
                            variants={staggerItem}
                            whileHover={{ borderColor: "rgba(239, 68, 68, 0.2)", transition: { duration: 0.2 } }}
                            className="flex items-start gap-4 p-5 rounded-xl bg-white dark:bg-white/[0.02] border border-slate-100 dark:border-white/5 shadow-sm dark:shadow-none transition-all duration-300 group"
                        >
                            <XCircle className="w-5 h-5 text-slate-300 dark:text-slate-600 mt-0.5 shrink-0 group-hover:text-red-400 transition-colors" />
                            <span className="text-sm text-slate-600 dark:text-slate-400 font-medium">{item}</span>
                        </MotionDiv>
                    ))}
                </MotionDiv>
            </div>
        </section>
    )
}

// Section 6: Boundaries (Final Section) - Enhanced with Progressive Reveal
const BoundariesSection = () => (
    <section className="py-40 px-4 bg-transparent text-slate-300 relative overflow-hidden">
        {/* Subtle top vignette */}
        <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-black/20 to-transparent pointer-events-none" />

        <MotionDiv
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
            variants={staggerContainer}
            className="max-w-3xl mx-auto text-center space-y-12 relative z-10"
        >
            <div>
                <MotionH2
                    variants={fadeUp}
                    className="text-4xl font-light leading-tight tracking-tight mb-6 text-slate-800 dark:text-slate-200"
                >
                    This is not a truth oracle. <br />
                    <MotionSpan
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.4, duration: 0.8 }}
                    >
                        It does not declare facts "true" or "false."
                    </MotionSpan>
                </MotionH2>
                <MotionP
                    variants={fadeUp}
                    className="text-xl text-slate-500 font-light leading-relaxed"
                >
                    It exposes epistemic gaps — where confidence exceeds evidence. <br />
                    <MotionSpan
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.6, duration: 0.8 }}
                        className="text-slate-400"
                    >
                        A tool for human experts to audit the recursive overconfidence of large language models.
                    </MotionSpan>
                </MotionP>
                <MotionDiv
                    variants={fadeUp}
                    className="text-xs font-mono text-slate-500 uppercase tracking-widest pt-8 border-t border-slate-200 dark:border-slate-800 mt-8"
                >
                    System State: Nominal • Research Artifact v1.5.1
                </MotionDiv>
            </div>

            {/* System Status Footer - Enhanced */}
            <MotionDiv
                variants={fadeUp}
                className="pt-20 flex flex-col items-center gap-3 border-t border-slate-200 dark:border-slate-800"
            >
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                    <MotionDiv
                        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                        className="w-1.5 h-1.5 rounded-full bg-emerald-500"
                    />
                    <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">System Status: Active</span>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-600 font-light">
                    Epistemic Audit Engine v1.5.1 (Research Artifact)
                </div>
            </MotionDiv>
        </MotionDiv>
    </section>
)

export default function LandingPage() {
    return (
        <div className="bg-transparent overflow-x-hidden transition-colors duration-300">
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