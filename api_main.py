#!/usr/bin/env python3
"""
FastAPI backend for conversation simulation platform.
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from dedalus_labs import AsyncDedalus
from person_agent import PersonAgent
from conversation_manager import ConversationManager
from api_router.profile_convo_api import chat_with_claude, get_conversation_history, clear_conversation_history, ChatMessage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Conversation Simulation API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_connections: Dict[str, WebSocket] = {}
user_sessions: Dict[str, Dict] = {}
predefined_profiles: Dict[str, Dict] = {}
active_conversations: Dict[str, ConversationManager] = {}


# ===== Models =====

class UserMessage(BaseModel):
    message: str
    session_id: str


class UserProfile(BaseModel):
    name: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    hobbies: List[str] = []
    personality_traits: List[str] = []
    interests: List[str] = []
    goals: List[str] = []
    location: Optional[str] = None
    education: Optional[str] = None


class ConversationRequest(BaseModel):
    session_id: str
    target_profile_id: str
    # Optional: if provided, use a predefined profile for the user instead of session profile
    user_profile_id: Optional[str] = None
    max_turns: int = 8
    enable_research: bool = False
    message_pause_seconds: float = 2.5


class ChatResponse(BaseModel):
    message: str
    message_type: str  # 'bot', 'user', 'system'
    timestamp: str
    session_id: str


class ConversationUpdate(BaseModel):
    conversation_id: str
    speaker: str
    message: str
    compatibility_scores: Optional[Dict[str, float]] = None
    turn_number: int
    is_finished: bool = False


# ===== Startup and Profile Management =====

@app.on_event("startup")
async def startup_event():
    """Load predefined profiles on startup"""
    await load_predefined_profiles()


async def load_predefined_profiles():
    """Load predefined profiles from profiles directory"""
    global predefined_profiles
    # Resolve profiles directory relative to this file to avoid CWD issues
    profiles_dir = (Path(__file__).parent / "profiles").resolve()
    
    for profile_file in profiles_dir.glob("*.json"):
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                profile_id = profile_file.stem
                predefined_profiles[profile_id] = profile_data
                logger.info(f"Loaded profile: {profile_data.get('name', profile_id)}")
        except Exception as e:
            logger.error(f"Error loading profile {profile_file}: {e}")

# ===== WebSocket Connection Management =====

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    
    # Initialize session if it doesn't exist
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            "profile": None,
            "chat_history": [],
            "profile_building_stage": "initial",
            "created_at": datetime.now().isoformat()
        }
    
    try:
        # Send welcome message
        await send_message_to_session(session_id, {
            "message": "Hello! I'm here to help you create your profile and then watch you chat with other personalities. What's your name?",
            "message_type": "bot",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        })
        
        while True:
            data = await websocket.receive_json()
            await handle_chat_message(session_id, data.get("message", ""))
            
    except WebSocketDisconnect:
        logger.info(f"Client {session_id} disconnected")
        if session_id in active_connections:
            del active_connections[session_id]


async def send_message_to_session(session_id: str, message_data: Dict):
    """Send message to specific session"""
    if session_id in active_connections:
        try:
            await active_connections[session_id].send_json(message_data)
        except Exception as e:
            logger.error(f"Error sending message to {session_id}: {e}")


# ===== Chat Handler =====

class ProfileBuilder:
    """Handles the profile building conversation flow"""
    
    def __init__(self):
        self.stages = [
            "initial",      # Get name
            "age",          # Get age
            "occupation",   # Get occupation
            "hobbies",      # Get hobbies
            "personality",  # Get personality traits
            "goals",        # Get goals
            "location",     # Get location
            "complete"      # Profile complete
        ]
    
    async def process_message(self, session_id: str, message: str) -> str:
        """Process user message and return bot response"""
        session = user_sessions[session_id]
        stage = session.get("profile_building_stage", "initial")
        
        if stage == "initial":
            return await self._handle_name(session_id, message)
        elif stage == "age":
            return await self._handle_age(session_id, message)
        elif stage == "occupation":
            return await self._handle_occupation(session_id, message)
        elif stage == "hobbies":
            return await self._handle_hobbies(session_id, message)
        elif stage == "personality":
            return await self._handle_personality(session_id, message)
        elif stage == "goals":
            return await self._handle_goals(session_id, message)
        elif stage == "location":
            return await self._handle_location(session_id, message)
        elif stage == "complete":
            return await self._handle_general_chat(session_id, message)
        
        return "I'm not sure how to help with that. Let's continue building your profile!"
    
    async def _handle_name(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        if not session["profile"]:
            session["profile"] = {}
        
        session["profile"]["name"] = message.strip()
        session["profile_building_stage"] = "age"
        return f"Nice to meet you, {message.strip()}! How old are you?"
    
    async def _handle_age(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        try:
            age = int(message.strip())
            session["profile"]["age"] = age
            session["profile_building_stage"] = "occupation"
            return "Great! What's your occupation or what do you do for work?"
        except ValueError:
            return "Please enter a valid age (just the number)."
    
    async def _handle_occupation(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        session["profile"]["occupation"] = message.strip()
        session["profile_building_stage"] = "hobbies"
        return "Interesting! What are your hobbies or interests? (You can list several, separated by commas)"
    
    async def _handle_hobbies(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        hobbies = [h.strip() for h in message.split(",") if h.strip()]
        session["profile"]["hobbies"] = hobbies
        session["profile_building_stage"] = "personality"
        return "Cool hobbies! How would you describe your personality? (e.g., creative, analytical, social, adventurous)"
    
    async def _handle_personality(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        traits = [t.strip() for t in message.split(",") if t.strip()]
        if not session["profile"].get("personality"):
            session["profile"]["personality"] = {}
        session["profile"]["personality"]["traits"] = traits
        session["profile_building_stage"] = "goals"
        return "Perfect! What are some of your goals or aspirations? (separate multiple goals with commas)"
    
    async def _handle_goals(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        goals = [g.strip() for g in message.split(",") if g.strip()]
        session["profile"]["personality"]["goals"] = goals
        session["profile_building_stage"] = "location"
        return "Awesome goals! Where are you located (city/state or country)?"
    
    async def _handle_location(self, session_id: str, message: str) -> str:
        session = user_sessions[session_id]
        if not session["profile"].get("background"):
            session["profile"]["background"] = {}
        session["profile"]["background"]["location"] = message.strip()
        session["profile_building_stage"] = "complete"
        
        # Format the complete profile
        profile = session["profile"]
        summary = f"""
