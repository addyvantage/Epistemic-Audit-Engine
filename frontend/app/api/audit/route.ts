import { NextResponse } from 'next/server'
import { fetchWithRetry } from '@/lib/fetch-retry'
import { getBackendBaseUrlConfig } from '@/lib/backend-url'

function errorMessage(error: unknown): string {
    if (error instanceof Error && error.message) return error.message
    return 'Backend request failed'
}

export async function POST(request: Request) {
    try {
        const body = await request.json()
        const { url: apiBase } = getBackendBaseUrlConfig()
        if (!apiBase) {
            return NextResponse.json(
                { status: 'unavailable', backendUrl: null, error: 'Backend URL not configured' },
                { status: 503 }
            )
        }
        const backendUrl = `${apiBase}/audit`

        const res = await fetchWithRetry(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        }, 3, 250)

        if (!res.ok) {
            const err = await res.text()
            return NextResponse.json(
                { status: 'error', backendUrl, error: err || `Audit request failed with ${res.status}` },
                { status: res.status }
            )
        }

        const data = await res.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error('Audit proxy failed:', error)
        return NextResponse.json(
            { status: 'unavailable', error: errorMessage(error) },
            { status: 503 }
        )
    }
}
