# 🧠 Source Logic — `src/`

Core Python modules powering the game engine and AI agents.

## `logic/`

| File | Description |
|---|---|
| `engine.py` | `Board` class — DSU-based territory management, legal move generation, scoring |
| `agents.py` | AI agents: `GreedyAgent`, `StarAgent`, `MCTSAgent`, `HybridLLMAgent` |
| `deck.py` | Full C3-edition tile deck with segment definitions |
| `models.py` | `Tile`, `TileSegment`, `Side`, `SegmentType` data classes |
| `auth_manager.py` | Simple in-memory user authentication |
| `telemetry.py` | Utility for structured game event tracking |

## `mcp/`

Experimental [Model Context Protocol](https://modelcontextprotocol.io/) server — exposes game state as an MCP resource so LLMs can query it directly.

| File | Description |
|---|---|
| `server.py` | MCP server exposing board state and legal moves |
| `prompts.py` | Prompt templates for LLM agents |
