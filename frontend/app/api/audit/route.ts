import { NextResponse } from 'next/server'

export async function POST(request: Request) {
    try {
        const body = await request.json()
        // Proxy to Python Backend
        // Backend runs on port 8000
        // Endpoint: /audit (presumed from app.py)

        // NOTE: In production, use ENV var. 
        // Assuming backend endpoint is /api/audit or similar.
        // Checking app.py in previous interactions, it defines `app = FastAPI()`. 
        // Usually routes are `/`.
        // Let's assume there is a generic POST endpoint.
        // I need to know the backend route. Step 1155 "uvicorn app:app"

        const backendUrl = 'http://127.0.0.1:8000/audit'

        const res = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        })

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
