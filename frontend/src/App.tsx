import React, { useState, useEffect } from 'react';
import { GameBoard } from './GameBoard';
import { authLogin, authRegister, startNewGame, fetchGameState, applyMove, triggerAiStep } from './api';
import type { GameState } from './types';
import { PlayCircle, LogIn, LayoutDashboard, Volume2, VolumeX } from 'lucide-react';

// ─── Left-panel content components ───────────────────────────────────────────
// Keeping them as sub-components with a key prop triggers the CSS re-animation
// when switching screens, without unmounting the hero image on the right.

function AuthPanel({
  email, setEmail, password, setPassword, authMode, setAuthMode, onAuth, onGuest
}: {
  email: string; setEmail: (v: string) => void;
  password: string; setPassword: (v: string) => void;
  authMode: 'login' | 'register'; setAuthMode: (m: 'login' | 'register') => void;
  onAuth: (e: React.FormEvent) => void; onGuest: () => void;
}) {
  return (
    <div className="w-full max-w-sm bg-slate-800/80 p-8 rounded-3xl shadow-2xl border border-slate-700/50">
      <div className="flex justify-center mb-6 text-blue-500">
        <div className="bg-blue-500/10 p-4 rounded-2xl border border-blue-500/20 shadow-inner">
          <LogIn size={40} />
        </div>
      </div>
      <h1 className="text-3xl font-black text-center text-white mb-2 tracking-tight">Carcassonne AI</h1>
      <p className="text-slate-400 text-center mb-8 font-medium">
        {authMode === 'login' ? 'Sign in to start the tournament' : 'Join the elite AI strategist club'}
      </p>
      <form onSubmit={onAuth} className="space-y-4">
        <input
          type="text" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
          className="w-full bg-slate-900/50 text-white p-4 rounded-xl border border-slate-700 outline-none focus:border-blue-500 transition-all font-medium"
        />
        <input
          type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
          className="w-full bg-slate-900/50 text-white p-4 rounded-xl border border-slate-700 outline-none focus:border-blue-500 transition-all font-medium"
        />
        <button className="w-full bg-blue-600 hover:bg-blue-500 text-white py-4 rounded-xl font-black text-lg transition-all transform active:scale-95 shadow-lg shadow-blue-500/25">
          {authMode === 'login' ? 'Login' : 'Register'}
        </button>
      </form>
      <div className="mt-8 flex flex-col gap-4">
        <button
          onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
          className="text-slate-400 hover:text-white text-xs font-bold text-center underline underline-offset-4"
        >
          {authMode === 'login' ? "Don't have an account? Register" : "Already have an account? Login"}
        </button>
        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-700/50"></div></div>
          <div className="relative flex justify-center text-[10px] uppercase font-black tracking-widest">
            <span className="bg-slate-800 px-3 text-slate-500">Or</span>
          </div>
        </div>
        <button onClick={onGuest} className="w-full border border-slate-700 hover:bg-slate-700/50 text-slate-300 py-3 rounded-xl text-sm font-bold transition-all">
          Enter as Guest
        </button>
      </div>
    </div>
  );
}

