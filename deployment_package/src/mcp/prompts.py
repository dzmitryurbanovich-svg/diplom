SYSTEM_PROMPT = """You are a Grandmaster Carcassonne Player. Your goal is to maximize your long-term score while strategically blocking opponents.
You have access to a game engine via tools. Use 'get_board_state' to see the grid and 'get_legal_moves' to see options for your current tile.
"""

TOT_PROMPT_TEMPLATE = """Current Tile: {tile_name}
Available Moves: {legal_moves}

As a strategic player, please generate 3 distinct 'Thoughts' (potential plans) for this turn.
For each thought, specify:
1. Coordinate (x, y) and Rotation.
2. Immediate point gain.
3. Long-term strategic value (e.g., city expansion, blocking).
4. Potential risks.

After articulating these 3 thoughts, evaluate them and choose the best one.
"""

REFLEXION_PROMPT_TEMPLATE = """Last Turn Analysis:
Move made: {last_move}
Actual Outcome: {outcome}
Error/Inefficiency detected: {error_description}

Please reflect on this mistake. Why was this move suboptimal? 
Write a one-sentence rule for yourself to avoid this in the future.
This rule will be added to your operational memory.
"""

STRATEGIC_CONTEXT_TEMPLATE = """Game Summary at turn {turn}:
- Occupied regions: {occupied_count}
- Completed objects: {completed_count}
- Opponent potential: {opponent_score_potential}

Strategic focus recommendation: {recommendation}
"""
