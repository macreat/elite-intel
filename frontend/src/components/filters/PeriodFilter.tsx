import type { PeriodPreset } from '../../types/api'

interface PeriodFilterProps {
  preset: PeriodPreset
  customStart?: string
  customEnd?: string
  onPresetChange: (value: PeriodPreset) => void
  onCustomStartChange: (value: string) => void
  onCustomEndChange: (value: string) => void
}

export function PeriodFilter({
  preset,
  customStart,
  customEnd,
  onPresetChange,
  onCustomStartChange,
  onCustomEndChange,
}: PeriodFilterProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div>
        <label className="label">Period</label>
        <select className="field min-w-44" value={preset} onChange={(event) => onPresetChange(event.target.value as PeriodPreset)}>
          <option value="today">Today</option>
          <option value="week">Current Week</option>
          <option value="month">Current Month</option>
          <option value="previous_month">Previous Month</option>
          <option value="year">This Year</option>
          <option value="all_time">All Time</option>
          <option value="custom">Custom Range</option>
        </select>
      </div>

      {preset === 'custom' ? (
        <>
          <div>
            <label className="label">Start Date</label>
            <input className="field" type="date" value={customStart ?? ''} onChange={(event) => onCustomStartChange(event.target.value)} />
          </div>
          <div>
            <label className="label">End Date</label>
            <input className="field" type="date" value={customEnd ?? ''} onChange={(event) => onCustomEndChange(event.target.value)} />
          </div>
        </>
      ) : null}
    </div>
  )
}
