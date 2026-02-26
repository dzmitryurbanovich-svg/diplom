import gradio as gr
import urllib.parse

from src.logic.engine import Board
from src.logic.deck import DECK_DEFINITIONS

import base64
import os

ASSETS_CACHE = {}

def load_assets():
    tiles_dir = "assets/tiles"
    base_names = "ABCDEFGHIJKLMNOPQRSTUVWX"
    for letter in base_names:
        path = f"{tiles_dir}/Base_Game_C3_Tile_{letter}.png"
        if os.path.exists(path):
            with open(path, "rb") as f:
                ASSETS_CACHE[letter] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
                
    meeples_dir = "assets/meeples"
    red_path = f"{meeples_dir}/red_meeple.png"
    if os.path.exists(red_path):
        with open(red_path, "rb") as f:
            ASSETS_CACHE["Player1_Meeple"] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    
    blue_path = f"{meeples_dir}/blue_meeple.jpg"
    if os.path.exists(blue_path):
        with open(blue_path, "rb") as f:
            ASSETS_CACHE["Player2_Meeple"] = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

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

class SVG_Renderer:
    """Generates an SVG map representation of the Carcassonne board state using real image assets."""
    
    TILE_SIZE = 100
    
    @classmethod
    def render_board(cls, board, last_played=None, ghost_moves=None, selected_coords=None) -> str:
        if not board.grid and not ghost_moves:
            return "<div style='text-align:center; padding:50px; color:#666;'>Game has not started.</div>"
            
        all_points = list(board.grid.keys())
        if ghost_moves:
            all_points.extend([(m[0], m[1]) for m in ghost_moves])
            
        if not all_points: all_points = [(0,0)]
        
        min_x = min(x for x, y in all_points)
        max_x = max(x for x, y in all_points)
        min_y = min(y for x, y in all_points)
        max_y = max(y for x, y in all_points)
        
        # Add 1.0 padding to ensure visibility of ghosts and edges
        v_min_x = min_x - 1.0
        v_min_y = min_y - 1.0
        v_width = (max_x - min_x + 3) 
        v_height = (max_y - min_y + 3)
        
        # We use a fixed aspect ratio container
        svg = [f'<div id="carcassonne_board" style="width: 100%; height: 500px; background: var(--background-fill-secondary); border: 2px solid var(--border-color-primary); border-radius: 12px; overflow: hidden; display:flex; justify-content:center; align-items:center;">']
        svg.append(f'<svg viewBox="{v_min_x * cls.TILE_SIZE} {- (max_y + 1.5) * cls.TILE_SIZE} {v_width * cls.TILE_SIZE} {v_height * cls.TILE_SIZE}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">')
        
        # Render actual tiles
        for (x, y), tile in board.grid.items():
            px = x * cls.TILE_SIZE
            py = - (y + 1) * cls.TILE_SIZE
            is_last = (x, y) == last_played
            svg.append(cls.render_tile(tile, px, py, is_last=is_last))
            
        # Render Ghosts
        if ghost_moves:
            for mx, my, mrot in ghost_moves:
                px = mx * cls.TILE_SIZE
                py = - (my + 1) * cls.TILE_SIZE
                is_selected = f"{mx},{my}" == selected_coords
                svg.append(cls.render_ghost(px, py, mx, my, is_selected=is_selected))
            
        svg.append('</svg></div>')
        
        # Inject JavaScript to handle clicks AND drops on ghosts
        js = f"""
        <script>
        function sendCarcassonneCoord(x, y) {{
            const val = x + "," + y;
            console.log("Carcassonne: Sending coord", val);
            const msg = {{ type: 'carcassonne_place', coords: val }};
            // 1. Try local update
            if (window.set_carcassonne_coords) window.set_carcassonne_coords(x, y);
            // 2. Post to self
            window.postMessage(msg, '*');
            // 3. Post to parent (Hugging Face frame)
            if (window.parent && window.parent !== window) {{
                window.parent.postMessage(msg, '*');
            }}
        }}

        function onGhostDrop(event, x, y) {{
            event.preventDefault();
            console.log("Carcassonne: Tile dropped at", x, y);
            sendCarcassonneCoord(x, y);
            event.target.setAttribute('fill-opacity', '0.7');
        }}

        function onGhostDragOver(event) {{
            event.preventDefault();
            event.target.setAttribute('fill-opacity', '0.9');
            event.target.setAttribute('stroke-width', '6');
        }}

        function onGhostDragLeave(event) {{
            event.target.setAttribute('fill-opacity', '0.3');
            event.target.setAttribute('stroke-width', '2');
        }}
        </script>
        """
        return "\n".join(svg) + js
        
    @classmethod
    def render_ghost(cls, px, py, mx, my, is_selected=False) -> str:
        s = cls.TILE_SIZE
        opacity = "0.7" if is_selected else "0.3"
        stroke_width = "5" if is_selected else "2"
        dash = "none" if is_selected else "5,5"
        # Clickable AND Droppable ghost tile
        return f'''<rect x="{px+2}" y="{py+2}" width="{s-4}" height="{s-4}" rx="10" 
            fill="#ffd166" fill-opacity="{opacity}" stroke="#ffd166" stroke-width="{stroke_width}" stroke-dasharray="{dash}" 
            cursor="pointer" style="pointer-events: all;" 
            onclick="sendCarcassonneCoord({mx}, {my})"
            ondragover="onGhostDragOver(event)"
            ondragleave="onGhostDragLeave(event)"
            ondrop="onGhostDrop(event, {mx}, {my})"/>'''

        
    @classmethod
    def render_tile(cls, tile, px, py, is_last=False) -> str:
        s = cls.TILE_SIZE
        
        g = [f'<g transform="translate({px}, {py})">']
        
        letter = TILE_LETTER_MAP.get(tile.name, "D")
        b64_img = ASSETS_CACHE.get(letter)
        
        if b64_img:
            # SVG rotate is clockwise. We rotate the image precisely around the tile center (s/2, s/2)
            rot = tile.rotation 
            g.append(f'<image href="{b64_img}" width="{s}" height="{s}" transform="rotate({rot} {s/2} {s/2})"/>')
        else:
            g.append(f'<rect width="{s}" height="{s}" fill="#ccc" stroke="#333"/>')
            
        if is_last:
            g.append(f'<rect width="{s}" height="{s}" fill="none" stroke="#ffd166" stroke-width="6" stroke-dasharray="10,5"/>')
            
        # Draw Meeples
        for i, seg in enumerate(tile.segments):
            if seg.meeple_player:
                meeple_img = ASSETS_CACHE.get(f"{seg.meeple_player}_Meeple")
                # Add some semi-random offset so meeples aren't perfectly dead center every single time
                ox = s/2 + (i * 8 - 12) - 15  # -15 to center the 30x30 meeple
                oy = s/2 + (i * 8 - 12) - 15
                if meeple_img:
                    g.append(f'<image href="{meeple_img}" x="{ox}" y="{oy}" width="30" height="30"/>')
                else:
                    color = "#e63946" if seg.meeple_player == "Player1" else "#1d3557"
                    g.append(f'<circle cx="{ox+15}" cy="{oy+15}" r="6" fill="{color}" stroke="#fff" stroke-width="2"/>')
                

        g.append('</g>')
        return "\n".join(g)

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
        for p_name, a_str in [("Player1", p1_str), ("Player2", p2_str)]:
            if a_str == "Star2.5": self.agents[p_name] = StarAgent(p_name)
            elif a_str == "MCTS": self.agents[p_name] = MCTSAgent(p_name)
            elif a_str == "Hybrid LLM": self.agents[p_name] = HybridLLMAgent(p_name, hf_token)
            elif a_str == "Greedy": self.agents[p_name] = GreedyAgent(p_name)
            else: self.agents[p_name] = None  # None indicates Human
            
        self.pending_human_turn = False
        self.pending_tile = None
        self.pending_legal_moves = []
        self.human_selected_rotation = 0
        self.human_selected_coords = None

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

    def get_ui_state(self):
        # Determine ghost moves for Human interaction
        ghost_moves = []
        human_coord_choices = []
        if self.pending_human_turn:
            # Only show ghost moves for the CURRENTLY selected human rotation
            ghost_moves = [(x, y, r) for x, y, r in self.pending_legal_moves if r == self.human_selected_rotation]
            human_coord_choices = [f"{x},{y}" for x, y, r in ghost_moves]
            
        log_html = "<div style='height:400px; overflow-y:auto; font-family:monospace; background: var(--background-fill-secondary); color: var(--body-text-color); padding:10px; border-radius:5px; border: 1px solid var(--border-color-primary);'>"
        log_html += "<br>".join(reversed(self.logs))
        log_html += "</div>"
        
        svg = SVG_Renderer.render_board(self.board, getattr(self, "last_played", None), ghost_moves=ghost_moves, selected_coords=self.human_selected_coords)
        
        stats = f"""
        ### 📊 Current Score
        - 🔴 **Player 1** ({self.p1_str}): {self.scores['Player1']} pts *(Meeples: {self.meeples['Player1']}/7)*
        - 🔵 **Player 2** ({self.p2_str}): {self.scores['Player2']} pts *(Meeples: {self.meeples['Player2']}/7)*
        
        **Tiles remaining:** {len(self.deck)}/72
        **Current Turn:** {self.current_player}
        """
        
        return svg, log_html, stats, human_coord_choices

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

