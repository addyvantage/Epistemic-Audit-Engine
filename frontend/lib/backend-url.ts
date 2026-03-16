const LOCAL_BACKEND_URL = 'http://127.0.0.1:8000'

const BACKEND_URL_ENV_KEYS = [
    'BACKEND_URL',
    'NEXT_PUBLIC_API_URL',
    'API_BASE_URL',
    'NEXT_PUBLIC_API_BASE',
] as const

function normalizeBackendUrl(url: string): string {
    return url.trim().replace(/\/+$/, '')
}

export type BackendUrlConfig = {
    url: string | null
    source: string | null
}

export function getBackendBaseUrlConfig(): BackendUrlConfig {
    for (const key of BACKEND_URL_ENV_KEYS) {
        const value = process.env[key]
        if (value && value.trim()) {
            return {
                url: normalizeBackendUrl(value),
                source: key,
            }
        }
    }

    if (process.env.NODE_ENV !== 'production') {
        return {
            url: LOCAL_BACKEND_URL,
            source: 'dev-default',
        }
    }

    return {
        url: null,
        source: null,
    }
}

export function getBackendBaseUrl(): string | null {
    return getBackendBaseUrlConfig().url
}
