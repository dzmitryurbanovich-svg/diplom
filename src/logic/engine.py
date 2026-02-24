from typing import Dict, Tuple, List, Optional
from .models import Tile, Side, SegmentType, TileSegment

class DSU:
    """Disjoint Set Union for tracking connected cities, roads, and fields."""
    def __init__(self):
        self.parent = {}
        self.size = {}
        self.pennants = {}
        self.open_edges = {}  # Number of edges waiting for connection
        self.meeples = {}     # Dict tracking player_name: count of meeples in this set

    def make_set(self, segment_id: str, pennants: int = 0, open_edges: int = 0):
        if segment_id not in self.parent:
            self.parent[segment_id] = segment_id
            self.size[segment_id] = 1
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
            # Union by size
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            self.pennants[root_i] += self.pennants[root_j]
            # Merge meeples
            for p, count in self.meeples[root_j].items():
                self.meeples[root_i][p] = self.meeples[root_i].get(p, 0) + count
            
            # When connecting two segments, we satisfy 2 open edges
            self.open_edges[root_i] = self.open_edges[root_i] + self.open_edges[root_j] - 2
            return True
        else:
            # Even if already in same set, one connection removes 2 open edges
            self.open_edges[root_i] -= 2
            return False

class Board:
    """Manages the grid of tiles and the game state."""
    def __init__(self):
        self.grid: Dict[Tuple[int, int], Tile] = {}
        self.dsu = {
            SegmentType.CITY: DSU(),
            SegmentType.ROAD: DSU(),
            SegmentType.FIELD: DSU()
        }
        self.monasteries: Dict[Tuple[int, int], Optional[str]] = {}  # Track (x, y) -> player who owns meeple
        self.segment_counter = 0

    def _get_next_segment_id(self) -> str:
        self.segment_counter += 1
        return f"seg_{self.segment_counter}"

    def is_legal_move(self, x: int, y: int, tile: Tile) -> bool:
        """Checks if placing a tile at (x, y) is legal without performing the placement."""
        if (x, y) in self.grid:
            return False
        
        adjacents = {
            Side.NORTH: (x, y + 1),
            Side.EAST: (x + 1, y),
            Side.SOUTH: (x, y - 1),
            Side.WEST: (x - 1, y)
        }
        
        has_adj = False
        if not self.grid: # First tile is always legal at (0,0)
            has_adj = True
        else:
            for side, pos in adjacents.items():
                if pos in self.grid:
                    has_adj = True
                    neighbor = self.grid[pos]
                    neighbor_side = Side((side.value + 2) % 4)
                    if tile.get_side_type(side) != neighbor.get_side_type(neighbor_side):
                        return False # Mismatch!
        
        return has_adj

    def place_tile(self, x: int, y: int, tile: Tile) -> bool:
        """Places a tile on the board if the move is legal."""
        if not self.is_legal_move(x, y, tile):
            return False

        adjacents = {
            Side.NORTH: (x, y + 1),
            Side.EAST: (x + 1, y),
            Side.SOUTH: (x, y - 1),
            Side.WEST: (x - 1, y)
        }

        # Register segments in DSU
        for segment in tile.segments:
            seg_id = self._get_next_segment_id()
            segment.id = seg_id
            p = 1 if segment.has_pennant else 0
            open_e = len(segment.sides)
            if segment.type in self.dsu:
                self.dsu[segment.type].make_set(seg_id, pennants=p, open_edges=open_e)

        # Perform unions with neighbors
        for side, pos in adjacents.items():
            if pos in self.grid:
                neighbor = self.grid[pos]
                neighbor_side = Side((side.value + 2) % 4)
                
                # Find segments on these matching sides
                seg_this = next((s for s in tile.segments if side in s.sides), None)
                seg_neigh = next((s for s in neighbor.segments if neighbor_side in s.sides), None)
                
                if seg_this and seg_neigh and seg_this.type == seg_neigh.type:
                    if seg_this.type in self.dsu:
                        self.dsu[seg_this.type].union(seg_this.id, seg_neigh.id)

        self.grid[(x, y)] = tile
        
        # Check if tile has a monastery
        for segment in tile.segments:
            if getattr(segment, 'is_monastery', False) or segment.type == SegmentType.MONASTERY:
                self.monasteries[(x, y)] = None  # Track monastery position
                
        return True

    def place_meeple(self, x: int, y: int, segment_index: int, player_name: str) -> bool:
        """Places a meeple on a specific segment of a tile if the feature is unoccupied."""
        if (x, y) not in self.grid:
            return False
            
        tile = self.grid[(x, y)]
        if segment_index < 0 or segment_index >= len(tile.segments):
            return False
            
        segment = tile.segments[segment_index]
        if getattr(segment, 'meeple_player', None) is not None:
            return False
            
        # Handle Monastery specially
        if getattr(segment, 'is_monastery', False) or segment.type == SegmentType.MONASTERY:
            if self.monasteries.get((x, y)) is not None:
                return False
            self.monasteries[(x, y)] = player_name
            segment.meeple_player = player_name
            return True
            
        if segment.type not in self.dsu:
            return False
            
        root = self.dsu[segment.type].find(segment.id)
        if len(self.dsu[segment.type].meeples.get(root, {})) > 0:
            return False # Feature already claimed
            
        self.dsu[segment.type].meeples[root][player_name] = 1
        segment.meeple_player = player_name
        return True

    def is_completed(self, segment_id: str, segment_type: SegmentType) -> bool:
        """Checks if a city or road is completed (no open edges)."""
        if segment_type not in self.dsu:
            return False
        root = self.dsu[segment_type].find(segment_id)
        return self.dsu[segment_type].open_edges[root] == 0

    def get_completed_features(self) -> List[Dict]:
        """Finds completed features, scores them, and removes meeples to return to players."""
        completed = []
        
        # Check standard DSU features
        for seg_type in [SegmentType.CITY, SegmentType.ROAD]:
            dsu = self.dsu[seg_type]
            for root, edges in list(dsu.open_edges.items()):
                if edges == 0 and len(dsu.meeples.get(root, {})) > 0:
                    # Score it
                    pts_per_tile = 2 if seg_type == SegmentType.CITY else 1
                    pts = (dsu.size[root] + dsu.pennants[root]) * pts_per_tile
                    
                    completed.append({
                        "type": seg_type.name,
                        "points": pts,
                        "meeples": dict(dsu.meeples[root])
                    })
                    # Return meeples
                    dsu.meeples[root] = {}

        # Check monasteries
        for (mx, my), owner in list(self.monasteries.items()):
            if owner is not None:
                # Count surrounding tiles
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if (mx + dx, my + dy) in self.grid:
                            count += 1
                if count == 9:
                    completed.append({
                        "type": "MONASTERY",
                        "points": 9,
                        "meeples": {owner: 1}
                    })
                    # Return meeple
                    self.monasteries[(mx, my)] = None
                    
        return completed

    def calculate_final_scores(self) -> List[Dict]:
        """Scores all incomplete features and fields at the end of the game."""
        results = []
        
        # Incomplete Cities (1pt/tile) and Roads (1pt/tile)
        for seg_type in [SegmentType.CITY, SegmentType.ROAD]:
            dsu = self.dsu[seg_type]
            for root, edges in list(dsu.open_edges.items()):
                if edges > 0 and len(dsu.meeples.get(root, {})) > 0:
                    pts = (dsu.size[root] + dsu.pennants[root]) * 1 # 1 pt for incomplete
                    results.append({
                        "type": f"INCOMPLETE_{seg_type.name}",
                        "points": pts,
                        "meeples": dict(dsu.meeples[root])
                    })

        # Incomplete Monasteries
        for (mx, my), owner in list(self.monasteries.items()):
            if owner is not None:
                count = sum(1 for dx in [-1,0,1] for dy in [-1,0,1] if (mx+dx, my+dy) in self.grid)
                results.append({
                    "type": "INCOMPLETE_MONASTERY",
                    "points": count,
                    "meeples": {owner: 1}
                })

        # Fields (3 pts per completed city bordering the field)
        field_dsu = self.dsu[SegmentType.FIELD]
        city_dsu = self.dsu[SegmentType.CITY]
        
        # Map each field root to the set of completed city roots it touches
        field_to_cities = {root: set() for root in field_dsu.meeples.keys() if len(field_dsu.meeples[root]) > 0}
        
        for (x, y), tile in self.grid.items():
            field_roots = set()
            city_roots = set()
            for seg in tile.segments:
                if seg.type == SegmentType.FIELD:
                    r = field_dsu.find(seg.id)
                    if r in field_to_cities:
                        field_roots.add(r)
                elif seg.type == SegmentType.CITY:
                    r = city_dsu.find(seg.id)
                    if city_dsu.open_edges[r] == 0: # Must be completed city
                        city_roots.add(r)
            
            for f_root in field_roots:
                for c_root in city_roots:
                    field_to_cities[f_root].add(c_root)

        for f_root, cities in field_to_cities.items():
            pts = len(cities) * 3
            if pts > 0:
                results.append({
                    "type": "FIELD",
                    "points": pts,
                    "meeples": dict(field_dsu.meeples[f_root])
                })

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
