# 🏰 Carcassonne AI Tournament Engine

🛡️ **Modern Web Stack**: React + Vite + Tailwind CSS v4 & FastAPI  
🤖 **Advanced AI**: MCTS, Greedy, and Hybrid LLM (Llama-3-70B via MCP)  
🚀 **Interactive UI**: High-speed Canvas rendering with Pan & Zoom  

An advanced digital implementation of the classic board game *Carcassonne*, specifically designed as a testing ground for various AI strategies and as part of a graduation thesis.

---

## ✨ Key Features

- **High-Performance Rendering**: Abandoned server-side Pillow rendering for client-side CSS/Canvas rendering.
- **Interactive Board**: Full Pan & Zoom support using `react-zoom-pan-pinch`.
- **Hybrid AI Strategy**: Combines heuristic tree search (MCTS) with LLM-based high-level strategic planning.
- **Full Ruleset Support**: Accurate implementation of Roads, Cities, Monasteries, and Fields (Farmers).
- **Telemetry & Logging**: Detailed JSON-based logging of every move for future model training (RLHF).

---

## 🏗️ Architecture

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.
- **Backend**: FastAPI (Python 3.11), Uvicorn, Pydantic.
- **Engine**: Custom graph-based DSU (Disjoint Set Union) for territory management and scoring.
- **Deployment**: Multi-stage Docker build hosted on Hugging Face Spaces.

## 🛠️ Usage (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+

### 1. Setup Backend
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to play!

---

## 🎓 Academic Context
This project serves as a practical demonstration for a diploma thesis on AI optimization in board games. It provides a robust framework for benchmarking MCTS against LLM-driven agents.

## 📝 License
GPL-3.0 License.
