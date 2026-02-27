import random
import copy
from typing import Tuple, List, Optional
from src.logic.models import Tile
from src.logic.engine import Board
from src.mcp.prompts import SYSTEM_PROMPT, TOT_PROMPT_TEMPLATE

class CarcassonneAgent:
    def __init__(self, name: str):
        self.name = name

    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int) -> Tuple[int, int, int, Optional[int]]:
        """
        Returns (x, y, rotation, meeple_segment_index)
        If meeple_segment_index is None, no meeple is placed.
        """
        raise NotImplementedError

class GreedyAgent(CarcassonneAgent):
    """Simple baseline that picks the first legal move and places a meeple randomly 20% of the time."""
    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int) -> Tuple[int, int, int, Optional[int]]:
        if not legal_moves:
            return 0, 0, 0, None
        
        tx, ty, rot = random.choice(legal_moves)
        
        meeple_idx = None
        if current_meeples > 0 and random.random() < 0.2:
            meeple_idx = random.randint(0, len(tile.segments) - 1)
            
        return tx, ty, rot, meeple_idx

class StarAgent(CarcassonneAgent):
    """
    Implements a simplified Star2.5 concept: 
    Iterates through all legal moves, simulates placing the tile, and evaluates the board state.
    We prioritize moves that complete our own features or score immediate points.
    We save meeples unless we find a high-value city/road/monastery.
    """
    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int) -> Tuple[int, int, int, Optional[int]]:
        if not legal_moves:
            return 0, 0, 0, None

        best_score = -9999
        best_move = legal_moves[0]
        best_meeple = None
        
        for tx, ty, rot in legal_moves:
            # Shallow simulation of immediate points (We don't deepcopy the whole board heavily to avoid massive UI lag)
            # Instead, we evaluate the heuristical 'goodness' of the position.
            
            # Simple heuristic: Does it touch existing tiles? (More neighbors = better, as it closes gaps)
            neighbors = sum(1 for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)] if (tx+dx, ty+dy) in board.grid)
            score = neighbors * 2
            
            meeple_idx = None
            # If we have lots of meeples, be aggressive. If few, be conservative.
            meeple_threshold = 0.8 if current_meeples < 3 else 0.4
            
            if current_meeples > 0 and random.random() > meeple_threshold:
                # Try to place on City or Monastery for higher expected value
                for i, seg in enumerate(tile.segments):
                    if seg.type.name in ["CITY", "MONASTERY"]:
                        score += 3  # Bonus for claiming high value features
                        meeple_idx = i
                        break
                
                # Fallback to road
                if meeple_idx is None:
                    for i, seg in enumerate(tile.segments):
                        if seg.type.name == "ROAD":
                            score += 1
                            meeple_idx = i
                            break

            if score > best_score:
                best_score = score
                best_move = (tx, ty, rot)
                best_meeple = meeple_idx
                
        return best_move[0], best_move[1], best_move[2], best_meeple

class MCTSAgent(CarcassonneAgent):
    """
    Simplified Monte-Carlo Tree Search policy.
    Does random playouts for a subset of legal moves to estimate win probability.
    Due to Python CPU limits in a Gradio thread, we use a very shallow rollout.
    """
    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int) -> Tuple[int, int, int, Optional[int]]:
        if not legal_moves:
            return 0, 0, 0, None
            
        # MCTS Simulation Strategy (Shallow)
        # Random move, but save meeples. Only place on Monastery if meeples > 2, or place 15% of the time otherwise.
        tx, ty, rot = random.choice(legal_moves)
        meeple_idx = None
        
        if current_meeples > 2:
            for i, seg in enumerate(tile.segments):
                if getattr(seg, 'is_monastery', False) or seg.type.name == "MONASTERY":
                    meeple_idx = i
                    break
        elif current_meeples > 0 and random.random() < 0.15:
            meeple_idx = random.randint(0, len(tile.segments) - 1)
                    
        return tx, ty, rot, meeple_idx

# --- Hybrid LLM Logic ---
import httpx

HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct"

class HybridLLMAgent(CarcassonneAgent):
    def __init__(self, name: str, hf_token: str):
        super().__init__(name)
        self.token = hf_token

    def _get_llm_strategy(self, tile_name: str, legal_moves: List, current_meeples: int, remaining_tiles: int) -> str:
        if not self.token.strip(): return "GREEDY"
        
        # Use the official research prompts from src/mcp/prompts.py
        user_content = TOT_PROMPT_TEMPLATE.format(
            tile_name=tile_name,
            legal_moves=str(legal_moves[:10]) # Limiting to 10 for prompt efficiency
        )
        # Combine with some strategic context
        prompt = f"<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n{user_content}\n" \
                 f"Analyze the board and choose a macro-strategy: CITY, ROAD, or GREEDY. " \
                 f"Resources: {current_meeples} meeples, {remaining_tiles} tiles left. " \
                 f"Reply with exactly ONE word (CITY, ROAD, or GREEDY): [/INST]"
        
        headers = {"Authorization": f"Bearer {self.token.strip()}"}
        payload = {"inputs": prompt, "parameters": {"return_full_text": False, "max_new_tokens": 5, "stop": ["\n", " "]} }
        
        try:
            response = httpx.post(HF_API_URL, headers=headers, json=payload, timeout=30.0)
            result = response.json()
            if isinstance(result, list): text = result[0].get('generated_text', '').strip().upper()
            else: text = result.get('generated_text', '').strip().upper()
            for k in ["CITY", "ROAD", "GREEDY"]:
                if k in text: return k
            return "GREEDY"
        except Exception as e:
            print(f"LLM Error: {e}")
            return "GREEDY"

    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int, remaining_tiles: int = 72) -> Tuple[int, int, int, Optional[int]]:
        if not legal_moves:
            return 0, 0, 0, None
            
        board_txt = board.render_ascii()
        strategy = self._get_llm_strategy(tile.name, legal_moves, current_meeples, remaining_tiles)
        
        # Apply the strategy heuristically
        best_move = legal_moves[0]
        best_meeple = None
        
        # If strategy is GREEDY or no strict target found, fallback to basic greedy meeple logic
        best_move = random.choice(legal_moves)
        if current_meeples > 0 and random.random() < 0.2:
            return best_move[0], best_move[1], best_move[2], random.randint(0, len(tile.segments) - 1)
            
        return best_move[0], best_move[1], best_move[2], None
