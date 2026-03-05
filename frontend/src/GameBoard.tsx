import React, { useState, useRef, useEffect, useMemo } from 'react';
import type { GameState, LegalMove } from './types';
import { TransformWrapper, TransformComponent, type ReactZoomPanPinchRef } from 'react-zoom-pan-pinch';
import { RotateCw, Target, ZoomIn, ZoomOut, Maximize2, Move, UserCheck, X } from 'lucide-react';

interface GameBoardProps {
    state: GameState;
    onMove: (x: number, y: number, r: number, meeple: string) => void;
}

const TILE_SIZE = 120;

// Helper to determine meeple visual position based on segment sides
const getMeeplePosition = (sides: string[]) => {
    // Basic mapping of sides to percentage offsets
    // We need to account for tile rotation too if we want absolute precision, 
    // but the backend sends sides relative to the CURRENT rotation of segments.

    if (sides.length === 0) return { top: '50%', left: '50%' }; // Center (Monastery/Center)

    // If multiple sides, average them
    let top = 0;
    let left = 0;

    sides.forEach(side => {
        if (side === 'NORTH') { top += 15; left += 50; }
        else if (side === 'EAST') { top += 50; left += 85; }
        else if (side === 'SOUTH') { top += 85; left += 50; }
        else if (side === 'WEST') { top += 50; left += 15; }
    });

    return {
        top: `${top / sides.length}%`,
        left: `${left / sides.length}%`
    };
};