_global_state = GameState("Human", "Star2.5")

def _unpack_ui_state(gs):
    svg, log, stats, coord_choices = gs.get_ui_state()
    
    # Initialize all UI variables with defaults to prevent UnboundLocalError
    controls_visible = False
    coord_val = "None"
    meeple_choices = ["None"]
    meeple_val = "None"
    tile_html_val = "<i>Waiting for turn...</i>"
    hint_val = "Ready. Click 'Next Turn' to proceed."
    coord_dd_val = None
    
    if gs.pending_human_turn:
        controls_visible = True
        t = gs.pending_tile
        # Apply rotation to preview
        letter = TILE_LETTER_MAP.get(t.name, "D")
        b64 = ASSETS_CACHE.get(letter)
        rot = gs.human_selected_rotation
        tile_html_val = f'''
        <div style="text-align:center;">
            <p><b>Draw: {t.name}</b></p>
            <div draggable="true" ondragstart="event.dataTransfer.setData('text/plain', 'tile')" style="cursor: grab; display: inline-block; transform: rotate({rot}deg); transition: transform 0.3s;">
                <img src="{b64}" width="120" style="margin: 0 auto; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));"/>
                <p style="font-size: 0.8em; color: #666; margin-top: 5px;">↔️ Drag or Click the board!</p>
            </div>
            <p>Rotation: {rot}°</p>
        </div>
        '''
        
        if not gs.human_selected_coords:
            coord_val = "📍 Click or select coordinates below"
            hint_val = "💡 <b>Tip:</b> If moves list is empty, try <b>🔄 Rotating</b> the tile!"
        else:
            coord_val = f"✅ Selected: **({gs.human_selected_coords})**"
            hint_val = "📝 <b>Next:</b> Choose if you want to place a 👤 <b>Meeple</b>, then click <b>Confirm Move</b>."
            coord_dd_val = gs.human_selected_coords
        
        meeple_choices = ["None"] + [f"{s.type.name} - {i}" for i, s in enumerate(t.segments)]
        meeple_val = "None"
        
    return (
        svg, log, stats,
        gr.update(visible=controls_visible),
        gr.update(value=coord_val),
        gr.update(choices=meeple_choices, value=meeple_val),
        gr.update(value=tile_html_val),
        gr.update(value=hint_val),
        gr.update(choices=coord_choices, value=coord_dd_val)
    )

