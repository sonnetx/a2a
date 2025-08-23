import React from 'react'
import { motion } from 'framer-motion'
import { Bot, User } from 'lucide-react'

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

interface MessageBubbleProps {
  message: Message
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex items-start space-x-3 ${message.isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
        message.isUser 
          ? 'bg-gradient-to-r from-primary-500 to-primary-600' 
          : 'glass border border-white/20'
      }`}>
        {message.isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-primary-400" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex flex-col ${message.isUser ? 'items-end' : 'items-start'} max-w-xs sm:max-w-md lg:max-w-lg`}>
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`message-bubble ${message.isUser ? 'user-message' : 'ai-message'}`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
        </motion.div>
        
        {/* Timestamp */}
        <span className="text-xs text-white/50 mt-1 px-2">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </motion.div>
  )
}

export default MessageBubble
