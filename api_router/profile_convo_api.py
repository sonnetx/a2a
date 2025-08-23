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
    user_id: str = "default_user"

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

async def clear_conversation_history(user_id: str) -> Dict[str, str]:
    """Clear conversation history for a user"""
    try:
        file_path = conv_history.get_conversation_file(user_id)
        if file_path.exists():
            file_path.unlink()
        return {"message": f"Conversation history cleared for {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")
