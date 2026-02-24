import gradio as gr
import urllib.parse

from src.logic.engine import Board
from src.logic.deck import DECK_DEFINITIONS

class SVG_Renderer:
    """Generates an SVG map representation of the Carcassonne board state."""
    
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
        cx, cy = px + s/2, py + s/2
        
        # Base field background
        g = [f'<g transform="translate({px}, {py})">']
        g.append(f'<rect width="{s}" height="{s}" fill="#a7c957" stroke="#6b903e" stroke-width="1"/>')
        
        from src.logic.models import Side, SegmentType
        
        road_paths = []
        city_polygons = []
        
        for seg in tile.segments:
            # Render Cities
            if seg.type == SegmentType.CITY:
                if len(seg.sides) == 4:
                    city_polygons.append(f'<rect x="0" y="0" width="{s}" height="{s}" fill="#d4a373" stroke="#8b5a2b" stroke-width="4"/>')
                elif len(seg.sides) == 1:
                    if Side.NORTH in seg.sides:
                        city_polygons.append(f'<path d="M 0 0 L {s} 0 L {s} {s/3} Q {s/2} {s/2} 0 {s/3} Z" fill="#d4a373" stroke="#8b5a2b" stroke-width="2"/>')
                    elif Side.SOUTH in seg.sides:
                        city_polygons.append(f'<path d="M 0 {s} L {s} {s} L {s} {s*2/3} Q {s/2} {s/2} 0 {s*2/3} Z" fill="#d4a373" stroke="#8b5a2b" stroke-width="2"/>')
                    elif Side.EAST in seg.sides:
                        city_polygons.append(f'<path d="M {s} 0 L {s} {s} L {s*2/3} {s} Q {s/2} {s/2} {s*2/3} 0 Z" fill="#d4a373" stroke="#8b5a2b" stroke-width="2"/>')
                    elif Side.WEST in seg.sides:
                        city_polygons.append(f'<path d="M 0 0 L 0 {s} L {s/3} {s} Q {s/2} {s/2} {s/3} 0 Z" fill="#d4a373" stroke="#8b5a2b" stroke-width="2"/>')
                elif len(seg.sides) == 2:
                    if Side.NORTH in seg.sides and Side.EAST in seg.sides:
                        city_polygons.append(f'<path d="M 0 0 L {s} 0 L {s} {s} Q {s/2} {s/2} 0 0 Z" fill="#d4a373" stroke="#8b5a2b" stroke-width="2"/>')
                    # Other 2-side cities follow similar radial or corner sweeping logic
                    else:
                        city_polygons.append(f'<rect x="{s/4}" y="{s/4}" width="{s/2}" height="{s/2}" fill="#d4a373" stroke="#8b5a2b" stroke-width="2"/>') # Fallback

            # Render Roads
            elif seg.type == SegmentType.ROAD:
                if len(seg.sides) == 2:
                    start_pt, end_pt = "", ""
                    pts = {Side.NORTH: f"{s/2},0", Side.SOUTH: f"{s/2},{s}", Side.EAST: f"{s},{s/2}", Side.WEST: f"0,{s/2}"}
                    paths = [pts.get(side) for side in seg.sides if side in pts]
                    if len(paths) == 2:
                        road_paths.append(f'<path d="M {paths[0]} Q {s/2},{s/2} {paths[1]}" fill="none" stroke="#e0e0e0" stroke-width="12"/>')
                elif len(seg.sides) == 1:
                    pts = {Side.NORTH: f"{s/2},0", Side.SOUTH: f"{s/2},{s}", Side.EAST: f"{s},{s/2}", Side.WEST: f"0,{s/2}"}
                    for side in seg.sides:
                        road_paths.append(f'<line x1="{s/2}" y1="{s/2}" x2="{pts[side].split(",")[0]}" y2="{pts[side].split(",")[1]}" stroke="#e0e0e0" stroke-width="12"/>')

        # Add all layers in order
        g.extend(city_polygons)
        g.extend(road_paths)

        # Monastery / Center logic
        if tile.center_type == SegmentType.MONASTERY:
            g.append(f'<circle cx="{s/2}" cy="{s/2}" r="{s/4}" fill="#bc4749" stroke="#fff" stroke-width="2"/>')
            g.append(f'<rect x="{s/2-s/8}" y="{s/2-s/8}" width="{s/4}" height="{s/4}" fill="#fff"/>')
            
        # Draw pennants
        for seg in tile.segments:
            if seg.has_pennant:
                g.append(f'<polygon points="{s/4},{s/4} {s/4+10},{s/4} {s/4+5},{s/4+15}" fill="#457b9d"/>')
                
        # Draw Meeples
        # For simplicity, if we have meeples on segments, draw them generally near their feature
        for i, seg in enumerate(tile.segments):
            if seg.meeple_player:
                color = "#e63946" if seg.meeple_player == "Player1" else "#1d3557"
                # Offset positions to not overlap
                ox = s/2 + (i * 5 - 10)
                oy = s/2 + (i * 5 - 10)
                g.append(f'<circle cx="{ox}" cy="{oy}" r="6" fill="{color}" stroke="#fff" stroke-width="2"/>')
                
        # Draw coordinate label 
        # g.append(f'<text x="5" y="15" font-size="10" fill="gray">{tile.name[:4]}</text>')

        g.append('</g>')
        return "\n".join(g)

