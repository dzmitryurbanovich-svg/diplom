import asyncio
import httpx
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

async def run_agent():
    # 1. Setup MCP Server connection parameters
    server_params = StdioServerParameters(
        command="venv/bin/python",
        args=["src/mcp/server.py"],
        env={**os.environ, "PYTHONPATH": os.getcwd()}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize MCP session
            await session.initialize()

            # 2. Get available tools from MCP
            tools_response = await session.list_tools()
            mcp_tools = tools_response.tools

            # Convert MCP tools to Ollama format
            ollama_tools = []
            for tool in mcp_tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            print(f"[*] Found {len(ollama_tools)} tools from MCP server.")

            # 3. Ask Ollama to act
            messages = [
                {"role": "system", "content": "You are a Carcassonne AI. Use tools to play the game."},
                {"role": "user", "content": "Check the board state, and if it's empty, place a 'starter' tile at (0,0) with 0 rotation."}
            ]

            print("[*] Sending request to Ollama...")
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": MODEL,
                    "messages": messages,
                    "tools": ollama_tools,
                    "stream": False
                }
                
                try:
                    response = await client.post(
                        OLLAMA_URL,
                        json=payload
                    )
                    if response.status_code != 200:
                        print(f"[ERROR] Ollama returned {response.status_code}: {response.text}")
                    response.raise_for_status()
                    result = response.json()
                except Exception as e:
                    print(f"[ERROR] Failed to contact Ollama: {e}")
                    return

                message = result.get('message', {})
                
                # 4. Handle tool calls from Ollama
                if 'tool_calls' in message:
                    for tool_call in message['tool_calls']:
                        func_name = tool_call['function']['name']
                        args = tool_call['function']['arguments']
                        
                        print(f"[!] Ollama wants to call Tool: {func_name}")
                        print(f"    Arguments: {args}")
                        
                        # Execute tool on MCP server
                        try:
                            mcp_result = await session.call_tool(func_name, args)
                            print(f"[*] MCP Server result: {mcp_result.content[0].text}")
                        except Exception as e:
                             print(f"[ERROR] MCP Tool execution failed: {e}")
                else:
                    print(f"[*] Ollama response Content: {message.get('content')}")

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except Exception as e:
        print(f"[ERROR] {e}")
