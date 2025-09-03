'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import api, { clearTokens } from '@/utils/api'

interface Phase {
  id: number
  phase_number: number
  is_completed: boolean
}

interface Profile {
  crystals: number
  energy: number
}

export default function FasesPage() {
  const [fases, setFases] = useState<Phase[]>([])
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Fetch das fases e perfil
  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('access')
      if (!token) {
        router.push('/login')
        return
      }

      try {
        const [fasesRes, profileRes] = await Promise.all([
          api.get('/game/phases/', { headers: { Authorization: `Bearer ${token}` } }),
          api.get('/game/profile/', { headers: { Authorization: `Bearer ${token}` } }),
        ])
        setFases(fasesRes.data)
        setProfile(profileRes.data)
      } catch {
        toast.error('Erro ao carregar dados. Faça login novamente.')
        clearTokens()
        router.push('/login')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [router])

  if (loading) return <p className="p-8 text-center">Carregando...</p>

  const firstIncompleteIndex = fases.findIndex((f) => !f.is_completed)
  const unlockedIndex = firstIncompleteIndex === -1 ? fases.length - 1 : firstIncompleteIndex

  const handleClick = async (fase: Phase, index: number) => {
    if (index > unlockedIndex) {
      toast('Esta fase ainda não está desbloqueada.')
      return
    }

    const token = localStorage.getItem('access')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      // 🔹 Chama a API para gastar energia e entrar
      // await api.post(`/game/phases/${fase.phase_number}/enter/`, {}, {
      //   headers: { Authorization: `Bearer ${token}` },
      // })

      // Atualiza o perfil (energia/cistais)
      const profileRes = await api.get('/game/profile/', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setProfile(profileRes.data)

      // Redireciona para a fase
      router.push(`/fases/${fase.phase_number}`)
    } catch (err: unknown) {
      if (err instanceof Error) {
        toast.error(err.message)
      } else {
        toast.error('Erro ao entrar na fase.')
      }
    }
  }

  const handleLogout = () => {
    clearTokens()
    router.push('/login')
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">Fases</h2>
          {profile && (
            <span className="bg-yellow-400 text-gray-900 font-semibold px-3 py-1 rounded">
              💎 Cristais: {profile?.crystals || 0} | ⚡ Energia: {profile?.energy || 0}
            </span>
          )}
        </div>
        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 rounded"
        >
          Sair
        </button>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {fases.map((fase, index) => {
          const isUnlocked = index <= unlockedIndex
          return (
            <button
              key={fase.id}
              onClick={() => handleClick(fase, index)}
              className={`py-4 rounded-lg font-semibold transition-colors ${
                isUnlocked
                  ? fase.is_completed
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-300 text-gray-600 cursor-not-allowed'
              }`}
            >
              Fase {fase.phase_number}
              {fase.is_completed && ' ✅'}
            </button>
          )
        })}
      </div>
    </div>
  )
}