'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { clearTokens } from '@/utils/api'

export function withAuth(Component: React.ComponentType) {
  return function Authenticated(props: any) {
    const router = useRouter()

    useEffect(() => {
      if (typeof window !== 'undefined') {
        const access = localStorage.getItem('access')
        const refresh = localStorage.getItem('refresh')

        // Se não tiver tokens, redireciona
        if (!access || !refresh) {
          clearTokens()
          router.push('/login')
        }
      }
    }, [router])

    return <Component {...props} />
  }
}
