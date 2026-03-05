# 🧪 Demos & Standalone Scripts

This folder contains standalone scripts for research experiments, tournament running, and LLM agent exploration. These scripts are **independent** from the web server and can be run directly from the project root.

## Scripts

| File | Description |
|---|---|
| `demo_engine.py` | Minimal demonstration of the game engine in the console |
| `play_game_ai.py` | Run a full AI vs AI match from the terminal with verbose output |
| `tournament_runner.py` | Run multi-game tournament brackets and collect statistics |
| `tournament_runner_cloud.py` | Tournament runner adapted for Hugging Face Inference API |
| `agents_baseline.py` | Baseline Greedy / Star agents for benchmarking |
| `agents_hf.py` | Agent using HF Inference API (Llama-3-70B) |
| `agents_hybrid.py` | Hybrid MCTS + LLM agent prototype |
| `agents_llm.py` | Pure LLM agent (zero-shot) |
| `ollama_agent.py` | Local Ollama agent (runs LLMs locally via Ollama) |
| `test_mcp_client.py` | Test client for the MCP protocol server |

## Usage

```bash
# Run from project root
python demos/play_game_ai.py
python demos/tournament_runner.py
```