function SetupPanel({
  email, p1, setP1, p2, setP2, onStart, onLogout
}: {
  email: string; p1: string; setP1: (v: string) => void;
  p2: string; setP2: (v: string) => void;
  onStart: () => void; onLogout: () => void;
}) {
  return (
    <div className="w-full max-w-sm">
      <h1 className="text-3xl font-black flex items-center gap-4 mb-2 text-white tracking-tight">
        <div className="bg-emerald-500 p-2 rounded-xl shadow-lg shadow-emerald-500/20"><LayoutDashboard size={32} /></div>
        Setup Match
      </h1>
      <p className="text-slate-400 mb-1 font-medium text-sm">Select your participants for this tournament session.</p>
      <p className="text-slate-600 mb-8 text-xs">
        Logged in as <span className="text-slate-400 font-mono">{email}</span>
        <button onClick={onLogout} className="ml-2 text-red-500/60 hover:text-red-400 underline text-[10px]">logout</button>
      </p>
      <div className="space-y-6 mb-8">
        <div className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700/50">
          <label className="block text-red-400 text-[10px] font-black uppercase tracking-[0.2em] mb-3">Player 1 (Red)</label>
          <select value={p1} onChange={e => setP1(e.target.value)} className="w-full bg-slate-900 text-white p-4 rounded-xl border border-slate-700 outline-none focus:ring-2 focus:ring-red-500 transition-all font-bold">
            <option>Human</option><option>Greedy</option><option>Star2.5</option><option>MCTS</option><option>Hybrid LLM</option>
          </select>
        </div>
        <div className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700/50">
          <label className="block text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] mb-3">Player 2 (Blue)</label>
          <select value={p2} onChange={e => setP2(e.target.value)} className="w-full bg-slate-900 text-white p-4 rounded-xl border border-slate-700 outline-none focus:ring-2 focus:ring-blue-500 transition-all font-bold">
            <option>Human</option><option>Greedy</option><option>Star2.5</option><option>MCTS</option><option>Hybrid LLM</option>
          </select>
        </div>
      </div>
      <button onClick={onStart} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-5 rounded-2xl font-black text-xl flex items-center justify-center gap-3 transition-all transform active:scale-95 shadow-xl shadow-emerald-500/30">
        <PlayCircle size={28} /> Start Game
      </button>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
function App() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogged, setIsLogged] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [session, setSession] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [p1, setP1] = useState('Human');
  const [p2, setP2] = useState('Star2.5');
  const [isMuted, setIsMuted] = useState(true); // Default muted due to browser policy
  const videoRef = React.useRef<HTMLVideoElement>(null);

  // Force video play on mount/update because autoPlay can be flaky
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.play().catch(e => console.error("Autoplay failed:", e));
    }
  }, [session]);

  // ─── Auto-login from localStorage ──────────────────────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem('carcassonne_user');
    if (saved) { setEmail(saved); setIsLogged(true); }
  }, []);

  useEffect(() => {
    if (isLogged && email) localStorage.setItem('carcassonne_user', email);
  }, [isLogged, email]);

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
    } catch {
      alert("Authentication failed. Is the API running?");
    }
  };

  const handleGuest = () => { setEmail('guest@example.com'); setIsLogged(true); };

  const handleLogout = () => {
    localStorage.removeItem('carcassonne_user');
    setIsLogged(false);
    setEmail('');
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

  const handleEndSession = () => {
    if (gameState?.game_over || window.confirm("Abandon this match?")) {
      setSession(null);
      setGameState(null);
    }
  };

  // ─── AI Game Loop — deduplicated, 100ms delay ──────────────────────────────
  const isFetchingRef = React.useRef(false);

  useEffect(() => {
    if (!session || !gameState || gameState.game_over) return;
    if (gameState.is_human_turn) return;
    if (isFetchingRef.current) return;

    const timer = setTimeout(async () => {
      isFetchingRef.current = true;
      try {
        await triggerAiStep(session);
        await refreshState(session);
      } finally {
        isFetchingRef.current = false;
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [session, gameState]);

  // ─── Pre-game screens (Auth + Setup) ─────────────────────────────────────
  // Hero image is rendered ONCE here and stays mounted during both screens.
  // Switching auth↔setup only swaps the left panel with a slide animation.
  if (!session) {
    const heroOverlayText = isLogged
      ? 'C3 EDITION • HIGH-FIDELITY AI TOURNAMENT'
      : null;

    return (
      <div className="min-h-screen w-full flex flex-row overflow-hidden bg-slate-900" style={{ backgroundColor: '#0f172a' }}>

        {/* Left Panel — slides in fresh on each screen change via key prop */}
        <div className="flex-shrink-0 w-full lg:w-[480px] min-h-screen flex items-center justify-center p-8 z-20 bg-slate-900 shadow-[20px_0_60px_rgba(0,0,0,0.5)]">
          <div key={isLogged ? 'setup' : 'auth'} className="w-full flex justify-center animate-fade-slide-in">
            {!isLogged
              ? <AuthPanel
                email={email} setEmail={setEmail}
                password={password} setPassword={setPassword}
                authMode={authMode} setAuthMode={setAuthMode}
                onAuth={handleAuth} onGuest={handleGuest}
              />
              : <SetupPanel
                email={email} p1={p1} setP1={setP1} p2={p2} setP2={setP2}
                onStart={handleStart} onLogout={handleLogout}
              />
            }
          </div>
        </div>

        {/* Right Panel — hero video is ALWAYS mounted, never reloads */}
        <div className="hidden lg:block relative flex-grow min-h-screen bg-slate-950">
          <video
            ref={videoRef}
            src="/hero_video.mp4"
            autoPlay
            loop
            muted={isMuted}
            playsInline
            className="absolute inset-0 w-full h-full object-cover opacity-80 z-0"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-slate-900 via-transparent/20 to-transparent z-10" />

          {/* Volume Toggle */}
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="absolute bottom-8 right-8 z-30 p-3 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full border border-white/10 text-white transition-all active:scale-95"
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </button>

          {/* Bottom overlay — shown on auth screen */}
          {!isLogged && (
            <div className="absolute bottom-16 left-16 z-20 text-white max-w-md drop-shadow-2xl animate-fade-in-up">
              <h2 className="text-4xl font-black mb-4 leading-tight">Master the Medieval Strategy.</h2>
              <p className="text-slate-200 font-medium leading-relaxed bg-black/20 backdrop-blur-sm p-4 rounded-2xl border border-white/10">
                Experience the classic Carcassonne enhanced by high-level AI algorithms. Build, compete, and evolve.
              </p>
            </div>
          )}

          {/* Top badge — shown on setup screen */}
          {isLogged && heroOverlayText && (
            <div className="absolute top-16 right-16 z-20 animate-fade-in">
              <div className="bg-black/60 backdrop-blur-md px-6 py-4 rounded-3xl border border-white/10 text-white/60 text-[10px] font-black tracking-widest shadow-2xl">
                {heroOverlayText}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── Game Screen — fades in ───────────────────────────────────────────────
  return (
    <div className="h-screen w-screen bg-slate-900 grid grid-rows-[3fr_2fr] md:grid-rows-1 md:grid-cols-[1fr_320px] overflow-hidden text-slate-200 animate-fade-in">
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
          onClick={handleEndSession}
          className={`mt-4 p-2 w-full rounded text-xs font-bold transition-all shadow-lg active:scale-95 shrink-0 ${gameState?.game_over ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-red-600/80 hover:bg-red-500 text-white'}`}
        >
          {gameState?.game_over ? 'New Game / Setup' : 'Abandon Match'}
        </button>
      </div>
    </div>
  );
}

export default App;
