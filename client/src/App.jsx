import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import './App.css'

// Supabase Configuration
const supabaseUrl = 'https://wjqtxvtlqswwxqdciuwm.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndqcXR4dnRscXN3d3hxZGNpdXdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1NzUxOTksImV4cCI6MjA4NTE1MTE5OX0.wjn1aDedu1CCxZWKg8lpxclrvPqGFWIPmc5hDIZuO6g'
const supabase = createClient(supabaseUrl, supabaseAnonKey)

function App() {
  const [data, setData] = useState({
    status: 0,
    temperature: 0,
    pressure: 0,
    speed: 0,
    gas_concentration: 0,
    valve_status: 1
  })
  const [history, setHistory] = useState([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    // 1. Initial Data & History Fetch
    const fetchInitialData = async () => {
      try {
        const { data: latestData, error: latestError } = await supabase
          .from('sensor_data')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(1)

        if (latestData && latestData.length > 0) {
          setData(latestData[0])
          setConnected(true)
        }

        const { data: historyData, error: historyError } = await supabase
          .from('sensor_data')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(50)

        if (historyData) {
          setHistory(historyData)
        }
      } catch (err) {
        console.error('Error fetching initial data:', err)
        setConnected(false)
      }
    }

    fetchInitialData()

    // 2. Realtime Subscription
    const channel = supabase
      .channel('sensor_changes')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'sensor_data' },
        (payload) => {
          console.log('Realtime Update:', payload.new)
          setData(payload.new)
          setHistory(prev => [payload.new, ...prev].slice(0, 50))
          setConnected(true)
        }
      )
      .subscribe((status) => {
        console.log('Subscription status:', status)
        if (status === 'SUBSCRIBED') {
          setConnected(true)
        } else if (status === 'CLOSED' || status === 'CHANNEL_ERROR') {
          setConnected(false)
        }
      })

    return () => {
      supabase.removeChannel(channel)
    }
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

  const getValveStatus = (v) => {
    switch (v) {
      case 1: return <div className="valve-banner open">VALVE STATUS: OPEN</div>
      case 2: return <div className="valve-banner interlock">🚨 GAS SHUT-OFF ACTIVE (INTERLOCK)</div>
      default: return <div className="valve-banner closed">VALVE STATUS: CLOSED</div>
    }
  }

  return (
    <div className="container">
      <header className="header">
        <h1>GAS FACILITY SAFETY MONITORING</h1>
        <div className={`connection-status ${connected ? 'online' : 'offline'}`}>
          {connected ? '● LIVE (SUPABASE)' : '○ CONNECTING...'}
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
              {history.map((row, i) => (
                <tr key={row.id || i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '1rem', color: '#64748b' }}>{new Date(row.timestamp).toLocaleString()}</td>
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
