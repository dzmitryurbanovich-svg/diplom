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
                {"role": "system", "content": "You are a Carcassonne AI. You follow a strict 4-step turn protocol:\n1. Call 'get_board_state' to see the current field.\n2. Call 'get_strategic_context' to understand the overall situation.\n3. Call 'get_legal_moves' for your current tile.\n4. Write a brief 'Tree of Thoughts' analysis and then call 'place_tile' with your chosen move.\nAll coordinates and rotation must be integers."},
                {"role": "user", "content": "It is your turn. You have a 'starter' tile. Please follow the 4-step protocol."}
            ]

            print("[*] Starting Autonomous Strategic Loop...")
            async with httpx.AsyncClient(timeout=120.0) as client:
                for turn in range(5): # Limit to 5 interactions
                    print(f"\n--- Interaction Step {turn+1} ---")
                    payload = {
                        "model": MODEL,
                        "messages": messages,
                        "tools": ollama_tools,
                        "stream": False
                    }
                    
                    try:
                        response = await client.post(OLLAMA_URL, json=payload)
                        response.raise_for_status()
                        result = response.json()
                    except Exception as e:
                        print(f"[ERROR] Ollama request failed: {e}")
                        break

                    message = result.get('message', {})
                    messages.append(message) # Add assistant's response to history
                    
                    # Show thoughts or plan
                    if message.get('content'):
                        print("\n[AI BRAIN]")
                        print("-" * 30)
                        print(message['content'])
                        print("-" * 30)
                    
                    # Handle tool calls
                    if 'tool_calls' in message:
                        tool_results_messages = []
                        for tool_call in message['tool_calls']:
                            func_name = tool_call['function']['name']
                            args = tool_call['function']['arguments']
                            
                            print(f"[!] Calling TOOL: {func_name}({args})")
                            
                            try:
                                mcp_result = await session.call_tool(func_name, args)
                                output_text = mcp_result.content[0].text
                                print(f"[*] Result: {output_text}")
                                
                                # If it was board state, print it visually too
                                if func_name == "get_board_state":
                                    print("\n[VISUAL BOARD]")
                                    print(output_text)

                                tool_results_messages.append({
                                    "role": "tool",
                                    "content": output_text,
                                    "tool_call_id": tool_call.get('id', 'temp-id') # Some models provide ID
                                })
                            except Exception as e:
                                 print(f"[ERROR] Tool execution failed: {e}")
                                 tool_results_messages.append({
                                    "role": "tool",
                                    "content": f"Error: {str(e)}",
                                    "tool_call_id": tool_call.get('id', 'temp-id')
                                })
                        
                        messages.extend(tool_results_messages)
                        
                        # Show board after turn actions
                        final_check = await session.call_tool("get_board_state", {})
                        print("\n[BOARD STATE AFTER ACTION]")
                        print(final_check.content[0].text)
                    else:
                        print("[*] AI has finished its reasoning/no further moves.")
                        break

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except Exception as e:
        print(f"[ERROR] {e}")
