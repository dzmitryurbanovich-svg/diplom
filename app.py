import gradio as gr
import urllib.parse

from src.logic.engine import Board
from src.logic.deck import DECK_DEFINITIONS

import base64
import os
from PIL import Image, ImageDraw, ImageOps
import io

ASSETS_CACHE = {}
ASSETS_PIL = {}

# Pre-load HF Token for persistence
HF_TOKEN_DEFAULT = os.environ.get("HF_TOKEN", "")
if not HF_TOKEN_DEFAULT and os.path.exists(".hf_token"):
    try:
        with open(".hf_token", "r") as f:
            HF_TOKEN_DEFAULT = f.read().strip()
    except: pass

def load_assets():
    tiles_dir = "assets/tiles"
    base_names = "ABCDEFGHIJKLMNOPQRSTUVWX"
    for letter in base_names:
        path = f"{tiles_dir}/Base_Game_C3_Tile_{letter}.png"
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
                ASSETS_CACHE[letter] = f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
                ASSETS_PIL[letter] = Image.open(io.BytesIO(data)).convert("RGBA")
                
    meeples_dir = "assets/meeples"
    red_path = f"{meeples_dir}/red_meeple.png"
    if os.path.exists(red_path):
        with open(red_path, "rb") as f:
            data = f.read()
            ASSETS_CACHE["Player1_Meeple"] = f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
            ASSETS_PIL["Player1_Meeple"] = Image.open(io.BytesIO(data)).convert("RGBA")
    
    blue_path = f"{meeples_dir}/blue_meeple.jpg"
    if os.path.exists(blue_path):
        with open(blue_path, "rb") as f:
            data = f.read()
            ASSETS_CACHE["Player2_Meeple"] = f"data:image/jpeg;base64,{base64.b64encode(data).decode('utf-8')}"
            ASSETS_PIL["Player2_Meeple"] = Image.open(io.BytesIO(data)).convert("RGBA")

load_assets()

TILE_LETTER_MAP = {
    "Monastery_Road": "A", "Monastery_Field": "B", "City4_Shield": "C",
    "City1_RoadStraight": "D", "City1_Fields": "E", "City2_Opposite_Shield": "F",
    "City2_Opposite": "G", "City2_Curve": "H", "City2_Curve_Shield": "I",
    "City1_RoadCurve": "J", "City1_RoadCurve_Mirror": "K", "City2_Curve_Road": "L",
    "City2_Curve_Road_Shield": "M", "City2_Curve_Road_NoShield": "N",
    "City1_RoadStraight_Shield": "O", "Crossroad": "P", "TJunction": "Q",
    "RoadStraight": "R", "RoadCurve": "S", "City3": "T", "City3_Shield": "U",
    "City3_Road": "V", "City3_Road_Shield": "W", "CityOpposite_Road": "X",
    "Starter": "D", "CityAdj": "H"
}

