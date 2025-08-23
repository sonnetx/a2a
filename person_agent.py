import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dedalus_labs import AsyncDedalus, DedalusRunner


class PersonAgent:
    """Enhanced PersonAgent with research capabilities and conversation management"""
    
    def __init__(self, name: str, profile_data: Dict, client: AsyncDedalus, model: str = "openai/gpt-4o"):
        self.name = name
        self.profile_data = profile_data
        self.client = client
        self.model = model
        self.knowledge = {}
        self.conversation_history = []
        
    @classmethod
    def from_file(cls, file_path: str, client: AsyncDedalus, model: str = "openai/gpt-4o"):
        """Create PersonAgent from JSON profile file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            return cls(profile_data.get('name', 'Unknown'), profile_data, client, model)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Error loading profile from {file_path}: {e}")
    
    @property
    def bio(self) -> str:
        """Generate bio string from profile data"""
        parts = []
        if 'age' in self.profile_data:
            parts.append(f"I'm {self.profile_data['age']} years old")
        if 'occupation' in self.profile_data:
            parts.append(f"I work as a {self.profile_data['occupation']}")
        if 'background' in self.profile_data and 'location' in self.profile_data['background']:
            parts.append(f"I live in {self.profile_data['background']['location']}")
        return ". ".join(parts) + "." if parts else "Nice to meet you!"
    
    @property
    def interests(self) -> List[str]:
        """Extract interests from profile data"""
        interests = []
        if 'hobbies' in self.profile_data:
            interests.extend(self.profile_data['hobbies'])
        if 'personality' in self.profile_data and 'interests' in self.profile_data['personality']:
            interests.extend(self.profile_data['personality']['interests'])
        return interests
    
    @property
    def personality_traits(self) -> List[str]:
        """Extract personality traits from profile data"""
        if 'personality' in self.profile_data and 'traits' in self.profile_data['personality']:
            return self.profile_data['personality']['traits']
        return []
    
    def get_formatted_profile(self) -> str:
        """Get formatted profile string for context"""
        formatted = [f"Name: {self.name}"]
        
        if 'age' in self.profile_data:
            formatted.append(f"Age: {self.profile_data['age']}")
        if 'occupation' in self.profile_data:
            formatted.append(f"Occupation: {self.profile_data['occupation']}")
        
        if self.interests:
            formatted.append(f"Interests/Hobbies: {', '.join(self.interests)}")
        
        if self.personality_traits:
            formatted.append(f"Personality traits: {', '.join(self.personality_traits)}")
        
        if 'personality' in self.profile_data and 'goals' in self.profile_data['personality']:
            goals = self.profile_data['personality']['goals']
            if goals:
                formatted.append(f"Goals: {', '.join(goals)}")
        
        if 'background' in self.profile_data:
            bg = self.profile_data['background']
            for key, value in bg.items():
                if value and value != 'N/A':
                    formatted.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(formatted)
    
    async def introduce(self) -> str:
        """Generate introduction message"""
        return f"Hello, I'm {self.name}. {self.bio}"
    
    async def research_person(self, other_agent_name: str) -> str:
        """Research information about another person using web search"""
        runner = DedalusRunner(self.client)
        
        try:
            result = await runner.run(
                input=f"Research information about a person named {other_agent_name}. Find their background, interests, and any notable achievements.",
                model=self.model,
                mcp_servers=["tsion/brave-search-mcp"],
                stream=False
            )
            
            research_data = result.final_output
            self.knowledge[other_agent_name] = {
                "research": research_data,
                "timestamp": datetime.now().isoformat()
            }
            
            return research_data
        except Exception as e:
            fallback_info = f"Could not research {other_agent_name} due to: {e}"
            self.knowledge[other_agent_name] = {
                "research": fallback_info,
                "timestamp": datetime.now().isoformat()
            }
            return fallback_info
    
    async def respond_to(self, other_agent_name: str, message: str) -> str:
        """Generate a response to another agent's message"""
        # Add to conversation history
        self.conversation_history.append({
            "speaker": other_agent_name, 
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build context
        context = self._build_response_context(other_agent_name)
        
        # Generate response
        runner = DedalusRunner(self.client)
        
        try:
            result = await runner.run(
                input=f"{context}\n\nRespond naturally as {self.name} to {other_agent_name}'s last message. Be conversational, show genuine interest, and keep your response to 2-3 sentences ending with a question to continue the conversation.",
                model=self.model,
                stream=False
            )
            
            response = result.final_output.strip()
            
            # Add own response to history
            self.conversation_history.append({
                "speaker": self.name, 
                "message": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
        except Exception as e:
            fallback_response = f"I'm sorry, I'm having trouble responding right now. Could you tell me more about yourself?"
            self.conversation_history.append({
                "speaker": self.name, 
                "message": fallback_response,
                "timestamp": datetime.now().isoformat()
            })
            return fallback_response
    
    def _build_response_context(self, other_agent_name: str) -> str:
        """Build context string for response generation"""
        context = f"You are {self.name}. Here is your profile:\n"
        context += self.get_formatted_profile() + "\n\n"
        
        # Add research about the other person
        if other_agent_name in self.knowledge:
            context += f"What you know about {other_agent_name}:\n"
            context += f"{self.knowledge[other_agent_name].get('research', 'No information available.')}\n\n"
        
        # Add recent conversation history
        if self.conversation_history:
            context += "Recent conversation:\n"
            # Show last 5 exchanges for context
            recent_history = self.conversation_history[-10:]  # Last 10 messages
            for entry in recent_history:
                context += f"{entry['speaker']}: {entry['message']}\n"
        
        return context
    
    def get_conversation_stats(self) -> Dict:
        """Get statistics about the conversation"""
        my_messages = [msg for msg in self.conversation_history if msg['speaker'] == self.name]
        other_messages = [msg for msg in self.conversation_history if msg['speaker'] != self.name]
        
        return {
            'total_messages': len(self.conversation_history),
            'my_messages': len(my_messages),
            'other_messages': len(other_messages),
            'avg_message_length': sum(len(msg['message'].split()) for msg in my_messages) / len(my_messages) if my_messages else 0,
            'questions_asked': sum(msg['message'].count('?') for msg in my_messages)
        }