# Task Checklist: Epistemic Audit Engine

- [x] **Landing Page v1.6: Hero Navigation**
  - [x] **Feature: Audit Entry Point**: Add "Run an Epistemic Audit" button to hero.
  - [x] **Interaction**: Implement minimal hover/tap micro-interactions (no glow).
  - [x] **Routing**: Link to `/audit`.

- [x] **Landing Page v1.7: Hero Navigation Finalization**
  - [x] **Feature: Dual Entry**: Add Secondary "View Methodology" ghost button.
  - [x] **Accessibility**: Ensure full keyboard focus/tab support for both.
  - [x] **Layout**: Stack on mobile, inline on desktop.
  - [x] **Verification**: Confirm keyboard nav works end-to-end.

- [x] **Landing Page v1.5.1: Stability & Audit Hardening**
  - [x] **Hook Extraction**: Isolate cursor logic in `useGuidedCursor`.
  - [x] **Font-Awareness**: Trigger recalculation on `document.fonts.ready`.
  - [x] **Dev Guards**: Warn if target refs are null.
  - [x] **Timer Freeze**: Ensure strictly zero timers in `INSPECT_FREELY`.
  - [x] **Instrumentation**: Add `data-claim-id` to spans.

- [x] **Landing Page v1.5: Research-Grade Interface Expansion**
  - [x] **Feature: Claim Decomposition**: Toggleable "Expert" overlay showing Predicate/Subject/Quantifier.
  - [x] **Feature: Evidence Strength Gradient**: Visualizing "Alignment Strength" instead of binary verification.
  - [x] **Feature: Provenance Preview**: Read-only metadata panel (Source Class, Timestamp).
  - [x] **Feature: Failure Mode Section**: Explicit "Where This System Can Fail" text block.
  - [x] **Refinement: Copy Audit**: Replace "Trust/Verified" with "Surfaces/Indicates".
  - [x] **Refinement: Cursor Logic**: Stop after 2 cycles; idempotent scroll.

- [x] **Landing Page v1.4.1: Cursor Position Fix**
  - [x] **Ref-Based Positioning**: Anchor cursor to actual DOM elements (`getBoundingClientRect`).
  - [x] **Coordinate System**: Ensure `position: relative` on container.
  - [x] **Exit Ritual**: Reset to neutral position relative to container.

- [x] **Landing Page v1.4: Epistemic UX Hardening**
  - [x] **Cursor Pedagogy**: Implement Entry Ritual, Intent Pause, and Exit Ritual in the State Machine.
  - [x] **Dual Modes**: Add "Guided" (Teaching) vs "Expert" (Inspection) mode toggle.
  - [x] **Micro-Annotations**: Add "Why this matters" delayed fade-in text to explanation cards.
  - [x] **Epistemic Humility**: Add "What This System Refuses To Do" section.
  - [x] **Timeline Semantics**: Ensure timeline nodes map 1:1 to claim indices with semantic labels.

- [x] **Landing Page v1.3: Guided Explainability Final**
  - [x] **Guided Demo Refinement**: Ensure cursor enters from outside and follows strict Move -> Dwell -> Explain cycle.
  - [x] **Explanations**: Verify headers match "Claim Isolation"/"Evidence Matching" and answer What, Why, Risk.
  - [x] **Visuals**: Check for "Step X of Y" counters and "Explainability Mode: Guided" pill.
  - [x] **Scroll Logic**: Confirm bidirectional scroll on all pedagogical sections.
  - [x] **Ending**: Verify clean exit (no CTA).

- [x] **Landing Page v1.2: Finalization & Hardening**
  - [x] **Guided Demo Hardening**: Replace interval timer with deterministic state machine.
  - [x] **Bidirectional Scroll**: Ensure `Positioning` and `Capabilities` sections animate on both scroll down and up.
  - [x] **Legacy Cleanup**: Completely remove the final "Run an epistemic audit" section.
  - [x] **Visual Consistency**: Enforce global glassmorphism constants and ease-in-out motion.
  - [x] **Micro-Polish**: Add step counters and explainability mode labels.

