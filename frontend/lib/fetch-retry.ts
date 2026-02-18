function isRetryableNetworkError(err: any): boolean {
    return (
        err?.cause?.code === 'ECONNREFUSED' ||
        err?.message?.includes?.('fetch failed') ||
        err?.message === 'Service Unavailable'
    )
}

function jitteredDelayMs(baseMs: number): number {
    const capped = Math.min(Math.max(0, baseMs), 2000)
    const jitterFactor = 1 + (Math.random() * 0.3 - 0.15)
    return Math.max(0, Math.round(capped * jitterFactor))
}

export async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 5, backoff = 300): Promise<Response> {
    let attempt = 0
    let delayMs = Math.max(0, backoff)
    let lastError: any = null

    while (attempt <= retries) {
        try {
            const res = await fetch(url, options)
            if (res.status !== 503) {
                return res
            }
            lastError = new Error('Service Unavailable')
        } catch (err: any) {
            if (!isRetryableNetworkError(err)) {
                throw err
            }
            lastError = err
        }

        if (attempt === retries) {
            break
        }

        await new Promise((resolve) => setTimeout(resolve, jitteredDelayMs(delayMs)))
        delayMs = Math.min(Math.round(delayMs * 1.5), 2000)
        attempt += 1
    }

    throw lastError || new Error('fetchWithRetry failed')
}
