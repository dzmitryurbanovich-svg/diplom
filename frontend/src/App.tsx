import React, { useState, useEffect } from 'react';
import { GameBoard } from './GameBoard';
import { authLogin, authRegister, startNewGame, fetchGameState, applyMove, triggerAiStep } from './api';
import type { GameState } from './types';
import { PlayCircle, LogIn, LayoutDashboard } from 'lucide-react';

function App() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogged, setIsLogged] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [session, setSession] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);

  const [p1, setP1] = useState('Human');
  const [p2, setP2] = useState('Star2.5');

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (authMode === 'login') {
        const res = await authLogin(email, password);
        if (res.success) setIsLogged(true);
        else alert(res.message);
      } else {
        const res = await authRegister(email, password);
        alert(res.message);
        if (res.success) setAuthMode('login');
      }
    } catch (e) {
      alert("Authentication failed. Is the API running?");
    }
  };

  const handleGuest = () => {
    setEmail('guest@example.com');
    setIsLogged(true);
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
          <h1 className="text-2xl font-bold text-center text-white mb-2">Carcassonne AI</h1>
          <p className="text-slate-400 text-center mb-6">
            {authMode === 'login' ? 'Sign in to start the tournament' : 'Create an account to join'}
          </p>
          <form onSubmit={handleAuth} className="space-y-4">
            <input
              type="text" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full bg-slate-700 text-white p-3 rounded-xl border border-slate-600 outline-none focus:border-blue-500"
            />
            <input
              type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full bg-slate-700 text-white p-3 rounded-xl border border-slate-600 outline-none focus:border-blue-500"
            />
            <button className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-bold transition">
              {authMode === 'login' ? 'Login' : 'Register'}
            </button>
          </form>

          <div className="mt-6 flex flex-col gap-3">
            <button
              onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
              className="text-slate-400 hover:text-white text-sm transition text-center"
            >
              {authMode === 'login' ? "Don't have an account? Register" : "Already have an account? Login"}
            </button>
            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-700"></div></div>
              <div className="relative flex justify-center text-xs uppercase"><span className="bg-slate-800 px-2 text-slate-500">Or</span></div>
            </div>
            <button
              onClick={handleGuest}
              className="w-full border border-slate-600 hover:bg-slate-700 text-slate-300 py-2 rounded-xl text-sm transition"
            >
              Enter as Guest (Demo)
            </button>
          </div>
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
            <div className="grid grid-cols-1 gap-4">
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
          </div>
          <button onClick={handleStart} className="w-full bg-emerald-600 hover:bg-emerald-500 py-4 rounded-xl font-bold text-xl flex items-center justify-center gap-2 transition">
            <PlayCircle /> Launch Match
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-slate-900 flex overflow-hidden text-slate-200">
      <div className="flex-1 p-4 h-full relative">
        {gameState && <GameBoard state={gameState} onMove={handleUserMove} />}
      </div>

      <div className="w-80 bg-slate-800 border-l border-slate-700 p-4 flex flex-col h-full shrink-0">
        <h2 className="text-xl font-bold mb-4 font-mono text-blue-400 shrink-0">TELEMETRY</h2>

        {gameState && (
          <div className="space-y-4 text-sm bg-slate-900 rounded p-4 border border-slate-700 shrink-0">
            <div className="flex justify-between">
              <span className="text-red-400 font-bold">Player 1: {gameState.scores['Player1']}</span>
              <span>🛠️ {gameState.meeples['Player1']}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-400 font-bold">Player 2: {gameState.scores['Player2']}</span>
              <span>🛠️ {gameState.meeples['Player2']}</span>
            </div>
            <div className="pt-2 border-t border-slate-700 text-slate-400 text-xs">
              Deck Remainder: {gameState.deck_remaining}
            </div>
          </div>
        )}

        <h3 className="font-bold text-slate-400 mt-6 mb-2 shrink-0">Logs ({gameState?.logs.length})</h3>
        <div className="flex-1 space-y-2 font-mono text-[10px] overflow-y-auto w-full break-words bg-black/40 p-2 rounded custom-scrollbar">
          {gameState?.logs.map((L, i) => (
            <div key={i} className="py-1 border-b border-white/5 opacity-80">{L}</div>
          ))}
        </div>

        <button onClick={() => setSession(null)} className="mt-4 p-2 bg-red-600 hover:bg-red-500 w-full rounded text-sm font-bold transition shrink-0">
          Abandon Match
        </button>
      </div>
    </div>
  );
}

export default App;