- [x] **Landing Page v1.1: Guided Epistemic Demo**
  - [x] **Cleanup**: Remove legacy duplicated CTA sections.
  - [x] **Animated Walkthrough**: Implement simulated cursor loop with claim-by-claim reveal.
  - [x] **Instructional Showcase**: Transform hover cards into self-teaching panels.
  - [x] **Synchronized Timeline**: React timeline nodes to the animated showcase focus.
  - [x] **Visual Polish**: Advanced glassmorphism, depth hierarchy, and micro-animations.
  - [x] **UI Refinement**: New instructional titles and "Guided" mode indicator.

- [x] **Landing Page v1.0**
  - [x] **Section 1: Hero**: Restrained headline, methodology CTA, refined animations.
  - [x] **Section 2: Capabilities**: Sequential fade-in cards for Atomic Claims, Evidence, Risk.
  - [x] **Section 3: Positioning**: Why hallucinations aren't binary.
  - [x] **Section 4: Showcase**: Static hover card and timeline demonstration.
  - [x] **Section 5: Serious Use**: Compact rows for research/policy/journalism.
  - [x] **Section 6: Boundaries**: Define what the engine is not (blunt text).
  - [x] **Section 7: Final CTA**: Calm center-aligned call to action.

- [x] **v1.6.4 Timeline Containment & Scaling**
  - [x] **Overflow Fix**: Replace `justify-between` with `overflow-x-auto` and `min-w-max`.
  - [x] **Scroll Into View**: Ensure keyboard-focused nodes scroll into view.
  - [x] **Accessibility**: Maintain ARIA labels and tab order.
  - [x] **Motion Hygiene**: Preserving scaling animations without layout shifts.

- [x] **v1.6.3 Audit Input Containment & Motion Polish**
  - [x] **Input Containment**: Wrap textarea in a scrollable fixed-height container to prevent spill.
  - [x] **Counter Redesign**: Move to dedicated footer bar with monospace formatting and color thresholds.
  - [x] **Motion Polish**: Add Framer Motion to char count updates, button hover/tap, and input focus bloom.
  - [x] **Visual Polish**: Ensure z-index safety and anchored layout.

- [x] **v1.6.2 Final Consistency & Accessibility**
  - [x] **Version Labels**: Update all display labels to "v1.6.2 Epistemic Interface".
  - [x] **Hover Card Dismissal**: Ensure Escape key reliably dismisses cards/previews.
  - [x] **Evidence Copy**: Refine uncertain snap copy to "No authoritative source could be confidently linked."
  - [x] **Glass Contrast**: Reduce background opacity by ~5% for better contrast.
  - [x] **Timeline Polish**: Verdict-aware focus rings and ARIA labels.
  - [x] **ARIA Hints**: Add roles and labels to highlights and cards.

- [x] **v1.6.1 Expansion & Polish**
  - [x] **Evidence Snapshot**: Fix semantic/visual contract (tint inheritance, copy update).
  - [x] **Glassmorphism Unification**: Eliminate nested white panels/nested blur layers.
  - [x] **Risk Bar Tone**: Soften colors to `bg-*-500/80`.
  - [x] **Header Icons**: Replace emojis with status dots/Lucide-style icons.

- [x] **v1.6.0 Expansion & Polish**
  - [x] **Unified UI (Hover Card)**: Glassmorphism tints, semantic evidence panels, authoritative citation chips.
  - [x] **Keyboard Navigation**: WCAG AA tab cycling, arrow navigation, escape to close, focus-triggered hover.
  - [x] **Timeline View**: Interactive node visualization of claims with scroll synchronization.
  - [x] **Explainability Mode**: Expert vs. Casual toggle for terminology and detail level.
  - [x] **Golden Dataset**: Implementation of `/golden/*.json` for regression testing.

- [x] **v1.5.1 Polish & Cleanup**
  - [x] **Risk Bar**: Simplify logic (one element, inline width).
  - [x] **Pointer Events**: Ensure robust behavior (auto/none).
  - [x] **Citation Tint**: Add verdict-aware border/glow to previews.
  - [x] **Integrity**: Verify animations and structure.
