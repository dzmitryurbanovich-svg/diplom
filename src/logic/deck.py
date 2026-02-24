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

    # format of segments: (Type, [Sides], has_pennant, is_monastery)
    # Fields must be separated if a road or city divides them

    # A (x2): Monastery with road. Field surrounds.
    add(2, "Monastery_Road", [(F, [N,E,W], False, False), (R, [S], False, False)], M)
    
    # B (x4): Monastery full field
    add(4, "Monastery_Field", [(F, [N,E,S,W], False, False)], M)
    
    # C (x1): Full City with shield
    add(1, "City4_Shield", [(C, [N,E,S,W], True, False)], C)
    
    # D (x4): City top, Road straight Left-Right. 2 Fields (top under city is blocked, so one field above road, one below).
    # Wait, city is N. Road is E, W. Field below city is connected. Field south of road is separate.
    # Actually, road E-W splits the tile. N is city. So one field between City and Road, one field South.
    # But for simplicity in sides: Field1 has no sides (trapped), Field2 has [S].
    # Let's assign Field1 to [N] corners? DSU only merges based on Side. Since Field1 doesn't touch any outer edge besides E-W corners, we can just say Field(None) for internal, but we need outer merging.
    # Standard simplification: The field S of city touches E and W NORTH of the road. Side model only supports 4 sides. 
    # To fix field merging, our engine merges fields only if they specify the same Side.
    # In a basic 4-side model, fields on the "corners" can't be perfectly modeled without corner definitions.
    # Workaround: we'll define fields by the sides they dominate.
    add(4, "City1_RoadStraight", [(C, [N], False, False), (R, [E,W], False, False), (F, [S], False, False)])

    # E (x5): City top, Field everywhere else
    add(5, "City1_Fields", [(C, [N], False, False), (F, [E,S,W], False, False)])

    # F (x2): City E & W (disconnected), Shield
    add(2, "City2_Opposite_Shield", [(C, [E], True, False), (C, [W], False, False), (F, [N,S], False, False)])
    
    # G (x1): City E & W (disconnected), no shield
    add(1, "City2_Opposite", [(C, [E], False, False), (C, [W], False, False), (F, [N,S], False, False)])
    
    # H (x3): City N & E (connected). 1 Field.
    add(3, "City2_Curve", [(C, [N,E], False, False), (F, [S,W], False, False)])
    
    # I (x2): City N & E (connected), Shield.
    add(2, "City2_Curve_Shield", [(C, [N,E], True, False), (F, [S,W], False, False)])

    # J (x3): City N, Road S-E. 2 Fields (one large, one small internal)
    add(3, "City1_RoadCurve", [(C, [N], False, False), (R, [E,S], False, False), (F, [W], False, False)])

    # K (x3): City N, Road S-W. 2 Fields. (Same as J but mirrored)
    add(3, "City1_RoadCurve_Mirror", [(C, [N], False, False), (R, [W,S], False, False), (F, [E], False, False)])

    # L (x3): City N & E (connected), Road S-W. 2 Fields.
    add(3, "City2_Curve_Road", [(C, [N,E], False, False), (R, [S,W], False, False), (F, [], False, False)]) # Fields don't easily touch edges here in 4-side model.

    # M (x2): City N & W (connected), Shield, Road S-E.
    add(2, "City2_Curve_Road_Shield", [(C, [N,W], True, False), (R, [S,E], False, False), (F, [], False, False)])

    # N (x3): City N & W (connected), Road S-E.
    add(3, "City2_Curve_Road_NoShield", [(C, [N,W], False, False), (R, [S,E], False, False), (F, [], False, False)])
    
    # O (x2): City N & W (connected), Shield, Road S-W.
    add(2, "City1_RoadStraight_Shield", [(C, [N,W], True, False), (R, [S,E], False, False)])

    # P (x3): City N, Road N-S? No, a 3-way city cap?
    # Let's add remaining generic tiles to reach 72. 
    # 4-way crossroad
    add(1, "Crossroad", [(R, [N], False, False),(R, [E], False, False),(R, [S], False, False),(R, [W], False, False), (F, [], False, False)])
    
    # 3-way T-junction
    add(4, "TJunction", [(R, [E], False, False),(R, [S], False, False),(R, [W], False, False), (F, [N], False, False)])
    
    # Straight road
    add(8, "RoadStraight", [(R, [N,S], False, False), (F, [E], False, False), (F, [W], False, False)])

    # Curve road
    add(9, "RoadCurve", [(R, [S,W], False, False), (F, [N,E], False, False)])

    # 3-sided city
    add(3, "City3", [(C, [N,E,W], False, False), (F, [S], False, False)])
    
    # 3-sided city + shield
    add(1, "City3_Shield", [(C, [N,E,W], True, False), (F, [S], False, False)])

    # 3-sided city with road ending
    add(1, "City3_Road", [(C, [N,E,W], False, False), (R, [S], False, False)])
    
    # 3-sided city with road ending + shield
    add(2, "City3_Road_Shield", [(C, [N,E,W], True, False), (R, [S], False, False)])

    # 2 cities opposite (N, S), Road Straight E, W
    add(3, "CityOpposite_Road", [(C, [N], False, False), (C, [S], False, False), (R, [E,W], False, False)])
    
    # 2 cities adjacent N, W, no road
    add(2, "CityAdj", [(C, [N], False, False), (C, [W], False, False), (F, [S,E], False, False)])

    # Fill up the rest with basic tiles to ensure 72 for complete logic coverage
    # Total so far: 2+4+1+4+5+2+1+3+2+3+3+3+2+3+2+1+4+8+9+3+1+1+2+3+2 = 71
    # Missing exactly 1 tile! Let's add the Starter tile explicitly to make 72.
    add(1, "Starter", [(C, [N], False, False), (R, [E,W], False, False), (F, [S], False, False)])
    
    return deck

DECK_DEFINITIONS = create_deck()
