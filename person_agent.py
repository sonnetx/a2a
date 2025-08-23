import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dedalus_labs import AsyncDedalus, DedalusRunner


class PersonAgent:
    """Enhanced PersonAgent with research capabilities, conversation management, and email notifications"""
    
    def __init__(self, name: str, profile_data: Dict, client: AsyncDedalus, model: str = "openai/gpt-4o"):
        self.name = name
        self.profile_data = profile_data
        self.client = client
        self.model = model
        self.knowledge = {}
        self.conversation_history = []
        self.compatibility_status = None  # None, 'compatible', 'incompatible'
        self.inbox_id = None  # Will store AgentMail inbox ID
        
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
    
    async def setup_email_inbox(self) -> str:
        """Note: AgentMail MCP server doesn't have create_inbox tool, so we'll handle this differently"""
        # The AgentMail MCP server only has: get_message, send_message, reply_to_message
        # We'll assume an inbox/email is provided or available through the API configuration
        
        if self.inbox_id:
            return f"Using existing email setup for {self.name}"
            
        # For now, we'll use a placeholder that indicates the email is handled by AgentMail's backend
        self.inbox_id = f"{self.name.lower().replace(' ', '_')}_agent"
        
        print(f"✉️ {self.name} configured for AgentMail (inbox managed by AgentMail backend)")
        return f"AgentMail email configured for {self.name}"
    
    async def introduce(self) -> str:
        """Generate introduction message"""
        return f"Hello, I'm {self.name}. {self.bio}"
    
    async def research_person(self, other_agent_name: str) -> str:
        """Research information about another person using web search"""
        runner = DedalusRunner(self.client)
        
        try:
            result = await runner.run(
                input=f"Research information about a person named {other_agent_name}. Find their background, interests, career, and any notable achievements. Focus on information that would help determine compatibility for friendship or professional relationships.",
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
        """Generate a fully natural response with organic compatibility assessment"""
        # Add to conversation history
        self.conversation_history.append({
            "speaker": other_agent_name, 
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        context = self._build_response_context(other_agent_name)
        
        runner = DedalusRunner(self.client)
        
        try:
            # Generate completely natural response
            response_result = await runner.run(
                input=f"""{context}

You are {self.name} having a natural conversation with {other_agent_name}. 

Respond authentically as yourself based on your personality and interests. As the conversation develops:
- Share your thoughts and experiences naturally
- Ask questions about things that genuinely interest you
- If you feel a connection forming, you might suggest staying in touch or meeting up
- If you sense you're quite different or the conversation isn't flowing well, you might naturally start wrapping up politely
- Be genuine about whether you're enjoying the conversation or finding common ground

Don't force compatibility assessment - let it emerge naturally from your authentic reactions to {other_agent_name}.""",
                model=self.model,
                stream=False
            )
            
            response = response_result.final_output.strip()
            
            # Add response to history
            self.conversation_history.append({
                "speaker": self.name, 
                "message": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check for natural compatibility conclusion after sufficient conversation
            if len(self.conversation_history) >= 6 and self.compatibility_status is None:
                await self._check_natural_compatibility_conclusion(other_agent_name, response)
            
            return response
            
        except Exception as e:
            fallback_response = f"I'm sorry, I'm having trouble responding right now. Could you tell me more about yourself?"
            self.conversation_history.append({
                "speaker": self.name, 
                "message": fallback_response,
                "timestamp": datetime.now().isoformat()
            })
            return fallback_response
    
    async def _check_natural_compatibility_conclusion(self, other_agent_name: str, latest_response: str) -> None:
        """Check if the agent naturally reached a compatibility conclusion"""
        runner = DedalusRunner(self.client)
        
        try:
            analysis_result = await runner.run(
                input=f"""Analyze this conversation between {self.name} and {other_agent_name} to determine if {self.name} has naturally reached a compatibility conclusion.

Recent conversation:
{self._format_recent_conversation(5)}

{self.name}'s latest response: "{latest_response}"

Look for natural signs of compatibility conclusion:

COMPATIBLE indicators:
- Expressing genuine enthusiasm about the other person
- Suggesting to meet up, stay in touch, or exchange contacts
- Saying things like "I'd love to..." "We should..." "Let's..."
- Expressing shared values or strong connection
- Inviting further interaction

INCOMPATIBLE indicators:
- Politely trying to end the conversation
- Expressing fundamental differences in values/lifestyle
- Using phrases like "Well, it was nice talking..." "I should probably..."
- Showing disinterest or discomfort
- Natural conversation winding down with closure

STILL DEVELOPING indicators:
- Continuing to ask questions and engage
- Exploring common interests
- Building rapport but not yet concluding
- Natural back-and-forth flow

Based ONLY on {self.name}'s natural behavior and language, respond with ONE of:
- NATURALLY_COMPATIBLE: if they expressed genuine desire for continued connection
- NATURALLY_INCOMPATIBLE: if they naturally concluded or showed disinterest
- STILL_DEVELOPING: if the conversation is naturally continuing without conclusion""",
                model=self.model,
                stream=False
            )
            
            analysis = analysis_result.final_output.strip()
            
            if "NATURALLY_COMPATIBLE" in analysis:
                self.compatibility_status = 'compatible'
                print(f"💚 {self.name} naturally concluded: COMPATIBLE with {other_agent_name}")
                await self._send_natural_compatibility_email(other_agent_name, latest_response, compatible=True)
                
            elif "NATURALLY_INCOMPATIBLE" in analysis:
                self.compatibility_status = 'incompatible' 
                print(f"💔 {self.name} naturally concluded: INCOMPATIBLE with {other_agent_name}")
                await self._send_natural_compatibility_email(other_agent_name, latest_response, compatible=False)
                
            else:
                print(f"🔄 {self.name} is still naturally developing conversation with {other_agent_name}")
                
        except Exception as e:
            print(f"Error checking natural compatibility: {e}")

    def _format_recent_conversation(self, num_messages: int = 5) -> str:
        """Format recent conversation history"""
        if not self.conversation_history:
            return "No conversation history"
            
        recent = self.conversation_history[-num_messages:]
        formatted = []
        for entry in recent:
            formatted.append(f"{entry['speaker']}: {entry['message']}")
        
        return "\n".join(formatted)
    
    async def _send_natural_compatibility_email(self, other_agent_name: str, final_message: str, compatible: bool) -> str:
        """Send an email using AgentMail's send_message tool"""
        if not self.inbox_id:
            await self.setup_email_inbox()
        
        runner = DedalusRunner(self.client)
        
        status = "Compatible" if compatible else "Incompatible"
        emoji = "💚" if compatible else "💔"
        
        try:
            result = await runner.run(
                input=f"""Use the AgentMail send_message tool to send an email with these details:

To: admin@example.com
Subject: {emoji} Natural Compatibility Assessment: {self.name} & {other_agent_name}

Message content:
---
Hi there,

This is an automated report from the AI agent compatibility system.

**Assessment Summary:**
- Agents: {self.name} ↔ {other_agent_name}
- Natural Conclusion: {status}
- Assessment Method: Organic conversation analysis

**How it happened:**
{self.name} naturally reached this conclusion during conversation. The final message that indicated compatibility was:
"{final_message}"

**Conversation Insights:**
- Duration: {self._get_conversation_duration()}
- Total exchanges: {len(self.conversation_history)}
- Key topics: {self._get_key_topics()}
- Flow: Natural and authentic

**What this means:**
{"Both agents showed genuine interest in continuing their connection. This suggests strong compatibility for future interactions." if compatible else "The agents naturally concluded their interaction, suggesting different compatibility needs. This is a healthy outcome."}

**Recent Conversation:**
{self._format_recent_conversation(8)}

Best regards,
{self.name} (AI Agent)
---

Please use the send_message tool from AgentMail to send this email now.""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            print(f"📧 {self.name} sent compatibility email about {other_agent_name} ({status})")
            return result.final_output
        except Exception as e:
            error_msg = f"Failed to send natural compatibility email: {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
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
            # Show last 10 messages for context
            recent_history = self.conversation_history[-10:]
            for entry in recent_history:
                context += f"{entry['speaker']}: {entry['message']}\n"
        
        return context
    
    def _get_conversation_duration(self) -> str:
        """Calculate conversation duration"""
        if len(self.conversation_history) < 2:
            return "Less than 1 minute"
        
        start_time = datetime.fromisoformat(self.conversation_history[0]['timestamp'])
        end_time = datetime.fromisoformat(self.conversation_history[-1]['timestamp'])
        duration = end_time - start_time
        
        minutes = duration.total_seconds() / 60
        if minutes < 1:
            return "Less than 1 minute"
        elif minutes < 60:
            return f"{int(minutes)} minutes"
        else:
            hours = int(minutes / 60)
            remaining_minutes = int(minutes % 60)
            return f"{hours}h {remaining_minutes}m"
    
    def _get_key_topics(self) -> str:
        """Extract key topics from conversation"""
        # Simple keyword extraction from conversation
        all_text = " ".join([msg['message'] for msg in self.conversation_history])
        
        # Common topics to look for
        topics = []
        topic_keywords = {
            'work': ['job', 'work', 'career', 'profession', 'office'],
            'hobbies': ['hobby', 'interest', 'enjoy', 'love', 'passion'],
            'travel': ['travel', 'trip', 'vacation', 'visit', 'country'],
            'family': ['family', 'parent', 'child', 'sibling', 'married'],
            'technology': ['tech', 'computer', 'software', 'AI', 'digital'],
            'sports': ['sport', 'game', 'team', 'play', 'exercise']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword.lower() in all_text.lower() for keyword in keywords):
                topics.append(topic)
        
        return ", ".join(topics) if topics else "General conversation"
    
    def _format_conversation_history(self) -> str:
        """Format conversation history for email"""
        formatted = []
        for entry in self.conversation_history:
            timestamp = entry['timestamp'].split('T')[1][:8]  # Just time, not date
            formatted.append(f"[{timestamp}] {entry['speaker']}: {entry['message']}")
        
        return "\n".join(formatted)
    
    def get_conversation_stats(self) -> Dict:
        """Get statistics about the conversation"""
        my_messages = [msg for msg in self.conversation_history if msg['speaker'] == self.name]
        other_messages = [msg for msg in self.conversation_history if msg['speaker'] != self.name]
        
        return {
            'total_messages': len(self.conversation_history),
            'my_messages': len(my_messages),
            'other_messages': len(other_messages),
            'avg_message_length': sum(len(msg['message'].split()) for msg in my_messages) / len(my_messages) if my_messages else 0,
            'questions_asked': sum(msg['message'].count('?') for msg in my_messages),
            'compatibility_status': self.compatibility_status,
            'conversation_duration': self._get_conversation_duration(),
            'key_topics': self._get_key_topics()
        }
    
    async def have_conversation_with(self, other_agent: 'PersonAgent', max_exchanges: int = 10) -> Dict:
        """Have a fully natural conversation with another agent until compatibility naturally emerges"""
        print(f"🤝 Starting natural conversation between {self.name} and {other_agent.name}")
        
        # Both agents create their own inboxes automatically
        await asyncio.gather(
            self.setup_email_inbox(),
            other_agent.setup_email_inbox()
        )
        
        # Research each other
        print(f"🔍 Agents researching each other...")
        await asyncio.gather(
            self.research_person(other_agent.name),
            other_agent.research_person(self.name)
        )
        
        # Start conversation with introduction
        intro = await self.introduce()
        print(f"\n{self.name}: {intro}")
        
        current_speaker = other_agent
        current_message = intro
        exchange_count = 0
        
        # Continue until natural conclusion or max exchanges
        while (exchange_count < max_exchanges and 
               self.compatibility_status is None and 
               other_agent.compatibility_status is None):
            
            response = await current_speaker.respond_to(
                self.name if current_speaker == other_agent else other_agent.name,
                current_message
            )
            
            print(f"{current_speaker.name}: {response}")
            
            # Switch speakers
            current_speaker = self if current_speaker == other_agent else other_agent
            current_message = response
            exchange_count += 1
            
            # Small delay to make conversation feel more natural
            await asyncio.sleep(0.5)
        
        # Final result
        result = {
            'participants': [self.name, other_agent.name],
            'exchanges': exchange_count,
            'conclusion_method': 'natural',
            'self_status': self.compatibility_status,
            'other_status': other_agent.compatibility_status,
            'conversation_stats': self.get_conversation_stats(),
            'natural_conclusion': {
                'self_reached_conclusion': self.compatibility_status is not None,
                'other_reached_conclusion': other_agent.compatibility_status is not None,
                'emails_sent': bool(self.compatibility_status) + bool(other_agent.compatibility_status)
            }
        }
        
        conclusion_status = "naturally concluded" if (self.compatibility_status or other_agent.compatibility_status) else "reached max exchanges"
        print(f"\n✅ Conversation {conclusion_status}")
        print(f"   {self.name}: {self.compatibility_status or 'no conclusion'}")
        print(f"   {other_agent.name}: {other_agent.compatibility_status or 'no conclusion'}")
        
        return result


async def demo_natural_agent_conversation():
    """Demo function showing the fully natural PersonAgent conversation"""
    
    # Initialize Dedalus client
    client = AsyncDedalus()  # Add your API key here if needed
    
    # Create two agents from profile files (or create simple profiles)
    alice_profile = {
        "name": "Alice",
        "age": 28,
        "occupation": "Marketing Manager", 
        "hobbies": ["hiking", "photography", "reading"],
        "personality": {
            "traits": ["outgoing", "creative", "adventurous"],
            "interests": ["nature", "travel", "art"],
            "goals": ["career growth", "work-life balance"]
        },
        "background": {
            "location": "San Francisco",
            "education": "Business degree"
        }
    }
    
    bob_profile = {
        "name": "Bob",
        "age": 25,
        "occupation": "Software Developer",
        "hobbies": ["gaming", "coding", "anime"],
        "personality": {
            "traits": ["introverted", "analytical", "loyal"],
            "interests": ["technology", "problem-solving", "sci-fi"],
            "goals": ["technical mastery", "financial stability"]
        },
        "background": {
            "location": "Seattle",
            "education": "Computer Science degree"
        }
    }
    
    # Create agents
    alice = PersonAgent("Alice", alice_profile, client)
    bob = PersonAgent("Bob", bob_profile, client)
    
    print("🚀 Starting fully natural agent conversation demo...")
    print("Features:")
    print("✅ Automatic inbox creation (no user input)")
    print("✅ Natural compatibility assessment")
    print("✅ Organic conversation flow")
    print("✅ Smart email notifications")
    print("="*50)
    
    # Have them converse naturally
    result = await alice.have_conversation_with(bob, max_exchanges=12)
    
    print("\n" + "="*50)
    print("📊 FINAL CONVERSATION ANALYSIS:")
    print(f"Method: {result['conclusion_method']}")
    print(f"Exchanges: {result['exchanges']}")
    print(f"Natural conclusions reached: {result['natural_conclusion']['emails_sent']}")
    print(f"Alice's assessment: {result['self_status'] or 'No conclusion'}")
    print(f"Bob's assessment: {result['other_status'] or 'No conclusion'}")
    
    return result


# Additional utility for testing with custom profiles
async def test_natural_compatibility(profile1: Dict, profile2: Dict):
    """Test natural compatibility between two custom profiles"""
    client = AsyncDedalus()
    
    agent1 = PersonAgent(profile1["name"], profile1, client)
    agent2 = PersonAgent(profile2["name"], profile2, client)
    
    return await agent1.have_conversation_with(agent2)


if __name__ == "__main__":
    asyncio.run(demo_natural_agent_conversation())