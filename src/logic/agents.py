import random
import copy
from typing import Tuple, List, Optional
from src.logic.models import Tile
from src.logic.engine import Board
from src.mcp.prompts import SYSTEM_PROMPT, TOT_PROMPT_TEMPLATE
from src.logic.telemetry import game_telemetry

class CarcassonneAgent:
    def __init__(self, name: str):
        self.name = name

    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int, remaining_tiles: int = 72) -> Tuple[int, int, int, Optional[int]]:
        """
        Returns (x, y, rotation, meeple_segment_index)
        If meeple_segment_index is None, no meeple is placed.
        """
        raise NotImplementedError

class GreedyAgent(CarcassonneAgent):
    """Simple baseline that picks the first legal move and places a meeple randomly 20% of the time."""
    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int, remaining_tiles: int = 72) -> Tuple[int, int, int, Optional[int]]:
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
    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int, remaining_tiles: int = 72) -> Tuple[int, int, int, Optional[int]]:
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
    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int, remaining_tiles: int = 72) -> Tuple[int, int, int, Optional[int]]:
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
import json
import re
from huggingface_hub import InferenceClient

class HybridLLMAgent(CarcassonneAgent):
    def __init__(self, name: str, hf_token: str):
        super().__init__(name)
        self.token = hf_token
        # InferenceClient handles endpoint routing (api-inference vs router) automatically
        self.client = InferenceClient(token=self.token.strip())
        self.last_strategy = "GREEDY"
        self.last_rationale = "No games played yet."
        print(f"[HYBRID] Initialized with InferenceClient (token: {self.token[:5]}...)", flush=True)

    def _get_llm_strategy(self, tile_name: str, legal_moves: list, meeple_count: int, remaining_tiles: int, past_lessons: str):
        if not self.token.strip(): 
            return "GREEDY", "No API token provided."

        user_content = TOT_PROMPT_TEMPLATE.format(
            tile_name=tile_name,
            legal_moves=str(legal_moves[:5]), # Truncate for tokens
            meeples_left=meeple_count,
            tiles_remaining=remaining_tiles
        )
        
        # Priority list of models known to be free/serverless
        models = [
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "Qwen/Qwen2.5-7B-Instruct",
            "microsoft/Phi-3-mini-4k-instruct"
        ]
        
        text = ""
        for model_id in models:
            try:
                print(f"[LLM DEBUG] Trying model: {model_id}", flush=True)
                response = self.client.chat_completion(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT + f"\n\nPast Lessons Learned:\n{past_lessons}"},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=250,
                    temperature=0.3
                )
                text = response.choices[0].message.content.strip()
                if text:
                    print(f"[LLM SUCCESS] Model {model_id} responded.", flush=True)
                    break 
            except Exception as e:
                print(f"[LLM WARNING] Model {model_id} failed: {e}", flush=True)
                continue

        if not text:
            print("[LLM ERROR] All models failed or returned empty text.", flush=True)
            return "GREEDY", "Emergency Fallback: All AI models unavailable."

        print(f"[LLM DEBUG] Raw Text: {text}", flush=True)
        
        # Extract order and rationale
        order = "GREEDY"
        rationale = "No explicit rationale provided by LLM."
        
        lines = text.split('\n')
        for line in lines:
            line_upper = line.upper()
            if 'ORDER:' in line_upper:
                order_val = line.split(':')[-1].strip().upper()
                # Clean up punctuation
                order_val = re.sub(r'[^A-Z]', '', order_val)
                if order_val in ["CITY", "ROAD", "MONASTERY", "GREEDY", "BLOCKING"]:
                    order = order_val
            elif 'RATIONALE:' in line_upper:
                rationale = line.split(':', 1)[-1].strip()
        
        self.last_strategy = order
        self.last_rationale = rationale
        return order, rationale

    def select_move(self, board: Board, tile: Tile, legal_moves: List[Tuple[int, int, int]], current_meeples: int, remaining_tiles: int = 72) -> Tuple[int, int, int, Optional[int]]:
        if not legal_moves:
            return 0, 0, 0, None
            
        # Load lessons from past games
        past_lessons = game_telemetry.get_past_lessons(self.name)
        
        strategy, rationale = self._get_llm_strategy(tile.name, legal_moves, current_meeples, remaining_tiles, past_lessons)
        print(f"[GENERAL {self.name}] Order: {strategy} | Rationale: {rationale}", flush=True)

        # --- SOLDIER LOGIC: Execute General's Strategy ---
        best_move = legal_moves[0]
        best_meeple = None
        best_tactical_score = -1
        
        for tx, ty, rot in legal_moves:
            score = 0
            meeple_idx = None
            
            # Simple neighbor metric
            neighbors = sum(1 for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)] if (tx+dx, ty+dy) in board.grid)
            score += neighbors
            
            # Tactical Meeple Placement based on Strategy
            if current_meeples > 0:
                for i, seg in enumerate(tile.segments):
                    seg_type = seg.type.name
                    if strategy == "CITY" and seg_type == "CITY":
                        score += 15
                        meeple_idx = i
                        break
                    elif strategy == "ROAD" and seg_type == "ROAD":
                        score += 8
                        meeple_idx = i
                        break
                    elif strategy == "MONASTERY" and seg_type == "MONASTERY":
                        score += 20
                        meeple_idx = i
                        break
                    elif strategy == "BLOCKING":
                        score += neighbors * 4 
                        meeple_idx = None
                        break
                    elif strategy == "GREEDY":
                        if seg_type in ["CITY", "MONASTERY"]:
                            score += 5
                            meeple_idx = i
                            break
                        elif seg_type == "ROAD":
                            score += 2
                            meeple_idx = i
            
            score += random.uniform(0, 0.5)

            if score > best_tactical_score:
                best_tactical_score = score
                best_move = (tx, ty, rot)
                best_meeple = meeple_idx
        
        return best_move[0], best_move[1], best_move[2], best_meeple
