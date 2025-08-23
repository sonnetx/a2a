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

function AgentAvatar({ id, name, color = '#6EE7B7', emoji = '🤖', position, isActive = false, currentMessage = null }: { 
  id: string, 
  name?: string, 
  color?: string, 
  emoji?: string, 
  position: Vec3,
  isActive?: boolean,
  currentMessage?: string | null
}) {
  const group = useRef<any>()
  useFrame(({ clock }) => {
    if (group.current) {
      const tilt = Math.sin(clock.getElapsedTime() * 1.3) * 0.06
      group.current.rotation.y = tilt
    }
  })

  // Bubble sizing tuned for a wide horizontal rectangle
  const messageLength = currentMessage ? currentMessage.length : 0
  const bubbleWidth = Math.min(messageLength * 0.06 + 1.6, 5.8)
  const bubbleHeight = 1.05
  const textMaxWidth = Math.max(bubbleWidth - 0.35, 1.2)
  const tailY = -bubbleHeight / 2 - 0.08
  return (
    <group ref={group} position={position}>
      <mesh castShadow receiveShadow>
        <sphereGeometry args={[0.6, 32, 32]} />
        <meshStandardMaterial opacity={isActive ? 1.0 : 0.6} transparent>
          <GradientTexture stops={[0, 0.5, 1]} colors={['white', color, '#ffffff']} size={1024} />
        </meshStandardMaterial>
      </mesh>

      <Billboard position={[0, 0.85, 0]}>
        <Text fontSize={0.35} anchorX="center" anchorY="middle">{emoji}</Text>
      </Billboard>

      <Billboard position={[0, -1.0, 0]}>
        <Text fontSize={0.28} color={isActive ? "#2b2b2b" : "#666666"} outlineColor="#ffffff" outlineWidth={0.015}>
          {name || id}
        </Text>
      </Billboard>

      {/* Speech Bubble */}
      {currentMessage && (
        <Billboard position={[0, 1.8, 0]}>
          <group>
            {/* Shadow */}
            <mesh position={[0.05, -0.05, -0.03]}>
              <planeGeometry args={[bubbleWidth + 0.2, bubbleHeight + 0.2]} />
              <meshBasicMaterial color="#000000" opacity={0.08} transparent />
            </mesh>

            {/* Border */}
            <mesh position={[0, 0, -0.005]}>
              <planeGeometry args={[bubbleWidth + 0.08, bubbleHeight + 0.08]} />
              <meshBasicMaterial color="#e6ebf0" opacity={0.9} transparent />
            </mesh>

            {/* Background */}
            <mesh position={[0, 0, -0.01]}
                  scale={[1, 1, 1]}
            >
              <planeGeometry args={[bubbleWidth, bubbleHeight]} />
              <meshBasicMaterial color="#ffffff" opacity={0.98} transparent />
            </mesh>

            {/* Tail */}
            <mesh position={[0, tailY, -0.01]}>
              <coneGeometry args={[0.08, 0.18, 3]} />
              <meshBasicMaterial color="#ffffff" opacity={0.98} transparent />
            </mesh>
            
            {/* Text */}
            <Text
              fontSize={0.14}
              maxWidth={textMaxWidth}
              lineHeight={1.28}
              color="#1e293b"
              anchorX="center"
              anchorY="middle"
              textAlign="center"
            >
              {currentMessage.length > 220 ? currentMessage.substring(0, 220) + '...' : currentMessage}
            </Text>
          </group>
        </Billboard>
      )}

      {isActive && <Sparkle position={[0.9, 0.2, 0]} />}
    </group>
  )
}

