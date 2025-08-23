# A2A Conversation Simulation Platform

A sophisticated AI-powered platform that simulates conversations between virtual personas, analyzes compatibility, and provides insights into personality dynamics.

## 🚀 Features

- **AI Persona Simulation**: Create and manage detailed virtual personas with rich personality profiles
- **Conversation Engine**: Generate realistic conversations between two personas using advanced AI models
- **Compatibility Analysis**: Score and analyze compatibility between different personality types
- **Web Interface**: Modern React frontend with real-time chat capabilities
- **Profile Management**: Build and customize user profiles from various data sources
- **Research Integration**: Web research capabilities for enhanced conversation context
- **Premium Network Access**: Connect with real people using advanced compatibility matching

## 🏗️ Architecture

### Backend
- **FastAPI**: High-performance Python web framework
- **AI Integration**: Dedalus Labs integration for advanced language models
- **WebSocket Support**: Real-time communication capabilities
- **Personality Tracking**: Dynamic personality analysis and adaptation

### Frontend
- **React 18**: Modern UI framework with TypeScript
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Smooth animations and transitions
- **Responsive Design**: Mobile-friendly interface

## 📁 Project Structure

```
├── api_main.py              # FastAPI backend server
├── main.py                  # CLI conversation runner
├── person_agent.py          # AI persona management
├── conversation_manager.py   # Conversation orchestration
├── personality_tracker.py   # Personality analysis
├── compatibility.py         # Compatibility scoring
├── frontend/                # React web application
│   ├── src/
│   │   ├── components/      # React components
│   │   └── App.tsx         # Main application
│   └── package.json        # Frontend dependencies
├── profiles/                # Persona profile definitions
├── scrapers/                # Data extraction tools
└── users.json              # User configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Dedalus Labs API key

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DEDALUS_API_KEY="your_api_key_here"

# Run the API server
python api_main.py
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### CLI Usage
```bash
# Run a conversation simulation
python main.py --profile1 profiles/person_alice.json --profile2 profiles/person_bob.json

# With custom parameters
python main.py --profile1 alice.json --profile2 bob.json --max-turns 15 --enable-research
```

## 💬 Usage Examples

### Creating Personas
```python
from person_agent import PersonAgent

# Load from JSON profile
agent = PersonAgent.from_file("profiles/person_alice.json", client, model)

# Create custom profile
profile = {
    "name": "Alice",
    "age": 28,
    "occupation": "Software Engineer",
    "personality": {
        "traits": ["analytical", "creative", "ambitious"],
        "interests": ["technology", "art", "travel"]
    }
}
```

### Running Conversations
```python
from conversation_manager import ConversationManager

# Initialize conversation
manager = ConversationManager(agent1, agent2)

# Start conversation
results = await manager.start_conversation(
    max_turns=10,
    enable_research=True
)
```

## 🔧 Configuration

### Environment Variables
- `DEDALUS_API_KEY`: Your Dedalus Labs API key
- `MODEL_NAME`: AI model to use (default: "openai/gpt-4o")
- `MAX_TURNS`: Maximum conversation turns (default: 10)

### Profile Format
Personas are defined in JSON format with the following structure:
```json
{
    "name": "Person Name",
    "age": 25,
    "occupation": "Job Title",
    "personality": {
        "traits": ["trait1", "trait2"],
        "interests": ["interest1", "interest2"],
        "goals": ["goal1", "goal2"]
    },
    "background": {
        "education": "Degree",
        "location": "City",
        "family": "Family status"
    }
}
```

## 🌐 API Endpoints

- `POST /conversation/start`: Start a new conversation
- `GET /profiles`: List available personas
- `POST /profiles`: Create new persona
- `WebSocket /ws/{session_id}`: Real-time conversation updates

## 🎯 Use Cases

- **Social Networking**: Connect real people based on compatibility
- **Dating & Relationships**: Match people using advanced algorithms
- **Professional Networking**: Connect professionals with similar interests
- **Community Building**: Create meaningful connections
- **Research & Development**: Study human connection patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [Dedalus Labs](https://dedalus.ai/) - AI model provider
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://reactjs.org/) - Frontend framework

## 📞 Support

For questions or support, please open an issue on GitHub or contact the development team.
