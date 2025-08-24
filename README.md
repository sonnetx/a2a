# YC AI Agents Hackathon: Bubblies

Bubblies is an AI networking area that simulates networking interactions between autonomous agents representing humans. Agents chat naturally, discover shared interests, and organically determine compatibility through conversation. Our stack includes AgentMail and Dedalus Labs, and it features MCP integration for automated research, intelligent conversation analysis, and compatibility-based email notifications.

## 🚀 Features

- **AI Persona Simulation**: Create and manage detailed virtual personas with personality profiles
- **Conversation Engine**: Generate realistic conversations between two personas based on use configured profiles
- **Compatibility Analysis**: Score and analyze compatibility between communication patterns and shared interest overlap metrics
- **Web Interface**: React frontend with chat interface and 3.js agent arena
- **Profile Management**: Build and customize user profiles from various data sources (LinkedIn Scraping)
- **Research Integration**: Web research capabilities through MCP for enhanced conversation context

Here's the expanded architecture section with more details:

## 🏗️ Architecture

### Backend
- **FastAPI**: High-performance Python web framework with automatic API documentation and async/await support
- **AI Integration**: Dedalus Labs integration for advanced language models (GPT-4, Claude) and MCP with streaming responses and context management
- **WebSocket Support**: Real-time bidirectional communication for live conversation updates and instant compatibility notifications
- **MCP Protocol**: Model Context Protocol integration enabling seamless tool connectivity and extensible agent capabilities
- **AgentMail**: Automated agent email system for compatibility reports and conversation summaries
- **Background Tasks**: Celery/asyncio for handling research tasks, email sending, and statistical analysis

### AI & Analytics Engine
- **Conversation Analysis**: Natural language processing for sentiment analysis, topic extraction, and engagement scoring
- **Compatibility Algorithms**: Multi-dimensional scoring using personality trait correlation matrices and behavioral pattern matching
- **Statistical Processing**: Real-time calculation of compatibility indices, confidence intervals, and predictive modeling
- **Research Capabilities**: Autonomous web research integration for agent background knowledge expansion
- **Memory Management**: Conversation context optimization with sliding window approaches for long-term interactions

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

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [Dedalus Labs](https://dedalus.ai/) - AI model provider
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://reactjs.org/) - Frontend framework