def step_game():
    _global_state.step_forward()
    return _unpack_ui_state(_global_state)

def rotate_tile():
    _global_state.rotate_human_tile()
    return _unpack_ui_state(_global_state)

def set_coords(coords):
    _global_state.set_human_coords(coords)
    return _unpack_ui_state(_global_state)

def submit_human(meeple):
    _global_state.execute_human_move(meeple)
    return _unpack_ui_state(_global_state)


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

HEAD_JS = """
<script>
// Global bridge function
window.set_carcassonne_coords = function(x, y) {
    console.log("Carcassonne API: Setting coords to", x, y);
    const input = document.querySelector('#hidden_coord_input textarea') || 
                  document.querySelector('#hidden_coord_input input');
    if (input) {
        input.value = x + "," + y;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
};

// Listen for messages from inside IFrames (for Hugging Face)
window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'carcassonne_place') {
        console.log("Carcassonne BRIDGE: Message received", event.data.coords);
        const parts = event.data.coords.split(",");
        window.set_carcassonne_coords(parts[0], parts[1]);
    }
});
</script>
"""

with gr.Blocks(title="Carcassonne AI Tournament Viewer") as demo:
    gr.Markdown("# 🏰 Carcassonne AI Tournament Engine")
    gr.Markdown("Watch entirely autonomous agents compete in the classic board game, applying heuristic tree search and LLM-driven strategy.")
    
    with gr.Row():
        with gr.Column(scale=2):
            board_view = gr.HTML(value="")
        with gr.Column(scale=1):
            with gr.Row():
                player1_dd = gr.Dropdown(choices=AGENT_CHOICES, value="Greedy", label="🔴 Player 1 AI Mechanism")
                player2_dd = gr.Dropdown(choices=AGENT_CHOICES, value="Star2.5", label="🔵 Player 2 AI Mechanism")
                
            token_input = gr.Textbox(label="Hugging Face Token (Required for Hybrid LLM only)", type="password", placeholder="hf_...", value=os.environ.get("HF_TOKEN", ""))
            stats_view = gr.Markdown(value="Hit start to begin.")
            
            with gr.Row():
                btn_step = gr.Button("▶️ Next Turn", variant="primary")
                btn_auto = gr.Button("⏩ Auto-Play (x10)", variant="secondary")
                btn_reset = gr.Button("🔄 Reset Board")
                
            # --- HUMAN CONTROLS (Hidden by default) ---
            with gr.Group(visible=False, elem_id="human_controls") as human_panel:
                gr.Markdown("### 👤 Your Turn!")
                with gr.Row():
                    human_tile_display = gr.HTML()
                    with gr.Column():
                        btn_rotate = gr.Button("🔄 Rotate Tile")
                        human_coord_display = gr.Markdown("Click a gold spot on the board!")
                        human_coord_dd = gr.Dropdown(label="Select Location (Fallback)", choices=[])
                        human_meeple_dd = gr.Dropdown(label="Meeple Target")
                        human_submit = gr.Button("✅ Confirm Move", variant="primary")
                human_hint_md = gr.HTML("💡 <b>Hint:</b> Click a gold spot on the board!", elem_classes=["hint-box"])
                
                # Hidden textbox to receive coordinate clicks from SVG
                # We keep it visible=True but use CSS to hide it, ensuring it exists in the DOM
                hidden_coords = gr.Textbox(visible=True, elem_id="hidden_coord_input", label="Internal Coord", container=False)
                gr.Markdown("---")
            # ------------------------------------------
            
            logs_view = gr.HTML(value="Logs will appear here.")
            
    # Function wiring: unpack all 9 outputs
    UI_OUTPUTS = [board_view, logs_view, stats_view, human_panel, human_coord_display, human_meeple_dd, human_tile_display, human_hint_md, human_coord_dd]
    
    btn_step.click(fn=step_game, inputs=[], outputs=UI_OUTPUTS)
    btn_rotate.click(fn=rotate_tile, inputs=[], outputs=UI_OUTPUTS)
    
    # Coordinates click handler
    hidden_coords.change(fn=set_coords, inputs=[hidden_coords], outputs=UI_OUTPUTS)
    human_coord_dd.change(fn=set_coords, inputs=[human_coord_dd], outputs=UI_OUTPUTS)
    
    human_submit.click(fn=submit_human, inputs=[human_meeple_dd], outputs=UI_OUTPUTS)
    
    btn_reset.click(fn=reset_game, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)
    player1_dd.change(fn=change_agents, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)
    player2_dd.change(fn=change_agents, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)

    
    def auto_play_10():
        for _ in range(10):
            _global_state.step_forward()
            if _global_state.game_over or _global_state.pending_human_turn:
                break
        return _unpack_ui_state(_global_state)
        
    btn_auto.click(fn=auto_play_10, inputs=[], outputs=UI_OUTPUTS)
    
    # Init
    demo.load(fn=reset_game, inputs=[player1_dd, player2_dd, token_input], outputs=UI_OUTPUTS)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        head=HEAD_JS,
        css="#hidden_coord_input { opacity: 0 !important; height: 0px !important; overflow: hidden !important; pointer-events: none !important; } .hint-box { background: var(--amber-50); padding: 10px; border-radius: 8px; border-left: 4px solid var(--amber-500); margin-top: 10px; }"
    )
