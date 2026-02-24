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
    def render_board(cls, board: Board) -> str:
        if not board.grid:
            return "<div style='text-align:center; padding:50px; color:#666;'>Game has not started.</div>"
            
        min_x = min(x for x, y in board.grid.keys())
        max_x = max(x for x, y in board.grid.keys())
        min_y = min(y for x, y in board.grid.keys())
        max_y = max(y for x, y in board.grid.keys())
        
        width = (max_x - min_x + 1) * cls.TILE_SIZE
        height = (max_y - min_y + 1) * cls.TILE_SIZE
        
        svg = [f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">']
        svg.append('<defs><pattern id="field" patternUnits="userSpaceOnUse" width="10" height="10"><rect width="10" height="10" fill="#a7c957"/></pattern></defs>')
        
        for (x, y), tile in board.grid.items():
            px = (x - min_x) * cls.TILE_SIZE
            # y goes up in coordinates, so we invert it for SVG (0,0 is top-left)
            py = (max_y - y) * cls.TILE_SIZE
            svg.append(cls.render_tile(tile, px, py))
            
        svg.append('</svg>')
        return "\n".join(svg)
        
    @classmethod
    def render_tile(cls, tile, px, py) -> str:
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
        
        self.p1_str = p1_str
        self.p2_str = p2_str
        self.agents = {}
        for p_name, a_str in [("Player1", p1_str), ("Player2", p2_str)]:
            if a_str == "Star2.5": self.agents[p_name] = StarAgent(p_name)
            elif a_str == "MCTS": self.agents[p_name] = MCTSAgent(p_name)
            elif a_str == "Hybrid LLM": self.agents[p_name] = HybridLLMAgent(p_name, hf_token)
            else: self.agents[p_name] = GreedyAgent(p_name)

    def play_turn(self):
        if not self.deck or self.game_over:
            if not self.game_over:
                self.game_over = True
                
                # End game scoring
                final_scores = self.board.calculate_final_scores()
                for score in final_scores:
                    for player, count in score["meeples"].items():
                        # If multiple players tie, they all get pts.
                        self.scores[player] += score["points"]
                
                self.logs.append(f"<b>[GAME OVER]</b> Final Scoring computed.")
                
                # Announce Winner
                p1_score = self.scores["Player1"]
                p2_score = self.scores["Player2"]
                if p1_score > p2_score:
                    self.logs.append(f"🏆 <b>Winner is Player 1 ({p1_score} vs {p2_score})!</b>")
                elif p2_score > p1_score:
                    self.logs.append(f"🏆 <b>Winner is Player 2 ({p2_score} vs {p1_score})!</b>")
                else:
                    self.logs.append(f"🤝 <b>It's a TIE ({p1_score} vs {p2_score})!</b>")
                    
            return self.get_ui_state()
            
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
        else:
            agent = self.agents[self.current_player]
            
            # Use specific signature if it's HybridLLMAgent to pass remaining tiles
            if isinstance(agent, HybridLLMAgent):
                tx, ty, rot, meeple_idx = agent.select_move(self.board, tile, legal_moves, self.meeples[self.current_player], len(self.deck))
                self.logs.append(f"🤖 <b>[LLM THINKING]</b> {self.current_player} (Hybrid LLM) analyzed board.")
            else:
                tx, ty, rot, meeple_idx = agent.select_move(self.board, tile, legal_moves, self.meeples[self.current_player])
                
            tile.rotate(rot // 90)
            self.board.place_tile(tx, ty, tile)
            self.logs.append(f"[{self.current_player}] Placed <b>{tile.name}</b> at ({tx}, {ty}) with rot {rot}.")
            
            # Place Meeple logic
            if meeple_idx is not None and self.meeples[self.current_player] > 0:
                if self.board.place_meeple(tx, ty, meeple_idx, self.current_player):
                    self.meeples[self.current_player] -= 1
                    self.logs.append(f"[{self.current_player}] Placed MEEPLE on feature at ({tx}, {ty}).")
        
        # End game step computations
        completed = self.board.get_completed_features()
        for comp in completed:
            for player, count in comp["meeples"].items():
                self.scores[player] += comp["points"]
                self.meeples[player] += count
                self.logs.append(f"🎉 <b>Feature Completed:</b> {comp['type']} (+{comp['points']} pts for {player}). Meeple returned.")

        # Switch player
        self.current_player = "Player2" if self.current_player == "Player1" else "Player1"
        return self.get_ui_state()

    def get_ui_state(self):
        # Instead of hardcoded #f4f4f4 background, use CSS variables for light/dark mode compatibility
        log_html = "<div style='height:400px; overflow-y:auto; font-family:monospace; background: var(--background-fill-secondary); color: var(--body-text-color); padding:10px; border-radius:5px; border: 1px solid var(--border-color-primary);'>"
        log_html += "<br>".join(reversed(self.logs))
        log_html += "</div>"
        
        svg = SVG_Renderer.render_board(self.board)
        
        stats = f"""
        ### 📊 Current Score
        - 🔴 **Player 1** ({self.p1_str}): {self.scores['Player1']} pts *(Meeples: {self.meeples['Player1']}/7)*
        - 🔵 **Player 2** ({self.p2_str}): {self.scores['Player2']} pts *(Meeples: {self.meeples['Player2']}/7)*
        
        **Tiles remaining:** {len(self.deck)}/72
        **Current Turn:** {self.current_player}
        """
        
        return svg, log_html, stats

_global_state = GameState()

def step_game():
    return _global_state.play_turn()

def reset_game(p1, p2, token):
    global _global_state
    _global_state = GameState(p1, p2, token)
    return _global_state.get_ui_state()

def change_agents(p1, p2, token):
    _global_state.p1_str = p1
    _global_state.p2_str = p2
    for p_name, a_str in [("Player1", p1), ("Player2", p2)]:
        if a_str == "Star2.5": _global_state.agents[p_name] = StarAgent(p_name)
        elif a_str == "MCTS": _global_state.agents[p_name] = MCTSAgent(p_name)
        elif a_str == "Hybrid LLM": _global_state.agents[p_name] = HybridLLMAgent(p_name, token)
        else: _global_state.agents[p_name] = GreedyAgent(p_name)
    return _global_state.get_ui_state()

AGENT_CHOICES = ["Greedy", "Star2.5", "MCTS", "Hybrid LLM"]

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
            
            logs_view = gr.HTML(value="Logs will appear here.")
            
    btn_step.click(fn=step_game, inputs=[], outputs=[board_view, logs_view, stats_view])
    btn_reset.click(fn=reset_game, inputs=[player1_dd, player2_dd, token_input], outputs=[board_view, logs_view, stats_view])
    
    # Real-time UI updates for dropdown changes
    player1_dd.change(fn=change_agents, inputs=[player1_dd, player2_dd, token_input], outputs=[board_view, logs_view, stats_view])
    player2_dd.change(fn=change_agents, inputs=[player1_dd, player2_dd, token_input], outputs=[board_view, logs_view, stats_view])
    
    def auto_play_10():
        for _ in range(10):
            r1, r2, r3 = _global_state.play_turn()
            if _global_state.game_over: break
        return r1, r2, r3
        
    btn_auto.click(fn=auto_play_10, inputs=[], outputs=[board_view, logs_view, stats_view])
    
    # Init
    demo.load(fn=reset_game, inputs=[player1_dd, player2_dd, token_input], outputs=[board_view, logs_view, stats_view])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
