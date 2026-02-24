"""
tournament_runner.py
──────────────────────────────────────────────────────────────────────────────
Multi-game tournament between GreedyAgent and HybridAgent.

Scoring logic
─────────────
Each game produces a shared board.  At the end we call `calculate_score` on
the MCP server to get total city/road points, then split those points between
the two players proportional to the number of tiles each one successfully
placed (a simple but fair attribution rule).

Final winner is decided by cumulative points across all games.
──────────────────────────────────────────────────────────────────────────────
"""

import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from demos.agents_baseline import GreedyAgent
from demos.agents_hybrid import HybridAgent

# ── Tournament settings ────────────────────────────────────────────────────
NUM_GAMES = 3
DECK_TEMPLATE = [
    "starter",
    "city_road", "city_road", "city_road",
    "city_road", "city_road", "city_road",
    "city_road", "city_road",
]

# ── Helpers ────────────────────────────────────────────────────────────────

def print_banner(text: str, width: int = 70):
    print("\n" + "═" * width)
    print(f"  {text}")
    print("═" * width)

def print_section(text: str):
    print(f"\n{'─' * 50}")
    print(f"  {text}")
    print("─" * 50)

async def reset_board(session: ClientSession):
    """There is no reset tool, so we restart a fresh session per game."""
    pass  # handled by spawning a fresh server process per game


async def play_game(
    game_num: int,
    server_params: StdioServerParameters,
    agent_names: tuple[str, str],
) -> dict:
    """
    Runs one full game and returns a result dict:
        {
          agent_names[0]: score,
          agent_names[1]: score,
          "tiles_placed": {agent_names[0]: n, agent_names[1]: n},
          "winner": name | "Draw",
        }
    """
    print_banner(f"GAME {game_num}  ·  {agent_names[0]} vs {agent_names[1]}")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            players = [
                GreedyAgent(agent_names[0], session),
                HybridAgent(agent_names[1], session),
            ]

            tiles_placed = {p.name: 0 for p in players}
            failed_turns = {p.name: 0 for p in players}

            deck = list(DECK_TEMPLATE)  # copy

            for i, tile_name in enumerate(deck):
                current = players[i % len(players)]
                print(f"\n  Turn {i+1:>2} │ {current.name:<20} draws '{tile_name}'")

                success = await current.make_move(tile_name)

                if success:
                    tiles_placed[current.name] += 1
                    print(f"           │   ✓ placed successfully")
                else:
                    failed_turns[current.name] += 1
                    print(f"           │   ✗ could not place (no legal move)")

            # ── Score calculation ──────────────────────────────────────────
            print_section(f"Game {game_num} — Scoring")

            score_result = await session.call_tool(
                "calculate_score",
                {"scores": tiles_placed},
            )
            score_data = json.loads(score_result.content[0].text)

            total_pts   = score_data.get("total_points", 0)
            city_pts    = score_data.get("city_points", 0)
            road_pts    = score_data.get("road_points", 0)
            total_tiles = score_data.get("total_tiles_placed", 1) or 1

            print(f"  Board totals  →  City: {city_pts} pts | Road: {road_pts} pts | Total: {total_pts} pts")
            print(f"  Tiles placed  →  {tiles_placed}")

            # Proportional attribution
            player_scores: dict[str, float] = {}
            for p in players:
                share = tiles_placed[p.name] / total_tiles
                player_scores[p.name] = round(total_pts * share, 1)

            # Determine game winner
            names_sorted = sorted(player_scores, key=lambda n: player_scores[n], reverse=True)
            if player_scores[names_sorted[0]] == player_scores[names_sorted[1]]:
                game_winner = "Draw"
            else:
                game_winner = names_sorted[0]

            print(f"\n  ┌─ Game {game_num} result ─────────────────────────────────────┐")
            for p in players:
                marker = " ← WINNER" if p.name == game_winner else ""
                print(f"  │  {p.name:<22}  {player_scores[p.name]:>6.1f} pts{marker}")
            if game_winner == "Draw":
                print(f"  │  *** DRAW ***")
            print(f"  └──────────────────────────────────────────────────────────┘")

            return {
                **player_scores,
                "tiles_placed": tiles_placed,
                "winner": game_winner,
            }


async def run_tournament():
    server_params = StdioServerParameters(
        command="venv/bin/python",
        args=["src/mcp/server.py"],
        env={**os.environ, "PYTHONPATH": os.getcwd()},
    )

    agent_names = ("GreedyPlayer", "Hybrid_General")

    # Accumulators
    total_scores: dict[str, float] = {n: 0.0 for n in agent_names}
    game_wins:    dict[str, int]   = {n: 0 for n in agent_names}
    draws = 0

    print_banner(
        f"TOURNAMENT START  ·  {NUM_GAMES} games  ·  "
        f"{agent_names[0]} (Greedy) vs {agent_names[1]} (Hybrid LLM)"
    )

    for g in range(1, NUM_GAMES + 1):
        result = await play_game(g, server_params, agent_names)

        for name in agent_names:
            total_scores[name] += result.get(name, 0.0)

        if result["winner"] == "Draw":
            draws += 1
        elif result["winner"] in game_wins:
            game_wins[result["winner"]] += 1

    # ── Grand final tally ─────────────────────────────────────────────────
    print_banner("TOURNAMENT FINAL RESULTS")

    print(f"\n  {'Algorithm':<24} {'Wins':>6} {'Total pts':>10}")
    print(f"  {'─'*24} {'─'*6} {'─'*10}")
    for name in agent_names:
        alg_label = "Greedy heuristic" if "Greedy" in name else "Hybrid LLM"
        print(f"  {name:<24} {game_wins[name]:>6} {total_scores[name]:>10.1f}")

    print(f"\n  Draws: {draws}")
    print()

    # Determine overall champion
    if total_scores[agent_names[0]] == total_scores[agent_names[1]]:
        champion = "DRAW — agents are evenly matched!"
    else:
        champion = max(total_scores, key=lambda n: total_scores[n])
        alg = "Greedy heuristic" if "Greedy" in champion else "Hybrid LLM"
        margin = abs(total_scores[agent_names[0]] - total_scores[agent_names[1]])
        champion = f"{champion}  [{alg}]  (+{margin:.1f} pts advantage)"

    print(f"  🏆  CHAMPION: {champion}")
    print()


if __name__ == "__main__":
    asyncio.run(run_tournament())
