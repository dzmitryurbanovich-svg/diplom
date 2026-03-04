from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import asyncer

from src.logic.engine import Board
from src.logic.deck import DECK_DEFINITIONS
from src.logic.agents import GreedyAgent, StarAgent, MCTSAgent, HybridLLMAgent
from src.logic.auth_manager import UserAuthManager
import copy
import random
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Host assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Host frontend build (dist)
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except:
    print("Warning: frontend/dist not found. Frontend will not be served.")

class GameSession:
    def __init__(self, p1_str="Human", p2_str="Star2.5"):
        self.board = Board()
        self.deck = copy.deepcopy(DECK_DEFINITIONS)
        random.shuffle(self.deck)
        
        starter_idx = next(i for i, t in enumerate(self.deck) if t.name == "Tile_Starter")
        starter = self.deck.pop(starter_idx)
        self.board.place_tile(0, 0, starter)
        
        self.scores = {"Player1": 0, "Player2": 0}
        self.meeples = {"Player1": 7, "Player2": 7}
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
            
            # Final scoring
            final_scores = self.board.calculate_final_scores()
            for s in final_scores:
                for p_name in s['meeples']:
                    if p_name in self.scores:
                        self.scores[p_name] += s['points']
            self.logs.append("🏁 **Game Over! Final scores calculated.**")
            return
            
        self.pending_tile = self.deck.pop(0)
        self.pending_legal_moves = self.board.get_legal_moves(self.pending_tile)
        
        while not self.pending_legal_moves and self.deck:
            self.logs.append(f"⚠️ Tile {self.pending_tile.name} has no valid moves. Discarding.")
            self.pending_tile = self.deck.pop(0)
            self.pending_legal_moves = self.board.get_legal_moves(self.pending_tile)
            
        if not self.pending_legal_moves:
            self.game_over = True
            self.logs.append("🏁 No legal moves left! Game Over.")

    def execute_move(self, move_coords, rotation, meeple_target):
        x, y = move_coords
        self.pending_tile.rotation = rotation
        placed = self.board.place_tile(x, y, self.pending_tile)
        if not placed:
            return False, "Failed to place tile."

        self.last_played = (x, y)
        log_msg = f"[{self.current_player}] Placed {self.pending_tile.name} at ({x}, {y}) with rot {rotation}."

        if meeple_target != "None" and self.meeples[self.current_player] > 0:
            if "CITY" in meeple_target or "ROAD" in meeple_target or "FIELD" in meeple_target or "MONASTERY" in meeple_target:
                idx = int(meeple_target.split('-')[-1].strip())
                if self.board.place_meeple(x, y, idx, self.current_player):
                    self.meeples[self.current_player] -= 1
                    log_msg += f" Placed MEEPLE."

        self.logs.append(log_msg)

        # Scoring
        scored_features = self.board.get_completed_features()
        for sf in scored_features:
            pts = sf['points']
            owner_tally = sf['meeples']
            if not owner_tally: continue
            
            max_meeples = max(owner_tally.values())
            winners = [p for p, c in owner_tally.items() if c == max_meeples]
            
            if len(winners) == 1:
                w = winners[0]
                self.scores[w] += pts
                self.logs.append(f"🎉 Feature Completed: {sf['type']} (+{pts} pts for {w}). Meeple returned.")
            else:
                self.logs.append(f"🤝 Tie Feature: {sf['type']} (+{pts} pts for {', '.join(winners)}).")
                for w in winners: self.scores[w] += pts
                
            for p, count in owner_tally.items():
                self.meeples[p] += count

        # Swap player
        self.current_player = "Player2" if self.current_player == "Player1" else "Player1"
        self.pending_tile = None
        self.pending_legal_moves = []
        return True, ""

# Database of sessions
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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    gs = sessions[session_id]
    
    # Serialize grid
    grid_data = []
    for (x, y), t in gs.board.grid.items():
        meeple_data = []
        for i, seg in enumerate(t.segments):
            if hasattr(seg, 'meeple_player') and seg.meeple_player:
                meeple_data.append({"index": i, "player": seg.meeple_player})
        grid_data.append({
            "x": x, "y": y, 
            "name": t.name, 
            "rotation": t.rotation,
            "meeples": meeple_data
        })
        
    # Serialize ghost moves
    moves = [{"x": x, "y": y, "r": r} for (x, y, r) in gs.pending_legal_moves]

    meeple_choices = ["None"]
    tile_name = None
    if gs.pending_tile:
        tile_name = gs.pending_tile.name
        meeple_choices += [f"{s.type.name} - {i}" for i, s in enumerate(gs.pending_tile.segments)]

    # Check if current player is AI or Human
    is_human = gs.agents[gs.current_player] is None
    
    return {
        "game_over": gs.game_over,
        "current_player": gs.current_player,
        "is_human_turn": is_human,
        "scores": gs.scores,
        "meeples": gs.meeples,
        "logs": gs.logs[-10:], # Return last 10 logs
        "deck_remaining": len(gs.deck),
        "grid": grid_data,
        "pending_tile": tile_name,
        "legal_moves": moves,
        "meeple_choices": meeple_choices,
        "last_played": {"x": gs.last_played[0], "y": gs.last_played[1]}
    }

@app.post("/api/game/{session_id}/move")
async def apply_move(session_id: str, req: MoveRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    gs = sessions[session_id]
    if gs.game_over:
        return {"success": False, "message": "Game Over"}
        
    agent = gs.agents[gs.current_player]
    if agent is not None:
        return {"success": False, "message": "Not a human turn"}
        
    success, msg = gs.execute_move((req.x, req.y), req.rotation, req.meeple_target)
    if success:
        gs.prepare_turn()
    return {"success": success, "message": msg}

@app.post("/api/game/{session_id}/ai_step")
async def ai_step_endpoint(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    gs = sessions[session_id]
    if gs.game_over:
        return {"success": False, "message": "Game Over"}
        
    agent = gs.agents[gs.current_player]
    if agent is None:
        return {"success": False, "message": "Not an AI turn"}
        
    gs.logs.append(f"🤖 [THINKING] {gs.current_player} ({agent.name}) is analyzing board...")
    # Because some AI blocking operations take time, run in async execution
    def sync_ai():
        return agent.select_move(gs.board, gs.pending_tile, gs.pending_legal_moves, gs.meeples[gs.current_player] > 0)
        
    try:
        best_move, meeple_idx, ai_logs = await asyncer.asyncify(sync_ai)()
    except Exception as e:
        gs.logs.append(f"❌ AI Error: {str(e)}")
        # Force a random move to prevent lock
        import random
        best_move = random.choice(gs.pending_legal_moves)
        meeple_idx = -1
        
    if best_move:
        mx, my, mrot = best_move
        meeple_str = "None"
        if meeple_idx != -1:
            meeple_str = f"AUTO - {meeple_idx}" # The engine accepts string and splits by -
        
        success, msg = gs.execute_move((mx, my), mrot, meeple_str)
        if success:
            gs.prepare_turn()
        return {"success": success, "message": msg}
    else:
        gs.game_over = True
        return {"success": False, "message": "AI failed to find a move."}
