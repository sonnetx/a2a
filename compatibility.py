import numpy as np
from typing import Dict, List, Tuple, Iterable, Optional
from dataclasses import dataclass

# Helper functions
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
    
    def get_overall_posterior_samples(self, n: int = 2000) -> np.ndarray:
        samples = np.zeros(n, dtype=float)
        for k, st in self.compatibility_factors.items():
            w = self.weights[k]
            # Vectorized sampling for speed
            xs = np.random.beta(st.alpha, st.beta, size=n)
            samples += w * xs
        return samples
    
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