Perfect! Your profile is complete:

**Name:** {profile.get('name', 'N/A')}
**Age:** {profile.get('age', 'N/A')}
**Occupation:** {profile.get('occupation', 'N/A')}
**Location:** {profile.get('background', {}).get('location', 'N/A')}
**Hobbies:** {', '.join(profile.get('hobbies', []))}
**Personality:** {', '.join(profile.get('personality', {}).get('traits', []))}
**Goals:** {', '.join(profile.get('personality', {}).get('goals', []))}

Now you can start conversations with other personalities! Type 'start conversation' to see available profiles, or just chat with me about anything.
"""
        return summary
    
    async def _handle_general_chat(self, session_id: str, message: str) -> str:
        """Handle general chat after profile is complete"""
        message_lower = message.lower().strip()
        
        if "start conversation" in message_lower or "available profiles" in message_lower:
            profiles_list = []
            for profile_id, profile_data in predefined_profiles.items():
                name = profile_data.get('name', profile_id)
                occupation = profile_data.get('occupation', 'Unknown')
                profiles_list.append(f"• **{name}** ({occupation}) - ID: `{profile_id}`")
            
            profiles_text = "\n".join(profiles_list)
            return f"""Here are the available personalities you can chat with:

{profiles_text}

To start a conversation, use the bot control panel on the right side of the screen, or tell me which profile you'd like to chat with!"""
        
        # Simple responses for general chat
        responses = [
            "That's interesting! Feel free to start a conversation with one of our personalities.",
            "I'd love to hear more! You can also begin chatting with other profiles whenever you're ready.",
            "Thanks for sharing! Ready to see how you'd get along with our other personalities?",
            "That sounds great! Want to try a conversation with one of our available profiles?"
        ]
        
        import random
        return random.choice(responses)


profile_builder = ProfileBuilder()


