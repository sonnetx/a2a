import { Suspense, useMemo, useRef, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Html, Billboard, GradientTexture } from '@react-three/drei'

const TAU = Math.PI * 2

type Vec3 = [number, number, number]

function polarToVec3(r: number, angle: number, y: number = 0): Vec3 {
  return [Math.cos(angle) * r, y, Math.sin(angle) * r]
}

function lerp(a: number, b: number, t: number) { return a + (b - a) * t }
function vec3Lerp(a: Vec3, b: Vec3, t: number): Vec3 { return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)] }

function bezier3(a: Vec3, b: Vec3, c: Vec3, d: Vec3, t: number): Vec3 {
  const ab = vec3Lerp(a, b, t); const bc = vec3Lerp(b, c, t); const cd = vec3Lerp(c, d, t)
  const abbc = vec3Lerp(ab, bc, t); const bccd = vec3Lerp(bc, cd, t)
  return vec3Lerp(abbc, bccd, t)
}

function useCircleLayout(agents: { id: string }[], radius = 6) {
  return useMemo(() => {
    const n = Math.max(agents.length, 1)
    const map = new Map<string, Vec3>()
    agents.forEach((a, i) => {
      const angle = (i / n) * TAU
      map.set(a.id, polarToVec3(radius, angle))
    })
    return map
  }, [agents])
}

function Sparkle({ position = [0, 0, 0] as Vec3 }) {
  const ref = useRef<any>()
  useFrame(({ clock }) => {
    if (!ref.current) return
    const t = clock.getElapsedTime()
    ref.current.scale.setScalar(1 + Math.sin(t * 6) * 0.15 + 0.15)
  })
  return (
    <mesh position={position} ref={ref}>
      <sphereGeometry args={[0.08, 16, 16]} />
      <meshStandardMaterial emissiveIntensity={1} emissive={'white'} color={'white'} />
    </mesh>
  )
}

function AgentAvatar({ id, name, color = '#6EE7B7', emoji = '🤖', position }: { id: string, name?: string, color?: string, emoji?: string, position: Vec3 }) {
  const group = useRef<any>()
  useFrame(({ clock }) => {
    if (group.current) {
      const tilt = Math.sin(clock.getElapsedTime() * 1.3) * 0.06
      group.current.rotation.y = tilt
    }
  })
  return (
    <group ref={group} position={position}>
      <mesh castShadow receiveShadow>
        <sphereGeometry args={[0.6, 32, 32]} />
        <meshStandardMaterial>
          <GradientTexture stops={[0, 0.5, 1]} colors={['white', color, '#ffffff']} size={1024} />
        </meshStandardMaterial>
      </mesh>

      <Billboard position={[0, 0.85, 0]}>
        <Text fontSize={0.35} anchorX="center" anchorY="middle">{emoji}</Text>
      </Billboard>

      <Billboard position={[0, -1.0, 0]}>
        <Text fontSize={0.28} color="#2b2b2b" outlineColor="#ffffff" outlineWidth={0.015}>{name || id}</Text>
      </Billboard>

      <Sparkle position={[0.9, 0.2, 0]} />
    </group>
  )
}

function MessageOrb({ fromPos, toPos, text, bornAt, duration = 2.0, height = 1.5, color = '#60A5FA', now }: {
  fromPos: Vec3
  toPos: Vec3
  text?: string
  bornAt: number
  duration?: number
  height?: number
  color?: string
  now: number
}) {
  const tNorm = (now - bornAt) / duration
  if (tNorm < 0 || tNorm > 1) return null

  const mid1: Vec3 = [(fromPos[0] * 2 + toPos[0]) / 3, height, (fromPos[2] * 2 + toPos[2]) / 3]
  const mid2: Vec3 = [(fromPos[0] + toPos[0] * 2) / 3, height, (fromPos[2] + toPos[2] * 2) / 3]
  const p = bezier3(fromPos, mid1, mid2, toPos, tNorm)

  return (
    <group position={p}>
      <mesh castShadow>
        <sphereGeometry args={[0.12, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.9} />
      </mesh>
      {text && (
        <Billboard position={[0, 0.45, 0]}>
          <Text fontSize={0.22} maxWidth={2} lineHeight={1.2} color="#1f2937">{text}</Text>
        </Billboard>
      )}
    </group>
  )
}

function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[60, 60]} />
      <meshStandardMaterial color="#f6f7fb" />
    </mesh>
  )
}

function Ring({ r = 6, y = 0.001 }) {
  const points = useMemo(() => {
    const arr: Vec3[] = []
    for (let i = 0; i < 64; i++) arr.push(polarToVec3(r, (i / 64) * TAU, y))
    return arr
  }, [r])
  return (
    <group>
      {points.map((p, i) => (
        <mesh key={i} position={p}>
          <boxGeometry args={[0.06, 0.02, 0.06]} />
          <meshStandardMaterial color="#e5e7eb" />
        </mesh>
      ))}
    </group>
  )
}

