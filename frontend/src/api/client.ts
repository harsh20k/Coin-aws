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
  // #region agent log
  const _startTime = Date.now()
  // #endregion
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
  // #region agent log
  fetch('http://127.0.0.1:7244/ingest/ca6e21a8-b6aa-467e-976e-d9f77506770e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ef78fc'},body:JSON.stringify({sessionId:'ef78fc',location:'client.ts:request:before-fetch',message:'Starting API request',data:{method,path,url},timestamp:Date.now(),hypothesisId:'H-F/H-H'})}).catch(()=>{});
  // #endregion
  const res = await fetch(url, opts)
  // #region agent log
  const _duration = Date.now() - _startTime
  fetch('http://127.0.0.1:7244/ingest/ca6e21a8-b6aa-467e-976e-d9f77506770e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ef78fc'},body:JSON.stringify({sessionId:'ef78fc',location:'client.ts:request:after-fetch',message:'API response received',data:{method,path,status:res.status,ok:res.ok,duration_ms:_duration},timestamp:Date.now(),hypothesisId:'H-F/H-H'})}).catch(()=>{});
  // #endregion
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
  // #region agent log
  fetch('http://127.0.0.1:7244/ingest/ca6e21a8-b6aa-467e-976e-d9f77506770e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ef78fc'},body:JSON.stringify({sessionId:'ef78fc',location:'client.ts:request:error',message:'API request failed',data:{method,path,status:res.status,detail},timestamp:Date.now(),hypothesisId:'H-I'})}).catch(()=>{});
  // #endregion
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
