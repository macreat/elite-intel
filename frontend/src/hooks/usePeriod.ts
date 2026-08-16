import { useMemo, useState } from 'react'
import type { PeriodPreset } from '../types/api'
import { getPeriodRange } from '../utils/period'

export function usePeriod(defaultPreset: PeriodPreset = 'month') {
  const [preset, setPreset] = useState<PeriodPreset>(defaultPreset)
  const [customStart, setCustomStart] = useState<string>('')
  const [customEnd, setCustomEnd] = useState<string>('')

  const range = useMemo(() => getPeriodRange(preset, customStart, customEnd), [preset, customStart, customEnd])

  return {
    preset,
    customStart,
    customEnd,
    range,
    setPreset,
    setCustomStart,
    setCustomEnd,
  }
}
