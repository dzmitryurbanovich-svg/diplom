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
    <div className="h-screen w-screen bg-slate-900 grid grid-rows-[3fr_2fr] md:grid-rows-1 md:grid-cols-[1fr_320px] overflow-hidden text-slate-200">
      {/* Game Board Area */}
      <div className="relative min-h-0 min-w-0 overflow-hidden border-b md:border-b-0 md:border-r border-slate-700">
        {gameState && <GameBoard state={gameState} onMove={handleUserMove} />}
      </div>

      {/* Telemetry Sidebar */}
      <div className="bg-slate-800 p-4 flex flex-col min-h-0 min-w-0 shadow-2xl z-10 overflow-hidden">
        <div className="flex justify-between items-center mb-4 shrink-0">
          <h2 className="text-lg font-bold font-mono text-blue-400">TELEMETRY</h2>
          {gameState && <span className="text-[10px] text-slate-500 uppercase">Room: {session?.slice(0, 8)}</span>}
        </div>

        {gameState && (
          <div className="grid grid-cols-2 md:grid-cols-1 gap-2 text-xs bg-slate-900/50 rounded-lg p-3 border border-slate-700/50 mb-4 shrink-0 shadow-inner">
            <div className="flex flex-col bg-red-500/10 p-2 rounded border border-red-500/20">
              <div className="flex justify-between items-center mb-1">
                <span className="text-red-400 font-bold">P1: {gameState.scores['Player1']}</span>
                <span className="text-[10px]">🛠️ {gameState.meeples['Player1']}</span>
              </div>
              <span className="text-[9px] text-red-300/60 uppercase font-mono tracking-tighter">{gameState.player_types['Player1']}</span>
            </div>
            <div className="flex flex-col bg-blue-500/10 p-2 rounded border border-blue-500/20">
              <div className="flex justify-between items-center mb-1">
                <span className="text-blue-400 font-bold">P2: {gameState.scores['Player2']}</span>
                <span className="text-[10px]">🛠️ {gameState.meeples['Player2']}</span>
              </div>
              <span className="text-[9px] text-blue-300/60 uppercase font-mono tracking-tighter">{gameState.player_types['Player2']}</span>
            </div>
            <div className="col-span-2 md:col-span-1 pt-1 text-center md:text-left text-slate-500 text-[10px]">
              DECK: {gameState.deck_remaining} LEFT
            </div>
          </div>
        )}

        <h3 className="font-bold text-slate-500 text-[10px] uppercase tracking-widest mb-2 shrink-0">Game Logs</h3>
        <div className="flex-1 min-h-0 font-mono text-[9px] overflow-y-auto w-full break-words bg-black/30 backdrop-blur-sm p-2 rounded border border-white/5 custom-scrollbar flex flex-col-reverse">
          <div className="flex flex-col">
            {gameState?.logs.map((L, i) => (
              <div key={i} className="py-1 border-b border-white/5 opacity-70 hover:opacity-100 transition-opacity">
                <span className="text-slate-600 mr-2">{i + 1}.</span>
                {L}
              </div>
            ))}
            {(!gameState?.logs || gameState.logs.length === 0) && <div className="text-slate-600 italic">No logs yet...</div>}
          </div>
        </div>

        <button
          onClick={() => { if (window.confirm("Abandon this match?")) setSession(null); }}
          className="mt-4 p-2 bg-red-600/80 hover:bg-red-500 text-white w-full rounded text-xs font-bold transition-all shadow-lg active:scale-95 shrink-0"
        >
          Abandon Match
        </button>
      </div>
    </div>
  );
}

export default App;
