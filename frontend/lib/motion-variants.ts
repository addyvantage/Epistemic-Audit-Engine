/**
 * Shared Framer Motion Variants Library
 *
 * Centralized animation patterns for consistent motion across the UI.
 * All durations use the project's custom easing: cubic-bezier(0.22, 1, 0.36, 1)
 */

import { Variants, Transition } from 'framer-motion'

// Base easing curve (matches globals.css)
export const PREMIUM_EASE = [0.22, 1, 0.36, 1] as const

// Standard transition presets
export const transitions = {
    fast: { duration: 0.2, ease: PREMIUM_EASE },
    normal: { duration: 0.4, ease: PREMIUM_EASE },
    slow: { duration: 0.6, ease: PREMIUM_EASE },
    dramatic: { duration: 1.2, ease: PREMIUM_EASE },
    spring: { type: "spring" as const, stiffness: 200, damping: 25 },
    springBouncy: { type: "spring" as const, stiffness: 300, damping: 20 },
} satisfies Record<string, Transition>

// --- Section & Container Variants ---

/**
 * Fade up animation - the workhorse for section reveals
 */
export const fadeUp: Variants = {
    hidden: {
        opacity: 0,
        y: 20
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.6,
            ease: PREMIUM_EASE
        }
    }
}

/**
 * Fade up with larger distance - for dramatic reveals
 */
export const fadeUpLarge: Variants = {
    hidden: {
        opacity: 0,
        y: 40
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.8,
            ease: PREMIUM_EASE
        }
    }
}

/**
 * Stagger container - wrap children that should animate sequentially
 */
export const staggerContainer: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2
        }
    }
}

/**
 * Fast stagger container - for tighter sequences
 */
export const staggerContainerFast: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.05,
            delayChildren: 0.1
        }
    }
}

/**
 * Stagger item - use as child of staggerContainer
 */
export const staggerItem: Variants = {
    hidden: {
        opacity: 0,
        y: 20
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.4,
            ease: PREMIUM_EASE
        }
    }
}

// --- Dramatic Reveal Variants ---

/**
 * Scale in with subtle blur - for important UI moments
 */
export const scaleIn: Variants = {
    hidden: {
        opacity: 0,
        scale: 0.95
    },
    visible: {
        opacity: 1,
        scale: 1,
        transition: {
            duration: 0.5,
            ease: PREMIUM_EASE
        }
    }
}

/**
 * Dramatic reveal - for hero elements and key focal points
 */
export const dramaticReveal: Variants = {
    hidden: {
        opacity: 0,
        scale: 0.9,
        filter: "blur(10px)"
    },
    visible: {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        transition: {
            duration: 1.2,
            ease: PREMIUM_EASE
        }
    }
}

/**
 * Scale in with blur - lighter version of dramatic reveal
 */
export const scaleInBlur: Variants = {
    hidden: {
        opacity: 0,
        scale: 0.95,
        filter: "blur(4px)"
    },
    visible: {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        transition: {
            duration: 0.6,
            ease: PREMIUM_EASE
        }
    }
}

// --- Slide Variants ---

/**
 * Slide in from right - for panels and sidebars
 */
export const slideInRight: Variants = {
    hidden: {
        opacity: 0,
        x: 100
    },
    visible: {
        opacity: 1,
        x: 0,
        transition: {
            type: "spring",
            damping: 25,
            stiffness: 200
        }
    },
    exit: {
        opacity: 0,
        x: 50,
        transition: {
            duration: 0.3,
            ease: PREMIUM_EASE
        }
    }
}

/**
 * Slide in from left
 */
export const slideInLeft: Variants = {
    hidden: {
        opacity: 0,
        x: -100
    },
    visible: {
        opacity: 1,
        x: 0,
        transition: {
            type: "spring",
            damping: 25,
            stiffness: 200
        }
    }
}

/**
 * Slide in from bottom - for modals and tooltips
 */
export const slideInBottom: Variants = {
    hidden: {
        opacity: 0,
        y: 50
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            type: "spring",
            damping: 25,
            stiffness: 200
        }
    },
    exit: {
        opacity: 0,
        y: 20,
        transition: {
            duration: 0.2,
            ease: PREMIUM_EASE
        }
    }
}

