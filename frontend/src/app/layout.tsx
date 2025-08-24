import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata = {
  title: 'Meu App',
  description: 'App estilo Duolingo',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-br">
      <body className="bg-gray-100 text-gray-900 min-h-screen flex flex-col">
        <header className="bg-green-600 text-white p-4 shadow">
          <div className="container mx-auto flex justify-between items-center">
            <h1 className="text-xl font-bold">Meu App</h1>
          </div>
        </header>
        <main className="flex-grow container mx-auto p-6">
          {children}
        </main>
        <footer className="bg-gray-200 text-center py-4 text-sm text-gray-600">
          © {new Date().getFullYear()} Meu App - Todos os direitos reservados
        </footer>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
