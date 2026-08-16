export function formatCurrency(value: number, currency = 'ARS') {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value)
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
