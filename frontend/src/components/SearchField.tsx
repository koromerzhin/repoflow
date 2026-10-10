import { Search } from 'lucide-react'

interface SearchFieldProps {
  label: string
  placeholder: string
  value: string
  onChange: (value: string) => void
}

export function SearchField({ label, placeholder, value, onChange }: SearchFieldProps) {
  return (
    <div className="relative min-w-56 flex-1">
      <Search
        className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500"
        aria-hidden
      />
      <input
        type="search"
        aria-label={label}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-md border border-slate-700 bg-slate-900 py-1.5 pl-9 pr-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:outline-none"
      />
    </div>
  )
}