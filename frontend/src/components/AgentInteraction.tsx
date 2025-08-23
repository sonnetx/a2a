import React, { useState, useRef, useEffect } from 'react'
import { Send, Users, Play, Square, RotateCcw, Settings } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface Agent {
  id: string
  name: string
  avatar: string
  personality: string
  isActive: boolean
}

interface ConversationTurn {
  id: string
  agentId: string
  message: string
  timestamp: Date
  turnNumber: number
}

const AgentInteraction: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: '1',
      name: 'Alice',
      avatar: '👩‍💻',
      personality: 'Analytical & Creative',
      isActive: true
    },
    {
      id: '2',
      name: 'Bob',
      avatar: '👨‍🎨',
      personality: 'Artistic & Intuitive',
      isActive: true
    }
  ])

  const [conversation, setConversation] = useState<ConversationTurn[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [currentTurn, setCurrentTurn] = useState(0)
  const [maxTurns, setMaxTurns] = useState(8)
  const [isLoading, setIsLoading] = useState(false)
  const [compatibilityScore, setCompatibilityScore] = useState<number | null>(null)
  
  const conversationEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [conversation])

  const startConversation = async () => {
    if (isRunning) return
    
    setIsRunning(true)
    setIsLoading(true)
    setConversation([])
    setCurrentTurn(0)
    setCompatibilityScore(null)

    // Simulate conversation turns
    for (let turn = 0; turn < maxTurns; turn++) {
      setCurrentTurn(turn + 1)
      
      // Simulate agent responses
      const activeAgents = agents.filter(agent => agent.isActive)
      for (const agent of activeAgents) {
        await new Promise(resolve => setTimeout(resolve, 1500)) // Simulate thinking time
        
        const message = generateAgentMessage(agent, turn)
        const turnData: ConversationTurn = {
          id: Date.now().toString(),
          agentId: agent.id,
          message,
          timestamp: new Date(),
          turnNumber: turn + 1
        }
        
        setConversation(prev => [...prev, turnData])
      }
    }

    // Calculate compatibility score
    setTimeout(() => {
      const score = Math.random() * 0.4 + 0.6 // Random score between 0.6-1.0
      setCompatibilityScore(score)
      setIsLoading(false)
    }, 1000)
  }

  const stopConversation = () => {
    setIsRunning(false)
    setIsLoading(false)
  }

  const resetConversation = () => {
    setConversation([])
    setCurrentTurn(0)
    setCompatibilityScore(null)
    setIsRunning(false)
    setIsLoading(false)
  }

  const generateAgentMessage = (agent: Agent, turn: number): string => {
    const messages = {
      'Alice': [
        "I've been thinking about the intersection of technology and creativity lately. What's your take on it?",
        "That's fascinating! I find that constraints often lead to the most innovative solutions. How do you approach problem-solving?",
        "I love that perspective! There's something beautiful about finding patterns in both art and code. What inspires you most?",
        "That's so true! I believe collaboration between different minds creates magic. How do you stay motivated when facing creative blocks?",
        "What an interesting insight! I think the key is balancing structure with artistic freedom. What's your experience with that?",
        "I'm curious about your creative process. How do you handle criticism of your work?",
        "That's a great point! I find that taking breaks actually helps my creativity flow better too. What's your approach?",
        "I believe every person has a unique artistic voice. What's the most rewarding part of creating something new for you?"
      ],
      'Bob': [
        "I love how art can communicate what words sometimes can't express. Technology is just another medium for creativity, isn't it?",
        "Sometimes the best ideas come when you least expect them. I think intuition plays a huge role in creative decisions.",
        "I find beauty in unexpected places too! Taking risks often leads to the most interesting results. What's your experience?",
        "I completely agree! I think the best collaborations happen when people bring different perspectives. How do you handle creative disagreements?",
        "That's so true! I find that stepping away from a project often gives me fresh insights. What's your creative routine like?",
        "I think criticism can be really valuable when it's constructive. It helps me grow as an artist. How do you process feedback?",
        "I believe creativity is like a muscle - the more you use it, the stronger it gets. What helps you get into a creative flow?",
        "The most rewarding part for me is seeing how my work affects others. It's amazing how art can connect people across different backgrounds."
      ]
    }
    
    const agentMessages = messages[agent.name as keyof typeof messages]
    if (turn < agentMessages.length) {
      return agentMessages[turn]
    }
    
    // Generate contextual responses for longer conversations
    const contextualResponses = [
      "That's a really interesting point. I'd love to explore that idea further.",
      "I never thought about it that way before. It gives me a new perspective.",
      "You know, that reminds me of something I was working on recently.",
      "I think we're really getting to the heart of what makes creativity so powerful.",
      "This conversation is making me think about my own creative process differently."
    ]
    
    return contextualResponses[turn % contextualResponses.length]
  }

  const toggleAgent = (agentId: string) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId ? { ...agent, isActive: !agent.isActive } : agent
    ))
  }

  return (
    <div className="w-full max-w-6xl mx-auto h-[85vh] flex flex-col">
      {/* Control Panel */}
      <div className="glass rounded-2xl p-6 mb-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold gradient-text flex items-center gap-3">
            <Users className="w-7 h-7" />
            Agent Interaction
          </h2>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-white/70">Max Turns:</span>
              <input
                type="number"
                min="1"
                max="20"
                value={maxTurns}
                onChange={(e) => setMaxTurns(parseInt(e.target.value))}
                className="w-16 px-2 py-1 bg-white/10 rounded-lg border border-white/20 text-white text-center"
                disabled={isRunning}
              />
            </div>
            
            {!isRunning ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startConversation}
                disabled={agents.filter(a => a.isActive).length < 2}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl font-semibold text-white shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                Start Conversation
              </motion.button>
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={stopConversation}
                className="flex items-center gap-2 px-6 py-3 bg-red-500 rounded-xl font-semibold text-white shadow-lg hover:shadow-xl transition-all"
              >
                <Square className="w-5 h-5" />
                Stop
              </motion.button>
            )}
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={resetConversation}
              className="flex items-center gap-2 px-4 py-3 bg-white/10 rounded-xl font-semibold text-white border border-white/20 hover:bg-white/20 transition-all"
            >
              <RotateCcw className="w-5 h-5" />
              Reset
            </motion.button>
          </div>
        </div>

        {/* Agent Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agents.map((agent) => (
            <motion.div
              key={agent.id}
              whileHover={{ scale: 1.02 }}
              className={`glass rounded-xl p-4 cursor-pointer transition-all ${
                agent.isActive ? 'ring-2 ring-primary-400' : 'opacity-60'
              }`}
              onClick={() => toggleAgent(agent.id)}
            >
              <div className="flex items-center gap-3">
                <div className="text-3xl">{agent.avatar}</div>
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{agent.name}</h3>
                  <p className="text-sm text-white/70">{agent.personality}</p>
                </div>
                <div className={`w-3 h-3 rounded-full ${agent.isActive ? 'bg-green-400' : 'bg-gray-400'}`}></div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Compatibility Score */}
        {compatibilityScore !== null && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-gradient-to-r from-primary-500/20 to-accent-500/20 rounded-xl border border-white/20"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">Compatibility Score:</span>
              <span className="text-2xl font-bold gradient-text">
                {(compatibilityScore * 100).toFixed(1)}%
              </span>
            </div>
            <div className="mt-2 w-full bg-white/20 rounded-full h-2">
              <div 
                className="h-2 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-1000"
                style={{ width: `${compatibilityScore * 100}%` }}
              ></div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Conversation Display */}
      <div className="glass rounded-3xl flex-1 flex flex-col overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-white/10">
          <h3 className="text-lg font-semibold text-white">
            Conversation {isRunning && `- Turn ${currentTurn}/${maxTurns}`}
          </h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <AnimatePresence>
            {conversation.map((turn, index) => {
              const agent = agents.find(a => a.id === turn.agentId)!
              return (
                <motion.div
                  key={turn.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex gap-3"
                >
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-semibold">
                      {agent.avatar}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-white">{agent.name}</span>
                      <span className="text-xs text-white/50">Turn {turn.turnNumber}</span>
                      <span className="text-xs text-white/50">
                        {turn.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="glass rounded-xl p-3">
                      <p className="text-white/90">{turn.message}</p>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-3 text-white/70"
            >
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>Agents are thinking...</span>
            </motion.div>
          )}
          
          <div ref={conversationEndRef} />
        </div>
      </div>
    </div>
  )
}

export default AgentInteraction
