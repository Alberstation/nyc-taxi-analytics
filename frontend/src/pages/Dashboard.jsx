import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'
import { fetchDashboardAll } from '../api'

const layout = {
  paper_bgcolor: 'rgba(20, 20, 20, 0.98)',
  plot_bgcolor: 'rgba(20, 20, 20, 0.98)',
  font: { color: '#f5f5f5', family: 'Outfit', size: 12 },
  margin: { t: 30, r: 15, b: 35, l: 45 },
  xaxis: { gridcolor: '#2a2a2a', tickfont: { size: 10 } },
  yaxis: { gridcolor: '#2a2a2a', tickfont: { size: 10 } },
  legend: { font: { size: 10 }, orientation: 'h', y: 1.02 },
}

const NOKIA_BLUE = '#005AFF'
const NOKIA_BLUE_LIGHT = '#3d7fff'
const YELLOW_COLOR = '#f0b429'
const GREEN_COLOR = '#3fb950'

function ChartCard({ title, subtitle, children }) {
  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>{title}</h3>
        {subtitle && <span className="chart-subtitle">{subtitle}</span>}
      </div>
      {children}
    </div>
  )
}

export default function Dashboard() {
  const [cabFilter, setCabFilter] = useState('yellow')
  const [metrics, setMetrics] = useState(null)
  const [tripsOverTime, setTripsOverTime] = useState(null)
  const [paymentType, setPaymentType] = useState(null)
  const [tripsByHour, setTripsByHour] = useState(null)
  const [tripsByWeekday, setTripsByWeekday] = useState(null)
  const [heatmap, setHeatmap] = useState(null)
  const [demandPred, setDemandPred] = useState(null)
  const [clusters, setClusters] = useState(null)
  const [durationPred, setDurationPred] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDashboardAll(cabFilter)
      setMetrics(data.metrics)
      setTripsOverTime(data.trips_over_time)
      setPaymentType(data.payment_type)
      setTripsByHour(data.trips_by_hour)
      setTripsByWeekday(data.trips_by_weekday)
      setHeatmap(data.heatmap)
      setDemandPred(data.demand_predictions)
      setClusters(data.cluster_zones)
      setDurationPred(data.duration_predictions)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [cabFilter, refreshKey])

  const lineColor = cabFilter === 'yellow' ? YELLOW_COLOR : GREEN_COLOR
  const barColor = cabFilter === 'yellow' ? YELLOW_COLOR : GREEN_COLOR

  const makeLineData = (data) => [
    { x: data?.labels ?? [], y: data?.data ?? [], type: 'scatter', mode: 'lines+markers', line: { color: lineColor }, marker: { size: 5 } },
  ]

  const makeBarData = (data) => [
    { x: data?.labels ?? [], y: data?.data ?? [], type: 'bar', marker: { color: barColor } },
  ]

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner" />
        <p>Loading dashboard data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h2>Error loading dashboard</h2>
        <p>{error}</p>
        <p className="hint">Upload some data first from the Upload page.</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="page-title">Analytics Dashboard</h1>
        <div className="dashboard-header-actions">
          <div className="cab-filter cab-tabs">
            <label>Cab type:</label>
            <button
              type="button"
              className={`tab-btn ${cabFilter === 'yellow' ? 'active' : ''}`}
              onClick={() => setCabFilter('yellow')}
            >
              Yellow
            </button>
            <button
              type="button"
              className={`tab-btn ${cabFilter === 'green' ? 'active' : ''}`}
              onClick={() => setCabFilter('green')}
            >
              Green
            </button>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-refresh"
            onClick={() => setRefreshKey((k) => k + 1)}
            disabled={loading}
            title="Refresh data"
          >
            {loading ? '...' : '⟳ Refresh'}
          </button>
        </div>
      </div>

      {/* Top metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Total Trips</span>
          <span className="metric-value">{metrics?.total_trips?.toLocaleString() ?? 0}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Avg Fare ($)</span>
          <span className="metric-value">{metrics?.avg_fare ?? 0}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Avg Distance (mi)</span>
          <span className="metric-value">{metrics?.avg_distance ?? 0}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Busiest Hour</span>
          <span className="metric-value">{metrics?.busiest_hour ?? 'N/A'}</span>
        </div>
      </div>

      {/* Charts grid - 2 columns */}
      <div className="charts-grid">
        <ChartCard title="Trips Over Time (Aggregation)" subtitle="Daily counts · 2025">
          <Plot
            data={makeLineData(tripsOverTime)}
            layout={{
              ...layout,
              height: 260,
              showlegend: false,
              margin: { ...layout.margin, b: 50 },
              xaxis: {
                ...layout.xaxis,
                range: ['2025-01-01', '2025-12-31'],
                tickfont: { size: 12, color: '#f5f5f5' },
                tickangle: -20,
                showgrid: true,
                nticks: 8,
                tickformat: '%b %d',
              },
            }}
            useResizeHandler
            style={{ width: '100%' }}
          />
        </ChartCard>

        <ChartCard title="Trips by Hour of Day (Aggregation)" subtitle="24h distribution · SQL GROUP BY">
          <Plot
            data={makeBarData(tripsByHour ?? { labels: [], data: [] })}
            layout={{ ...layout, height: 260, barmode: 'relative', showlegend: false }}
            useResizeHandler
            style={{ width: '100%' }}
          />
        </ChartCard>

        <ChartCard title="Trips by Day of Week (Aggregation)" subtitle="Mon–Sun · SQL GROUP BY">
          <Plot
            data={makeBarData(tripsByWeekday ?? { labels: [], data: [] })}
            layout={{ ...layout, height: 260, barmode: 'relative', showlegend: false }}
            useResizeHandler
            style={{ width: '100%' }}
          />
        </ChartCard>

        <ChartCard title="Trips by Payment Type (Aggregation)" subtitle="CC, Cash, etc. · SQL GROUP BY">
          <Plot
            data={makeBarData(paymentType ?? { labels: [], data: [] })}
            layout={{ ...layout, height: 260, barmode: 'relative', showlegend: false }}
            useResizeHandler
            style={{ width: '100%' }}
          />
        </ChartCard>

        <ChartCard title="Demand Prediction" subtitle="Next 7 days · Ridge + Polynomial (degree=2)">
          {demandPred?.labels?.length > 0 ? (
            <Plot
              data={[
                { x: demandPred.labels, y: demandPred.actual, type: 'scatter', mode: 'lines+markers', name: 'Actual', line: { color: NOKIA_BLUE } },
                { x: demandPred.labels, y: demandPred.predicted, type: 'scatter', mode: 'lines+markers', name: 'Predicted', line: { color: NOKIA_BLUE_LIGHT, dash: 'dash' } },
              ]}
              layout={{
                ...layout,
                height: 260,
                xaxis: { ...layout.xaxis, nticks: 8, tickangle: -15, tickformat: '%b %d' },
              }}
              useResizeHandler
              style={{ width: '100%' }}
            />
          ) : (
            <div className="chart-empty">Need 7+ days of data</div>
          )}
        </ChartCard>

        <ChartCard title="Fare Distribution" subtitle="Top 20 trips by distance (mi) · Fare ($)">
          {durationPred?.labels?.length > 0 ? (
            (() => {
              const xIndices = durationPred.labels.map((_, i) => i)
              return (
                <Plot
                  data={[
                    {
                      x: xIndices,
                      y: durationPred.actual,
                      type: 'bar',
                      name: 'Actual fare ($)',
                      marker: { color: NOKIA_BLUE },
                    },
                  ]}
                  layout={{
                    ...layout,
                    height: 260,
                    showlegend: false,
                    xaxis: {
                      ...layout.xaxis,
                      title: 'Trip distance (mi)',
                      tickangle: -25,
                      tickvals: xIndices,
                      ticktext: durationPred.labels,
                    },
                    yaxis: { ...layout.yaxis, title: 'Fare ($)' },
                  }}
                  useResizeHandler
                  style={{ width: '100%' }}
                />
              )
            })()
          ) : (
            <div className="chart-empty">Need 50+ valid trips (distance &gt; 0, fare ≥ 0)</div>
          )}
        </ChartCard>
      </div>

      {/* Full-width maps */}
      <div className="maps-grid">
        {heatmap?.points?.length > 0 && (
          <ChartCard title="Pickup Heatmap (Aggregation)" subtitle="Raw density by zone · SQL GROUP BY">
            <div className="map-wrapper">
              <Plot
                data={[{
                  lat: heatmap.points.map((p) => p.lat),
                  lon: heatmap.points.map((p) => p.lon),
                  text: heatmap.points.map((p) => `${p.zone || 'Zone'}: ${p.count} pickups`),
                  type: 'scattermap',
                  mode: 'markers',
                  marker: {
                    size: heatmap.points.map((p) => Math.min(22, 5 + p.count / 200)),
                    color: heatmap.points.map((p) => p.count),
                    colorscale: [[0, '#0a0a0a'], [0.5, '#005AFF'], [1, '#3d7fff']],
                    showscale: true,
                  },
                }]}
                layout={{ ...layout, map: { style: 'open-street-map', center: { lat: 40.73, lon: -73.99 }, zoom: 11 }, height: 380, showlegend: false }}
                useResizeHandler
                style={{ width: '100%' }}
              />
            </div>
          </ChartCard>
        )}

        {clusters?.zones?.length > 0 && (
          <ChartCard title="Demand Clusters (DBSCAN)" subtitle="Geographic clusters · eps=0.01, min_samples=4">
            <div className="map-wrapper">
              <Plot
                data={[{
                  lat: clusters.zones.map((z) => z.lat),
                  lon: clusters.zones.map((z) => z.lon),
                  text: clusters.zones.map((z) => `${z.zone} (${z.count} trips)${z.cluster >= 0 ? ` · Cluster ${z.cluster}` : ' · Noise'}`),
                  type: 'scattermap',
                  mode: 'markers',
                  marker: {
                    size: clusters.zones.map((z) => Math.min(18, 5 + z.count / 500)),
                    color: clusters.zones.map((z) => (z.cluster >= 0 ? z.cluster : -1)),
                    colorscale: [[0, '#0a0a0a'], [0.2, '#0047cc'], [0.5, '#005AFF'], [0.8, '#3d7fff'], [1, '#7aa8ff']],
                    showscale: true,
                  },
                }]}
                layout={{ ...layout, map: { style: 'open-street-map', center: { lat: 40.73, lon: -73.99 }, zoom: 11 }, height: 380, showlegend: false }}
                useResizeHandler
                style={{ width: '100%' }}
              />
            </div>
          </ChartCard>
        )}
      </div>
    </div>
  )
}
