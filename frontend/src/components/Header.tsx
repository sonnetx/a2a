import React from 'react'
import { Bot, Sparkles, Users } from 'lucide-react'

const Header: React.FC = () => {
  return (
    <header className="glass border-b border-white/10 p-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Bot className="w-8 h-8 text-primary-400" />
            <Users className="w-6 h-6 text-accent-400 absolute -top-1 -right-1" />
            <Sparkles className="w-4 h-4 text-yellow-400 absolute -bottom-1 -left-1 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">A2A Platform</h1>
            <p className="text-sm text-white/70">AI Chatbot & Agent Interaction</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-sm text-white/70">Online</span>
        </div>
      </div>
    </header>
  )
}

export default Header
