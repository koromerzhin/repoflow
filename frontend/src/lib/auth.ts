const TOKEN_KEY = 'repoflow-api-token'

const listeners = new Set<() => void>()

let token: string | null = readToken()
let unauthorized = false

function readToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function emit(): void {
  listeners.forEach((listener) => listener())
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getToken(): string | null {
  return token
}

export function getUnauthorized(): boolean {
  return unauthorized
}

export function setToken(value: string | null): void {
  const normalized = value && value.trim().length > 0 ? value.trim() : null
  token = normalized
  unauthorized = false
  try {
    if (normalized) {
      sessionStorage.setItem(TOKEN_KEY, normalized)
    } else {
      sessionStorage.removeItem(TOKEN_KEY)
    }
  } catch {
    // Stockage indisponible (mode privé) : le jeton reste en mémoire.
  }
  emit()
}

export function markUnauthorized(): void {
  if (!unauthorized) {
    unauthorized = true
    emit()
  }
}

export function resetAuth(): void {
  token = null
  unauthorized = false
  try {
    sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // Ignoré : rien à nettoyer.
  }
  emit()
}
