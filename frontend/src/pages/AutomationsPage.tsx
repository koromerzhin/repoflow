import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { AsyncState } from '@/components/AsyncState'
import { Badge } from '@/components/Badge'
import { PageHeader } from '@/components/PageHeader'
import { useAsync } from '@/hooks/useAsync'
import { formatDateTime } from '@/lib/status'
import {
  ApiError,
  createRepositoryConfig,
  createRule,
  deleteRepositoryConfig,
  deleteRule,
  getAutomationStatus,
  listRepositoryConfigs,
  setKillSwitch,
  updateRepositoryConfig,
  updateRule,
} from '@/services/apiClient'
import type { AutomationRule, RepositoryConfig } from '@/types/api'

export function AutomationsPage() {
  const { t } = useTranslation()
  const configs = useAsync((signal) => listRepositoryConfigs(signal), [])
  const status = useAsync((signal) => getAutomationStatus(signal), [])

  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const [newFullName, setNewFullName] = useState('')
  const [newBranch, setNewBranch] = useState('main')

  async function runAction(action: () => Promise<unknown>) {
    setBusy(true)
    setActionError(null)
    try {
      await action()
      configs.reload()
      status.reload()
    } catch (cause) {
      setActionError(cause instanceof ApiError ? cause.message : t('automations.actionError'))
    } finally {
      setBusy(false)
    }
  }

  function handleAddRepository(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const fullName = newFullName.trim()
    const branch = newBranch.trim() || 'main'
    if (!fullName) {
      return
    }
    void runAction(async () => {
      await createRepositoryConfig({ full_name: fullName, default_branch: branch })
      setNewFullName('')
      setNewBranch('main')
    })
  }

  const killSwitchEngaged = status.data?.kill_switch_engaged ?? false

  return (
    <div>
      <PageHeader
        title={t('automations.title')}
        description={t('automations.description')}
      />

      {actionError ? (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200"
        >
          {actionError}
        </div>
      ) : null}

      <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900/40 p-5">
        <h2 className="text-base font-semibold text-slate-100">{t('automations.safeguards')}</h2>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Badge
            className={
              status.data?.global_auto_merge_enabled
                ? 'bg-amber-500/15 text-amber-300 ring-amber-500/30'
                : 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
            }
          >
            {t('automations.globalMerge')}{' '}
            {status.data?.global_auto_merge_enabled
              ? t('automations.enabled')
              : t('automations.disabled')}
          </Badge>
          <Badge
            className={
              status.data?.worker_enabled
                ? 'bg-sky-500/15 text-sky-300 ring-sky-500/30'
                : 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
            }
          >
            {t('automations.worker')}{' '}
            {status.data?.worker_enabled ? t('automations.active') : t('automations.inactive')}
          </Badge>
          <button
            type="button"
            disabled={busy || status.loading}
            onClick={() => void runAction(() => setKillSwitch(!killSwitchEngaged))}
            className={
              killSwitchEngaged
                ? 'rounded-md border border-red-700 bg-red-900/40 px-3 py-1.5 text-sm text-red-100 transition hover:bg-red-900/60 disabled:opacity-50'
                : 'rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 transition hover:border-red-700 hover:text-red-200 disabled:opacity-50'
            }
          >
            {killSwitchEngaged ? t('automations.disengage') : t('automations.engage')}
          </button>
        </div>
        {killSwitchEngaged ? (
          <p className="mt-3 text-sm text-red-300">{t('automations.killSwitchActive')}</p>
        ) : null}
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-base font-semibold text-slate-100">
          {t('automations.trackedRepos')}
        </h2>

        <form onSubmit={handleAddRepository} className="mb-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm text-slate-400">
            <span>{t('automations.repoLabel')}</span>
            <input
              type="text"
              value={newFullName}
              onChange={(event) => setNewFullName(event.target.value)}
              placeholder="acme/web-app"
              className="w-56 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-400">
            <span>{t('automations.defaultBranch')}</span>
            <input
              type="text"
              value={newBranch}
              onChange={(event) => setNewBranch(event.target.value)}
              className="w-40 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </label>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 transition hover:border-sky-600 hover:text-sky-300 disabled:opacity-50"
          >
            <Plus className="size-4" aria-hidden />
            {t('automations.add')}
          </button>
        </form>

        <AsyncState
          loading={configs.loading}
          error={configs.error}
          isEmpty={configs.data?.items.length === 0}
          emptyMessage={t('automations.empty')}
          onRetry={configs.reload}
        >
          <ul className="space-y-4">
            {configs.data?.items.map((config) => (
              <li key={config.id}>
                <RepositoryConfigCard
                  config={config}
                  busy={busy}
                  onToggleEnabled={() =>
                    void runAction(() =>
                      updateRepositoryConfig(config.id, { enabled: !config.enabled }),
                    )
                  }
                  onDelete={() => void runAction(() => deleteRepositoryConfig(config.id))}
                  onAddRule={(payload) =>
                    void runAction(() => createRule(config.id, payload))
                  }
                  onToggleRule={(rule: AutomationRule) =>
                    void runAction(() =>
                      updateRule(rule.id, { auto_merge_enabled: !rule.auto_merge_enabled }),
                    )
                  }
                  onDeleteRule={(rule: AutomationRule) =>
                    void runAction(() => deleteRule(rule.id))
                  }
                />
              </li>
            ))}
          </ul>
        </AsyncState>
      </section>
    </div>
  )
}

