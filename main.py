#!/usr/bin/env python3

import asyncio
import os
import argparse
from typing import Optional
from dotenv import load_dotenv

from dedalus_labs import AsyncDedalus
from person_agent import PersonAgent
from conversation_manager import ConversationManager

# Load environment variables
load_dotenv()


async def run_conversation_simulation(
    profile1_path: str,
    profile2_path: str,
    max_turns: int = 10,
    enable_research: bool = True,
    model: str = "openai/gpt-4o",
    save_log: Optional[str] = None
):
    """
    Run a conversation simulation between two people with compatibility scoring.
    
    Args:
        profile1_path: Path to first person's JSON profile
        profile2_path: Path to second person's JSON profile
        max_turns: Maximum number of conversation turns
        enable_research: Whether to enable web research phase
        model: Model to use for conversation generation
        save_log: Optional filename to save conversation log
    """
    # Initialize Dedalus client
    client = AsyncDedalus()
    
    try:
        # Load person profiles and create agents
        print("Loading person profiles...")
        agent1 = PersonAgent.from_file(profile1_path, client, model)
        agent2 = PersonAgent.from_file(profile2_path, client, model)
        
        print(f"Created agents: {agent1.name} and {agent2.name}")
        
        # Create conversation manager
        conversation_manager = ConversationManager(agent1, agent2)
        
        # Start the conversation
        results = await conversation_manager.start_conversation(
            max_turns=max_turns,
            enable_research=enable_research
        )
        
        # Save conversation log if requested
        if save_log:
            conversation_manager.save_conversation_log(save_log)
            print(f"\nConversation log saved to: {save_log}")
        
        # Print summary
        print("\n" + "="*50)
        print("CONVERSATION SUMMARY")
        print("="*50)
        print(f"Overall Compatibility Score: {results.get('overall_compatibility', 'N/A'):.3f}")
        print(f"Status: {results.get('overall_status', 'Unknown')}")
        print(f"Total Turns: {results.get('turn_count', 'N/A')}")
        print(f"Total Messages: {results.get('message_count', 'N/A')}")
        
        if 'personality_summaries' in results:
            print("\nPersonality Observations:")
            for key, summary in results['personality_summaries'].items():
                print(f"  {key}: {summary}")
        
        return results
        
    except Exception as e:
        print(f"Error during conversation simulation: {e}")
        raise


async def run_predefined_example():
    """Run conversation with predefined example personas"""
    # You can create example profiles here or load them from files
    example_profiles = {
        "alice": {
            "name": "Alice Johnson",
            "age": 28,
            "occupation": "Software Engineer",
            "hobbies": ["rock climbing", "photography", "cooking"],
            "personality": {
                "traits": ["adventurous", "creative", "analytical"],
                "interests": ["technology", "outdoor activities", "art"],
                "goals": ["start a tech company", "travel to Japan", "learn guitar"]
            },
            "background": {
                "education": "Computer Science BS",
                "location": "San Francisco",
                "family": "Single, close to siblings"
            }
        },
        "bob": {
            "name": "Bob Smith",
            "age": 32,
            "occupation": "Marketing Manager",
            "hobbies": ["running", "coffee brewing", "reading"],
            "personality": {
                "traits": ["social", "organized", "curious"],
                "interests": ["business", "fitness", "literature"],
                "goals": ["run a marathon", "write a book", "learn Spanish"]
            },
            "background": {
                "education": "Marketing MBA",
                "location": "Austin",
                "family": "Married, two kids"
            }
        }
    }
    
    # Save example profiles to temp files
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_alice.json', delete=False) as f1:
        json.dump(example_profiles["alice"], f1, indent=2)
        alice_file = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_bob.json', delete=False) as f2:
        json.dump(example_profiles["bob"], f2, indent=2)
        bob_file = f2.name
    
    try:
        results = await run_conversation_simulation(
            alice_file,
            bob_file,
            max_turns=8,
            enable_research=False,  # Disable for example
            save_log="example_conversation.json"
        )
        return results
    finally:
        # Clean up temp files
        os.unlink(alice_file)
        os.unlink(bob_file)


async def run_celebrity_example():
    """Run conversation between two well-known figures (like the original example)"""
    client = AsyncDedalus()
    
    # Create celebrity personas similar to the original example
    elon = PersonAgent(
        name="Elon Musk",
        profile_data={
            "name": "Elon Musk",
            "age": 52,
            "occupation": "Entrepreneur and Business Magnate",
            "hobbies": ["engineering", "space exploration", "gaming"],
            "personality": {
                "traits": ["innovative", "ambitious", "analytical"],
                "interests": ["space exploration", "electric vehicles", "artificial intelligence", "neurotechnology"],
                "goals": ["colonize Mars", "advance sustainable energy", "develop brain-computer interfaces"]
            },
            "background": {
                "education": "Physics and Economics degrees",
                "location": "Texas/California",
                "family": "Multiple children"
            }
        },
        client=client
    )
    
    mark = PersonAgent(
        name="Mark Zuckerberg",
        profile_data={
            "name": "Mark Zuckerberg",
            "age": 39,
            "occupation": "CEO of Meta Platforms",
            "hobbies": ["programming", "fencing", "surfing"],
            "personality": {
                "traits": ["analytical", "focused", "competitive"],
                "interests": ["virtual reality", "social networking", "artificial intelligence", "fitness"],
                "goals": ["build the metaverse", "connect the world", "advance VR/AR technology"]
            },
            "background": {
                "education": "Harvard University (dropped out)",
                "location": "California",
                "family": "Married, two children"
            }
        },
        client=client
    )
    
    # Create conversation manager
    conversation_manager = ConversationManager(elon, mark)
    
    # Run conversation
    results = await conversation_manager.start_conversation(
        max_turns=6,
        enable_research=True,  # Let them research each other
        save_log="celebrity_conversation.json"
    )
    
    return results


def main():
    """Main entry point"""
    
    async def run_main():
        return await run_predefined_example()    
    return asyncio.run(run_main())


if __name__ == "__main__":
    main()