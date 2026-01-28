export async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 5, backoff = 300): Promise<Response> {
    try {
        const res = await fetch(url, options)

        // If 503 Service Unavailable (Backend loading), retry
        if (res.status === 503) {
            throw new Error('Service Unavailable')
        }

        return res
    } catch (err: any) {
        if (retries <= 0) throw err;

        // Retry on connection refused (FetchError/TypeError) or 503
        const isNetworkError = err.cause?.code === 'ECONNREFUSED' || err.message.includes('fetch failed') || err.message === 'Service Unavailable';

        if (isNetworkError) {
            console.log(`[FetchRetry] Retrying ${url} (${retries} attempts left) in ${backoff}ms...`);
            await new Promise(resolve => setTimeout(resolve, backoff));
            return fetchWithRetry(url, options, retries - 1, backoff * 1.5); // Exponential backoff
        }

        throw err;
    }
}
