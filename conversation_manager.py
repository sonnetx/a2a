import asyncio
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

from person_agent import PersonAgent
from personality_tracker import PersonalityTracker
from compatibility import CompatibilityScorer
from dedalus_labs import AsyncDedalus


class ConversationHistory:
    """Manages conversation history and provides context"""
    
    def __init__(self):
        self.history: List[Dict[str, str]] = []
    
    def add_message(self, speaker: str, message: str):
        """Add a message to the conversation history"""
        self.history.append({
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history_text(self, last_n: Optional[int] = None) -> str:
        """Get formatted conversation history"""
        if not self.history:
            return "No previous conversation."
        
        history_to_show = self.history[-last_n:] if last_n else self.history
        lines = ["Previous conversation:"]
        for entry in history_to_show:
            lines.append(f"{entry['speaker']}: {entry['message']}")
        return "\n".join(lines)
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.history)
    
    def get_last_message(self) -> Optional[Dict[str, str]]:
        """Get the last message in the conversation"""
        return self.history[-1] if self.history else None


class ConversationManager:
    """Manages conversations between two PersonAgents with compatibility scoring"""
    
    def __init__(self, agent1: PersonAgent, agent2: PersonAgent):
        self.agent1 = agent1
        self.agent2 = agent2
        self.conversation_history = ConversationHistory()
        
        # Initialize personality trackers (each agent tracks the other)
        self.agent1_tracks_agent2 = PersonalityTracker(agent2.name)
        self.agent2_tracks_agent1 = PersonalityTracker(agent1.name)
        
        # Initialize compatibility scorers (each agent scores the other)
        self.agent1_compatibility = CompatibilityScorer()
        self.agent2_compatibility = CompatibilityScorer()
        
        self.conversation_active = False
        self.turn_count = 0
    
    def _safe_print(self, text: str):
        """Safe printing that handles Unicode errors"""
        try:
            print(text)
        except UnicodeEncodeError:
            safe_text = text.encode('ascii', errors='ignore').decode('ascii')
            print(safe_text)
    
    async def start_conversation(self, max_turns: int = 10, enable_research: bool = True) -> Dict:
        """Start and manage a conversation between the two agents"""
        self.conversation_active = True
        self.turn_count = 0
        
        self._safe_print(f"=== Conversation between {self.agent1.name} and {self.agent2.name} ===")
        
        # Optional: Have agents research each other
        if enable_research:
            self._safe_print("\n--- Research Phase ---")
            await self._research_phase()
        
        self._safe_print("\n--- Conversation Phase ---")
        self._safe_print("Monitoring compatibility scores (posterior mean and 90% CI)...\n")
        
        # Start with agent1's introduction
        introduction = await self.agent1.introduce()
        self._safe_print(f"{self.agent1.name}: {introduction}")
        self.conversation_history.add_message(self.agent1.name, introduction)
        
        # Update tracking based on introduction
        self._update_observations(self.agent1, introduction, is_introduction=True)
        
        # Main conversation loop
        current_speaker = self.agent2  # Agent2 responds to introduction
        other_speaker = self.agent1
        last_message = introduction
        
        for turn in range(max_turns):
            self.turn_count = turn + 1
            
            # Generate response
            response = await current_speaker.respond_to(other_speaker.name, last_message)
            self._safe_print(f"{current_speaker.name}: {response}")
            self.conversation_history.add_message(current_speaker.name, response)
            
            # Update observations and compatibility
            self._update_observations(current_speaker, response)
            
            # Print compatibility scores
            self._print_compatibility_scores()
            
            # Check if conversation should end
            if self._should_end_conversation():
                break
            
            # Switch speakers
            current_speaker, other_speaker = other_speaker, current_speaker
            last_message = response
            
            self._safe_print("")  # spacing
            await asyncio.sleep(0.5)  # Brief pause for readability
        
        return self._end_conversation()
    
    async def _research_phase(self):
        """Have agents research each other"""
        try:
            self._safe_print(f"{self.agent1.name} is researching {self.agent2.name}...")
            research1 = await self.agent1.research_person(self.agent2.name)
            
            self._safe_print(f"{self.agent2.name} is researching {self.agent1.name}...")
            research2 = await self.agent2.research_person(self.agent1.name)
        except Exception as e:
            self._safe_print(f"Research phase encountered issues: {e}")
            self._safe_print("Continuing without research data...")
    
    def _update_observations(self, speaker: PersonAgent, message: str, is_introduction: bool = False):
        """Update personality tracking and compatibility scoring"""
        if speaker == self.agent1:
            # Agent2 observes Agent1
            new_traits = self.agent2_tracks_agent1.update_from_conversation(message)
            context = self.agent2_tracks_agent1.get_conversation_context(message)
            observed_traits = self.agent2_tracks_agent1.get_compatibility_factors()
            
            # Agent2 updates compatibility score for Agent1
            self.agent2_compatibility.update_scores(
                self.agent2.profile_data,
                observed_traits,
                context
            )
            
        else:
            # Agent1 observes Agent2
            new_traits = self.agent1_tracks_agent2.update_from_conversation(message)
            context = self.agent1_tracks_agent2.get_conversation_context(message)
            observed_traits = self.agent1_tracks_agent2.get_compatibility_factors()
            
            # Agent1 updates compatibility score for Agent2
            self.agent1_compatibility.update_scores(
                self.agent1.profile_data,
                observed_traits,
                context
            )
    
    def _print_compatibility_scores(self):
        """Print current compatibility scores"""
        try:
            # Get posterior samples
            agent1_samples = self.agent1_compatibility.get_overall_posterior_samples(n=2000)
            agent2_samples = self.agent2_compatibility.get_overall_posterior_samples(n=2000)
            
            # Calculate statistics
            agent1_mean = float(agent1_samples.mean())
            agent1_lo = float(np.quantile(agent1_samples, 0.05))
            agent1_hi = float(np.quantile(agent1_samples, 0.95))
            
            agent2_mean = float(agent2_samples.mean())
            agent2_lo = float(np.quantile(agent2_samples, 0.05))
            agent2_hi = float(np.quantile(agent2_samples, 0.95))
            
            avg_mean = 0.5 * (agent1_mean + agent2_mean)
            
            self._safe_print(
                f"[Compatibility] {self.agent1.name}→{self.agent2.name}: "
                f"mean={agent1_mean:.3f} [90% {agent1_lo:.3f},{agent1_hi:.3f}] | "
                f"{self.agent2.name}→{self.agent1.name}: "
                f"mean={agent2_mean:.3f} [90% {agent2_lo:.3f},{agent2_hi:.3f}] | "
                f"Avg mean={avg_mean:.3f}"
            )
        except Exception as e:
            self._safe_print(f"[Compatibility] Error calculating scores: {e}")
    
    def _should_end_conversation(self) -> bool:
        """Determine if conversation should end based on compatibility scores"""
        try:
            agent1_stop = self.agent1_compatibility.should_stop(self.turn_count)
            agent2_stop = self.agent2_compatibility.should_stop(self.turn_count)
            return agent1_stop or agent2_stop
        except Exception:
            # If scoring fails, use simple turn-based stopping
            return self.turn_count >= 8
    
    def _end_conversation(self) -> Dict:
        """End conversation and provide final analysis"""
        self.conversation_active = False
        self._safe_print("\n=== CONVERSATION ENDED ===")
        
        try:
            # Get final compatibility assessments
            agent1_status, agent1_msg = self.agent1_compatibility.get_compatibility_status()
            agent2_status, agent2_msg = self.agent2_compatibility.get_compatibility_status()
            
            self._safe_print(f"{self.agent1.name}'s final assessment: {agent1_msg}")
            self._safe_print(f"{self.agent2.name}'s final assessment: {agent2_msg}")
            
            # Calculate overall compatibility
            agent1_final = self.agent1_compatibility.get_overall_point_estimate()
            agent2_final = self.agent2_compatibility.get_overall_point_estimate()
            avg_compatibility = 0.5 * (agent1_final + agent2_final)
            
            # Provide overall assessment
            if avg_compatibility >= 0.55:
                overall_status = "HIGH COMPATIBILITY"
                overall_msg = "These two are likely to become good friends!"
            elif avg_compatibility <= 0.15:
                overall_status = "LOW COMPATIBILITY"
                overall_msg = "Friendship is unlikely to develop."
            else:
                overall_status = "MODERATE COMPATIBILITY"
                overall_msg = "Friendship potential is uncertain."
            
            self._safe_print(f"{overall_status}: {overall_msg}")
            
            # Detailed factor breakdown
            self._print_detailed_factors()
            
            # Conversation statistics
            agent1_stats = self.agent1.get_conversation_stats()
            agent2_stats = self.agent2.get_conversation_stats()
            
            return {
                'overall_compatibility': avg_compatibility,
                'overall_status': overall_status,
                'agent1_compatibility': agent1_final,
                'agent2_compatibility': agent2_final,
                'turn_count': self.turn_count,
                'message_count': self.conversation_history.get_message_count(),
                'agent1_stats': agent1_stats,
                'agent2_stats': agent2_stats,
                'personality_summaries': {
                    f"{self.agent1.name}_observes_{self.agent2.name}": self.agent1_tracks_agent2.get_personality_summary(),
                    f"{self.agent2.name}_observes_{self.agent1.name}": self.agent2_tracks_agent1.get_personality_summary()
                }
            }
        except Exception as e:
            self._safe_print(f"Error generating final analysis: {e}")
            return {
                'error': str(e),
                'turn_count': self.turn_count,
                'message_count': self.conversation_history.get_message_count()
            }
    
    def _print_detailed_factors(self):
        """Print detailed compatibility factor breakdown"""
        def factor_dump(label: str, scorer: CompatibilityScorer):
            self._safe_print(f"\n{label}:")
            try:
                for factor, beta_dist in scorer.compatibility_factors.items():
                    samples = np.random.beta(beta_dist.alpha, beta_dist.beta, size=3000)
                    lo, hi = np.quantile(samples, [0.05, 0.95])
                    self._safe_print(
                        f"  {factor.replace('_', ' ').title()}: "
                        f"mean={beta_dist.mean:.3f}, 90% CI [{lo:.3f}, {hi:.3f}]"
                    )
            except Exception as e:
                self._safe_print(f"  Error calculating factors: {e}")
        
        factor_dump(f"{self.agent1.name}'s factor view (of {self.agent2.name})", self.agent1_compatibility)
        factor_dump(f"{self.agent2.name}'s factor view (of {self.agent1.name})", self.agent2_compatibility)
    
    def save_conversation_log(self, filename: str):
        """Save conversation history and analysis to file"""
        log_data = {
            'participants': [self.agent1.name, self.agent2.name],
            'conversation_history': self.conversation_history.history,
            'final_analysis': self._end_conversation() if not self.conversation_active else None,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)