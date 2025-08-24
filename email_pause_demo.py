#!/usr/bin/env python3
"""
Demo showing AgentMail conversation pausing functionality.

When the agent needs boss confirmation, it:
1. Sends email to boss 
2. PAUSES conversation
3. Waits for boss reply
4. Resumes with boss info
"""

import asyncio
from dedalus_labs import AsyncDedalus
from person_agent import PersonAgent

async def demo_email_pause():
    """Demo the email pause functionality"""
    
    client = AsyncDedalus()
    
    # Create Michael's agent (has email capabilities)
    michael_profile = {
        "name": "Michael",
        "age": 30,
        "occupation": "Software Engineer",
        "context_and_goal": "Looking to schedule meetings and collaborate on projects"
    }
    
    # Create other agent  
    alice_profile = {
        "name": "Alice", 
        "age": 28,
        "occupation": "Project Manager",
        "hobbies": ["scheduling", "meetings"],
        "context_and_goal": "Wants to schedule Tuesday/Thursday meetings"
    }
    
    michael_agent = PersonAgent("Michael", michael_profile, client)
    alice_agent = PersonAgent("Alice", alice_profile, client)
    
    print("🚀 Email Pause Demo Starting...")
    print("=" * 50)
    
    # Setup email for Michael (only he gets email capabilities)
    await michael_agent.setup_email_inbox()
    
    # Start conversation - when Alice mentions Tuesday/Thursday, 
    # Michael's agent will email boss and PAUSE until reply
    result = await michael_agent.have_conversation_with(alice_agent, max_exchanges=8)
    
    print("\n" + "=" * 50)
    print("📊 CONVERSATION COMPLETED")
    print(f"Total exchanges: {result['exchanges']}")
    print(f"Michael status: {result['self_status'] or 'No conclusion'}")
    print(f"Alice status: {result['other_status'] or 'No conclusion'}")
    
    return result

if __name__ == "__main__":
    print("💬 Demo: Agent conversation with email pausing")
    print("When scheduling conflicts arise, conversation will pause")
    print("until boss replies via AgentMail")
    
    asyncio.run(demo_email_pause())
