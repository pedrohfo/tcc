'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import api, { clearTokens } from '@/utils/api'
import toast from 'react-hot-toast'
import axios from 'axios'

interface Alternative {
  id: number
  alternative_text: string
}

interface Phase {
  id: number
  phase_number: number
  question: {
    id: number
    question_text: string
    alternatives: Alternative[]
    image?: string
  }
  is_completed: boolean
}

interface Profile {
  crystals: number
}

export default function PhasePage() {
  const { phase_number } = useParams()
  const router = useRouter()

  const [phase, setPhase] = useState<Phase | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedAlt, setSelectedAlt] = useState<number | null>(null)
  const [showHint, setShowHint] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('access')
      if (!token) {
        router.push('/login')
        return
      }

      try {
        await api.post(`/game/phases/${phase_number}/enter/`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const [phaseRes, profileRes] = await Promise.all([
          api.get(`/game/phases/${phase_number}/`, { headers: { Authorization: `Bearer ${token}` } }),
          api.get('/game/profile/', { headers: { Authorization: `Bearer ${token}` } }),
        ])
        setPhase(phaseRes.data)
        setProfile(profileRes.data)
      } catch (err: unknown) {
          if (axios.isAxiosError(err)) {
            if (err.response?.status === 403) {
              toast.error('Esta fase ainda não está desbloqueada.')
            } else if (err.response?.status === 401) {
              toast.error('Sessão expirada. Faça login novamente.')
              clearTokens()
              router.push('/login')
            } else {
              toast.error('Erro ao carregar fase.')
            }
          } else {
            // Qualquer outro erro
            toast.error('Erro desconhecido ao carregar fase.')
          }
        } finally {
      setLoading(false)
    }
  }

    fetchData()
  }, [phase_number, router])

  if (loading) return <p className="p-8 text-center">Carregando...</p>
  if (!phase || !profile) return <p className="p-8 text-center">Fase não desbloqueada.</p>

  const handleSubmit = async () => {
    if (!selectedAlt) {
      toast('Escolha uma alternativa.')
      return
    }

    setSubmitting(true)
    try {
      const token = localStorage.getItem('access')
      const res = await api.post(
        `/game/phases/${phase.phase_number}/answer/`,
        { alternative_id: selectedAlt },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      if (res.data.correct) {
        toast.success(`Correto! Cristais: ${res.data.crystals}`)
        setProfile((p) => p && { ...p, crystals: res.data.crystals })
        setPhase({ ...phase, is_completed: true })
      } else {
        toast.error('Resposta incorreta.')
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err))
        toast.error(err?.response?.data?.detail || 'Erro ao enviar resposta.')
      else
        toast.error('Erro ao enviar resposta.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRequestHint = async () => {
    if (!profile || profile.crystals < 30) {
      toast.error('Cristais insuficientes para pedir dica.')
      return
    }

    setSubmitting(true)
    try {
      const token = localStorage.getItem('access')

      // Aqui você chamaria seu endpoint que retorna a dica do ChatGPT
      const hintRes = await api.post(
        `/game/hint/${phase.phase_number}/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setShowHint(hintRes.data.hint)
      setProfile({ ...profile, crystals: profile.crystals - 30 })
      toast.success('Dica liberada! 30 cristais foram consumidos.')
    } catch {
      toast.error('Erro ao gerar dica.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Fase {phase.phase_number}</h2>
        <span className="bg-yellow-400 text-gray-900 font-semibold px-3 py-1 rounded">
          💎 {profile.crystals}
        </span>
      </div>

      <div className="mb-6 p-6 bg-white rounded shadow">

        {phase.question.image && (
          <img
            src={phase.question.image}
            alt="Imagem da questão"
            className="mb-4 rounded max-h-64 object-contain mx-auto"
          />
        )}
        <p className="mb-4 text-gray-900">{phase.question.question_text}</p>

        <div className="grid gap-4">
          {phase.question.alternatives.map((alt) => (
            <button
              key={alt.id}
              onClick={() => setSelectedAlt(alt.id)}
              className={`p-3 rounded border font-medium text-left transition-colors text-gray-900 ${
                selectedAlt === alt.id ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {alt.alternative_text}
            </button>
          ))}
        </div>

        <div className="mt-4 flex gap-4">
          <button
            onClick={handleSubmit}
            disabled={submitting || phase.is_completed}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-semibold"
          >
            Enviar resposta
          </button>

          {!phase.is_completed && (
            <button
              onClick={handleRequestHint}
              disabled={submitting || profile.crystals < 30}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded font-semibold"
            >
              Gastar 30 cristais para dica
            </button>
          )}
        </div>

        {showHint && (
          <div className="mt-4 p-4 bg-blue-50 text-gray-900 rounded">
            <strong>Dica:</strong> {showHint}
          </div>
        )}
      </div>

      <button
        onClick={() => router.push('/fases')}
        className="mt-6 bg-gray-400 hover:bg-gray-500 text-white px-4 py-2 rounded font-semibold"
      >
        Voltar para Fases
      </button>
    </div>
  )
}
