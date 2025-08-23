#!/usr/bin/env python3
"""
Simple LLM conversation API using Anthropic Claude.
Logs conversations to profile files.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import anthropic
from fastapi import HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

class ChatMessage(BaseModel):
    message: str
    user_id: str = "my_agent"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str

class ConversationHistory:
    """Simple conversation history manager"""
    
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
    
    def get_conversation_file(self, user_id: str) -> Path:
        """Get conversation file path for user"""
        return self.profiles_dir / f"{user_id}_conversation.txt"
    
    def load_history(self, user_id: str) -> List[Dict[str, str]]:
        """Load conversation history for user"""
        file_path = self.get_conversation_file(user_id)
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                
                # Parse simple format: TIMESTAMP|ROLE|MESSAGE
                messages = []
                for line in content.split('\n'):
                    if '|' in line:
                        parts = line.split('|', 2)
                        if len(parts) == 3:
                            timestamp, role, message = parts
                            messages.append({
                                "role": role,
                                "content": message,
                                "timestamp": timestamp
                            })
                return messages
        except Exception as e:
            print(f"Error loading history for {user_id}: {e}")
            return []
    
    def save_message(self, user_id: str, role: str, message: str):
        """Save a message to conversation history"""
        file_path = self.get_conversation_file(user_id)
        timestamp = datetime.now().isoformat()
        
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp}|{role}|{message}\n")
        except Exception as e:
            print(f"Error saving message for {user_id}: {e}")
    
    def get_claude_messages(self, user_id: str, max_messages: int = 20) -> List[Dict[str, str]]:
        """Get conversation history in Claude API format"""
        history = self.load_history(user_id)
        
        # Get the last max_messages messages
        recent_history = history[-max_messages:] if len(history) > max_messages else history
        
        # Convert to Claude format (only role and content)
        claude_messages = []
        for msg in recent_history:
            if msg["role"] in ["user", "assistant"]:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return claude_messages

# Initialize conversation history manager
conv_history = ConversationHistory()

async def chat_with_claude(message: ChatMessage) -> ChatResponse:
    """
    Chat with Claude and maintain conversation history
    """
    try:
        # Load conversation history
        history = conv_history.get_claude_messages(message.user_id)
        
        # Add the new user message to history
        history.append({
            "role": "user",
            "content": message.message
        })
        
        # Make sure we don't exceed Claude's context limit (rough estimate)
        if len(history) > 30:
            history = history[-30:]  # Keep last 30 messages
        
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Using the latest available model
            max_tokens=1000,
            messages=history
        )
        
        # Extract response text
        response_text = ""
        if response.content and len(response.content) > 0:
            response_text = response.content[0].text
        else:
            response_text = "I'm sorry, I couldn't generate a response."
        
        # Save both user message and assistant response to history
        conv_history.save_message(message.user_id, "user", message.message)
        conv_history.save_message(message.user_id, "assistant", response_text)
        
        # Update user profile with conversation context
        await update_user_profile_from_chat(message.user_id)
        
        # Generate conversation ID (simple timestamp-based)
        conversation_id = f"{message.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Error in chat_with_claude: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

async def get_conversation_history(user_id: str) -> List[Dict[str, Any]]:
    """Get full conversation history for a user"""
    try:
        history = conv_history.load_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading history: {str(e)}")

async def update_user_profile_from_chat(user_id: str) -> None:
    """Update user profile JSON with summarized chat context"""
    try:
        # Load conversation history
        chat_history = conv_history.load_history(user_id)
        
        if not chat_history:
            return  # No chat history to process
        
        # Map certain user IDs to specific profile files
        profile_mapping = {
            "frontend_user": "my_agent",  # Map frontend_user to my_agent profile
            "default_user": "my_agent"    # Map default_user to my_agent profile
        }
        
        # Get the actual profile name to use
        profile_name = profile_mapping.get(user_id, user_id)
        profile_path = conv_history.profiles_dir / f"{profile_name}.json"
        
        # Load existing profile or create new one
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
        else:
            # Create basic profile structure if it doesn't exist
            profile_data = {
                "name": user_id,
                "personality": {},
                "background": {}
            }
        
        # Prepare chat history for summarization
        recent_messages = chat_history[-20:]  # Last 20 messages
        chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        # Use Claude to summarize the conversation and extract context
        summary_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on this conversation history, create a concise summary that captures:
1. The user's current interests, concerns, or goals
2. Recent topics they've discussed
3. Their communication style and preferences
4. Any context that would help an AI agent understand them better

Conversation history:
{chat_text}

Provide a 5-6 sentence summary that captures the essence of who this 
person is and what they care about based on this conversation. Also mention
any most-recently desginated tasks or goals they have.
"""
                }
            ]
        )
        
        # Extract summary
        if summary_response.content and len(summary_response.content) > 0:
            context_summary = summary_response.content[0].text.strip()
        else:
            context_summary = "Recent conversation history available."
        
        # Update the profile with context
        profile_data["context_and_goal"] = context_summary
        profile_data["last_updated"] = datetime.now().isoformat()
        
        # Save updated profile
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated profile for {user_id} with conversation context")
        
    except Exception as e:
        print(f"Error updating profile for {user_id}: {e}")
        # Don't raise exception to avoid breaking the chat flow


async def clear_conversation_history(user_id: str) -> Dict[str, str]:
    """Clear conversation history for a user"""
    try:
        file_path = conv_history.get_conversation_file(user_id)
        if file_path.exists():
            file_path.unlink()
        return {"message": f"Conversation history cleared for {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")
