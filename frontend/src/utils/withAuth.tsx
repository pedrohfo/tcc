'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { clearTokens } from '@/utils/api'

export function withAuth<T extends Record<string, unknown>>(Component: React.ComponentType<T>) {
  return function Authenticated(props: T) {
    const router = useRouter()

    useEffect(() => {
      if (typeof window === 'undefined') return

      const access = localStorage.getItem('access')
      const refresh = localStorage.getItem('refresh')

      if (!access || !refresh) {
        clearTokens()
        router.push('/login')
      }
    }, [router])

    return <Component {...props} />
  }
}
