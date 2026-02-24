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
    """Represents a part of a tile (e.g., a specific city fragment, road, or field)."""
    def __init__(self, segment_type: SegmentType, sides: List[Side], has_pennant: bool = False, is_monastery: bool = False):
        self.type = segment_type
        self.sides = sides
        self.has_pennant = has_pennant
        self.is_monastery = is_monastery
        self.id = None  # To be assigned by the board/DSU
        self.meeple_player: Optional[str] = None  # Which player owns the meeple on this segment

    def __repr__(self):
        return f"Segment({self.type.name}, sides={self.sides}, meeple={self.meeple_player})"

class Tile:
    """Represents a single square tile in the game."""
    def __init__(self, name: str, segments: List[TileSegment], center_type: SegmentType = SegmentType.FIELD):
        self.name = name
        self.segments = segments
        self.center_type = center_type
        self.rotation = 0  # 0, 90, 180, 270 degrees clockwise

    def rotate(self, times: int = 1):
        """Rotates the tile clockwise by 90 degrees * times."""
        self.rotation = (self.rotation + 90 * times) % 360
        for segment in self.segments:
            new_sides = []
            for side in segment.sides:
                new_sides.append(Side((side.value + times) % 4))
            segment.sides = new_sides

    def get_side_type(self, side: Side) -> SegmentType:
        """Returns the segment type on a specific side of the tile."""
        for segment in self.segments:
            if side in segment.sides:
                return segment.type
        return SegmentType.FIELD

    def __repr__(self):
        return f"Tile({self.name}, rotation={self.rotation})"