interface RepositoryConfigCardProps {
  config: RepositoryConfig
  busy: boolean
  onToggleEnabled: () => void
  onDelete: () => void
  onAddRule: (payload: {
    name: string
    branch_pattern: string
    auto_merge_enabled: boolean
    required_approvals: number
    require_green_checks: boolean
  }) => void
  onToggleRule: (rule: AutomationRule) => void
  onDeleteRule: (rule: AutomationRule) => void
}

function RepositoryConfigCard({
  config,
  busy,
  onToggleEnabled,
  onDelete,
  onAddRule,
  onToggleRule,
  onDeleteRule,
}: RepositoryConfigCardProps) {
  const { t } = useTranslation()
  const [ruleName, setRuleName] = useState('')
  const [branchPattern, setBranchPattern] = useState(config.default_branch)
  const [autoMerge, setAutoMerge] = useState(false)
  const [requiredApprovals, setRequiredApprovals] = useState(1)
  const [requireGreenChecks, setRequireGreenChecks] = useState(true)

  function handleAddRule(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const name = ruleName.trim()
    if (!name) {
      return
    }
    onAddRule({
      name,
      branch_pattern: branchPattern.trim() || '*',
      auto_merge_enabled: autoMerge,
      required_approvals: requiredApprovals,
      require_green_checks: requireGreenChecks,
    })
    setRuleName('')
    setAutoMerge(false)
    setRequiredApprovals(1)
    setRequireGreenChecks(true)
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-100">{config.full_name}</h3>
          <p className="mt-1 text-sm text-slate-400">
            {t('automations.config.defaultBranch')} {config.default_branch} ·{' '}
            {t('automations.config.addedOn', { date: formatDateTime(config.created_at) })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            className={
              config.enabled
                ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30'
                : 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
            }
          >
            {config.enabled ? t('automations.config.enabled') : t('automations.config.suspended')}
          </Badge>
          <button
            type="button"
            disabled={busy}
            onClick={onToggleEnabled}
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 transition hover:border-sky-600 hover:text-sky-300 disabled:opacity-50"
          >
            {config.enabled ? t('automations.config.suspend') : t('automations.config.activate')}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={onDelete}
            aria-label={t('automations.config.deleteAria', { name: config.full_name })}
            className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 transition hover:border-red-700 hover:text-red-200 disabled:opacity-50"
          >
            <Trash2 className="size-4" aria-hidden />
            {t('automations.config.delete')}
          </button>
        </div>
      </div>

      <div className="mt-4 border-t border-slate-800 pt-4">
        <h4 className="text-sm font-semibold text-slate-200">{t('automations.config.rules')}</h4>
        {config.rules.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">{t('automations.config.noRules')}</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {config.rules.map((rule) => (
              <li
                key={rule.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-100">{rule.name}</p>
                  <p className="text-xs text-slate-400">
                    {t('automations.config.branchPattern')} <code>{rule.branch_pattern}</code> ·{' '}
                    {t('automations.config.approvals', { count: rule.required_approvals })} ·{' '}
                    {t('automations.config.checksRequired', {
                      value: rule.require_green_checks
                        ? t('common.yes')
                        : t('common.no'),
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    className={
                      rule.auto_merge_enabled
                        ? 'bg-amber-500/15 text-amber-300 ring-amber-500/30'
                        : 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
                    }
                  >
                    {rule.auto_merge_enabled
                      ? t('automations.config.autoMerge')
                      : t('automations.config.manualMerge')}
                  </Badge>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onToggleRule(rule)}
                    className="rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-200 transition hover:border-sky-600 hover:text-sky-300 disabled:opacity-50"
                  >
                    {rule.auto_merge_enabled
                      ? t('automations.config.disable')
                      : t('automations.config.activate')}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onDeleteRule(rule)}
                    aria-label={t('automations.config.deleteRuleAria', { name: rule.name })}
                    className="inline-flex items-center rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-200 transition hover:border-red-700 hover:text-red-200 disabled:opacity-50"
                  >
                    <Trash2 className="size-3.5" aria-hidden />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={handleAddRule} className="mt-3 flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-slate-400">
            <span>{t('automations.rule.name')}</span>
            <input
              type="text"
              value={ruleName}
              onChange={(event) => setRuleName(event.target.value)}
              placeholder={t('automations.rule.namePlaceholder')}
              className="w-44 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-400">
            <span>{t('automations.rule.pattern')}</span>
            <input
              type="text"
              value={branchPattern}
              onChange={(event) => setBranchPattern(event.target.value)}
              className="w-40 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-400">
            <span>{t('automations.rule.approvals')}</span>
            <input
              type="number"
              min={0}
              max={10}
              value={requiredApprovals}
              onChange={(event) => setRequiredApprovals(Number(event.target.value))}
              className="w-24 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-300">
            <input
              type="checkbox"
              checked={requireGreenChecks}
              onChange={(event) => setRequireGreenChecks(event.target.checked)}
            />
            {t('automations.rule.requireChecks')}
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-300">
            <input
              type="checkbox"
              checked={autoMerge}
              onChange={(event) => setAutoMerge(event.target.checked)}
            />
            {t('automations.rule.autoMerge')}
          </label>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 transition hover:border-sky-600 hover:text-sky-300 disabled:opacity-50"
          >
            <Plus className="size-4" aria-hidden />
            {t('automations.rule.add')}
          </button>
        </form>
      </div>
    </div>
  )
}
