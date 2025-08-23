from typing import Dict, List, Set
from datetime import datetime


class PersonalityTracker:
    """Tracks observed personality traits, interests, and behaviors from conversation"""
    
    def __init__(self, person_name: str):
        self.person_name = person_name
        self.observed_traits = {
            'personality_traits': [],
            'interests': [],
            'hobbies': [],
            'goals': [],
            'communication_style': [],
            'age': 0,
            'location': '',
            'occupation': ''
        }
        self.observation_history = []
        
        # Enhanced keyword mapping
        self.trait_keywords = {
            'adventurous': ['climb', 'adventure', 'explore', 'travel', 'hike', 'expedition', 'journey'],
            'creative': ['write', 'photo', 'art', 'creative', 'music', 'paint', 'design', 'compose'],
            'analytical': ['engineer', 'code', 'solve', 'analyze', 'data', 'logic', 'research', 'study'],
            'nurturing': ['garden', 'grow', 'care', 'tend', 'help', 'support', 'mentor'],
            'social': ['meet', 'friends', 'together', 'share', 'party', 'hang', 'community', 'network'],
            'curious': ['wonder', 'curious', 'learn', 'discover', 'explore', 'why', 'how', 'question'],
            'organized': ['plan', 'schedule', 'organize', 'structure', 'system', 'routine'],
            'spontaneous': ['spontaneous', 'random', 'sudden', 'impulse', 'whim'],
            'competitive': ['compete', 'win', 'challenge', 'beat', 'race', 'contest'],
            'collaborative': ['team', 'together', 'collaborate', 'cooperate', 'group', 'partnership']
        }
        
        self.hobby_keywords = {
            'climbing': ['climb', 'boulder', 'rock', 'mountain', 'rappel'],
            'cooking': ['cook', 'recipe', 'food', 'sushi', 'bake', 'chef', 'kitchen'],
            'photography': ['photo', 'camera', 'picture', 'lens', 'shoot', 'portrait'],
            'gardening': ['garden', 'plant', 'grow', 'vegetable', 'flower', 'soil'],
            'writing': ['write', 'story', 'book', 'novel', 'blog', 'journal', 'poem'],
            'coffee': ['coffee', 'brew', 'roast', 'espresso', 'latte', 'barista'],
            'music': ['guitar', 'piano', 'sing', 'violin', 'band', 'concert', 'song'],
            'running': ['run', 'marathon', 'jog', 'sprint', 'training', 'race'],
            'reading': ['read', 'book', 'novel', 'library', 'literature'],
            'gaming': ['game', 'play', 'video', 'console', 'pc', 'mobile'],
            'fitness': ['gym', 'workout', 'exercise', 'fitness', 'strength', 'cardio'],
            'travel': ['travel', 'trip', 'vacation', 'visit', 'explore', 'journey']
        }
        
        self.communication_keywords = {
            'enthusiastic': ['!', 'amazing', 'awesome', 'fantastic', 'love', 'excited'],
            'thoughtful': ['think', 'consider', 'reflect', 'ponder', 'contemplate'],
            'direct': ['exactly', 'precisely', 'clearly', 'simply', 'straightforward'],
            'empathetic': ['understand', 'feel', 'relate', 'empathy', 'sorry', 'care'],
            'humorous': ['haha', 'funny', 'joke', 'laugh', 'amusing', 'hilarious'],
            'inquisitive': ['?', 'why', 'how', 'what', 'when', 'where', 'curious']
        }
    
    def update_from_conversation(self, message: str) -> Dict[str, List[str]]:
        """Extract and update observed traits from a conversation message"""
        message_lower = message.lower()
        new_observations = {
            'personality_traits': [],
            'hobbies': [],
            'communication_style': []
        }
        
        # Check for personality traits
        for trait, keywords in self.trait_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if trait not in self.observed_traits['personality_traits']:
                    self.observed_traits['personality_traits'].append(trait)
                    new_observations['personality_traits'].append(trait)
        
        # Check for hobbies/interests
        for hobby, keywords in self.hobby_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if hobby not in self.observed_traits['hobbies']:
                    self.observed_traits['hobbies'].append(hobby)
                    new_observations['hobbies'].append(hobby)
        
        # Check for communication style
        for style, keywords in self.communication_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if style not in self.observed_traits['communication_style']:
                    self.observed_traits['communication_style'].append(style)
                    new_observations['communication_style'].append(style)
        
        # Record observation with timestamp
        if any(new_observations.values()):
            self.observation_history.append({
                'timestamp': datetime.now().isoformat(),
                'message_snippet': message[:100] + "..." if len(message) > 100 else message,
                'new_observations': new_observations
            })
        
        return new_observations
    
    def get_conversation_context(self, message: str) -> Dict[str, any]:
        """Extract contextual information from a message for compatibility scoring"""
        message_lower = message.lower()
        tokens = message.split()
        
        context = {
            'asks_questions': message.count('?') > 0,
            'responds_thoughtfully': len(tokens) >= 12,
            'token_len': len(tokens),
            'question_marks': message.count('?'),
            'exclamation_marks': message.count('!'),
            'shares_personal_info': any(keyword in message_lower for keyword in 
                                     ['i am', 'i like', 'i love', 'i enjoy', 'my', 'i work', 'i live']),
            'shows_interest': any(keyword in message_lower for keyword in 
                                ['you', 'your', 'tell me', 'what about', 'how about']),
            'positive_sentiment': any(keyword in message_lower for keyword in 
                                   ['great', 'amazing', 'love', 'like', 'enjoy', 'fantastic', 'wonderful']),
            'uses_humor': any(keyword in message_lower for keyword in 
                            ['haha', 'lol', 'funny', 'joke', 'laugh']),
            'message_length_category': self._categorize_message_length(len(tokens))
        }
        
        return context
    
    def _categorize_message_length(self, token_count: int) -> str:
        """Categorize message length"""
        if token_count < 5:
            return 'very_short'
        elif token_count < 15:
            return 'short'
        elif token_count < 30:
            return 'medium'
        elif token_count < 50:
            return 'long'
        else:
            return 'very_long'
    
    def get_personality_summary(self) -> str:
        """Generate a summary of observed personality traits"""
        if not any(self.observed_traits.values()):
            return f"No specific traits observed for {self.person_name} yet."
        
        summary_parts = []
        
        if self.observed_traits['personality_traits']:
            summary_parts.append(f"Personality: {', '.join(self.observed_traits['personality_traits'])}")
        
        if self.observed_traits['hobbies']:
            summary_parts.append(f"Interests: {', '.join(self.observed_traits['hobbies'])}")
        
        if self.observed_traits['communication_style']:
            summary_parts.append(f"Communication style: {', '.join(self.observed_traits['communication_style'])}")
        
        return f"{self.person_name} appears to be: " + "; ".join(summary_parts)
    
    def get_compatibility_factors(self) -> Dict[str, List[str]]:
        """Return traits relevant for compatibility assessment"""
        return {
            'personality_traits': self.observed_traits['personality_traits'].copy(),
            'interests': self.observed_traits['hobbies'].copy(),
            'communication_style': self.observed_traits['communication_style'].copy()
        }
    
    def reset_observations(self):
        """Reset all observations (useful for new conversations)"""
        self.observed_traits = {
            'personality_traits': [],
            'interests': [],
            'hobbies': [],
            'goals': [],
            'communication_style': [],
            'age': 0,
            'location': '',
            'occupation': ''
        }
        self.observation_history = []