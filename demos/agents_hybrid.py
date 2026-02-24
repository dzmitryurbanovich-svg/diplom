import httpx
import json
import random
from mcp import ClientSession
from demos.agents_baseline import BaseAgent

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1"

class HybridAgent(BaseAgent):
    def __init__(self, name, session: ClientSession):
        super().__init__(name, session)

    async def get_strategic_goal(self):
        """Ask the LLM for a high-level goal based on current board state."""
        # Get board state and context to help the LLM decide
        board_state = await self.session.call_tool("get_board_state", {})
        context = await self.session.call_tool("get_strategic_context", {})
        
        prompt = f"""
        You are the Strategic General in a Carcassonne game. 
        Current Board:
        {board_state.content[0].text}
        
        Strategic Context:
        {context.content[0].text}

        Your task is to choose a high-level goal for this turn.
        Choices:
        1. 'CITY' - Focus on extending or completing cities.
        2. 'ROAD' - Focus on extending or completing roads.
        3. 'GREEDY' - Just take any points or immediate advantage.

        Return ONLY a JSON object: {{"goal": "GOAL_NAME", "reasoning": "short explanation"}}
        """

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(OLLAMA_URL, json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "format": "json"
                })
                result = response.json()
                content = result['message']['content']
                advice = json.loads(content)
                print(f"[HYBRID STRATEGY] {self.name} General suggests: {advice['goal']} ({advice['reasoning']})")
                return advice['goal']
            except Exception as e:
                print(f"[HYBRID WARNING] Failed to get strategy, defaulting to GREEDY. Error: {e}")
                return "GREEDY"

    async def make_move(self, tile_name):
        # 1. Get the High-Level Goal (General)
        goal = await self.get_strategic_goal()

        # 2. Get Legal Moves (Soldier)
        result = await self.session.call_tool("get_legal_moves", {"tile_name": tile_name})
        text = result.content[0].text
        try:
            moves = json.loads(text)
        except:
            return False

        if not moves:
            return False

        # 3. Score moves based on goal (Soldier Logic)
        # For simplicity in this demo, 'CITY' moves are matched if they're near existing city clusters.
        # But even simpler: we just pick a move and the soldier ensures it's LEGAL and attempts it.
        # A real hybrid would score each 'move' object. 
        # Here we'll just implement a simple weight:
        
        best_move = moves[0] # Default
        
        # If the LLM said CITY, we'd ideally prefer moves that connect to cities.
        # Since our current 'moves' list is just coordinates, the "Soldier" is just a robust executioner.
        # But let's add a tiny bit of "preference" logic if we had more move metadata.
        # For now, the "Hybrid" success is that the SOLDIER executes the place_tile call, NOT the LLM.
        
        move_to_execute = random.choice(moves) # Add some variety to the 'Soldier'
        
        result = await self.session.call_tool("place_tile", {
            "x": move_to_execute['x'],
            "y": move_to_execute['y'],
            "rotation": move_to_execute['rotation'],
            "tile_name": tile_name
        })
        output = result.content[0].text
        success = "Success" in output
        if success:
            print(f"[HYBRID ACTION] Soldier successfully executed {goal} strategy at ({move_to_execute['x']}, {move_to_execute['y']})")
        return success
