export interface MeepleData {
    index: number;
    player: string;
}

export interface TileData {
    x: number;
    y: number;
    name: string;
    rotation: number;
    meeples: MeepleData[];
}

export interface LegalMove {
    x: number;
    y: number;
    r: number;
}

export interface GameState {
    game_over: boolean;
    current_player: string;
    is_human_turn: boolean;
    scores: Record<string, number>;
    meeples: Record<string, number>;
    logs: string[];
    deck_remaining: number;
    grid: TileData[];
    pending_tile: string | null;
    legal_moves: LegalMove[];
    meeple_choices: string[];
    last_played: { x: number; y: number };
}