# Simple game orchestrator for the Gradio UI
class GameState:
    def __init__(self):
        self.board = Board()
        import random
        self.deck = DECK_DEFINITIONS[:] # copy
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

    def play_turn(self):
        if not self.deck or self.game_over:
            self.game_over = True
            
            # End game scoring
            final_scores = self.board.calculate_final_scores()
            for score in final_scores:
                for player, count in score["meeples"].items():
                    # If multiple players tie, they all get pts.
                    self.scores[player] += score["points"]
            
            self.logs.append(f"<b>[GAME OVER]</b> Final Scoring computed.")
            return self.get_ui_state()
            
        tile = self.deck.pop(0)
        
        # Basic Heuristic Agent Logic (Mocking LLM for UI speed, or we can use the real one)
        # Using a Greedy logic to find a placement
        legal_moves = []
        to_check = set()
        for (x, y) in self.board.grid:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                if (x + dx, y + dy) not in self.board.grid:
                    to_check.add((x + dx, y + dy))
                    
        for tx, ty in to_check:
            for rot in [0, 90, 180, 270]:
                test_tile = type(tile)(tile.name, tile.segments, tile.center_type) # Simple deep copy bypass for test
                # Wait, Python needs deepcopy for rotate
                import copy
                test_tile = copy.deepcopy(tile)
                test_tile.rotate(rot // 90)
                if self.board.is_legal_move(tx, ty, test_tile):
                    legal_moves.append((tx, ty, rot))
                    
        if not legal_moves:
            self.logs.append(f"[{self.current_player}] Drew {tile.name} but no legal moves. Discarded.")
        else:
            # Greedy: just pick the first one for the demo UI loop
            import random
            tx, ty, rot = random.choice(legal_moves)
            tile.rotate(rot // 90)
            self.board.place_tile(tx, ty, tile)
            self.logs.append(f"[{self.current_player}] Placed <b>{tile.name}</b> at ({tx}, {ty}) with rot {rot}.")
            
            # Place Meeple logic (Randomly decide 20% of time)
            if self.meeples[self.current_player] > 0 and random.random() < 0.2:
                for idx_seg, _ in enumerate(tile.segments):
                    if self.board.place_meeple(tx, ty, idx_seg, self.current_player):
                        self.meeples[self.current_player] -= 1
                        self.logs.append(f"[{self.current_player}] Placed MEEPLE on feature at ({tx}, {ty}).")
                        break
        
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
        log_html = "<div style='height:400px; overflow-y:auto; font-family:monospace; background:#f4f4f4; padding:10px; border-radius:5px; border: 1px solid #ddd;'>"
        log_html += "<br>".join(reversed(self.logs))
        log_html += "</div>"
        
        svg = SVG_Renderer.render_board(self.board)
        
        stats = f"""
        ### 📊 Current Score
        - 🔴 **Player 1:** {self.scores['Player1']} pts *(Meeples: {self.meeples['Player1']}/7)*
        - 🔵 **Player 2:** {self.scores['Player2']} pts *(Meeples: {self.meeples['Player2']}/7)*
        
        **Tiles remaining:** {len(self.deck)}/72
        **Current Turn:** {self.current_player}
        """
        
        return svg, log_html, stats

_global_state = GameState()

def step_game():
    return _global_state.play_turn()

def reset_game():
    global _global_state
    _global_state = GameState()
    return _global_state.get_ui_state()

with gr.Blocks(title="Carcassonne AI Tournament Viewer", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏰 Carcassonne AI Tournament Engine")
    gr.Markdown("Watch entirely autonomous agents compete in the classic board game, applying heuristic tree search and LLM-driven strategy.")
    
    with gr.Row():
        with gr.Column(scale=2):
            board_view = gr.HTML(value="")
        with gr.Column(scale=1):
            stats_view = gr.Markdown(value="Hit start to begin.")
            controls = gr.Row()
            with controls:
                btn_step = gr.Button("▶️ Next Turn", variant="primary")
                btn_auto = gr.Button("⏩ Auto-Play (x10)", variant="secondary")
                btn_reset = gr.Button("🔄 Reset Board")
            
            logs_view = gr.HTML(value="Logs will appear here.")
            
    btn_step.click(fn=step_game, outputs=[board_view, logs_view, stats_view])
    btn_reset.click(fn=reset_game, outputs=[board_view, logs_view, stats_view])
    
    def auto_play_10():
        for _ in range(10):
            r1, r2, r3 = _global_state.play_turn()
            if _global_state.game_over: break
        return r1, r2, r3
        
    btn_auto.click(fn=auto_play_10, outputs=[board_view, logs_view, stats_view])
    
    # Init
    demo.load(fn=reset_game, outputs=[board_view, logs_view, stats_view])

if __name__ == "__main__":
    demo.launch()
