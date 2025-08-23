import os
import json
import asyncio
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple, Iterable, Optional

import numpy as np
from dotenv import load_dotenv
from dedalus_labs import AsyncDedalus, DedalusRunner

load_dotenv()

# -----------------------------
# Probabilistic scoring helpers
# -----------------------------

@dataclass
class BetaState:
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def var(self) -> float:
        a, b = self.alpha, self.beta
        n = a + b
        return (a * b) / ((n ** 2) * (n + 1))

    def update(self, x: float, weight: float = 1.0):
        """Update Beta posterior with soft evidence x in [0, 1]."""
        x = max(0.0, min(1.0, float(x)))
        self.alpha += x * weight
        self.beta += (1.0 - x) * weight


def _ewma(values: List[float], alpha: float = 0.4) -> Optional[float]:
    if not values:
        return None
    s = float(values[0])
    for v in values[1:]:
        s = alpha * float(v) + (1 - alpha) * s
    return s


def _slope(values: List[float], window: int = 5) -> float:
    if len(values) < 2:
        return 0.0
    y = np.array(values[-window:], dtype=float)
    x = np.arange(len(y), dtype=float)
    x_centered = x - x.mean()
    denom = float(x_centered @ x_centered)
    if denom == 0.0:
        return 0.0
    return float((x_centered @ (y - y.mean())) / denom)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    a, b = set(a or []), set(b or [])
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union


def _balance(x: float) -> float:
    """Score is highest when x ~ 0.5 (balanced/complementary)."""
    return 1.0 - abs(x - 0.5) * 2.0


# -----------------------------
# Compatibility scoring engine
# -----------------------------

