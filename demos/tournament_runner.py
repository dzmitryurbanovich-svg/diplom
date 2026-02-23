import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from demos.agents_baseline import RandomAgent, GreedyAgent
from demos.agents_llm import LLMAgent

async def run_tournament():
    server_params = StdioServerParameters(
        command="venv/bin/python",
        args=["src/mcp/server.py"],
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Define players
            # We'll compare Greedy vs LLM (ToT)
            players = [
                GreedyAgent("GreedyPlayer", session),
                LLMAgent("AI_ToT", session, strategy="tot")
            ]

            deck = ["starter", "city_road", "city_road", "city_road", "city_road", "city_road"]
            
            print(f"[*] Starting Tournament: {players[0].name} vs {players[1].name}")
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
            print("\n=== TOURNAMENT RESULTS ===")
            stats = await session.call_tool("get_strategic_context", {})
            print(stats.content[0].text)

if __name__ == "__main__":
    asyncio.run(run_tournament())
