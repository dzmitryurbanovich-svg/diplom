from .models import Tile, TileSegment, SegmentType, Side

def build_tile(name, segments, center=SegmentType.FIELD):
    return Tile(name, segments, center_type=center)

def create_deck() -> list[Tile]:
    N, E, S, W = Side.NORTH, Side.EAST, Side.SOUTH, Side.WEST
    C, R, F, M = SegmentType.CITY, SegmentType.ROAD, SegmentType.FIELD, SegmentType.MONASTERY
    
    deck = []
    
    def add(count, name, segments, center=F):
        for _ in range(count):
            deck.append(build_tile(name, [TileSegment(t, s, p, m) for t, s, p, m in segments], center))

    # A (x2): Monastery with road. Field surrounds. Road is SOUTH.
    add(2, "Tile_A", [(F, [N,E,W], False, False), (R, [S], False, False)], M)
    
    # B (x4): Monastery full field
    add(4, "Tile_B", [(F, [N,E,S,W], False, False)], M)
    
    # C (x1): Full City with shield
    add(1, "Tile_C", [(C, [N,E,S,W], True, False)], C)
    
    # D (x4): City N. Road E, W. Fields S, and underneath City.
    add(4, "Tile_D", [(C, [N], False, False), (R, [E,W], False, False), (F, [S], False, False)])

    # E (x5): City N. Field E, S, W.
    add(5, "Tile_E", [(C, [N], False, False), (F, [E,S,W], False, False)])

    # F (x2): City E, W (disconnected). Shield. Fields N, S.
    add(2, "Tile_F", [(C, [E], True, False), (C, [W], False, False), (F, [N,S], False, False)])
    
    # G (x1): City E, W (disconnected). Fields N, S.
    add(1, "Tile_G", [(C, [E], False, False), (C, [W], False, False), (F, [N,S], False, False)])
    
    # H (x3): City N, S (disconnected). Fields E, W.
    add(3, "Tile_H", [(C, [N], False, False), (C, [S], False, False), (F, [E,W], False, False)])
    
    # I (x2): City N & W (connected). Field E & S. Shield.
    # Note: PNG visual actually implies city on TWO edges. Let's assume N and W are City.
    # Actually from python output earlier: N=CITY, E=FIELD, S=FIELD, W=CITY.
    add(2, "Tile_I", [(C, [N,W], True, False), (F, [E,S], False, False)])

    # J (x3): City N. Road E & S. Fields W and inner.
    # From script: N=CITY, E=ROAD, S=ROAD, W=FIELD
    add(3, "Tile_J", [(C, [N], False, False), (R, [E,S], False, False), (F, [W], False, False)])

    # K (x3): City N. Road S & W. Fields E and inner.
    # From script: N=CITY, E=FIELD, S=ROAD, W=ROAD
    add(3, "Tile_K", [(C, [N], False, False), (R, [S,W], False, False), (F, [E], False, False)])

    # L (x3): City N. Road E, S, W. Field split.
    # From script: N=CITY, E=ROAD, S=ROAD, W=ROAD
    add(3, "Tile_L", [(C, [N], False, False), (R, [E,S,W], False, False), (F, [], False, False)])

    # M (x2): City N, E (connected). Shield. Fields S, W.
    # From script: N=CITY, E=CITY, S=FIELD, W=FIELD
    add(2, "Tile_M", [(C, [N,E], True, False), (F, [S,W], False, False)])

    # N (x3): City N, E (connected). Fields S, W.
    # From script: N=CITY, E=CITY, S=FIELD, W=FIELD
    add(3, "Tile_N", [(C, [N,E], False, False), (F, [S,W], False, False)])
    
    # O (x2): City N, W (connected). Road E, S. Shield.
    # From script: N=CITY, E=ROAD, S=ROAD, W=CITY
    add(2, "Tile_O", [(C, [N,W], True, False), (R, [E,S], False, False), (F, [], False, False)])

    # P (x3): City N, W (connected). Road E, S.
    # From script: N=CITY, E=ROAD, S=ROAD, W=CITY
    add(3, "Tile_P", [(C, [N,W], False, False), (R, [E,S], False, False), (F, [], False, False)])

    # Q (x1): City N, E, W. Shield. 
    # From script: N=CITY, E=CITY, S=FIELD, W=CITY
    add(1, "Tile_Q", [(C, [N,E,W], True, False), (F, [S], False, False)])

    # R (x3): City N, E, W.
    # From script: N=CITY, E=CITY, S=FIELD, W=CITY
    add(3, "Tile_R", [(C, [N,E,W], False, False), (F, [S], False, False)])

    # S (x2): City N, E, W. Road S. Shield.
    # From script: N=CITY, E=CITY, S=ROAD, W=CITY
    add(2, "Tile_S", [(C, [N,E,W], True, False), (R, [S], False, False)])

    # T (x1): City N, E, W. Road S.
    # From script: N=CITY, E=CITY, S=ROAD, W=CITY
    add(1, "Tile_T", [(C, [N,E,W], False, False), (R, [S], False, False)])
    
    # U (x8): Road N, S.
    # From script: N=ROAD, E=FIELD, S=ROAD, W=FIELD
    add(8, "Tile_U", [(R, [N,S], False, False), (F, [E], False, False), (F, [W], False, False)])

    # V (x9): Road S, W.
    # From script: N=FIELD, E=FIELD, S=ROAD, W=ROAD
    add(9, "Tile_V", [(R, [S,W], False, False), (F, [N,E], False, False)])

    # W (x4): Road E, S, W. (T-Junction)
    # From script: N=FIELD, E=ROAD, S=ROAD, W=ROAD
    add(4, "Tile_W", [(R, [E,S,W], False, False), (F, [N], False, False)])

    # X (x1): Road N, E, S, W. (Crossroad)
    # From script: N=ROAD, E=ROAD, S=ROAD, W=ROAD
    add(1, "Tile_X", [(R, [N], False, False), (R, [E], False, False), (R, [S], False, False), (R, [W], False, False), (F, [], False, False)])

    # Starter Tile is Tile D exactly.
    # Total = 2+4+1+4+5+2+1+3+2+3+3+3+2+3+2+3+1+3+2+1+8+9+4+1 = 71
    add(1, "Tile_Starter", [(C, [N], False, False), (R, [E,W], False, False), (F, [S], False, False)])
    
    return deck

DECK_DEFINITIONS = create_deck()