class CompatibilityScorer:
    def __init__(self):
        # Posterior states for each factor
        self.compatibility_factors: Dict[str, BetaState] = {
            'personality_similarity': BetaState(),
            'complementary_traits':   BetaState(),
            'shared_interests':       BetaState(),
            'value_alignment':        BetaState(),
            'communication_style':    BetaState(),
            'lifestyle_compatibility':BetaState(),
            'social_energy':          BetaState(),
        }

        # Weights for overall score
        self.weights: Dict[str, float] = {
            'personality_similarity': 0.20,
            'complementary_traits':   0.15,
            'shared_interests':       0.25,
            'value_alignment':        0.20,
            'communication_style':    0.10,
            'lifestyle_compatibility':0.05,
            'social_energy':          0.05
        }

        # Probabilistic thresholds & stop policy
        self.positive_threshold: float = 0.55
        self.negative_threshold: float = 0.15
        self.confidence: float = 0.90  # need ≥90% belief to stop
        self.min_turns: int = 6        # patience
        self.cooldown: int = 2         # stability across last N decisions

        # Internal history for trend/hysteresis
        self._history_overall: List[float] = []
        self._last_decisions: List[Optional[str]] = []

    # ----- Factor updates -----

    def update_scores(self, observer_profile: dict, observed_traits: dict, conversation_context: dict):
        # Personality similarity
        obs_traits = set(observer_profile.get('personality', {}).get('traits', []))
        trg_traits = set(observed_traits.get('personality_traits', []))
        sim = _jaccard(obs_traits, trg_traits)
        self.compatibility_factors['personality_similarity'].update(sim, weight=2.0 * len(trg_traits or []))

        # Shared interests (merge interests + hobbies)
        oi = set(observer_profile.get('personality', {}).get('interests', []) + observer_profile.get('hobbies', []))
        ti = set(observed_traits.get('interests', []) + observed_traits.get('hobbies', []))
        shared = _jaccard(oi, ti)
        self.compatibility_factors['shared_interests'].update(shared, weight=2.0 * len(oi & ti))

        # Value alignment (goals)
        og = set(observer_profile.get('personality', {}).get('goals', []))
        tg = set(observed_traits.get('goals', []))
        val_sim = _jaccard(og, tg)
        self.compatibility_factors['value_alignment'].update(val_sim, weight=1.5 * len(og & tg))

        # Communication style
        q = 1.0 if conversation_context.get('asks_questions') else 0.0
        thoughtful = 1.0 if conversation_context.get('responds_thoughtfully') else 0.0
        comm = 0.6 * q + 0.4 * thoughtful
        self.compatibility_factors['communication_style'].update(comm, weight=1.0)

        # Lifestyle compatibility
        lifestyle = 0.0
        if abs(observer_profile.get('age', 0) - observed_traits.get('age', 0)) <= 8:
            lifestyle += 0.5
        oloc = observer_profile.get('background', {}).get('location', '')
        tloc = observed_traits.get('location', '')
        if oloc and tloc and oloc.lower() in tloc.lower():
            lifestyle += 0.5
        self.compatibility_factors['lifestyle_compatibility'].update(lifestyle, weight=0.8)

        # Social energy (heuristic)
        token_len = int(conversation_context.get('token_len', 0))
        question_marks = int(conversation_context.get('question_marks', 0))
        t_norm = _clip01(1.0 - min(token_len, 60) / 60.0)   # shorter → higher energy
        q_norm = _clip01(min(question_marks, 3) / 3.0)
        social_energy = 0.5 * t_norm + 0.5 * q_norm
        self.compatibility_factors['social_energy'].update(social_energy, weight=0.5)

        # Complementary traits (introversion–extroversion dyad)
        def infer_IE_from_traits(traits: set) -> Optional[float]:
            cues_ext = {'social', 'outgoing', 'energetic', 'talkative'}
            cues_int = {'reflective', 'quiet', 'thoughtful', 'reserved', 'analytical'}
            e = len(traits & cues_ext)
            i = len(traits & cues_int)
            if e + i == 0:
                return None
            return e / (e + i)

        ie_self = infer_IE_from_traits(obs_traits)
        ie_other = infer_IE_from_traits(trg_traits)
        comp_score = 0.5
        if ie_self is not None and ie_other is not None:
            # Complementarity → balanced dyad near 0.5
            # One simple mapping: balance between one's E and other's I
            # Score high when (self ~ E and other ~ I) OR (self ~ I and other ~ E)
            # We approximate by pushing toward 0.5:
            comp_score = _balance((ie_self + (1.0 - ie_other)) / 2.0)
        self.compatibility_factors['complementary_traits'].update(comp_score, weight=1.0)

    # ----- Overall posterior -----

    def get_overall_posterior_samples(self, n: int = 2000) -> np.ndarray:
        samples = np.zeros(n, dtype=float)
        for k, st in self.compatibility_factors.items():
            w = self.weights[k]
            # Vectorized sampling for speed
            xs = np.random.beta(st.alpha, st.beta, size=n)
            samples += w * xs
        return samples

    def get_overall_point_estimate(self) -> float:
        return sum(self.compatibility_factors[k].mean * self.weights[k] for k in self.compatibility_factors)

    # ----- Stop rule -----

    def should_stop(self, turn_index: int) -> bool:
        # patience
        if (turn_index + 1) < self.min_turns:
            return False

        samples = self.get_overall_posterior_samples(n=3000)
        p_high = float((samples >= self.positive_threshold).mean())
        p_low = float((samples <= self.negative_threshold).mean())
        overall_est = float(samples.mean())

        # record for trend guard
        self._history_overall.append(overall_est)
        sl = _slope(self._history_overall, window=5)
        improving = sl > 0.005  # gentle guard: positive slope → avoid early stop

        decision: Optional[str] = None
        if p_high >= self.confidence and not improving:
            decision = "HIGH"
        elif p_low >= self.confidence and not improving:
            decision = "LOW"
        else:
            decision = None

        self._last_decisions.append(decision)
        self._last_decisions = self._last_decisions[-self.cooldown:]

        if self._last_decisions and all(d == "HIGH" for d in self._last_decisions):
            return True
        if self._last_decisions and all(d == "LOW" for d in self._last_decisions):
            return True

        return False

    def get_compatibility_status(self) -> Tuple[str, str]:
        samples = self.get_overall_posterior_samples(n=3000)
        mean = float(samples.mean())
        lo, hi = np.quantile(samples, [0.05, 0.95])
        p_high = float((samples >= self.positive_threshold).mean())
        p_low = float((samples <= self.negative_threshold).mean())

        if p_high >= self.confidence:
            return "HIGH_COMPATIBILITY", f"Strong potential. Mean={mean:.2f}, 90% CI [{lo:.2f}, {hi:.2f}]"
        elif p_low >= self.confidence:
            return "LOW_COMPATIBILITY", f"Unlikely match. Mean={mean:.2f}, 90% CI [{lo:.2f}, {hi:.2f}]"
        else:
            return "MODERATE_COMPATIBILITY", f"Developing. Mean={mean:.2f}, 90% CI [{lo:.2f}, {hi:.2f}]"


# -----------------------------
# Lightweight personality tracker
# -----------------------------

