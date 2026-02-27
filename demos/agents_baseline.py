import random
import json
from mcp import ClientSession

class BaseAgent:
    def __init__(self, name, session: ClientSession):
        self.name = name
        self.session = session

    async def make_move(self, tile_name):
        raise NotImplementedError

class RandomAgent(BaseAgent):
    async def make_move(self, tile_name):
        # 1. Get legal moves
        result = await self.session.call_tool("get_legal_moves", {"tile_name": tile_name})
        # The tool returns a string: "Legal moves for starter: [{'x': 0, 'y': 0, 'rotation': 0}, ...]"
        # We need to parse it or have the tool return JSON. 
        # For simplicity in this demo, we'll parse the string or I'll update the server to be more "structured".
        text = result.content[0].text
        try:
            moves = json.loads(text)
        except Exception as e:
            print(f"[DEBUG] {self.name} failed to parse JSON: {e}. Text: {text}")
            return False

        if not moves:
            print(f"[DEBUG] {self.name} got empty moves list for {tile_name}")
            return False
        
        move = random.choice(moves)
        result = await self.session.call_tool("place_tile", {
            "x": move['x'],
            "y": move['y'],
            "rotation": move['rotation'],
            "tile_name": tile_name
        })
        return "Success" in result.content[0].text

class GreedyAgent(BaseAgent):
    async def make_move(self, tile_name):
        # 1. Get legal moves
        result = await self.session.call_tool("get_legal_moves", {"tile_name": tile_name})
        text = result.content[0].text
        try:
            moves = json.loads(text)
        except Exception as e:
            print(f"[DEBUG] {self.name} failed to parse JSON: {e}. Text: {text}")
            return False

        if not moves:
            print(f"[DEBUG] {self.name} got empty moves list for {tile_name}")
            return False
        
        move = moves[0] # Pick first legal move
        result = await self.session.call_tool("place_tile", {
            "x": move['x'],
            "y": move['y'],
            "rotation": move['rotation'],
            "tile_name": tile_name
        })
        output = result.content[0].text
        if "Success" not in output:
             print(f"[DEBUG] {self.name} place_tile failed: {output}")
        return "Success" in output
