import React, { useState, useEffect } from 'react';
import { GameBoard } from './GameBoard';
import { authLogin, startNewGame, fetchGameState, applyMove, triggerAiStep } from './api';
import type { GameState } from './types';
import { PlayCircle, LogIn, LayoutDashboard } from 'lucide-react';

function App() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogged, setIsLogged] = useState(false);
  const [session, setSession] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);

  const [p1, setP1] = useState('Human');
  const [p2, setP2] = useState('Star2.5');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await authLogin(email, password);
      if (res.success) {
        setIsLogged(true);
      } else {
        alert(res.message);
      }
    } catch (e) {
      alert("Login failed. Is the API running?");
    }
  };

  const handleStart = async () => {
    const s = await startNewGame(p1, p2);
    setSession(s);
    refreshState(s);
  };

  const refreshState = async (sid: string) => {
    const s = await fetchGameState(sid);
    setGameState(s);
  };

  const handleUserMove = async (x: number, y: number, r: number, meeple: string) => {
    if (!session) return;
    const res = await applyMove(session, x, y, r, meeple);
    if (!res.success) alert(res.message);
    refreshState(session);
  };

  // Game loop effect
  useEffect(() => {
    if (!session || !gameState || gameState.game_over) return;

    // If it's AI turn, request a step after a slight delay
    if (!gameState.is_human_turn) {
      const timer = setTimeout(async () => {
        await triggerAiStep(session);
        refreshState(session);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [session, gameState]);

  if (!isLogged) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 p-8 rounded-2xl shadow-2xl w-full max-w-md border border-slate-700">
          <div className="flex justify-center mb-6 text-blue-500"><LogIn size={48} /></div>
          <h1 className="text-2xl font-bold text-center text-white mb-2">Carcassonne Engine</h1>
          <p className="text-slate-400 text-center mb-6">Sign in to start the tournament</p>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full bg-slate-700 text-white p-3 rounded-xl border border-slate-600 outline-none focus:border-blue-500"
            />
            <input
              type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full bg-slate-700 text-white p-3 rounded-xl border border-slate-600 outline-none focus:border-blue-500"
            />
            <button className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-bold transition">Login</button>
          </form>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-4xl mx-auto bg-slate-800 p-8 rounded-2xl border border-slate-700 text-white">
          <h1 className="text-3xl font-bold flex items-center gap-3 mb-6"><LayoutDashboard /> Scenario Selection</h1>
          <div className="grid grid-cols-2 gap-8 mb-8">
            <div className="bg-slate-700 p-6 rounded-xl">
              <label className="block text-slate-300 text-sm mb-2">Player 1 (Red)</label>
              <select value={p1} onChange={e => setP1(e.target.value)} className="w-full bg-slate-800 p-3 rounded border border-slate-600">
                <option>Human</option>
                <option>Greedy</option>
                <option>Star2.5</option>
                <option>MCTS</option>
                <option>Hybrid LLM</option>
              </select>
            </div>
            <div className="bg-slate-700 p-6 rounded-xl">
              <label className="block text-slate-300 text-sm mb-2">Player 2 (Blue)</label>
              <select value={p2} onChange={e => setP2(e.target.value)} className="w-full bg-slate-800 p-3 rounded border border-slate-600">
                <option>Human</option>
                <option>Greedy</option>
                <option>Star2.5</option>
                <option>MCTS</option>
                <option>Hybrid LLM</option>
              </select>
            </div>
          </div>
          <button onClick={handleStart} className="w-full bg-emerald-600 hover:bg-emerald-500 py-4 rounded-xl font-bold text-xl flex items-center justify-center gap-2">
            <PlayCircle /> Launch Match
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-slate-900 flex overflow-hidden text-slate-200">
      <div className="flex-1 p-4 h-full">
        {gameState && <GameBoard state={gameState} onMove={handleUserMove} />}
      </div>

      {/* Sidebar right */}
      <div className="w-80 bg-slate-800 border-l border-slate-700 p-4 flex flex-col h-full overflow-y-auto">
        <h2 className="text-xl font-bold mb-4 font-mono text-blue-400">TELEMETRY</h2>

        {gameState && (
          <div className="space-y-4 text-sm bg-slate-900 rounded p-4 border border-slate-700">
            <div className="flex justify-between">
              <span className="text-red-400 font-bold">Player 1: {gameState.scores['Player1']}</span>
              <span>Meeples: {gameState.meeples['Player1']}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-400 font-bold">Player 2: {gameState.scores['Player2']}</span>
              <span>Meeples: {gameState.meeples['Player2']}</span>
            </div>
            <div className="pt-2 border-t border-slate-700 text-slate-400">
              Deck Remainder: {gameState.deck_remaining}
            </div>
          </div>
        )}

        <h3 className="font-bold text-slate-400 mt-6 mb-2">Logs ({gameState?.logs.length})</h3>
        <div className="flex-1 space-y-2 font-mono text-xs overflow-y-auto w-full break-words bg-black/40 p-2 rounded">
          {gameState?.logs.map((L, i) => (
            <div key={i} className="py-1 border-b border-white/5">{L}</div>
          ))}
        </div>

        <button onClick={() => setSession(null)} className="mt-4 p-2 bg-red-600 hover:bg-red-500 w-full rounded text-sm font-bold">
          Abandon Match
        </button>
      </div>
    </div>
  );
}

export default App;
