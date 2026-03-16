type FetchWithRetryRequestInit = RequestInit & {
    timeoutMs?: number
}

function isRetryableNetworkError(err: any): boolean {
    return (
        err?.cause?.code === 'ECONNREFUSED' ||
        err?.name === 'AbortError' ||
        err?.message?.includes?.('timed out') ||
        err?.message?.includes?.('fetch failed') ||
        err?.message === 'Service Unavailable'
    )
}

function jitteredDelayMs(baseMs: number): number {
    const capped = Math.min(Math.max(0, baseMs), 2000)
    const jitterFactor = 1 + (Math.random() * 0.3 - 0.15)
    return Math.max(0, Math.round(capped * jitterFactor))
}

function withRequestTimeout(options: FetchWithRetryRequestInit): {
    fetchOptions: RequestInit
    cleanup: () => void
} {
    const { timeoutMs, signal, ...fetchOptions } = options
    if (!timeoutMs || timeoutMs <= 0) {
        return {
            fetchOptions: { ...fetchOptions, signal },
            cleanup: () => undefined,
        }
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
        controller.abort(new Error(`Request timed out after ${timeoutMs}ms`))
    }, timeoutMs)

    const abortFromParent = () => {
        controller.abort(signal?.reason)
    }

    if (signal) {
        if (signal.aborted) {
            abortFromParent()
        } else {
            signal.addEventListener('abort', abortFromParent, { once: true })
        }
    }

    return {
        fetchOptions: { ...fetchOptions, signal: controller.signal },
        cleanup: () => {
            clearTimeout(timeoutId)
            signal?.removeEventListener?.('abort', abortFromParent)
        },
    }
}

export async function fetchWithRetry(url: string, options: FetchWithRetryRequestInit = {}, retries = 5, backoff = 300): Promise<Response> {
    let attempt = 0
    let delayMs = Math.max(0, backoff)
    let lastError: any = null

    while (attempt <= retries) {
        const { fetchOptions, cleanup } = withRequestTimeout(options)
        try {
            const res = await fetch(url, fetchOptions)
            if (res.status !== 503) {
                cleanup()
                return res
            }
            lastError = new Error('Service Unavailable')
        } catch (err: any) {
            if (!isRetryableNetworkError(err)) {
                cleanup()
                throw err
            }
            lastError = err
        } finally {
            cleanup()
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
