import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '@/services/apiClient'

export interface AsyncState<T> {
  data: T | null
  error: ApiError | null
  loading: boolean
  reload: () => void
}

/**
 * Petit hook d'exécution asynchrone avec états de chargement, d'erreur et
 * possibilité de rechargement. Le signal d'abandon est propagé pour annuler
 * les requêtes obsolètes.
 */
export function useAsync<T>(
  factory: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[] = [],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(true)
  const [nonce, setNonce] = useState(0)

  const reload = useCallback(() => setNonce((value) => value + 1), [])

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    /* eslint-disable react-hooks/set-state-in-effect -- Hook de chargement :
       la synchronisation de l'état local avec la requête est intentionnelle. */
    setLoading(true)
    setError(null)
    /* eslint-enable react-hooks/set-state-in-effect */

    factory(controller.signal)
      .then((result) => {
        if (!active) {
          return
        }
        setData(result)
        setLoading(false)
      })
      .catch((cause: unknown) => {
        if (!active || controller.signal.aborted) {
          return
        }
        setError(
          cause instanceof ApiError
            ? cause
            : new ApiError('Une erreur inattendue est survenue.', 0, 'unknown'),
        )
        setLoading(false)
      })

    return () => {
      active = false
      controller.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps])

  return { data, error, loading, reload }
}