class PIL_Renderer:
    """Generates a PIL Image representation of the Carcassonne board state."""
    
    TILE_SIZE = 120 # Slightly larger for better detail
    
    @classmethod
    def render_board(cls, board, last_played=None, ghost_moves=None, selected_coords=None, meeple_hints=None, is_ai_move=False):
        all_points = list(board.grid.keys())
        if ghost_moves:
            all_points.extend([(m[0], m[1]) for m in ghost_moves])
            
        if not all_points: all_points = [(0,0)]
        
        min_x = min(x for x, y in all_points)
        max_x = max(x for x, y in all_points)
        min_y = min(y for x, y in all_points)
        max_y = max(y for x, y in all_points)
        
        # 1-tile padding on edges
        width_tiles = max_x - min_x + 3
        height_tiles = max_y - min_y + 3
        
        canvas = Image.new("RGBA", (width_tiles * cls.TILE_SIZE, height_tiles * cls.TILE_SIZE), (40, 44, 52, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Helper to convert grid to pixel coords
        def get_t_pos(gx, gy):
            tx = (gx - min_x + 1) * cls.TILE_SIZE
            ty = (max_y - gy + 1) * cls.TILE_SIZE
            return tx, ty

        # Render Tiles
        for (gx, gy), tile in board.grid.items():
            tx, ty = get_t_pos(gx, gy)
            letter = TILE_LETTER_MAP.get(tile.name, "D")
            img = ASSETS_PIL.get(letter)
            
            if img:
                # Resize to cell size first
                img_resized = img.resize((cls.TILE_SIZE, cls.TILE_SIZE), Image.LANCZOS)
                # PIL rotate is counter-clockwise, Carcassonne logic is clockwise. 
                # Our tile.rotation is 0, 90, 180, 270 clockwise.
                rotated = img_resized.rotate(-tile.rotation, expand=False, resample=Image.BICUBIC)
                canvas.paste(rotated, (tx, ty), rotated)
            else:
                draw.rectangle([tx, ty, tx+cls.TILE_SIZE-1, ty+cls.TILE_SIZE-1], fill="grey", outline="white")
            
            if (gx, gy) == last_played:
                highlight_color = "#a0fe8c" if is_ai_move else "#ffd166"
                draw.rectangle([tx+1, ty+1, tx+cls.TILE_SIZE-2, ty+cls.TILE_SIZE-2], outline=highlight_color, width=4)

            # Draw Meeples
            for i, seg in enumerate(tile.segments):
                if seg.meeple_player:
                    meeple_img = ASSETS_PIL.get(f"{seg.meeple_player}_Meeple")
                    # Scale meeple
                    m_size = int(cls.TILE_SIZE * 0.3)
                    mx = tx + cls.TILE_SIZE // 2 - m_size // 2 + (i * 4 - 8)
                    my = ty + cls.TILE_SIZE // 2 - m_size // 2 + (i * 4 - 8)
                    if meeple_img:
                        m_resized = meeple_img.resize((m_size, m_size), Image.LANCZOS)
                        canvas.paste(m_resized, (mx, my), m_resized)
                    else:
                        color = (255, 0, 0, 255) if seg.meeple_player == "Player1" else (0, 0, 255, 255)
                        draw.ellipse([mx, my, mx+m_size, my+m_size], fill=color, outline="white")

        # Render Ghosts
        if ghost_moves:
            for gx, gy, rot in ghost_moves:
                tx, ty = get_t_pos(gx, gy)
                is_selected = f"{gx},{gy}" == selected_coords
                opacity = 180 if is_selected else 60
                width = 6 if is_selected else 2
                
                # Draw ghost placeholder
                draw.rectangle([tx+3, ty+3, tx+cls.TILE_SIZE-4, ty+cls.TILE_SIZE-4], 
                               outline=(255, 209, 102, opacity), width=width)
                if is_selected:
                    # Highlight selected ghost
                    overlay = Image.new("RGBA", (cls.TILE_SIZE-6, cls.TILE_SIZE-6), (255, 209, 102, 40))
                    canvas.paste(overlay, (tx+3, ty+3), overlay)
                    
                    # Draw Meeple Hints
                    if meeple_hints:
                        # Draw small indicators for valid meeple spots
                        # We use a simple circular arrangement around the center
                        import math
                        num_hints = len(meeple_hints)
                        for i, (seg_idx, seg_name) in enumerate(meeple_hints):
                            # Position dots in a circle
                            angle = (i / num_hints) * 2 * math.pi if num_hints > 1 else 0
                            dist = cls.TILE_SIZE * 0.25
                            hx = tx + cls.TILE_SIZE // 2 + int(dist * math.cos(angle)) - 5
                            hy = ty + cls.TILE_SIZE // 2 + int(dist * math.sin(angle)) - 5
                            
                            # Use player color for hint
                            hint_color = (255, 209, 102, 255) # Golden for "you can place here"
                            draw.ellipse([hx, hy, hx+10, hy+10], fill=hint_color, outline="white")
                            draw.text((hx+2, hy-12), str(seg_idx), fill="white")

        # Draw Coordinate Grid
        grid_color = (100, 104, 112, 120)
        label_color = (200, 204, 212, 255)
        
        # Vertical lines and X labels (at the bottom)
        for x in range(min_x - 1, max_x + 2):
            tx, _ = get_t_pos(x, max_y + 1)
            draw.line([tx, 0, tx, height_tiles * cls.TILE_SIZE], fill=grid_color, width=1)
            # Center label in tile slot
            draw.text((tx + cls.TILE_SIZE // 2 - 5, height_tiles * cls.TILE_SIZE - 20), str(x), fill=label_color)
            
        # Horizontal lines and Y labels (on the left)
        for y in range(min_y - 1, max_y + 2):
            _, ty = get_t_pos(min_x - 1, y)
            draw.line([0, ty, width_tiles * cls.TILE_SIZE, ty], fill=grid_color, width=1)
            draw.text((5, ty + cls.TILE_SIZE // 2 - 5), str(y), fill=label_color)

        return canvas, (min_x, max_x, min_y, max_y)

import os
import httpx
import asyncio
from src.logic.agents import GreedyAgent, StarAgent, MCTSAgent, HybridLLMAgent

# Simple game orchestrator for the Gradio UI
class GameState:
    def __init__(self, p1_str="Greedy", p2_str="Star2.5", hf_token=""):
        self.board = Board()
        import random
        import copy
        # Deepcopy is strictly required to prevent segment ID and meeple player mutations leaking across games
        self.deck = copy.deepcopy(DECK_DEFINITIONS)
        random.shuffle(self.deck)
        
        # Starter tile always at 0, 0
        starter_idx = next(i for i, t in enumerate(self.deck) if t.name == "Starter")
        starter = self.deck.pop(starter_idx)
        self.board.place_tile(0, 0, starter)
        
        self.scores = {"Player1": 0, "Player2": 0}
        self.meeples = {"Player1": 7, "Player2": 7}
        self.logs = ["[Game Started] Starter tile placed at (0, 0)."]
        self.current_player = "Player1"
        self.game_over = False
        self.last_played = (0, 0)
        
        self.p1_str = p1_str
        self.p2_str = p2_str
        self.agents = {}
        self.hf_token = hf_token or os.environ.get("HF_TOKEN", "")
        if not self.hf_token and os.path.exists(".hf_token"):
            try:
                with open(".hf_token", "r") as f:
                    self.hf_token = f.read().strip()
            except: pass
            
        # Save for persistence
        if self.hf_token:
            try:
                with open(".hf_token", "w") as f:
                    f.write(self.hf_token)
            except: pass

        for p_name, a_str in [("Player1", p1_str), ("Player2", p2_str)]:
            if a_str == "Star2.5": self.agents[p_name] = StarAgent(p_name)
            elif a_str == "MCTS": self.agents[p_name] = MCTSAgent(p_name)
            elif a_str == "Hybrid LLM": self.agents[p_name] = HybridLLMAgent(p_name, self.hf_token)
            elif a_str == "Greedy": self.agents[p_name] = GreedyAgent(p_name)
            else: self.agents[p_name] = None  # None indicates Human
            
        self.pending_human_turn = False
        self.pending_tile = None
        self.pending_legal_moves = []
        self.human_selected_rotation = 0
        self.human_selected_coords = None
        self.board_bounds = (0, 0, 0, 0) # Store min_x, max_x, min_y, max_y
        self.is_running = False

    def step_forward(self):
        """Advances the game. If it's an AI's turn, it executes it completely. 
        If it's a Human's turn, it halts and sets up the human turn state."""
        if not self.deck or self.game_over:
            return self._end_game()
            
        if self.pending_human_turn:
            return self.get_ui_state() # User clicked next but hasn't submitted
            
        tile = self.deck.pop(0)
        
        legal_moves = []
        to_check = set()
        for (x, y) in self.board.grid:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                if (x + dx, y + dy) not in self.board.grid:
                    to_check.add((x + dx, y + dy))
                    
        for tx, ty in to_check:
            for rot in [0, 90, 180, 270]:
                import copy
                test_tile = copy.deepcopy(tile)
                test_tile.rotate(rot // 90)
                if self.board.is_legal_move(tx, ty, test_tile):
                    legal_moves.append((tx, ty, rot))
                    
        if not legal_moves:
            self.logs.append(f"[{self.current_player}] Drew {tile.name} but no legal moves. Discarded.")
            self._switch_player()
            return self.get_ui_state()
            
        agent = self.agents[self.current_player]
        
        if agent is None:  # Human
            self.pending_human_turn = True
            self.pending_tile = tile
            self.pending_legal_moves = legal_moves
            self.human_selected_rotation = 0
            self.human_selected_coords = None
            self.logs.append(f"👤 <b>WAITING</b> for {self.current_player} (Human) to play <b>{tile.name}</b>.")
            return self.get_ui_state()
            
        # AI Turn Execution
        if isinstance(agent, HybridLLMAgent):
            tx, ty, rot, meeple_idx = agent.select_move(self.board, tile, legal_moves, self.meeples[self.current_player], len(self.deck))
            self.logs.append(f"🤖 <b>[LLM THINKING]</b> {self.current_player} (Hybrid LLM) analyzed board.")
        else:
            tx, ty, rot, meeple_idx = agent.select_move(self.board, tile, legal_moves, self.meeples[self.current_player])
            
        self._execute_placement(tile, tx, ty, rot, meeple_idx)
        return self.get_ui_state()
        
    def execute_human_move(self, meeple_str):
        if not self.pending_human_turn:
            return 
            
        if not self.human_selected_coords:
            self.logs.append("⚠️ <b>Alert:</b> Please select a location on the board first! Click one of the gold ghost tiles.")
            return 
            
        try:
            tx, ty = map(int, self.human_selected_coords.split(","))
        except:
            self.logs.append("⚠️ <b>Error:</b> Invalid coordinates selected. Please try again.")
            return
            
        rot = self.human_selected_rotation
        
        meeple_idx = None
        if meeple_str and "None" not in meeple_str:
            try:
                meeple_idx = int(meeple_str.split(" ")[-1])
            except:
                meeple_idx = None
            
        self._execute_placement(self.pending_tile, tx, ty, rot, meeple_idx)
        self.pending_human_turn = False
        self.pending_tile = None
        self.pending_legal_moves = []
        return self.get_ui_state()

    def _execute_placement(self, tile, tx, ty, rot, meeple_idx):
        tile.rotate(rot // 90)
        self.board.place_tile(tx, ty, tile)
        self.last_played = (tx, ty)
        self.logs.append(f"[{self.current_player}] Placed <b>{tile.name}</b> at ({tx}, {ty}) with rot {rot}.")
        
        if meeple_idx is not None and self.meeples[self.current_player] > 0:
            if self.board.place_meeple(tx, ty, meeple_idx, self.current_player):
                self.meeples[self.current_player] -= 1
                self.logs.append(f"[{self.current_player}] Placed MEEPLE on feature at ({tx}, {ty}).")
                
        completed = self.board.get_completed_features()
        for comp in completed:
            for player, count in comp["meeples"].items():
                self.scores[player] += comp["points"]
                self.meeples[player] += count
                self.logs.append(f"🎉 <b>Feature Completed:</b> {comp['type']} (+{comp['points']} pts for {player}). Meeple returned.")
                
        self._switch_player()
        
    def _switch_player(self):
        self.current_player = "Player2" if self.current_player == "Player1" else "Player1"
        
    def _end_game(self):
        if not self.game_over:
            self.game_over = True
            final_scores = self.board.calculate_final_scores()
            for score in final_scores:
                for player, count in score["meeples"].items():
                    self.scores[player] += score["points"]
            self.logs.append(f"<b>[GAME OVER]</b> Final Scoring computed.")
            p1_score = self.scores["Player1"]
            p2_score = self.scores["Player2"]
            if p1_score > p2_score:
                self.logs.append(f"🏆 <b>Winner is Player 1 ({p1_score} vs {p2_score})!</b>")
            elif p2_score > p1_score:
                self.logs.append(f"🏆 <b>Winner is Player 2 ({p2_score} vs {p1_score})!</b>")
            else:
                self.logs.append(f"🤝 <b>It's a TIE ({p1_score} vs {p2_score})!</b>")
        return self.get_ui_state()

    def rotate_human_tile(self):
        if not self.pending_human_turn: return
        self.human_selected_rotation = (self.human_selected_rotation + 90) % 360
        # When rotating, reset selected coordinates as they might no longer be legal
        self.human_selected_coords = None
        return self.get_ui_state()

    def set_human_coords(self, coords_str):
        if not self.pending_human_turn: return
        self.human_selected_coords = coords_str
        return self.get_ui_state()

    def get_ui_state(self):
        # Determine ghost moves for Human interaction
        ghost_moves = []
        human_coord_choices = []
        pending_human = getattr(self, "pending_human_turn", False)
        
        if pending_human:
            # Only show ghost moves for the CURRENTLY selected human rotation
            ghost_moves = [(x, y, r) for x, y, r in self.pending_legal_moves if r == self.human_selected_rotation]
            human_coord_choices = [f"{x},{y}" for x, y, r in ghost_moves]
            
        log_html = "<div style='height:180px; overflow-y:auto; font-family:monospace; background: var(--background-fill-secondary); color: var(--body-text-color); padding:10px; border-radius:5px; border: 1px solid var(--border-color-primary);'>"
        log_html += "<br>".join(reversed(self.logs))
        log_html += "</div>"
        
        # Determine if last move was by AI
        is_ai_move = False
        if getattr(self, "last_played_player", None):
            is_ai_move = self.agents.get(self.last_played_player) is not None

        img_obj, bounds = PIL_Renderer.render_board(self.board, getattr(self, "last_played", None), 
                                               ghost_moves=ghost_moves, 
                                               selected_coords=self.human_selected_coords,
                                               is_ai_move=is_ai_move)
        self.board_bounds = bounds
        
        # Calculate Meeple Hints for the selected coord
        meeple_hints = []
        if pending_human and self.human_selected_coords:
            tx, ty = map(int, self.human_selected_coords.split(","))
            t = self.pending_tile
            # Simulate placement to check legal meeple spots
            import copy
            sim_board = copy.deepcopy(self.board)
            sim_tile = copy.deepcopy(t)
            sim_tile.rotate(self.human_selected_rotation // 90)
            if sim_board.place_tile(tx, ty, sim_tile):
                for i, seg in enumerate(sim_tile.segments):
                    # Check if meeple can be placed there
                    if sim_board.place_meeple(tx, ty, i, self.current_player):
                        meeple_hints.append((i, seg.type.name))
            
            # Re-render with hints
            img_obj, _ = PIL_Renderer.render_board(self.board, getattr(self, "last_played", None), 
                                                 ghost_moves=ghost_moves, 
                                                 selected_coords=self.human_selected_coords,
                                                 meeple_hints=meeple_hints,
                                                 is_ai_move=is_ai_move)
        
        stats = f"""
        ### 📊 Current Score
        - 🔴 **Player 1** ({self.p1_str}): {self.scores['Player1']} pts *(Meeples: {self.meeples['Player1']}/7)*
        - 🔵 **Player 2** ({self.p2_str}): {self.scores['Player2']} pts *(Meeples: {self.meeples['Player2']}/7)*
        
        **Tiles remaining:** {len(self.deck)}/72
        **Current Turn:** {self.current_player}
        """
        
        return img_obj, log_html, stats

_global_state = GameState("Human", "Star2.5")

def _unpack_ui_state(gs):
    img, log, stats = gs.get_ui_state()
    
    # Initialize all UI variables with defaults to prevent UnboundLocalError
    controls_visible = False
    meeple_choices = ["None"]
    meeple_val = "None"
    tile_html_val = "<i>Waiting for turn...</i>"
    hint_val = "Ready. Click 'Next Turn' to proceed."
    
    if gs.pending_human_turn:
        controls_visible = True
        t = gs.pending_tile
        # Apply rotation to preview
        letter = TILE_LETTER_MAP.get(t.name, "D")
        b64 = ASSETS_CACHE.get(letter)
        rot = gs.human_selected_rotation
        tile_html_val = f'''
        <div style="text-align:center;">
            <p style="margin: 0; font-weight: bold;">Draw: {t.name}</p>
            <div style="display: inline-block; transform: rotate({rot}deg); transition: transform 0.3s; margin: 10px 0;">
                <img src="{b64}" width="120" style="margin: 0 auto; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));"/>
            </div>
            <p style="font-size: 0.8em; color: #666; margin: 0;">📍 Click silver spots on the board!</p>
            <p style="margin: 0;">Rotation: {rot}°</p>
        </div>
        '''
        
        hint_val = "💡 <b>Tip:</b> If moves list is empty, try <b>🔄 Rotating</b> the tile!"
        if gs.human_selected_coords:
            hint_val = "📝 <b>Next:</b> Choose if you want to place a 👤 <b>Meeple</b>, then click <b>Confirm Move</b>."
        
        meeple_choices = ["None"] + [f"{s.type.name} - {i}" for i, s in enumerate(t.segments)]
        meeple_val = "None"
        
    return (
        img, log, stats,
        gr.update(visible=controls_visible),
        gr.update(choices=meeple_choices, value=meeple_val),
        gr.update(value=tile_html_val),
        gr.update(value=hint_val)
    )

def step_game():
    _global_state.step_forward()
    return _unpack_ui_state(_global_state)

def rotate_tile():
    _global_state.rotate_human_tile()
    return _unpack_ui_state(_global_state)

def handle_board_click(evt: gr.SelectData):
    """Translates pixel clicks on gr.Image back to grid coordinates."""
    if not _global_state.pending_human_turn:
        return _unpack_ui_state(_global_state)
        
    px, py = evt.index
    min_x, max_x, min_y, max_y = _global_state.board_bounds
    ts = PIL_Renderer.TILE_SIZE
    
    # Reverse logic to get grid coords
    gx = (px // ts) + min_x - 1
    gy = max_y - (py // ts) + 1
    
    # Validation: Only call set_coords if this coordinate is actually a legal move
    # for the current rotation.
    legal_coords = [f"{x},{y}" for x, y, r in _global_state.pending_legal_moves if r == _global_state.human_selected_rotation]
    
    clicked_coord = f"{gx},{gy}"
    if clicked_coord in legal_coords:
        return set_coords(clicked_coord)
    else:
        # Ignore invalid clicks or log them
        _global_state.logs.append(f"⚠️ <b>Invalid Spot:</b> ({gx}, {gy}) is not available for current rotation.")
        return _unpack_ui_state(_global_state)

def game_loop():
    """Generator that runs the game automatically until game over or human turn."""
    _global_state.is_running = True
    
    # Initial state
    yield _unpack_ui_state(_global_state)
    
    while _global_state.is_running:
        if _global_state.game_over:
            _global_state.is_running = False
            yield _unpack_ui_state(_global_state)
            break
            
        if _global_state.pending_human_turn:
            _global_state.is_running = False
            _global_state.logs.append("⏳ <b>Your Turn!</b> Please place the tile.")
            yield _unpack_ui_state(_global_state)
            break
            
        # Step the game
        _global_state.step_forward()
        yield _unpack_ui_state(_global_state)
        
        # Small delay for visual progression
        import time
        time.sleep(0.5)

def set_coords(coords):
    _global_state.set_human_coords(coords)
    return _unpack_ui_state(_global_state)

def submit_human(meeple):
    """Executes the human move and automatically resumes the game loop."""
    _global_state.execute_human_move(meeple)
    
    # After submission, we want to auto-resume the game loop
    # We yield the immediate state first
    yield _unpack_ui_state(_global_state)
    
    # Small pause to let user see their tile placement
    import time
    time.sleep(1.0)
    
    # Resume the loop
    for update in game_loop():
        yield update


def reset_game(p1, p2, token):
    global _global_state
    _global_state = GameState(p1, p2, token)
    return _unpack_ui_state(_global_state)

def change_agents(p1, p2, token):
    _global_state.p1_str = p1
    _global_state.p2_str = p2
    for p_name, a_str in [("Player1", p1), ("Player2", p2)]:
        if a_str == "Star2.5": _global_state.agents[p_name] = StarAgent(p_name)
        elif a_str == "MCTS": _global_state.agents[p_name] = MCTSAgent(p_name)
        elif a_str == "Hybrid LLM": _global_state.agents[p_name] = HybridLLMAgent(p_name, token)
        elif a_str == "Greedy": _global_state.agents[p_name] = GreedyAgent(p_name)
        else: _global_state.agents[p_name] = None
    return _unpack_ui_state(_global_state)

AGENT_CHOICES = ["Human", "Greedy", "Star2.5", "MCTS", "Hybrid LLM"]



with gr.Blocks(title="Carcassonne AI Tournament Viewer") as demo:
    gr.Markdown("# 🏰 Carcassonne AI Tournament Engine")
    gr.Markdown("Watch entirely autonomous agents compete in the classic board game, applying heuristic tree search and LLM-driven strategy.")
    
    with gr.Row():
        with gr.Column(scale=2):
            board_view = gr.Image(interactive=False, type="pil", label="Carcassonne Board", height=500)
            logs_view = gr.HTML(value="Logs will appear here.")
        with gr.Column(scale=1):
            with gr.Row():
                player1_dd = gr.Dropdown(choices=AGENT_CHOICES, value="Greedy", label="🔴 Player 1 AI Mechanism")
                player2_dd = gr.Dropdown(choices=AGENT_CHOICES, value="Star2.5", label="🔵 Player 2 AI Mechanism")
                
            token_input = gr.Textbox(label="Hugging Face Token (Required for Hybrid LLM only)", type="password", placeholder="hf_...", value=HF_TOKEN_DEFAULT)
            stats_view = gr.Markdown(value="Hit Start to begin.")
            
            with gr.Row():
                btn_start = gr.Button("▶️ Start / Resume Game", variant="primary")
                btn_reset = gr.Button("🔄 Reset Board")
                
            # --- HUMAN CONTROLS (Modernized Layout) ---
            with gr.Group(visible=False, elem_id="human_controls") as human_panel:
                gr.Markdown("### 👤 Your Turn!")
                with gr.Row():
                    # Sidebar for tile preview
                    with gr.Column(scale=1):
                        human_tile_display = gr.HTML()
                        human_hint_md = gr.HTML("💡 <b>Hint:</b> Click a gold spot on the board!", elem_classes=["hint-box"])
                    
                    # Main action area
                    with gr.Column(scale=2):
                        with gr.Group():
                            btn_rotate = gr.Button("🔄 Rotate Tile", variant="secondary")
                            human_meeple_dd = gr.Dropdown(label="👤 Meeple Target")
                            human_submit = gr.Button("✅ Confirm Move", variant="primary", elem_classes=["lg-btn"])
                gr.Markdown("---")
            # ------------------------------------------
            
            with gr.Accordion("📖 Help & Token Guide", open=False):
                gr.Markdown("""
                ### 👤 How to Play
                1. Click on the **silver ghost tiles** on the board to select a location.
                2. Use the **🔄 Rotate** button to change tile orientation (ghost positions will update).
                3. Choose a **Meeple Target** if you want to place a follower.
                4. Click **✅ Confirm Move**.
                
                ### 🔑 Using Hybrid LLM
                To use the AI with LLM reasoning, you need a **Hugging Face Token**:
                1. Go to [Hugging Face Tokens](https://huggingface.co/settings/tokens).
                2. Create a 'Read' token and paste it above.
                3. **Pro Tip:** Set `HF_TOKEN` as a 'Secret' in your Space Settings to skip this step!
                """)
            
    # Function wiring: unpack all 7 outputs
    UI_OUTPUTS = [board_view, logs_view, stats_view, human_panel, human_meeple_dd, human_tile_display, human_hint_md]
    
    btn_start.click(fn=game_loop, inputs=[], outputs=UI_OUTPUTS)
    btn_rotate.click(fn=rotate_tile, inputs=[], outputs=UI_OUTPUTS)
    
    # Coordinates click handler
    board_view.select(fn=handle_board_click, inputs=[], outputs=UI_OUTPUTS)
    
    human_submit.click(fn=submit_human, inputs=[human_meeple_dd], outputs=UI_OUTPUTS)
    
    btn_reset.click(fn=reset_game, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)
    player1_dd.change(fn=change_agents, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)
    player2_dd.change(fn=change_agents, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)
    
    # Init
    demo.load(fn=reset_game, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        auth=(os.environ.get("GRADIO_USER", "admin"), os.environ.get("GRADIO_PASSWORD", "carcassonne2024")),
        css="""
        .hint-box { background: var(--amber-50); padding: 5px 10px; border-radius: 8px; border-left: 4px solid var(--amber-500); margin-top: 5px; font-size: 0.85em; }
        #human_controls { border: 1px solid var(--primary-500); padding: 10px; border-radius: 12px; background: var(--background-fill-primary); }
        .lg-btn { height: 45px !important; font-size: 1.1em !important; }
        footer { display: none !important; }
        """
    )
