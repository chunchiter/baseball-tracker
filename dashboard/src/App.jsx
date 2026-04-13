import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './App.css'

const WS_URL = 'ws://localhost:8000/ws'

function App() {
  const [connected, setConnected] = useState(false)
  const [state, setState] = useState({
    detecting: false,
    speed_kmh: 0,
    max_speed_kmh: 0,
    total_throws: 0,
    trail: [],
    last_throw: null
  })
  const [speedHistory, setSpeedHistory] = useState([])
  const [frame, setFrame] = useState(null)
  const wsRef = useRef(null)
  const canvasRef = useRef(null)

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [])

  function connect() {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, 2000) // reconectar automático
    }
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      setState(data)

      if (data.frame) setFrame(`data:image/jpeg;base64,${data.frame}`)

      if (data.speed_kmh > 0) {
        setSpeedHistory(prev => [...prev.slice(-30), {
          t: prev.length,
          speed: data.speed_kmh
        }])
      }
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header>
        <h1>Baseball Tracker</h1>
        <div className={`status ${connected ? 'online' : 'offline'}`}>
          {connected ? 'Conectado' : 'Desconectado'}
        </div>
      </header>

      <main>
        {/* Video feed */}
        <section className="video-section">
          <h2>Camara en vivo</h2>
          {frame
            ? <img src={frame} alt="feed" className="video-feed"/>
            : <div className="no-feed">Esperando camara...</div>
          }
        </section>

        {/* Stats */}
        <section className="stats">
          <div className={`stat-card ${state.detecting ? 'active' : ''}`}>
            <span className="stat-label">Estado</span>
            <span className="stat-value">
              {state.detecting ? 'DETECTANDO' : 'ESPERANDO'}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Velocidad</span>
            <span className="stat-value speed">{state.speed_kmh} km/h</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Max sesion</span>
            <span className="stat-value">{state.max_speed_kmh} km/h</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Lanzamientos</span>
            <span className="stat-value">{state.total_throws}</span>
          </div>
        </section>

        {/* Grafica de velocidad */}
        <section className="chart-section">
          <h2>Velocidad en tiempo real</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={speedHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333"/>
              <XAxis dataKey="t" hide/>
              <YAxis stroke="#aaa" unit=" km/h"/>
              <Tooltip formatter={(v) => [`${v} km/h`, 'Velocidad']}/>
              <Line
                type="monotone"
                dataKey="speed"
                stroke="#00ff88"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* Ultimo lanzamiento */}
        {state.last_throw && (
          <section className="last-throw">
            <h2>Ultimo lanzamiento</h2>
            <div className="throw-stats">
              <div className="stat-card">
                <span className="stat-label">Velocidad max</span>
                <span className="stat-value">{state.last_throw.max_speed_kmh} km/h</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Velocidad promedio</span>
                <span className="stat-value">{state.last_throw.avg_speed_kmh} km/h</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Puntos grabados</span>
                <span className="stat-value">{state.last_throw.points?.length}</span>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App