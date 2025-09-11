'use client'

import { useEffect, useState } from 'react'
import api from '@/utils/api'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

interface UserRank {
  user__username: string
  correct_answers: number
  wrong_answers: number
  score_calc: number
}

interface CurrentUserRank extends UserRank {
  rank: number
}

export default function RankingPage() {
  const [topUsers, setTopUsers] = useState<UserRank[]>([])
  const [currentUser, setCurrentUser] = useState<CurrentUserRank | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const fetchRanking = async () => {
      const token = localStorage.getItem('access')
      if (!token) {
        router.push('/login')
        return
      }

      try {
        const res = await api.get('/game/ranking/', {
          headers: { Authorization: `Bearer ${token}` },
        })

        setTopUsers(res.data.top_users || [])
        setCurrentUser(res.data.current_user || null)
      } catch (err) {
        toast.error('Erro ao carregar ranking.')
      } finally {
        setLoading(false)
      }
    }

    fetchRanking()
  }, [router])

  if (loading) return <p className="p-8 text-center">Carregando ranking...</p>

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">🏆 Ranking</h2>

      {/* Top 10 */}
      <div className="mb-8">
        {topUsers.length === 0 ? (
          <p>Nenhum dado disponível.</p>
        ) : (
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-900">
                <th className="border px-4 py-2">Posição</th>
                <th className="border px-4 py-2">Usuário</th>
                <th className="border px-4 py-2">Acertos</th>
                <th className="border px-4 py-2">Erros</th>
                <th className="border px-4 py-2">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {topUsers.map((u, idx) => (
                <tr key={idx}>
                  <td className="border px-4 py-2 text-center">{idx + 1}</td>
                  <td className="border px-4 py-2">{u.user__username}</td>
                  <td className="border px-4 py-2 text-center">{u.correct_answers}</td>
                  <td className="border px-4 py-2 text-center">{u.wrong_answers}</td>
                  <td className="border px-4 py-2 text-center">{u.score_calc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Usuário autenticado */}
      {currentUser && (
        <div className="bg-blue-800 p-4 rounded">
          <p className="font-bold">
            Sua posição no ranking: #{currentUser.rank}
          </p>
          <p>
            Acertos: {currentUser.correct_answers} | Erros:{' '}
            {currentUser.wrong_answers} | Saldo: {currentUser.score_calc}
          </p>
        </div>
      )}
    </div>
  )
}
