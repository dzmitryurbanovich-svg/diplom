import asyncio
import httpx
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

async def run_game():
    # Setup MCP Server connection parameters
    server_params = StdioServerParameters(
        command="venv/bin/python",
        args=["src/mcp/server.py"],
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Get available tools
            tools_response = await session.list_tools()
            ollama_tools = []
            for tool in tools_response.tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            messages = [
                {"role": "system", "content": "You are a Carcassonne AI. Your goal is to play 3 turns of the game autonomously. For each turn, you must: 1. Get board state, 2. Get legal moves, 3. Place a tile. Always use 'starter' for the first move, and 'city_side_road' for others. Use integers for coordinates."}
            ]

            print("[*] Starting 3-turn autonomous game session...")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                for turn in range(3):
                    print(f"\n=== GAME TURN {turn+1} ===")
                    messages.append({"role": "user", "content": f"Turn {turn+1}: Analyze the board and make your move."})
                    
                    # We enter a loop for the turn until the AI decides it's done or places a tile
                    turn_complete = False
                    while not turn_complete:
                        payload = {
                            "model": MODEL,
                            "messages": messages,
                            "tools": ollama_tools,
                            "stream": False
                        }
                        
                        response = await client.post(OLLAMA_URL, json=payload)
                        result = response.json()
                        message = result.get('message', {})
                        messages.append(message)

                        if message.get('content'):
                            print(f"[AI]: {message['content']}")

                        if 'tool_calls' in message:
                            for tool_call in message['tool_calls']:
                                func_name = tool_call['function']['name']
                                args = tool_call['function']['arguments']
                                print(f"[ACTION]: Calling {func_name}...")
                                
                                mcp_result = await session.call_tool(func_name, args)
                                output = mcp_result.content[0].text
                                print(f"[RESULT]: {output}")
                                
                                messages.append({
                                    "role": "tool",
                                    "content": output,
                                    "tool_call_id": tool_call.get('id', 'id')
                                })
                                
                                if func_name == "place_tile" and "Success" in output:
                                    turn_complete = True
                                    # Show final board of the turn
                                    final_board = await session.call_tool("get_board_state", {})
                                    print("\n[CURRENT BOARD]")
                                    print(final_board.content[0].text)
                        else:
                            turn_complete = True

            print("\n[*] Game session completed.")

if __name__ == "__main__":
    asyncio.run(run_game())
