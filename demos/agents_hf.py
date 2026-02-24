import httpx
import json
import random
import os
from mcp import ClientSession
from demos.agents_baseline import BaseAgent

# Hugging Face Inference API Configuration
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct"
# Token is read from env: export HF_TOKEN=hf_...
HF_TOKEN = os.environ.get("HF_TOKEN", "")

class HFAgent(BaseAgent):
    def __init__(self, name, session: ClientSession):
        super().__init__(name, session)
        self.headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    async def get_strategic_goal(self):
        """Ask the HF Inference API for a strategic keyword: CITY, ROAD, or GREEDY."""
        board_state = await self.session.call_tool("get_board_state", {})
        context = await self.session.call_tool("get_strategic_context", {})

        # Use the simplest possible instruction: one word answer
        # This approach is much more reliable than JSON on HF Inference API
        prompt = (
            f"<s>[INST] You are a Carcassonne AI. Read the board, then reply with exactly one word.\n\n"
            f"Board:\n{board_state.content[0].text}\n\n"
            f"Context:\n{context.content[0].text}\n\n"
            f"Choose your strategy:\n"
            f"  CITY  - extend/complete a city for 2 pts/tile\n"
            f"  ROAD  - build roads for 1 pt/tile\n"
            f"  GREEDY - take any legal placement\n\n"
            f"Reply with ONE word only (CITY, ROAD, or GREEDY): [/INST]"
        )

        payload = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": False,
                "max_new_tokens": 5,       # Only need one word
                "stop": ["\n", " ", ".", ","]
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(HF_API_URL, headers=self.headers, json=payload)
                result = response.json()

                if isinstance(result, list):
                    text = result[0].get('generated_text', '').strip().upper()
                else:
                    text = result.get('generated_text', '').strip().upper()

                # Clean up: extract the first recognized keyword
                goal = "GREEDY"  # default
                for keyword in ["CITY", "ROAD", "GREEDY"]:
                    if keyword in text:
                        goal = keyword
                        break

                reasoning_map = {
                    "CITY": "Completing a city scores 2pts/tile — high priority",
                    "ROAD": "Roads score steadily at 1pt/tile",
                    "GREEDY": "Taking any legal position to keep pace"
                }
                print(f"[HF CLOUD STRATEGY] {self.name} → {goal} ({reasoning_map[goal]})")
                return goal
            except Exception as e:
                print(f"[HF WARNING] Cloud inference failed, defaulting to GREEDY. Error: {e}")
                return "GREEDY"


    async def make_move(self, tile_name):
        # 1. Get the High-Level Goal (Cloud General)
        goal = await self.get_strategic_goal()

        # 2. Get Legal Moves (Local Soldier)
        result = await self.session.call_tool("get_legal_moves", {"tile_name": tile_name})
        text = result.content[0].text
        try:
            moves = json.loads(text)
        except:
            return False

        if not moves:
            return False

        # 3. Soldier Logic: Execute the strategy
        # Simplified: pick a random legal move to demonstrate execution
        move_to_execute = random.choice(moves)
        
        result = await self.session.call_tool("place_tile", {
            "x": move_to_execute['x'],
            "y": move_to_execute['y'],
            "rotation": move_to_execute['rotation'],
            "tile_name": tile_name
        })
        output = result.content[0].text
        success = "Success" in output
        if success:
            print(f"[HF CLOUD ACTION] Soldier executed {goal} strategy at ({move_to_execute['x']}, {move_to_execute['y']})")
        return success
