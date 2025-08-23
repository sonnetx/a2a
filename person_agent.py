import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dedalus_labs import AsyncDedalus, DedalusRunner
import os
from agentmail import AgentMail


class PersonAgent:   
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
            parts.append(f"{self.name} is {self.profile_data['age']} years old")
        if 'occupation' in self.profile_data:
            parts.append(f"works as a {self.profile_data['occupation']}")
        if 'background' in self.profile_data and 'location' in self.profile_data['background']:
            parts.append(f"and lives in {self.profile_data['background']['location']}")
        return ". ".join(parts) + "." if parts else f"{self.name} is looking forward to connecting!"
    
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
        
        # Add conversation context and goals if available
        if 'context_and_goal' in self.profile_data:
            formatted.append(f"Current Goals & Context: {self.profile_data['context_and_goal']}")
        
        return "\n".join(formatted)
    
    async def setup_email_inbox(self) -> str:
        """Setup email inbox using AgentMail"""
        api_key = os.getenv("AGENTMAIL_API_KEY")
        if not api_key:
            return "Error: AGENTMAIL_API_KEY not found in environment variables"
        
        self.agentmail_client = AgentMail(api_key=api_key)
        
        if self.inbox_id:
            return f"Using existing email setup for {self.name}"
        
        try:
            response = self.agentmail_client.inboxes.list()
            if len(response.inboxes) == 0:
                print("❌ No existing inboxes found")
                return "Error: No existing inboxes found"
            
            inbox = response.inboxes[0]
            self.inbox_id = inbox.inbox_id
            
            print(f"✉️ {self.name} configured for AgentMail using inbox: {self.inbox_id}")
            return f"AgentMail email configured for {self.name}"
        except Exception as e:
            print(f"❌ Error setting up AgentMail: {e}")
            return f"Error setting up AgentMail: {e}"
    
    async def introduce(self) -> str:
        """Generate introduction message"""
        runner = DedalusRunner(self.client)
        
        try:
            context = self.get_formatted_profile()
            
            result = await runner.run(
                input=f"""You are an AI agent representing {self.name}. Generate a brief introduction (1-2 sentences) where you:
1. Introduce yourself as an agent representing {self.name}
2. Mention what {self.name} is looking for or their main goal

Profile information:
{context}

Keep it conversational and focused on their current goals/interests.""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            return result.final_output.strip()
            
        except Exception as e:
            # Fallback to simple introduction
            return f"Hello, I'm an agent representing {self.name}. {self.name} is interested in connecting with others."
    
    async def research_person(self, other_agent_name: str) -> str:
        """Research information about another person using web search"""
        runner = DedalusRunner(self.client)
        
        try:
            # result = await runner.run(
            #     input=f"Research information about a person named {other_agent_name}. Find their background, interests, career, and any notable achievements. Focus on information that would help determine compatibility for friendship or professional relationships.",
            #     model=self.model,
            #     mcp_servers=["AgentMail"],
            #     stream=False
            # )
            
            # research_data = result.final_output
            # self.knowledge[other_agent_name] = {
            #     "research": research_data,
            #     "timestamp": datetime.now().isoformat()
            # }
            
            return ""
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
        
        # Only keep the last 20 messages to avoid context overflow
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        context = self._build_response_context(other_agent_name)
        
        runner = DedalusRunner(self.client)
        
        try:
            # Generate completely natural response
            response_result = await runner.run(
                input=f"""{context}

You are an AI agent representing {self.name} in a conversation with an agent representing {other_agent_name}. 
Speak in third person, using pronouns like "she" or "he" as appropriate, or use the actual name. Whatever fits with the flow of the conversation

IMPORTANT: Keep your responses SHORT and conversational (1-2 sentences max). Try to do some small talk, and try to not repeat the same
question or topic over and over. Like if we talked about scheduling once, don't ask about it again.

GOAL-ORIENTED BEHAVIOR: If your boss has current goals or context mentioned in their profile, 
try to naturally steer the conversation towards achieving those goals or addressing their current interests/concerns.

However, don't infer new information. If you find that there is some information that you may need from
your boss, send an email to your boss to get the information. For example, if they are planning to schedule
a time, you should send an eamil to confirm. Tell the other agent that you need to confirm with your boss.
""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            response = response_result.final_output.strip()
            
            # Add response to history
            self.conversation_history.append({
                "speaker": self.name, 
                "message": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check if agent needs to confirm something with their boss
            await self._check_for_boss_confirmation_needed(other_agent_name, response)
            
            return response
            
        except Exception as e:
            print(f"❌ ERROR in {self.name}.respond_to(): {e}")
            print(f"   Model: {self.model}")
            print(f"   Context length: {len(context) if context else 'None'}")
            print(f"   Other agent: {other_agent_name}")
            fallback_response = f"I'm sorry, I'm having trouble responding right now. Could you tell me more about yourself?"
            self.conversation_history.append({
                "speaker": self.name, 
                "message": fallback_response,
                "timestamp": datetime.now().isoformat()
            })
            
            return fallback_response
    
    async def _check_natural_compatibility_conclusion(self, other_agent_name: str, latest_response: str) -> None:
        """Check if the agent naturally reached a compatibility conclusion using AI analysis"""
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
                mcp_servers=["AgentMail"],
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

    async def _check_for_boss_confirmation_needed(self, other_agent_name: str, latest_response: str) -> None:
        """Check if the agent needs to confirm something with their boss"""
        runner = DedalusRunner(self.client)
        
        try:
            analysis_result = await runner.run(
                input=f"""Analyze if {self.name}'s agent needs to confirm something with {self.name} based on this conversation.

{self.name}'s Profile and Goals:
{self.get_formatted_profile()}

Recent conversation:
{self._format_recent_conversation(3)}

{self.name}'s latest response: "{latest_response}"

IMPORTANT: Only suggest confirmation if the agent needs information that is NOT already available in {self.name}'s profile, goals, or context.

Look for situations where the agent needs NEW information not in the profile:
- Scheduling specific times/dates (ONLY if {self.name}'s availability is unknown)
- Confirming details not covered in their goals/context
- Getting permission for things outside their stated interests

DO NOT suggest confirmation if:
- The information is already in {self.name}'s profile/goals
- The agent can reasonably respond based on existing context
- It's within {self.name}'s stated interests and goals

Respond with:
- NEEDS_CONFIRMATION: if agent needs NEW information not in profile
- NO_CONFIRMATION: if agent has enough information to proceed

Include a brief reason if confirmation is needed.""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            analysis = analysis_result.final_output.strip()
            
            if "NEEDS_CONFIRMATION" in analysis:
                await self._send_boss_confirmation_email(other_agent_name, latest_response, analysis)
                
        except Exception as e:
            print(f"Error checking boss confirmation: {e}")

    async def _send_boss_confirmation_email(self, other_agent_name: str, latest_response: str, reason: str) -> None:
        """Send a short confirmation email to the boss"""
        if not self.inbox_id:
            await self.setup_email_inbox()
        
        if not hasattr(self, 'agentmail_client'):
            return
        
        try:
            subject = f"Quick confirmation needed - conversation with {other_agent_name}"
            
            message_content = f"""Hi {self.name},

I'm chatting with {other_agent_name} and need to confirm something with you.

Recent exchange: "{latest_response}"

Please let me know how to proceed.

Thanks!"""

            result = self.agentmail_client.inboxes.messages.send(
                inbox_id=self.inbox_id,
                to="michaelli2005li@gmail.com",
                subject=subject,
                text=message_content
            )
            
            print(f"📧 Boss confirmation email sent to {self.name}")
            
        except Exception as e:
            print(f"❌ Error sending boss confirmation email: {e}")

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
        """Send an email using AgentMail client"""
        if not self.inbox_id:
            await self.setup_email_inbox()
        
        if not hasattr(self, 'agentmail_client'):
            return "Error: AgentMail client not initialized"
        
        status = "Compatible" if compatible else "Incompatible"
        emoji = "💚" if compatible else "💔"
        
        try:
            subject = f"{emoji} Natural Compatibility Assessment: {self.name} & {other_agent_name}"
            
            # Use AI to analyze conversation duration
            duration_analysis = await self._ai_analyze_conversation_duration()
            
            # Use AI to extract key topics
            key_topics = await self._ai_extract_key_topics()
            
            message_content = f"""Hi,

{self.name}'s agent here. Just concluded a conversation with {other_agent_name}.

Result: {status} - {final_message}

{"Looks like they connected well and might want to continue the relationship!" if compatible else "Natural conclusion reached - different compatibility needs."}"""

            # Send email using AgentMail
            result = self.agentmail_client.inboxes.messages.send(
                inbox_id=self.inbox_id,
                to="michaelli2005li@gmail.com",
                subject=subject,
                text=message_content
            )
            
            print(f"✅ Email sent from {self.inbox_id}")
            print(f"📧 To: michaelli2005li@gmail.com")
            print(f"📝 Subject: {subject}")
            print(f"🆔 Message ID: {result.message_id}")
            
            return f"Email sent successfully with message ID: {result.message_id}"
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return f"Error sending email: {e}"
    
    async def _ai_analyze_conversation_duration(self) -> str:
        """Use AI to analyze and describe conversation duration in a natural way"""
        if len(self.conversation_history) < 2:
            return "Less than 1 minute"
        
        start_time = datetime.fromisoformat(self.conversation_history[0]['timestamp'])
        end_time = datetime.fromisoformat(self.conversation_history[-1]['timestamp'])
        duration_seconds = (end_time - start_time).total_seconds()
        
        runner = DedalusRunner(self.client)
        
        try:
            result = await runner.run(
                input=f"""Describe this conversation duration in a natural, human-friendly way:
                
Duration in seconds: {duration_seconds}
Number of message exchanges: {len(self.conversation_history)}

Provide a brief, natural description of how long this conversation lasted. Consider both the actual time elapsed and the number of exchanges to give context about the conversation's pace and depth.""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            return result.final_output.strip()
        except Exception as e:
            # Fallback to simple calculation
            minutes = duration_seconds / 60
            if minutes < 1:
                return "Less than 1 minute"
            elif minutes < 60:
                return f"{int(minutes)} minutes"
            else:
                hours = int(minutes / 60)
                remaining_minutes = int(minutes % 60)
                return f"{hours}h {remaining_minutes}m"
    
    async def _ai_extract_key_topics(self) -> str:
        """Use AI to extract and summarize key topics from conversation"""
        if not self.conversation_history:
            return "No conversation topics"
        
        runner = DedalusRunner(self.client)
        
        try:
            all_messages = "\n".join([
                f"{msg['speaker']}: {msg['message']}" 
                for msg in self.conversation_history
            ])
            
            result = await runner.run(
                input=f"""Analyze this conversation and identify the key topics that were discussed:

{all_messages}

Extract and summarize the main themes, subjects, and areas of interest that came up during this conversation. Provide a concise summary of the key topics as a comma-separated list or brief description.""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            return result.final_output.strip()
        except Exception as e:
            return "General conversation topics"
    
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
    
    async def get_ai_conversation_stats(self) -> Dict:
        """Get AI-analyzed statistics about the conversation"""
        if not self.conversation_history:
            return {
                'total_messages': 0,
                'analysis': 'No conversation data available'
            }
        
        runner = DedalusRunner(self.client)
        
        try:
            conversation_text = self._format_conversation_history()
            
            result = await runner.run(
                input=f"""Analyze this conversation between {self.name} and others. Provide insights about:

Conversation Data:
{conversation_text}

Profile Context:
{self.get_formatted_profile()}

Please analyze:
1. Conversation engagement level (high/medium/low)
2. Communication style compatibility
3. Shared interests discovered
4. Conversation flow quality
5. Emotional tone and rapport
6. Questions asked and answered
7. Overall interaction assessment

Provide your analysis as a structured summary.""",
                model=self.model,
                mcp_servers=["AgentMail"],
                stream=False
            )
            
            return {
                'total_messages': len(self.conversation_history),
                'my_messages': len([msg for msg in self.conversation_history if msg['speaker'] == self.name]),
                'other_messages': len([msg for msg in self.conversation_history if msg['speaker'] != self.name]),
                'compatibility_status': self.compatibility_status,
                'ai_analysis': result.final_output.strip(),
                'conversation_duration': await self._ai_analyze_conversation_duration(),
                'key_topics': await self._ai_extract_key_topics()
            }
            
        except Exception as e:
            # Fallback to basic stats
            my_messages = [msg for msg in self.conversation_history if msg['speaker'] == self.name]
            other_messages = [msg for msg in self.conversation_history if msg['speaker'] != self.name]
            
            return {
                'total_messages': len(self.conversation_history),
                'my_messages': len(my_messages),
                'other_messages': len(other_messages),
                'compatibility_status': self.compatibility_status,
                'ai_analysis': f"Error during AI analysis: {e}",
                'conversation_duration': await self._ai_analyze_conversation_duration(),
                'key_topics': await self._ai_extract_key_topics()
            }
    
    def _format_conversation_history(self) -> str:
        """Format conversation history for analysis"""
        formatted = []
        for entry in self.conversation_history:
            timestamp = entry['timestamp'].split('T')[1][:8] if 'T' in entry['timestamp'] else 'unknown'
            formatted.append(f"[{timestamp}] {entry['speaker']}: {entry['message']}")
        
        return "\n".join(formatted)
    
    async def have_conversation_with(self, other_agent: 'PersonAgent', max_exchanges: int = 10) -> Dict:
        """Have a conversation with another agent until compatibility naturally emerges"""
        print(f"🤝 Starting conversation between {self.name} and {other_agent.name}")
        
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
        
        # Get AI-powered conversation analysis
        self_stats = await self.get_ai_conversation_stats()
        other_stats = await other_agent.get_ai_conversation_stats()
        
        # Final result with AI analysis
        result = {
            'participants': [self.name, other_agent.name],
            'exchanges': exchange_count,
            'conclusion_method': 'natural',
            'self_status': self.compatibility_status,
            'other_status': other_agent.compatibility_status,
            'ai_conversation_analysis': {
                f'{self.name}_analysis': self_stats,
                f'{other_agent.name}_analysis': other_stats
            },
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
    print("✅ AI-driven compatibility assessment")
    print("✅ Organic conversation flow")
    print("✅ Smart email notifications")
    print("✅ AI-powered topic extraction")
    print("✅ AI-analyzed conversation insights")
    print("="*50)
    
    # Have them converse naturally
    result = await alice.have_conversation_with(bob, max_exchanges=12)
    
    print("\n" + "="*50)
    print("📊 FINAL AI-POWERED CONVERSATION ANALYSIS:")
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