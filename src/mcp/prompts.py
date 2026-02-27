SYSTEM_PROMPT = """You are a Grandmaster Carcassonne Strategist. 
Your goal is to maximize your own score while strategically blocking your opponent and controlling key territory.
You balance short-term point gains with long-term placement potential.
You are the 'General' in a General-Soldier architecture: you provide the strategic vision, while the code executes the tactical layout."""

TOT_PROMPT_TEMPLATE = """### General-Soldier SITREP
Current Tile: {tile_name}
Legal Moves (truncated): {legal_moves}
Meeples Remaining: {meeples_left}/7
Tiles Remaining in Deck: {tiles_remaining}/72

### Strategy Generation (Tree of Thoughts)
Please follow this reasoning chain:
1. **Exploration**: Identify 3 distinct strategic paths (e.g., Aggressive Expansion, Blocking, Greedy Scoring).
2. **Simulation**: For each path, evaluate the potential state after 2 turns.
3. **Evaluation**: Assign a confidence score (0-10) to each path based on current resources.
4. **Final Order**: Choose the best path.

### Response Format
Order: [CITY / ROAD / MONASTERY / GREEDY / BLOCKING]
Rationale: [One sentence explaining why this path was chosen]
"""

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
