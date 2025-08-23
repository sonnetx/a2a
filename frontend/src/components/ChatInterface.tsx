import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your AI assistant. How can I help you today?',
      isUser: false,
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const simulateAIResponse = (userMessage: string) => {
    const responses = [
      "That's an interesting question! Let me think about that...",
      "I understand what you're asking. Here's my perspective on that topic.",
      "Great question! I'd be happy to help you with that.",
      "That's a fascinating topic. Let me share some insights with you.",
      "I see what you mean. Let me provide some useful information about that.",
    ]
    
    const randomResponse = responses[Math.floor(Math.random() * responses.length)]
    return `${randomResponse} You mentioned: "${userMessage}". I'm here to assist you with any questions or tasks you might have!`
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response delay
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000))

    const aiResponse: Message = {
      id: (Date.now() + 1).toString(),
      text: simulateAIResponse(userMessage.text),
      isUser: false,
      timestamp: new Date()
    }

    setIsTyping(false)
    setMessages(prev => [...prev, aiResponse])
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto h-[80vh] flex flex-col">
      {/* Chat Container */}
      <div className="glass rounded-3xl flex-1 flex flex-col overflow-hidden shadow-2xl">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </AnimatePresence>
          
          {isTyping && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-white/10">
          <div className="flex items-end space-x-4">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message here..."
                className="w-full glass-dark rounded-2xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-primary-400/50 placeholder-white/50 text-white min-h-[50px] max-h-32"
                rows={1}
              />
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white rounded-2xl p-3 transition-all duration-200 shadow-lg"
            >
              {isTyping ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