function usePlayback(duration: number, { autoPlay = true, speed = 1 } = {}) {
  const [playing, setPlaying] = useState(autoPlay)
  const [time, setTime] = useState(0)
  const speedRef = useRef(speed)
  useEffect(() => { speedRef.current = speed }, [speed])

  useFrame((_, delta) => {
    if (!playing) return
    setTime((t) => {
      const next = t + delta * (speedRef.current as number)
      return next > duration ? duration : next
    })
  })

  const play = () => setPlaying(true)
  const pause = () => setPlaying(false)
  const seek = (t: number) => setTime(Math.max(0, Math.min(duration, t)))
  return { time, playing, play, pause, seek }
}

function HUD({ time, duration, playing, onPlay, onPause, onSeek, onSpeed }: any) {
  return (
    <Html position={[0, 0, 0]} center style={{ width: 420 }}>
      <div className="pointer-events-auto select-none rounded-2xl bg-white/80 shadow-xl border border-gray-200 p-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <button onClick={playing ? onPause : onPlay} className="rounded-xl px-3 py-1.5 text-sm font-medium bg-gray-900 text-white">
            {playing ? 'Pause' : 'Play'}
          </button>
          <input type="range" min={0} max={duration} step={0.01} value={time} onChange={(e) => onSeek(parseFloat((e.target as HTMLInputElement).value))} className="flex-1"/>
          <span className="text-xs font-mono text-gray-700 w-20 text-right">{time.toFixed(1)}s / {duration.toFixed(1)}s</span>
          <select onChange={(e) => onSpeed(parseFloat(e.target.value))} className="ml-2 rounded-md border px-2 py-1 text-sm">
            <option value={0.5}>0.5×</option>
            <option value={1}>1×</option>
            <option value={1.5}>1.5×</option>
            <option value={2}>2×</option>
          </select>
        </div>
      </div>
    </Html>
  )
}

function Scene({ agents, interactions, duration: durationProp }: any) {
  const positions = useCircleLayout(agents, 6)
  const duration = useMemo(() => {
    return durationProp ?? Math.max(6, Math.max(...interactions.map((m: any) => m.t)) + 3)
  }, [interactions, durationProp])

  const [speed, setSpeed] = useState(1)
  const { time, playing, play, pause, seek } = usePlayback(duration, { autoPlay: true, speed })

  return (
    <>
      <ambientLight intensity={0.7} />
      <directionalLight position={[6, 10, 6]} intensity={0.9} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
      <Ground />
      <Ring r={6} />

      {agents.map((a: any) => (
        <AgentAvatar key={a.id} id={a.id} name={a.name} color={a.color} emoji={a.emoji} position={positions.get(a.id) as Vec3} />
      ))}

      {interactions.map((m: any, i: number) => {
        const fromPos = positions.get(m.from)
        const toPos = positions.get(m.to)
        if (!fromPos || !toPos) return null
        const color = m.kind === 'email' ? '#F59E0B' : m.kind === 'tool' ? '#10B981' : '#60A5FA'
        return (
          <MessageOrb key={m.id || i} fromPos={fromPos} toPos={toPos} text={m.text} bornAt={m.t} now={time} color={color} />
        )
      })}

      <HUD time={time} duration={duration} playing={playing} onPlay={play} onPause={pause} onSeek={seek} onSpeed={setSpeed} />

      <OrbitControls enablePan={false} maxPolarAngle={Math.PI/2.1} minDistance={6} maxDistance={18} />
    </>
  )
}

export default function AgentAnimation() {
  const agents = [
    { id: 'agent_alice', name: 'Alice', color: '#34D399', emoji: '🧠' },
    { id: 'agent_bob', name: 'Bob', color: '#93C5FD', emoji: '📨' },
    { id: 'nova_lead', name: 'Nova PM', color: '#F472B6', emoji: '🩺' },
  ]

  const interactions = [
    { from: 'agent_alice', to: 'agent_bob', t: 0.5, text: 'Goal: warm intro + pilot scope', kind: 'chat' },
    { from: 'agent_bob', to: 'nova_lead',  t: 2.0, text: 'Draft outreach…', kind: 'chat' },
    { from: 'agent_bob', to: 'agent_alice', t: 3.4, text: 'Need your availability & redlines', kind: 'chat' },
    { from: 'agent_bob', to: 'human',      t: 4.0, text: 'Escalate: ask controller (email)', kind: 'email' },
    { from: 'agent_alice', to: 'agent_bob', t: 6.5, text: 'Controller replied — finalize', kind: 'chat' },
    { from: 'agent_bob', to: 'nova_lead',  t: 8.2, text: 'Final message w/ constraints', kind: 'chat' },
  ].map((m, i) => ({ id: `evt_${i}`, ...m }))

  const agentsWithHuman = useMemo(() => ([...agents, { id: 'human', name: 'You', color: '#FBBF24', emoji: '🧑' }]), [])

  return (
    <div className="w-full h-[720px] rounded-2xl overflow-hidden border border-gray-200 shadow-sm">
      <Canvas shadows camera={{ position: [0, 9, 12], fov: 45 }}>
        <Suspense fallback={<Html center>Loading…</Html>}>
          <Scene agents={agentsWithHuman} interactions={interactions} />
        </Suspense>
      </Canvas>
    </div>
  )
}