async def handle_chat_message(session_id: str, message: str):
    """Handle incoming chat messages"""
    session = user_sessions[session_id]
    
    # Add user message to history
    user_msg = {
        "message": message,
        "message_type": "user",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    }
    session["chat_history"].append(user_msg)
    
    # Send user message back to confirm receipt
    await send_message_to_session(session_id, user_msg)
    
    # Process message and get bot response
    try:
        bot_response = await profile_builder.process_message(session_id, message)
        
        bot_msg = {
            "message": bot_response,
            "message_type": "bot",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        session["chat_history"].append(bot_msg)
        
        # Send bot response
        await send_message_to_session(session_id, bot_msg)
        
    except Exception as e:
        logger.error(f"Error processing message for {session_id}: {e}")
        error_msg = {
            "message": "Sorry, I encountered an error. Please try again.",
            "message_type": "system",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        await send_message_to_session(session_id, error_msg)


# ===== REST API Endpoints =====

@app.get("/")
async def get_index():
    """Serve a simple API status page since frontend will be separate"""
    return {
        "message": "Personality Chat Simulator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "websocket": "/ws/{session_id}",
            "profiles": "/api/profiles",
            "session": "/api/session/{session_id}",
            "start_conversation": "/api/conversation/start",
            "chat": "/api/chat",
            "chat_history": "/api/chat/history/{user_id}",
            "clear_history": "/api/chat/history/{user_id}",
            "docs": "/docs"
        },
        "frontend_note": "Frontend should be deployed separately using v0 or your preferred React framework"
    }


@app.get("/api/profiles")
async def get_profiles():
    """Get list of available predefined profiles"""
    return {"profiles": predefined_profiles}


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "profile": user_sessions[session_id].get("profile"),
        "profile_complete": user_sessions[session_id].get("profile_building_stage") == "complete",
        "chat_history": user_sessions[session_id].get("chat_history", [])
    }


@app.post("/api/conversation/start")
async def start_conversation(request: ConversationRequest, background_tasks: BackgroundTasks):
    """Start a conversation between user's profile and a target profile"""
    if request.session_id not in user_sessions:
        # Initialize a minimal session so streaming works even without chat/profile building
        user_sessions[request.session_id] = {
            "profile": None,
            "chat_history": [],
            "profile_building_stage": "complete" if request.user_profile_id else "initial",
            "created_at": datetime.now().isoformat()
        }
    
    session = user_sessions[request.session_id]
    
    # Validate or resolve the user profile source
    user_profile_data: Optional[Dict[str, Any]] = None
    if request.user_profile_id:
        if request.user_profile_id not in predefined_profiles:
            raise HTTPException(status_code=404, detail="User profile id not found")
        user_profile_data = predefined_profiles[request.user_profile_id]
    else:
        if not session.get("profile") or session.get("profile_building_stage") != "complete":
            raise HTTPException(status_code=400, detail="User profile not complete")
        user_profile_data = session["profile"]
    
    if request.target_profile_id not in predefined_profiles:
        raise HTTPException(status_code=404, detail="Target profile not found")
    
    conversation_id = str(uuid.uuid4())
    
    # Schedule the conversation to run in the background
    background_tasks.add_task(
        run_conversation_background,
        conversation_id,
        request.session_id,
        request.target_profile_id,
        request.max_turns,
        request.enable_research,
        request.message_pause_seconds,
        user_profile_data,
    )
    
    return {
        "conversation_id": conversation_id,
        "status": "started",
        "user_profile": user_profile_data.get("name", "Unknown"),
        "target_profile": predefined_profiles[request.target_profile_id]["name"]
    }


@app.get("/api/conversations/{session_id}")
async def get_conversations(session_id: str):
    """Get active conversations for a session"""
    session_conversations = {
        conv_id: conv for conv_id, conv in active_conversations.items()
        if hasattr(conv, 'session_id') and conv.session_id == session_id
    }
    return {"conversations": list(session_conversations.keys())}


# ===== LLM Chat Endpoints =====

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """Chat with Claude LLM"""
    response = await chat_with_claude(message)
    return response


@app.get("/api/chat/history/{user_id}")
async def get_chat_history(user_id: str):
    """Get conversation history for a user"""
    history = await get_conversation_history(user_id)
    return {"user_id": user_id, "history": history}


@app.delete("/api/chat/history/{user_id}")
async def clear_chat_history(user_id: str):
    """Clear conversation history for a user"""
    result = await clear_conversation_history(user_id)
    return result


async def run_conversation_background(
    conversation_id: str,
    session_id: str,
    target_profile_id: str,
    max_turns: int,
    enable_research: bool,
    message_pause_seconds: float = 5.0,
    user_profile_data: Optional[Dict[str, Any]] = None,
):
    """Run conversation in background and stream updates to client"""
    try:
        client = AsyncDedalus()
        
        # Resolve user profile: explicit param takes precedence, otherwise from session
        if user_profile_data is None:
            user_profile_data = user_sessions[session_id]["profile"]
        print(f"🔍 Creating user agent with profile: {json.dumps(user_profile_data, indent=2)}")
        
        user_agent = PersonAgent(
            name=user_profile_data["name"],
            profile_data=user_profile_data,
            client=client
        )
        
        # Create target agent from predefined profile
        target_profile = predefined_profiles[target_profile_id]
        target_agent = PersonAgent(
            name=target_profile["name"],
            profile_data=target_profile,
            client=client
        )
        
        # Create conversation manager
        conv_manager = ConversationManager(user_agent, target_agent)
        conv_manager.conversation_id = conversation_id
        conv_manager.session_id = session_id
        active_conversations[conversation_id] = conv_manager
        
        # Send conversation start notification
        print(f"\n🎬 STARTING CONVERSATION: {user_agent.name} ↔ {target_agent.name}")
        print("=" * 60)
        
        await send_conversation_update(session_id, {
            "conversation_id": conversation_id,
            "speaker": "system",
            "message": f"Starting conversation between {user_agent.name} and {target_agent.name}...",
            "turn_number": 0,
            "is_finished": False
        })
        
        # Run the conversation with streaming updates
        await run_conversation_with_streaming(conv_manager, session_id, max_turns, enable_research, message_pause_seconds)
        
    except Exception as e:
        logger.error(f"Error in background conversation {conversation_id}: {e}")
        await send_conversation_update(session_id, {
            "conversation_id": conversation_id,
            "speaker": "system",
            "message": f"Error in conversation: {e}",
            "turn_number": -1,
            "is_finished": True
        })
    finally:
        if conversation_id in active_conversations:
            del active_conversations[conversation_id]


