import { useState, useRef } from 'react'
import { uploadFile, loadSample } from '../api'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [cabType, setCabType] = useState('yellow')
  const [maxRows, setMaxRows] = useState(100000)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const f = e.target.files?.[0]
    setFile(f)
    setError(null)
    setMessage(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const res = await uploadFile(file, cabType, maxRows)
      setMessage(`Successfully ingested ${res.created?.toLocaleString()} trips.`)
      setFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadSample = async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const res = await loadSample()
      setMessage(`Loaded ${res.created?.toLocaleString()} sample trips from ${res.files_loaded} file(s).`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="upload-page">
      <h1 className="page-title">Upload Data</h1>
      <p className="upload-desc">
        Upload NYC TLC taxi trip data (CSV or Parquet). Supports both Yellow and Green taxi schemas.
      </p>

      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}

      <div className="upload-card">
        <h2>File Upload</h2>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.parquet"
          onChange={handleFileChange}
          className="file-input"
        />
        {file && <p className="file-name">Selected: {file.name}</p>}

        <div className="upload-options">
          <label>
            Cab type:
            <select value={cabType} onChange={(e) => setCabType(e.target.value)}>
              <option value="yellow">Yellow</option>
              <option value="green">Green</option>
            </select>
          </label>
          <label>
            Max rows:
            <input
              type="number"
              value={maxRows}
              onChange={(e) => setMaxRows(Number(e.target.value) || 100000)}
              min={1000}
              max={500000}
              step={10000}
            />
          </label>
        </div>

        <button onClick={handleUpload} disabled={loading || !file} className="btn btn-primary">
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </div>

      <div className="upload-card">
        <h2>Load Sample Data</h2>
        <p>Load up to 600,000 trips from the 6 preloaded parquet files in the <code>data/</code> folder (green & yellow, Jan–Mar 2025).</p>
        <button onClick={handleLoadSample} disabled={loading} className="btn btn-secondary">
          {loading ? 'Loading...' : 'Load Sample'}
        </button>
      </div>
    </div>
  )
}
