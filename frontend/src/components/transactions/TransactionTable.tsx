import { Pencil, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import type { Transaction } from '../../types/transaction'
import { formatCurrency, formatDate } from '../../utils/format'

interface TransactionTableProps {
  items: Transaction[]
  onDelete: (id: number) => void
}

export function TransactionTable({ items, onDelete }: TransactionTableProps) {
  return (
    <>
      <div className="hidden overflow-hidden rounded-xl border border-white/[0.06] bg-navy-700/60 backdrop-blur-sm md:block">
        <table className="min-w-full divide-y divide-white/[0.06]">
          <thead className="bg-navy-800/50 text-left text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Notes</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {items.map((item) => (
              <tr key={item.id} className="transition-colors hover:bg-white/[0.02]">
                <td className="px-4 py-3 text-sm text-slate-300">{formatDate(item.occurred_at)}</td>
                <td className="px-4 py-3 text-sm">
                  <span
                    className={clsx(
                      'inline-flex rounded-full px-2 py-1 text-xs font-medium',
                      item.transaction_type === 'INCOME'
                        ? 'bg-mint-600/15 text-mint-500'
                        : 'bg-rose-500/15 text-rose-400',
                    )}
                  >
                    {item.transaction_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-slate-300">{item.category_name ?? `#${item.category_id}`}</td>
                <td className="px-4 py-3 text-sm text-slate-200">{item.description}</td>
                <td className="px-4 py-3 text-sm font-medium text-white">{formatCurrency(item.amount, item.currency_code)}</td>
                <td className="max-w-[220px] truncate px-4 py-3 text-sm text-slate-500">{item.notes ?? '-'}</td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex gap-2">
                    <Link to={`/transactions/${item.id}/edit`} className="btn-secondary !px-2 !py-1" aria-label="Edit transaction">
                      <Pencil className="h-4 w-4" />
                    </Link>
                    <button
                      type="button"
                      className="btn-secondary !px-2 !py-1 text-rose-400"
                      onClick={() => onDelete(item.id)}
                      aria-label="Delete transaction"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 md:hidden">
        {items.map((item) => (
          <article key={item.id} className="card">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">{formatDate(item.occurred_at)}</p>
              <span
                className={clsx(
                  'inline-flex rounded-full px-2 py-1 text-xs font-medium',
                  item.transaction_type === 'INCOME' ? 'bg-mint-600/15 text-mint-500' : 'bg-rose-500/15 text-rose-400',
                )}
              >
                {item.transaction_type}
              </span>
            </div>
            <p className="mt-2 font-medium text-white">{item.description}</p>
            <p className="text-sm text-slate-400">{item.category_name ?? `#${item.category_id}`}</p>
            <p className="mt-1 text-base font-semibold text-white">{formatCurrency(item.amount, item.currency_code)}</p>
            <p className="mt-1 text-sm text-slate-500">{item.notes ?? '-'}</p>
            <div className="mt-3 flex gap-2">
              <Link to={`/transactions/${item.id}/edit`} className="btn-secondary w-full gap-1">
                <Pencil className="h-4 w-4" /> Edit
              </Link>
              <button type="button" className="btn-secondary w-full gap-1 text-rose-400" onClick={() => onDelete(item.id)}>
                <Trash2 className="h-4 w-4" /> Delete
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  )
}
