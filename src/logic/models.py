from enum import Enum, auto
from typing import List, Dict, Optional, Tuple

class SegmentType(Enum):
    CITY = auto()
    ROAD = auto()
    FIELD = auto()
    MONASTERY = auto()

class Side(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

class TileSegment:
    """Represents a part of a tile using node indices (0-11)."""
    def __init__(self, segment_type: SegmentType, nodes: List[int], has_pennant: bool = False, is_monastery: bool = False):
        self.type = segment_type
        self.nodes = nodes  # Indices 0-11
        self.has_pennant = has_pennant
        self.is_monastery = is_monastery
        self.id = None
        self.meeple_player: Optional[str] = None

    def __repr__(self):
        return f"Segment({self.type.name}, nodes={self.nodes}, meeple={self.meeple_player})"

class Tile:
    """Represents a single square tile in the game with 12 edge nodes."""
    def __init__(self, name: str, segments: List[TileSegment], center_type: SegmentType = SegmentType.FIELD):
        self.name = name
        self.segments = segments
        self.center_type = center_type
        self.rotation = 0

    def rotate(self, times: int = 1):
        """Rotates the tile by shifting node indices (3 nodes per 90 degrees)."""
        times = times % 4
        if times == 0: return
        self.rotation = (self.rotation + 90 * times) % 360
        shift = times * 3
        for segment in self.segments:
            segment.nodes = [(n + shift) % 12 for n in segment.nodes]

    def get_side_nodes(self, side: Side) -> List[int]:
        """Returns the 3 node indices associated with a specific side."""
        if side == Side.NORTH: return [0, 1, 2]
        if side == Side.EAST:  return [3, 4, 5]
        if side == Side.SOUTH: return [6, 7, 8]
        if side == Side.WEST:  return [9, 10, 11]
        return []

    def get_node_type(self, node_index: int) -> SegmentType:
        """Returns the segment type at a specific node index."""
        for segment in self.segments:
            if node_index in segment.nodes:
                return segment.type
        return SegmentType.FIELD # Default

    def __repr__(self):
        return f"Tile({self.name}, rotation={self.rotation})"