class PersonalityTracker:
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

    def update_from_conversation(self, message: str):
        """Keyword-based extraction (can be upgraded to real NLP later)."""
        message_lower = message.lower()

        trait_keywords = {
            'adventurous': ['climb', 'adventure', 'explore', 'travel'],
            'creative':    ['write', 'photo', 'art', 'creative', 'music'],
            'analytical':  ['engineer', 'code', 'solve', 'analyze'],
            'nurturing':   ['garden', 'grow', 'care', 'tend'],
            'social':      ['meet', 'friends', 'together', 'share', 'party', 'hang'],
            'curious':     ['wonder', 'curious', 'learn', 'discover']
        }

        for trait, kws in trait_keywords.items():
            if any(k in message_lower for k in kws) and trait not in self.observed_traits['personality_traits']:
                self.observed_traits['personality_traits'].append(trait)

        hobby_keywords = {
            'climbing':     ['climb', 'boulder', 'rock'],
            'cooking':      ['cook', 'recipe', 'food', 'sushi', 'bake'],
            'photography':  ['photo', 'camera', 'picture'],
            'gardening':    ['garden', 'plant', 'grow', 'vegetable'],
            'writing':      ['write', 'story', 'book', 'novel'],
            'coffee':       ['coffee', 'brew', 'roast'],
            'music':        ['guitar', 'piano', 'sing', 'violin', 'band'],
            'running':      ['run', 'marathon', 'jog'],
        }

        for hobby, kws in hobby_keywords.items():
            if any(k in message_lower for k in kws) and hobby not in self.observed_traits['hobbies']:
                self.observed_traits['hobbies'].append(hobby)


# -----------------------------
# Conversation logging
# -----------------------------

