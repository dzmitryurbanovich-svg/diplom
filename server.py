from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import asyncer
import os
import copy
import random

from src.logic.engine import Board
from src.logic.deck import DECK_DEFINITIONS, create_deck
from src.logic.telemetry import game_telemetry
from src.logic.agents import GreedyAgent, StarAgent, MCTSAgent, HybridLLMAgent
from src.logic.auth_manager import UserAuthManager
import json
import time

LOG_DIR = "game_logs"
os.makedirs(LOG_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/api/debug-ls")
async def debug_list_files():
    files = []
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        dist_path = os.path.join(base_path, "frontend/dist")
        for root, _, filenames in os.walk(dist_path):
            for filename in filenames:
                rel_root = os.path.relpath(root, base_path)
                files.append(os.path.join(rel_root, filename))
        return {"files": files, "cwd": os.getcwd(), "base_path": base_path}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/diag")
async def get_diagnostics():
    from src.logic.telemetry import game_telemetry
    summary_path = os.path.join(game_telemetry.log_dir, "summary_stats.jsonl")
    
    diag = {
        "hf_token_set": bool(os.environ.get("HF_TOKEN")),
        "log_dir": game_telemetry.log_dir,
        "log_dir_exists": os.path.exists(game_telemetry.log_dir),
        "summary_file_exists": os.path.exists(summary_path),
        "summary_file_size": os.path.getsize(summary_path) if os.path.exists(summary_path) else 0,
        "sessions_count": len(sessions),
        "cwd": os.getcwd()
    }
    return diag

class GameSession:
    def __init__(self, p1_str="Human", p2_str="Star2.5"):
        self.p1_type = p1_str
        self.p2_type = p2_str
        self.board = Board()
        self.deck = create_deck()
        random.shuffle(self.deck)
        
        starter_idx = next(i for i, t in enumerate(self.deck) if t.name == "Tile_Starter")
        starter = self.deck.pop(starter_idx)
        starter.name = "Tile_D" # Map to actual asset name
        self.board.place_tile(0, 0, starter)
        
        # Scores and meeples are now managed by the board itself
        self.scores = self.board.scores
        self.meeples = self.board.meeple_counts
        self.logs = ["[Game Started] Starter tile placed at (0, 0)."]
        self.current_player = "Player1"
        self.game_over = False
        self.last_played = (0, 0)
        
        self.hf_token = os.environ.get("HF_TOKEN", "")
            
        self.agents = {}
        for p_name, a_str in [("Player1", p1_str), ("Player2", p2_str)]:
            if a_str == "Star2.5": self.agents[p_name] = StarAgent(p_name)
            elif a_str == "MCTS": self.agents[p_name] = MCTSAgent(p_name)
            elif a_str == "Hybrid LLM": self.agents[p_name] = HybridLLMAgent(p_name, self.hf_token)
            elif a_str == "Greedy": self.agents[p_name] = GreedyAgent(p_name)
            else: self.agents[p_name] = None
            
        self.pending_tile = None
        self.pending_legal_moves = []
        
    def prepare_turn(self):
        if self.game_over: return
        if not self.deck:
            self.game_over = True
            self.board.calculate_final_scores()
            self.logs.append("🏁 **Game Over! Final scores calculated.**")
            
        if self.game_over:
            s1 = self.board.scores.get("Player1", 0)
            s2 = self.board.scores.get("Player2", 0)
            winner = "Player1" if s1 > s2 else "Player2" if s2 > s1 else "Draw"
            print(f"[DEBUG] Finalizing game: s1={s1}, s2={s2}, winner={winner}")
            game_telemetry.finalize_game(self.board.scores, winner)
            return

        self.pending_tile = self.deck.pop(0)
        self.pending_legal_moves = self.board.get_legal_moves(self.pending_tile)
        
        while not self.pending_legal_moves and self.deck:
            self.logs.append(f"⚠️ Tile {self.pending_tile.name} has no valid moves. Discarding.")
            self.pending_tile = self.deck.pop(0)
            self.pending_legal_moves = self.board.get_legal_moves(self.pending_tile)

        if not self.pending_legal_moves:
            self.game_over = True
            self.board.calculate_final_scores()
            self.logs.append("🏁 No legal moves left! Game Over.")

        if self.game_over:
            s1 = self.board.scores.get("Player1", 0)
            s2 = self.board.scores.get("Player2", 0)
            winner = "Player1" if s1 > s2 else "Player2" if s2 > s1 else "Draw"
            print(f"[DEBUG] Finalizing game: s1={s1}, s2={s2}, winner={winner}")
            game_telemetry.finalize_game(self.board.scores, winner)

    def execute_move(self, move_coords, rotation, meeple_target, strategy=None, rationale=None):
        x, y = move_coords
        while self.pending_tile.rotation != rotation:
            self.pending_tile.rotate(1)
            
        placed = self.board.place_tile(x, y, self.pending_tile)
        if not placed: return False, "Failed to place tile."

        self.last_played = (x, y)
        log_msg = f"[{self.current_player}] Placed {self.pending_tile.name} at ({x}, {y}) with rot {rotation}."

        if meeple_target != "None":
            try:
                if "-" in meeple_target:
                    idx = int(meeple_target.split('-')[-1].strip())
                else:
                    idx = int(meeple_target)
                
                if self.board.place_meeple(x, y, idx, self.current_player):
                    log_msg += f" Placed MEEPLE."
            except (ValueError, IndexError):
                pass

        self.logs.append(log_msg)
        self.board.get_completed_features()
        
        # Log this move for training data using unified telemetry
        game_telemetry.log_turn({
            "player": self.current_player,
            "player_type": self.p1_type if self.current_player == "Player1" else self.p2_type,
            "move": {"x": x, "y": y, "rotation": rotation, "meeple": meeple_target},
            "scores": copy.deepcopy(self.board.scores),
            "deck_remaining": len(self.deck),
            "strategy": strategy,
            "rationale": rationale
        }, session_id=f"{self.hf_token if self.hf_token else 'dev'}_{id(self)}")

        self.current_player = "Player2" if self.current_player == "Player1" else "Player1"
        self.pending_tile = None
        self.pending_legal_moves = []
        return True, ""

    # Telemetry is now handled via unified logic in execute_move

sessions: Dict[str, GameSession] = {}

class LoginRequest(BaseModel):
    email: str
    password: str

class StartGameRequest(BaseModel):
    p1_type: str
    p2_type: str

class MoveRequest(BaseModel):
    x: int
    y: int
    rotation: int
    meeple_target: str

@app.post("/api/auth/login")
def login(req: LoginRequest):
    success, msg = UserAuthManager.login(req.email, req.password)
    return {"success": success, "message": msg}

@app.post("/api/auth/register")
def register(req: LoginRequest):
    msg = UserAuthManager.register(req.email, req.password)
    return {"success": "✅" in msg, "message": msg}

@app.post("/api/game/new")
def new_game(req: StartGameRequest):
    sess_id = str(uuid.uuid4())
    sessions[sess_id] = GameSession(req.p1_type, req.p2_type)
    sessions[sess_id].prepare_turn()
    return {"session_id": sess_id}

@app.get("/api/game/{session_id}/state")
def get_state(session_id: str):
    if session_id not in sessions: raise HTTPException(status_code=404, detail="Session not found")
    gs = sessions[session_id]
    grid_data = []
    for (x, y), t in gs.board.grid.items():
        meeple_data = [{"index": i, "player": seg.meeple_player} for i, seg in enumerate(t.segments) if hasattr(seg, 'meeple_player') and seg.meeple_player]
        grid_data.append({"x": x, "y": y, "name": t.name, "rotation": t.rotation, "meeples": meeple_data})
    
    moves = [{"x": x, "y": y, "r": r} for (x, y, r) in gs.pending_legal_moves]
    tile_name = None
    meeple_choices = []
    if gs.pending_tile:
        tile_name = gs.pending_tile.name
        meeple_choices = [{"index": i, "type": s.type.name, "nodes": s.nodes} for i, s in enumerate(gs.pending_tile.segments)]

    return {
        "game_over": gs.game_over, "current_player": gs.current_player, "is_human_turn": gs.agents[gs.current_player] is None,
        "scores": gs.scores, "meeples": gs.meeples, "logs": gs.logs, "deck_remaining": len(gs.deck),
        "grid": grid_data, "pending_tile": tile_name, "legal_moves": moves, "meeple_choices": meeple_choices,
        "last_played": {"x": gs.last_played[0], "y": gs.last_played[1]},
        "player_types": {"Player1": gs.p1_type, "Player2": gs.p2_type}
    }

@app.post("/api/game/{session_id}/move")
async def apply_move(session_id: str, req: MoveRequest):
    if session_id not in sessions: raise HTTPException(status_code=404, detail="Session not found")
    gs = sessions[session_id]
    if gs.game_over: return {"success": False, "message": "Game Over"}
    if gs.agents[gs.current_player] is not None: return {"success": False, "message": "Not a human turn"}
    success, msg = gs.execute_move((req.x, req.y), req.rotation, req.meeple_target)
    if success: gs.prepare_turn()
    return {"success": success, "message": msg}

@app.post("/api/game/{session_id}/ai_step")
async def ai_step_endpoint(session_id: str):
    if session_id not in sessions: raise HTTPException(status_code=404, detail="Session not found")
    gs = sessions[session_id]
    if gs.game_over: return {"success": False, "message": "Game Over"}
    agent = gs.agents[gs.current_player]
    if agent is None: return {"success": False, "message": "Not an AI turn"}
    
    gs.logs.append(f"🤖 [THINKING] {gs.current_player} ({agent.name}) is analyzing board...")
    def sync_ai():
        # Pass both counts: current meeples and remaining tiles
        return agent.select_move(
            gs.board, 
            gs.pending_tile, 
            gs.pending_legal_moves, 
            gs.meeples[gs.current_player],
            len(gs.deck)
        )
    
    try:
        # Agents return (x, y, rot, meeple_idx) or they used to return (best_move, meeple_idx, logs)
        # Looking at src/logic/agents.py, most return x, y, rot, meeple_idx.
        # HybridLLMAgent returns x, y, rot, meeple_idx.
        # But StarAgent and others also return 4 values.
        result = await asyncer.asyncify(sync_ai)()
        if len(result) == 4:
            mx, my, mrot, midx = result
        else:
            move, midx, _ = result
            mx, my, mrot = move
        
        # Capture strategy and rationale for telemetry
        strategy = getattr(agent, 'last_strategy', None)
        rationale = getattr(agent, 'last_rationale', None)
        
        meeple_str = str(midx) if midx is not None else "None"
        success, msg = gs.execute_move((mx, my), mrot, meeple_str, strategy=strategy, rationale=rationale)
        if success: gs.prepare_turn()
        return {"success": success, "message": msg}
    except Exception as e:
        gs.logs.append(f"❌ AI Error: {str(e)}")
        # Fallback move
        if gs.pending_legal_moves:
            mx, my, mrot = random.choice(gs.pending_legal_moves)
            success, msg = gs.execute_move((mx, my), mrot, "None")
            if success: gs.prepare_turn()
            return {"success": success, "message": f"AI Error Fallback: {msg}"}
        return {"success": False, "message": f"AI Error: {str(e)}"}
    return {"success": False, "message": "AI failed to find a move."}

# --- Production Static File Serving (Unified SPA Handler) ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DIST_PATH = os.path.join(BASE_PATH, "frontend/dist")

@app.get("/{path:path}")
async def serve_frontend(path: str):
    # 1. Try to serve exact file from dist
    file_path = os.path.join(DIST_PATH, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 2. Block api 404s
    if path.startswith("api/"):
        raise HTTPException(status_code=404)
        
    # 3. Fallback to index.html for SPA routing
    index_path = os.path.join(DIST_PATH, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": f"Frontend files missing at {DIST_PATH}"}
