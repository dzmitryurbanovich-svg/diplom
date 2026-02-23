from src.logic.engine import Board
from src.logic.deck import create_starter_tile, create_city_straight_road, create_full_city
from src.logic.models import Side, SegmentType

def demo():
    board = Board()
    
    # 1. Place starter tile at (0,0)
    starter = create_starter_tile()
    print(f"Placing {starter.name} at (0,0): {board.place_tile(0, 0, starter)}")
    
    # 2. Try placing a mismatched tile at (0,1)
    # North of starter is CITY. South of this new tile must be CITY.
    # create_city_straight_road has CITY at NORTH by default. Let's rotate it 180.
    tile2 = create_city_straight_road()
    tile2.rotate(2) # Is now South city.
    print(f"Placing {tile2.name} at (0,1) rotated 180: {board.place_tile(0, 1, tile2)}")
    
    # 3. Check if the city is completed?
    # Starter had city on NORTH. tile2 had city on SOUTH. 
    # They should connect. 
    seg_id = tile2.segments[0].id # The city segment
    root = board.dsu[SegmentType.CITY].find(seg_id)
    open_edges = board.dsu[SegmentType.CITY].open_edges[root]
    print(f"City root: {root}, Open edges: {open_edges}")
    
    # 4. Place a tile to close the city if needed
    # Actually, starter city only had 1 side (N). tile2 city (after 180 rot) had 1 side (S).
    # Since they connect N-S, open edges should be (1+1) - 2 = 0!
    if board.is_completed(seg_id, SegmentType.CITY):
        print("SUCCESS: City is completed!")
    else:
        print("FAIL: City should be completed.")

if __name__ == "__main__":
    demo()
