export function normalizeText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

export function matchesQuery(value: string, query: string): boolean {
  const normalized = normalizeText(query.trim())
  if (!normalized) {
    return true
  }
  return normalizeText(value).includes(normalized)
}