export const GameBoard: React.FC<GameBoardProps> = ({ state, onMove }) => {
    const [selectedMove, setSelectedMove] = useState<LegalMove | null>(null);
    const [rotation, setRotation] = useState<number>(0);
    const [selectedMeepleIdx, setSelectedMeepleIdx] = useState<number | null>(null);
    const transformRef = useRef<ReactZoomPanPinchRef>(null);

    // Filter moves that match current rotation constraints
    const validPlacements = useMemo(() =>
        state.legal_moves.filter(m => m.r === rotation),
        [state.legal_moves, rotation]);

    // Initial center on mount
    useEffect(() => {
        const timer = setTimeout(() => {
            if (transformRef.current) {
                transformRef.current.centerView(0.8);
            }
        }, 300);
        return () => clearTimeout(timer);
    }, []);

    // Auto-center on new moves
    useEffect(() => {
        if (transformRef.current && (state.last_played.x !== 0 || state.last_played.y !== 0)) {
            transformRef.current.centerView(0.8, 500);
        }
    }, [state.last_played.x, state.last_played.y]);

    // Compute grid bounds
    const bounds = useMemo(() => {
        let minX = -1, minY = -1, maxX = 1, maxY = 1;
        if (state.grid.length > 0) {
            minX = Math.min(...state.grid.map(t => t.x), ...state.legal_moves.map(m => m.x)) - 2;
            minY = Math.min(...state.grid.map(t => t.y), ...state.legal_moves.map(m => m.y)) - 2;
            maxX = Math.max(...state.grid.map(t => t.x), ...state.legal_moves.map(m => m.x)) + 2;
            maxY = Math.max(...state.grid.map(t => t.y), ...state.legal_moves.map(m => m.y)) + 2;
        }
        return { minX, minY, maxX, maxY };
    }, [state.grid, state.legal_moves]);

    const width = (bounds.maxX - bounds.minX + 1) * TILE_SIZE;
    const height = (bounds.maxY - bounds.minY + 1) * TILE_SIZE;

    const getPos = (x: number, y: number) => ({
        left: (x - bounds.minX) * TILE_SIZE,
        top: (bounds.maxY - y) * TILE_SIZE,
    });

    const handleCenter = () => {
        if (transformRef.current) {
            transformRef.current.resetTransform(500);
            setTimeout(() => transformRef.current?.centerView(0.8, 300), 100);
        }
    };

    const handleZoomIn = () => transformRef.current?.zoomIn(0.2);
    const handleZoomOut = () => transformRef.current?.zoomOut(0.2);

    const handleGhostClick = (move: LegalMove) => {
        if (selectedMove && selectedMove.x === move.x && selectedMove.y === move.y) {
            // Confirm placement
            onMove(move.x, move.y, rotation, selectedMeepleIdx !== null ? String(selectedMeepleIdx) : "None");
            setSelectedMove(null);
            setRotation(0);
            setSelectedMeepleIdx(null);
        } else {
            setSelectedMove(move);
        }
    };

    const handleRotate = () => {
        setRotation((r) => (r + 90) % 360);
        setSelectedMeepleIdx(null); // Reset meeple selection as segment positions change
    };

    return (
        <div className="flex flex-col h-full w-full bg-slate-900 overflow-hidden shadow-xl rounded-xl border border-slate-700 min-h-0 min-w-0">
            {/* HUD Panel */}
            <div className="bg-slate-800 p-3 border-b border-slate-700 flex flex-wrap justify-between items-center text-white gap-2 shrink-0 z-50">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Turn</div>
                        <div className={`px-2 py-0.5 rounded text-xs font-bold ${state.current_player === 'Player1' ? 'bg-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.3)]' : 'bg-blue-500 text-white shadow-[0_0_10px_rgba(59,130,246,0.3)]'}`}>
                            {state.current_player}
                        </div>
                    </div>
                    {state.is_human_turn && <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20 animate-pulse"><UserCheck size={12} /> YOUR TURN</div>}
                </div>

                {state.is_human_turn && state.pending_tile && (
                    <div className="flex items-center gap-3 bg-slate-700/50 px-3 py-1.5 rounded-lg border border-slate-600/50 animate-fade-in-up">
                        <div className="relative group">
                            <img
                                src={`/assets/tiles/Base_Game_C3_Tile_${state.pending_tile.replace('Tile_', '')}.png`}
                                className="w-10 h-10 shadow-lg rounded-sm border border-white/10"
                                style={{ transform: `rotate(${rotation}deg)`, transition: 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
                            />
                            <div className="absolute -bottom-1 -right-1 bg-slate-900 text-[8px] px-1 rounded border border-white/20">NEXT</div>
                        </div>

                        <button
                            onClick={handleRotate}
                            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-[10px] px-4 py-2 rounded font-bold transition shadow-lg active:scale-95"
                        >
                            <RotateCw size={14} /> ROTATE
                        </button>
                    </div>
                )}
            </div>

            {/* Board Canvas */}
            <div className="flex-1 relative bg-slate-950 min-h-0">
                {/* Floating Controls */}
                <div className="absolute bottom-10 left-10 z-[100] flex flex-col gap-3 p-3 bg-slate-900/90 backdrop-blur-md border-2 border-white/20 rounded-2xl shadow-2xl">
                    <button onClick={handleZoomIn} className="w-12 h-12 flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all shadow-lg active:scale-95" title="Zoom In"><ZoomIn size={24} /></button>
                    <button onClick={handleZoomOut} className="w-12 h-12 flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all shadow-lg active:scale-95" title="Zoom Out"><ZoomOut size={24} /></button>
                    <div className="w-full h-px bg-white/10 my-1" />
                    <button onClick={handleCenter} className="w-12 h-12 flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition-all shadow-lg active:scale-95" title="Recenter View"><Target size={24} /></button>
                    <button onClick={handleCenter} className="w-12 h-12 flex items-center justify-center bg-orange-600 hover:bg-orange-500 text-white rounded-xl transition-all shadow-lg active:scale-95" title="Reset Camera"><Maximize2 size={24} /></button>
                </div>

                <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-black/60 backdrop-blur-md px-6 py-2 rounded-full border border-white/10 text-xs text-blue-400 font-bold flex items-center gap-3 pointer-events-none shadow-2xl">
                    <Move size={14} className="animate-pulse" /> DRAG TO PAN • PINCH TO ZOOM
                </div>

                <TransformWrapper
                    ref={transformRef}
                    initialScale={0.8}
                    minScale={0.05}
                    maxScale={5}
                    centerOnInit={true}
                    limitToBounds={false}
                    wheel={{ step: 0.1 }}
                    doubleClick={{ disabled: true }}
                    panning={{ velocityDisabled: true }}
                >
                    <TransformComponent wrapperStyle={{ width: '100%', height: '100%' }} contentStyle={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <div
                            className="relative shadow-2xl ring-4 ring-white/5 cursor-grab active:cursor-grabbing"
                            style={{ width, height, background: '#1a1d23' }}
                        >
                            {/* Coordinate Grid */}
                            {Array.from({ length: bounds.maxX - bounds.minX + 1 }).map((_, i) => (
                                Array.from({ length: bounds.maxY - bounds.minY + 1 }).map((_, j) => {
                                    const gx = bounds.minX + i;
                                    const gy = bounds.minY + j;
                                    return (
                                        <div
                                            key={`grid-${gx}-${gy}`}
                                            className="absolute border border-white/[0.03] flex items-center justify-center pointer-events-none"
                                            style={{ ...getPos(gx, gy), width: TILE_SIZE, height: TILE_SIZE }}
                                        >
                                            <span className="text-[10px] text-white/10 font-mono">({gx},{gy})</span>
                                        </div>
                                    );
                                })
                            ))}

                            {/* Placed Tiles */}
                            {state.grid.map((tile, i) => (
                                <div
                                    key={`tile-${tile.x}-${tile.y}-${i}`}
                                    className={`absolute ${state.last_played.x === tile.x && state.last_played.y === tile.y ? 'animate-tile-drop' : ''}`}
                                    style={{ ...getPos(tile.x, tile.y), width: TILE_SIZE, height: TILE_SIZE, zIndex: 10 }}
                                >
                                    <img
                                        src={`/assets/tiles/Base_Game_C3_Tile_${tile.name.replace('Tile_', '')}.png`}
                                        className="w-full h-full shadow-2xl rounded-sm border border-white/5"
                                        style={{ transform: `rotate(${tile.rotation}deg)` }}
                                        alt={tile.name}
                                    />
                                    {/* Real Meeples */}
                                    {tile.meeples.map((m, midx) => (
                                        <div
                                            key={`meeple-${midx}`}
                                            className="absolute z-20 transition-transform hover:scale-125 animate-meeple-pop"
                                            style={{
                                                width: TILE_SIZE * 0.35,
                                                height: TILE_SIZE * 0.35,
                                                left: (TILE_SIZE / 2) - (TILE_SIZE * 0.175),
                                                top: (TILE_SIZE / 2) - (TILE_SIZE * 0.175),
                                            }}
                                        >
                                            <img
                                                src={`/assets/meeples/${m.player === 'Player1' ? 'red' : 'blue'}_meeple.${m.player === 'Player1' ? 'png' : 'jpg'}`}
                                                className="w-full h-full drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)]"
                                            />
                                        </div>
                                    ))}

                                    {/* Last Played Glow */}
                                    {state.last_played.x === tile.x && state.last_played.y === tile.y && (
                                        <div className="absolute inset-0 border-[3px] border-orange-400/80 z-20 pointer-events-none rounded-[1px] shadow-[inset_0_0_15px_-5px_#fb923c]" />
                                    )}
                                </div>
                            ))}

                            {/* Ghost Moves */}
                            {state.is_human_turn && validPlacements.map((move, i) => {
                                const isSelected = selectedMove && selectedMove.x === move.x && selectedMove.y === move.y;
                                return (
                                    <div
                                        key={`ghost-${move.x}-${move.y}-${i}`}
                                        className="absolute z-30 flex items-center justify-center transition-all"
                                        style={{ ...getPos(move.x, move.y), width: TILE_SIZE, height: TILE_SIZE, padding: '2px' }}
                                    >
                                        <div
                                            onClick={() => handleGhostClick(move)}
                                            className={`w-full h-full rounded border-2 cursor-pointer transition-all duration-300
                                                ${isSelected ? 'bg-black/40 border-emerald-400 border-4 shadow-[0_0_20px_rgba(52,211,153,0.4)]' : 'bg-white/5 border-white/10 border-dashed hover:bg-white/10 hover:border-white/30'}
                                            `}
                                        >
                                            <img
                                                src={`/assets/tiles/Base_Game_C3_Tile_${state.pending_tile?.replace('Tile_', '')}.png`}
                                                className={`w-full h-full object-cover transition-opacity duration-300 ${isSelected ? 'opacity-80' : 'opacity-0'}`}
                                                style={{ transform: `rotate(${rotation}deg)` }}
                                            />

                                            {isSelected && (
                                                <>
                                                    {/* Meeple Hotspots */}
                                                    {state.meeples[state.current_player] > 0 && state.meeple_choices.map((choice) => {
                                                        const pos = getMeeplePosition(choice.sides);
                                                        const isThisSelected = selectedMeepleIdx === choice.index;
                                                        return (
                                                            <div
                                                                key={`hotspot-${choice.index}`}
                                                                onClick={(e) => { e.stopPropagation(); setSelectedMeepleIdx(isThisSelected ? null : choice.index); }}
                                                                className={`absolute z-50 w-6 h-6 -ml-3 -mt-3 rounded-full border-2 transition-all cursor-crosshair flex items-center justify-center
                                                                    ${isThisSelected ? 'bg-emerald-500 border-white scale-125 shadow-lg' : 'bg-white/20 border-white/40 hover:bg-white/40 hover:scale-110 animate-hotspot-pulse'}
                                                                `}
                                                                style={{ top: pos.top, left: pos.left }}
                                                                title={`${choice.type} placement`}
                                                            >
                                                                {isThisSelected && <div className="text-[10px] font-black text-white">✓</div>}
                                                            </div>
                                                        );
                                                    })}

                                                    {/* Ghost Meeple Presentation */}
                                                    {selectedMeepleIdx !== null && (
                                                        <div
                                                            className="absolute z-40 transition-all duration-300 animate-meeple-pop pointer-events-none"
                                                            style={{
                                                                ...getMeeplePosition(state.meeple_choices.find(c => c.index === selectedMeepleIdx)?.sides || []),
                                                                width: TILE_SIZE * 0.3, height: TILE_SIZE * 0.3,
                                                                marginLeft: -(TILE_SIZE * 0.15), marginTop: -(TILE_SIZE * 0.15)
                                                            }}
                                                        >
                                                            <img
                                                                src={`/assets/meeples/${state.current_player === 'Player1' ? 'red' : 'blue'}_meeple.${state.current_player === 'Player1' ? 'png' : 'jpg'}`}
                                                                className="w-full h-full opacity-60 drop-shadow-xl"
                                                            />
                                                        </div>
                                                    )}

                                                    {/* Confirmation Overlay */}
                                                    <div className="absolute inset-0 flex flex-col items-center justify-end pb-2 pointer-events-none">
                                                        <div className="bg-emerald-500 text-white px-3 py-1 rounded-full text-[10px] font-black shadow-xl animate-bounce">CLICK AGAIN TO CONFIRM</div>
                                                    </div>

                                                    {/* Cancel Button */}
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); setSelectedMove(null); setSelectedMeepleIdx(null); }}
                                                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow-lg border border-white/20 pointer-events-auto hover:bg-red-400 transition-colors"
                                                    >
                                                        <X size={12} />
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </TransformComponent>
                </TransformWrapper>
            </div>
        </div>
    );
};
