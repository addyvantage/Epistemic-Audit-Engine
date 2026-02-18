"use client"

import React, { useEffect, useState } from "react"
import { ClaimInspectorPanel } from "@/components/ClaimInspectorPanel"

type Props = {
    claim: any | null
    open: boolean
    onClose: () => void
}

export function InspectorOverlay({ claim, open, onClose }: Props) {
    const [cursor, setCursor] = useState({ x: 0, y: 0 })
    const [cursorVisible, setCursorVisible] = useState(false)

    useEffect(() => {
        if (!open) return

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                onClose()
            }
        }

        window.addEventListener("keydown", onKeyDown)
        return () => window.removeEventListener("keydown", onKeyDown)
    }, [open, onClose])

    if (!open) return null

    return (
        <div className="fixed inset-0 z-40" aria-hidden={!open}>
            <div
                className="absolute inset-0 cursor-none"
                onMouseMove={(event) => {
                    setCursor({ x: event.clientX, y: event.clientY })
                    setCursorVisible(true)
                }}
                onMouseLeave={() => setCursorVisible(false)}
                onWheel={(event) => {
                    const scrollContainer = document.getElementById("source-document-scroll")
                    if (scrollContainer) {
                        scrollContainer.scrollTop += event.deltaY
                        event.preventDefault()
                    }
                }}
                onClick={onClose}
            />

            {cursorVisible ? (
                <div
                    className="pointer-events-none fixed z-50"
                    style={{ left: cursor.x, top: cursor.y, transform: "translate(-50%, -50%)" }}
                >
                    <div className="h-9 w-9 rounded-full border border-black bg-white/95 shadow-lg flex items-center justify-center">
                        <svg className="h-3.5 w-3.5 text-black" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M6 6L18 18M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </div>
                </div>
            ) : null}

            <div className="absolute inset-y-0 right-0 z-50 w-full max-w-[430px] p-3 sm:p-4 pointer-events-none cursor-default">
                <div className="h-full pointer-events-auto">
                    <ClaimInspectorPanel claim={claim} onClose={onClose} className="h-full" />
                </div>
            </div>
        </div>
    )
}
