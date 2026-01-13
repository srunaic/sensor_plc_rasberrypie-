import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [data, setData] = useState({
    status: 0,
    temperature: 0,
    pressure: 0,
    speed: 0,
    gas_concentration: 0,
    valve_status: 1 // OPEN by default
  })
  const [history, setHistory] = useState([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    // Use the current window hostname to avoid CORS mismatches (localhost vs 127.0.0.1)
    const host = window.location.hostname;
    const backendUrl = `http://${host}:8000`;
    const wsUrl = `ws://${host}:8000/ws/monitoring`;

    // WebSocket Connection
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket Connected')
    }

    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data)
      setData(newData)
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('WebSocket Disconnected')
    }

    // Fetch History
    fetch(`${backendUrl}/api/history`)
      .then(res => res.json())
      .then(json => setHistory(json))
      .catch(err => console.error("Initial fetch failed:", err))

    return () => ws.close()
  }, [])

  const getStatusText = (s) => {
    switch (s) {
      case 1: return <><span className="status-indicator status-run"></span>RUNNING</>
      case 2: return <><span className="status-indicator status-fault"></span>FAULT / ALARM</>
      default: return <><span className="status-indicator status-stop"></span>STOPPED</>
    }
  }

  const getGasStatus = (ppm) => {
    if (ppm > 40) return <span className="gas-status alarm">🚨 ALARM (CRITICAL)</span>
    if (ppm > 20) return <span className="gas-status warning">⚠️ WARNING</span>
    return <span className="gas-status normal">✅ NORMAL</span>
  }

  //#region PLC Status Interlock safe value 
  const getValveStatus = (v) => {
    switch (v) {
      case 1: return <div className="valve-banner open">VALVE STATUS: OPEN</div>
      case 2: return <div className="valve-banner interlock">🚨 GAS SHUT-OFF ACTIVE (INTERLOCK)</div>
      default: return <div className="valve-banner closed">VALVE STATUS: CLOSED</div>
    }
  }
  //#endregion

  //Online Status
  return (
    <div className="container">
      <header className="header">
        <h1>GAS FACILITY SAFETY MONITORING</h1>
        <div className={`connection-status ${connected ? 'online' : 'offline'}`}>
          {connected ? '● SERVER ONLINE' : '○ SERVER OFFLINE'}
        </div>
      </header>

      {getValveStatus(data.valve_status)}

      <div className="dashboard">
        <div className="card highlight">
          <h2>Gas Status</h2>
          <div className="value-display">
            {getGasStatus(data.gas_concentration)}
          </div>
          <div className="sub-value">Current: {data.gas_concentration?.toFixed(2)} PPM</div>
        </div>

        <div className="card">
          <h2>Equipment Health</h2>
          <div className="value-display" style={{ fontSize: '1.8rem' }}>
            {getStatusText(data.status)}
          </div>
          {data.valve_status === 2 && <div className="safety-note">Interlock reset requires on-site manual reset.</div>}
        </div>

        <div className="card">
          <h2>Temperature</h2>
          <div className="value-display">
            {data.temperature?.toFixed(2)}<span className="unit">°C</span>
          </div>
        </div>

        <div className="card">
          <h2>Pressure</h2>
          <div className="value-display">
            {data.pressure?.toFixed(2)}<span className="unit">bar</span>
          </div>
        </div>
      </div>

      <section className="history-section" style={{ marginTop: '2rem' }}>
        <h2>Safety Audit History</h2>
        <div className="history-table-container card" style={{ marginTop: '1rem', padding: '0' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: '1rem' }}>Timestamp</th>
                <th style={{ padding: '1rem' }}>Event Type</th>
                <th style={{ padding: '1rem' }}>Gas (PPM)</th>
                <th style={{ padding: '1rem' }}>Valve</th>
                <th style={{ padding: '1rem' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {history.slice(0, 10).map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '1rem', color: '#64748b' }}>{row.timestamp}</td>
                  <td style={{ padding: '1rem' }}>
                    {row.valve_status === 2 ? <span style={{ color: '#ef4444' }}>GAS_INTERLOCK</span> : row.gas_concentration > 20 ? 'GAS_WARNING' : 'SYSTEM_LOG'}
                  </td>
                  <td style={{ padding: '1rem' }}>{row.gas_concentration?.toFixed(2)}</td>
                  <td style={{ padding: '1rem' }}>{row.valve_status === 1 ? 'OPEN' : 'CLOSED'}</td>
                  <td style={{ padding: '1rem', fontSize: '0.85rem' }}>
                    {row.valve_status === 2 ? 'Automatic shut-off due to high concentration' : 'Normal operation'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default App