class ConversationHistory:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add_message(self, speaker: str, message: str):
        self.history.append({
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def get_history_text(self) -> str:
        if not self.history:
            return "No previous conversation."
        lines = ["Previous conversation:"]
        for entry in self.history:
            lines.append(f"{entry['speaker']}: {entry['message']}")
        return "\n".join(lines)


# -----------------------------
# IO helpers
# -----------------------------

def load_person_data(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        formatted = []
        formatted.append(f"Name: {data.get('name','N/A')}")
        formatted.append(f"Age: {data.get('age','N/A')}")
        formatted.append(f"Occupation: {data.get('occupation','N/A')}")
        hobbies = data.get('hobbies', [])
        if hobbies:
            formatted.append(f"Hobbies: {', '.join(hobbies)}")

        if 'personality' in data:
            p = data['personality']
            if p.get('traits'):
                formatted.append(f"Personality traits: {', '.join(p.get('traits', []))}")
            if p.get('interests'):
                formatted.append(f"Interests: {', '.join(p.get('interests', []))}")
            if p.get('goals'):
                formatted.append(f"Goals: {', '.join(p.get('goals', []))}")

        if 'background' in data:
            b = data['background']
            formatted.append(f"Education: {b.get('education','N/A')}")
            formatted.append(f"Location: {b.get('location','N/A')}")
            formatted.append(f"Family: {b.get('family','N/A')}")

        if 'additional_info' in data:
            add = data['additional_info']
            for k, v in add.items():
                if isinstance(v, list):
                    formatted.append(f"{k.replace('_',' ').title()}: {', '.join(v)}")
                else:
                    formatted.append(f"{k.replace('_',' ').title()}: {v}")

        return data.get('name'), "\n".join(formatted)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return None, None


async def generate_response(client: AsyncDedalus, person_name: str, person_info: str,
                            conversation_history: ConversationHistory, other_person_name: str) -> str:
    runner = DedalusRunner(client)
    history_text = conversation_history.get_history_text()

    prompt = f"""You are {person_name}. Here is your profile:
{person_info}

{history_text}

You are having a conversation with {other_person_name}. Respond as {person_name} would, speaking directly to {other_person_name}.
Be natural, conversational, and true to your personality. Keep your response to 2-3 sentences and end with a question to continue the conversation.
If this is the start of the conversation, introduce yourself briefly and start a friendly conversation with a question."""

    result = await runner.run(
        input=prompt,
        model=["openai/gpt-4.1", "claude-3-5-sonnet-20241022"],
        stream=False
    )
    return result.final_output.strip()


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        safe_text = text.encode('ascii', errors='ignore').decode('ascii')
        print(safe_text)


# -----------------------------
# Main simulation loop
# -----------------------------

async def run_conversation_with_compatibility(max_turns: int = 10):
    client = AsyncDedalus()
    conversation_history = ConversationHistory()

    # Load both person profiles
    alice_name, alice_info = load_person_data("person_alice.json")
    bob_name, bob_info = load_person_data("person_bob.json")
    if not alice_name or not bob_name:
        print("Error loading person profiles.")
        return

    with open("person_alice.json", "r", encoding="utf-8") as f:
        alice_data = json.load(f)
    with open("person_bob.json", "r", encoding="utf-8") as f:
        bob_data = json.load(f)

    # Initialize trackers and scorers
    alice_tracks_bob = PersonalityTracker(bob_name)
    bob_tracks_alice = PersonalityTracker(alice_name)
    alice_view = CompatibilityScorer()  # Alice judging Bob
    bob_view = CompatibilityScorer()    # Bob judging Alice

    print(f"=== Conversation between {alice_name} and {bob_name} ===")
    print("Monitoring compatibility scores (posterior mean and 90% CI)...\n")

    for turn in range(max_turns):
        if turn % 2 == 0:
            current_speaker = alice_name
            current_info = alice_info
            current_data = alice_data
            other_speaker = bob_name
            # when Alice speaks, Bob updates his view of Alice
            updating_tracker = bob_tracks_alice
            updating_scorer = bob_view
            observer_profile = bob_data
        else:
            current_speaker = bob_name
            current_info = bob_info
            current_data = bob_data
            other_speaker = alice_name
            updating_tracker = alice_tracks_bob
            updating_scorer = alice_view
            observer_profile = alice_data

        # Generate response text
        response = await generate_response(
            client, current_speaker, current_info, conversation_history, other_speaker
        )

        # Update personality tracking with what we just observed
        updating_tracker.update_from_conversation(response)

        # Build richer conversation context
        question_marks = response.count('?')
        tokens = len(response.split())
        conversation_context = {
            'asks_questions': question_marks > 0,
            'responds_thoughtfully': tokens >= 12,
            'token_len': tokens,
            'question_marks': question_marks,
        }

        # Update compatibility from the observer's perspective with observed traits
        observed_traits = updating_tracker.observed_traits
        updating_scorer.update_scores(observer_profile, observed_traits, conversation_context)

        # Add to history & print
        conversation_history.add_message(current_speaker, response)
        safe_print(f"{current_speaker}: {response}")

        # Compute posterior summaries for print
        alice_samples = alice_view.get_overall_posterior_samples(n=2000)
        bob_samples = bob_view.get_overall_posterior_samples(n=2000)
        alice_mean, alice_lo, alice_hi = float(alice_samples.mean()), float(np.quantile(alice_samples, 0.05)), float(np.quantile(alice_samples, 0.95))
        bob_mean, bob_lo, bob_hi = float(bob_samples.mean()), float(np.quantile(bob_samples, 0.05)), float(np.quantile(bob_samples, 0.95))
        avg_mean = 0.5 * (alice_mean + bob_mean)

        safe_print(f"[Compatibility] Alice→Bob: mean={alice_mean:.3f} [90% {alice_lo:.3f},{alice_hi:.3f}] | "
                   f"Bob→Alice: mean={bob_mean:.3f} [90% {bob_lo:.3f},{bob_hi:.3f}] | Avg mean={avg_mean:.3f}")

        # Check for conversation termination using improved stop rule
        alice_stop = alice_view.should_stop(turn)
        bob_stop = bob_view.should_stop(turn)

        if alice_stop or bob_stop:
            safe_print("\n=== CONVERSATION ENDED ===")
            a_status, a_msg = alice_view.get_compatibility_status()
            b_status, b_msg = bob_view.get_compatibility_status()
            safe_print(f"Alice's final assessment: {a_msg}")
            safe_print(f"Bob's final assessment: {b_msg}")

            if avg_mean >= 0.55:
                safe_print("HIGH COMPATIBILITY: These two are likely to become good friends!")
            elif avg_mean <= 0.15:
                safe_print("LOW COMPATIBILITY: Friendship is unlikely to develop.")
            else:
                safe_print("MODERATE COMPATIBILITY: Friendship potential is uncertain.")

            # Detailed factor breakdown
            def factor_dump(label: str, scorer: CompatibilityScorer):
                safe_print(f"\n{label}:")
                for factor, st in scorer.compatibility_factors.items():
                    lo, hi = np.quantile(np.random.beta(st.alpha, st.beta, size=3000), [0.05, 0.95])
                    safe_print(f"  {factor.replace('_', ' ').title()}: mean={st.mean:.3f}, 90% CI [{lo:.3f}, {hi:.3f}]")

            factor_dump("Alice’s factor view (of Bob)", alice_view)
            factor_dump("Bob’s factor view (of Alice)", bob_view)
            break

        safe_print("")  # spacing
        await asyncio.sleep(1)

    # If we reached max turns without stopping
    if turn == max_turns - 1:
        safe_print("\n=== CONVERSATION ENDED (MAX TURNS REACHED) ===")
        alice_final = alice_view.get_overall_point_estimate()
        bob_final = bob_view.get_overall_point_estimate()
        avg_final = 0.5 * (alice_final + bob_final)
        safe_print(f"Final average compatibility (point estimate): {avg_final:.3f}")


# -----------------------------
# Entrypoint
# -----------------------------

async def main():
    await run_conversation_with_compatibility(max_turns=10)

if __name__ == "__main__":
    asyncio.run(main())
