import json
import os
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import anthropic
from datetime import datetime

load_dotenv()

@dataclass
class UserProfile:
    """User profile data structure (excluding name, occupation, education, location)"""
    age: int
    hobbies: List[str]
    personality: Dict[str, List[str]]  # traits, interests, goals
    background: Dict[str, str]  # family only
    additional_info: Dict[str, str]  # custom fields based on conversation
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ConversationalProfileAgent:
    """Conversational agent that determines user profile through questions"""
    
    def __init__(self):
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        
        self.client = anthropic.Anthropic(api_key=self.claude_api_key)
        self.conversation_history = []
        self.profile_data = {}
        
    async def ask_claude_for_next_question(self, conversation_so_far: str, profile_gathered: Dict) -> str:
        """Ask Claude to generate the next question based on conversation and profile data gathered"""
        
        prompt = f"""
You are conducting a concise personality profiling interview. Your goal is to efficiently gather ALL required profile information in 4-6 questions maximum.

REQUIRED FIELDS TO COMPLETE:
- age: User's age
- hobbies: List of hobbies and activities they enjoy  
- personality.traits: Personality characteristics (curious, adventurous, creative, etc.)
- personality.interests: Areas of interest (literature, nature, music, technology, etc.)
- personality.goals: Personal goals and aspirations
- background.family: Family situation and relationships
- additional_info: Any interesting specific details

CONVERSATION SO FAR:
{conversation_so_far}

CURRENT PROFILE DATA:
{json.dumps(profile_gathered, indent=2)}

STRATEGY: Ask questions that can gather MULTIPLE profile fields at once. Be efficient but conversational.

RULES:
- Design questions to extract 2-3 profile fields per question when possible
- Be friendly but concise - no unnecessary small talk
- If you have sufficient data for a complete profile, respond with exactly: "PROFILE_COMPLETE"
- Prioritize missing fields over expanding existing ones
- Ask open-ended questions that naturally reveal multiple aspects

Next question:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return self.get_fallback_question(profile_gathered)

    def get_fallback_question(self, profile_gathered: Dict) -> str:
        """Generate fallback questions when Claude API fails"""
        missing_fields = []
        
        if not profile_gathered.get("age"):
            missing_fields.append("age")
        if not profile_gathered.get("hobbies"):
            missing_fields.append("hobbies")
        if not profile_gathered.get("personality", {}).get("traits"):
            missing_fields.append("traits")
        if not profile_gathered.get("personality", {}).get("interests"):
            missing_fields.append("interests")
        if not profile_gathered.get("personality", {}).get("goals"):
            missing_fields.append("goals")
        if not profile_gathered.get("background", {}).get("family"):
            missing_fields.append("family")
        
        # Efficient questions that gather multiple fields
        if "age" in missing_fields and "hobbies" in missing_fields:
            return "How old are you, and what do you like to do in your free time?"
        elif "traits" in missing_fields and "interests" in missing_fields:
            return "What are you passionate about, and how would your friends describe your personality?"
        elif "goals" in missing_fields and "family" in missing_fields:
            return "What are your main goals right now, and how does your family situation influence them?"
        elif missing_fields:
            return f"Tell me about your {missing_fields[0]}."
        else:
            return "PROFILE_COMPLETE"

    async def analyze_response_and_update_profile(self, user_response: str) -> Dict:
        """Analyze user response and extract profile information"""
        
        prompt = f"""
You are analyzing a user's response to extract profile information. 

USER RESPONSE: "{user_response}"

CURRENT PROFILE DATA:
{json.dumps(self.profile_data, indent=2)}

Extract any new information from the user's response and return ONLY a JSON object with the updated profile data. Include these fields:

{{
  "age": number or null,
  "hobbies": [list of hobbies mentioned],
  "personality": {{
    "traits": [personality traits that can be inferred],
    "interests": [areas of interest mentioned],
    "goals": [goals or aspirations mentioned]
  }},
  "background": {{
    "family": "family situation description"
  }},
  "additional_info": {{
    "key": "value pairs for any interesting specific details"
  }}
}}

RULES:
- Only include information that can be reasonably inferred from the response
- Merge with existing data, don't overwrite unless contradicted
- For lists, add new items to existing ones
- For additional_info, create descriptive keys for specific details
- If no new information, return the current profile data unchanged