function MessageOrb({ fromPos, toPos, text, bornAt, duration = 3.0, height = 1.5, color = '#60A5FA', now }: {
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
          <Text fontSize={0.18} maxWidth={3} lineHeight={1.2} color="#1f2937" anchorX="center" anchorY="middle">
            {text.length > 100 ? text.substring(0, 100) + '...' : text}
          </Text>
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

function FakeAgents() {
  const fakePositions: Vec3[] = useMemo(() => ([
    [-12, 0, 12],
    [10, 0, -8],
    [14, 0, 4],
    [-15, 0, -10],
    [6, 0, 14],
    [-6, 0, -14],
    [0, 0, 16],
  ]), [])

  const colors = ['#CBD5E1', '#D1FAE5', '#BFDBFE', '#FDE68A', '#FBCFE8', '#A7F3D0', '#E9D5FF']

  return (
    <group>
      {fakePositions.map((p, i) => (
        <AgentAvatar
          key={`fake_${i}`}
          id={`fake_${i}`}
          name=""
          color={colors[i % colors.length]}
          emoji=""
          position={p}
          isActive={false}
          currentMessage={null}
        />
      ))}
    </group>
  )
}

// Types for real conversation data
interface ConversationMessage {
  id: string
  speaker: string
  message: string
  timestamp: number
  turnNumber: number
}

interface Agent {
  id: string
  name: string
  occupation?: string
  color: string
  emoji: string
  isActive: boolean
}

interface ConversationUpdate {
  conversation_id: string
  speaker: string
  message: string
  turn_number: number
  is_finished: boolean
}

// Removed ConversationControls overlay per request

function Scene({ agents, messages }: any) {
  const positions = useCircleLayout(agents, 6)
  const [currentTime, setCurrentTime] = useState(0)
  const [agentMessages, setAgentMessages] = useState<{[key: string]: string}>({})

  useFrame((_, delta) => {
    setCurrentTime(t => t + delta)
  })

  // Update agent messages when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1]
      setAgentMessages(prev => ({
        ...prev,
        [latestMessage.speaker]: latestMessage.message
      }))
      
      // Clear message after 5 seconds
      setTimeout(() => {
        setAgentMessages(prev => {
          const updated = { ...prev }
          delete updated[latestMessage.speaker]
          return updated
        })
      }, 5000)
    }
  }, [messages])

  return (
    <>
      <ambientLight intensity={0.7} />
      <directionalLight position={[6, 10, 6]} intensity={0.9} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
      <Ground />
      <Ring r={6} />
      <FakeAgents />

      {agents.map((agent: Agent) => (
        <AgentAvatar 
          key={agent.id} 
          id={agent.id} 
          name={agent.name} 
          color={agent.color} 
          emoji={agent.emoji} 
          position={positions.get(agent.id) as Vec3}
          isActive={agent.isActive}
          currentMessage={agentMessages[agent.name] || null}
        />
      ))}

      {messages.map((message: ConversationMessage) => {
        // Find speaker and target for message flow
        const speakerAgent = agents.find((a: Agent) => a.name === message.speaker)
        const otherAgents = agents.filter((a: Agent) => a.name !== message.speaker && a.isActive)
        
        if (!speakerAgent || otherAgents.length === 0) return null
        
        const fromPos = positions.get(speakerAgent.id)
        const toPos = positions.get(otherAgents[0].id) // Send to first other active agent
        
        if (!fromPos || !toPos) return null
        
        return (
          <MessageOrb 
            key={message.id} 
            fromPos={fromPos} 
            toPos={toPos} 
            text={message.message} 
            bornAt={message.timestamp} 
            now={currentTime}
            color={speakerAgent.color}
            duration={4.0}
          />
        )
      })}

      {/* Controls removed from scene */}

      <OrbitControls enablePan={false} maxPolarAngle={Math.PI/2.1} minDistance={6} maxDistance={18} />
    </>
  )
}

