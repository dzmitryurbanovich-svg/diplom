from typing import Dict, Tuple, List, Optional
from .models import Tile, Side, SegmentType, TileSegment

class DSU:
    """Disjoint Set Union for tracking connected cities, roads, and fields."""
    def __init__(self):
        self.parent = {}
        self.size = {}
        self.pennants = {}
        self.open_edges = {}  # Number of edges waiting for connection

    def make_set(self, segment_id: str, pennants: int = 0, open_edges: int = 0):
        if segment_id not in self.parent:
            self.parent[segment_id] = segment_id
            self.size[segment_id] = 1
            self.pennants[segment_id] = pennants
            self.open_edges[segment_id] = open_edges

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
        self.segment_counter = 0

    def _get_next_segment_id(self) -> str:
        self.segment_counter += 1
        return f"seg_{self.segment_counter}"

    def place_tile(self, x: int, y: int, tile: Tile) -> bool:
        """Places a tile on the board if the move is legal."""
        if (x, y) in self.grid:
            return False
        
        # Check adjacency and side matching
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
        
        if not has_adj:
            return False

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
        return True

    def is_completed(self, segment_id: str, segment_type: SegmentType) -> bool:
        """Checks if a city or road is completed (no open edges)."""
        if segment_type not in self.dsu:
            return False
        root = self.dsu[segment_type].find(segment_id)
        return self.dsu[segment_type].open_edges[root] == 0

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