async def run_conversation_with_streaming(
    conv_manager: ConversationManager,
    session_id: str,
    max_turns: int,
    enable_research: bool,
    message_pause_seconds: float = 5.0
):
    """Run conversation with real-time streaming to client"""
    try:
        # Optional research phase
        if enable_research:
            await send_conversation_update(session_id, {
                "conversation_id": conv_manager.conversation_id,
                "speaker": "system",
                "message": "Research phase: agents are learning about each other...",
                "turn_number": 0,
                "is_finished": False
            })
            await conv_manager._research_phase()
        
        # Start with introduction
        introduction = await conv_manager.agent1.introduce()
        conv_manager.conversation_history.add_message(conv_manager.agent1.name, introduction)
        
        print(f"\n💬 {conv_manager.agent1.name}: {introduction}")
        
        await send_conversation_update(session_id, {
            "conversation_id": conv_manager.conversation_id,
            "speaker": conv_manager.agent1.name,
            "message": introduction,
            "turn_number": 1,
            "is_finished": False
        })
        
        # No compatibility tracking needed
        
        # Pause to allow frontend to display the introduction message
        print(f"⏳ Waiting {message_pause_seconds}s for introduction display...")
        await asyncio.sleep(message_pause_seconds)
        
        # Main conversation loop
        current_speaker = conv_manager.agent2
        other_speaker = conv_manager.agent1
        last_message = introduction
        
        for turn in range(max_turns):
            # Generate response
            response = await current_speaker.respond_to(other_speaker.name, last_message)
            conv_manager.conversation_history.add_message(current_speaker.name, response)
            
            # Log conversation to terminal
            print(f"💬 {current_speaker.name}: {response}")
            
            # No compatibility tracking needed
            
            # No compatibility scoring needed
            
            # Send update
            await send_conversation_update(session_id, {
                "conversation_id": conv_manager.conversation_id,
                "speaker": current_speaker.name,
                "message": response,
                "turn_number": turn + 2,  # +1 for introduction, +1 for current turn
                "is_finished": False
            })
            
            # Check if conversation should end based on max turns
            should_end = turn >= max_turns - 2
            
            if should_end:
                break
            
            # Switch speakers
            current_speaker, other_speaker = other_speaker, current_speaker
            last_message = response
            
            # Pause to allow frontend to display the message bubble before next response
            print(f"⏳ Waiting {message_pause_seconds}s for message display...")
            await asyncio.sleep(message_pause_seconds)
        
        # Send final summary
        final_message = f"""
Conversation ended!
• Total turns: {turn + 1}
• Max turns reached: {max_turns}
"""
        
        print(f"\n🏁 CONVERSATION ENDED")
        print("=" * 60)
        print(f"📊 Total Turns: {turn + 1}")
        print("=" * 60)
        
        await send_conversation_update(session_id, {
            "conversation_id": conv_manager.conversation_id,
            "speaker": "system",
            "message": final_message.strip(),
            "turn_number": turn + 2,
            "is_finished": True
        })
        
    except Exception as e:
        logger.error(f"Error in streaming conversation: {e}")
        await send_conversation_update(session_id, {
            "conversation_id": conv_manager.conversation_id,
            "speaker": "system",
            "message": f"Error during conversation: {e}",
            "turn_number": -1,
            "is_finished": True
        })


async def send_conversation_update(session_id: str, update_data: Dict):
    """Send conversation update to client"""
    if session_id in active_connections:
        message_data = {
            "type": "conversation_update",
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }
        await send_message_to_session(session_id, message_data)

if __name__ == "__main__":
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )