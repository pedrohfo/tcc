'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export function withAuth(Component: React.ComponentType) {
  return function Authenticated(props: any) {
    const router = useRouter()

    useEffect(() => {
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token')
        if (!token) router.push('/')
      }
    }, [router])

    return <Component {...props} />
  }
}
