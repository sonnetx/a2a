# A2A Chatbot Frontend

A modern, beautiful chatbot interface built with React, TypeScript, and Tailwind CSS. Features a glassmorphism design with AI-themed colors and smooth animations.

## Features

- 🎨 Modern glassmorphism UI design
- 🤖 AI-themed color scheme (blues and purples)
- ✨ Smooth animations with Framer Motion
- 📱 Responsive design
- 💬 Real-time typing indicators
- 🎯 TypeScript for type safety
- ⚡ Fast development with Vite

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd a2a/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit `http://localhost:3000`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Design Features

### Visual Elements
- Glassmorphism effects with backdrop blur
- Gradient backgrounds with floating orbs
- Rounded corners and smooth shadows
- AI-themed blue and purple color palette

### Components
- **Header**: Shows bot status and branding
- **ChatInterface**: Main chat container with message history
- **MessageBubble**: Individual message components for user and AI
- **TypingIndicator**: Animated dots showing AI is responding

### Animations
- Smooth message entry/exit animations
- Floating background elements
- Pulsing status indicators
- Hover effects on interactive elements

## Customization

The color scheme can be customized in `tailwind.config.js`:
- `primary`: Blue tones for main elements
- `accent`: Purple tones for highlights

The glassmorphism effects are defined in `src/index.css` with the `.glass` and `.glass-dark` classes.

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Animations
- **Vite** - Build tool
- **Lucide React** - Icon library
