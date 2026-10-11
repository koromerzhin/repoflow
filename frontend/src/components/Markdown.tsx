import ReactMarkdown, { type Components } from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

type Size = 'base' | 'sm'

const components: Components = {
  h1: ({ children }) => (
    <h1 className="mt-4 mb-2 text-base font-semibold text-slate-100">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mt-4 mb-2 text-sm font-semibold text-slate-100">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mt-3 mb-1.5 text-sm font-semibold text-slate-200">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="mt-3 mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-300">
      {children}
    </h4>
  ),
  p: ({ children }) => <p className="my-2 leading-relaxed">{children}</p>,
  a: ({ children, href }) => (
    <a href={href} rel="noreferrer" className="text-sky-400 underline hover:text-sky-300">
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="my-2 ml-5 list-disc space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 ml-5 list-decimal space-y-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-4 border-slate-700 pl-3 italic text-slate-400">
      {children}
    </blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[0.85em] text-slate-200">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-lg bg-slate-950/70 p-3 font-mono text-xs text-slate-300 [&>code]:bg-transparent [&>code]:p-0 [&>code]:text-inherit">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-left">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border-b border-slate-700 px-2 py-1.5 text-xs font-medium uppercase tracking-wide text-slate-400">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border-b border-slate-800 px-2 py-1.5">{children}</td>
  ),
  img: ({ src, alt }) => (
    <img src={src} alt={alt} className="my-2 max-w-full rounded-lg" loading="lazy" />
  ),
  hr: () => <hr className="my-4 border-slate-800" />,
  del: ({ children }) => <del className="text-slate-500 line-through">{children}</del>,
  details: ({ children }) => (
    <details className="my-3 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2">
      {children}
    </details>
  ),
  summary: ({ children }) => (
    <summary className="cursor-pointer select-none font-medium text-slate-200">
      {children}
    </summary>
  ),
  kbd: ({ children }) => (
    <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[0.85em] text-slate-200">
      {children}
    </kbd>
  ),
  sub: ({ children }) => <sub>{children}</sub>,
  sup: ({ children }) => <sup>{children}</sup>,
  input: ({ checked }) => (
    <input
      type="checkbox"
      checked={checked}
      disabled
      readOnly
      className="mr-1.5 size-3 accent-sky-500"
    />
  ),
}

interface MarkdownProps {
  children: string
  size?: Size
}

export function Markdown({ children, size = 'base' }: MarkdownProps) {
  return (
    <div
      className={
        size === 'base' ? 'text-sm text-slate-300' : 'text-xs text-slate-400'
      }
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        components={components}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
