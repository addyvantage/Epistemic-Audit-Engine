"use client"
import { useRouter } from "next/navigation"

export function LogoButton() {
    const router = useRouter()

    return (
        <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 focus:outline-none group"
            aria-label="Epistemic Audit Home"
        >
            <div className="w-8 h-8 rounded-md bg-slate-900 text-white flex items-center justify-center font-mono text-xs font-bold shadow-sm group-hover:bg-slate-800 transition-colors">
                EA
            </div>
            <span className="font-semibold text-slate-900 tracking-tight group-hover:text-slate-700 transition-colors">
                Epistemic Audit
            </span>
        </button>
    )
}
