import asyncio
import json
import os
import sys
from mcp import ClientSession
from mcp.client.sse import sse_client
from demos.agents_baseline import GreedyAgent
from demos.agents_hf import HFAgent

# Your Hugging Face Space SSE URL
if not os.environ.get("HF_TOKEN"):
    print("\n[ERROR] HF_TOKEN environment variable is not set!")
    print("Please export your Hugging Face API token before running the tournament:")
    print("  export HF_TOKEN='your_hf_token_here'")
    print("You can generate a token at https://huggingface.co/settings/tokens\n")
    sys.exit(1)

HF_SPACE_URL = os.environ.get("HF_SPACE_URL", "https://dzmitro-carcassonne-ai.hf.space/sse")

async def run_tournament():
    print(f"[*] Connecting to Cloud MCP Server: {HF_SPACE_URL}...")
    
    async with sse_client(HF_SPACE_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Reset board first to ensure a clean game each run
            reset_result = await session.call_tool("reset_board", {})
            print(f"[*] {reset_result.content[0].text}")

            players = [
                GreedyAgent("GreedyPlayer", session),
                HFAgent("Cloud_General", session)
            ]

            # 21-tile deck: variety of types
            deck = ["starter"] + ["city_road", "full_city", "city_road"] * 6 + ["city_road", "city_road"]
            
            print(f"[*] Starting Cloud Tournament: {players[0].name} vs {players[1].name}")
            print(f"[*] Deck size: {len(deck)}")

            # Per-player tracking
            per_player = {p.name: {"moves": 0, "success": 0} for p in players}

            for i, tile_name in enumerate(deck):
                current_player = players[i % len(players)]
                print(f"\n--- Turn {i+1}: {current_player.name} drawing {tile_name} ---")
                
                success = await current_player.make_move(tile_name)
                per_player[current_player.name]["moves"] += 1
                
                if success:
                    per_player[current_player.name]["success"] += 1
                    print(f"[SUCCESS] {current_player.name} placed {tile_name}")
                else:
                    print(f"[FAILED] {current_player.name} could not make a legal move")

                board_result = await session.call_tool("get_board_state", {})
                print(board_result.content[0].text)

            # === FINAL SCORING (Carcassonne Rules) ===
            print("\n" + "="*55)
            print("   FINAL TOURNAMENT RESULTS  (Carcassonne Rules)")
            print("="*55)

            score_result = await session.call_tool("calculate_score", {"scores": {}})
            score_data = json.loads(score_result.content[0].text)

            total_tiles = score_data["total_tiles_placed"]
            city_pts    = score_data["city_points"]
            road_pts    = score_data["road_points"]
            total_pts   = score_data["total_points"]

            total_successes = sum(s["success"] for s in per_player.values())

            print(f"\n  Tiles on board : {total_tiles}")
            print(f"  City points    : {city_pts}  (2pts/tile completed, 1pt incomplete)")
            print(f"  Road points    : {road_pts}  (1pt/tile)")
            print(f"  Board total    : {total_pts} pts\n")

            player_scores = {}
            for p_name, s in per_player.items():
                share  = (s["success"] / total_successes) if total_successes > 0 else 0
                earned = round(total_pts * share)
                player_scores[p_name] = earned
                pct    = round(s["success"] / s["moves"] * 100) if s["moves"] > 0 else 0
                print(f"  👤 {p_name}")
                print(f"     Successful moves : {s['success']}/{s['moves']}  ({pct}%)")
                print(f"     Points earned    : {earned} pts\n")

            winner = max(player_scores, key=player_scores.get)
            print(f"  🥇 WINNER: {winner}  ({player_scores[winner]} pts)")
            print("="*55)

if __name__ == "__main__":
    try:
        asyncio.run(run_tournament())
    except Exception as e:
        print(f"[ERROR] Tournament failed: {e}")
