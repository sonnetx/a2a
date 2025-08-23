import React, { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import AgentInteraction from './components/AgentInteraction'
import TabNavigation from './components/TabNavigation'

function App() {
  const [activeTab, setActiveTab] = useState('chatbot')

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-500/20 rounded-full blur-3xl animate-float" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary-400/10 rounded-full blur-3xl animate-pulse-slow"></div>
      </div>

      {/* Main content */}
      <div className="relative z-10 flex flex-col h-screen">
        {/* Tab Navigation at top */}
        <div className="pt-6 px-4">
          <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
        </div>
        
        {/* Content area takes remaining space */}
        <div className="flex-1 flex items-center justify-center px-4 pb-4">
          {activeTab === 'chatbot' ? <ChatInterface /> : <AgentInteraction />}
        </div>
      </div>
    </div>
  )
}

export default App
