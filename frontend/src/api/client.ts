import { fetchAuthSession } from 'aws-amplify/auth'

const baseUrl = import.meta.env.VITE_API_URL ?? '/api'

async function getToken(): Promise<string> {
  const session = await fetchAuthSession()
  const token = session.tokens?.idToken?.toString()
  if (!token) throw new Error('No token')
  return token
}

export async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const token = await getToken()
  const url = path.startsWith('http') ? path : `${baseUrl}${path}`
  const opts: RequestInit = {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(url, opts)
  if (res.status === 401) {
    const { signOut } = await import('aws-amplify/auth')
    await signOut()
    window.location.href = '/'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const text = await res.text()
    let detail: string
    try {
      const j = JSON.parse(text)
      detail = j.detail ?? text
    } catch {
      detail = text || res.statusText
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
  delete: (path: string) => request<void>('DELETE', path),
}
