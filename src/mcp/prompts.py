SYSTEM_PROMPT = """You are a Carcassonne Grandmaster. 
Think carefully about each move. Your goal is to maximize points and block opponents.
Provide your final choice in the format:
ORDER: [CATEGORY]
RATIONALE: [REASON]"""

TOT_PROMPT_TEMPLATE = """### GAME STATE
Tile: {tile_name}
Moves: {legal_moves}
Meeples: {meeples_left}/7
Deck: {tiles_remaining} remaining

### INSTRUCTION
1. Analyze the legal moves.
2. Choose the best strategy (CITY, ROAD, MONASTERY, GREEDY, or BLOCKING).
3. Provide a one-sentence rationale.

### RESPONSE
ORDER: 
RATIONALE: """

# Tool for reflecting on previous bad results
REFLEXION_PROMPT_TEMPLATE = """### Reflexion Cycle
Previous Order: {last_order}
Actual Result: {result_description}
Error Detected: {error}

Analyze why the previous strategy failed. Was it a meeple deficit? A forgotten blocking opportunity?
Update your strategic rules to prevent this in the next cycle."""

SITUATIONAL_AWARENESS_TEMPLATE = """### Battlefield Analysis
- Score Gap: {score_gap}
- Opportunity Cost: {opp_cost}
- Mid-Game Phase Indicators: {phase_info}

Recommendation: {recommendation}
"""