export default function AgentAnimation() {
  // WebSocket connection state
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [sessionId] = useState(() => `animation_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  
  // Conversation state
  // Fixed profiles: Michael (my_agent) and Alice (person_alice)
  const [availableProfiles, setAvailableProfiles] = useState<{[key: string]: any}>({})
  const [isRunning, setIsRunning] = useState(false)
  const [messages, setMessages] = useState<ConversationMessage[]>([])

  
  // Agent state - dynamic based on conversation
  const [agents, setAgents] = useState<Agent[]>([
    { id: 'user', name: 'You', color: '#FBBF24', emoji: '🧑', isActive: false },
  ])

  // Load profiles and setup WebSocket on mount
  useEffect(() => {
    loadProfiles()
    connectWebSocket()
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [])

  const loadProfiles = async () => {
    try {
      const backendUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8000' 
        : ''
      
      const response = await fetch(`${backendUrl}/api/profiles`)
      const data = await response.json()
      setAvailableProfiles(data.profiles)
      console.log('Loaded profiles:', data.profiles)
      // Set the local user agent's display name to match my_agent profile
      const myName = data.profiles?.['my_agent']?.name
      if (myName) {
        setAgents(prev => [{ ...prev[0], name: myName }, ...prev.slice(1)])
      }
    } catch (error) {
      console.error('Error loading profiles:', error)
    }
  }

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80')
    
    // For development, assume backend is on port 8000
    const backendPort = host === 'localhost' || host === '127.0.0.1' ? '8000' : port
    const wsUrl = `${protocol}//${host}:${backendPort}/ws/${sessionId}`
    
    console.log('Attempting WebSocket connection to:', wsUrl)
    setConnectionStatus('connecting')
    
    const websocket = new WebSocket(wsUrl)
    
    websocket.onopen = () => {
      setConnectionStatus('connected')
      console.log('WebSocket connected for animation:', wsUrl)
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message received:', data)
      handleWebSocketMessage(data)
    }
    
    websocket.onclose = (event) => {
      setConnectionStatus('disconnected')
      console.log('WebSocket disconnected:', event.code, event.reason)
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnectionStatus('disconnected')
    }
    
    setWs(websocket)
  }

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'conversation_update') {
      const update: ConversationUpdate = data.data
      
      if (update.speaker === 'system') {
        // Handle system messages
        if (update.is_finished) {
          setIsRunning(false)

        }
        return
      }
      
      // Add message to animation
      const message: ConversationMessage = {
        id: `${update.conversation_id}_${update.turn_number}`,
        speaker: update.speaker,
        message: update.message,
        timestamp: Date.now() / 1000, // Convert to seconds for animation timing
        turnNumber: update.turn_number
      }
      
      setMessages(prev => [...prev, message])
      

      
      // Update agent activity
      setAgents(prev => prev.map(agent => ({
        ...agent,
        isActive: agent.name === update.speaker || agent.name === 'You'
      })))
    }
  }

  const startConversation = async () => {
    if (isRunning || connectionStatus !== 'connected') return
    
    setIsRunning(true)
    setMessages([])


    // Use fixed IDs: my_agent (user) and person_alice (target)
    const targetProfile = availableProfiles['person_alice']
    if (targetProfile) {
      const newAgent: Agent = {
        id: 'person_alice',
        name: targetProfile.name,
        color: '#93C5FD', // Blue for conversation partner
        emoji: '🤖',
        isActive: true
      }
      
      setAgents(prev => [
        { ...prev[0], isActive: true, name: availableProfiles['my_agent']?.name || prev[0].name },
        newAgent
      ])
    }

    try {
      const backendUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8000' 
        : ''
      
      // Directly start conversation using fixed user_profile_id = 'my_agent' and target 'person_alice'
      const response = await fetch(`${backendUrl}/api/conversation/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          target_profile_id: 'person_alice',
          user_profile_id: 'my_agent',
          max_turns: 8,
          enable_research: true
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to start conversation: ${response.status} - ${errorText}`)
      }

      const result = await response.json()
      console.log('Animation conversation started:', result)
      
    } catch (error) {
      console.error('Error starting conversation:', error)
      setIsRunning(false)
    }
  }

  // ensureAnimationProfile no longer needed; using predefined my_agent

  const stopConversation = () => {
    setIsRunning(false)
  }

  // Reset handled implicitly by starting/stopping; explicit button removed

  return (
    <div className="w-full h-[720px] rounded-2xl overflow-hidden border border-gray-200 shadow-sm relative">
      <Canvas shadows camera={{ position: [0, 9, 12], fov: 45 }}>
        <Suspense fallback={<Html center>Loading…</Html>}>
          <Scene 
            agents={agents}
            messages={messages}
          />
        </Suspense>
      </Canvas>

      {/* Connection status - top right of screen */}
      <div className="fixed top-3 right-3 z-50">
        <span className={`px-3 py-1.5 rounded-full text-xs font-semibold shadow-sm ${
          connectionStatus === 'connected' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' :
          connectionStatus === 'connecting' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
          'bg-red-100 text-red-700 border border-red-200'
        }`}>
          {connectionStatus}
        </span>
      </div>

      {/* Start button - bottom center of screen */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
        {!isRunning ? (
          <button
            onClick={startConversation}
            disabled={connectionStatus !== 'connected'}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:from-slate-300 disabled:to-slate-400 disabled:cursor-not-allowed font-semibold shadow-lg transition-all duration-200"
          >
            ▶️ Start Conversation
          </button>
        ) : (
          <button
            onClick={stopConversation}
            className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl hover:from-red-700 hover:to-red-800 font-semibold shadow-lg transition-all duration-200"
          >
            ⏹️ Stop
          </button>
        )}
      </div>
    </div>
  )
}