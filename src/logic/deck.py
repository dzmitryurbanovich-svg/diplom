from .models import Tile, TileSegment, SegmentType, Side

def build_tile(name, segments, center=SegmentType.FIELD):
    return Tile(name, segments, center_type=center)

def _get_tile_factory(name, segments, center=SegmentType.FIELD):
    return lambda: build_tile(name, [TileSegment(t, s, p, m) for t, s, p, m in segments], center)

C, R, F, M = SegmentType.CITY, SegmentType.ROAD, SegmentType.FIELD, SegmentType.MONASTERY

TILE_TYPES = {
    # Node Map: N(0,1,2), E(3,4,5), S(6,7,8), W(9,10,11)
    "Tile_A": _get_tile_factory("Tile_A", [(F, [0,1,2,3,4,5,6,8,9,10,11], False, False), (R, [7], False, False)], M),
    "Tile_B": _get_tile_factory("Tile_B", [(F, [0,1,2,3,4,5,6,7,8,9,10,11], False, False)], M),
    "Tile_C": _get_tile_factory("Tile_C", [(C, [0,1,2,3,4,5,6,7,8,9,10,11], True, False)], C),
    "Tile_D": _get_tile_factory("Tile_D", [(C, [0,1,2], False, False), (R, [4,10], False, False), (F, [3], False, False), (F, [5,6,7,8,9], False, False), (F, [11], False, False)]),
    "Tile_E": _get_tile_factory("Tile_E", [(C, [0,1,2], False, False), (F, [3,4,5,6,7,8,9,10,11], False, False)]),
    "Tile_F": _get_tile_factory("Tile_F", [(C, [3,4,5], True, False), (C, [9,10,11], False, False), (F, [0,1,2,6,7,8], False, False)]),
    "Tile_G": _get_tile_factory("Tile_G", [(C, [3,4,5], False, False), (C, [9,10,11], False, False), (F, [0,1,2,6,7,8], False, False)]),
    "Tile_H": _get_tile_factory("Tile_H", [(C, [0,1,2], False, False), (C, [6,7,8], False, False), (F, [3,4,5,9,10,11], False, False)]),
    "Tile_I": _get_tile_factory("Tile_I", [(C, [0,1,2,9,10,11], True, False), (F, [3,4,5,6,7,8], False, False)]),
    "Tile_J": _get_tile_factory("Tile_J", [(C, [0,1,2], False, False), (R, [4,7], False, False), (F, [3], False, False), (F, [5,6,8,9,10,11], False, False)]),
    "Tile_K": _get_tile_factory("Tile_K", [(C, [0,1,2], False, False), (R, [7,10], False, False), (F, [3,4,5,6,8,9], False, False), (F, [11], False, False)]),
    "Tile_L": _get_tile_factory("Tile_L", [(C, [0,1,2], False, False), (R, [4], False, False), (R, [7], False, False), (R, [10], False, False), (F, [3], False, False), (F, [5,6], False, False), (F, [8,9], False, False), (F, [11], False, False)]),
    "Tile_M": _get_tile_factory("Tile_M", [(C, [0,1,2,3,4,5], True, False), (F, [6,7,8,9,10,11], False, False)]),
    "Tile_N": _get_tile_factory("Tile_N", [(C, [0,1,2,3,4,5], False, False), (F, [6,7,8,9,10,11], False, False)]),
    "Tile_O": _get_tile_factory("Tile_O", [(C, [0,1,2,9,10,11], True, False), (R, [4,7], False, False), (F, [3], False, False), (F, [5,6,8], False, False)]),
    "Tile_P": _get_tile_factory("Tile_P", [(C, [0,1,2,9,10,11], False, False), (R, [4,7], False, False), (F, [3], False, False), (F, [5,6,8], False, False)]),
    "Tile_Q": _get_tile_factory("Tile_Q", [(C, [0,1,2,3,4,5,9,10,11], True, False), (F, [6,7,8], False, False)]),
    "Tile_R": _get_tile_factory("Tile_R", [(C, [0,1,2,3,4,5,9,10,11], False, False), (F, [6,7,8], False, False)]),
    "Tile_S": _get_tile_factory("Tile_S", [(C, [0,1,2,3,4,5,9,10,11], True, False), (R, [7], False, False), (F, [6,8], False, False)]),
    "Tile_T": _get_tile_factory("Tile_T", [(C, [0,1,2,3,4,5,9,10,11], False, False), (R, [7], False, False), (F, [6,8], False, False)]),
    "Tile_U": _get_tile_factory("Tile_U", [(R, [1,7], False, False), (F, [0,11,10,9,8], False, False), (F, [2,3,4,5,6], False, False)]),
    "Tile_V": _get_tile_factory("Tile_V", [(R, [7,10], False, False), (F, [11,0,1,2,3,4,5,6], False, False), (F, [8,9], False, False)]),
    "Tile_W": _get_tile_factory("Tile_W", [(R, [4], False, False), (R, [7], False, False), (R, [10], False, False), (F, [5,6], False, False), (F, [8,9], False, False), (F, [11,0,1,2,3], False, False)]),
    "Tile_X": _get_tile_factory("Tile_X", [(R, [1], False, False), (R, [4], False, False), (R, [7], False, False), (R, [10], False, False), (F, [2,3], False, False), (F, [5,6], False, False), (F, [8,9], False, False), (F, [11,0], False, False)]),
    "Tile_Starter": _get_tile_factory("Tile_Starter", [(C, [0,1,2], False, False), (R, [4,10], False, False), (F, [3], False, False), (F, [5,6,7,8,9], False, False), (F, [11], False, False)]),
}

def create_deck() -> list[Tile]:
    counts = {
        "Tile_A": 2, "Tile_B": 4, "Tile_C": 1, "Tile_D": 4, "Tile_E": 5, "Tile_F": 2,
        "Tile_G": 1, "Tile_H": 3, "Tile_I": 2, "Tile_J": 3, "Tile_K": 3, "Tile_L": 3,
        "Tile_M": 2, "Tile_N": 3, "Tile_O": 2, "Tile_P": 3, "Tile_Q": 1, "Tile_R": 3,
        "Tile_S": 2, "Tile_T": 1, "Tile_U": 8, "Tile_V": 9, "Tile_W": 4, "Tile_X": 1
    }
    deck = []
    for name, count in counts.items():
        for _ in range(count):
            deck.append(TILE_TYPES[name]())
    return deck

DECK_DEFINITIONS = TILE_TYPES
