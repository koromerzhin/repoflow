import { X } from 'lucide-react'
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { VisibilityBadge } from '@/components/VisibilityBadge'
import { matchesQuery } from '@/lib/search'
import type { Repository } from '@/types/api'

interface ComboboxOption {
  value: string
  label: string
  repository?: Repository
}

interface RepositoryComboboxProps {
  repositories: Repository[]
  value: string
  onChange: (value: string) => void
  label: string
}

export function RepositoryCombobox({
  repositories,
  value,
  onChange,
  label,
}: RepositoryComboboxProps) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const listboxId = useId()

  const options = useMemo<ComboboxOption[]>(() => {
    const all: ComboboxOption[] = [
      { value: '', label: t('filter.all') },
      ...repositories.map((repository) => ({
        value: repository.full_name,
        label: repository.full_name,
        repository,
      })),
    ]
    return all.filter((option) => matchesQuery(option.label, query))
  }, [repositories, query, t])

  useEffect(() => {
    if (open && activeIndex >= 0) {
      listRef.current?.children[activeIndex]?.scrollIntoView?.({ block: 'nearest' })
    }
  }, [open, activeIndex])

  function select(optionValue: string) {
    onChange(optionValue)
    setOpen(false)
    setQuery('')
    setActiveIndex(-1)
    inputRef.current?.focus()
  }

  function closeList() {
    setOpen(false)
    setQuery('')
    setActiveIndex(-1)
  }

  function openList() {
    setOpen(true)
    setQuery('')
    const index = options.findIndex((option) => option.value === value)
    setActiveIndex(index >= 0 ? index : 0)
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (!open) {
        openList()
        return
      }
      setActiveIndex((index) => Math.min(index + 1, options.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => Math.max(index - 1, 0))
    } else if (event.key === 'Home' && open) {
      event.preventDefault()
      setActiveIndex(0)
    } else if (event.key === 'End' && open) {
      event.preventDefault()
      setActiveIndex(options.length - 1)
    } else if (event.key === 'Enter') {
      const option = options[activeIndex]
      if (open && option) {
        event.preventDefault()
        select(option.value)
      }
    } else if (event.key === 'Escape') {
      closeList()
    }
  }

  function handleBlur(event: React.FocusEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      closeList()
    }
  }

  return (
    <div className="relative" onBlur={handleBlur}>
      <div className="flex items-center gap-1">
        <input
          ref={inputRef}
          type="text"
          role="combobox"
          autoComplete="off"
          aria-label={label}
          aria-expanded={open}
          aria-controls={open ? listboxId : undefined}
          aria-autocomplete="list"
          aria-activedescendant={
            open && activeIndex >= 0 ? `${listboxId}-opt-${activeIndex}` : undefined
          }
          value={open ? query : value}
          placeholder={t('filter.searchPlaceholder')}
          onChange={(event) => {
            setQuery(event.target.value)
            setOpen(true)
            setActiveIndex(0)
          }}
          onFocus={openList}
          onClick={openList}
          onKeyDown={handleKeyDown}
          className="w-48 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
        />
        {value ? (
          <button
            type="button"
            aria-label={t('filter.clear')}
            onClick={() => select('')}
            className="rounded-md border border-slate-700 bg-slate-900 p-1.5 text-slate-400 transition hover:border-sky-600 hover:text-sky-300"
          >
            <X className="size-3.5" aria-hidden />
          </button>
        ) : null}
      </div>

      {open ? (
        <ul
          id={listboxId}
          ref={listRef}
          role="listbox"
          aria-label={t('filter.listLabel')}
          className="absolute left-0 z-40 mt-1 max-h-64 w-full min-w-56 overflow-y-auto rounded-md border border-slate-700 bg-slate-900 py-1 shadow-xl"
        >
          {options.map((option, index) => (
            <li
              key={option.value || '__all__'}
              id={`${listboxId}-opt-${index}`}
              role="option"
              aria-selected={option.value === value}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => select(option.value)}
              className={[
                'flex cursor-pointer items-center justify-between gap-3 px-3 py-2 text-sm',
                index === activeIndex
                  ? 'bg-slate-800 text-slate-50'
                  : 'text-slate-300 hover:bg-slate-800',
              ].join(' ')}
            >
              <span className="min-w-0 truncate">{option.label}</span>
              {option.repository ? <VisibilityBadge isPrivate={option.repository.private} /> : null}
            </li>
          ))}
          {options.length === 0 ? (
            <li className="px-3 py-2 text-xs text-slate-500" aria-live="polite">
              {t('filter.noResult')}
            </li>
          ) : null}
        </ul>
      ) : null}
    </div>
  )
}