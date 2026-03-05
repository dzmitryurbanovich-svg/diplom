from typing import Dict, Tuple, List, Optional
from .models import Tile, Side, SegmentType, TileSegment

class DSU:
    """Disjoint Set Union for tracking connected cities, roads, and fields with tile counting."""
    def __init__(self):
        self.parent = {}
        self.tiles = {}       # root -> set of unique tile coordinates (x, y)
        self.pennants = {}     # root -> count of pennants
        self.open_edges = {}  # root -> total open connection ends
        self.meeples = {}     # root -> dict tracking player_name: meeple count

    def make_set(self, segment_id: str, tile_pos: Tuple[int, int], pennants: int = 0, open_edges: int = 0):
        if segment_id not in self.parent:
            self.parent[segment_id] = segment_id
            self.tiles[segment_id] = {tile_pos}
            self.pennants[segment_id] = pennants
            self.open_edges[segment_id] = open_edges
            self.meeples[segment_id] = {}

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            # Simple union (size is now implicitly handles via self.tiles set size)
            if len(self.tiles[root_i]) < len(self.tiles[root_j]):
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.tiles[root_i].update(self.tiles[root_j])
            self.pennants[root_i] += self.pennants[root_j]
            
            # Merge meeples
            for p, count in self.meeples[root_j].items():
                self.meeples[root_i][p] = self.meeples[root_i].get(p, 0) + count
            
            # One node-pair connection satisfies 2 open ends
            self.open_edges[root_i] = self.open_edges[root_i] + self.open_edges[root_j] - 2
            return True
        else:
            # Connection within same set (loop) removes 2 open ends
            self.open_edges[root_i] -= 2
            return False

