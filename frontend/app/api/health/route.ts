import { NextResponse } from 'next/server'
import { fetchWithRetry } from '@/lib/fetch-retry'

export async function GET() {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'
    const backendUrl = `${apiBase}/health`

    try {
        const res = await fetchWithRetry(backendUrl, { method: 'GET' }, 3, 250)
        const raw = await res.text()

        if (!res.ok) {
            return NextResponse.json(
                { status: 'error', pipeline_ready: false, detail: raw || 'Health check failed' },
                { status: res.status }
            )
        }

        try {
            const parsed = JSON.parse(raw)
            const hasStatus = typeof parsed?.status === 'string'
            const pipelineReady = parsed?.pipeline_ready
            const hasBooleanishPipeline =
                typeof pipelineReady === 'boolean' ||
                pipelineReady === 0 ||
                pipelineReady === 1 ||
                pipelineReady === 'true' ||
                pipelineReady === 'false'

            if (!hasStatus || !hasBooleanishPipeline) {
                return NextResponse.json(
                    { status: 'error', pipeline_ready: false, detail: 'Unexpected health payload' },
                    { status: 502 }
                )
            }
            return NextResponse.json(parsed)
        } catch {
            return NextResponse.json({ status: 'error', pipeline_ready: false }, { status: 502 })
        }
    } catch (error) {
        return NextResponse.json(
            { status: 'error', pipeline_ready: false, detail: 'Backend not reachable' },
            { status: 503 }
        )
    }
}
