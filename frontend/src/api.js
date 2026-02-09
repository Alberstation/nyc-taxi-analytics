const API_BASE = '/api'

function withCabType(path, cabType) {
  if (cabType && cabType !== 'all') {
    const sep = path.includes('?') ? '&' : '?'
    return `${path}${sep}cab_type=${cabType}`
  }
  return path
}

/** Single request for all dashboard data - much faster than 9 separate calls */
export async function fetchDashboardAll(cabType = 'all') {
  const url = withCabType(`${API_BASE}/dashboard/`, cabType)
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) throw new Error('Failed to fetch dashboard')
  return res.json()
}

export async function fetchMetrics(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/metrics/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

export async function fetchTripsOverTime(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/trips-over-time/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch trips over time')
  return res.json()
}

export async function fetchPaymentType(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/payment-type/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch payment type')
  return res.json()
}

export async function fetchTripsByHour(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/trips-by-hour/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch trips by hour')
  return res.json()
}

export async function fetchTripsByWeekday(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/trips-by-weekday/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch trips by weekday')
  return res.json()
}

export async function fetchHeatmap(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/heatmap/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch heatmap')
  return res.json()
}

export async function fetchDemandPredictions(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/demand-predictions/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch demand predictions')
  return res.json()
}

export async function fetchClusterZones(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/cluster-zones/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch cluster zones')
  return res.json()
}

export async function fetchDurationPredictions(cabType = 'all') {
  const res = await fetch(withCabType(`${API_BASE}/duration-predictions/`, cabType))
  if (!res.ok) throw new Error('Failed to fetch duration predictions')
  return res.json()
}

export async function uploadFile(file, cabType = 'yellow', maxRows = 100000) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('cab_type', cabType)
  formData.append('max_rows', maxRows.toString())
  const res = await fetch(`${API_BASE}/upload/`, {
    method: 'POST',
    body: formData,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || 'Upload failed')
  return data
}

export async function loadSample() {
  const res = await fetch(`${API_BASE}/load-sample/`, { method: 'POST' })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || 'Load sample failed')
  return data
}
