import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './App.css'

const WS_URL = 'ws://localhost:8000/ws'

function TrailCanvas({ trail, width = 640, height = 480 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, width, height)

    // Fondo oscuro
    ctx.fillStyle = '#0a0a0a'
    ctx.fillRect(0, 0, width, height)

    const validPoints = trail.filter(p => p !== null)
    if (validPoints.length < 2) return

    // Dibujar trayectoria con degradado
    for (let i = 1; i < trail.length; i++) {
      if (!trail[i] || !trail[i - 1]) continue

      const alpha = i / trail.length
      const thickness = Math.max(1, alpha * 6)

      ctx.beginPath()
      ctx.moveTo(trail[i - 1][0], trail[i - 1][1])
      ctx.lineTo(trail[i][0], trail[i][1])
      ctx.strokeStyle = `rgba(0, 255, 136, ${alpha})`
      ctx.lineWidth = thickness
      ctx.lineCap = 'round'
      ctx.stroke()
    }

    // Punto actual (último)
    const last = validPoints[validPoints.length - 1]
    if (last) {
      ctx.beginPath()
      ctx.arc(last[0], last[1], 8, 0, Math.PI * 2)
      ctx.fillStyle = '#00ff88'
      ctx.fill()

      // Halo
      ctx.beginPath()
      ctx.arc(last[0], last[1], 14, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(0, 255, 136, 0.3)'
      ctx.lineWidth = 3
      ctx.stroke()
    }

    // Punto inicial
    const first = validPoints[0]
    if (first) {
      ctx.beginPath()
      ctx.arc(first[0], first[1], 6, 0, Math.PI * 2)
      ctx.fillStyle = '#ff4444'
      ctx.fill()
    }

  }, [trail])

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ width: '100%', borderRadius: '8px' }}
    />
  )
}

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
      setTimeout(connect, 2000)
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
      <header>
        <h1>Baseball Tracker</h1>
        <div className={`status ${connected ? 'online' : 'offline'}`}>
          {connected ? 'Conectado' : 'Desconectado'}
        </div>
      </header>

      <main>
        {/* Video + Trayectoria lado a lado */}
        <section className="feeds">
          <div className="feed-box">
            <h2>Camara en vivo</h2>
            {frame
              ? <img src={frame} alt="feed" className="video-feed"/>
              : <div className="no-feed">Esperando camara...</div>
            }
          </div>
          <div className="feed-box">
            <h2>Trayectoria en vivo</h2>
            <TrailCanvas trail={state.trail} />
          </div>
        </section>

        {/* Stats */}
        <section className="stats">
          <div className={`stat-card ${state.detecting ? 'active' : ''}`}>
            <span className="stat-label">Estado</span>
            <span className="stat-value">{state.detecting ? 'DETECTANDO' : 'ESPERANDO'}</span>
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

        {/* Grafica velocidad */}
        <section className="chart-section">
          <h2>Velocidad en tiempo real</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={speedHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222"/>
              <XAxis dataKey="t" hide/>
              <YAxis stroke="#555" unit=" km/h"/>
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
                <span className="stat-label">Promedio</span>
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