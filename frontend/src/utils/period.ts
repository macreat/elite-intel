import type { CalendarDateRange, PeriodPreset } from '../types/api'
import { formatCalendarDate } from './format'

/** Returns local calendar dates; the API client supplies the browser timezone. */
export function getPeriodRange(
  preset: PeriodPreset,
  customStart?: string,
  customEnd?: string,
): CalendarDateRange {
  const now = new Date()
  const start = new Date(now)
  const end = new Date(now)

  if (preset === 'today') {
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
  } else if (preset === 'week') {
    const day = now.getDay()
    const diff = day === 0 ? 6 : day - 1
    start.setDate(now.getDate() - diff)
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
  } else if (preset === 'month') {
    start.setDate(1)
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)
  } else if (preset === 'previous_month') {
    start.setMonth(now.getMonth() - 1, 1)
    start.setHours(0, 0, 0, 0)
    end.setMonth(now.getMonth(), 0)
    end.setHours(23, 59, 59, 999)
  } else {
    return {
      start_date: customStart || formatCalendarDate(now),
      end_date: customEnd || formatCalendarDate(now),
    }
  }

  return {
    start_date: formatCalendarDate(start),
    end_date: formatCalendarDate(end),
  }
}
