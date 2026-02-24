import httpx
import json
from mcp import ClientSession
from demos.agents_baseline import BaseAgent

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1"

class LLMAgent(BaseAgent):
    def __init__(self, name, session: ClientSession, strategy="standard"):
        super().__init__(name, session)
        self.strategy = strategy

    async def make_move(self, tile_name):
        # 1. Get available tools
        tools_response = await self.session.list_tools()
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

        system_prompt = "You are a Carcassonne expert AI. "
        if self.strategy == "tot":
             system_prompt += "Use a Tree of Thoughts strategy: explore multiple legal moves, evaluate their long-term scoring potential (completing cities, roads), and choose the optimal location."
        else:
             system_prompt += "Make a strategic move to maximize your score."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The current tile is '{tile_name}'. Analyze the board state, get legal moves, and place the tile optimally."}
        ]

        async with httpx.AsyncClient(timeout=120.0) as client:
            turn_complete = False
            attempts = 0
            while not turn_complete and attempts < 5:
                attempts += 1
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
                    print(f"[AI THOUGHTS] {self.name}: {message['content']}")

                if 'tool_calls' in message:
                    for tool_call in message['tool_calls']:
                        func_name = tool_call['function']['name']
                        args = tool_call['function']['arguments']
                        
                        mcp_result = await self.session.call_tool(func_name, args)
                        output = mcp_result.content[0].text
                        
                        messages.append({
                            "role": "tool",
                            "content": output,
                            "tool_call_id": tool_call.get('id', 'id')
                        })
                        
                        if func_name == "place_tile" and "Success" in output:
                            turn_complete = True
                            return True # Explicit success
                else:
                    # AI just talked, didn't call tool
                    break
            return False # Failed to place tile
