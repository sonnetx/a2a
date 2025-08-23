import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Lock, Crown } from 'lucide-react'
import PaymentModal from './PaymentModal'

interface Persona {
  id: string
  name: string
  age: number
  occupation: string
  personality: string[]
  interests: string[]
  avatar: string
  compatibility: number
}

const NetworkAccess: React.FC = () => {
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [hasAccess, setHasAccess] = useState(false)

  // Sample personas (in a real app, these would come from the backend)
  const samplePersonas: Persona[] = [
    {
      id: '1',
      name: 'Alice Chen',
      age: 28,
      occupation: 'Software Engineer',
      personality: ['Analytical', 'Creative', 'Ambitious'],
      interests: ['Technology', 'Rock Climbing', 'Photography'],
      avatar: '👩‍💻',
      compatibility: 0.85
    },
    {
      id: '2',
      name: 'Bob Smith',
      age: 32,
      occupation: 'Marketing Director',
      personality: ['Extroverted', 'Strategic', 'Empathetic'],
      interests: ['Business', 'Travel', 'Cooking'],
      avatar: '👨‍💼',
      compatibility: 0.72
    },
    {
      id: '3',
      name: 'Emma Rodriguez',
      age: 25,
      occupation: 'UX Designer',
      personality: ['Creative', 'Detail-oriented', 'User-focused'],
      interests: ['Design', 'Art', 'Psychology'],
      avatar: '👩‍🎨',
      compatibility: 0.91
    },
    {
      id: '4',
      name: 'David Kim',
      age: 29,
      occupation: 'Data Scientist',
      personality: ['Logical', 'Curious', 'Collaborative'],
      interests: ['AI/ML', 'Chess', 'Hiking'],
      avatar: '👨‍🔬',
      compatibility: 0.78
    },
    {
      id: '5',
      name: 'Sophie Williams',
      age: 27,
      occupation: 'Product Manager',
      personality: ['Organized', 'Visionary', 'Team-oriented'],
      interests: ['Innovation', 'Reading', 'Yoga'],
      avatar: '👩‍💼',
      compatibility: 0.88
    },
    {
      id: '6',
      name: 'Michael Chen',
      age: 31,
      occupation: 'Financial Analyst',
      personality: ['Analytical', 'Risk-aware', 'Goal-driven'],
      interests: ['Finance', 'Golf', 'Wine'],
      avatar: '👨‍💼',
      compatibility: 0.65
    }
  ]

  const handlePaymentSuccess = () => {
    setHasAccess(true)
  }

  const getCompatibilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }



  if (hasAccess) {
    return (
      <div className="w-full max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center gap-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-3 rounded-full mb-4">
            <Crown className="w-5 h-5" />
            <span className="font-semibold">Premium Access Active</span>
          </div>
                  <h1 className="text-3xl font-bold text-white mb-4">Premium Network</h1>
        <p className="text-white/70 max-w-xl mx-auto">
          Connect with our curated collection of people, each with unique personalities and conversation styles.
        </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {samplePersonas.map((persona, index) => (
            <motion.div
              key={persona.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="glass rounded-xl p-4 hover:scale-105 transition-all duration-200 cursor-pointer group"
            >
              <div className="text-center mb-3">
                <div className="text-3xl mb-2">{persona.avatar}</div>
                <h3 className="text-lg font-bold text-white mb-1">{persona.name}</h3>
                <p className="text-white/70 text-sm">{persona.occupation}</p>
              </div>

              <div className="flex flex-wrap gap-1 mb-3 justify-center">
                {persona.personality.slice(0, 2).map((trait, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-white/10 rounded text-xs text-white/80"
                  >
                    {trait}
                  </span>
                ))}
              </div>

              <div className="text-center">
                <span className={`text-sm font-medium ${getCompatibilityColor(persona.compatibility)}`}>
                  {Math.round(persona.compatibility * 100)}% Match
                </span>
              </div>

              <button className="w-full mt-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium py-2 px-4 rounded-lg hover:from-primary-600 hover:to-accent-600 transition-all duration-200 opacity-0 group-hover:opacity-100">
                Chat Now
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-3xl mx-auto text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="inline-flex items-center gap-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white px-6 py-3 rounded-full mb-6">
          <Crown className="w-5 h-5" />
          <span className="font-semibold">Premium Network Access</span>
        </div>
        
        <h1 className="text-3xl font-bold text-white mb-4">
          Unlock Premium Network
        </h1>
        
        <p className="text-white/70 max-w-xl mx-auto mb-8">
          Access our curated collection of people with advanced compatibility matching and unlimited conversations.
        </p>
      </motion.div>

      {/* Preview Grid */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        {samplePersonas.slice(0, 6).map((persona, index) => (
          <motion.div
            key={persona.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            className="glass rounded-lg p-3 relative group"
          >
            <div className="text-center">
              <div className="text-2xl mb-1 opacity-40">{persona.avatar}</div>
              <h3 className="text-xs font-medium text-white/60 mb-1">{persona.name}</h3>
              <p className="text-xs text-white/40">{persona.occupation}</p>
            </div>
            
            {/* Lock Overlay */}
            <div className="absolute inset-0 bg-black/60 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Lock className="w-4 h-4 text-white/70" />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Simple CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass rounded-xl p-6"
      >
        <div className="text-center mb-4">
          <div className="text-3xl font-bold text-white mb-1">$0.50</div>
          <p className="text-white/70">One-time unlock</p>
        </div>
        
        <button
          onClick={() => setShowPaymentModal(true)}
          className="w-full bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold py-3 px-6 rounded-lg hover:from-primary-600 hover:to-accent-600 transition-all duration-200"
        >
          <Crown className="w-4 h-4 inline mr-2" />
          Get Premium Access
        </button>
        
        <p className="text-white/50 text-xs mt-3">
          Secure payment • Instant access
        </p>
      </motion.div>

      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        onPaymentSuccess={handlePaymentSuccess}
      />
    </div>
  )
}

export default NetworkAccess