class Board:
    """Manages the grid of tiles and the game state with precise 12-node rules."""
    def __init__(self):
        self.grid: Dict[Tuple[int, int], Tile] = {}
        self.dsu = {
            SegmentType.CITY: DSU(),
            SegmentType.ROAD: DSU(),
            SegmentType.FIELD: DSU()
        }
        self.monasteries: Dict[Tuple[int, int], Optional[str]] = {}
        self.segment_counter = 0
        self.scores = {"Player1": 0, "Player2": 0}
        self.meeple_counts = {"Player1": 7, "Player2": 7}

    def _get_next_segment_id(self) -> str:
        self.segment_counter += 1
        return f"seg_{self.segment_counter}"

    def is_legal_move(self, x: int, y: int, tile: Tile) -> bool:
        if (x, y) in self.grid: return False
        adj = {Side.NORTH: (x, y+1), Side.EAST: (x+1, y), Side.SOUTH: (x, y-1), Side.WEST: (x-1, y)}
        has_adj = not self.grid
        for side, pos in adj.items():
            if pos in self.grid:
                has_adj = True
                neighbor = self.grid[pos]
                this_nodes = tile.get_side_nodes(side)
                neigh_nodes = list(reversed(neighbor.get_side_nodes(Side((side.value + 2) % 4))))
                for i in range(3):
                    if tile.get_node_type(this_nodes[i]) != neighbor.get_node_type(neigh_nodes[i]):
                        return False
        return has_adj

    def get_legal_moves(self, tile: Tile) -> List[Tuple[int, int, int]]:
        legal_moves = []
        if not self.grid: return [(0,0,r) for r in [0, 90, 180, 270]]
        candidates = set()
        for (x, y) in self.grid:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                if (x+dx, y+dy) not in self.grid: candidates.add((x+dx, y+dy))
        for x, y in candidates:
            for _ in range(4):
                if self.is_legal_move(x, y, tile): legal_moves.append((x, y, tile.rotation))
                tile.rotate(1)
        return legal_moves

    def place_tile(self, x: int, y: int, tile: Tile) -> bool:
        if not self.is_legal_move(x, y, tile): return False
        
        # Register segments
        for segment in tile.segments:
            seg_id = self._get_next_segment_id()
            segment.id = seg_id
            if segment.type in self.dsu:
                p = 1 if segment.has_pennant else 0
                self.dsu[segment.type].make_set(seg_id, tile_pos=(x, y), pennants=p, open_edges=len(segment.nodes))

        # Union with neighbors
        adj = {Side.NORTH: (x, y+1), Side.EAST: (x+1, y), Side.SOUTH: (x, y-1), Side.WEST: (x-1, y)}
        for side, pos in adj.items():
            if pos in self.grid:
                neighbor = self.grid[pos]
                this_nodes = tile.get_side_nodes(side)
                neigh_nodes = list(reversed(neighbor.get_side_nodes(Side((side.value + 2) % 4))))
                for i in range(3):
                    if tile.get_node_type(this_nodes[i]) == neighbor.get_node_type(neigh_nodes[i]):
                        seg_this = next((s for s in tile.segments if this_nodes[i] in s.nodes), None)
                        seg_neigh = next((s for s in neighbor.segments if neigh_nodes[i] in s.nodes), None)
                        if seg_this and seg_neigh and seg_this.type in self.dsu:
                            self.dsu[seg_this.type].union(seg_this.id, seg_neigh.id)

        self.grid[(x, y)] = tile
        for segment in tile.segments:
            if getattr(segment, 'is_monastery', False) or segment.type == SegmentType.MONASTERY:
                self.monasteries[(x, y)] = None
        return True

    def place_meeple(self, x: int, y: int, segment_index: int, player_name: str) -> bool:
        if (x, y) not in self.grid or self.meeple_counts.get(player_name, 0) <= 0: return False
        tile = self.grid[(x, y)]
        if segment_index < 0 or segment_index >= len(tile.segments): return False
        segment = tile.segments[segment_index]
        if getattr(segment, 'meeple_player', None) is not None: return False

        if getattr(segment, 'is_monastery', False) or segment.type == SegmentType.MONASTERY:
            if self.monasteries.get((x, y)) is not None: return False
            self.monasteries[(x, y)] = player_name
            segment.meeple_player = player_name
            self.meeple_counts[player_name] -= 1
            return True

        if segment.type not in self.dsu: return False
        root = self.dsu[segment.type].find(segment.id)
        if self.dsu[segment.type].meeples.get(root): return False # Feature occupied
        
        self.dsu[segment.type].meeples[root][player_name] = 1
        segment.meeple_player = player_name
        self.meeple_counts[player_name] -= 1
        return True

    def get_completed_features(self) -> List[Dict]:
        completed = []
        for st in [SegmentType.CITY, SegmentType.ROAD]:
            dsu = self.dsu[st]
            roots = set(dsu.find(sid) for sid in dsu.parent.keys())
            for root in roots:
                if dsu.open_edges[root] == 0 and sum(dsu.meeples[root].values()) > 0:
                    tile_count = len(dsu.tiles[root])
                    pts = (tile_count + dsu.pennants[root]) * (2 if st == SegmentType.CITY else 1)
                    meeples = dsu.meeples[root]
                    max_count = max(meeples.values())
                    winners = [p for p, c in meeples.items() if c == max_count]
                    for w in winners: self.scores[w] += pts
                    for p, c in meeples.items(): self.meeple_counts[p] += c
                    dsu.meeples[root] = {}
                    completed.append({"type": st.name, "points": pts, "winners": winners})
                    # Clear visual meeple
                    for (gx, gy), t in self.grid.items():
                        for seg in t.segments:
                            if seg.type == st and dsu.find(seg.id) == root: seg.meeple_player = None

        for (mx, my), owner in list(self.monasteries.items()):
            if owner:
                if sum(1 for dx in [-1,0,1] for dy in [-1,0,1] if (mx+dx, my+dy) in self.grid) == 9:
                    self.scores[owner] += 9
                    self.meeple_counts[owner] += 1
                    self.monasteries[(mx, my)] = None
                    for seg in self.grid[(mx, my)].segments:
                        if (getattr(seg, 'is_monastery', False) or seg.type == SegmentType.MONASTERY): seg.meeple_player = None
                    completed.append({"type": "MONASTERY", "points": 9, "winners": [owner]})
        return completed

    def calculate_final_scores(self) -> List[Dict]:
        results = []
        # Cities/Roads
        for st in [SegmentType.CITY, SegmentType.ROAD]:
            dsu = self.dsu[st]
            roots = set(dsu.find(sid) for sid in dsu.parent.keys())
            for root in roots:
                if sum(dsu.meeples[root].values()) > 0:
                    tile_count = len(dsu.tiles[root])
                    pts = (tile_count + dsu.pennants[root]) * 1
                    meeples = dsu.meeples[root]
                    max_v = max(meeples.values())
                    winners = [p for p, c in meeples.items() if c == max_v]
                    for w in winners: self.scores[w] += pts
                    results.append({"type": f"INCOMPLETE_{st.name}", "points": pts, "winners": winners})

        # Monasteries
        for (mx, my), owner in self.monasteries.items():
            if owner:
                pts = sum(1 for dx in [-1,0,1] for dy in [-1,0,1] if (mx+dx, my+dy) in self.grid)
                self.scores[owner] += pts
                results.append({"type": "INCOMPLETE_MONASTERY", "points": pts, "winners": [owner]})

        # Fields (Precise Node Adjacency)
        field_dsu = self.dsu[SegmentType.FIELD]
        city_dsu = self.dsu[SegmentType.CITY]
        f_to_c = {root: set() for root in set(field_dsu.find(sid) for sid in field_dsu.parent.keys()) if sum(field_dsu.meeples[root].values()) > 0}
        
        for (x, y), tile in self.grid.items():
            completed_cities = [city_dsu.find(s.id) for s in tile.segments if s.type == SegmentType.CITY and city_dsu.open_edges[city_dsu.find(s.id)] == 0]
            if not completed_cities: continue
            for f_seg in tile.segments:
                if f_seg.type == SegmentType.FIELD:
                    f_root = field_dsu.find(f_seg.id)
                    if f_root in f_to_c:
                        for c_seg in tile.segments:
                            if c_seg.type == SegmentType.CITY:
                                c_root = city_dsu.find(c_seg.id)
                                if c_root in completed_cities:
                                    if any(abs(nf-nc)%12 in [1,11] for nf in f_seg.nodes for nc in c_seg.nodes):
                                        f_to_c[f_root].add(c_root)

        for f_root, cities in f_to_c.items():
            pts = len(cities) * 3
            meeples = field_dsu.meeples[f_root]
            max_v = max(meeples.values())
            winners = [p for p, c in meeples.items() if c == max_v]
            for w in winners: self.scores[w] += pts
            results.append({"type": "FIELD", "points": pts, "winners": winners})
        return results

        for f_root, cities in field_to_cities.items():
            pts = len(cities) * 3
            if pts > 0:
                meeples = dict(field_dsu.meeples[f_root])
                results.append({"type": "FIELD", "points": pts, "meeples": meeples})
                max_m = max(meeples.values())
                for p in [p for p, c in meeples.items() if c == max_m]:
                    self.scores[p] = self.scores.get(p, 0) + pts

        return results

    def render_ascii(self) -> str:
        """Returns an ASCII representation of the board."""
        if not self.grid:
            return "   (Empty Board)"
        
        min_x = min(x for x, y in self.grid.keys())
        max_x = max(x for x, y in self.grid.keys())
        min_y = min(y for x, y in self.grid.keys())
        max_y = max(y for x, y in self.grid.keys())
        
        # Add padding
        min_x -= 1
        max_x += 1
        min_y -= 1
        max_y += 1
        
        output = []
        # Header row (x-axis)
        header = "   " + " ".join(f"{x:2}" for x in range(min_x, max_x + 1))
        output.append(header)
        output.append("   " + "-" * len(header))

        for y in range(max_y, min_y - 1, -1):
            row = [f"{y:2}|"]
            for x in range(min_x, max_x + 1):
                if (x, y) in self.grid:
                    tile = self.grid[(x, y)]
                    symbol = tile.name[0].upper() if tile.name else "?"
                    row.append(f"[{symbol}]")
                else:
                    row.append(" . ")
            output.append(" ".join(row))
        
        return "\n".join(output)
