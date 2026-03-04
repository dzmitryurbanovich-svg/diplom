import axios from 'axios';
import type { GameState } from './types';

const CLIENT = axios.create({
    baseURL: '/api',
});

export const authLogin = async (email: string, password: string) => {
    const res = await CLIENT.post('/auth/login', { email, password });
    return res.data;
};

export const authRegister = async (email: string, password: string) => {
    const res = await CLIENT.post('/auth/register', { email, password });
    return res.data;
};

export const startNewGame = async (p1_type: string, p2_type: string) => {
    const res = await CLIENT.post('/game/new', { p1_type, p2_type });
    return res.data.session_id;
};

export const fetchGameState = async (sessionId: string): Promise<GameState> => {
    const res = await CLIENT.get(`/game/${sessionId}/state`);
    return res.data;
};

export const applyMove = async (
    sessionId: string,
    x: number,
    y: number,
    rotation: number,
    meeple_target: string
) => {
    const res = await CLIENT.post(`/game/${sessionId}/move`, {
        x, y, rotation, meeple_target
    });
    return res.data;
};

export const triggerAiStep = async (sessionId: string) => {
    const res = await CLIENT.post(`/game/${sessionId}/ai_step`);
    return res.data;
};
