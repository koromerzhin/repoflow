import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <p className="text-5xl font-bold text-slate-700">404</p>
      <h1 className="text-xl font-semibold text-slate-100">Page introuvable</h1>
      <p className="max-w-md text-sm text-slate-400">
        La page demandée n'existe pas ou a été déplacée.
      </p>
      <Link
        to="/"
        className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-500"
      >
        Retour au tableau de bord
      </Link>
    </div>
  )
}
