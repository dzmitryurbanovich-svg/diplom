# 🧪 AI Research & Analytics

This folder contains command-line tools for simulating games, benchmarking AI performance, and generating research data for the diploma thesis.

## Core Scripts

| File | Description |
|---|---|
| `tournament_runner.py` | **The Main Benchmarker**: Run extensive game brackets and export Win/Loss statistics to `logs/telemetry/summary_stats.jsonl`. |
| `play_game_ai.py` | **Tactical Debugger**: Plays a single game between two agents with detailed console output of every move, rationale, and score change. |

## Usage

Run these scripts from the **project root**:

```bash
# Run a single AI battle
python scripts_research/play_game_ai.py

# Run a benchmarking tournament
python scripts_research/tournament_runner.py
```
