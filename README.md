# 🏰 Carcassonne AI — Diploma Research Project

> An advanced digital implementation of the classic board game *Carcassonne*, designed as a research testbed for AI strategy comparison and a graduation thesis on intelligent game agents.

**Live Demo → [dzmitro-carcassonne-ai.hf.space](https://dzmitro-carcassonne-ai.hf.space)**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent AI** | Greedy, MCTS, Star2.5, and Hybrid LLM Agents compete head-to-head |
| 🧠 **Hybrid LLM Strategy** | Llama-3-70B via Hugging Face Inference for high-level strategic planning |
| ⚡ **Real-time Board** | Interactive canvas with Pan & Zoom, animated tile placements |
| 🎯 **Full Ruleset** | Cities, Roads, Monasteries, and Fields (Farmers) with accurate scoring |
| 📂 **Training Logs** | Every move auto-logged to JSONL for AI model fine-tuning (RLHF) |
| 🔐 **Auth System** | User registration/login with guest access |
| 🚀 **Cloud Deployment** | Multi-stage Docker on Hugging Face Spaces |

---

## 🏗️ Architecture & Organization

The repository is divided into three distinct areas:

### 1. 🌐 Web Game (Server)
Everything needed to run the interactive Carcassonne game on **Hugging Face Spaces** or locally.
- `server.py`: FastAPI backend, session manager, and diagnostic endpoints.
- `src/logic/`: The core game engine (DSU-based), rule validation, and unified AI agents.
- `frontend/`: React + Three.js interactive board (Source & Built assets).
- `assets/`: 4K Tile textures and meeple models.

### 2. 🧪 AI Research & Analytics
Command-line tools for academic benchmarking and data collection.
- `scripts_research/`: 
  - `tournament_runner.py`: Run extensive game brackets (e.g., MCTS vs Hybrid LLM) and extract Win/Loss statistics.
  - `play_game_ai.py`: CLI-based game engine viewer with verbose tactical logs.
- `logs/telemetry/`: Auto-generated JSONL datasets from both Web and CLI gameplay.

### 3. 🎓 Diploma Thesis (Academic)
- `thesis_latex/`: Complete LaTeX source code, PDF, and presentation for the graduation thesis.
- `thesis_latex/docs/`: Academic literature and research papers.

---

## 🚀 Quick Start (Local)

**Prerequisites:** Python 3.11+, Node.js 20+

```bash
# 1. Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000

# 2. Frontend (in a second terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** to play.

---

## 🤖 AI Agents

| Agent | Strategy | Strength |
|---|---|---|
| **Greedy** | Score-maximizing heuristic | Fast, predictable |
| **Star2.5** | Minimax with α-β pruning | Tactical, 2-ply lookahead |
| **MCTS** | Monte Carlo Tree Search | Strongest heuristic baseline |
| **Hybrid LLM** | MCTS + LLM strategic commentary | Experimental, research focus |

---

## 📂 Training Data Format

Every move is automatically appended to `game_logs/session_<id>.jsonl`:

```json
{"player": "Player1", "player_type": "MCTS", "move": {"x": 2, "y": -1, "rotation": 90, "meeple": "None"}, "timestamp": 1740000000.0, "scores": {"Player1": 8, "Player2": 4}, "deck_remaining": 62}
```

Useful for RLHF, imitation learning, and behavioral cloning experiments.

---

## 🎓 Academic Context

This project is the practical component of a diploma thesis on **"Comparative Analysis of AI Strategy Methods in Tile-Based Board Games"**. It benchmarks classical search (MCTS) against modern LLM-driven agents in a fully-featured Carcassonne environment.

## 📝 License

GPL-3.0 License — see [LICENSE](LICENSE).
