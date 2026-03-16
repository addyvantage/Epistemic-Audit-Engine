import { NextResponse } from 'next/server'
import { fetchWithRetry } from '@/lib/fetch-retry'
import { getBackendBaseUrlConfig } from '@/lib/backend-url'

const HEALTH_TIMEOUT_MS = 1500

function parseBooleanish(value: unknown): boolean | null {
    if (typeof value === 'boolean') return value
    if (value === 1 || value === '1' || value === 'true') return true
    if (value === 0 || value === '0' || value === 'false') return false
    return null
}

function errorMessage(error: unknown): string {
    if (error instanceof Error && error.message) return error.message
    return 'Backend not reachable'
}

export async function GET() {
    const { url: apiBase, source } = getBackendBaseUrlConfig()
    if (!apiBase) {
        return NextResponse.json(
            {
                status: 'unavailable',
                pipeline_ready: false,
                backendUrl: null,
                error: 'Backend URL not configured',
            },
            { status: 503 }
        )
    }
    const backendUrl = `${apiBase}/health`

    try {
        const res = await fetchWithRetry(
            backendUrl,
            {
                method: 'GET',
                cache: 'no-store',
                timeoutMs: HEALTH_TIMEOUT_MS,
            },
            0,
            0
        )
        const raw = await res.text()

        if (!res.ok) {
            return NextResponse.json(
                {
                    status: 'unavailable',
                    pipeline_ready: false,
                    backendUrl,
                    error: raw || `Backend health returned ${res.status}`,
                },
                { status: 503 }
            )
        }

        try {
            const parsed = JSON.parse(raw)
            const hasStatus = typeof parsed?.status === 'string'
            const pipelineReady = parseBooleanish(parsed?.pipeline_ready)
            const normalizedPipelineReady = pipelineReady ?? parsed?.status === 'ok'

            if (!hasStatus) {
                return NextResponse.json(
                    {
                        status: 'unavailable',
                        pipeline_ready: false,
                        backendUrl,
                        error: 'Unexpected health payload',
                    },
                    { status: 502 }
                )
            }

            return NextResponse.json({
                ...parsed,
                pipeline_ready: normalizedPipelineReady,
                backendUrl,
                backendUrlSource: source,
            })
        } catch {
            return NextResponse.json(
                {
                    status: 'unavailable',
                    pipeline_ready: false,
                    backendUrl,
                    error: 'Health endpoint returned non-JSON response',
                },
                { status: 502 }
            )
        }
    } catch (error) {
        return NextResponse.json(
            {
                status: 'unavailable',
                pipeline_ready: false,
                backendUrl,
                error: errorMessage(error),
            },
            { status: 503 }
        )
    }
}
