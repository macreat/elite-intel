const LOCALE_BY_CURRENCY: Record<string, string> = {
  COP: 'es-CO',
  ARS: 'es-AR',
}

export function formatCurrency(value: number, currency = 'ARS') {
  return new Intl.NumberFormat(LOCALE_BY_CURRENCY[currency] ?? 'es-AR', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value)
}

// Parse a lenient user-entered amount string into a Number (returns null if not parseable)
export function parseUserAmount(input: string): number | null {
  if (!input) return null
  // Keep digits, dots and commas and minus
  const cleaned = String(input).trim()
  if (!cleaned) return null

  // If both dot and comma present, assume the last one is the decimal separator
  const hasDot = cleaned.indexOf('.') >= 0
  const hasComma = cleaned.indexOf(',') >= 0

  let normalized = cleaned.replace(/[^0-9.,-]/g, '')
  if (hasDot && hasComma) {
    // determine which appears last
    const lastDot = cleaned.lastIndexOf('.')
    const lastComma = cleaned.lastIndexOf(',')
    if (lastComma > lastDot) {
      // comma is decimal, remove dots as thousands
      normalized = normalized.replace(/\./g, '')
      normalized = normalized.replace(/,/g, '.')
    } else {
      // dot is decimal, remove commas as thousands
      normalized = normalized.replace(/,/g, '')
    }
  } else if (hasComma && !hasDot) {
    // comma assumed as decimal
    normalized = normalized.replace(/\./g, '')
    normalized = normalized.replace(/,/g, '.')
  } else {
    // only dots or only digits - treat dot as decimal if it appears once and there are digits after
    // otherwise, dots are thousands separators
    const parts = normalized.split('.')
    if (parts.length > 2) {
      // multiple dots -> remove all as thousands, then no decimal
      normalized = normalized.replace(/\./g, '')
    }
    // if single dot and right side length <= 2, keep it as decimal; otherwise remove as thousands
    if (parts.length === 2 && parts[1].length <= 2) {
      // keep
    } else if (parts.length === 2) {
      // ambiguous: treat as thousands separators
      normalized = normalized.replace(/\./g, '')
    }
  }

  // Final normalized should have dot as decimal separator
  const num = Number(normalized)
  if (Number.isNaN(num)) return null
  return num
}

export function formatAmountForDisplay(value: string | number | null): string {
  if (value === null || value === undefined || value === '') return ''
  const num = typeof value === 'number' ? value : parseUserAmount(String(value))
  if (num === null) return ''
  return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num)
}

export function formatDate(iso: string) {
  const datePart = iso.slice(0, 10)
  if (/^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
    return datePart
  }

  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  return date.toISOString().slice(0, 10)
}

export function formatCalendarDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function getTodayCalendarDate() {
  return formatCalendarDate(new Date())
}

export function toInputDate(iso: string) {
  const datePart = iso.slice(0, 10)
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    return iso
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
    const parsed = new Date(iso)
    return Number.isNaN(parsed.getTime()) ? datePart : formatCalendarDate(parsed)
  }
  return formatDate(iso)
}

export function fromInputDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day, 0, 0, 0, 0).toISOString()
}

export function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}
