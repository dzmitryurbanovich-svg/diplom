import React, { useState } from 'react';
import type { GameState, LegalMove } from './types';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { RotateCw } from 'lucide-react';

interface GameBoardProps {
    state: GameState;
    onMove: (x: number, y: number, r: number, meeple: string) => void;
}

const TILE_SIZE = 120;

export const GameBoard: React.FC<GameBoardProps> = ({ state, onMove }) => {
    const [selectedMove, setSelectedMove] = useState<LegalMove | null>(null);
    const [rotation, setRotation] = useState<number>(0);
    const [meepleTarget, setMeepleTarget] = useState<string>("None");

    // Filter moves that match current rotation constraints, or show all options
    const validPlacements = state.legal_moves.filter(m => m.r === rotation);

    // Compute grid bounds to center
    let minX = 0, minY = 0, maxX = 0, maxY = 0;
    if (state.grid.length > 0) {
        minX = Math.min(...state.grid.map(t => t.x), ...state.legal_moves.map(m => m.x)) - 1;
        minY = Math.min(...state.grid.map(t => t.y), ...state.legal_moves.map(m => m.y)) - 1;
        maxX = Math.max(...state.grid.map(t => t.x), ...state.legal_moves.map(m => m.x)) + 1;
        maxY = Math.max(...state.grid.map(t => t.y), ...state.legal_moves.map(m => m.y)) + 1;
    }

    const width = (maxX - minX + 1) * TILE_SIZE;
    const height = (maxY - minY + 1) * TILE_SIZE;

    // Convert game coordinates to pixel placement inside the canvas
    const getPos = (x: number, y: number) => {
        return {
            left: (x - minX) * TILE_SIZE,
            top: (maxY - y) * TILE_SIZE,
        };
    };

    const handleGhostClick = (move: LegalMove) => {
        if (selectedMove && selectedMove.x === move.x && selectedMove.y === move.y) {
            // Confirm move
            onMove(move.x, move.y, rotation, meepleTarget);
            setSelectedMove(null);
            setRotation(0);
            setMeepleTarget("None");
        } else {
            setSelectedMove(move);
        }
    };

    return (
        <div className="flex flex-col h-full bg-slate-900 overflow-hidden shadow-xl rounded-xl border border-slate-700">

            {/* HUD Panel */}
            <div className="bg-slate-800 p-4 border-b border-slate-700 flex justify-between items-center text-white">
                <div className="flex items-center gap-4">
                    <div className="text-sm font-semibold text-slate-400">TURN</div>
                    <div className={`px-3 py-1 rounded text-sm font-bold ${state.current_player === 'Player1' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                        {state.current_player}
                    </div>
                </div>

                {state.is_human_turn && state.pending_tile && (
                    <div className="flex items-center gap-4 bg-slate-700/50 p-2 rounded-lg">
                        <div className="flex flex-col items-center">
                            <span className="text-xs text-slate-400 mb-1">Draw</span>
                            <img
                                src={`/assets/tiles/Base_Game_C3_Tile_${state.pending_tile.replace('Tile_', '')}.png`}
                                className="w-12 h-12 shadow"
                                style={{ transform: `rotate(${rotation}deg)` }}
                            />
                        </div>

                        <div className="flex flex-col gap-2">
                            <button
                                onClick={() => setRotation((r) => (r + 90) % 360)}
                                className="flex items-center justify-center gap-2 bg-slate-600 hover:bg-slate-500 text-white text-xs px-3 py-1.5 rounded transition"
                            >
                                <RotateCw size={14} /> Rotate
                            </button>

                            <select
                                className="bg-slate-700 text-white text-xs p-1 rounded border border-slate-600 outline-none"
                                value={meepleTarget}
                                onChange={(e) => setMeepleTarget(e.target.value)}
                            >
                                {state.meeple_choices.map(c => <option key={c} value={c}>{c.includes('None') ? 'No Meeple' : c}</option>)}
                            </select>
                        </div>
                    </div>
                )}
            </div>

            {/* Board Canvas */}
            <div className="flex-1 relative cursor-grab active:cursor-grabbing">
                <TransformWrapper
                    initialScale={1}
                    minScale={0.2}
                    maxScale={4}
                    centerOnInit={true}
                    wheel={{ step: 0.1 }}
                >
                    <TransformComponent wrapperStyle={{ width: '100%', height: '100%' }}>
                        <div
                            className="relative"
                            style={{ width, height, background: '#20242d', backgroundImage: 'radial-gradient(#ffffff11 1px, transparent 1px)', backgroundSize: '120px 120px' }}
                        >

                            {/* Placed Tiles */}
                            {state.grid.map((tile, i) => (
                                <div key={i} className="absolute" style={{ ...getPos(tile.x, tile.y), width: TILE_SIZE, height: TILE_SIZE }}>
                                    <img
                                        src={`/assets/tiles/Base_Game_C3_Tile_${tile.name.replace('Tile_', '')}.png`}
                                        className="w-full h-full shadow-lg"
                                        style={{ transform: `rotate(${tile.rotation}deg)` }}
                                        alt={tile.name}
                                    />
                                    {/* Meeples */}
                                    {tile.meeples.map((m, midx) => (
                                        <img
                                            key={midx}
                                            src={`/assets/meeples/${m.player === 'Player1' ? 'red' : 'blue'}_meeple.${m.player === 'Player1' ? 'png' : 'jpg'}`}
                                            className="absolute z-10 drop-shadow-lg"
                                            style={{
                                                width: TILE_SIZE * 0.3,
                                                height: TILE_SIZE * 0.3,
                                                left: (TILE_SIZE / 2) - (TILE_SIZE * 0.15) + (midx * 10 - 5),
                                                top: (TILE_SIZE / 2) - (TILE_SIZE * 0.15) + (midx * 10 - 5),
                                            }}
                                        />
                                    ))}

                                    {/* Highlight last played */}
                                    {state.last_played.x === tile.x && state.last_played.y === tile.y && (
                                        <div className="absolute inset-0 border-4 border-orange-400 z-20 pointer-events-none" />
                                    )}
                                </div>
                            ))}

                            {/* Ghost Moves (Interactable) */}
                            {state.is_human_turn && validPlacements.map((move, i) => {
                                const isSelected = selectedMove && selectedMove.x === move.x && selectedMove.y === move.y;
                                return (
                                    <div
                                        key={`ghost-${i}`}
                                        className="absolute z-30 flex items-center justify-center transition-all group"
                                        style={{ ...getPos(move.x, move.y), width: TILE_SIZE, height: TILE_SIZE, padding: '4px' }}
                                    >
                                        <div
                                            onClick={() => handleGhostClick(move)}
                                            className={`w-full h-full rounded border-2 cursor-pointer
                        ${isSelected ? 'bg-green-500/40 border-green-400 border-4' : 'bg-slate-500/20 border-slate-500 border-dashed hover:bg-slate-400/40'}
                      `}
                                        >
                                            {isSelected && (
                                                <div className="w-full h-full flex flex-col items-center justify-center text-white bg-black/50 backdrop-blur-sm rounded pb-1 pointer-events-none">
                                                    <img
                                                        src={`/assets/tiles/Base_Game_C3_Tile_${state.pending_tile?.replace('Tile_', '')}.png`}
                                                        className="w-16 h-16 shadow"
                                                        style={{ transform: `rotate(${rotation}deg)` }}
                                                    />
                                                    <div className="text-[10px] mt-1 bg-green-600 px-2 rounded-full font-bold">CLICK TO PLACE</div>
                                                </div>
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
