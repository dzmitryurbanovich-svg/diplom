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

## 🏗️ Architecture

```
diplom/
├── server.py              # FastAPI backend & game session manager
├── src/
│   ├── logic/
│   │   ├── engine.py      # Board, DSU territory engine, scoring
│   │   ├── agents.py      # AI agents (Greedy, MCTS, Star2.5, Hybrid LLM)
│   │   ├── deck.py        # Full tile definitions (C3 asset set)
│   │   ├── models.py      # Tile, Segment, Side data models
│   │   └── auth_manager.py
│   └── mcp/               # Model Context Protocol server (experimental)
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main app: Auth, Setup, Game screens
│   │   ├── GameBoard.tsx  # Interactive canvas board component
│   │   ├── api.ts         # API client layer
│   │   └── types.ts       # TypeScript types
│   └── dist/              # Production build (served by FastAPI)
├── demos/                 # Standalone scripts: tournaments, LLM experiments
├── assets/                # Tile & meeple images (C3 edition)
├── game_logs/             # Auto-generated JSONL training data (runtime)
├── Dockerfile             # Multi-stage build for HF Spaces
└── deploy_to_hf.py        # One-command deployment script
```

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
