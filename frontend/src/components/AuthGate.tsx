import { KeyRound } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import { useAuth } from '@/hooks/useAuth'

export function AuthGate({ children }: { children: ReactNode }) {
  const { t } = useTranslation()
  const { unauthorized, login } = useAuth()
  const [token, setTokenValue] = useState('')

  if (!unauthorized) {
    return <>{children}</>
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!token.trim()) {
      return
    }
    login(token)
    window.location.reload()
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-xl border border-slate-800 bg-slate-900/40 p-6"
      >
        <div className="mb-4 flex items-center gap-2 text-sky-300">
          <KeyRound className="size-5" aria-hidden />
          <h1 className="text-lg font-semibold text-slate-100">{t('auth.title')}</h1>
        </div>
        <p className="mb-4 text-sm text-slate-400">{t('auth.description')}</p>
        <label className="block text-sm text-slate-300">
          <span className="mb-1 block">{t('auth.tokenLabel')}</span>
          <input
            type="password"
            autoFocus
            autoComplete="off"
            value={token}
            onChange={(event) => setTokenValue(event.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-sky-500 focus:outline-none"
          />
        </label>
        <button
          type="submit"
          className="mt-4 w-full rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-500"
        >
          {t('auth.submit')}
        </button>
      </form>
    </main>
  )
}
