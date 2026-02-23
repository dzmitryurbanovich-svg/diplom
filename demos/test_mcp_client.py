import asyncio
import json
import sys

async def run_test():
    # Start the server process
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    process = await asyncio.create_subprocess_exec(
        "venv/bin/python", "src/mcp/server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

    async def send_request(method, params, req_id):
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        process.stdin.write(json.dumps(request).encode() + b"\n")
        await process.stdin.drain()

    # 1. Initialize
    await send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }, 1)
    
    line = await process.stdout.readline()
    print(f"Init Response: {line.decode().strip()}")

    # 2. Call get_board_state
    await send_request("tools/call", {
        "name": "get_board_state",
        "arguments": {}
    }, 2)
    
    line = await process.stdout.readline()
    print(f"Board Response: {line.decode().strip()}")

    # 3. Call place_tile (starter)
    await send_request("tools/call", {
        "name": "place_tile",
        "arguments": {"x": 0, "y": 0, "rotation": 0, "tile_name": "starter"}
    }, 3)
    
    line = await process.stdout.readline()
    print(f"Place Response: {line.decode().strip()}")

    # 4. Final state
    await send_request("tools/call", {
        "name": "get_board_state",
        "arguments": {}
    }, 4)
    
    line = await process.stdout.readline()
    print(f"Final Board Response: {line.decode().strip()}")

    process.terminate()
    await process.wait()

if __name__ == "__main__":
    asyncio.run(run_test())
