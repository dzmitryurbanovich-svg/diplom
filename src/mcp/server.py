import asyncio
import os
import json
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import mcp.types as types

from src.logic.engine import Board
from src.logic.deck import DECK_DEFINITIONS, create_starter_tile
from src.logic.models import Side, Tile, TileSegment, SegmentType
from src.mcp.prompts import SYSTEM_PROMPT, TOT_PROMPT_TEMPLATE

# Global game state (for demo purposes)
board = Board()
current_tile = None

server = Server("carcassonne-engine")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="get_board_state",
            description="Returns the current state of the game board.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_legal_moves",
            description="Returns all legal moves (x, y, rotation) for a given tile name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tile_name": {"type": "string", "description": "The name of the tile from the deck."}
                },
                "required": ["tile_name"],
            },
        ),
        types.Tool(
            name="place_tile",
            description="Places a tile on the board.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"oneOf": [{"type": "integer"}, {"type": "string"}]},
                    "y": {"oneOf": [{"type": "integer"}, {"type": "string"}]},
                    "rotation": {"oneOf": [{"type": "integer"}, {"type": "string"}], "enum": [0, 90, 180, 270, "0", "90", "180", "270"]},
                    "tile_name": {"type": "string"}
                },
                "required": ["x", "y", "rotation", "tile_name"],
            },
        ),
        types.Tool(
            name="get_strategic_context",
            description="Analyzes the board and returns a text summary of strategic opportunities.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="calculate_score",
            description="Calculates the Carcassonne score for all players at end of game.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scores": {
                        "type": "object",
                        "description": "Dict of player_name -> tiles_placed"
                    }
                },
                "required": ["scores"],
            },
        ),
        types.Tool(
            name="reset_board",
            description="Resets the game board to its initial empty state. Call this before starting a new tournament.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """List available prompts."""
    return [
        types.Prompt(
            name="strategic_advisor",
            description="A prompt that guides the LLM through a Tree of Thoughts decision process.",
            arguments=[
                types.PromptArgument(
                    name="tile_name",
                    description="Name of the tile to place",
                    required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """Get a specific prompt."""
    if name == "strategic_advisor":
        tile_name = arguments.get("tile_name", "unknown")
        # In a real scenario, we'd fetch legal moves here
        return types.GetPromptResult(
            description="Strategic orientation for the current turn.",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=TOT_PROMPT_TEMPLATE.format(tile_name=tile_name, legal_moves="[...]"),
                    ),
                )
            ],
        )
    raise ValueError(f"Unknown prompt: {name}")

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    global board
    
    if name == "get_board_state":
        content = board.render_ascii()
        return [types.TextContent(type="text", text=f"Current Board State:\n{content}")]

    elif name == "get_legal_moves":
        tile_name = arguments.get("tile_name")
        if tile_name not in DECK_DEFINITIONS:
            return [types.TextContent(type="text", text=f"Error: Tile '{tile_name}' not found.")]
        
        # Simple brute-force scanner for legal moves around existing tiles
        legal_moves = []
        # In a real game, we'd check all empty neighbors of occupied cells
        to_check = set()
        if not board.grid:
            to_check.add((0, 0))
        else:
            for (x, y) in board.grid:
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    if (x + dx, y + dy) not in board.grid:
                        to_check.add((x + dx, y + dy))
        
        for tx, ty in to_check:
            for rot in [0, 90, 180, 270]:
                test_tile = DECK_DEFINITIONS[tile_name]()
                test_tile.rotate(rot // 90)
                if board.is_legal_move(tx, ty, test_tile):
                    legal_moves.append({"x": tx, "y": ty, "rotation": rot})
        
        import sys
        print(f"[*] Returning {len(legal_moves)} legal moves for {tile_name}", file=sys.stderr)
        return [types.TextContent(type="text", text=json.dumps(legal_moves))]

    elif name == "place_tile":
        try:
            x = int(arguments.get("x"))
            y = int(arguments.get("y"))
            rot = int(arguments.get("rotation"))
        except (ValueError, TypeError):
            return [types.TextContent(type="text", text="Error: Coordinates and rotation must be integers.")]
            
        tile_name = arguments.get("tile_name")
        
        if tile_name not in DECK_DEFINITIONS:
            return [types.TextContent(type="text", text=f"Error: Tile '{tile_name}' not found.")]
        
        tile = DECK_DEFINITIONS[tile_name]()
        tile.rotate(rot // 90)
        
        success = board.place_tile(x, y, tile)
        if success:
            return [types.TextContent(type="text", text=f"Success: Placed {tile_name} at ({x}, {y}) with rotation {rot}.")]
        else:
            reason = "Reason unknown"
            if (x, y) in board.grid: reason = "Position occupied"
            elif not board.is_legal_move(x, y, tile): reason = "Illegal move (no adjacency or mismatch)"
            print(f"[ERROR] place_tile failed for {tile_name} at ({x}, {y}): {reason}", file=sys.stderr)
            return [types.TextContent(type="text", text=f"Error: Invalid move at ({x}, {y}). {reason}")]

    elif name == "get_strategic_context":
        # Simplified strategic analysis
        city_count = len([s for s in board.dsu[SegmentType.CITY].parent if board.dsu[SegmentType.CITY].parent[s] == s])
        road_count = len([s for s in board.dsu[SegmentType.ROAD].parent if board.dsu[SegmentType.ROAD].parent[s] == s])
        
        report = f"Strategic situation:\n- Open cities: {city_count}\n- Active roads: {road_count}\n"
        report += "Focus: Look for opportunities to complete cities for points or use roads to block opponent expansion."
        
        return [types.TextContent(type="text", text=report)]

    elif name == "calculate_score":
        # Carcassonne scoring rules:
        # Completed city: 2 pts per tile + 2 per pennant
        # Incomplete city (at game end): 1 pt per tile + 1 per pennant
        # Completed road: 1 pt per tile
        # Incomplete road: 1 pt per tile
        total_tiles = len(board.grid)

        # Count cities and roads in DSU
        city_dsu = board.dsu.get(SegmentType.CITY)
        road_dsu = board.dsu.get(SegmentType.ROAD)

        city_points = 0
        road_points = 0

        if city_dsu:
            seen_city_roots = set()
            for seg_id in city_dsu.parent:
                root = city_dsu.find(seg_id)
                if root not in seen_city_roots:
                    seen_city_roots.add(root)
                    size = city_dsu.size.get(root, 1)
                    pennants = city_dsu.pennants.get(root, 0)
                    open_edges = city_dsu.open_edges.get(root, 1)
                    is_complete = (open_edges == 0)
                    pts_per_tile = 2 if is_complete else 1
                    city_points += (size + pennants) * pts_per_tile

        if road_dsu:
            seen_road_roots = set()
            for seg_id in road_dsu.parent:
                root = road_dsu.find(seg_id)
                if root not in seen_road_roots:
                    seen_road_roots.add(root)
                    size = road_dsu.size.get(root, 1)
                    road_points += size  # 1 pt per tile always

        total_score = city_points + road_points
        result = {
            "total_tiles_placed": total_tiles,
            "city_points": city_points,
            "road_points": road_points,
            "total_points": total_score
        }
        return [types.TextContent(type="text", text=json.dumps(result))]

    elif name == "reset_board":
        board = Board()
        return [types.TextContent(type="text", text="Board reset successfully.")]

    raise ValueError(f"Unknown tool: {name}")

async def main_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="carcassonne",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

# --- SSE / Web Server Implementation ---
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (
        read_stream,
        write_stream,
    ):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="carcassonne",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

async def handle_root(request):
    return JSONResponse({"status": "running", "mcp_endpoint": "/sse"})

starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/", endpoint=handle_root),
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--sse":
        import uvicorn
        port = int(os.environ.get("PORT", 7860)) # Default HF port
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        asyncio.run(main_stdio())
