import asyncio
import os
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from demos.agents_baseline import GreedyAgent
from demos.agents_hybrid import HybridAgent

# Your Hugging Face Space SSE URL
HF_SPACE_URL = "https://dzmitro-carcassonne-ai.hf.space/sse"

async def run_tournament():
    print(f"[*] Connecting to Cloud MCP Server: {HF_SPACE_URL}...")
    
    async with sse_client(HF_SPACE_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Define players: Greedy vs Hybrid
            # These agents are transport-agnostic and work with the cloud session
            players = [
                GreedyAgent("GreedyPlayer", session),
                HybridAgent("Hybrid_General", session)
            ]

            deck = ["starter", "city_road", "city_road", "city_road", "city_road", "city_road"]
            
            print(f"[*] Starting Cloud Tournament: {players[0].name} vs {players[1].name}")
            print(f"[*] Deck size: {len(deck)}")

            for i, tile_name in enumerate(deck):
                current_player = players[i % len(players)]
                print(f"\n--- Turn {i+1}: {current_player.name} drawing {tile_name} ---")
                
                success = await current_player.make_move(tile_name)
                
                if success:
                    print(f"[SUCCESS] {current_player.name} placed {tile_name}")
                else:
                    print(f"[FAILED] {current_player.name} could not make a legal move")

                # Show board
                board_result = await session.call_tool("get_board_state", {})
                print(board_result.content[0].text)

            # Final scoring (from strategic context)
            print("\n=== CLOUD TOURNAMENT RESULTS ===")
            stats = await session.call_tool("get_strategic_context", {})
            print(stats.content[0].text)

if __name__ == "__main__":
    # Ensure dependencies are installed: pip install httpx-sse
    try:
        asyncio.run(run_tournament())
    except ImportError:
        print("[ERROR] Missing dependencies! Please run: pip install httpx-sse")
    except Exception as e:
        print(f"[ERROR] Tournament failed: {e}")
