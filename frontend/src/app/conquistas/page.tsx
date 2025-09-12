'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import api, { clearTokens } from '@/utils/api'

interface Achievement {
  id: number
  name: string
  description: string
  earned: boolean
}

export default function ConquistasPage() {
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const fetchAchievements = async () => {
      const token = localStorage.getItem('access')
      if (!token) {
        router.push('/login')
        return
      }

      try {
        const res = await api.get<Achievement[]>('/game/achievements/', {
          headers: { Authorization: `Bearer ${token}` },
        })
        setAchievements(res.data)
      } catch {
        toast.error('Erro ao carregar conquistas. Faça login novamente.')
        clearTokens()
        router.push('/login')
      } finally {
        setLoading(false)
      }
    }

    fetchAchievements()
  }, [router])

  if (loading) {
    return <p className="p-8 text-center">Carregando conquistas...</p>
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">🏆 Minhas Conquistas</h2>
        <button
          onClick={() => router.push('/fases')}
          className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded"
        >
          Voltar às Fases
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {achievements.map((ach) => (
          <div
            key={ach.id}
            className={`p-6 rounded-lg shadow-md border transition ${
              ach.earned
                ? 'bg-green-100 border-green-400'
                : 'bg-gray-100 border-gray-300'
            }`}
          >
            <h3
              className={`text-lg font-bold mb-2 ${
                ach.earned ? 'text-green-800' : 'text-gray-600'
              }`}
            >
              {ach.name}
            </h3>
            {ach.earned ? (
              <p className="text-gray-800">{ach.description}</p>
            ) : (
              <p className="italic text-gray-500">Não conquistada ainda</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
