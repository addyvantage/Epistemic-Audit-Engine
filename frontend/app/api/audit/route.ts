import { NextResponse } from 'next/server'
import { fetchWithRetry } from '@/lib/fetch-retry';

export async function POST(request: Request) {
    try {
        const body = await request.json()
        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
        const backendUrl = `${apiBase}/audit`;

        const res = await fetchWithRetry(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        }, 10, 500) // Aggressive retry: 10 attempts, starting at 500ms

        if (!res.ok) {
            const err = await res.text()
            return NextResponse.json({ error: err }, { status: res.status })
        }

        const data = await res.json()
        return NextResponse.json(data)

    } catch (e) {
        console.error(e)
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
    }
}