Return ONLY the JSON object:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Clean up response if it has markdown formatting
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            updated_profile = json.loads(response_text)
            
            # Merge with existing profile data
            self.merge_profile_data(updated_profile)
            return self.profile_data
            
        except Exception as e:
            print(f"Error analyzing response: {e}")
            return self.profile_data

    def merge_profile_data(self, new_data: Dict):
        """Merge new profile data with existing data"""
        for key, value in new_data.items():
            if key == "personality":
                if "personality" not in self.profile_data:
                    self.profile_data["personality"] = {"traits": [], "interests": [], "goals": []}
                
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, list):
                        existing = self.profile_data["personality"].get(subkey, [])
                        # Add new items that aren't already present
                        for item in subvalue:
                            if item not in existing:
                                existing.append(item)
                        self.profile_data["personality"][subkey] = existing
                    else:
                        self.profile_data["personality"][subkey] = subvalue
                        
            elif key == "additional_info":
                if "additional_info" not in self.profile_data:
                    self.profile_data["additional_info"] = {}
                self.profile_data["additional_info"].update(value)
                
            elif isinstance(value, list) and key in self.profile_data:
                # Merge lists
                existing = self.profile_data[key]
                for item in value:
                    if item not in existing:
                        existing.append(item)
                        
            else:
                self.profile_data[key] = value

    async def conduct_interview(self) -> UserProfile:
        """Main interview loop"""
        print("Hi! I'll create your personality profile with just a few quick questions.\n")
        
        conversation_text = ""
        max_questions = 6  # Reduced limit for concise interviews
        question_count = 0
        
        while question_count < max_questions:
            # Get next question from Claude
            next_question = await self.ask_claude_for_next_question(conversation_text, self.profile_data)
            
            if next_question == "PROFILE_COMPLETE":
                print("\nGreat! I think I have enough information to create your profile.")
                break
                
            print(f"\n{next_question}")
            user_response = input("Your answer: ").strip()
            
            if not user_response:
                print("Please provide an answer to continue.")
                continue
                
            # Add to conversation history
            self.conversation_history.append(f"Q: {next_question}")
            self.conversation_history.append(f"A: {user_response}")
            conversation_text = "\n".join(self.conversation_history)
            
            # Analyze response and update profile
            await self.analyze_response_and_update_profile(user_response)
            
            question_count += 1
        
        # Create final profile object
        profile = UserProfile(
            age=self.profile_data.get("age", 25),
            hobbies=self.profile_data.get("hobbies", []),
            personality=self.profile_data.get("personality", {"traits": [], "interests": [], "goals": []}),
            background={"family": self.profile_data.get("background", {}).get("family", "")},
            additional_info=self.profile_data.get("additional_info", {})
        )
        
        return profile

    def save_profile(self, profile: UserProfile, person_name: str = None):
        """Save profile to user-profiles directory"""
        # Create user-profiles directory
        profiles_dir = os.path.join(os.path.dirname(__file__), "user-profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        
        # Generate filename based on person's name
        if person_name:
            # Clean name for filename (replace spaces with underscores, lowercase)
            clean_name = person_name.lower().replace(' ', '_').replace('-', '_')
            filename = f"{clean_name}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_profile_{timestamp}.json"
        
        filepath = os.path.join(profiles_dir, filename)
        
        # Save profile
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"\nProfile saved to: {filepath}")
        return filepath

async def main():
    """Main function to run the conversational profiling agent"""
    import sys
    
    # Check for person name argument
    if len(sys.argv) < 2:
        print("Usage: python agent.py \"Person Name\"")
        sys.exit(1)
    
    person_name = sys.argv[1]
    print(f"Creating profile for: {person_name}")
    
    try:
        agent = ConversationalProfileAgent()
        profile = await agent.conduct_interview()
        
        print("\n" + "="*50)
        print(f"FINAL PROFILE FOR {person_name.upper()}")
        print("="*50)
        print(json.dumps(profile.to_dict(), indent=2, ensure_ascii=False))
        
        # Save profile with person's name
        agent.save_profile(profile, person_name)
        
    except KeyboardInterrupt:
        print("\nInterview interrupted by user.")
    except Exception as e:
        print(f"Error during interview: {e}")

if __name__ == "__main__":
    asyncio.run(main())