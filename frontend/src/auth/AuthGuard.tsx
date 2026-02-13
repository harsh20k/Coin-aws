import { Authenticator } from '@aws-amplify/ui-react'
import '@aws-amplify/ui-react/styles.css'
import { ReactNode, useEffect } from 'react'
import { api } from '../api/client'
import { isAuthConfigured } from './AmplifyConfig'

async function registerUser(): Promise<void> {
  await api.put('/users/me', {})
}

function Inner({ children }: { children: ReactNode }) {
  useEffect(() => {
    registerUser().catch(() => {})
  }, [])
  return <>{children}</>
}

export function AuthGuard({ children }: { children: ReactNode }) {
  if (!isAuthConfigured) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p>Auth not configured. Set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_APP_CLIENT_ID in .env</p>
        <p><a href="https://github.com/aws-amplify/amplify-js">See Amplify docs</a></p>
      </div>
    )
  }
  return (
    <Authenticator>
      {() => <Inner>{children}</Inner>}
    </Authenticator>
  )
}
