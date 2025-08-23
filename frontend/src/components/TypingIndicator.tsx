import React from 'react'
import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'

const TypingIndicator: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex items-start space-x-3"
    >
      {/* Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full glass border border-white/20 flex items-center justify-center">
        <Bot className="w-5 h-5 text-primary-400" />
      </div>

      {/* Typing Animation */}
      <div className="glass rounded-2xl px-4 py-3 max-w-xs">
        <div className="flex items-center space-x-1">
          <span className="text-sm text-white/70 mr-2">AI is typing</span>
          <div className="typing-indicator">
            <motion.div
              className="w-2 h-2 bg-primary-400 rounded-full"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
            />
            <motion.div
              className="w-2 h-2 bg-primary-400 rounded-full"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
            />
            <motion.div
              className="w-2 h-2 bg-primary-400 rounded-full"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default TypingIndicator
