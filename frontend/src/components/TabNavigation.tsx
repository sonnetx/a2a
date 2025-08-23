import React from 'react'
import { Bot, Users, Orbit } from 'lucide-react'
import { motion } from 'framer-motion'

interface TabNavigationProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    {
      id: 'chatbot',
      label: 'AI Chatbot',
      icon: Bot,
      description: 'Chat with AI assistant'
    },
    {
      id: 'agents',
      label: 'Agent Interaction',
      icon: Users,
      description: 'Watch AI agents converse'
    },
    {
      id: 'agent-animation',
      label: 'Agent Animation',
      icon: Orbit,
      description: '3D visualization of agents'
    }
  ]

  return (
    <div className="flex justify-center mb-4">
      <div className="glass rounded-2xl p-2 flex gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          
          return (
            <motion.button
              key={tab.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onTabChange(tab.id)}
              className={`relative px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              <div className="flex items-center gap-2">
                <Icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </div>
              
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-gradient-to-r from-primary-500 to-accent-500 rounded-xl -z-10"
                  initial={false}
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}

export default TabNavigation