// --- Card Variants ---

/**
 * Card hover effect - use with whileHover
 */
export const cardHover = {
    scale: 1.02,
    transition: { duration: 0.2, ease: PREMIUM_EASE }
}

/**
 * Card tap effect - use with whileTap
 */
export const cardTap = {
    scale: 0.98
}

/**
 * Card with lift - combines scale and shadow
 */
export const cardLift: Variants = {
    rest: {
        scale: 1,
        y: 0,
        transition: { duration: 0.2, ease: PREMIUM_EASE }
    },
    hover: {
        scale: 1.02,
        y: -4,
        transition: { duration: 0.2, ease: PREMIUM_EASE }
    },
    tap: {
        scale: 0.98,
        y: 0
    }
}

// --- Button Variants ---

/**
 * Primary button animation
 */
export const buttonPrimary: Variants = {
    rest: {
        scale: 1,
        transition: { duration: 0.2, ease: PREMIUM_EASE }
    },
    hover: {
        scale: 1.02,
        transition: { duration: 0.2, ease: PREMIUM_EASE }
    },
    tap: {
        scale: 0.98
    }
}

// --- List Variants ---

/**
 * List container with stagger
 */
export const listContainer: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            when: "beforeChildren",
            staggerChildren: 0.08
        }
    }
}

/**
 * List item animation
 */
export const listItem: Variants = {
    hidden: {
        opacity: 0,
        x: -20
    },
    visible: {
        opacity: 1,
        x: 0,
        transition: {
            duration: 0.3,
            ease: PREMIUM_EASE
        }
    }
}

// --- Table Row Variants ---

/**
 * Table row with stagger - for data tables
 */
export const tableRowStagger: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.05
        }
    }
}

export const tableRow: Variants = {
    hidden: {
        opacity: 0,
        y: 10
    },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.3,
            ease: PREMIUM_EASE
        }
    }
}

// --- Pulse & Glow Variants ---

/**
 * Gentle pulse - for status indicators
 */
export const gentlePulse: Variants = {
    pulse: {
        scale: [1, 1.05, 1],
        opacity: [0.7, 1, 0.7],
        transition: {
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
        }
    }
}

/**
 * Glow pulse - for highlighted elements
 */
export const glowPulse: Variants = {
    glow: {
        boxShadow: [
            "0 0 20px rgba(16, 185, 129, 0.1)",
            "0 0 30px rgba(16, 185, 129, 0.2)",
            "0 0 20px rgba(16, 185, 129, 0.1)"
        ],
        transition: {
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
        }
    }
}

// --- Progress Variants ---

/**
 * Progress bar fill animation
 */
export const progressFill = (percentage: number): Variants => ({
    hidden: { width: "0%" },
    visible: {
        width: `${percentage}%`,
        transition: {
            duration: 1,
            ease: PREMIUM_EASE,
            delay: 0.3
        }
    }
})

/**
 * Count up animation helper
 */
export const countUp: Variants = {
    hidden: {
        opacity: 0,
        scale: 0.8
    },
    visible: {
        opacity: 1,
        scale: 1,
        transition: {
            duration: 0.5,
            ease: PREMIUM_EASE
        }
    }
}

// --- Viewport Options ---

/**
 * Standard viewport options for whileInView
 */
export const viewportOnce = { once: true, margin: "-100px" }
export const viewportAlways = { once: false, margin: "-50px" }

// --- Utility Functions ---

/**
 * Creates a delay variant for staggered manual control
 */
export const withDelay = (variants: Variants, delay: number): Variants => {
    const result: Variants = {}
    for (const key in variants) {
        const variant = variants[key]
        if (typeof variant === 'object' && variant !== null) {
            result[key] = {
                ...variant,
                transition: {
                    ...(variant as any).transition,
                    delay: ((variant as any).transition?.delay || 0) + delay
                }
            }
        }
    }
    return result
}

/**
 * Creates a custom stagger container with specified timing
 */
export const createStaggerContainer = (
    staggerDelay: number = 0.1,
    initialDelay: number = 0.2
): Variants => ({
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: staggerDelay,
            delayChildren: initialDelay
        }
    }
})
