"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api, { saveTokens } from "@/utils/api";
import toast from "react-hot-toast";
import axios from "axios";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post("/auth/login/", { email, password });
      // Espera { access, refresh }
      if (res.data?.access && res.data?.refresh) {
        const { access, refresh } = res.data
        saveTokens(res.data.access, res.data.refresh);
        // salvar cookie para server-side
        document.cookie = `access=${access}; path=/; max-age=3600`
        document.cookie = `refresh=${refresh}; path=/; max-age=604800`
        toast.success("Login realizado!");
        router.push("/fases");
      } else {
        toast.error("Resposta do servidor inválida.");
      }
    } catch (err: unknown) {
      // Tenta extrair erros DRF
      if (axios.isAxiosError(err)) {
        const detail =
          err?.response?.data?.detail ||
          err?.response?.data?.non_field_errors?.[0] ||
          "Credenciais inválidas.";
        toast.error(String(detail), { duration: 7000 });
      } else {
        toast.error("Erro de Login!")
      }
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = email.trim() && password.trim() && !loading;

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 p-4">
      <form
        onSubmit={handleLogin}
        className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md"
      >
        <h1 className="text-3xl font-extrabold mb-6 text-gray-900">Entrar</h1>

        <label className="block mb-2 font-medium text-gray-900">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Digite seu email"
          className="w-full p-3 border border-gray-300 rounded-lg mb-4 text-gray-900 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          autoComplete="email"
          required
        />

        <label className="block mb-2 font-medium text-gray-900">Senha</label>
        <div className="relative mb-6">
          <input
            type={showPw ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Digite sua senha"
            className="w-full p-3 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 pr-12"
            autoComplete="current-password"
            required
          />
          <button
            type="button"
            onClick={() => setShowPw((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-800 hover:underline"
            aria-label={showPw ? "Ocultar senha" : "Mostrar senha"}
          >
            {showPw ? "Ocultar" : "Mostrar"}
          </button>
        </div>

        <button
          type="submit"
          disabled={!canSubmit}
          className={`w-full py-3 rounded-lg transition font-semibold ${
            canSubmit
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "bg-blue-300 text-white cursor-not-allowed"
          }`}
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>

        <p className="mt-4 text-center text-gray-900">
          Não tem conta?{" "}
          <a href="/signup" className="text-blue-700 font-semibold hover:underline">
            Criar conta
          </a>
        </p>
      </form>
    </div>
  );
}
