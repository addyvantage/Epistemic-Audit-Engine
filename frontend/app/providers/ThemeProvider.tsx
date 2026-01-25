"use client"
import { createContext, useContext, useEffect, useState, ReactNode } from "react"

type Theme = "light" | "dark"
type ThemeContextType = {
    theme: Theme
    toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<Theme>("light")

    // Sync with system/local storage on mount
    useEffect(() => {
        const stored = localStorage.getItem("theme") as Theme | null
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches

        const shouldBeDark = stored === "dark" || (!stored && prefersDark)

        if (shouldBeDark) {
            document.documentElement.classList.add("dark")
            setTheme("dark")
        } else {
            document.documentElement.classList.remove("dark")
            setTheme("light")
        }
    }, [])

    const toggleTheme = () => {
        const isDark = document.documentElement.classList.contains("dark")
        if (isDark) {
            document.documentElement.classList.remove("dark")
            localStorage.setItem("theme", "light")
            setTheme("light")
        } else {
            document.documentElement.classList.add("dark")
            localStorage.setItem("theme", "dark")
            setTheme("dark")
        }
    }

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    const ctx = useContext(ThemeContext)
    if (!ctx) throw new Error("useTheme must be used inside ThemeProvider")
    return ctx
}
