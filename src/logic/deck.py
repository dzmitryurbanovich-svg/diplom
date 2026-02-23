from .models import Tile, TileSegment, SegmentType, Side

def create_starter_tile() -> Tile:
    """The standard starting tile: City(N), Road(E, W), Field(S)."""
    return Tile(
        name="Starter",
        segments=[
            TileSegment(SegmentType.CITY, [Side.NORTH]),
            TileSegment(SegmentType.ROAD, [Side.EAST, Side.WEST]),
            TileSegment(SegmentType.FIELD, [Side.SOUTH])
        ]
    )

def create_city_straight_road() -> Tile:
    """Tile with city on one side and a road passing through."""
    return Tile(
        name="CitySideRoad",
        segments=[
            TileSegment(SegmentType.CITY, [Side.NORTH]),
            TileSegment(SegmentType.ROAD, [Side.SOUTH, Side.EAST]),
            TileSegment(SegmentType.FIELD, [Side.WEST])
        ]
    )

def create_full_city() -> Tile:
    """Rare tile: all City sides."""
    return Tile(
        name="FullCity",
        segments=[
            TileSegment(SegmentType.CITY, [Side.NORTH, Side.EAST, Side.SOUTH, Side.WEST], has_pennant=True)
        ]
    )

# This would be expanded to all 72 tiles in a full implementation
DECK_DEFINITIONS = {
    "starter": create_starter_tile,
    "full_city": create_full_city,
    "city_road": create_city_straight_road
}
